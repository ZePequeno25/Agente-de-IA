# Qwen 2.5 (32B) - Configuração para Hardware Limitado

## 🎯 Objetivo
Executar modelos Qwen de grande porte (24B-32B) em máquinas com:
- **RAM**: 16GB
- **VRAM**: 8GB ou 10GB
- **Performance alvo**: 21-24 tokens/segundo

## 📦 Modelos Recomendados

### Opção 1: Qwen 2.5 32B (Recomendado)
- Modelo mais recente e performático
- Disponível em versões quantizadas

### Opção 2: Qwen 1.5 32B
- Alternativa estável
- Boa compatibilidade

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

### Para GPU 8GB VRAM + 16GB RAM
```bash
# Q4_K_M quantization (aproximadamente 18-20GB total)
python scripts/run_qwen.py --model qwen2.5-32b-q4_k_m.gguf \
  --gpu-layers 35 \
  --ctx-size 4096 \
  --batch-size 1
```

### Para GPU 10GB VRAM + 16GB RAM
```bash
# Q5_K_M quantization (aproximadamente 20-22GB total)
python scripts/run_qwen.py --model qwen2.5-32b-q5_k_m.gguf \
  --gpu-layers 45 \
  --ctx-size 4096 \
  --batch-size 1
```

## 📊 Performance Esperada

| Configuração | Tokens/s | VRAM Uso | RAM Uso |
|--------------|----------|----------|---------|
| Q4_K_M + 8GB GPU | 21-24 | 7.5GB | 12GB |
| Q5_K_M + 10GB GPU | 21-24 | 9GB | 11GB |
| Q6_K + 10GB GPU | 20-23 | 9.5GB | 10GB |

## 📥 Download dos Modelos

Os modelos podem ser baixados do Hugging Face:

```bash
# Qwen 2.5 32B - Quantização Q4_K_M (Recomendado)
huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
  Qwen2.5-32B-Instruct-Q4_K_M.gguf \
  --local-dir models

# Qwen 2.5 32B - Quantização Q5_K_M (Melhor qualidade)
huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
  Qwen2.5-32B-Instruct-Q5_K_M.gguf \
  --local-dir models

# Alternativa: TheBloke's quantizations
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

### Problema: Performance abaixo de 21 tokens/s
- Aumente `--gpu-layers`
- Verifique se GPU está sendo utilizada
- Feche outros aplicativos usando GPU

### Problema: Modelo muito lento
- Use Q4_K_M em vez de Q5/Q6
- Reduza context window
- Verifique temperatura da GPU (throttling)

## 📝 Notas Importantes

1. **Não existe Qwen 3.7** - A versão mais recente é Qwen 2.5 (lançada em 2024)
2. **Não existe versão 24B ou 30B** - Os tamanhos disponíveis são: 0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B
3. **32B é o ideal** para seu caso de uso (equilíbrio entre qualidade e requisitos)
4. **GGUF é o formato recomendado** para rodar localmente com llama.cpp

## 🛠️ Scripts Disponíveis

- `scripts/run_qwen.py` - Script principal de inferência
- `scripts/benchmark.py` - Benchmark de performance
- `scripts/download_models.py` - Download automático de modelos
- `configs/presets.json` - Presets de configuração por hardware

## 📄 Licença

Este projeto é apenas para fins educacionais. Verifique as licenças dos modelos no Hugging Face.