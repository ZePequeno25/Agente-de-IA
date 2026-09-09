#!/usr/bin/env python3
"""
Script de benchmark para testar performance do modelo Qwen.

Uso:
    python benchmark.py --model models/Qwen2.5-32B-Instruct-Q4_K_M.gguf
    python benchmark.py --preset gpu_8gb_ram_16gb
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

try:
    from llama_cpp import Llama
except ImportError:
    print("❌ llama-cpp-python não instalado. Execute: pip install -r requirements.txt")
    sys.exit(1)


TEST_PROMPTS = [
    "Explique o que é inteligência artificial em 3 parágrafos.",
    "Escreva um poema curto sobre tecnologia.",
    "Qual a diferença entre machine learning e deep learning?",
    "Descreva os benefícios da energia solar.",
]


def load_preset(preset_name: str) -> dict:
    """Carrega preset de configuração."""
    config_path = Path(__file__).parent.parent / "configs" / "presets.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        configs = json.load(f)
    
    if preset_name not in configs["presets"]:
        available = ", ".join(configs["presets"].keys())
        raise ValueError(f"Preset '{preset_name}' não encontrado. Disponíveis: {available}")
    
    return configs["presets"][preset_name]


def run_benchmark(llm: Llama, prompt: str, max_tokens: int = 128) -> Dict:
    """Executa benchmark para um único prompt."""
    
    messages = [{"role": "user", "content": prompt}]
    
    # Warmup
    _ = llm.create_chat_completion(
        messages=messages,
        max_tokens=10,
        stream=False,
    )
    
    # Benchmark real
    start_time = time.time()
    token_count = 0
    
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        stream=True,
    )
    
    for chunk in response:
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                token_count += 1
    
    elapsed = time.time() - start_time
    tokens_per_second = token_count / elapsed if elapsed > 0 else 0
    
    return {
        "prompt": prompt[:50] + "...",
        "tokens_generated": token_count,
        "time_elapsed": elapsed,
        "tokens_per_second": tokens_per_second,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark de performance para Qwen 2.5 32B"
    )
    
    parser.add_argument("--model", "-m", type=str, required=True)
    parser.add_argument("--preset", "-p", type=str, default=None)
    parser.add_argument("--gpu-layers", "-gl", type=int, default=35)
    parser.add_argument("--ctx-size", "-c", type=int, default=4096)
    parser.add_argument("--threads", "-t", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--iterations", "-i", type=int, default=3)
    
    args = parser.parse_args()
    
    # Carregar preset se especificado
    config = {}
    if args.preset:
        config = load_preset(args.preset)
        print(f"📋 Usando preset: {args.preset}\n")
    
    gpu_layers = args.gpu_layers or config.get("gpu_layers", 35)
    ctx_size = args.ctx_size or config.get("ctx_size", 4096)
    threads = args.threads or config.get("threads", 8)
    
    # Verificar se modelo existe
    if not Path(args.model).exists():
        print(f"❌ Modelo não encontrado: {args.model}")
        sys.exit(1)
    
    # Carregar modelo
    print(f"📦 Carregando modelo: {args.model}")
    print(f"⚙️  GPU Layers: {gpu_layers}, Context: {ctx_size}, Threads: {threads}\n")
    
    llm = Llama(
        model_path=args.model,
        n_ctx=ctx_size,
        n_gpu_layers=gpu_layers,
        n_threads=threads,
        verbose=False,
        use_mlock=True,
        use_mmap=True,
    )
    
    print("✅ Modelo carregado!\n")
    print("=" * 70)
    print("🔍 INICIANDO BENCHMARK")
    print("=" * 70 + "\n")
    
    all_results = []
    
    for i in range(args.iterations):
        print(f"\n📝 Iteração {i+1}/{args.iterations}")
        print("-" * 50)
        
        iteration_results = []
        
        for prompt in TEST_PROMPTS:
            result = run_benchmark(llm, prompt, max_tokens=args.max_tokens)
            iteration_results.append(result)
            
            print(f"\nPrompt: {result['prompt']}")
            print(f"  Tokens: {result['tokens_generated']} | "
                  f"Tempo: {result['time_elapsed']:.2f}s | "
                  f"Tokens/s: {result['tokens_per_second']:.2f}")
        
        all_results.extend(iteration_results)
    
    # Calcular médias
    avg_tokens_per_second = sum(r["tokens_per_second"] for r in all_results) / len(all_results)
    avg_time = sum(r["time_elapsed"] for r in all_results) / len(all_results)
    total_tokens = sum(r["tokens_generated"] for r in all_results)
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS FINAIS")
    print("=" * 70)
    print(f"\n   Iterações: {args.iterations}")
    print(f"   Prompts por iteração: {len(TEST_PROMPTS)}")
    print(f"   Total de tokens gerados: {total_tokens}")
    print(f"   Tempo médio por geração: {avg_time:.2f}s")
    print(f"   🎯 Média de tokens/segundo: {avg_tokens_per_second:.2f}")
    
    # Avaliação da meta
    target_min, target_max = 21, 24
    
    if target_min <= avg_tokens_per_second <= target_max:
        print(f"   ✅ META ATINGIDA! ({target_min}-{target_max} tokens/s)")
    elif avg_tokens_per_second < target_min:
        print(f"   ⚠️  ABAIXO DA META ({target_min}-{target_max} tokens/s)")
        print(f"       Sugestões:")
        print(f"         - Aumente --gpu-layers (atual: {gpu_layers})")
        print(f"         - Use quantização menor (Q4_K_M em vez de Q5/Q6)")
        print(f"         - Reduza --ctx-size")
    else:
        print(f"   🚀 ACIMA DA META! Excelente performance.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
