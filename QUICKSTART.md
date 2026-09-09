# Guia Rápido de Inicialização - Qwen3 e Qwen2.5

## 🚀 Começando em 5 Minutos

### Passo 1: Instalar Dependências

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar pacotes
pip install -r requirements.txt
```

### Passo 2: Baixar Modelo

```bash
# Listar modelos disponíveis
python scripts/download_models.py --list

# Qwen3-30B-A3B (MoE) - RECOMENDADO para GPU 8GB-10GB
python scripts/download_models.py qwen3_30b_a3b_moe Q4_K_M

# Qwen2.5-32B (Dense) - Alternativa estável
python scripts/download_models.py qwen2.5_32b Q4_K_M

# Qwen3-32B (Dense) - Última geração
python scripts/download_models.py qwen3_32b Q5_K_M
```

### Passo 3: Executar

```bash
# Qwen3-30B-A3B (MoE) - GPU 8GB
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb_qwen3_moe

# Qwen3-30B-A3B (MoE) - GPU 10GB
python scripts/run_qwen.py --preset gpu_10gb_ram_16gb_qwen3_moe

# Qwen2.5/Qwen3 32B (Dense) - GPU 8GB
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb_dense

# Qwen2.5/Qwen3 32B (Dense) - GPU 10GB
python scripts/run_qwen.py --preset gpu_10gb_ram_16gb_dense

# Ou especificar manualmente
python scripts/run_qwen.py --model models/Qwen3-30B-A3B-Instruct-Q4_K_M.gguf --gpu-layers 40
```

### Passo 4: Testar Performance

```bash
# Executar benchmark
python scripts/benchmark.py --model models/Qwen3-30B-A3B-Instruct-Q4_K_M.gguf --preset gpu_8gb_ram_16gb_qwen3_moe
```

---

## 📋 Comandos Úteis

### Chat Interativo
```bash
# Qwen3-30B-A3B (MoE) - Mais eficiente
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb_qwen3_moe

# Qwen2.5-32B (Dense) - Alternativa
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb_dense
```

### Benchmark de Performance
```bash
python scripts/benchmark.py --model models/*.gguf --iterations 3
```

### Download de Modelos
```bash
# Listar disponíveis
python scripts/download_models.py --list

# Baixar Qwen3-30B-A3B (MoE) - Recomendado
python scripts/download_models.py qwen3_30b_a3b_moe Q4_K_M

# Baixar Qwen2.5-32B (Dense)
python scripts/download_models.py qwen2.5_32b Q4_K_M
```

---

## ⚙️ Presets Disponíveis

| Preset | Modelo | GPU Layers | Quantização | Tokens/s Esperado |
|--------|--------|-----------|-------------|-------------------|
| `gpu_8gb_ram_16gb_qwen3_moe` | Qwen3-30B-A3B | 40 | Q4_K_M | 22-26 |
| `gpu_8gb_ram_16gb_dense` | Qwen2.5/Qwen3 32B | 35 | Q4_K_M | 21-24 |
| `gpu_10gb_ram_16gb_qwen3_moe` | Qwen3-30B-A3B | 50 | Q5_K_M | 24-28 |
| `gpu_10gb_ram_16gb_dense` | Qwen2.5/Qwen3 32B | 45 | Q5_K_M | 21-24 |
| `gpu_10gb_high_quality` | Qwen2.5-32B | 40 | Q6_K | 20-23 |
| `cpu_only` | Qwen2.5-32B | 0 | Q4_K_M | 3-6 |

---

## 🔧 Ajustes Finos

### Se estiver usando menos VRAM que o disponível:
```bash
# Aumente gpu_layers
python scripts/run_qwen.py --model modelo.gguf --gpu-layers 50
```

### Se estiver faltando memória:
```bash
# Reduza gpu_layers ou context size
python scripts/run_qwen.py --model modelo.gguf --gpu-layers 25 --ctx-size 2048
```

### Para máxima velocidade (MoE):
```bash
# Qwen3-30B-A3B com Q4_K_M e mais gpu layers
python scripts/download_models.py qwen3_30b_a3b_moe Q4_K_M
python scripts/run_qwen.py --model models/*Q4_K_M.gguf --gpu-layers 50
```

---

## ❓ Problemas Comuns

### "Out of Memory"
- Reduza `--gpu-layers`
- Use quantização menor (Q3 ou Q4)
- Diminua `--ctx-size`

### Performance abaixo de 21 tokens/s
- Aumente `--gpu-layers` (40+ para MoE, 35+ para Dense)
- Verifique se a GPU está sendo usada (`nvidia-smi`)
- Feche outros programas usando GPU

### Modelo não carrega
- Verifique se há espaço em disco (~20GB livres)
- Confirme se o download foi completado
- Tente reiniciar o sistema

---

## 📞 Suporte

Consulte o README.md principal para documentação completa.
