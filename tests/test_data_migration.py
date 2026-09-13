import tempfile
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
            self.assertEqual("asset", (result / "cartao" / "imagem.png").read_text())
            self.assertEqual("legado", (legacy / "models" / "cartao" / "template_v3.json").read_text())

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
