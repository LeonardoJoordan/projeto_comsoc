import subprocess
import sys
import platform
import os
from pathlib import Path

def build_app():
    print("🚀 Iniciando a blindagem e compilação do C.O.M.S.O.C. com Nuitka...")
    
    # Define o ponto de entrada e caminhos
    base_dir = Path(__file__).parent.absolute()
    main_file = base_dir / "main.py"
    exe_name = "Projeto ComSoc"

   # Base do comando Nuitka
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # <-- Alteração 1: Troca de --onefile para --standalone
        f"--output-filename={exe_name}",
        "--output-dir=build",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=imageformats,platforms",
        "--include-module=encodings",
        "--include-module=sqlite3",
        "--include-package=features",
        "--include-package=core",
        "--include-package=shared",
        "--follow-imports"
    ]

    # Injeção de argumentos específicos por Sistema Operacional
    sistema = platform.system()
    if sistema == "Windows":
        cmd.insert(cmd.index("--plugin-enable=pyside6") + 1, "--windows-console-mode=disable")
        
        # Verifica se o arquivo .ico existe na raiz
        icon_path = base_dir / "icone.ico"
        if icon_path.exists():
            cmd.append(f"--windows-icon-from-ico={icon_path}")
            print("🎨 Ícone do Windows (.ico) detectado e adicionado.")

    elif sistema == "Darwin": # macOS
        cmd.append("--macos-create-app-bundle")
        
        # Verifica se o arquivo .icns existe na raiz
        icon_path = base_dir / "icone.icns"
        if icon_path.exists():
            cmd.append(f"--macos-app-icon={icon_path}")
            print("🎨 Ícone do macOS (.icns) detectado e adicionado.")
    
    cmd.append(str(main_file))
    
    try:
        os.makedirs("build", exist_ok=True)
        subprocess.run(cmd, check=True)
        print(f"\n✅ Missão Cumprida! O executável '{exe_name}' está pronto na pasta 'build'.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")

if __name__ == "__main__":
    build_app()

# Assim que a instalação terminar, você pode retomar a sequência de compilação normalmente:
#    flatpak-builder --repo=repo --force-clean build-dir com.leobelisario.ProjetoComSoc.yaml
#    flatpak build-bundle repo ProjetoComSoc.flatpak com.leobelisario.ProjetoComSoc
#    flatpak install --reinstall ProjetoComSoc.flatpak