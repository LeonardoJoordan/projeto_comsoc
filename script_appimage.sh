#!/bin/bash
set -e

echo "🔧 Montando AppDir e gerando AppImage..."

DIST_DIR="build/main.dist"
APP_DIR="COMSOC.AppDir"
USR_BIN="$APP_DIR/usr/bin"
USR_LIB="$APP_DIR/usr/lib"
PYSIDE6_VENV="venv/lib/python3.13/site-packages/PySide6"

# Limpa e recria o AppDir
rm -rf "$APP_DIR"
mkdir -p "$USR_BIN"
mkdir -p "$USR_LIB"

# Copia tudo do main.dist para usr/bin
echo "📦 Copiando binário e libs do Nuitka..."
cp -r "$DIST_DIR"/. "$USR_BIN/"

# Copia as libs do Qt do venv do PySide6
echo "📦 Copiando libs do Qt do venv..."
cp -L "$PYSIDE6_VENV/Qt/lib/libQt6"* "$USR_LIB/"

# Copia os plugins de plataforma do venv
echo "📦 Copiando plugins de plataforma..."
mkdir -p "$USR_BIN/platforms"
cp -L "$PYSIDE6_VENV/Qt/plugins/platforms/"* "$USR_BIN/platforms/"

# Cria o AppRun
cat > "$APP_DIR/AppRun" << 'EOF'
#!/bin/sh
SELF=$(dirname $(readlink -f "$0"))
export PATH="$SELF/usr/bin:$PATH"
export LD_LIBRARY_PATH="$SELF/usr/lib:$SELF/usr/bin:$LD_LIBRARY_PATH"
export QT_PLUGIN_PATH="$SELF/usr/bin/PySide6/qt-plugins"
export QT_QPA_PLATFORM=xcb
exec "$SELF/usr/bin/COMSOC_OFICIAL" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Cria o .desktop
cat > "$APP_DIR/app.desktop" << 'EOF'
[Desktop Entry]
Name=COMSOC
Exec=COMSOC_OFICIAL
Icon=app
Type=Application
Categories=Utility;
EOF

# Ícone placeholder
touch "$APP_DIR/app.png"

# Mostra tamanho antes de gerar
echo ""
echo "📊 Tamanho do AppDir: $(du -sh $APP_DIR | cut -f1)"

# Gera o AppImage
echo ""
echo "📦 Gerando AppImage..."
ARCH=x86_64 ./appimagetool "$APP_DIR" Projeto_ComSoc.AppImage

echo ""
echo "✅ Projeto_ComSoc.AppImage gerado com sucesso!"