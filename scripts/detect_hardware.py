"""
Detector de Hardware - Analisa o sistema e recomenda a melhor configuração
Funciona em Windows, Linux e macOS
"""
import os
import sys
import json
import platform
import subprocess
import re


def get_system_info():
    """Coleta informações do sistema operacional"""
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
    }


def get_cpu_info():
    """Coleta informações da CPU"""
    cpu_info = {
        'cores': os.cpu_count() or 1,
        'model': 'Unknown'
    }
    
    try:
        if platform.system() == 'Windows':
            # Windows via registry
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name'],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                cpu_info['model'] = lines[1].strip()
        
        elif platform.system() == 'Linux':
            # Linux via /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
        
        elif platform.system() == 'Darwin':  # macOS
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                cpu_info['model'] = result.stdout.strip()
    
    except Exception:
        pass
    
    return cpu_info


def get_ram_info():
    """Coleta informações de RAM em GB"""
    ram_gb = 8  # Default conservador
    
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                bytes_mem = int(lines[1].strip())
                ram_gb = bytes_mem // (1024 ** 3)
        
        elif platform.system() == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        ram_gb = kb // (1024 * 1024)
                        break
        
        elif platform.system() == 'Darwin':  # macOS
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bytes_mem = int(result.stdout.strip())
                ram_gb = bytes_mem // (1024 ** 3)
    
    except Exception:
        pass
    
    return {'total_gb': ram_gb}


def get_gpu_info():
    """Coleta informações da GPU e VRAM"""
    gpu_info = {
        'detected': False,
        'model': 'Unknown',
        'vram_gb': 0,
        'cuda_available': False
    }
    
    try:
        # Tenta detectar NVIDIA via nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            gpu_info['detected'] = True
            gpu_info['cuda_available'] = True
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[0].split(', ')
                gpu_info['model'] = parts[0] if len(parts) > 0 else 'NVIDIA GPU'
                if len(parts) > 1:
                    vram_mb = int(parts[1].replace(' MiB', ''))
                    gpu_info['vram_gb'] = vram_mb // 1024
    
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Se não detectou NVIDIA, tenta outras GPUs
    if not gpu_info['detected']:
        try:
            if platform.system() == 'Darwin':  # macOS com Apple Silicon
                gpu_info['detected'] = True
                gpu_info['model'] = 'Apple Silicon'
                # Estimativa baseada no modelo
                result = subprocess.run(
                    ['sysctl', '-n', 'hw.model'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and 'M' in result.stdout:
                    gpu_info['vram_gb'] = 8  # Estimativa conservadora
            
            elif platform.system() == 'Linux':
                # Tenta detectar AMD/Intel via lspci
                result = subprocess.run(
                    ['lspci', '|', 'grep', '-i', 'vga'],
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    gpu_info['detected'] = True
                    gpu_info['model'] = result.stdout.strip().split(':')[2] if ':' in result.stdout else 'GPU'
        
        except Exception:
            pass
    
    return gpu_info


def recommend_configuration(system_info, cpu_info, ram_info, gpu_info):
    """
    Recomenda a melhor configuração baseada no hardware detectado
    
    Returns:
        Dicionário com preset recomendado e parâmetros
    """
    ram_gb = ram_info['total_gb']
    vram_gb = gpu_info.get('vram_gb', 0)
    has_gpu = gpu_info.get('detected', False)
    
    recommendation = {
        'preset': None,
        'model_recommendation': '',
        'gpu_layers': 0,
        'quantization': 'Q4_K_M',
        'reasoning': []
    }
    
    # Lógica de recomendação
    if ram_gb < 16:
        recommendation['reasoning'].append(f"RAM limitada ({ram_gb}GB) - Recomenda-se upgrade para 16GB mínimo")
        recommendation['model_recommendation'] = 'qwen3_7b'
        recommendation['quantization'] = 'Q4_K_M'
        if has_gpu and vram_gb >= 6:
            recommendation['gpu_layers'] = min(25, vram_gb * 3)
        else:
            recommendation['gpu_layers'] = 0
            recommendation['reasoning'].append("Execução apenas na CPU devido à VRAM insuficiente")
    
    elif ram_gb >= 16:
        if has_gpu:
            if vram_gb >= 10:
                recommendation['preset'] = 'gpu_10gb_ram_16gb_qwen3_moe'
                recommendation['model_recommendation'] = 'qwen3_30b_a3b_moe'
                recommendation['gpu_layers'] = 50
                recommendation['quantization'] = 'Q5_K_M'
                recommendation['reasoning'].append(f"GPU com {vram_gb}GB VRAM detectada - Configuração ótima")
            
            elif vram_gb >= 8:
                recommendation['preset'] = 'gpu_8gb_ram_16gb_qwen3_moe'
                recommendation['model_recommendation'] = 'qwen3_30b_a3b_moe'
                recommendation['gpu_layers'] = 40
                recommendation['quantization'] = 'Q4_K_M'
                recommendation['reasoning'].append(f"GPU com {vram_gb}GB VRAM detectada - Configuração recomendada")
            
            elif vram_gb >= 6:
                recommendation['preset'] = 'gpu_6gb_ram_16gb'
                recommendation['model_recommendation'] = 'qwen2.5_14b'
                recommendation['gpu_layers'] = 30
                recommendation['quantization'] = 'Q4_K_M'
                recommendation['reasoning'].append(f"GPU com {vram_gb}GB VRAM - Modelo intermediário recomendado")
            
            else:
                recommendation['preset'] = 'cpu_ram_16gb'
                recommendation['model_recommendation'] = 'qwen2.5_7b'
                recommendation['gpu_layers'] = 0
                recommendation['quantization'] = 'Q4_K_M'
                recommendation['reasoning'].append("VRAM insuficiente - Execução híbrida CPU/GPU")
        else:
            # Sem GPU dedicada
            if ram_gb >= 32:
                recommendation['preset'] = 'cpu_ram_32gb'
                recommendation['model_recommendation'] = 'qwen2.5_32b'
                recommendation['gpu_layers'] = 0
                recommendation['quantization'] = 'Q4_K_M'
                recommendation['reasoning'].append("Sem GPU - Usando RAM abundante para modelo maior")
            else:
                recommendation['preset'] = 'cpu_ram_16gb'
                recommendation['model_recommendation'] = 'qwen2.5_14b'
                recommendation['gpu_layers'] = 0
                recommendation['quantization'] = 'Q4_K_M'
                recommendation['reasoning'].append("Sem GPU - Modelo médio recomendado")
    
    return recommendation


def generate_config_file(recommendation, output_path='configs/auto_detected.json'):
    """Gera arquivo de configuração automático"""
    config = {
        'auto_generated': True,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'recommended_preset': recommendation['preset'],
        'parameters': {
            'gpu_layers': recommendation['gpu_layers'],
            'quantization': recommendation['quantization'],
            'model': recommendation['model_recommendation']
        },
        'reasoning': recommendation['reasoning']
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    """Função principal - Detecta hardware e gera recomendação"""
    print("=" * 60)
    print("DETECTOR DE HARDWARE - QWEN CONFIGURATION")
    print("=" * 60)
    
    print("\n📊 Coletando informações do sistema...")
    
    system_info = get_system_info()
    cpu_info = get_cpu_info()
    ram_info = get_ram_info()
    gpu_info = get_gpu_info()
    
    print(f"\n💻 Sistema Operacional: {system_info['os']} {system_info['os_version']}")
    print(f"🖥️  CPU: {cpu_info['cores']} núcleos - {cpu_info['model']}")
    print(f"🧠 RAM: {ram_info['total_gb']} GB")
    print(f"🎮 GPU: {'Detectada' if gpu_info['detected'] else 'Não detectada'}")
    if gpu_info['detected']:
        print(f"   Modelo: {gpu_info['model']}")
        print(f"   VRAM: {gpu_info['vram_gb']} GB")
        print(f"   CUDA: {'Disponível' if gpu_info['cuda_available'] else 'Indisponível'}")
    
    print("\n🔍 Analisando hardware e gerando recomendação...")
    
    recommendation = recommend_configuration(system_info, cpu_info, ram_info, gpu_info)
    
    print(f"\n✅ CONFIGURAÇÃO RECOMENDADA:")
    print(f"   Modelo: {recommendation['model_recommendation']}")
    print(f"   Preset: {recommendation['preset'] or 'Customizado'}")
    print(f"   GPU Layers: {recommendation['gpu_layers']}")
    print(f"   Quantização: {recommendation['quantization']}")
    
    print(f"\n📝 Motivos:")
    for reason in recommendation['reasoning']:
        print(f"   • {reason}")
    
    # Gera arquivo de configuração
    config_path = generate_config_file(recommendation)
    print(f"\n💾 Configuração salva em: {config_path}")
    
    print("\n" + "=" * 60)
    print("Use o comando abaixo para executar com esta configuração:")
    print(f"python scripts/run_qwen.py --config {config_path}")
    print("=" * 60)
    
    return recommendation


if __name__ == '__main__':
    main()
