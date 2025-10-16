<!-- filepath: /Users/alisio/dev/medifolder/docs/requisites.md -->
# 🧾 Software Requirements Specification (SRS)

## 🏷️ Sistema: CliniKondo - Assistente de Organização Médica

### 📘 Descrição Geral

**CliniKondo** é o assistente que transforma o caos de exames, receitas e laudos em pura harmonia digital. Ele organiza os documentos médicos da família com leveza, humor e método — cada PDF encontra seu lugar e traz um pouco de alegria à pasta!

Sistema de linha de comando (CLI), compatível com macOS e Debian, para:

- Classificação automática de documentos médicos (PDFs e imagens) **exclusivamente via LLM**
- Extração de metadados via LLM (OpenAI, Ollama ou compatível)  
- **OCR automático** para PDFs escaneados e imagens
- Renomeação e organização dos arquivos em estrutura hierárquica por paciente e tipo  
- Criação automática de pastas e nomes padronizados  
- **Sistema inteligente de pacientes** com fuzzy matching e detecção de duplicatas
- **Comandos avançados** para gestão, validação e relatórios
- **Validações robustas** de arquivos com correção automática

---

## 🧱 Entidades

### 📄 1. Documento Médico

| Campo                          | Tipo      | Descrição                                                                  |
|-------------------------------|-----------|----------------------------------------------------------------------------|
| `caminho_entrada`             | string    | Caminho original do arquivo                                                |
| `nome_arquivo_original`       | string    | Nome original do arquivo                                                   |
| `formato`                     | enum      | Formato do arquivo (pdf, png, jpg, jpeg, tif, tiff, heic, txt)            |
| `texto_extraido`              | string    | Texto extraído via PyPDF2 ou OCR (Tesseract+PyMuPDF)                     |
| `nome_paciente_inferido`      | string    | Nome inferido via LLM                                                      |
| `data_documento`              | date      | Data extraída do conteúdo                                                  |
| `tipo_documento`              | string    | Categoria (exame, receita, vacina, controle, contato, laudo, agenda, documento) |
| `especialidade`               | string    | Área médica relacionada                                                    |
| `descricao_curta`             | string    | Descrição curta (até 4 termos ou 60 caracteres)                            |
| `nome_arquivo_final`          | string    | Nome padronizado final do arquivo                                          |
| `caminho_destino`             | string    | Caminho de destino                                                         |
| `classificado_como_compartilhado` | boolean | Se foi alocado em pasta Compartilhado                                     |
| `confianca_extracao`          | float     | Nível de confiança da extração LLM (0.0-1.0)                              |
| `metodo_extracao`             | enum      | Sempre "llm" (fallback removido)                                          |
| `hash_arquivo`                | string    | Hash SHA-256 do arquivo original                                           |
| `tamanho_arquivo_bytes`       | integer   | Tamanho do arquivo em bytes                                                |
| `log_processamento`           | string    | Log estruturado da operação                                                |

#### Validações

- Campos obrigatórios: `data_documento`, `tipo_documento`, `nome_paciente_inferido`  
- **Formatos suportados**: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.heic`, `.txt`
- **Tamanho máximo**: 50MB por arquivo
- **Caracteres perigosos**: Detecção e correção automática de nomes problemáticos
- **Detecção de duplicatas**: Baseada em hash SHA-256
- **Arquivos vazios**: Rejeitados automaticamente
- Nome final do arquivo:
  - Formato: `aaaa-mm-nome_paciente-tipo-especialidade-descricao.extensao`  
  - Minúsculo, sem acentos, máximo 150 caracteres, seguro para sistemas de arquivos  

#### Ações

- `processar_documento`  
- `renomear_documento`  
- `copiar_documento` (padrão)
- `mover_documento` (opcional com `--mover`)
- `validar_documento`  

---

### 👤 2. Paciente

| Campo                  | Tipo         | Descrição                                                  |
|------------------------|--------------|-------------------------------------------------------------|
| `nome_completo`        | string       | Nome principal do paciente                                  |
| `nomes_alternativos`   | list<string> | Variações, apelidos e aliases                               |
| `slug_diretorio`       | string       | Nome da pasta (ex: `alicia_cordeiro`)                       |
| `data_nascimento`      | date         | (Opcional)                                                  |
| `genero`               | enum         | (Opcional) masculino, feminino, outro                       |
| `documentos_associados`| list<string> | IDs dos documentos relacionados                             |
| `data_criacao`         | datetime     | Quando o paciente foi registrado                            |
| `similaridade_threshold` | float      | Limite para detecção de duplicatas (padrão: 0.8)           |

#### Ações

- `adicionar_paciente`  
- `editar_paciente`  
- `remover_paciente`
- `fusionar_pacientes`
- `detectar_duplicatas_paciente`
- `reconciliar_nome` (com fuzzy matching)
- `adicionar_alias`
- `verificar_correspondencia_nome_llm`  

#### Regras de Fuzzy Matching

- **Correspondência exata**: Primeiro, busca nome completo e aliases exatos
- **Fuzzy matching**: Se não encontrar, usa `difflib.SequenceMatcher` com threshold 0.8
- **Normalização**: Remove acentos, converte para minúsculas, padroniza espaços
- **Detecção de conflitos**: Impede aliases duplicados entre pacientes diferentes
- **Criação automática**: Se sem correspondência, novo paciente é criado automaticamente  

---

### 📂 3. Tipo de Documento

| Campo               | Tipo         | Descrição                                                        |
|---------------------|--------------|------------------------------------------------------------------|
| `nome_tipo`         | string       | Nome do tipo (ex: `exame`, `receita`)                            |
| `subpasta_destino`  | string       | Nome sanitizado da subpasta (minúsculo, sem acento, com `_`)     |
| `palavras_chave`    | list<string> | Palavras relacionadas ao tipo                                    |
| `especialidades_rel`| list<string> | Especialidades médicas associadas                                |
| `requer_data`       | boolean      | Se o tipo exige data obrigatória                                 |

#### Tipos de Documento Suportados

- `exame` → `exames` (palavras-chave: "exame", "resultado", "imagem", "ultrassom", "laboratorio")
- `receita` → `receitas_medicas` (palavras-chave: "receita", "prescricao", "medicamento")
- `vacina` → `vacinas` (palavras-chave: "vacina", "imunizacao", "dose", "cartao")
- `controle` → `controle_de_pressao_e_glicose` (palavras-chave: "pressao", "glicose", "monitoramento")
- `contato` → `contatos_medicos` (palavras-chave: "contato", "telefone", "endereco", "clinica")
- `laudo` → `laudos` (palavras-chave: "laudo", "relatorio", "atestado")
- `agenda` → `agendas` (palavras-chave: "agenda", "consulta", "agendamento")
- `documento` → `documentos` (palavras-chave: "documento", "formulario") - **tipo padrão/fallback**

#### Sistema de Sinônimos

- `relatorio` → `laudo`
- `resultado` → `exame`
- `exame_laboratorial` → `exame`
- `teste` → `exame`
- `atestado` → `laudo`
- `declaracao` → `documento`
- `formulario` → `documento`
- `comprovante` → `documento`

#### Ações

- `inferir_tipo_documento`  
- `mapear_para_subpasta`
- `resolver_sinonimo`
- `fuzzy_match_tipo`  

---

### 🤖 4. Extração LLM

| Campo                | Tipo         | Descrição                                                         |
|----------------------|--------------|-------------------------------------------------------------------|
| `documento_id`       | string       | ID do documento analisado                                         |
| `texto_extraido`     | string       | Texto via PyPDF2, OCR (PyMuPDF+Tesseract) ou extração direta     |
| `prompt_utilizado`   | string       | Prompt estruturado enviado ao LLM                                 |
| `resposta_bruta_llm` | string       | Texto/JSON recebido do LLM                                        |
| `dados_extraidos`    | dict         | Dados estruturados extraídos                                     |
| `modelo_utilizado`   | string       | Nome do modelo (ex: `gpt-4`, `gpt-oss:20b`)                     |
| `api_base`           | string       | Endpoint da API (OpenAI ou Ollama)                                |
| `data_extracao`      | datetime     | Data da requisição                                                |
| `tempo_resposta_ms`  | integer      | Duração da resposta                                               |
| `tentativa_numero`   | integer      | Número da tentativa (1-3)                                         |
| `sucesso`            | boolean      | Status da extração                                                |
| `confianca_calculada`| float        | Confiança baseada em campos obrigatórios presentes               |
| `mensagem_erro`      | string       | Erro detalhado, se houver                                         |

#### Configuração LLM

- **Modelos suportados**: OpenAI (gpt-4, gpt-3.5-turbo) e Ollama (qualquer modelo)
- **Temperatura**: 0.3 (padrão, configurável)
- **Max tokens**: 1024 (padrão, configurável)  
- **Timeout**: 30 segundos por requisição
- **Retry**: Até 3 tentativas em caso de falha
- **Prompt estruturado**: Categorias e especialidades válidas incluídas

#### Regras

- **LLM obrigatório**: Sistema não funciona sem configuração de LLM válida
- **Campos extraídos obrigatórios**: `nome_paciente`, `data_documento`, `tipo_documento`  
- **Prompt com categorias**: LLM recebe lista de categorias e especialidades válidas
- **Tratamento de markdown**: Remove automaticamente ```json das respostas
- **Validação de JSON**: Verifica estrutura antes de processar
- **Se falhar**: Documento **não é processado** (sem fallback)  

---

### ⚙️ 5. Configuração do Sistema

| Campo                             | Fonte       | Valor Padrão            |
|-----------------------------------|-------------|--------------------------|
| `input_dir`                      | CLI         | — (obrigatório)          |
| `output_dir`                     | CLI         | — (obrigatório)          |
| `modelo_llm`                     | CLI / ENV   | `gpt-4`                  |
| `openai_api_key`                 | CLI / ENV   | — (obrigatório)          |
| `openai_api_base`                | CLI / ENV   | `https://api.openai.com/v1` |
| `llm_temperature`                | CLI / ENV   | `0.3`                    |
| `llm_max_tokens`                 | CLI / ENV   | `1024`                   |
| `timeout_llm_segundos`           | CLI / ENV   | `30`                     |
| `tentativas_max_llm`             | CLI / ENV   | `3`                      |
| `prompt_template_path`           | CLI / ENV   | (hardcoded no código)    |
| `match_nome_paciente_auto`       | Interno     | `true`                   |
| `criar_paciente_sem_match`       | Interno     | `true`                   |
| `mover_para_compartilhado_sem_match` | Interno | `false`                  |
| `mover_arquivo_original`         | CLI         | `false`                  |
| `executar_copia_apos_erro`       | Interno     | `false`                  |
| `log_nivel`                      | CLI         | `info`                   |
| `dry_run`                        | CLI         | `false`                  |

#### Validações Obrigatórias

- **OPENAI_API_KEY**: Deve estar definida (mesmo para Ollama, use "mock-key")
- **Pastas**: `--input` e `--output` são obrigatórios
- **Formatos**: Apenas arquivos com extensões suportadas são processados
- **Tamanho**: Arquivos > 50MB são rejeitados
- **Conectividade**: Valida se endpoint LLM está acessível

---

## 🔁 Regras de Negócio

### 🎯 Identificação de Paciente com Fuzzy Matching

1. **Busca exata**: Nome completo e aliases conhecidos
2. **Fuzzy matching**: `difflib.SequenceMatcher` com threshold 0.8
3. **Normalização**: Remove acentos, converte para minúsculas, padroniza espaços
4. **Se não encontrar**: Novo paciente criado automaticamente
5. **Sistema de aliases**: Permite múltiplos nomes para mesmo paciente
6. **Detecção de conflitos**: Impede aliases duplicados

### 🤖 Extração Exclusiva via LLM

- **LLM obrigatório**: Sistema requer configuração válida de LLM
- **Sem fallback**: Não há extração heurística ou regex
- **Prompt estruturado**: Inclui categorias e especialidades válidas
- **Sistema de retry**: Até 3 tentativas com timeout de 30s cada
- **Markdown parsing**: Remove automaticamente ```json das respostas
- **Confiança calculada**: Baseada em campos obrigatórios extraídos
- **Falha = não processa**: Se LLM falhar, documento não é movido

### 📄 OCR Automático para PDFs Escaneados

- **Detecção automática**: Se PyPDF2 não extrair texto, aplica OCR
- **PyMuPDF + Tesseract**: Converte páginas PDF em imagens e extrai texto
- **Suporte a português**: OCR configurado para língua portuguesa
- **Página por página**: Processa cada página separadamente e combina
- **Logs detalhados**: Em modo debug, mostra conteúdo extraído via OCR
- **Fallback graceful**: Se OCR falhar, continua com texto vazio

### 📁 Preservação do Arquivo Original

- **Comportamento padrão**: Arquivo original é **preservado** no local de origem  
- **Cópia para destino**: Documento é copiado para estrutura organizada
- **Opção `--mover`**: Remove original após cópia bem-sucedida  
- **Validação antes de mover**: Confirma que cópia foi bem-sucedida

### 🛡️ Validações e Segurança

- **Tamanho máximo**: 50MB por arquivo
- **Formatos permitidos**: Lista específica de extensões médicas
- **Caracteres perigosos**: Detecção e correção automática
- **Arquivos vazios**: Rejeitados automaticamente  
- **Detecção de duplicatas**: Hash SHA-256 para identificar arquivos idênticos
- **Nomes seguros**: Sanitização para compatibilidade de sistemas de arquivos

---

## 💻 Interface de Linha de Comando (CLI)

### 📌 Comandos Principais

#### 🎯 **`processar`** - Organizar documentos médicos
```bash
python -m src.clinikondo processar --input <pasta> --output <pasta> [opções]
```

#### 👥 **`listar-pacientes`** - Gerenciar pacientes registrados
```bash
python -m src.clinikondo listar-pacientes [--formato json|tabela|csv] [--filtro <texto>]
```

#### 🔍 **`verificar-duplicatas`** - Detectar arquivos duplicados
```bash
python -m src.clinikondo verificar-duplicatas --pasta <pasta> [--acao listar|remover|mover]
```

#### 📊 **`relatorio-processamento`** - Gerar relatórios
```bash
python -m src.clinikondo relatorio-processamento --pasta <pasta> [--formato texto|json|html]
```

#### ✅ **`validar-estrutura`** - Validar arquivos
```bash
python -m src.clinikondo validar-estrutura --pasta <pasta> [--corrigir]
```

#### 📋 **`mostrar-log`** - Exibir logs
```bash
python -m src.clinikondo mostrar-log [--arquivo <caminho>] [--nivel debug|info|warning|error]
```

#### 🔧 **`gerenciar-pacientes`** - Interface de gestão de pacientes
```bash
# Adicionar paciente
python -m src.clinikondo gerenciar-pacientes adicionar --nome "<nome>" [--genero <genero>]

# Editar paciente  
python -m src.clinikondo gerenciar-pacientes editar --paciente <slug> [--nome <novo_nome>] [--alias <alias>]

# Remover paciente
python -m src.clinikondo gerenciar-pacientes remover --paciente <slug>

# Fusionar pacientes
python -m src.clinikondo gerenciar-pacientes fusionar --origem <slug1> --destino <slug2>

# Detectar duplicatas
python -m src.clinikondo gerenciar-pacientes detectar-duplicatas [--threshold 0.8]
```

### 🧰 Parâmetros Comuns

| Parâmetro             | Tipo     | Descrição                                     |
|-----------------------|----------|-----------------------------------------------|
| `--input`             | string   | Pasta de documentos a serem processados       |
| `--output`            | string   | Pasta de destino organizada                   |
| `--model`             | string   | Modelo LLM (gpt-4, gpt-oss:20b, etc.)        |
| `--api-key`           | string   | Chave da API (ou mock-key para Ollama)       |
| `--api-base`          | string   | URL do endpoint (ex: http://localhost:11434/v1) |
| `--temperature`       | float    | Temperatura do LLM (0.0-1.0, padrão: 0.3)    |
| `--max-tokens`        | integer  | Tokens máximos por resposta (padrão: 1024)    |
| `--timeout`           | integer  | Timeout em segundos (padrão: 30)             |
| `--dry-run`           | boolean  | Executa sem mover/copiar arquivos (teste)     |
| `--mover`             | boolean  | Move arquivo original (padrão: copia e preserva) |
| `--log-level`         | string   | Nível de log (debug, info, warning, error)   |
| `--help`              | boolean  | Exibe ajuda do comando                        |

---

## 🧪 Casos de Uso

### 📥 Caso de Uso 1: Processar Documentos com LLM

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Usuário executa `processar` com pastas input/output       | Sistema valida configuração LLM e pastas                      |
| 2     | Sistema encontra arquivos suportados na pasta input        | Lista de arquivos .pdf, .jpg, etc. é criada                   |
| 3     | Para cada arquivo: extração de texto (PyPDF2 ou OCR)      | Texto extraído com sucesso ou OCR aplicado automaticamente    |
| 4     | LLM processa texto com prompt estruturado                 | JSON estruturado retornado com metadados extraídos            |
| 5     | Fuzzy matching identifica ou cria paciente                | Paciente existente encontrado ou novo paciente criado         |
| 6     | Documento é renomeado e copiado para pasta do paciente    | Estrutura hierárquica criada, original preservado             |
| 7     | Log estruturado é gerado                                   | Métricas de processamento salvas em formato JSON              |

### 👥 Caso de Uso 2: Gerenciamento Inteligente de Pacientes

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Sistema detecta nome similar durante processamento         | Fuzzy matching identifica possível duplicata                  |
| 2     | Usuário executa `gerenciar-pacientes detectar-duplicatas` | Lista de possíveis pacientes duplicados é exibida             |
| 3     | Usuário confirma fusão com `fusionar`                     | Pacientes são mesclados preservando aliases                   |
| 4     | Documentos são reorganizados automaticamente              | Estrutura de pastas atualizada para paciente unificado        |
| 5     | Aliases são consolidados                                   | Todas as variações de nome ficam disponíveis para match       |

### 🔍 Caso de Uso 3: Validação e Correção Automática

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Usuário executa `validar-estrutura --corrigir`            | Sistema escanceia arquivos em busca de problemas              |
| 2     | Arquivos com nomes problemáticos são detectados           | Lista de problemas é exibida (caracteres perigosos, etc.)     |
| 3     | Sistema oferece correções automáticas                     | Nomes são sanitizados automaticamente                         |
| 4     | Arquivos muito grandes ou formatos inválidos são listados | Relatório completo de problemas é gerado                      |
| 5     | Duplicatas são identificadas por hash                      | Ações de limpeza são sugeridas                                |

### 📊 Caso de Uso 4: Relatórios e Monitoramento

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Usuário executa `relatorio-processamento --formato html`  | Sistema analisa pasta organizada                              |
| 2     | Estatísticas de pacientes e documentos são coletadas      | Contadores por tipo, especialidade, período são calculados    |
| 3     | Relatório visual é gerado                                  | HTML com gráficos e tabelas é criado                          |
| 4     | Duplicatas e problemas são destacados                      | Seção de limpeza sugerida é incluída                          |
| 5     | Métricas de qualidade são exibidas                        | Taxa de sucesso, confiança média, etc.                        |

---

## ✅ Critérios de Aceitação

| Requisito                                      | Critério de Aceitação                                           |
|-----------------------------------------------|------------------------------------------------------------------|
| Extração LLM obrigatória                      | 100% dos processamentos usam LLM (sem fallback)                 |
| Classificação correta de documentos            | ≥ 90% dos documentos corretamente classificados                  |
| Identificação de pacientes com fuzzy matching  | ≥ 95% de acurácia incluindo variações de nome                   |
| OCR automático para PDFs escaneados           | 100% dos PDFs sem texto têm OCR aplicado automaticamente        |
| Validações de arquivo                          | 100% dos arquivos inválidos são rejeitados com motivo claro     |
| Comandos CLI avançados                         | Todos os 7 comandos principais funcionais                       |
| Preservação de originais                       | 100% dos arquivos originais preservados (exceto com `--mover`)  |
| Detecção de duplicatas                         | 100% de precisão na identificação por hash SHA-256              |
| Sistema de pacientes                           | Fuzzy matching com threshold configurável funcional             |
| Resiliência a falhas                          | Sistema deve falhar graciosamente com logs claros               |
| Tempo de resposta LLM                         | 95% das requisições concluídas em até 30 segundos               |
| Logging estruturado                            | Logs JSON detalhados para auditoria e debug                     |

---

## 📜 Logging e Auditoria

### 🔍 Formato de Log Estruturado por Documento

```json
{
  "timestamp": "2023-10-15T14:30:22Z",
  "arquivo_original": "entrada/exame_joao.pdf",
  "hash_sha256": "a1b2c3d4e5f6...",
  "tamanho_bytes": 2048576,
  "formato_arquivo": "pdf",
  "metodo_extracao_texto": "ocr",  // "pypdf2" ou "ocr"
  "ocr_aplicado": true,
  "paginas_processadas": 3,
  "chars_extraidos": 1247,
  "llm_config": {
    "modelo": "gpt-oss:20b",
    "api_base": "http://localhost:11434/v1",
    "temperatura": 0.3,
    "max_tokens": 1024,
    "timeout": 30
  },
  "extracao_llm": {
    "tentativas": 1,
    "sucesso": true,
    "tempo_resposta_ms": 3214,
    "confianca_calculada": 0.95,
    "campos_extraidos": ["nome_paciente", "data_documento", "tipo_documento", "especialidade"],
    "prompt_chars": 2156,
    "resposta_chars": 312
  },
  "paciente": {
    "nome_extraido": "João Silva Santos",
    "paciente_correspondido": "joao_silva_santos",
    "metodo_match": "fuzzy",  // "exato", "fuzzy", "criado"
    "similaridade_score": 0.87,
    "aliases_utilizados": ["João Silva", "Joãozinho"]
  },
  "documento_final": {
    "nome_arquivo_final": "2023-10-joao_silva_santos-exame-cardiologia-eletrocardiograma.pdf",
    "pasta_destino": "saida/joao_silva_santos/exames/",
    "acao_executada": "copiado",  // "copiado" ou "movido"
    "estrutura_criada": true
  },
  "validacoes": {
    "tamanho_valido": true,
    "formato_suportado": true,
    "caracteres_seguros": true,
    "arquivo_duplicado": false
  },
  "status_final": "sucesso",
  "duracao_total_ms": 8456,
  "erros": [],
  "warnings": ["confianca_data_baixa"]
}
```

### 🔧 Níveis de Log

| Nível     | Descrição                                  | Exemplo de Uso                                |
| --------- | ------------------------------------------ | --------------------------------------------- |
| `debug`   | OCR detalhado, prompts LLM, fuzzy matching | `--log-level debug` mostra texto extraído via OCR |
| `info`    | Etapas principais e resultado final        | Processamento padrão com métricas             |
| `warning` | Problemas recuperáveis                     | Baixa confiança, caracteres sanitizados      |
| `error`   | Falhas críticas                           | LLM inacessível, arquivo corrompido           |

### 📊 Comandos de Auditoria

```bash
# Ver logs de debug com OCR detalhado
python -m src.clinikondo processar --input docs/ --output organizados/ --log-level debug

# Gerar relatório de processamento
python -m src.clinikondo relatorio-processamento --pasta organizados/ --formato json

# Validar integridade pós-processamento
python -m src.clinikondo validar-estrutura --pasta organizados/

# Verificar duplicatas por hash
python -m src.clinikondo verificar-duplicatas --pasta organizados/ --acao listar
```

---

## 🏗️ Arquitetura e Dependências

### 📚 Dependências Principais

- **openai**: Cliente para APIs OpenAI e compatíveis (Ollama)
- **PyPDF2**: Extração de texto de PDFs com texto embutido
- **PyMuPDF (fitz)**: Conversão de PDFs em imagens para OCR
- **pytesseract**: OCR via Tesseract Engine
- **Pillow**: Processamento de imagens
- **argparse**: Interface CLI nativa do Python
- **difflib**: Fuzzy matching para nomes de pacientes
- **hashlib**: Geração de hashes SHA-256 para duplicatas

### 🏛️ Estrutura de Módulos

```
src/clinikondo/
├── __main__.py          # Interface CLI com subcomandos
├── config.py            # Configuração e validações
├── processing.py        # Processamento de documentos e OCR
├── llm.py              # Extração via LLM (OpenAI/Ollama)
├── patients.py         # Sistema de pacientes com fuzzy matching
├── types.py            # Tipos de documentos e mapeamento
├── models.py           # Estruturas de dados (dataclasses)
└── utils.py            # Utilitários e funções auxiliares
```

---

## 🔐 Segurança e Privacidade

### 🛡️ Proteção de Dados

- **Processamento local**: Documentos médicos permanecem na máquina do usuário
- **APIs externa**: Apenas texto extraído é enviado ao LLM (sem imagens)
- **Logs seguros**: Não armazenam conteúdo médico, apenas metadados
- **Validação de entrada**: Rejeita arquivos suspeitos ou muito grandes
- **Sanitização**: Remove caracteres perigosos de nomes de arquivos

### 🔑 Configuração Segura

- **Variáveis de ambiente**: API keys não ficam em linha de comando
- **Timeouts**: Evita travamentos em requisições LLM
- **Fallback graceful**: Sistema não quebra com falhas de rede
- **Validação de endpoints**: Confirma conectividade antes de processar lote

---

## ✅ Status de Implementação

### 🎯 **COMPLETO** - Funcionalidades Core
- ✅ Extração exclusiva via LLM (sem fallback)
- ✅ OCR automático para PDFs escaneados (PyMuPDF + Tesseract)
- ✅ Sistema de pacientes com fuzzy matching
- ✅ Comandos CLI avançados (7 comandos implementados)
- ✅ Validações robustas de arquivos
- ✅ Detecção de duplicatas por hash SHA-256
- ✅ Logging estruturado em JSON
- ✅ Preservação de arquivos originais por padrão

### 🎯 **COMPLETO** - Interface e Usabilidade  
- ✅ CLI com subcomandos e ajuda contextual
- ✅ Mensagens com emojis e feedback claro
- ✅ Modo debug com OCR detalhado
- ✅ Relatórios em múltiplos formatos (JSON, HTML, tabela)
- ✅ Correção automática de problemas detectados

### 🎯 **COMPLETO** - Robustez e Qualidade
- ✅ Sistema de retry com timeout configurável
- ✅ Tratamento gracioso de falhas
- ✅ Validação completa de configuração
- ✅ Testes funcionais validados
- ✅ Documentação técnica atualizada

---

**CliniKondo está completamente implementado e alinhado com esta especificação!** 🎉

---

*"Cada documento encontra seu lugar e traz um pouco de alegria à pasta!"* ✨
