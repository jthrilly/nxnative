"""NSP script: a cartridge image (.xci) is the base game whatever title ID its name is tagged with, and a merged one bundles its update ([v<N>] in its name) and DLC (nx_extract --list).
Animal Crossing's "[01006F8002326800][v1769472][Base][v2.0.5][3 DLC's].xci" is tagged with the update's title ID. nx_extract is stood in for (no game files or keys needed)."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('build_ipa_from_nsp', REPO / 'scripts/build_ipa_from_nsp.py')
nsp = importlib.util.module_from_spec(spec); spec.loader.exec_module(nsp)

APP = 0x01006F8002326000
NAME = "Animal Crossing New Horizons [01006F8002326800][v1769472][Base][v2.0.5][3 DLC's].xci"
LISTING = f'{APP:016x} Application v0\n{APP | 0x800:016x} Patch v1769472\n{APP + 0x1001:016x} AddOnContent v0\n{APP + 0x1002:016x} AddOnContent v0\n{APP + 0x1003:016x} AddOnContent v65536\n'


class Xci(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.xci = self.tmp / NAME; self.xci.write_bytes(bytes(0x100) + b'HEAD')   # a card header: scan_nsps takes a file by its header (is_package)
        self.runs = []
        for cm in (mock.patch.object(nsp, 'PROG', mock.Mock()), mock.patch.object(nsp, 'say', lambda m: None), mock.patch.object(nsp, 'run', self.fake_nx)):
            cm.__enter__(); self.addCleanup(cm.__exit__, None, None, None)

    def fake_nx(self, cmd, log, env=None, cwd=None, on_line=None):
        self.runs.append([str(c) for c in cmd[2:]])
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        if cmd[2] == '--list': Path(log).write_text(LISTING)
        else: Path(cmd[4]).mkdir(parents=True)

    def test_merged_xci_is_base_and_update(self):
        app, fam = nsp.scan_nsps(self.tmp)
        self.assertEqual((app, fam['base'], fam['updates'], fam['dlc']), (APP, self.xci, [(1769472, self.xci)], []))
        self.assertEqual(nsp.pick_nsps(fam, nsp.nsp_versions(fam, {}), ['v1769472']), {'v1769472': (self.xci, self.xci)})

    def test_cartridge_dump_without_update(self):
        self.xci.rename(self.tmp / 'Game [01006F8002326000][v0].xci')
        app, fam = nsp.scan_nsps(self.tmp)
        self.assertEqual((app, fam['base'].name, fam['updates']), (APP, 'Game [01006F8002326000][v0].xci', []))

    def test_an_update_nsp_beside(self):
        upd = self.tmp / 'Update [01006F8002326800][v2228224].nsp'; upd.write_bytes(b'PFS0' + bytes(12))   # an empty PFS0: no ticket, the name's tag
        app, fam = nsp.scan_nsps(self.tmp)
        self.assertEqual((fam['base'], sorted(fam['updates'])), (self.xci, [(1769472, self.xci), (2228224, upd)]))

    def test_bundled_dlc(self):
        app, fam = nsp.scan_nsps(self.tmp)
        work = self.tmp / 'work'; logs = work / 'logs'; logs.mkdir(parents=True)
        nsp_dlc = self.tmp / 'DLC [01006F8002327002][v0].nsp'; nsp_dlc.write_bytes(b'PFS0' + bytes(12)); fam['dlc'].append((APP + 0x1002, 0, nsp_dlc))
        self.assertEqual(nsp.extract_aoc(Path('nx'), Path('keys'), REPO, work, app, fam, logs), work / 'aoc')
        self.assertEqual(sorted(p.name for p in (work / 'aoc').iterdir()), ['1.img', '2.img', '3.img'])
        aoc = sorted((r for r in self.runs if r[0] == '--aoc'), key=lambda r: r[2])
        self.assertEqual(aoc, [['--aoc', str(self.xci), str(work / 'aoc.partial/1.img'), '--romfs-image', f'{APP + 0x1001:016x}'], ['--aoc', str(nsp_dlc), str(work / 'aoc.partial/2.img'), '--romfs-image'],   # the NSP wins
                               ['--aoc', str(self.xci), str(work / 'aoc.partial/3.img'), '--romfs-image', f'{APP + 0x1003:016x}']])

    def test_cartridge_without_dlc(self):
        self.xci.rename(self.tmp / 'Game [01006F8002326000][v0].xci')
        app, fam = nsp.scan_nsps(self.tmp)
        work = self.tmp / 'work'; logs = work / 'logs'; logs.mkdir(parents=True)
        with mock.patch.object(nsp, 'bundled_dlc', lambda *a: []):
            self.assertIsNone(nsp.extract_aoc(Path('nx'), Path('keys'), REPO, work, app, fam, logs))


if __name__ == '__main__':
    unittest.main()
