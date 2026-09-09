#!/usr/bin/env python3
"""
Script para download de modelos Qwen GGUF do Hugging Face.

Uso:
    python download_models.py qwen2.5_32b Q4_K_M
    python download_models.py qwen1.5_32b Q5_K_M
    python download_models.py --list
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download, list_repo_files
except ImportError:
    print("❌ huggingface_hub não instalado. Execute: pip install -r requirements.txt")
    sys.exit(1)


def load_config() -> dict:
    """Carrega configurações dos modelos."""
    config_path = Path(__file__).parent.parent / "configs" / "presets.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configs não encontrado: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_models():
    """Lista todos os modelos disponíveis."""
    config = load_config()
    
    print("\n📦 Modelos Disponíveis:\n")
    print("=" * 70)
    
    for key, model in config["models"].items():
        print(f"\n🔹 {model['name']} ({key})")
        print(f"   Repositório: {model['repo']}")
        print(f"   Camadas: {model['total_layers']}")
        print(f"   Recomendado: {model['recommended']}")
        print(f"   Quantizações disponíveis:")
        
        for quant, filename in model["files"].items():
            print(f"      - {quant}: {filename}")
    
    print("\n" + "=" * 70)
    print("\nExemplos de uso:")
    print("  python download_models.py qwen2.5_32b Q4_K_M")
    print("  python download_models.py qwen1.5_32b Q5_K_M")


def download_model(model_key: str, quantization: str):
    """Baixa um modelo específico."""
    config = load_config()
    
    # Encontrar modelo
    model_info = None
    for key, model in config["models"].items():
        if model_key.lower() in key.lower() or key.lower() in model_key.lower():
            model_info = model
            break
    
    if not model_info:
        available = ", ".join(config["models"].keys())
        print(f"❌ Modelo '{model_key}' não encontrado.")
        print(f"Modelos disponíveis: {available}")
        sys.exit(1)
    
    # Encontrar arquivo de quantização
    if quantization not in model_info["files"]:
        available = ", ".join(model_info["files"].keys())
        print(f"❌ Quantização '{quantization}' não disponível para este modelo.")
        print(f"Quantizações disponíveis: {available}")
        sys.exit(1)
    
    filename = model_info["files"][quantization]
    repo_id = model_info["repo"]
    
    # Diretório de destino
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    print(f"\n📥 Download iniciando...")
    print(f"   Modelo: {model_info['name']}")
    print(f"   Repositório: {repo_id}")
    print(f"   Quantização: {quantization}")
    print(f"   Arquivo: {filename}")
    print(f"   Destino: {models_dir}")
    print("\n⏳ Isso pode levar alguns minutos dependendo da sua conexão...\n")
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=models_dir,
            local_dir_use_symlinks=False,
        )
        
        print(f"\n✅ Download concluído com sucesso!")
        print(f"   Arquivo salvo em: {downloaded_path}")
        
        # Mostrar tamanho do arquivo
        file_size = Path(downloaded_path).stat().st_size
        size_gb = file_size / (1024 ** 3)
        print(f"   Tamanho: {size_gb:.2f} GB")
        
    except Exception as e:
        print(f"\n❌ Erro no download: {e}")
        print("\nVerifique:")
        print("  - Sua conexão com a internet")
        print("  - Se há espaço suficiente em disco")
        print("  - Se o repositório existe no Hugging Face")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download de modelos Qwen GGUF do Hugging Face"
    )
    
    parser.add_argument(
        "model",
        nargs="?",
        help="Chave do modelo (ex: qwen2.5_32b, qwen1.5_32b)"
    )
    
    parser.add_argument(
        "quantization",
        nargs="?",
        help="Tipo de quantização (ex: Q4_K_M, Q5_K_M, Q6_K)"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Listar modelos disponíveis"
    )
    
    args = parser.parse_args()
    
    if args.list or (not args.model and not args.quantization):
        list_models()
        return
    
    if not args.model or not args.quantization:
        print("❌ É necessário especificar modelo e quantização.")
        print("\nUse --list para ver opções disponíveis.")
        print("\nExemplo:")
        print("  python download_models.py qwen2.5_32b Q4_K_M")
        sys.exit(1)
    
    download_model(args.model, args.quantization)


if __name__ == "__main__":
    main()
