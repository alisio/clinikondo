"""Integração com serviços LLM e heurísticas locais."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict

from .config import Config
from .models import Document, LLMExtractionResult
from .patients import PatientRegistry
from .types import DocumentTypeCatalog

LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT = """
Você é um assistente de IA especializado em interpretar documentos médicos digitalizados 
(laudos, exames, receitas, formulários, etc.). 
Seu papel é analisar o texto fornecido e identificar as informações principais 
de forma estruturada e padronizada.

Analise cuidadosamente o conteúdo textual do documento (mesmo que contenha ruídos de OCR, 
formatações quebradas ou textos mistos) e retorne um objeto JSON com os seguintes campos:

{{
  "nome_paciente": "<texto>",
  "data_documento": "<AAAA-MM-DD>",
  "tipo_documento": "<categoria válida>",
  "especialidade": "<especialidade válida>",
  "descricao_curta": "<resumo breve, até 60 caracteres>"
}}

**CATEGORIAS VÁLIDAS para `tipo_documento`:**
- exame → para resultados de análises clínicas, laboratoriais, de imagem ou ultrassom
- receita → para prescrições médicas e medicamentos
- vacina → para registros de vacinação e imunização
- controle → para medições ou acompanhamento (pressão, glicemia etc.)
- contato → para dados de médicos, clínicas, endereços, telefones
- laudo → para relatórios médicos, pareceres, atestados
- agenda → para agendamentos ou confirmações de consulta
- documento → para formulários, carteirinhas, solicitações ou arquivos administrativos

**ESPECIALIDADES VÁLIDAS:**
- radiologia
- laboratorial
- cardiologia
- endocrinologia
- ginecologia
- clinica_geral
- dermatologia
- pediatria

**Instruções adicionais:**
- Sempre tente preencher todos os campos, mesmo que inferindo com base no conteúdo.
- Use **letras minúsculas e sem acento** nos valores categóricos (`tipo_documento`, `especialidade`).
- O campo `descricao_curta` deve conter até **60 caracteres e no máximo 4 termos**, descrevendo o tipo do documento (ex: "hemograma completo", "ultrassom abdominal", "receita antibiótico", "laudo oftalmológico").
- Se houver múltiplas datas, priorize a data de **emissão, coleta ou atendimento médico**.
- Caso o nome do paciente não esteja claramente legível, utilize a melhor inferência possível baseada em padrões típicos (ex: linhas que iniciam com "Paciente:", "Cliente:", "Nome:", etc.).

Agora processe o conteúdo a seguir:

Documento:
\"\"\"
{texto}
\"\"\"
""".strip()


class BaseExtractor(ABC):
    """Interface base para extratores de metadados."""

    @abstractmethod
    def extract(
        self,
        document: Document,
        *,
        patient_registry: PatientRegistry,
        type_catalog: DocumentTypeCatalog,
    ) -> LLMExtractionResult:
        raise NotImplementedError


class OpenAILLMExtractor(BaseExtractor):
    """Extrator que utiliza a API da OpenAI."""

    def __init__(self, config: Config, prompt_template: str | None = None) -> None:
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY não configurada.")
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - depende de pip
            raise RuntimeError("Pacote 'openai' não está instalado.") from exc
        self._client = OpenAI(api_key=config.openai_api_key, base_url=config.openai_api_base)
        self._model = config.modelo_llm
        self._temperature = config.llm_temperature
        self._max_tokens = config.llm_max_tokens
        self._prompt_template = prompt_template or DEFAULT_PROMPT

    def extract(
        self,
        document: Document,
        *,
        patient_registry: PatientRegistry,
        type_catalog: DocumentTypeCatalog,
    ) -> LLMExtractionResult:
        prompt = self._prompt_template.format(texto=document.texto_extraido)
        start = time.perf_counter()
        raw_response = self._call_openai(prompt)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        
        # Logging estruturado conforme SRS
        log_estruturado = {
            "metodo_extracao": "llm",
            "modelo_utilizado": self._model,
            "tempo_resposta_ms": elapsed_ms,
            "sucesso": False,
            "mensagem_erro": None,
            "prompt_utilizado": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "resposta_bruta_llm": raw_response[:200] + "..." if len(raw_response) > 200 else raw_response,
        }
        
        LOGGER.debug("LLM respondeu em %sms", elapsed_ms)
        
        try:
            # Debug
            print(f"DEBUG: Resposta do LLM: '{raw_response}'")
            
            if not raw_response.strip():
                raise RuntimeError("LLM retornou resposta vazia")
            
            # Remove markdown se presente
            content = raw_response.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ``` genérico
            if content.endswith('```'):
                content = content[:-3]  # Remove ``` final
            
            content = content.strip()
            print(f"DEBUG: Conteúdo limpo: '{content}'")

            parsed = json.loads(content)
            log_estruturado["sucesso"] = True
            log_estruturado["dados_extraidos"] = parsed
        except json.JSONDecodeError as exc:
            log_estruturado["mensagem_erro"] = f"JSON inválido: {exc}"
            LOGGER.error("Extração LLM falhou: %s", log_estruturado)
            raise RuntimeError(f"Resposta do LLM não é JSON válido: {exc}") from exc
        
        # Log final estruturado conforme SRS
        LOGGER.info("Extração LLM concluída: %s", log_estruturado)
        return self._build_result(parsed)

    def _call_openai(self, prompt: str) -> str:
        """Chama API OpenAI com sistema de retry conforme SRS."""
        print(f"DEBUG: Usando endpoint {self._client.base_url}")
        print("DEBUG: Fazendo chamada para chat.completions.create")
        
        max_tentativas = 3  # Conforme SRS: "Até 3 tentativas"
        for tentativa in range(1, max_tentativas + 1):
            try:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                    timeout=30,  # Conforme SRS: "Padrão 30 segundos"
                    messages=[
                        {"role": "system", "content": "Você extrai metadados estruturados de documentos médicos."},
                        {"role": "user", "content": prompt},
                    ],
                )
                response_content = completion.choices[0].message.content
                print(f"DEBUG: Sucesso na tentativa {tentativa}")
                return response_content
            except Exception as e:
                print(f"DEBUG: Erro na tentativa {tentativa}/{max_tentativas}: {e}")
                if tentativa == max_tentativas:
                    raise RuntimeError(f"Falha após {max_tentativas} tentativas: {e}") from e
                # Aguarda antes de tentar novamente
                import time
                time.sleep(1 * tentativa)  # Backoff progressivo

    def _build_result(self, data: Dict[str, Any]) -> LLMExtractionResult:
        try:
            # Tratar casos onde data_documento pode ser None ou inválida
            data_doc = data.get("data_documento")
            if data_doc and isinstance(data_doc, str) and data_doc.strip():
                try:
                    data_documento = date.fromisoformat(data_doc)
                except ValueError:
                    # Se não conseguir fazer parse, usar data atual
                    data_documento = date.today()
            else:
                data_documento = date.today()
            
            # Calcular confiança conforme SRS (0.0-1.0)
            confianca = self._calcular_confianca_extracao(data)
            
            result = LLMExtractionResult(
                nome_paciente=data.get("nome_paciente", "").strip() or None,
                data_documento=data_documento,
                tipo_documento=data.get("tipo_documento", "").strip() or None,
                especialidade=data.get("especialidade", "").strip() or None,
                descricao_curta=data.get("descricao_curta", "").strip() or None,
            )
            
            # Adicionar confiança aos extras (SRS requer campo confianca_extracao)
            if not hasattr(result, 'extras') or result.extras is None:
                result.extras = {}
            result.extras['confianca_extracao'] = confianca
            
            return result
        except Exception as e:
            print(f"DEBUG: Erro ao processar resultado: {e}")
            print(f"DEBUG: Dados recebidos: {data}")
            # Retorna resultado com dados mínimos em caso de erro
            result = LLMExtractionResult(
                nome_paciente=None,
                data_documento=date.today(),
                tipo_documento=None,
                especialidade=None,
                descricao_curta=None,
            )
            result.extras = {'confianca_extracao': 0.0}
            return result
    
    def _calcular_confianca_extracao(self, data: Dict[str, Any]) -> float:
        """Calcula nível de confiança da extração conforme SRS (0.0-1.0)."""
        confianca = 1.0
        
        # Penalizar campos obrigatórios ausentes (SRS: campos obrigatórios)
        campos_obrigatorios = ['nome_paciente', 'data_documento', 'tipo_documento']
        for campo in campos_obrigatorios:
            valor = data.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                confianca -= 0.3  # Penalidade por campo obrigatório ausente
        
        # Bonificar campos opcionais preenchidos
        campos_opcionais = ['especialidade', 'descricao_curta']
        for campo in campos_opcionais:
            valor = data.get(campo)
            if valor and isinstance(valor, str) and valor.strip():
                confianca += 0.1  # Bônus por campo opcional preenchido
        
        # Garantir que confiança fica entre 0.0 e 1.0
        return max(0.0, min(1.0, confianca))


def build_extractor(config: Config, prompt_text: str | None) -> BaseExtractor:
    """Cria o extrator LLM - aplicação utiliza exclusivamente LLM."""
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY é obrigatória. Sistema requer LLM para funcionamento.")
    
    try:
        return OpenAILLMExtractor(config, prompt_text)
    except Exception as exc:
        raise RuntimeError(f"Falha ao inicializar extrator LLM: {exc}. Sistema requer LLM para funcionamento.") from exc

