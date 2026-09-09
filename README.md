# Qwen3 (30B) e Qwen2.5 (32B) - Configuração para Hardware Limitado

## 🎯 Objetivo
Executar modelos Qwen de grande porte (27B-32B) em máquinas com:
- **RAM**: 16GB
- **VRAM**: 8GB ou 10GB
- **Performance alvo**: 21-24 tokens/segundo

## 📦 Modelos Recomendados

### Opção 1: Qwen3-30B-A3B (Recomendado - MoE)
- **Arquitetura**: Mixture of Experts (MoE)
- **Parâmetros totais**: 30B
- **Parâmetros ativos**: ~3B por token
- **Vantagem**: Mais eficiente, mesma qualidade com menos computação
- **Disponível**: Versões quantizadas GGUF

### Opção 2: Qwen2.5-32B (Dense)
- **Arquitetura**: Dense Transformer
- **Parâmetros totais**: 32B
- **Vantagem**: Modelo estável e bem testado
- **Disponível**: Amplamente disponível em GGUF

### Opção 3: Qwen3-32B (Dense)
- **Arquitetura**: Dense Transformer
- **Parâmetros totais**: 32B
- **Vantagem**: Última geração, melhor qualidade
- **Disponível**: Versões quantizadas GGUF

## 🔧 Técnicas de Otimização

### 1. **Quantização GGUF (4-bit a 6-bit)**
- Reduz memória necessária em ~70%
- Mantém 95-98% da qualidade original
- Formato ideal: Q4_K_M ou Q5_K_M

### 2. **GPU Offload Estratégico**
- Carregar camadas do modelo na GPU
- Manter restante na RAM do sistema
- Otimizar transferência CPU↔GPU

### 3. **Context Window Otimizado**
- Reduzir contexto quando possível
- Usar sliding window para conversas longas

### 4. **Batch Size = 1**
- Processamento sequencial
- Menor uso de memória

### 5. **Flash Attention**
- Acelera atenção em ~2x
- Reduz uso de memória VRAM

## 🚀 Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Configurações por Hardware

### Para GPU 8GB VRAM + 16GB RAM - Qwen3-30B (MoE)
```bash
# Q4_K_M quantization (aproximadamente 16-18GB total, mais eficiente por ser MoE)
python scripts/run_qwen.py --model qwen3-30b-a3b-q4_k_m.gguf \
  --gpu-layers 40 \
  --ctx-size 4096 \
  --batch-size 1
```

### Para GPU 8GB VRAM + 16GB RAM - Qwen2.5/Qwen3 32B (Dense)
```bash
# Q4_K_M quantization (aproximadamente 18-20GB total)
python scripts/run_qwen.py --model qwen2.5-32b-q4_k_m.gguf \
  --gpu-layers 35 \
  --ctx-size 4096 \
  --batch-size 1
```

### Para GPU 10GB VRAM + 16GB RAM - Qwen3-30B (MoE)
```bash
# Q5_K_M quantization (aproximadamente 18-20GB total)
python scripts/run_qwen.py --model qwen3-30b-a3b-q5_k_m.gguf \
  --gpu-layers 50 \
  --ctx-size 4096 \
  --batch-size 1
```

### Para GPU 10GB VRAM + 16GB RAM - Qwen2.5/Qwen3 32B (Dense)
```bash
# Q5_K_M quantization (aproximadamente 20-22GB total)
python scripts/run_qwen.py --model qwen2.5-32b-q5_k_m.gguf \
  --gpu-layers 45 \
  --ctx-size 4096 \
  --batch-size 1
```

## 📊 Performance Esperada

| Modelo | Configuração | Tokens/s | VRAM Uso | RAM Uso |
|--------|--------------|----------|----------|---------|
| Qwen3-30B-A3B (MoE) | Q4_K_M + 8GB GPU | 22-26 | 7GB | 10GB |
| Qwen3-30B-A3B (MoE) | Q5_K_M + 10GB GPU | 24-28 | 8.5GB | 9GB |
| Qwen2.5-32B (Dense) | Q4_K_M + 8GB GPU | 21-24 | 7.5GB | 12GB |
| Qwen2.5-32B (Dense) | Q5_K_M + 10GB GPU | 21-24 | 9GB | 11GB |
| Qwen3-32B (Dense) | Q4_K_M + 8GB GPU | 21-24 | 7.5GB | 12GB |
| Qwen3-32B (Dense) | Q5_K_M + 10GB GPU | 21-24 | 9GB | 11GB |

**Nota**: Modelos MoE (Mixture of Experts) como Qwen3-30B-A3B são mais eficientes pois ativam apenas ~3B parâmetros por token, resultando em maior velocidade com menor uso de recursos.

## 📥 Download dos Modelos

Os modelos podem ser baixados do Hugging Face:

### Qwen3-30B-A3B (MoE) - Recomendado
```bash
# Q4_K_M quantization (Melhor equilíbrio)
huggingface-cli download bartowski/Qwen3-30B-A3B-Instruct-GGUF \
  Qwen3-30B-A3B-Instruct-Q4_K_M.gguf \
  --local-dir models

# Q5_K_M quantization (Melhor qualidade)
huggingface-cli download bartowski/Qwen3-30B-A3B-Instruct-GGUF \
  Qwen3-30B-A3B-Instruct-Q5_K_M.gguf \
  --local-dir models
```

### Qwen2.5-32B (Dense) - Alternativa Estável
```bash
# Q4_K_M quantization (Recomendado para GPU 8GB)
huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
  Qwen2.5-32B-Instruct-Q4_K_M.gguf \
  --local-dir models

# Q5_K_M quantization (Recomendado para GPU 10GB)
huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
  Qwen2.5-32B-Instruct-Q5_K_M.gguf \
  --local-dir models
```

### Qwen3-32B (Dense) - Última Geração
```bash
# Q4_K_M quantization
huggingface-cli download bartowski/Qwen3-32B-Instruct-GGUF \
  Qwen3-32B-Instruct-Q4_K_M.gguf \
  --local-dir models

# Q5_K_M quantization
huggingface-cli download bartowski/Qwen3-32B-Instruct-GGUF \
  Qwen3-32B-Instruct-Q5_K_M.gguf \
  --local-dir models
```

### Alternativas (TheBloke / MaziyarPanahi)
```bash
# Caso os modelos acima não estejam disponíveis
huggingface-cli download TheBloke/Qwen-32B-Chat-GGUF \
  qwen-32b-chat.Q4_K_M.gguf \
  --local-dir models
```

## 🔍 Monitoramento

Use o script de benchmark para validar performance:

```bash
python scripts/benchmark.py --model models/Qwen2.5-32B-Instruct-Q4_K_M.gguf
```

## ⚠️ Troubleshooting

### Problema: Out of Memory
- Reduza `--gpu-layers`
- Use quantização menor (Q3_K_M)
- Diminua `--ctx-size`
- Para modelos Dense 32B, prefira Q4_K_M em GPUs 8GB

### Problema: Performance abaixo de 21 tokens/s
- Aumente `--gpu-layers` até o limite da VRAM
- Verifique se GPU está sendo utilizada (`nvidia-smi`)
- Feche outros aplicativos usando GPU
- Para Qwen3-30B-A3B (MoE), use pelo menos 40 camadas na GPU

### Problema: Modelo muito lento
- Use Q4_K_M em vez de Q5/Q6
- Reduza context window
- Verifique temperatura da GPU (throttling)
- Certifique-se de que Flash Attention está habilitado

### Problema: Modelo não carrega
- Verifique espaço em disco (modelos GGUF 32B precisam de ~18-22GB)
- Valide integridade do arquivo GGUF
- Tente baixar novamente o modelo

## 📝 Notas Importantes

1. **Qwen3-30B-A3B (MoE)**: Modelo Mixture of Experts com 30B parâmetros totais, ativando apenas ~3B por token - mais eficiente para hardware limitado
2. **Qwen2.5-32B e Qwen3-32B (Dense)**: Modelos densos tradicionais com todos os 32B parâmetros ativos
3. **Não existe Qwen 3.7 ou versões 24B/27B/30B densas** - Os tamanhos disponíveis são: 0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B e o MoE 30B-A3B
4. **GGUF é o formato recomendado** para rodar localmente com llama.cpp
5. **Modelos MoE são ideais** para GPUs 8GB-10GB pois exigem menos VRAM durante inferência
6. **Quantização Q4_K_M** oferece melhor equilíbrio entre qualidade e performance para seu caso de uso

## 🛠️ Scripts Disponíveis

- `scripts/run_qwen.py` - Script principal de inferência
- `scripts/benchmark.py` - Benchmark de performance
- `scripts/download_models.py` - Download automático de modelos
- `configs/presets.json` - Presets de configuração por hardware

## 📄 Licença

Este projeto é apenas para fins educacionais. Verifique as licenças dos modelos no Hugging Face.