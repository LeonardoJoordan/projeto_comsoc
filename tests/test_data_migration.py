import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from core import paths
from core import settings as app_settings


class DataMigrationTests(unittest.TestCase):
    def test_legacy_data_is_copied_without_overwriting_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            legacy = base / paths.LEGACY_APP_ID
            current = base / paths.APP_ID
            (legacy / "models" / "cartao").mkdir(parents=True)
            (current / "models" / "cartao").mkdir(parents=True)
            (legacy / "models" / "cartao" / "template_v3.json").write_text("legado")
            (legacy / "models" / "cartao" / "imagem.png").write_text("asset")
            (current / "models" / "cartao" / "template_v3.json").write_text("fornax")

            with patch.dict("os.environ", {"XDG_DATA_HOME": temp_dir}), patch(
                "core.paths.platform.system", return_value="Linux"
            ):
                result = paths.get_models_dir()

            self.assertEqual(current / "models", result)
            self.assertEqual("fornax", (result / "cartao" / "template_v3.json").read_text())
            self.assertFalse((result / "cartao" / "imagem.png").exists())
            self.assertEqual("legado", (legacy / "models" / "cartao" / "template_v3.json").read_text())

    def test_deleted_model_is_not_restored(self):
        with tempfile.TemporaryDirectory() as root, patch.dict("os.environ", {"XDG_DATA_HOME": root}), patch("core.paths.platform.system", return_value="Linux"):
            legacy = Path(root) / paths.LEGACY_APP_ID / "models" / "cartao"
            legacy.mkdir(parents=True)
            (legacy / "template_v3.json").write_text("original")
            target = paths.get_models_dir() / "cartao"
            self.assertEqual("original", (target / "template_v3.json").read_text())
            shutil.rmtree(target)
            self.assertFalse((paths.get_models_dir() / "cartao").exists())
            self.assertTrue(legacy.exists())

    def test_interrupted_copy_is_not_published_and_can_resume(self):
        with tempfile.TemporaryDirectory() as root, patch.dict("os.environ", {"XDG_DATA_HOME": root}), patch("core.paths.platform.system", return_value="Linux"):
            legacy = Path(root) / paths.LEGACY_APP_ID / "models" / "cartao"
            legacy.mkdir(parents=True)
            (legacy / "template_v3.json").write_text("original")
            (legacy / "asset").write_text("image")
            target = Path(root) / paths.APP_ID / "models" / "cartao"
            with patch("core.paths._verified_copy", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    paths.get_models_dir()
            self.assertFalse(target.exists())
            paths.get_models_dir()
            self.assertEqual("original", (target / "template_v3.json").read_text())
            self.assertEqual("image", (target / "asset").read_text())

    def test_settings_migration_preserves_existing_values(self):
        class FakeSettings:
            def __init__(self, values):
                self.values = values

            def value(self, key, default=None, type=None):
                value = self.values.get(key, default)
                return type(value) if type and value is not None else value

            def allKeys(self):
                return list(self.values)

            def setValue(self, key, value):
                self.values[key] = value

            def sync(self):
                pass

        current = FakeSettings({"dark_mode": False})
        legacy = FakeSettings({"dark_mode": True, "geometry": b"old"})
        with patch("core.settings.QSettings", side_effect=[current, legacy]):
            result = app_settings.get_app_settings()

        self.assertIs(result, current)
        self.assertFalse(current.values["dark_mode"])
        self.assertEqual(b"old", current.values["geometry"])
        self.assertTrue(current.values[app_settings.MIGRATION_MARKER])


if __name__ == "__main__":
    unittest.main()
