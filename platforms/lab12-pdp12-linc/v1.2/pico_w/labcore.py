"""LAB-12: a compact LINC-inspired experimental computer for Pico / Pico W.

This is not a PDP-12 instruction-set emulator.  It preserves key laboratory
functions of that machine: programmed acquisition, a laboratory clock,
experimental memory, validated observations, event annotation, and on-board
analysis.  The browser is an operator console, not the scientific engine.

No MCU-specific imports.  CPython tests exercise the same code that runs on
MicroPython.  Units are seconds, degrees Celsius and 1/seconds unless noted.

A running experiment implements this didactic five-instruction cycle:
    ACQUIRE -> VALIDATE -> STORE -> ANALYZE -> PUBLISH

ACQUIRE is external to this module (MSP430 one-wire), VALIDATE occurs in
protocol.py and the remaining operations are implemented below.
"""
import math

PROGRAM = ('ACQUIRE', 'VALIDATE', 'STORE', 'ANALYZE', 'PUBLISH')
MEMORY_SIZE = 160  # 160 experiments readings; CSV belongs on the PC.


class LabComputer:
    """Pico-resident state machine, bounded memory and scientific model."""

    def __init__(self, ambient_c=23.0, period_ms=1000):
        self.ambient_c = float(ambient_c)
        self.period_ms = period_ms
        self.fit_enabled = True
        self.run_id = 0
        self.running = False
        self.memory = []
        self.events = []
        self.total_samples = 0
        self.good_samples = 0
        self.bad_samples = 0
        self.lost_samples = 0
        self.prev_seq = None
        self.prev_time_ms = None
        self.period_mean_ms = 0.0
        self.period_m2 = 0.0
        self.period_count = 0
        self.model = None
        self.trigger_c = None  # autonomous falling-temperature experiment event
        self.trigger_armed = False
        self.trigger_fired = False

    def clear(self):
        """New experiment / clear volatile lab memory (does not erase CSV)."""
        self.run_id += 1
        self.memory = []
        self.events = []
        self.total_samples = self.good_samples = self.bad_samples = 0
        self.lost_samples = 0
        self.prev_seq = self.prev_time_ms = None
        self.period_count = 0
        self.period_mean_ms = self.period_m2 = 0.0
        self.model = None
        self.trigger_armed = False
        self.trigger_fired = False

    def set_trigger(self, temp_c):
        """Program Pico to detect a threshold crossing independently of Chrome.

        Crossing requires one valid reading ABOVE target followed later by
        one valid reading AT or BELOW target; fires only once per run.
        """
        if temp_c is not None and not -40.0 <= temp_c <= 110.0:
            raise ValueError('Threshold must be -40..110 C')
        self.trigger_c = temp_c
        self.trigger_armed = False
        self.trigger_fired = False

    def set_ambient(self, temp_c):
        if not -40.0 <= temp_c <= 110.0:
            raise ValueError('Ambient temperature must be -40..110 C')
        self.ambient_c = float(temp_c)
        self.calculate_model()

    def mark(self, label, t_ms):
        """Mark a change in experimental conditions; no physical output."""
        # Carefully limit source length, memory and control characters.
        label = ''.join(c for c in label if 32 <= ord(c) <= 126)[:44]
        if not label:
            raise ValueError('Empty event label')
        mark = {'type': 'event', 'run_id': self.run_id,
                't_ms': t_ms, 'label': label}
        if len(self.events) >= 48:
            self.events.pop(0)
        self.events.append(mark)
        return mark

    def ingest(self, evidence, t_ms, clock_source, marker_count):
        """STORE and ANALYZE an independently validated MSP430 observation.

        t_ms is measured from the first observation in main.py, with an
        observed end-of-acquisition event preferred over UART reception.
        """
        seq = evidence['seq']
        missing, duplicate = 0, False
        if self.prev_seq is not None:
            step = (seq - self.prev_seq) & 0xFFFF
            if 1 < step < 0x8000:
                missing = step - 1
                self.lost_samples += missing
            elif step == 0 or step >= 0x8000:
                duplicate = True
        self.prev_seq = seq
        if duplicate:
            evidence['valid'] = False
            evidence['temp_c'] = None
            evidence['quality'] += ';DUPLICATE_OR_OLD_SEQ'

        interval_ms = None
        if self.prev_time_ms is not None:
            interval_ms = t_ms - self.prev_time_ms
            if interval_ms > 0:
                self.period_count += 1
                delta = interval_ms - self.period_mean_ms
                self.period_mean_ms += delta / self.period_count
                self.period_m2 += delta * (interval_ms - self.period_mean_ms)
        self.prev_time_ms = t_ms
        self.total_samples += 1
        if evidence['valid']:
            self.good_samples += 1
        else:
            self.bad_samples += 1

        item = {
            'type': 'sample', 'run_id': self.run_id,
            'seq': seq, 't_ms': t_ms, 'delta_ms': interval_ms,
            'clock_source': clock_source, 'marker_count': marker_count,
            'temp_c': evidence['temp_c'], 'raw_x16': evidence['x16'],
            'valid': evidence['valid'], 'quality': evidence['quality'],
            'rom_crc_ok': evidence['rom_crc_ok'],
            'scratch_crc_ok': evidence['scratch_crc_ok'],
            'temp_agrees': evidence['temp_agrees'],
            'resolution_bits': evidence['resolution_bits'],
            'missing': missing, 'rom': evidence['rom'],
            'scratch': evidence['scratch'], 'inject': evidence['inject'],
            'msp_status': evidence['status'], 'raw': evidence.get('raw', ''),
        }
        if len(self.memory) == MEMORY_SIZE:
            self.memory.pop(0)
        self.memory.append(item)
        # Event-driven lab computing: the Pico detects a physical condition
        # and records its own event, even if the dashboard is not connected.
        automatic_event = None
        if item['valid'] and self.trigger_c is not None and not self.trigger_fired:
            if item['temp_c'] > self.trigger_c:
                self.trigger_armed = True
            elif self.trigger_armed:
                automatic_event = self.mark('COOLED_TO_%.2fC' % self.trigger_c, t_ms)
                self.trigger_fired = True
        item['trigger_event'] = automatic_event
        self.calculate_model()
        if self.model and item['valid']:
            value = self.predict(t_ms)
            item['model_temp_c'] = round(value, 5)
            item['residual_c'] = round(item['temp_c'] - value, 5)
        else:
            item['model_temp_c'] = None
            item['residual_c'] = None
        # The browser receives the computed model, never independently fits.
        item['model'] = self.model
        return item

    def calculate_model(self):
        """On-board least-squares log-linear Newton cooling model.

        log(T - ambient) = intercept - k * t.  A positive k describes cooling.
        Require a small but meaningful temperature difference (>0.5 C),
        sufficient data and temporal spread; these are educational safeguards,
        NOT an uncertainty-qualified nonlinear statistical estimator.
        """
        self.model = None
        if not self.fit_enabled:
            return
        values = []
        for p in self.memory:
            if p['valid'] and p['temp_c'] is not None:
                excess = p['temp_c'] - self.ambient_c
                if excess > 0.5:
                    values.append((p['t_ms']/1000.0, math.log(excess)))
        n = len(values)
        if n < 6 or (values[-1][0] - values[0][0]) < 5.0:
            return
        sx = sum(p[0] for p in values)
        sy = sum(p[1] for p in values)
        sxx = sum(p[0]*p[0] for p in values)
        sxy = sum(p[0]*p[1] for p in values)
        denominator = n*sxx - sx*sx
        if abs(denominator) < 1.0e-8:
            return
        slope = (n*sxy - sx*sy)/denominator
        k = -slope
        if not 0.0 < k < 1.0:
            return
        intercept = (sy - slope*sx)/n
        initial_excess = math.exp(intercept)
        t0 = self.ambient_c + initial_excess
        error_sum = 0.0
        for t, ln_excess in values:
            measured = self.ambient_c + math.exp(ln_excess)
            predicted = self.ambient_c + initial_excess*math.exp(-k*t)
            error_sum += (measured - predicted)**2
        self.model = {
            'ambient_c': round(self.ambient_c, 5),
            't0_c': round(t0, 5),
            'k_per_s': round(k, 8),
            'tau_s': round(1.0/k, 3),
            'rms_c': round(math.sqrt(error_sum/n), 5),
            'points': n,
            'method': 'log-linear least squares on Pico',
        }

    def predict(self, t_ms):
        if self.model is None:
            return None
        m = self.model
        return m['ambient_c'] + (m['t0_c']-m['ambient_c'])*math.exp(-m['k_per_s']*t_ms/1000.0)

    def status(self):
        jitter = ((self.period_m2 / (self.period_count-1)) ** 0.5
                  if self.period_count > 1 else None)
        return {
            'type': 'status', 'device': 'LAB12_PICO_W', 'run_id': self.run_id,
            'running': self.running, 'ambient_c': self.ambient_c,
            'period_ms': self.period_ms, 'program': PROGRAM,
            'total': self.total_samples, 'good': self.good_samples,
            'bad': self.bad_samples, 'missing': self.lost_samples,
            'memory_items': len(self.memory), 'memory_capacity': MEMORY_SIZE,
            'events': len(self.events), 'fit_enabled': self.fit_enabled,
            'trigger_c': self.trigger_c, 'trigger_armed': self.trigger_armed,
            'trigger_fired': self.trigger_fired,
            'measured_period_ms': (round(self.period_mean_ms, 3)
                                    if self.period_count else None),
            'interval_sd_ms': round(jitter, 3) if jitter is not None else None,
            'model': self.model,
        }
