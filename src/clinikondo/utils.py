"""Funções utilitárias usadas pelo pipeline do CliniKondo."""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger(__name__)

_DATE_PATTERNS = (
    re.compile(r"(?P<year>20\d{2})[-/](?P<month>0[1-9]|1[0-2])[-/](?P<day>0[1-9]|[12]\d|3[01])"),
    re.compile(
        r"(?P<day>0[1-9]|[12]\d|3[01])[-/](?P<month>0[1-9]|1[0-2])[-/](?P<year>20\d{2})"
    ),
)

_WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)


def strip_accents(value: str) -> str:
    """Remove acentos preservando apenas caracteres ASCII."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def sanitize_token(value: str, *, separator: str = "-", allow_digits: bool = True) -> str:
    """Normaliza um token para ser usado em nomes seguros de arquivo ou diretório."""
    ascii_value = strip_accents(value).lower()
    safe_chars: list[str] = []
    for ch in ascii_value:
        if ch.isalpha() or (allow_digits and ch.isdigit()):
            safe_chars.append(ch)
        elif ch in {" ", "-", "_"}:
            safe_chars.append(separator)
    sanitized = "".join(safe_chars)
    sanitized = re.sub(rf"{separator}+", separator, sanitized)
    sanitized = sanitized.strip(separator)
    return sanitized or "na"


def slugify(value: str, *, separator: str = "_") -> str:
    """Cria um slug seguro para diretórios de pacientes."""
    return sanitize_token(value, separator=separator)


def ensure_directory(path: Path) -> None:
    """Garante que um diretório exista."""
    path.mkdir(parents=True, exist_ok=True)


def first_date_from_text(text: str) -> date | None:
    """Tenta extrair a primeira data válida encontrada no texto."""
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                return date(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            except ValueError as exc:  # pragma: no cover - data inválida improvável
                LOGGER.debug("Não foi possível converter data %s: %s", match.group(0), exc)
    return None


def short_description(text: str, *, max_terms: int = 4, max_length: int = 60) -> str:
    """Gera uma descrição curta com base no texto."""
    words = _WORD_PATTERN.findall(text)
    if not words:
        return "documento"
    selected: Iterable[str] = (sanitize_token(word, separator="_") for word in words)
    filtered = [word for word in selected if word]
    if not filtered:
        return "documento"
    result = filtered[:max_terms]
    description = "-".join(result)
    return description[:max_length] or "documento"


def enforce_length(value: str, *, max_length: int) -> str:
    """Trunca o valor para no máximo *max_length* caracteres."""
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


def validate_safe_path(path: Path, base_dir: Path | None = None) -> None:
    """Valida se um caminho é seguro e não permite traversal de diretório.

    Args:
        path: Caminho a ser validado
        base_dir: Diretório base permitido (opcional)

    Raises:
        ValueError: Se o caminho for inseguro
    """
    # Resolver o caminho absoluto
    resolved = path.resolve()

    # Verificar se contém componentes perigosos (..)
    parts = resolved.parts
    if ".." in parts:
        raise ValueError(f"Caminho contém '..' (traversal): {path}")

    # Se base_dir fornecido, verificar se está dentro dele
    if base_dir:
        base_resolved = base_dir.resolve()
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValueError(f"Caminho fora do diretório base: {path} (base: {base_dir})")

    # Verificar se não é um link simbólico perigoso (opcional, mas recomendado)
    if path.is_symlink():
        target = path.readlink()
        if target.is_absolute() and not str(target).startswith(
            str(base_dir or Path.home())
        ):
            raise ValueError(f"Link simbólico aponta para local não permitido: {path} -> {target}")

