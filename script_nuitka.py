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

   # Base do comando Nuitka com Clang
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone", 
        f"--output-filename={exe_name}",
        "--output-dir=build",
        "--plugin-enable=pyside6",
        "--include-qt-plugins=imageformats,platforms",
        "--include-module=encodings",
        "--include-module=sqlite3",
        "--include-package=features",
        "--include-package=core",
        "--include-package=shared",
        "--include-package=fitz",
        "--include-package=pymupdf",
        "--clang",                      # A MÁGICA ACONTECE AQUI: Força o uso do LLVM/Clang
        "--lto=no",                     
        "--jobs=32",                    # Deixa o Ryzen 9 brilhar
        "--show-progress",              # Mostra o que está acontecendo no terminal
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
        cmd.append("--macos-app-mode=gui") 
        cmd.append("--static-libpython=no") # Resolve o problema da biblioteca estática ausente no Python do Mac
        
        # Verifica se o arquivo .icns existe na raiz
        icon_path = base_dir / "icone.icns"
        if icon_path.exists():
            cmd.append(f"--macos-app-icon={icon_path}")
            print("🎨 Ícone do macOS (.icns) detectado e adicionado.")
    
    cmd.append(str(main_file))
    
    try:
        os.makedirs("build", exist_ok=True)
        subprocess.run(cmd, check=True)
        print(f"\n✅ Compilação Nuitka concluída! O executável base está na pasta 'build'.")
        
        if sistema == "Darwin":
            print("\n🍎 Iniciando a criação do .DMG para macOS...")
            # O create-dmg precisa ser instalado no Mac M1 emprestado rodando: brew install create-dmg
            try:
                subprocess.run([
                    "create-dmg",
                    "--volname", "Instalador COMSOC",
                    "--window-pos", "200", "120",
                    "--window-size", "800", "400",
                    "--icon-size", "100",
                    "--hide-extension", f"{exe_name}.app",
                    "--app-drop-link", "600", "185",
                    "Projeto_ComSoc_Instalador.dmg",
                    "build/"
                ], check=True)
                print("✅ DMG gerado com sucesso na raiz do projeto!")
            except FileNotFoundError:
                print("⚠️ Aviso: 'create-dmg' não encontrado. Instale rodando no terminal do Mac: brew install create-dmg")
            except Exception as e:
                print(f"❌ Erro ao criar DMG (se o arquivo .dmg já existir, apague-o antes de recompilar): {e}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")

if __name__ == "__main__":
    build_app()

# Assim que a instalação terminar, você pode retomar a sequência de compilação normalmente:
#    flatpak-builder --repo=repo --force-clean build-dir com.leobelisario.ProjetoComSoc.yaml
#    flatpak build-bundle repo ProjetoComSoc.flatpak com.leobelisario.ProjetoComSoc
#    flatpak install --reinstall ProjetoComSoc.flatpak