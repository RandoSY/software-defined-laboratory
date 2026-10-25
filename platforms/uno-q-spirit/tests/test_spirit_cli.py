import csv
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import spirit_cli as cli

class FakeBridge:
    def __init__(self): self.calls=[]
    def call(self, method, *args, timeout=5):
        self.calls.append((method, args))
        if method == cli.RPC_COMMAND: return '{"ok":true}'
        return cli.MockBridge().call(cli.RPC_STATUS)

class FailBridge:
    def call(self, method, *args, timeout=5):
        raise TimeoutError('simulated disconnection')

class TestCLI(unittest.TestCase):
    def test_mock_status(self):
        d=cli.sample(cli.MockBridge()); self.assertEqual(d['schema'],1)
        self.assertEqual(d['mode'],'synthetic'); self.assertEqual(len(d['spectral']['channels']),18)
        self.assertEqual(d['temp_c']['state'],'SYNTH')
    def test_mock_live_missing(self):
        m=cli.MockBridge();cli.request(m,'mode live')
        d=cli.sample(m);self.assertEqual(d['temp_c']['state'],'MISSING')
        self.assertIsNone(d['temp_c']['value'])
    def test_prototype_profile_marks_unused_sensors_disabled(self):
        m=cli.MockBridge()
        self.assertTrue(cli.request(m, 'profile prototype')['ok'])
        cli.request(m,'mode live')
        d=cli.sample(m)
        self.assertEqual(d['profile'], 'prototype')
        self.assertEqual(d['temp_c']['state'], 'MISSING')
        self.assertEqual(d['spectral']['state'], 'MISSING')
        self.assertEqual(d['hx711_counts']['state'], 'DISABLED')
        self.assertEqual(d['distance_cm']['state'], 'DISABLED')
        self.assertIsNone(d['distance_cm']['value'])
        cli.request(m, 'profile all')
        self.assertEqual(cli.sample(m)['hx711_counts']['state'],'MISSING')

    def test_direct_profile_cli(self):
        args = cli.build_parser().parse_args(['profile', 'prototype'])
        m = cli.MockBridge()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.execute(m, args), 0)
        self.assertEqual(m.profile, 'prototype')

    def test_bad_gain(self):
        with self.assertRaises(ValueError): cli.request(cli.MockBridge(),'gain 13')
    def test_invalid_response(self):
        with self.assertRaises(ValueError): cli.decode('[1,2,3]')
    def test_invalid_schema(self):
        class C:
            def call(self,*a,**k): return json.dumps({'schema':4})
        with self.assertRaises(ValueError):cli.sample(C())
    def test_bad_channels(self):
        class C:
            def call(self,*a,**k):
                d=json.loads(cli.MockBridge().call(cli.RPC_STATUS));d['spectral']['channels']=[1];return json.dumps(d)
        with self.assertRaises(ValueError):cli.sample(C())
    def test_rpc_name(self):
        f=FakeBridge();cli.request(f,'tare');self.assertEqual(f.calls[0][0], 'spirit.command')
    def test_transport_failure(self):
        with self.assertRaises(TimeoutError):cli.sample(FailBridge())
    def test_flatten(self):
        r=cli.flatten(cli.sample(cli.MockBridge()));self.assertEqual(r['mode'],'synthetic')
        self.assertEqual(len(json.loads(r['spectrum_18'])),18)
    def test_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data.csv'
            a=cli.build_parser().parse_args(['--mock','capture','--count','3','--period','0.1','--output',str(p)])
            with redirect_stdout(io.StringIO()): self.assertEqual(cli.execute(cli.MockBridge(),a),0)
            with p.open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[0]['temp_state'],'SYNTH')
    def test_capture_fault_tolerant(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'data.csv'
            a=cli.build_parser().parse_args(['capture','--count','2','--period','0.1','--output',str(p)])
            with redirect_stdout(io.StringIO()): cli.execute(FailBridge(),a)
            with p.open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]['mode'],'ERROR')
    def test_interval_boundary(self):
        m=cli.MockBridge();cli.request(m,'interval 100');self.assertEqual(m.interval,100)
        with self.assertRaises(ValueError):cli.request(m,'interval 99')

if __name__=='__main__': unittest.main()
