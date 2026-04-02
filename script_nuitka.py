import subprocess
import sys
from pathlib import Path

def build_app():
    print("Iniciando configuração de compilação do ComSoc com Nuitka...")
    
    # Flags base para empacotamento PySide6
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",                     # Cria uma pasta com todos os arquivos necessários
        "--plugin-enable=pyside6",          # Plugin essencial para mapear as bibliotecas do Qt
        "--windows-console-mode=disable",   # Oculta a janela preta de terminal no Windows
        "--output-dir=build",               # Pasta de destino
        "main.py"                           # Ponto de entrada da aplicação
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Compilação concluída com sucesso. Verifique a pasta 'build/main.dist'.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro durante a compilação: {e}")

if __name__ == "__main__":
    build_app()