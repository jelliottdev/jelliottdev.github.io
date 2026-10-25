"""The preview route must avoid archives; both routes stop on failed stages."""
import subprocess
import unittest
from pathlib import Path
from build_research import build


class BuildTests(unittest.TestCase):
    def test_stale_or_invalid_runtime_inputs_stop_before_publication(self):
        names = []
        def failing(command, **options):
            names.append(Path(command[1]).name)
            raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError):
            build(Path('/fixture'), run=failing)
        self.assertEqual(names, ['build_local_run_inputs.py'])

    def test_preview_runs_content_and_map_without_archive_or_catalog_writes(self):
        calls = []
        build(Path('/fixture'), run=lambda command, **options: calls.append((command, options)), preview=True)
        names = [Path(call[0][1]).name for call in calls]
        self.assertEqual(names, ['build_experiments.py', 'build_research_map.py', 'build_home_clusters.py'])
        self.assertTrue(all(call[1]['check'] and call[1]['cwd'] == Path('/fixture') for call in calls))

    def test_full_build_preserves_dependency_order_and_failure_stops_it(self):
        names = []
        def failing(command, **options):
            names.append(Path(command[1]).name)
            if names[-1] == 'build_experiments.py':
                raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError):
            build(Path('/fixture'), run=failing)
        self.assertEqual(names, ['build_local_run_inputs.py', 'build_published_count_evidence.py', 'build_experiments.py'])
        names.clear()
        build(Path('/fixture'), run=lambda command, **options: names.append(Path(command[1]).name))
        self.assertEqual(names[0], 'build_local_run_inputs.py')
        self.assertLess(names.index('build_local_run_inputs.py'), names.index('build_published_count_evidence.py'))
        self.assertLess(names.index('build_published_count_evidence.py'), names.index('build_experiments.py'))
        self.assertLess(names.index('build_experiments.py'), names.index('build_access_exports.py'))
        self.assertLess(names.index('build_research_map.py'), names.index('build_home_clusters.py'))
        self.assertLess(names.index('build_home_clusters.py'), names.index('check_download_catalog.py'))


if __name__ == '__main__':
    unittest.main()
