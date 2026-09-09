#!/usr/bin/env python3
"""
Script principal para rodar Qwen 2.5 32B com otimizações para hardware limitado.
Suporta GPUs com 8GB-10GB VRAM e 16GB RAM.

Uso:
    python run_qwen.py --model models/Qwen2.5-32B-Instruct-Q4_K_M.gguf --gpu-layers 35
    python run_qwen.py --preset gpu_8gb_ram_16gb
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from llama_cpp import Llama
except ImportError:
    print("❌ llama-cpp-python não instalado. Execute: pip install -r requirements.txt")
    sys.exit(1)


def load_preset(preset_name: str) -> dict:
    """Carrega preset de configuração."""
    config_path = Path(__file__).parent.parent / "configs" / "presets.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de presets não encontrado: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        configs = json.load(f)
    
    if preset_name not in configs["presets"]:
        available = ", ".join(configs["presets"].keys())
        raise ValueError(f"Preset '{preset_name}' não encontrado. Disponíveis: {available}")
    
    return configs["presets"][preset_name]


def get_model_info(model_name: str) -> dict:
    """Obtém informações do modelo."""
    config_path = Path(__file__).parent.parent / "configs" / "presets.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        configs = json.load(f)
    
    for key, info in configs["models"].items():
        if model_name.lower() in key.lower() or key.lower() in model_name.lower():
            return info
    
    return {"total_layers": 64, "recommended": "Q4_K_M"}


def create_llama_instance(
    model_path: str,
    gpu_layers: int = 35,
    ctx_size: int = 4096,
    batch_size: int = 1,
    threads: int = 8,
    threads_batch: int = 4,
    flash_attn: bool = True,
    main_gpu: int = 0,
    verbose: bool = False,
) -> Llama:
    """Cria instância do Llama com configurações otimizadas."""
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
    
    print(f"📦 Carregando modelo: {model_path}")
    print(f"⚙️  Configurações:")
    print(f"   - GPU Layers: {gpu_layers}")
    print(f"   - Context Size: {ctx_size}")
    print(f"   - Batch Size: {batch_size}")
    print(f"   - Threads: {threads}")
    print(f"   - Flash Attention: {flash_attn}")
    
    llm = Llama(
        model_path=model_path,
        n_ctx=ctx_size,
        n_batch=batch_size,
        n_gpu_layers=gpu_layers,
        n_threads=threads,
        n_threads_batch=threads_batch,
        flash_attn=flash_attn,
        main_gpu=main_gpu,
        verbose=verbose,
        # Otimizações de memória
        use_mlock=True,  # Previne swapping
        use_mmap=True,   # Mapeamento de memória
    )
    
    print("✅ Modelo carregado com sucesso!")
    return llm


def chat_loop(llm: Llama, system_prompt: Optional[str] = None):
    """Loop interativo de chat."""
    
    default_system = "Você é um assistente útil e prestativo."
    system = system_prompt or default_system
    
    messages = [
        {"role": "system", "content": system}
    ]
    
    print("\n" + "="*60)
    print("🤗 Chat iniciado! Digite 'quit' ou 'exit' para sair.")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("👤 Você: ").strip()
            
            if user_input.lower() in ["quit", "exit", "sair"]:
                print("\n👋 Até logo!")
                break
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            print("\n🤖 Assistente: ", end="", flush=True)
            
            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9,
                stream=True,
            )
            
            full_response = ""
            for chunk in response:
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_response += content
            
            print("\n")
            messages.append({"role": "assistant", "content": full_response})
            
            # Manter histórico limitado para economizar memória
            if len(messages) > 20:
                messages = [messages[0]] + messages[-19:]
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrrompido pelo usuário.")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")


def benchmark(llm: Llama, prompt: str = "Explique o que é inteligência artificial em detalhes."):
    """Benchmark simples de performance."""
    import time
    
    print("\n🔍 Executando benchmark...")
    print(f"Prompt: {prompt[:50]}...\n")
    
    start_time = time.time()
    token_count = 0
    
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        stream=True,
    )
    
    for chunk in response:
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                token_count += 1
                print(content, end="", flush=True)
    
    elapsed = time.time() - start_time
    tokens_per_second = token_count / elapsed if elapsed > 0 else 0
    
    print(f"\n\n📊 Resultados:")
    print(f"   - Tokens gerados: {token_count}")
    print(f"   - Tempo total: {elapsed:.2f}s")
    print(f"   - Tokens/segundo: {tokens_per_second:.2f}")
    print(f"   - Meta (21-24 t/s): {'✅ Atingida' if 21 <= tokens_per_second <= 24 else '⚠️ Fora da meta'}")


def main():
    parser = argparse.ArgumentParser(
        description="Rodar Qwen 2.5 32B otimizado para hardware limitado"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="Caminho para o modelo GGUF"
    )
    
    parser.add_argument(
        "--preset", "-p",
        type=str,
        choices=["gpu_8gb_ram_16gb", "gpu_10gb_ram_16gb", "gpu_10gb_high_quality", "cpu_only"],
        help="Usar preset de configuração"
    )
    
    parser.add_argument("--gpu-layers", "-gl", type=int, default=None)
    parser.add_argument("--ctx-size", "-c", type=int, default=None)
    parser.add_argument("--batch-size", "-b", type=int, default=None)
    parser.add_argument("--threads", "-t", type=int, default=None)
    parser.add_argument("--benchmark", action="store_true", help="Executar benchmark")
    parser.add_argument("--system-prompt", "-s", type=str, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    # Determinar configurações
    config = {}
    
    if args.preset:
        config = load_preset(args.preset)
        print(f"📋 Usando preset: {args.preset}")
        print(f"   Descrição: {config['description']}\n")
    
    # Override com argumentos da linha de comando
    model_path = args.model
    gpu_layers = args.gpu_layers or config.get("gpu_layers", 35)
    ctx_size = args.ctx_size or config.get("ctx_size", 4096)
    batch_size = args.batch_size or config.get("batch_size", 1)
    threads = args.threads or config.get("threads", 8)
    threads_batch = config.get("threads_batch", 4)
    flash_attn = config.get("flash_attn", True)
    main_gpu = config.get("main_gpu", 0)
    
    # Se nenhum modelo especificado, procurar no diretório models
    if not model_path:
        models_dir = Path(__file__).parent.parent / "models"
        gguf_files = list(models_dir.glob("*.gguf"))
        
        if not gguf_files:
            print("❌ Nenhum modelo GGUF encontrado em models/")
            print("\nBaixe um modelo:")
            print("  python scripts/download_models.py qwen2.5_32b Q4_K_M")
            sys.exit(1)
        
        # Usar primeiro modelo encontrado
        model_path = str(gguf_files[0])
        print(f"📦 Modelo detectado: {model_path}\n")
    
    # Criar instância
    llm = create_llama_instance(
        model_path=model_path,
        gpu_layers=gpu_layers,
        ctx_size=ctx_size,
        batch_size=batch_size,
        threads=threads,
        threads_batch=threads_batch,
        flash_attn=flash_attn,
        main_gpu=main_gpu,
        verbose=args.verbose,
    )
    
    # Executar benchmark ou chat
    if args.benchmark:
        benchmark(llm)
    else:
        chat_loop(llm, system_prompt=args.system_prompt)


if __name__ == "__main__":
    main()
