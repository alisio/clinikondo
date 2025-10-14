"""Carregamento e validação da configuração do Medifolder."""

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
    executar_copia_apos_erro: bool = False
    log_nivel: str = "info"
    dry_run: bool = False
    estrategia_extracao: str = "auto"

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

    @property
    def state_dir(self) -> Path:
        return self.output_dir / ".medifolder"

    @property
    def patients_storage_path(self) -> Path:
        return self.state_dir / "patients.json"

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

    input_dir = Path(args.input or env.get("MEDIFOLDER_INPUT_DIR", ".")).expanduser()
    output_dir = Path(args.output or env.get("MEDIFOLDER_OUTPUT_DIR", "./output")).expanduser()

    modelo_llm = args.model or env.get("MEDIFOLDER_MODEL", DEFAULT_MODEL)
    openai_api_key = args.api_key or env.get("OPENAI_API_KEY")
    openai_api_base = args.api_base or env.get("OPENAI_API_BASE")
    llm_temperature = (
        args.temperature
        if args.temperature is not None
        else float(env.get("MEDIFOLDER_TEMPERATURE", 0.2))
    )
    llm_max_tokens = (
        args.max_tokens
        if args.max_tokens is not None
        else int(env.get("MEDIFOLDER_MAX_TOKENS", 512))
    )
    prompt_template = args.prompt_template or env.get("MEDIFOLDER_PROMPT_TEMPLATE")
    prompt_template_path = Path(prompt_template).expanduser() if prompt_template else None
    match_nome_paciente_auto = (
        args.match_patient
        if args.match_patient is not None
        else _bool_from_env(env.get("MEDIFOLDER_MATCH_PATIENT"), True)
    )
    criar_paciente_sem_match = (
        args.create_patient
        if args.create_patient is not None
        else _bool_from_env(env.get("MEDIFOLDER_CREATE_PATIENT"), True)
    )
    mover_para_compartilhado_sem_match = (
        args.move_to_shared
        if args.move_to_shared is not None
        else _bool_from_env(env.get("MEDIFOLDER_MOVE_TO_SHARED"), False)
    )
    executar_copia_apos_erro = (
        args.copy_on_error
        if args.copy_on_error is not None
        else _bool_from_env(env.get("MEDIFOLDER_COPY_ON_ERROR"), False)
    )
    log_nivel = args.log_level or env.get("MEDIFOLDER_LOG_LEVEL", "info")
    dry_run = args.dry_run or _bool_from_env(env.get("MEDIFOLDER_DRY_RUN"), False)
    estrategia_extracao = args.strategy or env.get("MEDIFOLDER_STRATEGY", "auto")

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
        executar_copia_apos_erro=executar_copia_apos_erro,
        log_nivel=log_nivel,
        dry_run=dry_run,
        estrategia_extracao=estrategia_extracao,
    )
    config.validar()
    return config

