"""NSP script: a merged cartridge image (.xci) is the base game, its bundled update and its DLC, whatever title ID its name is tagged with: Animal Crossing's
"[01006F8002326800][v1769472][Base][v2.0.5][3 DLC's].xci" is tagged with the update's title ID. The package's content metas (nx_extract --contents) decide, not the name.
nx_extract is stood in for (no game files or keys needed)."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('build_ipa_from_nsp', REPO / 'scripts/build_ipa_from_nsp.py')
nsp = importlib.util.module_from_spec(spec); spec.loader.exec_module(nsp)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_nsp_scan import xci   # noqa: E402  an XCI whose secure partition holds empty files with these names

APP = 0x01006F8002326000
NAME = "Animal Crossing New Horizons [01006F8002326800][v1769472][Base][v2.0.5][3 DLC's].xci"
CONTENTS = [('Application', APP, 0), ('Patch', APP | 0x800, 1769472), ('AddOnContent', APP + 0x1001, 0), ('AddOnContent', APP + 0x1002, 0), ('AddOnContent', APP + 0x1003, 65536)]


class Xci(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.xci = self.tmp / NAME; xci(self.xci, [f'{c}.cnmt.nca' for c in 'abcde'] + ['f.nca'])
        self.runs = []
        for cm in (mock.patch.object(nsp, 'PROG', mock.Mock()), mock.patch.object(nsp, 'say', lambda m: None), mock.patch.object(nsp, 'run', self.fake_nx)):
            cm.__enter__(); self.addCleanup(cm.__exit__, None, None, None)

    def fake_nx(self, cmd, log, env=None, cwd=None, on_line=None, ok=()):
        self.runs.append([str(c) for c in cmd[2:]])
        Path(cmd[4]).parent.mkdir(parents=True, exist_ok=True)

    def scan(self):
        return nsp.scan_nsps(self.tmp, None, lambda p: CONTENTS if p == self.xci else None)

    def test_merged_xci_is_base_update_and_dlc(self):
        app, fam = self.scan()
        self.assertEqual((app, fam['base'], fam['updates']), (APP, self.xci, [(1769472, self.xci)]))
        self.assertEqual(sorted(t for t, _, _ in fam['dlc']), [APP + 0x1001, APP + 0x1002, APP + 0x1003])

    def test_an_update_nsp_beside(self):
        upd = self.tmp / 'Update [01006F8002326800][v2228224].nsp'; upd.write_bytes(b'PFS0' + bytes(12))   # an empty PFS0: no ticket, the name's tag
        app, fam = self.scan()
        self.assertEqual((fam['base'], sorted(fam['updates'])), (self.xci, [(1769472, self.xci), (2228224, upd)]))

    def test_bundled_dlc_named_by_title_id(self):
        app, fam = self.scan()
        work = self.tmp / 'work'; logs = work / 'logs'; logs.mkdir(parents=True)
        nsp.extract_aoc(Path('nx'), Path('keys'), REPO, work, app, fam, logs)
        aoc = sorted(r for r in self.runs if r[0] == '--aoc')
        self.assertEqual(aoc, [['--aoc', str(self.xci), str(work / f'aoc.partial/{i}.img'), '--romfs-image', f'{APP + 0x1000 + i:016x}'] for i in (1, 2, 3)])


if __name__ == '__main__':
    unittest.main()
