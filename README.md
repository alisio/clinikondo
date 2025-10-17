# �✨ CliniKondo - O Assistente de Organização Médica

**CliniKondo** é o assistente que transforma o caos de exames, receitas e laudos em pura harmonia digital! 🎯

Com leveza, humor e método, CliniKondo organiza os documentos médicos da sua família de forma inteligente — cada PDF encontra seu lugar perfeito e traz um pouco de alegria à pasta! Sistema de linha de comando (CLI) com IA que classifica automaticamente documentos médicos usando LLM, organizando em estrutura hierárquica por paciente e tipo.

## ✨ Magia do CliniKondo

- 🪄 **Organização Marie Kondo Style**: Cada documento médico encontra seu lugar ideal com alegria!
- 🤖 **IA Especializada**: Utiliza exclusivamente LLM (OpenAI/Ollama) para classificação inteligente
- 🏗️ **Estrutura Zen**: Cria hierarquia organizada `paciente/tipo_documento/arquivo_harmonioso.pdf`
- 🔍 **Reconhecimento Mágico**: Identifica pacientes e metadados com precisão de IA
- 🔄 **Persistência Gentil**: Até 3 tentativas suaves com timeout de 30s
- 📝 **Diário de Bordo**: Logging estruturado de toda a transformação
- 💝 **Cuidado com Originais**: Preserva arquivos originais com carinho (padrão)

## 📋 Tipos de Documento Suportados

| Tipo | Pasta Destino | Descrição |
|------|---------------|-----------|
| `exame` | `exames` | Resultados, imagens, ultrassom, laboratório |
| `receita` | `receitas_medicas` | Prescrições, medicamentos |
| `vacina` | `vacinas` | Cartão de vacina, imunização |
| `controle` | `controle_de_pressao_e_glicose` | Monitoramento de pressão/glicose |
| `contato` | `contatos_medicos` | Contatos médicos, telefones, clínicas |
| `laudo` | `laudos` | Laudos, relatórios, atestados |
| `agenda` | `agendas` | Consultas, agendamentos |
| `documento` | `documentos` | Formulários e documentos gerais |

## 🏥 Especialidades que CliniKondo Reconhece

`radiologia`, `laboratorial`, `cardiologia`, `endocrinologia`, `ginecologia`, `clinica_geral`, `dermatologia`, `pediatria`

## 📄 Formatos que Trazem Alegria ao CliniKondo

### **Formatos de Arquivo:**
- **PDFs**: `.pdf` (com ou sem texto embutido)
- **Imagens**: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.heic`
- **Texto**: `.txt`

### **🔍 Processamento Inteligente de PDFs:**

| Tipo de PDF | Método de Extração | Dependências |
|-------------|-------------------|--------------|
| **PDF com texto** | PyPDF2 | `PyPDF2>=3.0.0` |
| **PDF escaneado** | OCR automático (estratégia configurável) | Ver tabela abaixo |

> 🚀 **OCR Automático**: Se um PDF não contém texto embutido, o sistema automaticamente aplica OCR para extrair o texto das imagens

### **⚙️ Estratégias de OCR:**

CliniKondo oferece **3 estratégias de OCR** para máxima flexibilidade:

| Estratégia | Descrição | Dependências | Quando Usar |
|-----------|-----------|--------------|-------------|
| **`hybrid`** (padrão) | PyPDF2 → Multimodal → Traditional | Todas abaixo | Máxima compatibilidade e qualidade |
| **`multimodal`** | Apenas LLM Vision (GPT-4) | OpenAI API | Documentos complexos, melhor precisão |
| **`traditional`** | Apenas Tesseract OCR | `PyMuPDF`, `pillow`, `pytesseract` | Documentos simples, máxima velocidade |

**Exemplos:**

```bash
# Estratégia híbrida (padrão)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --ocr-strategy hybrid

# Estratégia multimodal (melhor qualidade)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --model gpt-4-vision-preview \
  --ocr-strategy multimodal

# Estratégia tradicional (mais rápida)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --ocr-strategy traditional
```

### **⚙️ Configuração OCR:**

```bash
# macOS
brew install tesseract

# Ubuntu/Debian  
sudo apt install tesseract-ocr tesseract-ocr-por

# Windows
# Baixar de: https://github.com/UB-Mannheim/tesseract/wiki
```

## ⚙️ Configuração

### 1. **Instalação**

```bash
# Clone o repositório
git clone <url-do-repo>
cd clinikondo

# Crie e ative ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

#### **Opções de Instalação:**

**🚀 Instalação Completa (Obrigatória):**
```bash
# LLM + OCR + PDF (todas as funcionalidades)
pip install -r requirements.txt
```

**📦 Instalação via PyPI (Modo editable):**
```bash
# Instala todas as dependências
pip install -e ".[llm,pdf,ocr,dev]"
```

> ⚠️ **Importante**: Sistema requer LLM obrigatoriamente. Configuração de `OPENAI_API_KEY` é obrigatória.

### 2. **Configuração do LLM (Obrigatória)**

#### **Opção A: OpenAI**
```bash
export OPENAI_API_KEY="sua-chave-openai"
export OPENAI_API_BASE="https://api.openai.com/v1"  # opcional
```

#### **Opção B: Ollama (Local)**
```bash
# Instale Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Execute um modelo
ollama run gpt-oss:20b  # ou outro modelo compatível

# Configure variáveis
export OPENAI_API_KEY="mock-key"  # qualquer valor
export OPENAI_API_BASE="http://localhost:11434/v1"
```

### 3. **Estrutura de Pastas**

```bash
### **🏠 Preparando o Sanctuário CliniKondo:**

```bash
# Criando o espaço sagrado de organização
mkdir -p ~/clinikondo/{entrada,saida}

# Colocando documentos para a transformação mágica
cp seus_documentos.pdf ~/clinikondo/entrada/
```

## 🚀 Como Usar

### **Comando Básico**
```bash
python -m src.clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-4 \
  --log-level info
```

### **Com Ollama Local**
```bash
python -m src.clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-oss:20b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --temperature 0.3 \
  --max-tokens 1024 \
  --ocr-strategy hybrid \
  --log-level info
```

### **Modo Teste (Dry-run)**
```bash
python -m src.clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-4 \
  --dry-run  # Não move arquivos, apenas simula
```

## 📊 Parâmetros Disponíveis

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `--input` | path | - | **Obrigatório**: Pasta com documentos para processar |
| `--output` | path | - | **Obrigatório**: Pasta de destino organizada |
| `--model` | string | `gpt-4` | Modelo LLM a usar |
| `--api-base` | url | OpenAI | Endpoint da API (para Ollama: `http://localhost:11434/v1`) |
| `--api-key` | string | - | Chave da API (para Ollama: qualquer valor) |
| `--temperature` | float | `0.2` | Criatividade do modelo (0.0-1.0) |
| `--max-tokens` | int | `512` | Tokens máximos na resposta |
| `--ocr-strategy` | string | `hybrid` | Estratégia OCR: `hybrid`, `multimodal`, `traditional` |
| `--log-level` | string | `info` | Nível de log: `debug`, `info`, `warning`, `error` |
| `--dry-run` | bool | `false` | Simula sem mover arquivos |
| `--mover` | bool | `false` | Move (deleta originais) em vez de copiar |

### 🔀 Configuração Multi-Modelo (Avançado)

A aplicação suporta **modelos separados** para OCR e classificação, permitindo otimização de custo e qualidade:

| Parâmetro | Tipo | Fallback | Descrição |
|-----------|------|----------|-----------|
| `--ocr-model` | string | `--model` | Modelo para OCR (opcional) |
| `--ocr-api-key` | string | `--api-key` | API key para OCR (opcional) |
| `--ocr-api-base` | url | `--api-base` | Endpoint para OCR (opcional) |
| `--classification-model` | string | `--model` | Modelo para classificação (opcional) |
| `--classification-api-key` | string | `--api-key` | API key para classificação (opcional) |
| `--classification-api-base` | url | `--api-base` | Endpoint para classificação (opcional) |

**Exemplo - OCR Local + Classificação Cloud:**
```bash
python -m src.clinikondo processar \
  --input ~/docs \
  --output ~/organizados \
  --model gpt-3.5-turbo \
  --api-key sk-... \
  --ocr-model llama3.2-vision \
  --ocr-api-base http://localhost:11434/v1 \
  --ocr-api-key mock-key \
  --ocr-strategy multimodal
```

**Benefícios:**
- 💰 **Economia**: Use OCR local grátis (Ollama) + classificação cloud barata
- ⚡ **Performance**: Modelos especializados para cada tarefa
- 🎯 **Qualidade**: Melhor modelo Vision para OCR, melhor modelo geral para classificação

## 📁 Estrutura de Saída

```
~/clinikondo/saida/
├── antonio_alisio_de_menezes_cordeiro/
│   ├── exames/
│   │   ├── ```
2024-03-15-antonio_alisio_de_menezes_cordeiro-exame-laboratorial-hemograma-completo.pdf
```

**Padrão:** `AAAA-MM-DD-nome_paciente-tipo-especialidade-descricao.ext`
│   │   └── 2024-02-20-antonio_alisio_de_menezes_cordeiro-exame-cardiologia-eletrocardiograma.pdf
│   ├── receitas_medicas/
│   │   └── 2024-03-10-antonio_alisio_de_menezes_cordeiro-receita-cardiologia-captopril-uso-continuo.pdf
│   └── laudos/
│       └── 2024-03-01-antonio_alisio_de_menezes_cordeiro-laudo-radiologia-radiografia-torax.pdf
└── maria_silva_santos/
    └── vacinas/
        └── 2024-01-15-maria_silva_santos-vacina-pediatria-covid-terceira-dose.pdf
```

## 🔧 Troubleshooting

### **Problema: "ImportError: No module named 'openai'"**
```bash
pip install openai
```

### **Problema: "OPENAI_API_KEY não configurada"**
```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

### **Problema: "Connection refused" com Ollama**
```bash
# Verifique se Ollama está rodando
ollama ps

# Inicie se necessário
ollama serve &
ollama run gpt-oss:20b
```

### **Problema: Código não atualiza após edições**
```bash
# Use PYTHONPATH para forçar versão local
PYTHONPATH=/path/to/clinikondo/src python -m clinikondo [argumentos]
```

## 📝 Exemplos de Uso

### **1. Processamento Básico**
```bash
python -m clinikondo --input ./docs --output ./organized --model gpt-4
```

### **2. Com Configurações Personalizadas**
```bash
python -m clinikondo \
  --input ./medical_docs \
  --output ./sorted_docs \
  --model gpt-3.5-turbo \
  --temperature 0.1 \
  --max-tokens 256 \
  --log-level debug
```

### **3. Teste com Ollama**
```bash
export PYTHONPATH=/Users/seu-usuario/dev/clinikondo/src
python -m clinikondo \
  --input ~/documentos_medicos \
  --output ~/documentos_organizados \
  --model llama3:8b \
  --api-base http://localhost:11434/v1 \
  --api-key qualquer-coisa \
  --dry-run
```

## 📖 Logs e Monitoramento

O sistema gera logs estruturados conforme SRS:

```json
{
  "arquivo": "exame_sangue.pdf",
  "status": "sucesso", 
  "confianca_extracao": 0.95,
  "metodo_extracao": "llm",
  "paciente_identificado": "antonio_cordeiro",
  "tipo_documento": "exame",
  "especialidade": "laboratorial",
  "duracao_total_ms": 3214,
  "timestamp": "2024-03-15T14:30:22Z"
}
```

## 🎯 Critérios de Qualidade

- ✅ **≥ 90%** de documentos corretamente classificados
- ✅ **≥ 95%** de acurácia na identificação de pacientes  
- ✅ **≥ 95%** das requisições LLM concluídas em 30s
- ✅ **100%** dos originais preservados (modo padrão)
- ✅ **100%** de detecção de duplicatas por hash SHA-256

## 🧪 Testes

```bash
# Execute todos os testes
pytest

# Testes com cobertura
pytest --cov=clinikondo

# Teste específico
pytest tests/test_processing.py -v
```

## 📦 Dependências

### **🔧 Requirements Files:**

| Arquivo | Descrição | Uso |
|---------|-----------|-----|
| `requirements.txt` | **Completo** - Todas as funcionalidades | Produção completa |
| `requirements-minimal.txt` | **Básico** - Apenas heurísticas + PDF | Uso simples sem LLM |
| `requirements-dev.txt` | **Desenvolvimento** - Ferramentas dev + testes | Desenvolvimento |

### **🎯 Dependências por Funcionalidade:**

| Funcionalidade | Dependências | Obrigatório |
|---------------|--------------|-------------|
| **LLM Processing** | `openai>=1.35.0` | ✅ |
| **PDF Processing** | `PyPDF2>=3.0.0` | ✅ |
| **OCR/Images** | `pillow>=10.0.0`, `pytesseract>=0.3.10` | ❌ |
| **Development** | `pytest`, `ruff`, `mypy`, etc. | ❌ |

> ⚠️ **Sistema requer LLM**: A aplicação utiliza exclusivamente LLM para processamento

## 🚀 Trazendo CliniKondo para Casa

### **⚡ Rituais de Instalação:**

```bash
# 🏠 Instalação Completa (recomendada)
pip install -r requirements.txt

# 🔧 Para Desenvolvedores  
pip install -r requirements-dev.txt

# 🎯 Instalação Customizada
pip install -e ".[pdf,ocr]"  # escolha suas funcionalidades favoritas
```

> 🌟 **CliniKondo Wisdom**: LLM é essencial para a magia acontecer!

### **🔧 Dependências do Sistema:**

**Tesseract OCR** (necessário apenas para processamento de imagens):
```bash
# macOS
brew install tesseract

# Ubuntu/Debian  
sudo apt install tesseract-ocr

# Windows
# Download: https://github.com/UB-Mannheim/tesseract/wiki
```
