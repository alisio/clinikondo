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
from .utils import first_date_from_text, sanitize_token, short_description

LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT = """
Você é um assistente que extrai informações de documentos médicos digitalizados.
Analise o conteúdo abaixo e retorne um JSON com os campos:
- nome_paciente (texto)
- data_documento (AAAA-MM-DD)
- tipo_documento (uma palavra)
- especialidade (uma palavra ou frase curta)
- descricao_curta (até 60 caracteres, no máximo 4 termos)

Se não houver informação suficiente, faça a melhor inferência possível.

Documento:
{texto}
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


class RuleBasedExtractor(BaseExtractor):
    """Extrator baseado em heurísticas simples, usado como fallback."""

    def extract(
        self,
        document: Document,
        *,
        patient_registry: PatientRegistry,
        type_catalog: DocumentTypeCatalog,
    ) -> LLMExtractionResult:
        texto = document.texto_extraido or document.nome_arquivo_original
        patient = patient_registry.match_in_text(texto)
        if patient:
            nome_paciente = patient.nome_completo
        else:
            nome_paciente = self._infer_patient_from_text(texto)
        data_documento = first_date_from_text(texto) or date.today()
        doc_type = type_catalog.infer_from_text(texto)
        especialidade = self._infer_especialidade(texto, doc_type)
        descricao = short_description(texto)
        classificar_como_compartilhado = nome_paciente.lower() == "compartilhado"
        extras: Dict[str, str] = {}
        if patient:
            extras["paciente_match"] = patient.slug_diretorio
        return LLMExtractionResult(
            nome_paciente=nome_paciente,
            data_documento=data_documento,
            tipo_documento=doc_type.nome_tipo,
            especialidade=especialidade,
            descricao_curta=descricao,
            classificar_como_compartilhado=classificar_como_compartilhado,
            extras=extras,
        )

    @staticmethod
    def _infer_patient_from_text(texto: str) -> str:
        lowered = texto.lower()
        markers = ["paciente:", "nome:", "sr.", "sra."]
        for marker in markers:
            if marker in lowered:
                start = lowered.index(marker) + len(marker)
                snippet = texto[start:].split("\n", 1)[0]
                return snippet.strip().split(",")[0].split(";")[0][:60] or "Compartilhado"
        return "Compartilhado"

    @staticmethod
    def _infer_especialidade(texto: str, doc_type) -> str:
        sanitized = sanitize_token(texto, separator=" ")
        for especialidade in doc_type.especialidades_rel:
            if sanitize_token(especialidade, separator=" ") in sanitized:
                return especialidade
        # heurística adicional
        hints = {
            "cardiologia": ["cardio", "pressao", "taquicardia"],
            "endocrinologia": ["glicose", "insulina", "hormonal"],
            "clinica_geral": ["clinica geral", "consulta"],
            "dermatologia": ["dermato", "pele"],
            "pediatria": ["crianca", "pediatra"],
        }
        for nome, palavras in hints.items():
            for palavra in palavras:
                if palavra in sanitized:
                    return nome
        return doc_type.especialidades_rel[0] if doc_type.especialidades_rel else "clinica_geral"


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
        LOGGER.debug("LLM respondeu em %sms", elapsed_ms)
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Resposta do LLM não é JSON válido: {exc}") from exc
        return self._build_result(parsed)

    def _call_openai(self, prompt: str) -> str:
        # compatível com SDKs >=1.0
        if hasattr(self._client, "responses"):
            response = self._client.responses.create(
                model=self._model,
                temperature=self._temperature,
                max_output_tokens=self._max_tokens,
                input=prompt,
            )
            return response.output_text  # type: ignore[attr-defined]
        # fallback para SDKs antigos
        completion = self._client.chat.completions.create(  # type: ignore[attr-defined]
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": "Você extrai metadados estruturados de documentos médicos."},
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content  # type: ignore[index]

    def _build_result(self, data: Dict[str, Any]) -> LLMExtractionResult:
        try:
            nome_paciente = data["nome_paciente"]
            data_documento = date.fromisoformat(data["data_documento"])
            tipo_documento = data["tipo_documento"]
        except (KeyError, ValueError) as exc:
            raise RuntimeError(f"Campos faltando na resposta do LLM: {exc}") from exc
        especialidade = data.get("especialidade")
        descricao_curta = data.get("descricao_curta")
        classificar_como_compartilhado = data.get("classificar_como_compartilhado", False)
        extras = {
            key: str(value)
            for key, value in data.items()
            if key
            not in {"nome_paciente", "data_documento", "tipo_documento", "especialidade", "descricao_curta", "classificar_como_compartilhado"}
        }
        return LLMExtractionResult(
            nome_paciente=nome_paciente,
            data_documento=data_documento,
            tipo_documento=tipo_documento,
            especialidade=especialidade,
            descricao_curta=descricao_curta,
            classificar_como_compartilhado=bool(classificar_como_compartilhado),
            extras=extras,
        )


def build_extractor(config: Config, prompt_text: str | None) -> BaseExtractor:
    """Cria o extrator conforme a estratégia configurada."""
    strategy = config.estrategia_extracao.lower()
    if strategy == "heuristico":
        return RuleBasedExtractor()
    if strategy == "llm":
        return OpenAILLMExtractor(config, prompt_text)
    if strategy == "auto":
        if config.openai_api_key:
            try:
                return OpenAILLMExtractor(config, prompt_text)
            except Exception as exc:  # pragma: no cover - depende de ambiente
                LOGGER.warning("Falha ao iniciar extrator LLM, usando heurístico: %s", exc)
        return RuleBasedExtractor()
    raise ValueError(f"Estratégia desconhecida: {config.estrategia_extracao}")

