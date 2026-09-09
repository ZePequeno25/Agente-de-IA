# Guia Rápido de Inicialização

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

# Baixar Qwen 2.5 32B com quantização Q4_K_M (recomendado para GPU 8GB)
python scripts/download_models.py qwen2.5_32b Q4_K_M

# Ou baixe para GPU 10GB com melhor qualidade
python scripts/download_models.py qwen2.5_32b Q5_K_M
```

### Passo 3: Executar

```bash
# Usar preset para GPU 8GB
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb

# Ou usar preset para GPU 10GB
python scripts/run_qwen.py --preset gpu_10gb_ram_16gb

# Ou especificar manualmente
python scripts/run_qwen.py --model models/Qwen2.5-32B-Instruct-Q4_K_M.gguf --gpu-layers 35
```

### Passo 4: Testar Performance

```bash
# Executar benchmark
python scripts/benchmark.py --model models/Qwen2.5-32B-Instruct-Q4_K_M.gguf --preset gpu_8gb_ram_16gb
```

---

## 📋 Comandos Úteis

### Chat Interativo
```bash
python scripts/run_qwen.py --preset gpu_8gb_ram_16gb
```

### Benchmark de Performance
```bash
python scripts/benchmark.py --model models/*.gguf --iterations 3
```

### Download de Modelos
```bash
# Listar disponíveis
python scripts/download_models.py --list

# Baixar específico
python scripts/download_models.py qwen2.5_32b Q4_K_M
```

---

## ⚙️ Presets Disponíveis

| Preset | GPU Layers | Quantização | Tokens/s Esperado |
|--------|-----------|-------------|-------------------|
| `gpu_8gb_ram_16gb` | 35 | Q4_K_M | 21-24 |
| `gpu_10gb_ram_16gb` | 45 | Q5_K_M | 21-24 |
| `gpu_10gb_high_quality` | 40 | Q6_K | 20-23 |
| `cpu_only` | 0 | Q4_K_M | 3-6 |

---

## 🔧 Ajustes Finos

### Se estiver usando menos VRAM que o disponível:
```bash
# Aumente gpu_layers
python scripts/run_qwen.py --model modelo.gguf --gpu-layers 45
```

### Se estiver faltando memória:
```bash
# Reduza gpu_layers ou context size
python scripts/run_qwen.py --model modelo.gguf --gpu-layers 25 --ctx-size 2048
```

### Para máxima velocidade:
```bash
# Use Q3_K_M e mais gpu layers
python scripts/download_models.py qwen2.5_32b Q3_K_M
python scripts/run_qwen.py --model models/*Q3_K_M.gguf --gpu-layers 50
```

---

## ❓ Problemas Comuns

### "Out of Memory"
- Reduza `--gpu-layers`
- Use quantização menor (Q3 ou Q4)
- Diminua `--ctx-size`

### Performance abaixo de 21 tokens/s
- Aumente `--gpu-layers`
- Verifique se a GPU está sendo usada
- Feche outros programas usando GPU

### Modelo não carrega
- Verifique se há espaço em disco (~20GB livres)
- Confirme se o download foi completado
- Tente reiniciar o sistema

---

## 📞 Suporte

Consulte o README.md principal para documentação completa.
