import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_docs.py"
SPEC = importlib.util.spec_from_file_location("sync_docs", SCRIPT)
sync_docs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = sync_docs
SPEC.loader.exec_module(sync_docs)


class SynchronizationTest(unittest.TestCase):
    def project(self, source: Path, destination: Path, required: bool = True):
        return sync_docs.Project(
            id="test-project",
            title="Test project",
            repository=source.parent,
            source=source,
            destination=destination,
            required=required,
        )

    def test_directory_sync_is_idempotent_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            (source / "guide.md").write_text("first\n", encoding="utf-8")
            project = self.project(source, destination)

            self.assertTrue(sync_docs.synchronize(project, check=False))
            self.assertEqual("first\n", (destination / "guide.md").read_text(encoding="utf-8"))
            self.assertTrue(sync_docs.synchronize(project, check=True))

            (source / "guide.md").write_text("second\n", encoding="utf-8")
            self.assertFalse(sync_docs.synchronize(project, check=True))
            self.assertTrue(sync_docs.synchronize(project, check=False))
            self.assertEqual("second\n", (destination / "guide.md").read_text(encoding="utf-8"))

    def test_individual_file_can_be_synchronized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            destination = root / "nested" / "destination.md"
            source.write_text("content\n", encoding="utf-8")

            self.assertTrue(sync_docs.synchronize(self.project(source, destination), check=False))
            self.assertEqual(source.read_bytes(), destination.read_bytes())

    def test_optional_missing_source_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.project(root / "missing", root / "destination", required=False)
            self.assertTrue(sync_docs.synchronize(project, check=True))

    def test_stale_optional_output_is_detected_and_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "destination"
            destination.mkdir()
            (destination / "stale.md").write_text("stale\n", encoding="utf-8")
            project = self.project(root / "missing", destination, required=False)

            self.assertFalse(sync_docs.synchronize(project, check=True))
            self.assertTrue(sync_docs.synchronize(project, check=False))
            self.assertFalse(destination.exists())

    def test_required_missing_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.project(root / "missing", root / "destination")
            with self.assertRaises(FileNotFoundError):
                sync_docs.synchronize(project, check=False)


if __name__ == "__main__":
    unittest.main()
