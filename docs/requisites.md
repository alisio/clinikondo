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
| `confianca_extracao`          | float     | Nível de confiança da extração LLM (0.0-1.0)                              |
| `metodo_extracao`             | enum      | Método usado (llm, ocr_regex, manual)                                      |
| `hash_arquivo`                | string    | Hash SHA-256 do arquivo original                                           |
| `tamanho_arquivo_bytes`       | integer   | Tamanho do arquivo em bytes                                                |
| `log_processamento`           | string    | Log da operação                                                            |

#### Validações

- Campos obrigatórios: `data_documento`, `tipo_documento`, `nome_paciente_inferido`  
- **Validação de arquivos**: Apenas formatos permitidos (pdf, jpg, png, tiff, docx)
- **Tamanho máximo**: 50MB por arquivo
- **Validação de nomes**: Caracteres seguros para sistemas de arquivos
- **Detecção de duplicatas**: Baseada em hash SHA-256
- Nome final do arquivo:
  - Formato: `aaaa-mm-nome_paciente-tipo-especialidade-descricao.extensao`  
  - Minúsculo, sem acentos, máximo 150 caracteres, seguro para sistemas de arquivos  

#### Ações

- `processar_documento`  
- `renomear_documento`  
- `copiar_documento`  
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
- Se sem correspondência, **novo paciente é criado automaticamente**  

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
- Outros: `laudo`, `relatorio`, `atestado`, `agenda`, `documento`, `formulario`  

#### Ações

- `inferir_tipo_documento`  
- `mapear_para_subpasta`  

---

### 🤖 4. Extração LLM

| Campo                | Tipo         | Descrição                                                         |
|----------------------|--------------|-------------------------------------------------------------------|
| `documento_id`       | string       | ID do documento analisado                                         |
| `texto_extraido`     | string       | OCR ou texto embutido                                             |
| `prompt_utilizado`   | string       | Prompt enviado ao LLM                                             |
| `resposta_bruta_llm` | string       | Texto/JSON recebido                                               |
| `dados_extraidos`    | dict         | Dados estruturados extraídos                                     |
| `modelo_utilizado`   | string       | Nome do modelo (ex: `gpt-4`)                                     |
| `data_extracao`      | datetime     | Data da requisição                                                |
| `tempo_resposta_ms`  | integer      | Duração da resposta                                               |
| `sucesso`            | boolean      | Status da extração                                                |
| `mensagem_erro`      | string       | Erro, se houver                                                   |

#### Regras

- Campos extraídos obrigatórios: `nome_paciente`, `data_documento`, `tipo_documento`  
- Prompt parametrizável via template com placeholders  
- Se falhar, documento **não é movido nem renomeado**  

---

### ⚙️ 5. Configuração do Sistema

| Campo                             | Fonte       | Valor Padrão            |
|-----------------------------------|-------------|--------------------------|
| `caminho_entrada`                | CLI / ENV   | —                        |
| `caminho_saida`                  | CLI / ENV   | —                        |
| `modelo_llm`                     | CLI / ENV   | `gpt-4`                  |
| `openai_api_key`                 | CLI / ENV   | —                        |
| `openai_api_base`                | CLI / ENV   | —                        |
| `llm_temperature`                | CLI / ENV   | `0.2`                    |
| `llm_max_tokens`                 | CLI / ENV   | `512`                    |
| `prompt_template_path`           | CLI / ENV   | `prompt_base.txt`        |
| `match_nome_paciente_auto`       | Interno     | `true`                   |
| `criar_paciente_sem_match`       | Interno     | `true`                   |
| `mover_para_compartilhado_sem_match` | Interno | `false`                  |
| `criar_pasta_desconhecidos`      | CLI / ENV   | `true`                   |
| `nome_padrao_paciente_desconhecido` | Interno  | `paciente_desconhecido`  |
| `tentativas_max_llm`             | CLI / ENV   | `3`                      |
| `timeout_llm_segundos`           | CLI / ENV   | `30`                     |
| `executar_copia_apos_erro`       | Interno     | `false`                  |
| `mover_arquivo_original`         | CLI / ENV   | `false`                  |
| `log_nivel`                      | CLI / ENV   | `info`                   |

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
- Se LLM não conseguir extrair nome válido:
  - Nome padrão: `paciente_desconhecido_AAAAMMDD_HHMMSS`
  - Exemplo: `paciente_desconhecido_20231015_143022`
  - Documento movido para pasta `Desconhecidos/` se habilitado  

### 🤖 Extração via LLM

- Utiliza modelo, temperatura e tokens configurados  
- Usa template de prompt customizável  
- **Sistema de retry**: Até 3 tentativas em caso de falha de rede/API
- **Timeout configurável**: Padrão 30 segundos por requisição
- **Fallback para OCR**: Se LLM falhar, tenta extração baseada em regex
- Em caso de erro total, documento não é copiado nem renomeado  

### 📄 Preservação do Arquivo Original

- **Comportamento padrão**: O arquivo original é **preservado** no local de origem  
- O documento processado é **copiado** para o destino com novo nome  
- Opção `--mover` no CLI permite mover (deletar original) se desejado  
- Se `mover_arquivo_original=true`, o arquivo original é removido após cópia bem-sucedida  

### � Preservação do Arquivo Original

- **Comportamento padrão**: O arquivo original é **preservado** no local de origem  
- O documento processado é **copiado** para o destino com novo nome  
- Opção `--mover` no CLI permite mover (deletar original) se desejado  
- Se `mover_arquivo_original=true`, o arquivo original é removido após cópia bem-sucedida

### �📝 Nome de Arquivo Final

```

aaaa-mm-nome_paciente-tipo-especialidade-descricao.extensao

````

- Exemplo: `2023-07-alicia_cordeiro-exame-cardiologia-eletrocardiograma.pdf`  

---

## 💻 Interface de Linha de Comando (CLI)

### 📌 Comandos Suportados

- `processar_documento --arquivo <caminho>`  
  Processa um único documento.

- `processar_lote --pasta <caminho>`  
  Processa todos os documentos de uma pasta.

- `listar_pacientes [--estatisticas]`  
  Exibe pacientes registrados e opcionalmente estatísticas.

- `verificar_duplicatas --pasta <caminho>`  
  Identifica possíveis documentos duplicados por hash.

- `relatorio_processamento [--periodo <dias>]`  
  Gera relatório de documentos processados.

- `validar_estrutura --pasta <caminho>`  
  Valida integridade da estrutura de pastas organizadas.

- `mostrar_log --arquivo <caminho>`  
  Exibe o log detalhado do processamento de um arquivo.

### 🧰 Parâmetros Comuns

| Parâmetro             | Tipo     | Descrição                                     |
|-----------------------|----------|-----------------------------------------------|
| `--arquivo`           | string   | Caminho do arquivo a ser processado           |
| `--pasta`             | string   | Caminho da pasta para processamento em lote   |
| `--modo-teste`        | boolean  | Executa sem copiar/renomear arquivos (dry-run) |
| `--mover`             | boolean  | Move arquivo original (padrão: copia e preserva) |
| `--skip-duplicatas`   | boolean  | Pula arquivos já processados (baseado em hash) |
| `--max-tentativas`    | integer  | Número máximo de tentativas para LLM (padrão: 3) |
| `--timeout`           | integer  | Timeout em segundos para LLM (padrão: 30) |
| `--forcar`            | boolean  | Ignora erros e força execução                 |
| `--verbose`           | boolean  | Saída detalhada (equivale a --log-nivel debug) |
| `--help`              | boolean  | Exibe ajuda                                   |

---

## 🧪 Casos de Uso

### 📥 Caso de Uso 1: Processar Documento Individual

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Usuário executa comando CLI com caminho de entrada         | Sistema localiza arquivo                                       |
| 2     | OCR e/ou extração de texto é executada                     | Texto extraído com sucesso                                     |
| 3     | LLM processa o texto com prompt parametrizado              | Dados estruturados retornados (`nome_paciente`, `tipo`, etc.) |
| 4     | Documento é renomeado e copiado para pasta do paciente     | Estrutura correta, nome final validado, original preservado |
| 5     | Log de processamento é salvo                               | Log em arquivo ou STDOUT detalha todas as etapas              |

### 📦 Caso de Uso 2: Processamento em Lote

| Etapa | Ação                                                       | Resultado Esperado                                             |
|-------|------------------------------------------------------------|----------------------------------------------------------------|
| 1     | Usuário executa comando CLI apontando pasta                | Todos os documentos são processados em sequência              |
| 2     | Falhas são registradas e não interrompem o lote            | Arquivos com erro são listados com motivo                     |
| 3     | Sucesso parcial é permitido                                | Apenas os arquivos válidos são renomeados/copiados            |
| 4     | Relatório final exibido                                    | Contagem de sucessos/falhas, tempos médios, etc.              |

---

## ✅ Critérios de Aceitação

| Requisito                                      | Critério de Aceitação                                           |
|-----------------------------------------------|------------------------------------------------------------------|
| Classificação correta de documentos            | ≥ 90% dos documentos corretamente classificados                  |
| Identificação de pacientes                     | ≥ 95% de acurácia com nomes padronizados ou variações            |
| Processamento em lote                          | Lotes de 100 arquivos devem ser concluídos em até 5 minutos      |
| Estrutura de pastas                            | 100% dos arquivos válidos devem ser realocados corretamente      |
| Preservação de originais                       | 100% dos arquivos originais preservados (exceto se `--mover`)    |
| Detecção de duplicatas                         | 100% de precisão na identificação por hash SHA-256              |
| Resiliência a falhas                          | Sistema deve continuar processamento mesmo com falhas parciais    |
| Tempo de resposta LLM                         | 95% das requisições concluídas em até 30 segundos               |
| Logging detalhado                              | Logs devem conter tempo total, erros e ações executadas          |

---

## 📜 Logging e Auditoria

### 🔍 Formato de Log por Documento

```json
{
  "arquivo": "entrada/documento_001.pdf",
  "hash_sha256": "a1b2c3d4e5f6...",
  "tamanho_bytes": 2048576,
  "status": "sucesso",
  "confianca_extracao": 0.95,
  "metodo_extracao": "llm",
  "tentativas_llm": 1,
  "paciente_identificado": "alicia_cordeiro",
  "tipo_documento": "exame",
  "especialidade": "cardiologia",
  "acoes": [
    "texto_extraido",
    "llm_extraido",
    "renomeado",
    "copiado"
  ],
  "erros": [],
  "warnings": ["baixa_confianca_data"],
  "duracao_total_ms": 3214,
  "timestamp": "2023-10-15T14:30:22Z"
}
````

### 🔧 Níveis de Log

| Nível     | Descrição                                  |
| --------- | ------------------------------------------ |
| `debug`   | Inclui todas as requisições, prompts, etc. |
| `info`    | Etapas principais e resultado              |
| `warning` | Problemas recuperáveis                     |
| `error`   | Falhas críticas (ex: falha na LLM)         |

---

## 🔐 Permissões

Como é um sistema CLI, permissões são implícitas no uso do terminal.
Podem ser expandidas se o sistema for exposto como API ou tiver interface multiusuário no futuro.

---

## ✅ Status

Especificação completa e robustamente atualizada.

* Todas as entidades definidas com campos, validações e ações aprimoradas
* Regras de negócio estabelecidas com tratamento de casos extremos
* Sistema de retry e fallback para maior resiliência 
* Detecção de duplicatas por hash SHA-256
* Validações de segurança e tamanho de arquivos
* Comportamento padrão para pacientes não identificados
* Parâmetros de configuração expandidos e flexíveis via CLI/ENV
* Comandos CLI adicionais para manutenção e relatórios
* Comportamento padrão para **copiar** (não mover) arquivos originais
* Logging estruturado com métricas detalhadas
* Critérios de aceitação robustos incluindo performance e resiliência
* Interface de CLI documentada com parâmetros avançados
