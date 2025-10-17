"""Pacote principal do CliniKondo."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .config import Config, load_config_from_args
from .llm import build_extractor
from .models import Document
from .patients import PatientRegistry
from .processing import DocumentProcessor
from .types import DocumentTypeCatalog

__all__ = [
    "Config",
    "Document",
    "DocumentProcessor",
    "PatientRegistry",
    "DocumentTypeCatalog",
    "build_extractor",
    "load_config_from_args",
    "run_pipeline",
]


def run_pipeline(config: Config) -> List[Document]:
    """Executa o pipeline completo a partir de uma configuração válida."""
    prompt_text = None
    if config.prompt_template_path:
        prompt_text = config.prompt_text()
    state_dir = config.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    registry_path = config.patients_storage_path
    patient_registry = PatientRegistry(registry_path)
    type_catalog = DocumentTypeCatalog()
    extractor = build_extractor(config, prompt_text)
    processor = DocumentProcessor(
        config=config,
        extractor=extractor,
        patient_registry=patient_registry,
        type_catalog=type_catalog,
    )
    return processor.process_all()

