# 🧾 Medifolder - Classificador Automatizado de Documentos Médicos

Sistema de linha de comando (CLI) para classificação automática de documentos médicos (PDFs e imagens) com extração de metadados via LLM, organização hierárquica por paciente e tipo, e renomeação padronizada.

## 🎯 Funcionalidades

- ✅ **Classificação Automática**: Organiza documentos por tipo (exames, receitas, laudos, etc.)
- ✅ **Extração via LLM**: Utiliza modelos OpenAI ou compatíveis (Ollama) para extrair metadados
- ✅ **Organização Hierárquica**: Cria estrutura `paciente/tipo_documento/arquivo_renomeado.pdf`
- ✅ **Identificação Inteligente**: Reconhece pacientes mesmo com nomes abreviados
- ✅ **Sistema de Retry**: Até 3 tentativas com timeout configurável (30s)
- ✅ **Logging Estruturado**: Rastreamento completo do processamento
- ✅ **Preservação de Originais**: Arquivos originais são mantidos por padrão

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

## 🏥 Especialidades Reconhecidas

`radiologia`, `laboratorial`, `cardiologia`, `endocrinologia`, `ginecologia`, `clinica_geral`, `dermatologia`, `pediatria`

## ⚙️ Configuração

### 1. **Instalação**

```bash
# Clone o repositório
git clone <url-do-repo>
cd medifolder

# Crie e ative ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale dependências
pip install -e .[dev]
```

### 2. **Configuração do LLM**

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
# Crie as pastas necessárias
mkdir -p ~/medifolder/entrada
mkdir -p ~/medifolder/saida

# Coloque documentos médicos para processar
cp seus_documentos.pdf ~/medifolder/entrada/
```

## 🚀 Como Usar

### **Comando Básico**
```bash
python -m medifolder \
  --input ~/medifolder/entrada \
  --output ~/medifolder/saida \
  --model gpt-4 \
  --log-level info
```

### **Com Ollama Local**
```bash
PYTHONPATH=/path/to/medifolder/src python -m medifolder \
  --input ~/medifolder/entrada \
  --output ~/medifolder/saida \
  --model gpt-oss:20b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --temperature 0.3 \
  --max-tokens 1024 \
  --log-level info
```

### **Modo Teste (Dry-run)**
```bash
python -m medifolder \
  --input ~/medifolder/entrada \
  --output ~/medifolder/saida \
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
| `--log-level` | string | `info` | Nível de log: `debug`, `info`, `warning`, `error` |
| `--dry-run` | bool | `false` | Simula sem mover arquivos |
| `--mover` | bool | `false` | Move (deleta originais) em vez de copiar |

## 📁 Estrutura de Saída

```
~/medifolder/saida/
├── antonio_alisio_de_menezes_cordeiro/
│   ├── exames/
│   │   ├── 2024-03-15-antonio_alisio_de_menezes_cordeiro-exame-laboratorial-hemograma-completo.pdf
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
PYTHONPATH=/path/to/medifolder/src python -m medifolder [argumentos]
```

## 📝 Exemplos de Uso

### **1. Processamento Básico**
```bash
python -m medifolder --input ./docs --output ./organized --model gpt-4
```

### **2. Com Configurações Personalizadas**
```bash
python -m medifolder \
  --input ./medical_docs \
  --output ./sorted_docs \
  --model gpt-3.5-turbo \
  --temperature 0.1 \
  --max-tokens 256 \
  --log-level debug
```

### **3. Teste com Ollama**
```bash
export PYTHONPATH=/Users/seu-usuario/dev/medifolder/src
python -m medifolder \
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
pytest --cov=medifolder

# Teste específico
pytest tests/test_processing.py -v
```
