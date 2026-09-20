"""Verifica a seleção real do ícone, não apenas o nome retornado pelo MIME."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_mime_icon_does_not_lose_to_the_themes_generic_document(tmp_path):
    if sys.platform != 'linux' or not Path('/usr/bin/python3').exists():
        pytest.skip('Exige GTK/GIO do Linux')
    for command in ('update-mime-database', 'update-desktop-database'):
        if not shutil.which(command):
            pytest.skip(f'{command} indisponível')
    probe = subprocess.run(['/usr/bin/python3', '-c',
                            'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk'],
                           capture_output=True)
    if probe.returncode:
        pytest.skip('GTK 3/PyGObject indisponível')
    env = dict(os.environ, XDG_DATA_HOME=str(tmp_path / 'share'), XDG_CACHE_HOME=str(tmp_path / 'cache'))
    subprocess.run([sys.executable, str(ROOT / 'tools/install_linux_integration.py'),
                    '--no-default'], env=env, check=True, capture_output=True)
    subprocess.run(['/usr/bin/python3', '-c', '''
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
mime = 'application/x-fornax-template'
assert Gio.content_type_guess('example.fornax', None)[0] == mime
assert Gio.content_type_guess('example.fornax.bak', None)[0] != mime
theme = Gtk.IconTheme.new()
theme.set_custom_theme('Adwaita')
for size in (32, 64, 96, 128):
    icon = theme.lookup_by_gicon(Gio.content_type_get_icon(mime), size, 0)
    assert icon is not None
    assert 'FornaxForge' in icon.get_filename(), icon.get_filename()
    assert icon.load_icon().get_width() > 0
'''], env=env, check=True, capture_output=True)
