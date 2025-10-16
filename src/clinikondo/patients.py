"""Registro de pacientes conhecidos pelo sistema."""

from __future__ import annotations

import difflib
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

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
        
        # Primeiro, tentar match exato
        for patient in self._patients.values():
            candidates = [_normalize_name(patient.nome_completo), *(_normalize_name(alias) for alias in patient.nomes_alternativos)]
            if normalized in candidates:
                return patient
        
        # Se não encontrou match exato, tentar fuzzy match com threshold alto
        fuzzy_matches = self.fuzzy_match(name, threshold=0.9)
        if fuzzy_matches:
            best_match = fuzzy_matches[0]
            LOGGER.info(f"Fuzzy match encontrado: '{name}' -> '{best_match[0].nome_completo}' (similaridade: {best_match[1]:.2f})")
            return best_match[0]
        
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

    def fuzzy_match(self, name: str, threshold: float = 0.8) -> List[Tuple[Patient, float]]:
        """Encontra pacientes similares usando fuzzy matching."""
        normalized_input = _normalize_name(name).lower()
        matches = []
        
        for patient in self._patients.values():
            # Comparar com nome principal
            patient_name = _normalize_name(patient.nome_completo).lower()
            similarity = difflib.SequenceMatcher(None, normalized_input, patient_name).ratio()
            
            if similarity >= threshold:
                matches.append((patient, similarity))
            
            # Comparar com aliases
            for alias in patient.nomes_alternativos:
                alias_normalized = _normalize_name(alias).lower()
                alias_similarity = difflib.SequenceMatcher(None, normalized_input, alias_normalized).ratio()
                
                if alias_similarity >= threshold:
                    # Usar maior similaridade se já existe match
                    existing_match = next((m for m in matches if m[0] == patient), None)
                    if existing_match:
                        max_similarity = max(existing_match[1], alias_similarity)
                        matches.remove(existing_match)
                        matches.append((patient, max_similarity))
                    else:
                        matches.append((patient, alias_similarity))
        
        # Ordenar por similaridade (maior primeiro)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def find_similar_patients(self, name: str, threshold: float = 0.7) -> List[Tuple[Patient, float]]:
        """Encontra pacientes similares para detecção de duplicatas."""
        return self.fuzzy_match(name, threshold)

    def add_alias(self, patient_slug: str, alias: str) -> bool:
        """Adiciona um alias a um paciente existente."""
        patient = self._patients.get(patient_slug)
        if not patient:
            return False
        
        # Verificar se alias já existe
        if alias in patient.nomes_alternativos:
            return True
        
        # Verificar se alias conflita com outro paciente
        existing_match = self.match(alias)
        if existing_match and existing_match.slug_diretorio != patient_slug:
            LOGGER.warning(f"Alias '{alias}' já está sendo usado pelo paciente {existing_match.nome_completo}")
            return False
        
        patient.nomes_alternativos.append(alias)
        return True

    def merge_patients(self, source_slug: str, target_slug: str) -> bool:
        """Merge dois pacientes, movendo aliases do source para o target."""
        source = self._patients.get(source_slug)
        target = self._patients.get(target_slug)
        
        if not source or not target:
            return False
        
        # Mover aliases do source para target
        for alias in source.nomes_alternativos:
            if alias not in target.nomes_alternativos:
                target.nomes_alternativos.append(alias)
        
        # Adicionar nome completo do source como alias do target
        if source.nome_completo not in target.nomes_alternativos:
            target.nomes_alternativos.append(source.nome_completo)
        
        # Remover paciente source
        del self._patients[source_slug]
        
        LOGGER.info(f"Pacientes mesclados: {source.nome_completo} -> {target.nome_completo}")
        return True

    def detect_possible_duplicates(self, threshold: float = 0.85) -> List[Tuple[Patient, Patient, float]]:
        """Detecta possíveis pacientes duplicados."""
        duplicates = []
        patients_list = list(self._patients.values())
        
        for i, patient1 in enumerate(patients_list):
            for patient2 in patients_list[i+1:]:
                # Comparar nomes principais
                name1 = _normalize_name(patient1.nome_completo).lower()
                name2 = _normalize_name(patient2.nome_completo).lower()
                
                similarity = difflib.SequenceMatcher(None, name1, name2).ratio()
                
                if similarity >= threshold:
                    duplicates.append((patient1, patient2, similarity))
        
        # Ordenar por similaridade (maior primeiro)
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def update_patient(self, slug: str, nome_completo: str = None, genero: str = None, aliases: List[str] = None) -> bool:
        """Atualiza informações de um paciente."""
        patient = self._patients.get(slug)
        if not patient:
            return False
        
        if nome_completo:
            patient.nome_completo = nome_completo
        
        if genero:
            patient.genero = genero
        
        if aliases is not None:
            patient.nomes_alternativos = aliases
        
        return True

    def remove_patient(self, slug: str) -> bool:
        """Remove um paciente do registro."""
        if slug in self._patients:
            patient = self._patients[slug]
            del self._patients[slug]
            LOGGER.info(f"Paciente removido: {patient.nome_completo}")
            return True
        return False
