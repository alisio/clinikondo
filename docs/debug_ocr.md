# 🐛 CliniKondo Debug - OCR e Extração de Texto Mágica ✨

## Como Ativar o Modo Debug

Para ver o conteúdo extraído via OCR e outros detalhes da magia CliniKondo:

```bash
python -m clinikondo processar \
  --input ~/clinikondo/entrada \
  --output ~/clinikondo/saida \
  --model gpt-oss:20b \
  --api-base http://localhost:11434/v1 \
  --api-key mock-key \
  --ocr-strategy hybrid \
  --log-level debug \
  --dry-run
```

### Configuração Multi-Modelo (Opcional)

A aplicação suporta modelos separados para OCR e classificação:

```bash
# OCR local (Ollama) + Classificação cloud (OpenAI)
python -m clinikondo processar \
  --input ~/docs \
  --output ~/organizados \
  --model gpt-3.5-turbo \
  --api-key sk-... \
  --ocr-model llama3.2-vision \
  --ocr-api-base http://localhost:11434/v1 \
  --ocr-api-key mock-key \
  --ocr-strategy multimodal \
  --log-level debug
```

## 🎯 Estratégias de OCR

CliniKondo suporta **3 estratégias de OCR** para máxima flexibilidade:

| Estratégia | Descrição | Quando Usar |
|-----------|-----------|-------------|
| `hybrid` (padrão) | PyPDF2 → Multimodal → Traditional | Máxima compatibilidade e qualidade |
| `multimodal` | Apenas LLM multimodal (GPT-4 Vision) | Documentos complexos, melhor precisão |
| `traditional` | Apenas Tesseract OCR | Documentos simples, máxima velocidade |

### Exemplo com cada estratégia:

```bash
# Estratégia Híbrida (padrão - melhor de ambos)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --ocr-strategy hybrid

# Estratégia Multimodal (apenas LLM Vision)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --model gpt-4-vision-preview \
  --ocr-strategy multimodal

# Estratégia Tradicional (apenas Tesseract)
python -m clinikondo processar \
  --input docs/ --output saida/ \
  --ocr-strategy traditional
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

### 3. **PDFs Escaneados (OCR Tradicional):**
```
INFO - PDF sem texto embutido detectado, tentando OCR: exame_escaneado.pdf
DEBUG - Iniciando OCR tradicional em PDF com 3 páginas: exame_escaneado.pdf
DEBUG - OCR tradicional página 1/3 (87 chars): Resultado do exame de sangue realizado em 15/10/2025...
DEBUG - OCR tradicional página 2/3 (0 chars): nenhum texto encontrado
DEBUG - OCR tradicional página 3/3 (156 chars): Assinatura do médico responsável Dr. João Silva CRM 12345...
INFO - OCR tradicional concluído para exame_escaneado.pdf: 243 caracteres extraídos
```

### 4. **PDFs Escaneados (OCR Multimodal - GPT-4 Vision):**
```
INFO - PDF sem texto embutido detectado, tentando OCR: receita_complexa.pdf
DEBUG - Iniciando OCR multimodal em PDF com 2 páginas: receita_complexa.pdf
DEBUG - OCR multimodal página 1/2 (312 chars): PRESCRIÇÃO MÉDICA
Dr. João Silva - CRM 12345
Paciente: Maria Santos
Medicamento: Losartana 50mg
Posologia: 1 comprimido ao dia...
DEBUG - OCR multimodal página 2/2 (89 chars): Validade: 30 dias
Assinatura digital verificada
INFO - OCR multimodal concluído para receita_complexa.pdf: 401 caracteres extraídos
```

### 5. **Imagens com OCR:**
```
DEBUG - OCR imagem receita.jpg (89 chars): Prescrição médica para paciente Maria Silva...
```

### 5. **Casos sem Texto:**
```
DEBUG - OCR tradicional página 2/3: nenhum texto encontrado
DEBUG - OCR multimodal página 1/1: nenhum texto encontrado
DEBUG - OCR imagem foto_borrosa.png: nenhum texto encontrado
```

## 🔍 Exemplo Completo

Suponha um PDF escaneado de um exame. No modo debug você verá:

```bash
INFO - Processando exame_hemograma.pdf
DEBUG - PyPDF2 extraiu 0 caracteres de exame_hemograma.pdf
INFO - PDF sem texto embutido detectado, tentando OCR: exame_hemograma.pdf
DEBUG - Iniciando OCR multimodal em PDF com 2 páginas: exame_hemograma.pdf
DEBUG - OCR multimodal página 1/2 (312 chars): LABORATÓRIO CLÍNICO XYZ
Exame: Hemograma Completo
Paciente: João Silva
Data: 15/10/2025
Resultado:
- Hemácias: 4.5 milhões/mm³
- Leucócitos: 7.200/mm³...
DEBUG - OCR multimodal página 2/2 (89 chars): Dr. Maria Santos
CRM: 98765
Responsável Técnico
INFO - OCR multimodal concluído para exame_hemograma.pdf: 401 caracteres extraídos
```

## ⚙️ Configuração

### Variável de Ambiente:
```bash
export CLINIKONDO_LOG_LEVEL=debug
export CLINIKONDO_OCR_STRATEGY=multimodal  # ou hybrid, traditional
```

### Arquivo de Configuração (.env):
```
CLINIKONDO_LOG_LEVEL=debug
CLINIKONDO_OCR_STRATEGY=hybrid
```

## 🎯 Casos de Uso

- **Verificar qualidade do OCR** em documentos escaneados
- **Debugar problemas** de extração de texto
- **Validar conteúdo** antes do processamento LLM
- **Identificar páginas problemáticas** em PDFs
- **Comparar estratégias** de OCR (traditional vs multimodal)
- **Ajustar configurações** do Tesseract ou modelo LLM se necessário

## 🔍 Comparação de Estratégias

| Aspecto | Traditional | Multimodal | Hybrid |
|---------|------------|-----------|--------|
| **Velocidade** | ⚡⚡⚡ Rápida | 🐌 Lenta | ⚡⚡ Média |
| **Precisão** | ⭐⭐⭐ Boa | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Muito boa |
| **Custo** | 💰 Grátis | 💰💰💰 API paga | 💰💰 API + grátis |
| **Documentos Simples** | ✅ Ideal | ⚠️ Overkill | ✅ Boa |
| **Documentos Complexos** | ⚠️ Limitado | ✅ Excelente | ✅ Muito bom |
| **Requisitos** | Tesseract | API OpenAI | Ambos |

## 📊 Níveis de Log Disponíveis

| Nível | Conteúdo |
|-------|----------|
| `error` | Apenas erros críticos |
| `warning` | Erros + avisos |
| `info` | Erros + avisos + informações gerais |
| `debug` | **Tudo** + detalhes do OCR e extração |