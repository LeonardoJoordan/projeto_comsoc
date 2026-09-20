import subprocess
import sys
import platform
import os
import plistlib
from pathlib import Path

def build_app():
    print("🚀 Iniciando a compilação do FORNAX Forge com Nuitka...")
    
    # Define o ponto de entrada e caminhos
    base_dir = Path(__file__).parent.absolute()
    os.chdir(base_dir)
    main_file = base_dir / "main.py"
    exe_name = "FORNAX_Forge"

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
        "--include-package=pypdf",
        "--include-package=cryptography",
        "--include-data-dir=assets=assets",
        "--clang",                      # A MÁGICA ACONTECE AQUI: Força o uso do LLVM/Clang
        "--lto=no",                     
        f"--jobs={max(1, int(os.environ.get('FORNAX_BUILD_JOBS', min(4, os.cpu_count() or 1))))}",
        "--show-progress",              # Mostra o que está acontecendo no terminal
        "--follow-imports"
    ]

    # Injeção de argumentos específicos por Sistema Operacional
    sistema = platform.system()
    if sistema == "Windows":
        cmd.insert(cmd.index("--plugin-enable=pyside6") + 1, "--windows-console-mode=disable")
        
        # Verifica se o arquivo .ico existe na raiz
        icon_path = base_dir / "assets" / "icons" / "fornax-forge.ico"
        if icon_path.exists():
            cmd.append(f"--windows-icon-from-ico={icon_path}")
            print("🎨 Ícone do Windows (.ico) detectado e adicionado.")

    elif sistema == "Darwin": # macOS
        cmd.append("--macos-create-app-bundle")
        cmd.append("--macos-app-mode=gui") 
        cmd.append("--static-libpython=no") 
        cmd.append(f"--output-filename={exe_name}") # Garante o nome correto da pasta .app
        
        icon_path = base_dir / "assets" / "icons" / "fornax-forge_1024.png"
        if icon_path.exists():
            cmd.append(f"--macos-app-icon={icon_path}")
            print("🎨 Ícone do macOS (PNG 1024 px) detectado e adicionado.")
    
    cmd.append(str(main_file))
    
    try:
        os.makedirs("build", exist_ok=True)
        subprocess.run(cmd, check=True)
        print(f"\n✅ Compilação Nuitka concluída! O executável base está na pasta 'build'.")
        
        if sistema == "Darwin":
            print("\n🍎 Iniciando a criação do .DMG nativo para macOS...")
            app_path = Path("build") / f"{exe_name}.app"
            dmg_output = "FORNAX_Forge_Instalador.dmg"
            
            # Garante a renomeação caso o Nuitka ignore a flag externa
            if Path("build/main.app").exists():
                if app_path.exists():
                    import shutil
                    shutil.rmtree(app_path)
                os.rename("build/main.app", app_path)

            plist_path = app_path / "Contents" / "Info.plist"
            with plist_path.open("rb") as stream:
                plist = plistlib.load(stream)
            plist["CFBundleDocumentTypes"] = [{
                "CFBundleTypeName": "Modelo FORNAX Forge",
                "CFBundleTypeRole": "Editor",
                "LSHandlerRank": "Owner",
                "LSItemContentTypes": ["com.leobelisario.fornax-template"],
            }]
            plist["UTExportedTypeDeclarations"] = [{
                "UTTypeIdentifier": "com.leobelisario.fornax-template",
                "UTTypeDescription": "Modelo FORNAX Forge",
                "UTTypeConformsTo": ["public.data", "public.archive"],
                "UTTypeTagSpecification": {
                    "public.filename-extension": ["fornax"],
                    "public.mime-type": "application/x-fornax-template",
                },
            }]
            with plist_path.open("wb") as stream:
                plistlib.dump(plist, stream)
            
            try:
                subprocess.run([
                    "hdiutil", "create",
                    "-volname", "FORNAX Forge",
                    "-srcfolder", str(app_path),
                    "-ov", "-format", "UDZO",
                    dmg_output
                ], check=True)
                print(f"✅ DMG simplificado gerado com sucesso: {dmg_output}")
            except Exception as e:
                print(f"❌ Erro ao criar o DMG via hdiutil: {e}")
                raise

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")
        raise

if __name__ == "__main__":
    build_app()

# Assim que a instalação terminar, você pode retomar a sequência de compilação normalmente:
#    flatpak-builder --repo=repo --force-clean build-dir com.leobelisario.FornaxForge.yaml
#    flatpak build-bundle repo FORNAX_Forge.flatpak com.leobelisario.FornaxForge
#    flatpak install --reinstall FORNAX_Forge.flatpak
