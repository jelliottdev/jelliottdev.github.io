"""Pipeline failure controls without running the expensive source census."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('corpus_pipeline',ROOT/'experiments/records/corpus-prefix-census/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)


class PipelineControls(unittest.TestCase):
    def test_stage_order_and_offline_arguments(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(pipeline.subprocess,'run') as run:
            source=Path(tmp)/'source';source.mkdir()
            pipeline.reproduce(source,Path(tmp)/'output')
            calls=run.call_args_list
            self.assertEqual([Path(c.args[0][1]).name for c in calls],['run_corpus_prefixes.py','check_corpus_prefixes.py','compare_corpus_prefixes.py','check_corpus_comparison.py','render_corpus_comparison.py'])
            self.assertTrue(all(c.kwargs['check'] for c in calls))
            self.assertTrue(all('--allow-fetch' not in c.args[0] for c in calls))

    def test_failure_stops_every_later_stage(self):
        for failure in range(5):
            with self.subTest(stage=failure),tempfile.TemporaryDirectory() as tmp:
                source=Path(tmp)/'source';source.mkdir()
                effects=[subprocess.CompletedProcess([],0)]*failure+[subprocess.CalledProcessError(1,['fixture'])]
                with patch.object(pipeline.subprocess,'run',side_effect=effects) as run:
                    with self.assertRaises(subprocess.CalledProcessError):pipeline.reproduce(source,Path(tmp)/'output')
                    self.assertEqual(run.call_count,failure+1)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(pipeline.subprocess,'run') as run:
            source=Path(tmp)/'source';source.mkdir();output=Path(tmp)/'output';output.mkdir()
            marker=output/'report.json';marker.write_text('fixture',encoding='utf-8')
            with self.assertRaises(ValueError):pipeline.reproduce(source,output)
            self.assertEqual(marker.read_text(encoding='utf-8'),'fixture');run.assert_not_called()


if __name__=='__main__':unittest.main()
