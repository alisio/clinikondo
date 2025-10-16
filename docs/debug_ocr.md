# 🐛 Modo Debug do CliniKondo - OCR e Extração de Texto

## Como Ativar o Modo Debug

Para ver o conteúdo extraído via OCR e outros detalhes da magia CliniKondo:

```bash
python -m clinikondo \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-oss:20b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --log-level debug \
  --dry-run
```

## 📋 O que Aparece no Modo Debug

### 1. **Extração de Texto Geral:**
```
DEBUG - Texto extraído de documento.pdf (245 chars): Este é um exemplo de texto extraído do documento...
```

### 2. **PDFs com Texto Embutido:**
```
DEBUG - PyPDF2 extraiu 123 caracteres de relatorio.pdf
```

### 3. **PDFs Escaneados (OCR):**
```
INFO - PDF sem texto embutido detectado, tentando OCR: exame_escaneado.pdf
DEBUG - Iniciando OCR em PDF com 3 páginas: exame_escaneado.pdf
DEBUG - OCR página 1/3 (87 chars): Resultado do exame de sangue realizado em 15/10/2025...
DEBUG - OCR página 2/3 (0 chars): nenhum texto encontrado
DEBUG - OCR página 3/3 (156 chars): Assinatura do médico responsável Dr. João Silva CRM 12345...
INFO - OCR concluído para exame_escaneado.pdf: 243 caracteres extraídos
DEBUG - OCR extraiu 243 caracteres de exame_escaneado.pdf: Resultado do exame de sangue...
```

### 4. **Imagens com OCR:**
```
DEBUG - OCR imagem receita.jpg (89 chars): Prescrição médica para paciente Maria Silva...
```

### 5. **Casos sem Texto:**
```
DEBUG - OCR página 2/3: nenhum texto encontrado
DEBUG - OCR imagem foto_borrosa.png: nenhum texto encontrado
```

## 🔍 Exemplo Completo

Suponha um PDF escaneado de um exame. No modo debug você verá:

```bash
INFO - Processando exame_hemograma.pdf
DEBUG - PyPDF2 extraiu 0 caracteres de exame_hemograma.pdf
INFO - PDF sem texto embutido detectado, tentando OCR: exame_hemograma.pdf
DEBUG - Iniciando OCR em PDF com 2 páginas: exame_hemograma.pdf
DEBUG - OCR página 1/2 (312 chars): LABORATÓRIO CLÍNICO XYZ
Exame: Hemograma Completo
Paciente: João Silva
Data: 15/10/2025
Resultado:
- Hemácias: 4.5 milhões/mm³
- Leucócitos: 7.200/mm³...
DEBUG - OCR página 2/2 (89 chars): Dr. Maria Santos
CRM: 98765
Responsável Técnico
DEBUG - OCR concluído para exame_hemograma.pdf: 401 caracteres extraídos
DEBUG - Texto extraído de exame_hemograma.pdf (401 chars): LABORATÓRIO CLÍNICO XYZ
Exame: Hemograma Completo...
```

## ⚙️ Configuração

### Variável de Ambiente:
```bash
export MEDIFOLDER_LOG_LEVEL=debug
```

### Arquivo de Configuração (.env):
```
MEDIFOLDER_LOG_LEVEL=debug
```

## 🎯 Casos de Uso

- **Verificar qualidade do OCR** em documentos escaneados
- **Debugar problemas** de extração de texto
- **Validar conteúdo** antes do processamento LLM
- **Identificar páginas problemáticas** em PDFs
- **Ajustar configurações** do Tesseract se necessário

## 📊 Níveis de Log Disponíveis

| Nível | Conteúdo |
|-------|----------|
| `error` | Apenas erros críticos |
| `warning` | Erros + avisos |
| `info` | Erros + avisos + informações gerais |
| `debug` | **Tudo** + detalhes do OCR e extração |