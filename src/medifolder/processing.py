"""Orquestração do pipeline de processamento de documentos."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Iterable, List

from .config import Config
from .llm import BaseExtractor
from .models import Document, DocumentProcessingError
from .patients import PatientRegistry
from .types import DocumentTypeCatalog
from .utils import ensure_directory, sanitize_token, short_description, slugify

LOGGER = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".txt"}


class DocumentProcessor:
    """Processa documentos conforme regras de negócio definidas."""

    def __init__(
        self,
        config: Config,
        extractor: BaseExtractor,
        patient_registry: PatientRegistry,
        type_catalog: DocumentTypeCatalog,
    ) -> None:
        self.config = config
        self.extractor = extractor
        self.patient_registry = patient_registry
        self.type_catalog = type_catalog

    def collect_documents(self) -> List[Path]:
        documents: list[Path] = []
        for path in sorted(self.config.input_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append(path)
        return documents

    def process_all(self) -> List[Document]:
        processed: list[Document] = []
        for path in self.collect_documents():
            LOGGER.info("Processando %s", path.name)
            try:
                document = self._process_single(path)
                processed.append(document)
            except Exception as exc:  # pragma: no cover - logging de erro
                LOGGER.exception("Erro ao processar %s: %s", path.name, exc)
                if self.config.executar_copia_apos_erro:
                    self._preserve_on_error(path)
        self.patient_registry.save()
        return processed

    def _process_single(self, path: Path) -> Document:
        document = Document(caminho_entrada=path)
        document.texto_extraido = self._extract_text(path)
        extractor_result = self.extractor.extract(
            document,
            patient_registry=self.patient_registry,
            type_catalog=self.type_catalog,
        )
        document.aplicar_extracao(extractor_result)
        if not document.descricao_curta:
            document.descricao_curta = short_description(document.texto_extraido)
        document.validar_campos_obrigatorios()
        patient = self._resolve_patient(document)
        doc_type = self.type_catalog.resolve(document.tipo_documento)
        final_name = self._build_final_name(document, patient.slug_diretorio)
        document.nome_arquivo_final = final_name
        destination_dir = self._build_destination_dir(patient.slug_diretorio, doc_type.subpasta_destino, document)
        ensure_directory(destination_dir)
        destination_path = self._unique_destination(destination_dir / final_name)
        document.caminho_destino = destination_path
        if not self.config.dry_run:
            self._move_document(document.caminho_entrada, destination_path)
        document.log_processamento = f"Documento movido para {destination_path}"
        return document

    def _resolve_patient(self, document: Document):
        inferred_name = document.nome_paciente_inferido or "Compartilhado"
        patient = None
        if self.config.match_nome_paciente_auto:
            patient = self.patient_registry.match(inferred_name)
        if not patient and self.config.match_nome_paciente_auto:
            patient = self.patient_registry.match_in_text(document.texto_extraido)
        if patient:
            return patient
        if self.config.mover_para_compartilhado_sem_match:
            document.classificado_como_compartilhado = True
            return self.patient_registry.ensure_patient("Compartilhado", create_if_missing=True)
        if not self.config.criar_paciente_sem_match:
            raise DocumentProcessingError("Paciente não encontrado e criação automática desabilitada.")
        return self.patient_registry.ensure_patient(inferred_name, create_if_missing=True)

    def _build_destination_dir(
        self, patient_slug: str, subfolder: str, document: Document
    ) -> Path:
        base_dir = self.config.output_dir
        if document.classificado_como_compartilhado:
            base_dir = base_dir / "compartilhado"
        return base_dir / patient_slug / subfolder

    def _build_final_name(self, document: Document, patient_slug: str) -> str:
        data_prefix = document.data_documento.strftime("%Y-%m")
        patient_part = slugify(document.nome_paciente_inferido or patient_slug, separator="_")
        tipo_part = sanitize_token(document.tipo_documento or "documento", separator="-")
        especialidade_part = sanitize_token(document.especialidade or "geral", separator="-")
        descricao_part = sanitize_token(document.descricao_curta or "documento", separator="-")
        descricao_part = descricao_part[:60]
        base_name = f"{data_prefix}-{patient_part}-{tipo_part}-{especialidade_part}-{descricao_part}"
        extension = document.caminho_entrada.suffix.lower()
        full_name = f"{base_name}{extension}"
        if len(full_name) > 150:
            excesso = len(full_name) - 150
            descricao_part = descricao_part[:-excesso] if excesso < len(descricao_part) else descricao_part[: max(1, 60 - excesso)]
            base_name = f"{data_prefix}-{patient_part}-{tipo_part}-{especialidade_part}-{descricao_part}"
            full_name = f"{base_name}{extension}"
        return full_name

    def _unique_destination(self, target: Path) -> Path:
        if not target.exists():
            return target
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while True:
            candidate = target.with_name(f"{stem}-{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _move_document(self, source: Path, destination: Path) -> None:
        shutil.move(source, destination)

    def _preserve_on_error(self, source: Path) -> None:
        destino_base = self.config.output_dir / "falhas"
        ensure_directory(destino_base)
        destino = destino_base / source.name
        counter = 1
        while destino.exists():
            destino = destino_base / f"{source.stem}-{counter}{source.suffix}"
            counter += 1
        shutil.copy2(source, destino)

    def _extract_text(self, path: Path) -> str:
        try:
            if path.suffix.lower() == ".txt":
                return path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".pdf":
                return self._extract_text_pdf(path)
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic"}:
                return self._extract_text_image(path)
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            LOGGER.warning("Falha ao extrair texto de %s: %s", path.name, exc)
            return ""

    @staticmethod
    def _extract_text_pdf(path: Path) -> str:
        try:
            import PyPDF2  # type: ignore
        except ImportError:  # pragma: no cover - depende de pip
            LOGGER.debug("PyPDF2 não instalado, retornando texto vazio para %s", path)
            return ""
        text_parts: list[str] = []
        with path.open("rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    @staticmethod
    def _extract_text_image(path: Path) -> str:
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore
        except ImportError:  # pragma: no cover - depende de pip
            LOGGER.debug("Bibliotecas de OCR não instaladas, texto vazio para %s", path)
            return ""
        with Image.open(path) as img:
            return pytesseract.image_to_string(img)
