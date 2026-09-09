#!/usr/bin/env python3
"""
Sistema de Detecção Automática de Hardware e Configuração Ótima
Detecta SO, RAM, GPU e configura o melhor modelo e parâmetros para a máquina
"""

import os
import sys
import json
import platform
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, List


class SystemDetector:
    """Detecta hardware e sistema operacional para configuração automática"""
    
    def __init__(self):
        self.system_info = self._detect_system()
        
    def _detect_system(self) -> Dict[str, Any]:
        """Detecta informações do sistema"""
        return {
            "os": self._detect_os(),
            "ram_gb": self._detect_ram(),
            "gpu": self._detect_gpu(),
            "cpu_cores": self._detect_cpu_cores(),
            "python_version": sys.version.split()[0],
            "architecture": platform.machine()
        }
    
    def _detect_os(self) -> Dict[str, str]:
        """Detecta sistema operacional"""
        return {
            "name": platform.system(),
            "version": platform.version(),
            "release": platform.release(),
            "machine": platform.machine()
        }
    
    def _detect_ram(self) -> float:
        """Detecta RAM total em GB"""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong
                
                class MEMORYSTATUS(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', c_ulonglong),
                        ('ullAvailPhys', c_ulonglong),
                        ('ullTotalPageFile', c_ulonglong),
                        ('ullAvailPageFile', c_ulonglong),
                        ('ullTotalVirtual', c_ulonglong),
                        ('ullAvailVirtual', c_ulonglong),
                        ('ullAvailExtendedVirtual', c_ulonglong),
                    ]
                
                memory = MEMORYSTATUS()
                memory.dwLength = ctypes.sizeof(MEMORYSTATUS)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
                return round(memory.ullTotalPhys / (1024 ** 3), 2)
            else:
                # Linux/Mac
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            kb = int(line.split()[1])
                            return round(kb / (1024 * 1024), 2)
        except Exception:
            pass
        return 16.0  # Valor padrão seguro
    
    def _detect_gpu(self) -> List[Dict[str, Any]]:
        """Detecta GPUs disponíveis"""
        gpus = []
        
        # Tentar detectar NVIDIA via nvidia-smi
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(', ')
                    if len(parts) >= 2:
                        name = parts[0]
                        memory_mb = int(parts[1].replace(' MiB', ''))
                        gpus.append({
                            "vendor": "NVIDIA",
                            "name": name,
                            "memory_mb": memory_mb,
                            "memory_gb": round(memory_mb / 1024, 2)
                        })
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Tentar detectar via PyTorch (se disponível)
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    if not any(g['name'] == gpu_name for g in gpus):
                        gpus.append({
                            "vendor": "NVIDIA",
                            "name": gpu_name,
                            "memory_mb": int(gpu_memory * 1024),
                            "memory_gb": round(gpu_memory, 2)
                        })
        except ImportError:
            pass
        
        # Detectar Apple Silicon
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            gpus.append({
                "vendor": "Apple",
                "name": "Apple Silicon",
                "memory_mb": 0,  # Memória unificada
                "memory_gb": 0
            })
        
        return gpus
    
    def _detect_cpu_cores(self) -> int:
        """Detecta número de cores da CPU"""
        try:
            return os.cpu_count() or 4
        except Exception:
            return 4
    
    def get_optimal_config(self) -> Dict[str, Any]:
        """Retorna configuração ótima baseada no hardware detectado"""
        ram_gb = self.system_info['ram_gb']
        gpus = self.system_info['gpu']
        
        # Determinar melhor GPU
        best_gpu = None
        if gpus:
            # Priorizar GPU com mais memória
            best_gpu = max(gpus, key=lambda x: x['memory_gb'])
        
        # Calcular configuração recomendada
        config = {
            "system": self.system_info,
            "recommendations": {}
        }
        
        # Lógica de recomendação
        if best_gpu and best_gpu['vendor'] == 'NVIDIA':
            gpu_mem = best_gpu['memory_gb']
            
            if gpu_mem >= 10:
                # GPU 10GB+
                config["recommendations"] = {
                    "model": "qwen3_30b_a3b_moe",
                    "quantization": "Q5_K_M",
                    "gpu_layers": 50,
                    "context_size": 8192,
                    "threads": max(1, self.system_info['cpu_cores'] - 2),
                    "batch_size": 512,
                    "expected_tokens_s": "24-28",
                    "reason": f"GPU {best_gpu['name']} com {gpu_mem}GB permite Q5_K_M com 50 layers"
                }
            elif gpu_mem >= 8:
                # GPU 8GB
                config["recommendations"] = {
                    "model": "qwen3_30b_a3b_moe",
                    "quantization": "Q4_K_M",
                    "gpu_layers": 40,
                    "context_size": 8192,
                    "threads": max(1, self.system_info['cpu_cores'] - 2),
                    "batch_size": 512,
                    "expected_tokens_s": "22-26",
                    "reason": f"GPU {best_gpu['name']} com {gpu_mem}GB permite Q4_K_M com 40 layers"
                }
            elif gpu_mem >= 6:
                # GPU 6GB
                config["recommendations"] = {
                    "model": "qwen2_5_7b",
                    "quantization": "Q5_K_M",
                    "gpu_layers": 35,
                    "context_size": 4096,
                    "threads": max(1, self.system_info['cpu_cores'] - 2),
                    "batch_size": 256,
                    "expected_tokens_s": "30-40",
                    "reason": f"GPU {gpu_mem}GB limitada, recomendado modelo 7B"
                }
            else:
                # GPU < 6GB
                config["recommendations"] = {
                    "model": "qwen2_5_7b",
                    "quantization": "Q4_K_M",
                    "gpu_layers": 25,
                    "context_size": 4096,
                    "threads": max(1, self.system_info['cpu_cores'] - 2),
                    "batch_size": 256,
                    "expected_tokens_s": "25-35",
                    "reason": f"GPU {gpu_mem}GB muito limitada, usar modelo 7B com quantização leve"
                }
        elif best_gpu and best_gpu['vendor'] == 'Apple':
            # Apple Silicon
            config["recommendations"] = {
                "model": "qwen3_30b_a3b_moe",
                "quantization": "Q4_K_M",
                "gpu_layers": -1,  # Todas as camadas na GPU (Metal)
                "context_size": 8192,
                "threads": max(1, self.system_info['cpu_cores'] - 2),
                "batch_size": 512,
                "expected_tokens_s": "20-25",
                "reason": "Apple Silicon com memória unificada, usar todas as camadas na GPU"
            }
        else:
            # CPU only
            if ram_gb >= 32:
                config["recommendations"] = {
                    "model": "qwen3_30b_a3b_moe",
                    "quantization": "Q4_K_M",
                    "gpu_layers": 0,
                    "context_size": 4096,
                    "threads": self.system_info['cpu_cores'],
                    "batch_size": 256,
                    "expected_tokens_s": "8-12",
                    "reason": f"Sem GPU dedicada, mas {ram_gb}GB RAM permite modelo 30B apenas na CPU"
                }
            elif ram_gb >= 16:
                config["recommendations"] = {
                    "model": "qwen2_5_7b",
                    "quantization": "Q4_K_M",
                    "gpu_layers": 0,
                    "context_size": 4096,
                    "threads": self.system_info['cpu_cores'],
                    "batch_size": 256,
                    "expected_tokens_s": "12-18",
                    "reason": f"Sem GPU dedicada, {ram_gb}GB RAM, recomendado modelo 7B"
                }
            else:
                config["recommendations"] = {
                    "model": "qwen2_5_3b",
                    "quantization": "Q4_K_M",
                    "gpu_layers": 0,
                    "context_size": 2048,
                    "threads": self.system_info['cpu_cores'],
                    "batch_size": 128,
                    "expected_tokens_s": "15-25",
                    "reason": f"Hardware limitado ({ram_gb}GB RAM), usar modelo 3B"
                }
        
        return config
    
    def save_config(self, output_path: str = "configs/auto_config.json"):
        """Salva configuração detectada em arquivo"""
        config = self.get_optimal_config()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def print_report(self):
        """Imprime relatório do sistema e recomendações"""
        config = self.get_optimal_config()
        
        print("\n" + "="*60)
        print("🔍 RELATÓRIO DE DETECÇÃO DE HARDWARE")
        print("="*60)
        
        print(f"\n💻 Sistema Operacional:")
        print(f"   OS: {config['system']['os']['name']}")
        print(f"   Versão: {config['system']['os']['version']}")
        print(f"   Arquitetura: {config['system']['os']['machine']}")
        
        print(f"\n🧠 Memória RAM: {config['system']['ram_gb']} GB")
        print(f"⚙️  CPU Cores: {config['system']['cpu_cores']}")
        
        if config['system']['gpu']:
            print(f"\n🎮 GPU(s) Detectada(s):")
            for gpu in config['system']['gpu']:
                print(f"   - {gpu['vendor']} {gpu['name']} ({gpu['memory_gb']} GB)")
        else:
            print(f"\n🎮 GPU: Nenhuma GPU dedicada detectada")
        
        print(f"\n🐍 Python: {config['system']['python_version']}")
        
        print("\n" + "="*60)
        print("📋 RECOMENDAÇÕES DE CONFIGURAÇÃO")
        print("="*60)
        
        rec = config['recommendations']
        print(f"\n✅ Modelo Recomendado: {rec['model']}")
        print(f"✅ Quantização: {rec['quantization']}")
        print(f"✅ GPU Layers: {rec['gpu_layers']}")
        print(f"✅ Context Size: {rec['context_size']}")
        print(f"✅ Threads: {rec['threads']}")
        print(f"✅ Batch Size: {rec['batch_size']}")
        print(f"📊 Tokens/s Esperados: {rec['expected_tokens_s']}")
        print(f"💡 Motivo: {rec['reason']}")
        
        print("\n" + "="*60)
        print(f"💾 Config salva em: configs/auto_config.json")
        print("="*60 + "\n")


def main():
    """Função principal"""
    detector = SystemDetector()
    detector.print_report()
    config_path = detector.save_config()
    print(f"Configuração automática salva em: {config_path}")


if __name__ == "__main__":
    main()
