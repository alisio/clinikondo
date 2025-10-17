# CliniKondo - O Assistente de Organização Médica ✨

**CliniKondo** é o assistente que transforma o caos de exames, receitas e laudos em pura harmonia digital! 🎯

Com leveza, humor e método, CliniKondo organiza os documentos médicos da sua família de forma inteligente — cada PDF encontra seu lugar perfeito e traz um pouco de alegria à pasta! Sistema de linha de comando (CLI) com IA que classifica automaticamente documentos médicos usando LLM, organizando em estrutura hierárquica por paciente e tipo.

## 📋 Pré-requisitos

- **Python**: 3.10 ou superior
- **Sistema Operacional**: macOS, Linux ou Windows
- **RAM**: 2GB mínimo (4GB recomendado)
- **Espaço em Disco**: 100MB para a aplicação + espaço para documentos
- **Conexão com Internet**: Necessária para APIs externas (OpenAI) ou opcional para Ollama local
- **Dependências do Sistema** (opcional, para OCR tradicional):
  - Tesseract OCR (apenas se usar `--ocr-strategy traditional`)

## ✨ Magia do CliniKondo

- 🪄 **Organização Marie Kondo Style**: Cada documento médico encontra seu lugar ideal com alegria!
- 🤖 **IA Especializada**: Utiliza exclusivamente LLM (OpenAI/Ollama) para classificação inteligente
- 🏗️ **Estrutura Zen**: Cria hierarquia organizada `paciente/tipo_documento/arquivo_harmonioso.pdf`
- 🔍 **Reconhecimento Mágico**: Identifica pacientes e metadados com precisão de IA
- 🔄 **Persistência Gentil**: Até 3 tentativas com timeout de 240s e delay de 30s entre tentativas
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

`radiologia`, `laboratorial`, `cardiologia`, `endocrinologia`, `ginecologia`, `clinica_geral`, `dermatologia`, `pediatria`, `oftalmologia`

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
python -m src.clinikondo processar \
  --input docs/ \
  --output saida/ \
  --model gpt-4 \
  --ocr-strategy hybrid

# Estratégia multimodal (melhor qualidade)
python -m src.clinikondo processar \
  --input docs/ \
  --output saida/ \
  --model gpt-4-vision-preview \
  --ocr-strategy multimodal

# Estratégia tradicional (mais rápida)
python -m src.clinikondo processar \
  --input docs/ \
  --output saida/ \
  --model gpt-4 \
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

**🏠 Preparando o Sanctuário CliniKondo:**

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
  --model mistral-small3.1:24b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --temperature 0.3 \
  --max-tokens 1024 \
  --timeout 240 \
  --retry-delay 30 \
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
| `--timeout` | int | `240` | Timeout em segundos por requisição LLM |
| `--retry-delay` | int | `30` | Tempo de espera entre tentativas (segundos) |
| `--ocr-strategy` | string | `hybrid` | Estratégia OCR: `hybrid`, `multimodal`, `traditional` |
| `--log-level` | string | `info` | Nível de log: `debug`, `info`, `warning`, `error` |
| `--dry-run` | bool | `false` | Simula sem mover arquivos |
| `--mover` | bool | `false` | Move (deleta originais) em vez de copiar |
| `--force-reprocess` | bool | `false` | Ignora cache e reprocessa duplicatas |

## 🔄 Sistema de Detecção de Duplicatas

CliniKondo possui um **sistema inteligente de cache** que evita reprocessamento desnecessário de documentos idênticos, economizando tempo e custos de API.

### **Como Funciona:**

1. **Hash SHA-256**: Cada documento recebe um hash único baseado em seu conteúdo
2. **Cache Persistente**: Hashes processados são salvos em `.clinikondo/processed_hashes.json`
3. **Detecção Automática**: Antes de processar, o sistema verifica se o hash já existe
4. **Economia Garantida**: Documentos duplicados **não** são enviados para o LLM

### **📍 Localização do Cache:**

```
~/seu_diretorio_saida/.clinikondo/
├── processed_hashes.json  # Cache de documentos processados
└── patients.json          # Registro de pacientes
```

**Exemplo:**
```bash
# Se você usa --output ~/clinikondo/saida
~/clinikondo/saida/.clinikondo/processed_hashes.json
~/clinikondo/saida/.clinikondo/patients.json
```

### **💰 Benefícios:**

| Cenário | LLM Chamado? | Custo | Tempo |
|---------|--------------|-------|-------|
| **Arquivo novo** | ✅ Sim | 100% | ~3-5s |
| **Hash duplicado** | ❌ Não | 0% | <0.1s |
| **Nome duplicado** (hash diferente) | ✅ Sim | 100% | ~3-5s |

### **🎯 Tipos de Duplicata:**

#### **1. Hash Idêntico** (conteúdo igual)
```bash
# Primeiro processamento
sadasdasd.pdf → processado com LLM → salvo

# Segundo processamento (mesmo arquivo, nome diferente)
documento_copia.pdf → ⏭️ IGNORADO (hash idêntico)
```

**Log:**
```json
{
  "tipo_duplicata": "hash_identico",
  "acao": "processamento_pulado",
  "custo_economizado": "1_chamada_llm"
}
```

#### **2. Nome Duplicado** (conteúdo diferente)
```bash
# Dois exames do mesmo paciente/data
exame1.pdf → 2025-07-29-joao_silva-exame-sangue.pdf
exame2.pdf → 2025-07-29-joao_silva-exame-sangue_v2.pdf  # versão numerada
```

**Log:**
```json
{
  "tipo_duplicata": "nome_duplicado",
  "acao": "versao_numerada_criada",
  "nome_versionado": "arquivo_v2.pdf"
}
```

### **🚀 Forçar Reprocessamento:**

Use `--force-reprocess` quando:
- Você atualizou o modelo LLM
- Mudou o prompt de classificação
- Quer reprocessar tudo ignorando o cache

```bash
python -m src.clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-4 \
  --force-reprocess  # Ignora cache de hashes
```

### **🧹 Gerenciar o Cache:**

#### **Ver conteúdo do cache:**
```bash
cat ~/clinikondo/saida/.clinikondo/processed_hashes.json | python -m json.tool
```

#### **Limpar apenas o cache:**
```bash
rm ~/clinikondo/saida/.clinikondo/processed_hashes.json
```

#### **Limpar tudo (cache + arquivos processados):**
```bash
rm -rf ~/clinikondo/saida/*
```

#### **Estatísticas do cache:**
```bash
# Contar documentos processados
cat ~/clinikondo/saida/.clinikondo/processed_hashes.json | python -c "import sys, json; print(f'{len(json.load(sys.stdin))} documentos no cache')"
```

### **📊 Estrutura do Cache:**

```json
{
  "d745e981204baa6e554bee6cf5ec6b862f742925ba73fb315c3de9e02ccee00b": {
    "hash_sha256": "d745e981...",
    "arquivo_original": "/Users/user/entrada/exame.pdf",
    "arquivo_destino": "/Users/user/saida/joao/exames/2025-07-29-joao-exame.pdf",
    "timestamp": "2025-10-17T18:29:42.989671",
    "paciente_slug": "joao_silva",
    "tipo_documento": "exame"
  }
}
```

### **⚠️ Importante:**

- Cache é **específico por pasta de saída** (`--output`)
- Diferentes pastas de saída têm caches independentes
- Cache persiste entre execuções do programa
- `--dry-run` **não** registra hashes no cache

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
  --timeout 240 \
  --retry-delay 30 \
  --ocr-model llama3.2-vision \
  --ocr-api-base http://localhost:11434/v1 \
  --ocr-api-key mock-key \
  --ocr-strategy multimodal
```

**Benefícios:**
- 💰 **Economia**: Use OCR local grátis (Ollama) + classificação cloud barata
- ⚡ **Performance**: Modelos especializados para cada tarefa
- 🎯 **Qualidade**: Melhor modelo Vision para OCR, melhor modelo geral para classificação

## 🧑‍⚕️ Gerenciamento de Pacientes

CliniKondo mantém um **registro inteligente de pacientes** com funcionalidades avançadas de reconciliação de nomes, detecção de duplicatas e aliases.

### **📍 Localização do Registro:**

```
~/seu_diretorio_saida/.clinikondo/patients.json
```

### **🎯 Funcionalidades Automáticas:**

1. **Identificação Inteligente**
   - LLM extrai nome do paciente do documento
   - Sistema busca paciente existente (match exato ou fuzzy)
   - Se não encontrado, cria automaticamente

2. **Fuzzy Matching** (threshold 0.9)
   - "João Silva" → "Joao da Silva" ✅
   - "Maria Santos" → "Maria S. Santos" ✅
   - Ignora acentos, pontuação e espaços extras

3. **Sistema de Aliases**
   - "João" pode ser alias de "João Pedro Silva"
   - Útil para nomes informais ou abreviados
   - Conflitos são detectados automaticamente

### **📋 Comandos CLI:**

#### **Listar Pacientes**
```bash
python -m src.clinikondo listar-pacientes \
  --output ~/clinikondo/saida
```

**Saída:**
```
📋 Pacientes cadastrados:
  • João Silva (joao-silva) - 12 documentos
  • Maria Santos (maria-santos) - 8 documentos
  • Pedro Oliveira (pedro-oliveira) - 5 documentos
```

#### **Adicionar Paciente Manualmente**
```bash
python -m src.clinikondo pacientes adicionar \
  --output ~/clinikondo/saida \
  --nome "Ana Carolina Mendes" \
  --genero feminino
```

#### **Editar Paciente**
```bash
# Editar nome
python -m src.clinikondo pacientes editar \
  --output ~/clinikondo/saida \
  --slug ana-carolina-mendes \
  --nome "Ana Carolina Mendes Ferreira"

# Adicionar alias
python -m src.clinikondo pacientes editar \
  --output ~/clinikondo/saida \
  --slug ana-carolina-mendes \
  --adicionar-alias "Ana" \
  --adicionar-alias "Carol"

# Alterar gênero
python -m src.clinikondo pacientes editar \
  --output ~/clinikondo/saida \
  --slug ana-carolina-mendes \
  --genero feminino
```

#### **Detectar Pacientes Duplicados**
```bash
python -m src.clinikondo pacientes detectar-duplicatas \
  --output ~/clinikondo/saida \
  --threshold 0.85
```

**Saída:**
```
🔍 Possíveis duplicatas detectadas:

  ⚠️  João Silva ↔️ Joao da Silva (similaridade: 92%)
  ⚠️  Maria Santos ↔️ M. Santos (similaridade: 87%)
  
💡 Use 'pacientes fusionar' para mesclar duplicatas
```

#### **Fusionar (Mesclar) Pacientes Duplicados**
```bash
python -m src.clinikondo pacientes fusionar \
  --output ~/clinikondo/saida \
  --source joao-da-silva \
  --target joao-silva
```

**Resultado:**
- Todos os aliases do paciente `source` são movidos para `target`
- Nome completo do `source` vira alias do `target`
- Paciente `source` é removido
- Documentos **NÃO** são movidos automaticamente

#### **Remover Paciente**
```bash
python -m src.clinikondo pacientes remover \
  --output ~/clinikondo/saida \
  --slug joao-silva
```

⚠️ **Atenção**: Remove apenas do registro. Documentos na pasta permanecem intactos.

### **📊 Estrutura do Registro (`patients.json`):**

```json
[
  {
    "nome_completo": "João Silva Santos",
    "slug_diretorio": "joao-silva-santos",
    "nomes_alternativos": ["João Silva", "João", "J. Santos"],
    "genero": "masculino"
  },
  {
    "nome_completo": "Maria Carolina Mendes",
    "slug_diretorio": "maria-carolina-mendes",
    "nomes_alternativos": ["Maria", "Carol"],
    "genero": "feminino"
  }
]
```

### **🔍 Como Funciona a Identificação:**

```
1. LLM extrai: "Paciente: João da Silva"
   ↓
2. Normaliza: "joao da silva"
   ↓
3. Busca exata: NÃO encontrado
   ↓
4. Fuzzy match (0.9): "joão silva santos" → 92% similar
   ↓
5. Match encontrado! ✅
   ↓
6. Documento salvo em: joao-silva-santos/exames/
```

### **💡 Boas Práticas:**

- **Use aliases** para nomes informais: "João" → alias de "João Pedro Silva"
- **Detecte duplicatas** periodicamente: `pacientes detectar-duplicatas`
- **Revise fuzzy matches** nos logs para garantir precisão
- **Adicione gênero** para melhor organização de documentos
- **Não delete manualmente** `patients.json` - use comandos CLI

### **⚠️ Importante:**

- Registro é **específico por pasta de saída** (`--output`)
- Slugs são únicos e imutáveis (base para nome de diretórios)
- Conflitos de alias são bloqueados automaticamente
- Fusão de pacientes **NÃO move** documentos entre pastas

## �️ Comandos Utilitários

CliniKondo oferece comandos adicionais para manutenção e análise do sistema.

### **📋 Verificar Duplicatas de Documentos**
```bash
python -m src.clinikondo verificar-duplicatas \
  ~/clinikondo/saida \
  --acao listar  # ou 'remover', 'mover'
```

**Ações:**
- `listar`: Lista documentos duplicados sem modificar
- `remover`: Remove duplicatas automaticamente
- `mover`: Move duplicatas para pasta de backup

### **📊 Relatório de Processamento**
```bash
python -m src.clinikondo relatorio-processamento \
  --output-dir ~/clinikondo/saida \
  --periodo 30 \
  --formato texto  # ou 'json', 'html'
```

**Informações incluídas:**
- Total de documentos processados
- Taxa de sucesso/falha
- Distribuição por tipo de documento
- Pacientes com mais documentos
- Estatísticas por período

### **✅ Validar Estrutura de Pastas**
```bash
python -m src.clinikondo validar-estrutura \
  ~/clinikondo/saida \
  --corrigir  # opcional: corrige problemas automaticamente
```

**Validações:**
- Nomenclatura de arquivos correta
- Estrutura de diretórios adequada
- Arquivos órfãos ou mal posicionados
- Metadados faltantes

### **📜 Visualizar Logs**
```bash
python -m src.clinikondo mostrar-log \
  --nivel INFO \
  --linhas 100
```

**Níveis disponíveis:** `DEBUG`, `INFO`, `WARNING`, `ERROR`

## �📁 Estrutura de Saída

**Padrão de Nomenclatura:** `AAAA-MM-DD-nome_paciente-tipo-especialidade-descricao.ext`

```
~/clinikondo/saida/
├── nome_do_paciente/
│   ├── exames/
│   │   ├── 2024-03-15-nome_do_paciente-exame-laboratorial-hemograma-completo.pdf
│   │   └── 2024-02-20-nome_do_paciente-exame-cardiologia-eletrocardiograma.pdf
│   ├── receitas_medicas/
│   │   └── 2024-03-10-nome_do_paciente-receita-cardiologia-captopril-uso-continuo.pdf
│   └── laudos/
│       └── 2024-03-01-nome_do_paciente-laudo-radiologia-radiografia-torax.pdf
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

### **Problema: Timeout muito curto para documentos grandes**
```bash
# Aumente o timeout e retry delay
python -m src.clinikondo processar \
  --input ~/entrada \
  --output ~/saida \
  --model gpt-4 \
  --timeout 600 \
  --retry-delay 60
```

## 📝 Exemplos de Uso

### **1. Processamento Básico**
```bash
python -m src.clinikondo processar \
  --input ./docs \
  --output ./organized \
  --model gpt-4
```

### **2. Com Configurações Personalizadas**
```bash
python -m src.clinikondo processar \
  --input ./medical_docs \
  --output ./sorted_docs \
  --model gpt-3.5-turbo \
  --temperature 0.1 \
  --max-tokens 256 \
  --timeout 180 \
  --retry-delay 20 \
  --log-level debug
```

### **3. Teste com Ollama**
```bash
python -m src.clinikondo processar \
  --input ~/documentos_medicos \
  --output ~/documentos_organizados \
  --model llama3:8b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --dry-run
```

### **4. Reprocessamento Forçado**
```bash
# Útil após atualizar modelo ou prompt
python -m src.clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-4-turbo \
  --force-reprocess  # Ignora cache de duplicatas
```

### **5. Gerenciar Pacientes**
```bash
# Listar todos os pacientes
python -m src.clinikondo listar-pacientes --output ~/clinikondo/saida

# Detectar duplicatas
python -m src.clinikondo pacientes detectar-duplicatas --output ~/clinikondo/saida

# Adicionar alias a paciente existente
python -m src.clinikondo pacientes editar \
  --output ~/clinikondo/saida \
  --slug joao-silva \
  --adicionar-alias "João"

# Fusionar pacientes duplicados
python -m src.clinikondo pacientes fusionar \
  --output ~/clinikondo/saida \
  --source joao-da-silva \
  --target joao-silva
```

## 📖 Logs e Monitoramento

O sistema gera logs estruturados conforme SRS:

### **Log de Processamento Bem-Sucedido:**
```json
{
  "arquivo": "exame_sangue.pdf",
  "status": "sucesso", 
  "confianca_extracao": 0.95,
  "metodo_extracao": "llm",
  "paciente_identificado": "joao",
  "tipo_documento": "exame",
  "especialidade": "laboratorial",
  "duracao_total_ms": 3214,
  "timestamp": "2024-03-15T14:30:22Z"
}
```

### **Log de Duplicata Detectada:**
```json
{
  "evento": "duplicata_detectada",
  "tipo_duplicata": "hash_identico",
  "arquivo_novo": "/Users/user/entrada/documento.pdf",
  "arquivo_original": "/Users/user/entrada/documento_original.pdf",
  "hash_sha256": "d745e981204baa6e...",
  "acao": "processamento_pulado",
  "custo_economizado": "1_chamada_llm",
  "timestamp": "2025-10-17T18:37:07.761598"
}
```

### **Log de Nome Duplicado:**
```json
{
  "evento": "duplicata_detectada",
  "tipo_duplicata": "nome_duplicado",
  "arquivo_novo": "/Users/user/entrada/exame.pdf",
  "nome_original": "2025-07-29-joao-exame-sangue.pdf",
  "nome_versionado": "2025-07-29-joao-exame-sangue_v2.pdf",
  "hash_novo": "d745e981...",
  "hash_original": "diferente",
  "acao": "versao_numerada_criada",
  "timestamp": "2025-10-17T18:29:42.989234"
}
```

## 🎯 Critérios de Qualidade

- ✅ **≥ 90%** de documentos corretamente classificados
- ✅ **≥ 95%** de acurácia na identificação de pacientes  
- ✅ **≥ 95%** das requisições LLM concluídas em 240s (com timeout configurável)
- ✅ **100%** dos originais preservados (modo padrão)
- ✅ **100%** de detecção de duplicatas por hash SHA-256
- ✅ **0%** de custo LLM em documentos duplicados (economia via cache)

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

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir com o CliniKondo:

1. **Fork o projeto**
2. **Crie uma branch** para sua feature (`git checkout -b feature/MinhaNovaFeature`)
3. **Commit suas mudanças** (`git commit -m 'Adiciona MinhaNovaFeature'`)
4. **Push para a branch** (`git push origin feature/MinhaNovaFeature`)
5. **Abra um Pull Request**

### Diretrizes de Contribuição

- Siga as convenções de código do projeto (use `ruff` para linting)
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Mantenha o tom amigável e acessível do projeto

### Reportando Bugs

Encontrou um bug? Por favor, abra uma [issue](https://github.com/alisio/clinikondo/issues) com:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs. observado
- Versão do Python e sistema operacional
- Logs relevantes (use `--log-level debug`)

## 📜 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

### Resumo da Licença

```
MIT License

Copyright (c) 2025 CliniKondo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[...]
```

## 🙏 Agradecimentos

- Inspirado pelo método de organização **Marie Kondo**
- Desenvolvido com ❤️ para facilitar a vida de famílias que precisam gerenciar documentos médicos
- Agradecimentos especiais à comunidade open-source e aos projetos que tornaram isso possível

---

**Versão Atual:** 1.0.0  
**Status:** Em desenvolvimento ativo  
**Última Atualização:** Outubro 2025
