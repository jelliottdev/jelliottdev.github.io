"""The isolated export test copies publication inputs, never unrelated local trees."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from test_export_reproducibility import copy_tracked_checkout


class CheckoutCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='export-copy-unit-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source, self.target = self.base / 'source', self.base / 'isolated'
        self.source.mkdir()
        self.git('init', '-q')

    def git(self, *args, input=None):
        return subprocess.check_output(['git', *args], cwd=self.source, input=input,
                                       stderr=subprocess.STDOUT)

    def write(self, name, data=b'tracked', stage=True):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if stage:
            self.git('add', '--', name)
        return path

    def test_current_bytes_staged_additions_and_independent_copies(self):
        names = ['.publication', 'nested/a file.txt', 'nested/runes-ᚠ-é.txt']
        for name in names:
            self.write(name)
        # The Git inventory must not substitute stale index content.
        (self.source / names[1]).write_bytes(b'edited after staging\x00\xff')
        self.write('new/staged.txt', b'newly staged')
        self.assertEqual(copy_tracked_checkout(self.source, self.target), 4)
        for name in names + ['new/staged.txt']:
            self.assertEqual((self.target / name).read_bytes(), (self.source / name).read_bytes())
            self.assertFalse(os.path.samefile(self.target / name, self.source / name))
        (self.target / names[1]).write_bytes(b'isolated build output')
        self.assertEqual((self.source / names[1]).read_bytes(), b'edited after staging\x00\xff')
        self.assertFalse((self.target / '.git').exists())

    def test_untracked_poison_and_deep_trees_are_not_enumerated(self):
        self.write('scripts/build.py')
        self.write('research/source-intake/poison.md', b'must not publish', stage=False)
        self.write('qa-temp/deep/untracked/payload.txt', stage=False)
        # Any recursive enumeration would defeat the bounded inventory.
        with patch('os.scandir', side_effect=AssertionError('Do not enumerate checkout trees')):
            self.assertEqual(copy_tracked_checkout(self.source, self.target), 1)
        self.assertFalse((self.target / 'research').exists())
        self.assertFalse((self.target / 'qa-temp').exists())

    def test_rebuilt_archives_are_excluded_before_any_copy(self):
        excluded = ['downloads/reference-data.zip', 'downloads/original-images.zip',
                    'downloads/transcriptions-and-readings.zip', 'downloads/experiments/example.zip']
        for name in excluded:
            self.write(name)
            (self.source / name).unlink()  # A regenerated archive need not exist yet.
        self.write('downloads/source-evidence.zip')
        self.assertEqual(copy_tracked_checkout(self.source, self.target), 1)
        for name in excluded:
            self.assertFalse((self.target / name).exists())
        self.assertTrue((self.target / 'downloads/source-evidence.zip').is_file())

    def test_missing_tracked_source_fails_before_copying_anything(self):
        self.write('a.txt')
        self.write('missing.txt').unlink()
        with self.assertRaises(FileNotFoundError):
            copy_tracked_checkout(self.source, self.target)
        self.assertFalse((self.target / 'a.txt').exists())

    def test_existing_destination_cannot_overwrite_a_linked_source(self):
        original = self.write('input.txt', b'unchanged source')
        self.target.mkdir()
        (self.target / 'input.txt').hardlink_to(original)
        with self.assertRaisesRegex(ValueError, 'must not already exist'):
            copy_tracked_checkout(self.source, self.target)
        self.assertEqual(original.read_bytes(), b'unchanged source')

    def test_unresolved_merge_entries_are_rejected(self):
        self.write('conflict.txt')
        oid = self.git('hash-object', '-w', '--stdin', input=b'conflict').strip()
        self.git('update-index', '--force-remove', 'conflict.txt')
        entries = b''.join(b'100644 ' + oid + b' ' + str(stage).encode() + b'\tconflict.txt\n'
                           for stage in (1, 2, 3))
        self.git('update-index', '--index-info', input=entries)
        with self.assertRaisesRegex(ValueError, 'index conflict'):
            copy_tracked_checkout(self.source, self.target)

    def test_unsafe_inventory_paths_and_resolved_escapes_are_rejected_portably(self):
        self.write('nested/input.txt')
        for name in ('../outside', '/absolute', 'C:/drive', 'back\\slash'):
            inventory = b'100644 ' + b'0' * 40 + b' 0\t' + name.encode() + b'\0'
            with patch('test_export_reproducibility.subprocess.check_output',
                       side_effect=[os.fsencode(str(self.source)) + b'\n', inventory]):
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    copy_tracked_checkout(self.source, self.target)
        # Exercise containment on Windows too, even when symlink creation is disabled.
        real_resolve = Path.resolve
        for escaping, message in ((self.source / 'nested/input.txt', 'source escapes'),
                                  (self.target / 'nested/input.txt', 'destination escapes')):
            def resolve(path, *args, **kwargs):
                return self.base / 'outside.txt' if path == escaping else real_resolve(path, *args, **kwargs)
            with patch.object(Path, 'resolve', resolve):
                with self.assertRaisesRegex(ValueError, message):
                    copy_tracked_checkout(self.source, self.target)

    def test_tracked_symlink_mode_and_worktree_symlink_escape_are_rejected(self):
        self.write('link.txt')
        oid = self.git('hash-object', '-w', '--stdin', input=b'../outside.txt').strip().decode()
        self.git('update-index', '--add', '--cacheinfo', '120000,' + oid + ',link.txt')
        with self.assertRaisesRegex(ValueError, 'regular tracked files'):
            copy_tracked_checkout(self.source, self.target)
        self.git('update-index', '--cacheinfo', '100644,' + oid + ',link.txt')
        (self.source / 'link.txt').unlink()
        outside = self.base / 'outside.txt'
        outside.write_bytes(b'outside')
        try:
            (self.source / 'link.txt').symlink_to(outside)
        except OSError:
            self.skipTest('This host does not permit creating filesystem symlinks')
        with self.assertRaisesRegex(ValueError, 'escapes its checkout'):
            copy_tracked_checkout(self.source, self.target)

    def test_overlapping_and_destination_escape_paths_are_rejected(self):
        self.write('nested/input.txt')
        for target in (self.source, self.source / 'copy', self.base):
            with self.assertRaisesRegex(ValueError, 'separate'):
                copy_tracked_checkout(self.source, target)
        self.target.mkdir()
        outside = self.base / 'outside'
        outside.mkdir()
        try:
            (self.target / 'nested').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('This host does not permit creating directory symlinks')
        with self.assertRaisesRegex(ValueError, 'destination escapes'):
            copy_tracked_checkout(self.source, self.target)
        self.assertFalse((outside / 'input.txt').exists())


if __name__ == '__main__':
    unittest.main()
