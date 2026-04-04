import subprocess
import sys
import os
from pathlib import Path

def build_app():
    print("🚀 Iniciando a blindagem e compilação do C.O.M.S.O.C. com Nuitka...")
    
    # Define o ponto de entrada e caminhos
    base_dir = Path(__file__).parent.absolute()
    main_file = base_dir / "main.py"
    exe_name = "COMSOC_OFICIAL"

    # Comando corrigido
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        f"--output-filename={exe_name}",
        "--output-dir=build",
        
        # Plugins e Interface
        "--plugin-enable=pyside6",
        "--windows-console-mode=disable",
        
        # Blindagem de Sistema (conforme seu script de sucesso)
        "--include-module=encodings",
        "--include-module=sqlite3",
        
        # Inclusão da Arquitetura de Features
        "--include-package=features",
        "--include-package=core",
        "--include-package=shared",
        
        # Otimização de busca de módulos
        "--follow-imports",
        
        str(main_file)
    ]
    
    try:
        os.makedirs("build", exist_ok=True)
        # Executa o processo
        subprocess.run(cmd, check=True)
        print(f"\n✅ Missão Cumprida! O executável '{exe_name}' está pronto na pasta 'build'.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")

if __name__ == "__main__":
    build_app()