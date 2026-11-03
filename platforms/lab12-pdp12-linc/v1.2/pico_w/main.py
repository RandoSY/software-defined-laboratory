"""LAB-12 / Pico W: experiment computer, not a USB/TTL converter.

Program structure reflects the early LINC/PDP-12 laboratory philosophy:
  ACQUIRE  -> request hardware measurements from MSP430
  VALIDATE -> independently check ROM / scratchpad / decoded temperature
  STORE    -> preserve a bounded ring of timestamped measurements
  ANALYZE  -> fit Newton's cooling on the RP2040, calculate residuals
  PUBLISH  -> stream structured results to the Chrome operator console

Hardware: MSP430 TX P1.2 -> Pico GP1 (UART0 RX); MSP430 RX P1.1 <-
Pico GP0 (UART0 TX); common GND. Optional 1 ms event marker
MSP430 P2.0 -> Pico GP2. DS18B20 DQ belongs on MSP430 P1.7.
Pico/Pico W USB data cable -> PC. Chrome Web Serial, no Wi-Fi/bridge.

GP2 soft-IRQ timestamps are *not* calibrated precision measurements.
Neither the marker nor UART arrival is the exact DS18B20 sample instant.

USB commands, newline terminated:
HELLO, STATUS, START, STOP, PING, RATE=1000..60000,
AMBIENT=23.0, TRIGGER=40.0|OFF, FIT=0|1, MARK=short text, HISTORY, CLEAR,
FAULT=0|1|2 (instructional error injection; NOT for real control).

The RP2040 maintains a volatile experiment memory of 160 points, whereas
Chrome owns long-run CSV files.  This is explicitly NOT a PDP-12 emulator.
"""
import sys
import time
from machine import Pin, UART
try:
    import ujson as json
except ImportError:
    import json
try:
    import uselect as select
except ImportError:
    import select
from labcore import LabComputer
from protocol import parse_evidence

UART_BAUD = 9600
UART_LINE_MAX = 240
USB_LINE_MAX = 100
STATUS_PERIOD_MS = 5000

msp = UART(0, baudrate=UART_BAUD, tx=Pin(0), rx=Pin(1), timeout=0, rxbuf=512)
marker = Pin(2, Pin.IN, Pin.PULL_DOWN)
marker_count = 0
marker_ticks_us = 0


def on_marker(pin):
    """Interrupt: avoid allocation, printing or slow work here."""
    global marker_count, marker_ticks_us
    marker_ticks_us = time.ticks_us()
    marker_count += 1


marker.irq(trigger=Pin.IRQ_RISING, handler=on_marker)
lab = LabComputer(ambient_c=23.0)
rx = bytearray()
rx_dropping = False
usb_buffer = ''
error_counts = {'decode': 0, 'line_overflow': 0}
marker_consumed = 0
last_tick_us = None
elapsed_us = 0
start_ticks_ms = time.ticks_ms()


def emit(record):
    """All USB communications are one complete JSON object per line.

    Avoid printf-style diagnostic noise: console software can reliably frame
    messages, regardless of arrival packet size and serial buffering.
    """
    sys.stdout.write(json.dumps(record) + '\n')


def report_error(where, message):
    emit({'type': 'error', 'source': where, 'message': str(message)})


def lab_status():
    state = lab.status()
    state.update({'uptime_ms': time.ticks_diff(time.ticks_ms(), start_ticks_ms),
                  'marker_events': marker_count,
                  'errors': error_counts,
                  'uart_baud': UART_BAUD, 'firmware': '1.1'})
    return state


def lab_timestamp_us():
    """Use fresh physical marker if available, otherwise UART arrival.

    Maintain *deltas* between consecutive samples to avoid subtracting a
    stale absolute ticks_us() value after the RP2040 tick counter wraps.
    Both timer sources are from one MCU clock domain.
    """
    global marker_consumed, last_tick_us, elapsed_us
    if marker_count != marker_consumed:
        t = marker_ticks_us
        marker_consumed = marker_count
        origin = 'gp2_soft_irq'
    else:
        t = time.ticks_us()
        origin = 'uart_arrival'
    if last_tick_us is not None:
        difference = time.ticks_diff(t, last_tick_us)
        if difference >= 0:
            elapsed_us += difference
    last_tick_us = t
    return elapsed_us // 1000, origin


def handle_msp(text):
    if text.startswith('DEVICE,') or text.startswith('ACK,') or text.startswith('ERROR,'):
        if text == 'ACK,START':
            lab.running = True
        elif text == 'ACK,STOP':
            lab.running = False
        emit({'type': 'msp_message', 'message': text})
        return
    try:
        evidence = parse_evidence(text)
    except (ValueError, TypeError) as exc:
        error_counts['decode'] += 1
        report_error('evidence_parser', exc)
        return
    if evidence is None:
        emit({'type': 'msp_message', 'message': text[:120]})
        return
    evidence['raw'] = text
    t_ms, source = lab_timestamp_us()
    item = lab.ingest(evidence, t_ms, source, marker_count)
    emit(item)
    if item['trigger_event']:
        emit(item['trigger_event'])


def read_msp():
    """Nonblocking framed UART: never block the lab clock or USB console."""
    global rx_dropping
    available = msp.any()
    if not available:
        return
    data = msp.read(min(available, 192))
    if not data:
        return
    for byte in data:
        if byte == 10:
            if rx_dropping:
                rx_dropping = False
                rx[:] = b''
                continue
            try:
                record = bytes(rx).decode('ascii').strip()
                if record:
                    handle_msp(record)
            except (ValueError, UnicodeError) as exc:
                error_counts['decode'] += 1
                report_error('uart_ascii', exc)
            rx[:] = b''
        elif byte != 13 and not rx_dropping:
            if len(rx) < UART_LINE_MAX:
                rx.append(byte)
            else:
                rx[:] = b''
                rx_dropping = True
                error_counts['line_overflow'] += 1
                report_error('uart', 'Line too long; discarded')


def send_to_msp(command):
    msp.write(command + '\n')
    emit({'type': 'command_sent', 'command': command, 'target': 'MSP430'})


def console_command(raw):
    """Whitelist commands; never expose arbitrary Python execution here."""
    global elapsed_us, last_tick_us, marker_consumed
    cmd = raw.strip()
    upper = cmd.upper()
    if not upper:
        return
    if upper in ('HELLO', 'STATUS'):
        emit(lab_status())
    elif upper == 'HISTORY':
        emit({'type': 'history_start', 'run_id': lab.run_id,
              'available': len(lab.memory), 'partial': lab.total_samples > len(lab.memory)})
        for point in lab.memory:
            copy = dict(point)
            copy['type'] = 'history_sample'
            copy['model'] = None  # Latest model is delivered by status.
            emit(copy)
        for event in lab.events:
            emit(event)
        emit({'type': 'history_end', 'run_id': lab.run_id,
              'model': lab.model})
    elif upper == 'CLEAR':
        lab.clear()
        elapsed_us = 0
        last_tick_us = None
        marker_consumed = marker_count
        emit({'type': 'cleared', 'run_id': lab.run_id,
              'message': 'Pico volatile experiment memory cleared, PC CSV not erased'})
        emit(lab_status())
    elif upper.startswith('AMBIENT='):
        try:
            value = float(cmd.split('=', 1)[1])
            # NaN comparison must be rejected explicitly.
            if not -40.0 <= value <= 110.0:
                raise ValueError('Outside range -40..110 C')
            lab.set_ambient(value)
            emit({'type': 'parameter', 'name': 'ambient_c', 'value': value,
                  'model': lab.model})
        except ValueError:
            report_error('command', 'AMBIENT requires a number -40..110 C')
    elif upper.startswith('TRIGGER='):
        try:
            value = None if upper == 'TRIGGER=OFF' else float(upper[8:])
            lab.set_trigger(value)
            emit({'type': 'parameter', 'name': 'trigger_c', 'value': value})
        except ValueError:
            report_error('command', 'TRIGGER expects -40..110 C or OFF')
    elif upper in ('FIT=0', 'FIT=1'):
        lab.fit_enabled = upper == 'FIT=1'
        lab.calculate_model()
        emit({'type': 'parameter', 'name': 'fit_enabled',
              'value': lab.fit_enabled, 'model': lab.model})
    elif upper.startswith('MARK='):
        try:
            emit(lab.mark(cmd.split('=', 1)[1], elapsed_us // 1000))
        except ValueError as exc:
            report_error('command', exc)
    elif upper in ('START', 'STOP', 'PING', 'FAULT=0', 'FAULT=1', 'FAULT=2'):
        send_to_msp(upper)
    elif upper.startswith('RATE='):
        try:
            period = int(upper.split('=', 1)[1])
            if period < 1000 or period > 60000:
                raise ValueError('Out of bounds')
            lab.period_ms = period
            send_to_msp('RATE=' + str(period))
            emit({'type': 'parameter', 'name': 'period_ms', 'value': period})
        except ValueError:
            report_error('command', 'RATE requires milliseconds 1000..60000')
    else:
        report_error('command', 'Unsupported operator command: ' + cmd[:48])


def read_console(poller):
    """MicroPython USB REPL stdin is Chrome's serial channel in this lab.

    Do not simultaneously connect Thonny, serial monitors or Chrome to the
    same USB CDC port.  MicroPython prints its boot banner on soft reset;
    Chrome will skip all non-JSON lines safely.
    """
    global usb_buffer
    if not poller.poll(0):
        return
    char = sys.stdin.read(1)
    if not char:
        return
    if char in '\r\n':
        if usb_buffer:
            console_command(usb_buffer)
        usb_buffer = ''
    elif len(usb_buffer) < USB_LINE_MAX:
        usb_buffer += char
    else:
        usb_buffer = ''
        report_error('command', 'Operator command too long')


def main():
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    emit({'type': 'hello', 'device': 'LAB12_PICO_W', 'firmware': '1.1',
          'description': 'MicroPython LINC-inspired experimental computer'})
    emit(lab_status())
    heartbeat = time.ticks_ms()
    while True:
        read_msp()
        read_console(poller)
        now = time.ticks_ms()
        if time.ticks_diff(now, heartbeat) >= STATUS_PERIOD_MS:
            heartbeat = now
            emit(lab_status())
        time.sleep_ms(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Stop running this session in Thonny, return to interactive REPL.
        print('LAB-12 operator console stopped with Ctrl+C')
