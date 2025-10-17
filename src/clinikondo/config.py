"""Carregamento e validação da configuração do CliniKondo."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "gpt-4"
DEFAULT_PROMPT_FILENAME = "prompt_base.txt"


def _bool_from_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim"}


@dataclass(slots=True)
class Config:
    """Configuração carregada via CLI e variáveis de ambiente."""

    input_dir: Path
    output_dir: Path
    modelo_llm: str = DEFAULT_MODEL
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    llm_temperature: float = 0.2
    llm_max_tokens: int = 512
    prompt_template_path: Path | None = None
    match_nome_paciente_auto: bool = True
    criar_paciente_sem_match: bool = True
    mover_para_compartilhado_sem_match: bool = False
    mover_arquivo_original: bool = False
    executar_copia_apos_erro: bool = False
    log_nivel: str = "info"
    dry_run: bool = False
    ocr_strategy: str = "hybrid"  # hybrid, multimodal, traditional
    # Multi-model configuration (SRS v2.0)
    ocr_model: str | None = None  # Se None, usa modelo_llm
    ocr_api_key: str | None = None  # Se None, usa openai_api_key
    ocr_api_base: str | None = None  # Se None, usa openai_api_base
    classification_model: str | None = None  # Se None, usa modelo_llm
    classification_api_key: str | None = None  # Se None, usa openai_api_key
    classification_api_base: str | None = None  # Se None, usa openai_api_base

    def validar(self) -> None:
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Diretório de entrada não existe: {self.input_dir}")
        if not self.input_dir.is_dir():
            raise NotADirectoryError(f"Diretório de entrada inválido: {self.input_dir}")
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.output_dir.is_dir():
            raise NotADirectoryError(f"Diretório de saída inválido: {self.output_dir}")
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("Temperatura deve estar entre 0 e 2.")
        if self.llm_max_tokens <= 0:
            raise ValueError("llm_max_tokens deve ser positivo.")
        # Validação obrigatória: sistema requer LLM
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY é obrigatória. Sistema utiliza exclusivamente LLM para processamento.")
        # Validar estratégia OCR
        if self.ocr_strategy not in {"hybrid", "multimodal", "traditional"}:
            raise ValueError(f"ocr_strategy inválida: {self.ocr_strategy}. Use: hybrid, multimodal ou traditional")

    @property
    def state_dir(self) -> Path:
        return self.output_dir / ".clinikondo"

    @property
    def patients_storage_path(self) -> Path:
        return self.state_dir / "patients.json"
    
    # Propriedades com fallback para multi-model (SRS v2.0)
    @property
    def effective_ocr_model(self) -> str:
        """Modelo efetivo para OCR (fallback para modelo_llm)."""
        return self.ocr_model or self.modelo_llm
    
    @property
    def effective_ocr_api_key(self) -> str | None:
        """API key efetiva para OCR (fallback para openai_api_key)."""
        return self.ocr_api_key or self.openai_api_key
    
    @property
    def effective_ocr_api_base(self) -> str | None:
        """API base efetiva para OCR (fallback para openai_api_base)."""
        return self.ocr_api_base or self.openai_api_base
    
    @property
    def effective_classification_model(self) -> str:
        """Modelo efetivo para classificação (fallback para modelo_llm)."""
        return self.classification_model or self.modelo_llm
    
    @property
    def effective_classification_api_key(self) -> str | None:
        """API key efetiva para classificação (fallback para openai_api_key)."""
        return self.classification_api_key or self.openai_api_key
    
    @property
    def effective_classification_api_base(self) -> str | None:
        """API base efetiva para classificação (fallback para openai_api_base)."""
        return self.classification_api_base or self.openai_api_base

    def prompt_text(self) -> str | None:
        if not self.prompt_template_path:
            return None
        if not self.prompt_template_path.exists():
            raise FileNotFoundError(
                f"Template de prompt não encontrado: {self.prompt_template_path}"
            )
        return self.prompt_template_path.read_text(encoding="utf-8")


def load_config_from_args(args: argparse.Namespace) -> Config:
    """Carrega a configuração mesclando argumentos e variáveis de ambiente."""
    env = os.environ

    input_dir = Path(args.input or env.get("CLINIKONDO_INPUT_DIR", ".")).expanduser()
    output_dir = Path(args.output or env.get("CLINIKONDO_OUTPUT_DIR", "./output")).expanduser()

    modelo_llm = args.model or env.get("CLINIKONDO_MODEL", DEFAULT_MODEL)
    openai_api_key = args.api_key or env.get("OPENAI_API_KEY")
    openai_api_base = args.api_base or env.get("OPENAI_API_BASE")
    llm_temperature = (
        args.temperature
        if args.temperature is not None
        else float(env.get("CLINIKONDO_TEMPERATURE", 0.2))
    )
    llm_max_tokens = (
        args.max_tokens
        if args.max_tokens is not None
        else int(env.get("CLINIKONDO_MAX_TOKENS", 512))
    )
    prompt_template = args.prompt_template or env.get("CLINIKONDO_PROMPT_TEMPLATE")
    prompt_template_path = Path(prompt_template).expanduser() if prompt_template else None
    match_nome_paciente_auto = (
        args.match_patient
        if args.match_patient is not None
        else _bool_from_env(env.get("CLINIKONDO_MATCH_PATIENT"), True)
    )
    criar_paciente_sem_match = (
        args.create_patient
        if args.create_patient is not None
        else _bool_from_env(env.get("CLINIKONDO_CREATE_PATIENT"), True)
    )
    mover_para_compartilhado_sem_match = (
        args.move_to_shared
        if args.move_to_shared is not None
        else _bool_from_env(env.get("CLINIKONDO_MOVE_TO_SHARED"), False)
    )
    executar_copia_apos_erro = (
        args.copy_on_error
        if args.copy_on_error is not None
        else _bool_from_env(env.get("CLINIKONDO_COPY_ON_ERROR"), False)
    )
    mover_arquivo_original = (
        args.mover
        if hasattr(args, 'mover') and args.mover
        else _bool_from_env(env.get("CLINIKONDO_MOVER_ARQUIVO"), False)
    )
    log_nivel = args.log_level or env.get("CLINIKONDO_LOG_LEVEL", "info")
    dry_run = args.dry_run or _bool_from_env(env.get("CLINIKONDO_DRY_RUN"), False)
    ocr_strategy = (
        args.ocr_strategy
        if hasattr(args, 'ocr_strategy') and args.ocr_strategy
        else env.get("CLINIKONDO_OCR_STRATEGY", "hybrid")
    )
    
    # Multi-model configuration (SRS v2.0)
    ocr_model = (
        args.ocr_model
        if hasattr(args, 'ocr_model') and args.ocr_model
        else env.get("CLINIKONDO_OCR_MODEL")
    )
    ocr_api_key = (
        args.ocr_api_key
        if hasattr(args, 'ocr_api_key') and args.ocr_api_key
        else env.get("CLINIKONDO_OCR_API_KEY")
    )
    ocr_api_base = (
        args.ocr_api_base
        if hasattr(args, 'ocr_api_base') and args.ocr_api_base
        else env.get("CLINIKONDO_OCR_API_BASE")
    )
    classification_model = (
        args.classification_model
        if hasattr(args, 'classification_model') and args.classification_model
        else env.get("CLINIKONDO_CLASSIFICATION_MODEL")
    )
    classification_api_key = (
        args.classification_api_key
        if hasattr(args, 'classification_api_key') and args.classification_api_key
        else env.get("CLINIKONDO_CLASSIFICATION_API_KEY")
    )
    classification_api_base = (
        args.classification_api_base
        if hasattr(args, 'classification_api_base') and args.classification_api_base
        else env.get("CLINIKONDO_CLASSIFICATION_API_BASE")
    )

    config = Config(
        input_dir=input_dir,
        output_dir=output_dir,
        modelo_llm=modelo_llm,
        openai_api_key=openai_api_key,
        openai_api_base=openai_api_base,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        prompt_template_path=prompt_template_path,
        match_nome_paciente_auto=match_nome_paciente_auto,
        criar_paciente_sem_match=criar_paciente_sem_match,
        mover_para_compartilhado_sem_match=mover_para_compartilhado_sem_match,
        mover_arquivo_original=mover_arquivo_original,
        executar_copia_apos_erro=executar_copia_apos_erro,
        log_nivel=log_nivel,
        dry_run=dry_run,
        ocr_strategy=ocr_strategy,
        ocr_model=ocr_model,
        ocr_api_key=ocr_api_key,
        ocr_api_base=ocr_api_base,
        classification_model=classification_model,
        classification_api_key=classification_api_key,
        classification_api_base=classification_api_base,
    )
    config.validar()
    return config

