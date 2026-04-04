import subprocess
import sys
import os
from pathlib import Path

def build_app():
    print("🚀 Iniciando a blindagem e compilação do C.O.M.S.O.C. com Nuitka...")
    
    # Define o ponto de entrada e o nome do executável final
    base_dir = Path(__file__).parent
    main_file = base_dir / "main.py"
    exe_name = "COMSOC_OFICIAL"

    # Comando Nuitka com as técnicas do seu script de sucesso e blindagem Linux
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",                  # Empacota todas as dependências 
        "--onefile",                     # Gera um único executável para facilitar a distribuição 
        f"--output-filename={exe_name}", # Nome personalizado do binário 
        "--output-dir=build",            # Pasta de destino 
        
        # --- Plugins e Interface ---
        "--plugin-enable=pyside6",       # Plugin essencial para mapear o Qt
        "--windows-console-mode=disable", # Remove o terminal em background (caso rode no Windows)
        
        # --- Blindagem e Inclusão de Assets (Técnicas do script 2) ---
        "--include-module=encodings",    # Vacina contra bugs de acentuação (UTF-8) 
        "--include-module=sqlite3",      # Garante suporte a banco de dados se necessário 
        
        # --- Compressão Extrema ---
        "--zstd-compression-level=3",    # Usa a lib zstandard para reduzir o tamanho final
        
        # --- Inclusão de Pastas do Projeto (Features) ---
        # Como usamos Vertical Slicing, garantimos que todas as pastas de domínio entrem
        "--include-package=features",
        "--include-package=core",
        "--include-package=shared",
        
        # --- Inclusão de Dados Externos ---
        # Se houver uma pasta de modelos padrão ou ícones, mapeamos aqui
        # "--include-data-dir=models=models", 
        
        str(main_file)
    ]
    
    try:
        # Garante que a pasta de build exista
        os.makedirs("build", exist_ok=True)
        
        subprocess.run(cmd, check=True)
        print(f"\n✅ Missão Cumprida! O executável '{exe_name}' está pronto na pasta 'build'.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")

if __name__ == "__main__":
    build_app()