"""Registro de pacientes conhecidos pelo sistema."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, Optional

from .models import Patient
from .utils import sanitize_token, slugify, strip_accents

LOGGER = logging.getLogger(__name__)


def _normalize_name(value: str) -> str:
    return sanitize_token(value, separator=" ", allow_digits=False)


class PatientRegistry:
    """Gerencia o cadastro e reconciliação de nomes de pacientes."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path
        self._patients: Dict[str, Patient] = {}
        if storage_path:
            self._load()

    def _load(self) -> None:
        if not self._storage_path or not self._storage_path.exists():
            return
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            LOGGER.warning("Não foi possível carregar pacientes: %s", exc)
            return
        for entry in raw:
            patient = Patient(
                nome_completo=entry["nome_completo"],
                slug_diretorio=entry["slug_diretorio"],
                nomes_alternativos=entry.get("nomes_alternativos", []),
                genero=entry.get("genero"),
            )
            self._patients[patient.slug_diretorio] = patient

    def save(self) -> None:
        if not self._storage_path:
            return
        data = [
            {
                "nome_completo": patient.nome_completo,
                "slug_diretorio": patient.slug_diretorio,
                "nomes_alternativos": patient.nomes_alternativos,
                "genero": patient.genero,
            }
            for patient in self._patients.values()
        ]
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self) -> Iterable[Patient]:
        return list(self._patients.values())

    def get_by_slug(self, slug: str) -> Optional[Patient]:
        return self._patients.get(slug)

    def match(self, name: str) -> Optional[Patient]:
        """Tenta encontrar um paciente existente pelo nome informado."""
        normalized = _normalize_name(name)
        for patient in self._patients.values():
            candidates = [_normalize_name(patient.nome_completo), *(_normalize_name(alias) for alias in patient.nomes_alternativos)]
            if normalized in candidates:
                return patient
        return None

    def match_in_text(self, text: str) -> Optional[Patient]:
        """Tenta identificar um paciente baseado no texto extraído."""
        normalized_text = _normalize_name(strip_accents(text))
        for patient in self._patients.values():
            for name in patient.nomes_normalizados():
                cleaned = _normalize_name(name)
                if cleaned and cleaned in normalized_text:
                    return patient
        return None

    def ensure_patient(self, name: str, *, create_if_missing: bool = True) -> Patient | None:
        patient = self.match(name)
        if patient:
            return patient
        if not create_if_missing:
            return None
        slug = slugify(name)
        index = 1
        unique_slug = slug
        while unique_slug in self._patients:
            index += 1
            unique_slug = f"{slug}-{index}"
        patient = Patient(nome_completo=name, slug_diretorio=unique_slug, nomes_alternativos=[])
        self._patients[unique_slug] = patient
        return patient

    def upsert(self, patient: Patient) -> None:
        self._patients[patient.slug_diretorio] = patient
