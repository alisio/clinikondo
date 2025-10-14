# 🧾 Software Requirements Specification (SRS)

## 🏷️ Sistema: Classificador Automatizado de Documentos Médicos Familiares com Extração via LLM

### 📘 Descrição Geral

Sistema de linha de comando (CLI), compatível com macOS e Debian, para:

- Classificação automática de documentos médicos (PDFs e imagens)
- Extração de metadados via LLM (OpenAI ou compatível)
- Renomeação e organização dos arquivos em estrutura hierárquica por paciente e tipo
- Criação automática de pastas e nomes padronizados
- Identificação automática do paciente e tipo de documento, mesmo com nomes abreviados ou inconsistentes

---

## 🧱 Entidades

### 📄 1. Documento Médico

| Campo                          | Tipo      | Descrição                                                                  |
|-------------------------------|-----------|----------------------------------------------------------------------------|
| `caminho_entrada`             | string    | Caminho original do arquivo                                                |
| `nome_arquivo_original`       | string    | Nome original do arquivo                                                   |
| `formato`                     | enum      | Formato do arquivo (pdf, jpg, png, etc.)                                   |
| `texto_extraido`              | string    | Texto extraído via OCR (se aplicável)                                      |
| `nome_paciente_inferido`      | string    | Nome inferido via LLM                                                      |
| `data_documento`              | date      | Data extraída do conteúdo                                                  |
| `tipo_documento`              | string    | Categoria (exame, receita, etc.)                                           |
| `especialidade`               | string    | Área médica relacionada                                                    |
| `descricao_curta`             | string    | Descrição curta (até 4 termos ou 60 caracteres)                            |
| `nome_arquivo_final`          | string    | Nome padronizado final do arquivo                                          |
| `caminho_destino`             | string    | Caminho de destino                                                         |
| `classificado_como_compartilhado` | boolean | Se foi alocado em pasta Compartilhado                                     |
| `log_processamento`           | string    | Log da operação                                                            |

#### Validações
- Campos obrigatórios: `data_documento`, `tipo_documento`, `nome_paciente_inferido`
- Nome final do arquivo:
  - Formato: `aaaa-mm-nome_paciente-tipo-especialidade-descricao.extensao`
  - Minúsculo, sem acentos, 150 caracteres máx, seguro para sistemas de arquivos

#### Ações
- `processar_documento`
- `renomear_documento`
- `mover_documento`
- `descartar_documento`

---

### 👤 2. Paciente

| Campo                  | Tipo         | Descrição                                                  |
|------------------------|--------------|-------------------------------------------------------------|
| `nome_completo`        | string       | Nome principal do paciente                                  |
| `nomes_alternativos`   | list<string> | Variações e apelidos usados                                 |
| `slug_diretorio`       | string       | Nome da pasta (ex: `alicia_cordeiro`)                       |
| `data_nascimento`      | date         | (Opcional)                                                  |
| `genero`               | enum         | (Opcional) M, F ou outro                                    |
| `documentos_associados`| list<string> | IDs dos documentos relacionados                             |

#### Ações
- `cadastrar_paciente`
- `atualizar_paciente`
- `reconciliar_nome`
- `verificar_correspondencia_nome_llm`

#### Regras
- Correspondência automática via LLM
- Se sem correspondência, **cria novo paciente automaticamente**

---

### 📂 3. Tipo de Documento

| Campo               | Tipo         | Descrição                                                        |
|---------------------|--------------|------------------------------------------------------------------|
| `nome_tipo`         | string       | Nome do tipo (ex: `exame`, `receita`)                            |
| `subpasta_destino`  | string       | Nome sanitizado da subpasta (minúsculo, sem acento, com `_`)     |
| `palavras_chave`    | list<string> | Palavras relacionadas ao tipo                                    |
| `especialidades_rel`| list<string> | Especialidades médicas associadas                                |
| `requer_data`       | boolean      | Se o tipo exige data obrigatória                                 |

#### Exemplos de Tipos

- `exame` → `exames`
- `receita` → `receitas_medicas`
- `vacina` → `vacinas`
- `controle` → `controle_de_pressao_e_glicose`
- `contato` → `contatos_medicos`
- `laudo`, `relatorio`, `atestado`, `agenda`, `documento`, `formulario`...

#### Ações
- `inferir_tipo_documento`
- `mapear_para_subpasta`

---

### 🤖 4. Extração LLM

| Campo                | Tipo         | Descrição                                                         |
|----------------------|--------------|-------------------------------------------------------------------|
| `documento_id`       | string       | ID do documento analisado                                        |
| `texto_extraido`     | string       | OCR ou texto embutido                                            |
| `prompt_utilizado`   | string       | Prompt enviado ao LLM                                            |
| `resposta_bruta_llm` | string       | Texto/JSON recebido                                               |
| `dados_extraidos`    | dict         | Dados estruturados extraídos                                     |
| `modelo_utilizado`   | string       | Nome do modelo (ex: `gpt-4`)                                     |
| `data_extracao`      | datetime     | Data da requisição                                               |
| `tempo_resposta_ms`  | integer      | Duração da resposta                                               |
| `sucesso`            | boolean      | Status da extração                                                |
| `mensagem_erro`      | string       | Erro, se houver                                                   |

#### Regras
- Campos extraídos obrigatórios: `nome_paciente`, `data_documento`, `tipo_documento`
- Prompt parametrizável via template com placeholders
- Se falhar, documento **não é movido/copied**

---

### ⚙️ 5. Configuração do Sistema

| Campo                             | Fonte       | Valor Padrão |
|-----------------------------------|-------------|---------------|
| `caminho_entrada`                | CLI / ENV   | —             |
| `caminho_saida`                  | CLI / ENV   | —             |
| `modelo_llm`                     | CLI / ENV   | `gpt-4`       |
| `openai_api_key`                 | CLI / ENV   | —             |
| `openai_api_base`                | CLI / ENV   | —             |
| `llm_temperature`               | CLI / ENV   | `0.2`         |
| `llm_max_tokens`                | CLI / ENV   | `512`         |
| `prompt_template_path`          | CLI / ENV   | `prompt_base.txt` |
| `match_nome_paciente_auto`      | Interno     | `true`        |
| `criar_paciente_sem_match`      | Interno     | `true`        |
| `mover_para_compartilhado_sem_match` | Interno | `false`       |
| `executar_copia_apos_erro`      | Interno     | `false`       |
| `log_nivel`                     | CLI / ENV   | `info`        |

#### Ações
- `carregar_configuracao`
- `validar_configuracao`
- `exportar_configuracao`

---

## 🔁 Regras de Negócio

### 🎯 Identificação de Paciente
- Nome inferido é reconciliado com base de pacientes conhecidos
- Se não houver correspondência:
  - LLM tenta inferir correspondência
  - Se falhar, **novo paciente é criado automaticamente**

### 🤖 Extração via LLM
- Utiliza modelo, temperatura, e tokens configurados
- Usa template de prompt customizável
- Em caso de erro, documento não é movido nem nomeado

### 📝 Nome de Arquivo Final
```

aaaa-mm-nome_paciente-tipo-especialidade-descricao.extensao

```
- Exemplo: `2023-07-alicia_cordeiro-exame-cardiologia-eletrocardiograma.pdf`

---

## 🔐 Permissões

Como é um sistema CLI, permissões são implícitas no uso do terminal.  
Podem ser expandidas se o sistema for exposto como API ou tiver interface multiusuário no futuro.

---

## ✅ Status

Especificação completa concluída.

- Todas as entidades definidas com campos, validações e ações
- Regras de negócio bem estabelecidas
- Parâmetros de configuração padronizados e flexíveis via CLI/ENV

---
