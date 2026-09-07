import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QImage
from features.editor_qml.bridge import EditorBridge

APP = QApplication.instance() or QApplication([])
ROOT = Path(__file__).resolve().parents[3]


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.bridge = EditorBridge()
        self.errors = []
        self.bridge.error.connect(self.errors.append)

    def tearDown(self):
        self.bridge._render_timer.stop()
        self.temp.cleanup()

    def fixture(self, name="teste2"):
        target = self.base / name
        shutil.copytree(ROOT / "models" / name, target)
        return target / "template_v3.json"

    def test_legacy_roundtrip_preserves_unknown_data_and_background(self):
        path = self.fixture()
        data = json.loads(path.read_text())
        data["future_metadata"] = {"keep": [1, 2, 3]}
        path.write_text(json.dumps(data))
        self.assertTrue(self.bridge.load(str(path)))
        self.bridge.select("text:0")
        self.bridge.setValue("font_color", "#123456")
        self.assertTrue(self.bridge.save())
        saved = json.loads(path.read_text())
        self.assertEqual(saved["background_path"], data["background_path"])
        self.assertEqual(saved.get("bg_props"), data.get("bg_props"))
        self.assertEqual(saved["future_metadata"], data["future_metadata"])
        self.assertEqual(saved.get("imposition_settings"), data.get("imposition_settings"))
        self.assertEqual(saved["boxes"][0]["font_color"], "#123456")
        self.assertFalse(self.bridge.state["dirty"])
        self.bridge.undo()
        self.assertTrue(self.bridge.state["dirty"])
        self.bridge.redo()
        self.assertFalse(self.bridge.state["dirty"])

    def test_geometry_history_lock_and_duplicate(self):
        self.bridge.addItem("text")
        self.bridge.moveSelected(90, 100)
        self.bridge.resizeItem("text:0", 600, 500)
        self.assertEqual(self.bridge.state["selected"]["h"], 200)
        self.bridge.setValue("locked", True)
        self.bridge.moveSelected(500, 500)
        self.assertEqual(self.bridge.state["selected"]["x"], 90)
        self.bridge.setValue("visible", False)
        self.assertFalse(self.bridge.state["selected"]["visible"])
        self.bridge.setValue("locked", False)
        self.bridge.duplicateSelected()
        self.assertEqual(len(self.bridge.state["layers"]), 2)
        self.bridge.deleteSelected()
        self.assertEqual(len(self.bridge.state["layers"]), 1)
        self.bridge.undo()
        self.assertEqual(len(self.bridge.state["layers"]), 2)

    def test_assets_save_as_reopen_and_render(self):
        source = self.fixture()
        original = source.read_bytes()
        self.assertTrue(self.bridge.load(str(source)))
        self.bridge.render()
        first = bytes(self.bridge.provider.image.constBits())
        target = self.base / "copy" / "template_v3.json"
        self.assertTrue(self.bridge.save_to(target, "Cópia"), self.errors)
        self.assertEqual(source.read_bytes(), original)
        saved = json.loads(target.read_text())
        self.assertTrue((target.parent / saved["background_path"]).exists())
        for item in saved["signatures"]:
            self.assertTrue((target.parent / item["path"]).exists())
        self.assertTrue(self.bridge.load(str(target)))
        self.bridge.render()
        self.assertEqual(bytes(self.bridge.provider.image.constBits()), first)
        self.assertFalse(self.errors)

    def test_import_image_and_signature_uses_legacy_collections(self):
        asset = self.base / "image.png"
        image = QImage(80, 40, QImage.Format_ARGB32)
        image.fill(QColor("red"))
        image.save(str(asset))
        self.assertTrue(self.bridge.add_asset("image", str(asset)))
        self.assertTrue(self.bridge.add_asset("signature", str(asset)))
        self.assertTrue(self.bridge.save_to(self.base / "new" / "template_v3.json"))
        self.assertEqual(len(self.bridge._data["images"]), 1)
        self.assertEqual(len(self.bridge._data["signatures"]), 1)
        self.assertIsNone(self.bridge._data["background_path"])

    def test_text_variables_link_and_field_order(self):
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p><b>{Nome}</b> |Cargo: {Cargo}|</p>")
        self.assertEqual(self.bridge.state["fields"], ["Nome", "Cargo"])
        self.bridge.setValue("has_link", True)
        link = self.bridge.state["selected"]["link_key"]
        self.assertIn(link, self.bridge.state["fields"])
        self.bridge.moveField(0, 1)
        self.assertEqual(self.bridge.state["fields"][:2], ["Cargo", "Nome"])
        self.bridge.setValue("has_link", False)
        self.assertNotIn(link, self.bridge.state["fields"])
        self.bridge.setValue("html", "<p>Texto simples</p>")
        self.bridge.formatText("Negrito")
        self.assertTrue(self.bridge.state["selected"]["bold"])

    def test_guides_and_invalid_numbers(self):
        self.bridge.addGuide(True)
        self.bridge.moveGuide(0, 20)
        self.assertEqual(self.bridge.state["guides"][0]["pos"], 20)
        self.bridge.guideOption("guidelines_locked", True)
        self.bridge.moveGuide(0, 40)
        self.assertEqual(self.bridge.state["guides"][0]["pos"], 20)
        self.bridge.addItem("text")
        for value in ("nan", "inf", "-10", "0", "bad"):
            self.bridge.setValue("w", value)
        self.assertEqual(self.bridge.state["selected"]["w"], 300)

    def test_external_change_is_not_overwritten(self):
        path = self.fixture("teste")
        self.bridge.load(str(path))
        self.bridge.addItem("text")
        externally_changed = path.read_bytes() + b"\n "
        path.write_bytes(externally_changed)
        self.assertFalse(self.bridge.save())
        self.assertEqual(path.read_bytes(), externally_changed)
        self.assertTrue(self.bridge.state["dirty"])

    def test_invalid_load_keeps_current_document(self):
        self.bridge.addItem("text")
        before = self.bridge.state
        path = self.base / "bad.json"
        path.write_text('{"canvas_size": {"w": 0, "h": 20}}')
        self.assertFalse(self.bridge.load(str(path)))
        self.assertEqual(before["layers"], self.bridge.state["layers"])

    def test_saved_model_opens_in_untouched_legacy_editor(self):
        from features.editor.editor_window import EditorWindow
        self.bridge.addItem("text")
        self.bridge.setValue("html", "<p>{Nome} <b>Teste</b></p>")
        self.bridge.setValue("font_color", "#654321")
        path = self.base / "compat" / "template_v3.json"
        self.assertTrue(self.bridge.save_to(path))
        legacy = EditorWindow()
        legacy.load_from_json(str(path))
        state = legacy.get_current_scene_state()
        self.assertEqual(len(state["boxes"]), 1)
        self.assertEqual(state["boxes"][0]["font_color"], "#654321")
        self.assertEqual(state["placeholders"], ["Nome"])
        legacy.deleteLater()


if __name__ == "__main__":
    unittest.main()
