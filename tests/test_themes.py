import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QSettings
from core.themes import theme_manager, themed_style, load_theme
from features.workspace.settings_dialogs import CustomThemeDialog, ThemeDialog
from features.generator.renderer import NativeRenderer
from tests.test_rendering_pipeline import template


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.manager = theme_manager()
        self.manager.select('dark')

    def tearDown(self):
        self.manager.select('dark')
        self.manager.settings = None

    def test_styles_update_and_document_swatch_is_preserved(self):
        text = QLabel()
        swatch = QLabel()
        themed_style(text, 'color: @text@; background: @field@;')
        themed_style(swatch, 'background: #ff0000; border: 1px solid @border@;')
        self.manager.select('light')
        self.assertIn('#20222a', text.styleSheet())
        self.assertIn('#ff0000', swatch.styleSheet())
        self.assertIn(self.manager.light['colors']['border'], swatch.styleSheet())

    def test_cancel_restores_original_custom_preview(self):
        dialog = ThemeDialog()
        self.assertFalse(hasattr(dialog, 'swatches'))
        self.assertEqual(-1, dialog.choice.findText('Personalizado…'))
        self.assertEqual('Criar tema', dialog.btn_create_theme.text())
        self.assertEqual(5, dialog.choice.count())
        dialog.choice.setCurrentIndex(dialog.choice.findData('light'))
        self.assertEqual('light', self.manager.theme_id)
        dialog.reject()
        self.assertEqual('dark', self.manager.theme_id)

    def test_advanced_dialog_previews_and_cancel_restores_theme(self):
        dialog = CustomThemeDialog()
        data = copy.deepcopy(self.manager.current)
        data['colors']['accent'] = '#123456'
        self.manager.select('dark', data)
        dialog.refresh_swatches()
        self.assertEqual('#123456', self.manager.color('accent'))
        dialog.reject()
        self.assertEqual(self.manager.dark['colors']['accent'], self.manager.color('accent'))

    def test_builtin_themes_have_readable_text_and_checkbox_borders(self):
        def luminance(hex_color):
            rgb = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
            return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))
        def contrast(a, b):
            low, high = sorted((luminance(a), luminance(b)))
            return (high + .05) / (low + .05)
        for name, theme in self.manager.builtins.items():
            colors = theme['colors']
            with self.subTest(theme=name):
                for background in ('surface', 'panel', 'field', 'button', 'selection'):
                    self.assertGreaterEqual(contrast(colors['text'], colors[background]), 4.5)
                self.assertGreaterEqual(contrast(colors['on_accent'], colors['accent']), 4.5)
                self.assertGreaterEqual(contrast(colors['border_strong'], colors['field']), 3)
                self.assertGreaterEqual(contrast(colors['border_strong'], colors['surface']), 3)
                self.manager.select(name)
                self.assertIn('QCheckBox::indicator:checked', self.app.styleSheet())

    def test_advanced_dialog_saves_named_profile(self):
        with tempfile.TemporaryDirectory() as folder, patch('core.themes.get_app_data_dir', return_value=Path(folder)):
            dialog = CustomThemeDialog()
            dialog.name.setText('Institucional')
            dialog.save()
            self.assertTrue(dialog.saved_id.startswith('custom-'))
            self.assertTrue((Path(folder) / 'themes' / f'{dialog.saved_id}.json').is_file())

    def test_custom_theme_roundtrip_and_invalid_fallback(self):
        with tempfile.TemporaryDirectory() as folder, patch('core.themes.get_app_data_dir', return_value=Path(folder)):
            colors = dict(self.manager.current['colors'], accent='#006699')
            settings = QSettings(str(Path(folder)/'settings.ini'), QSettings.Format.IniFormat)
            self.manager.initialize(settings)
            identifier = self.manager.save_custom('Meu tema', colors)
            self.manager.persist()
            self.manager.select('dark')
            self.manager.initialize(settings)
            self.assertEqual(identifier, self.manager.theme_id)
            self.assertEqual('#006699', self.manager.color('accent'))
            (Path(folder)/'themes'/(identifier+'.json')).write_text('{invalid')
            self.manager.initialize(settings)
            self.assertEqual('dark', self.manager.theme_id)

    def test_partial_theme_defaults_and_invalid_color(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'theme.json'
            path.write_text(json.dumps({'version':1,'colors':{'accent':'#112233'}}))
            data = load_theme(path, self.manager.dark['colors'])
            self.assertEqual(self.manager.color('text'), data['colors']['text'])
            path.write_text(json.dumps({'version':1,'colors':{'accent':'red; border:none'}}))
            with self.assertRaises(ValueError):
                load_theme(path, self.manager.dark['colors'])

    def test_rendering_is_identical_across_themes(self):
        with tempfile.TemporaryDirectory() as folder:
            data = template()
            data['__model_dir'] = folder
            original = copy.deepcopy(data)
            before = NativeRenderer(data).render_to_qimage({}, {})
            for theme_id in self.manager.builtins:
                with self.subTest(theme=theme_id):
                    self.manager.select(theme_id)
                    after = NativeRenderer(data).render_to_qimage({}, {})
                    self.assertEqual(before, after)
                    self.assertEqual(original, data)


if __name__ == '__main__':
    unittest.main()
