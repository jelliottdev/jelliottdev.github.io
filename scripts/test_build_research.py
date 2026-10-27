"""The preview route must avoid archives; both routes stop on failed stages."""
import subprocess
import sys
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
        self.assertTrue(all(call[0][0] == sys.executable for call in calls))
        self.assertEqual([call[0][2:] for call in calls], [[], [], ['.']])

    def test_full_build_preserves_dependency_order_and_failure_stops_it(self):
        names = []
        def failing(command, **options):
            names.append(Path(command[1]).name)
            if names[-1] == 'build_experiments.py':
                raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError):
            build(Path('/fixture'), run=failing)
        self.assertEqual(names, ['build_local_run_inputs.py', 'build_finite_sequence_banks.py', 'build_repeating_key_banks.py', 'build_published_count_evidence.py', 'build_published_evidence_history.py', 'build_experiments.py'])
        names.clear()
        build(Path('/fixture'), run=lambda command, **options: names.append(Path(command[1]).name))
        self.assertEqual(names[0], 'build_local_run_inputs.py')
        self.assertLess(names.index('build_local_run_inputs.py'), names.index('build_published_count_evidence.py'))
        self.assertLess(names.index('build_local_run_inputs.py'), names.index('build_finite_sequence_banks.py'))
        self.assertLess(names.index('build_finite_sequence_banks.py'), names.index('build_repeating_key_banks.py'))
        self.assertLess(names.index('build_repeating_key_banks.py'), names.index('build_experiments.py'))
        self.assertLess(names.index('build_published_count_evidence.py'), names.index('build_published_evidence_history.py'))
        self.assertLess(names.index('build_published_evidence_history.py'), names.index('build_experiments.py'))
        self.assertLess(names.index('build_experiments.py'), names.index('build_declared_program_evidence.mjs'))
        self.assertLess(names.index('build_declared_program_evidence.mjs'), names.index('build_published_program_catalog.py'))
        self.assertLess(names.index('build_published_program_catalog.py'), names.index('build_pinned_parent_artifacts.mjs'))
        self.assertLess(names.index('build_repeating_key_banks.py'), names.index('build_pinned_parent_artifacts.mjs'))
        self.assertLess(names.index('build_pinned_parent_artifacts.mjs'), names.index('build_compiled_program_index.mjs'))
        self.assertLess(names.index('build_compiled_program_index.mjs'), names.index('build_evidence_registry_fingerprint.mjs'))
        self.assertLess(names.index('build_evidence_registry_fingerprint.mjs'), names.index('build_published_program_discovery.mjs'))
        self.assertLess(names.index('build_published_program_discovery.mjs'), names.index('archive_authored_sources.py'))
        self.assertLess(names.index('archive_authored_sources.py'), names.index('build_access_exports.py'))
        self.assertLess(names.index('build_research_map.py'), names.index('build_home_clusters.py'))
        self.assertLess(names.index('build_home_clusters.py'), names.index('check_download_catalog.py'))


    def test_repeating_bank_check_is_pinned_and_stops_before_content_build(self):
        calls = []
        def failing(command, **options):
            calls.append((command, options))
            if Path(command[1]).name == 'build_repeating_key_banks.py':
                raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError):
            build(Path('/fixture'), run=failing)
        self.assertEqual([Path(c[0][1]).name for c in calls],
                         ['build_local_run_inputs.py', 'build_finite_sequence_banks.py', 'build_repeating_key_banks.py'])
        self.assertEqual(calls[-1][0][2:], ['--check'])
        self.assertEqual(calls[-1][1], {'cwd': Path('/fixture'), 'check': True})


    def test_source_archive_is_extended_before_exports_and_failure_stops_publication(self):
        calls = []
        def fail(command, **options):
            calls.append(command)
            if Path(command[1]).name == 'archive_authored_sources.py':
                raise subprocess.CalledProcessError(1, command)
        with self.assertRaises(subprocess.CalledProcessError):
            build(Path('/fixture'), run=fail)
        self.assertEqual(Path(calls[-1][1]).name, 'archive_authored_sources.py')
        self.assertEqual(calls[-1][2:], ['--write'])
        self.assertNotIn('build_access_exports.py', [Path(c[1]).name for c in calls])


    def test_program_derivatives_use_their_actual_write_cli_and_runtime(self):
        calls = []
        node = 'C:/Program Files/nodejs/node.exe'
        build(Path('/fixture'), run=lambda command, **options: calls.append((command, options)),
              node_executable=node)
        commands = {Path(command[1]).name: command for command, _ in calls}
        expected = {
            'build_declared_program_evidence.mjs': (node, ['--write']),
            'build_published_program_catalog.py': (sys.executable, ['--write']),
            'build_pinned_parent_artifacts.mjs': (node, ['--write']),
            'build_compiled_program_index.mjs': (node, []),
            'build_evidence_registry_fingerprint.mjs': (node, []),
            'build_published_program_discovery.mjs': (node, ['--write']),
        }
        for name, (interpreter, flags) in expected.items():
            with self.subTest(stage=name):
                self.assertEqual(commands[name], [interpreter, str(Path('/fixture/scripts') / name), *flags])
        self.assertTrue(all(options == {'cwd': Path('/fixture'), 'check': True} for _, options in calls))
        for command, _ in calls:
            self.assertEqual(command[0], node if command[1].endswith('.mjs') else sys.executable)

    def test_each_program_derivative_failure_stops_before_archives_or_later_derivatives(self):
        stages = ['build_declared_program_evidence.mjs', 'build_published_program_catalog.py', 'build_pinned_parent_artifacts.mjs',
                  'build_compiled_program_index.mjs',
                  'build_evidence_registry_fingerprint.mjs', 'build_published_program_discovery.mjs']
        for failed in stages:
            with self.subTest(stage=failed):
                calls = []
                def failing(command, **options):
                    calls.append(Path(command[1]).name)
                    if calls[-1] == failed:
                        raise subprocess.CalledProcessError(1, command)
                with self.assertRaises(subprocess.CalledProcessError):
                    build(Path('/fixture'), run=failing)
                self.assertEqual(calls[-1], failed)
                self.assertEqual([name for name in calls if name in stages], stages[:stages.index(failed) + 1])
                for later in ['archive_authored_sources.py', 'build_articles.py', 'build_access_exports.py',
                              'build_home_clusters.py', 'check_download_catalog.py']:
                    self.assertNotIn(later, calls)

    def test_preview_never_invokes_node_or_any_program_derivative(self):
        calls = []
        build(Path('/fixture'), run=lambda command, **options: calls.append(command), preview=True,
              node_executable='must-not-be-invoked')
        self.assertEqual(calls, [
            [sys.executable, str(Path('/fixture/scripts/build_experiments.py'))],
            [sys.executable, str(Path('/fixture/scripts/build_research_map.py'))],
            [sys.executable, str(Path('/fixture/scripts/build_home_clusters.py')), '.'],
        ])


if __name__ == '__main__':
    unittest.main()
