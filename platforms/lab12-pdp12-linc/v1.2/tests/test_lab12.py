"""Host tests for exactly the core modules deployed on Pico W.

Run: python -m unittest discover -s tests -v
No hardware is necessary for these tests; they do NOT validate 1-Wire
physical waveforms, the compiled MSP430, or USB CDC behavior.
"""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pico_w'))
from labcore import LabComputer, MEMORY_SIZE, PROGRAM
from protocol import crc8, parse_evidence, signed16

ROM_BODY = bytes.fromhex('28123456789ABC')
ROM = ROM_BODY + bytes([crc8(ROM_BODY)])


def make_line(seq, temp_c, inject=0, tamper_crc=False):
    """Construct a DS18B20 observation with two self-consistent CRCs."""
    raw=int(round(temp_c*16)) & 0xffff
    scratch=bytearray([raw&255,raw>>8,0x4B,0x46,0x7F,0xFF,0x0C,0x10])
    scratch.append(crc8(scratch))
    if tamper_crc:
        scratch[8] ^= 1
    return ('SEQ_HEX=%04X,STATUS=%d,STATE=0,X16_HEX=%04X,ROM=%s,SCRATCH=%s,INJECT=%d' %
            (seq,0 if inject==0 else -2,raw,ROM.hex().upper(),bytes(scratch).hex().upper(),inject))


class ProtocolTests(unittest.TestCase):
    def test_valid_evidence(self):
        e=parse_evidence(make_line(2, 65.5))
        self.assertTrue(e['valid'])
        self.assertEqual(e['resolution_bits'],12)
        self.assertEqual(e['temp_c'],65.5)

    def test_invalid_scratch_crc(self):
        e=parse_evidence(make_line(2, 65.5,tamper_crc=True))
        self.assertFalse(e['valid'])
        self.assertIsNone(e['temp_c'])

    def test_injected_fault_is_excluded(self):
        e=parse_evidence(make_line(2, 65.5,inject=1))
        self.assertFalse(e['valid'])

    def test_signed16(self):
        self.assertEqual(signed16(0xfff0),-16)
        self.assertEqual(signed16(0x0010),16)


class LabComputerTests(unittest.TestCase):
    def test_newton_fit_on_pico_core(self):
        lab=LabComputer(ambient_c=23.0)
        for i in range(1,40):
            t=i*5.0
            temp=23+50*math.exp(-0.0025*t)
            e=parse_evidence(make_line(i,temp))
            p=lab.ingest(e,int(t*1000),'gp2_soft_irq',i)
        self.assertTrue(p['valid'])
        self.assertTrue(lab.model is not None)
        self.assertAlmostEqual(lab.model['k_per_s'],0.0025,delta=0.00005)
        self.assertLess(lab.model['rms_c'],0.1)
        self.assertEqual(lab.good_samples,39)

    def test_missing_sequence(self):
        lab=LabComputer()
        lab.ingest(parse_evidence(make_line(1,67)),0,'uart_arrival',0)
        output=lab.ingest(parse_evidence(make_line(5,66)),5000,'uart_arrival',0)
        self.assertEqual(output['missing'],3)
        self.assertEqual(lab.status()['missing'],3)

    def test_duplicate_is_invalid(self):
        lab=LabComputer()
        lab.ingest(parse_evidence(make_line(1,67)),0,'uart_arrival',0)
        p=lab.ingest(parse_evidence(make_line(1,67)),1000,'uart_arrival',0)
        self.assertFalse(p['valid'])
        self.assertIsNone(p['temp_c'])

    def test_bounded_lab_memory(self):
        lab=LabComputer()
        for i in range(MEMORY_SIZE+8):
            lab.ingest(parse_evidence(make_line(i,70)),i*1000,'uart_arrival',0)
        self.assertEqual(len(lab.memory),MEMORY_SIZE)
        self.assertEqual(lab.total_samples,MEMORY_SIZE+8)

    def test_independent_threshold_event(self):
        lab=LabComputer()
        lab.set_trigger(40.0)
        a=lab.ingest(parse_evidence(make_line(1,46)),0,'gp2_soft_irq',1)
        b=lab.ingest(parse_evidence(make_line(2,39)),2000,'gp2_soft_irq',2)
        c=lab.ingest(parse_evidence(make_line(3,38)),4000,'gp2_soft_irq',3)
        self.assertIsNone(a['trigger_event'])
        self.assertEqual(b['trigger_event']['label'],'COOLED_TO_40.00C')
        self.assertIsNone(c['trigger_event'])
        self.assertTrue(lab.status()['trigger_fired'])

    def test_mark_clear(self):
        lab=LabComputer()
        e=lab.mark('Removed lid',12500)
        self.assertEqual(e['label'],'Removed lid')
        lab.clear()
        self.assertEqual(lab.events,[])
        self.assertEqual(lab.run_id,1)
        self.assertIn('ANALYZE',PROGRAM)

    def test_ambient_range(self):
        lab=LabComputer()
        with self.assertRaises(ValueError):
            lab.set_ambient(200.0)


if __name__ == '__main__':
    unittest.main()
