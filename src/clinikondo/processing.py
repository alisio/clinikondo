"""Orquestração do pipeline de processamento de documentos CliniKondo."""

from __future__ import annotations

import io
import logging
import shutil
from pathlib import Path
from typing import Iterable, List

from .config import Config
from .llm import BaseExtractor
from .models import Document, DocumentProcessingError
from .patients import PatientRegistry
from .types import DocumentTypeCatalog
from .utils import ensure_directory, sanitize_token, short_description, slugify, validate_safe_path

LOGGER = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".txt"}


class DocumentProcessor:
    """Processa documentos com a magia organizacional do CliniKondo! ✨"""

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
        # Validar arquivo antes do processamento
        validation_errors = self._validate_file(path)
        if validation_errors:
            error_msg = f"Arquivo {path.name} falhou na validação: {'; '.join(validation_errors)}"
            LOGGER.warning(error_msg)
            raise DocumentProcessingError(error_msg)
        
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
        
        # Log adequado conforme a ação realizada
        if self.config.dry_run:
            action = "seria copiado para" if not self.config.mover_arquivo_original else "seria movido para"
        else:
            action = "copiado para" if not self.config.mover_arquivo_original else "movido para"
        
        document.log_processamento = f"Documento {action} {destination_path}"
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
        data_prefix = document.data_documento.strftime("%Y-%m-%d")
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
        """Move ou copia o documento conforme configuração."""
        # Validar caminho de destino para prevenir traversal
        validate_safe_path(destination, self.config.output_dir)
        
        if self.config.mover_arquivo_original:
            # Move o arquivo (deleta original)
            shutil.move(source, destination)
        else:
            # Copia o arquivo (preserva original) - comportamento padrão
            shutil.copy2(source, destination)

    def _preserve_on_error(self, source: Path) -> None:
        destino_base = self.config.output_dir / "falhas"
        ensure_directory(destino_base)
        destino = destino_base / source.name
        counter = 1
        while destino.exists():
            destino = destino_base / f"{source.stem}-{counter}{source.suffix}"
            counter += 1
        
        # Validar caminho de destino para prevenir traversal
        validate_safe_path(destino, self.config.output_dir)
        
        shutil.copy2(source, destino)

    def _extract_text(self, path: Path) -> str:
        try:
            if path.suffix.lower() == ".txt":
                text = path.read_text(encoding="utf-8")
                return text
            elif path.suffix.lower() == ".pdf":
                return self._extract_text_pdf(path)
            elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic"}:
                return self._extract_text_image(path)
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
                return text
        except Exception as exc:
            LOGGER.warning("Falha ao extrair texto de %s: %s", path.name, exc)
            return ""

    def _extract_text_pdf(self, path: Path) -> str:
        """Extrai texto de PDF seguindo a estratégia configurada."""
        strategy = self.config.ocr_strategy
        
        # Tentar PyPDF2 primeiro (rápido e eficiente)
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            LOGGER.debug("PyPDF2 não instalado")
            return self._apply_ocr_strategy(path, strategy, pypdf2_failed=True)
        
        text_parts: list[str] = []
        with path.open("rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        
        extracted_text = "\n".join(text_parts).strip()
        
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("PyPDF2 extraiu %d caracteres de %s", len(extracted_text), path.name)
        
        # Se não conseguiu extrair texto, aplicar estratégia OCR
        if not extracted_text:
            LOGGER.info("PDF sem texto embutido detectado, tentando OCR: %s", path.name)
            return self._apply_ocr_strategy(path, strategy, pypdf2_failed=True)
        
        return extracted_text
    
    def _apply_ocr_strategy(self, path: Path, strategy: str, pypdf2_failed: bool = False) -> str:
        """Aplica estratégia de OCR conforme configuração."""
        if strategy == "multimodal":
            # Apenas multimodal
            return self._extract_text_pdf_with_multimodal_ocr(path)
        
        elif strategy == "traditional":
            # Apenas OCR tradicional
            return self._extract_text_pdf_with_ocr(path)
        
        else:  # hybrid (padrão)
            # Tenta multimodal primeiro, fallback para traditional
            try:
                text = self._extract_text_pdf_with_multimodal_ocr(path)
                if text and len(text.strip()) > 0:
                    return text
            except Exception as exc:
                LOGGER.debug("Multimodal OCR falhou, tentando traditional: %s", exc)
            
            # Fallback para traditional
            return self._extract_text_pdf_with_ocr(path)

    @staticmethod
    def _extract_text_image(path: Path) -> str:
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore
        except ImportError:  # pragma: no cover - depende de pip
            LOGGER.debug("Bibliotecas de OCR não instaladas, texto vazio para %s", path)
            return ""
        
        with Image.open(path) as img:
            extracted_text = pytesseract.image_to_string(img, lang='por')
            
            # Log detalhado em modo debug
            if LOGGER.isEnabledFor(logging.DEBUG):
                text_clean = extracted_text.strip()
                char_count = len(text_clean)
                if char_count > 0:
                    preview = text_clean[:200] + "..." if len(text_clean) > 200 else text_clean
                    LOGGER.debug("OCR imagem %s (%d chars): %s", path.name, char_count, preview)
                else:
                    LOGGER.debug("OCR imagem %s: nenhum texto encontrado", path.name)
            
            return extracted_text

    @staticmethod
    def _extract_text_pdf_with_ocr(path: Path) -> str:
        """Extrai texto de PDF escaneado usando OCR tradicional."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore
        except ImportError:  # pragma: no cover - depende de pip
            LOGGER.debug("Bibliotecas de OCR/PDF não instaladas para %s", path)
            return ""
        
        text_parts: list[str] = []
        
        # Abre o PDF com PyMuPDF
        with fitz.open(path) as doc:
            total_pages = len(doc)
            LOGGER.debug("Iniciando OCR tradicional em PDF com %d páginas: %s", total_pages, path.name)
            
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                
                # Converte página para imagem
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Aplica OCR na imagem
                with Image.open(io.BytesIO(img_data)) as img:
                    page_text = pytesseract.image_to_string(img, lang='por')
                    text_parts.append(page_text)
                    
                    # Log detalhado por página em modo debug
                    if LOGGER.isEnabledFor(logging.DEBUG):
                        page_text_clean = page_text.strip()
                        char_count = len(page_text_clean)
                        if char_count > 0:
                            preview = page_text_clean[:150] + "..." if len(page_text_clean) > 150 else page_text_clean
                            LOGGER.debug("OCR tradicional página %d/%d (%d chars): %s", page_num + 1, total_pages, char_count, preview)
                        else:
                            LOGGER.debug("OCR tradicional página %d/%d: nenhum texto encontrado", page_num + 1, total_pages)
        
        final_text = "\n".join(text_parts)
        LOGGER.info("OCR tradicional concluído para %s: %d caracteres extraídos", path.name, len(final_text))
        return final_text
    
    def _extract_text_pdf_with_multimodal_ocr(self, path: Path) -> str:
        """Extrai texto de PDF escaneado usando LLM multimodal (ex: GPT-4 Vision)."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image  # type: ignore
            import base64
            from openai import OpenAI  # type: ignore
        except ImportError:  # pragma: no cover - depende de pip
            LOGGER.debug("Bibliotecas necessárias para OCR multimodal não instaladas")
            raise RuntimeError("Bibliotecas necessárias para OCR multimodal não instaladas")
        
        # Validar segurança da transmissão de dados médicos
        api_base = self.config.effective_ocr_api_base or "https://api.openai.com/v1"
        if not api_base.startswith("https://"):
            raise RuntimeError(
                f"Transmissão insegura detectada: API base deve usar HTTPS para proteger dados médicos. "
                f"URL atual: {api_base}. Configure uma URL HTTPS segura."
            )
        
        if not self.config.effective_ocr_api_key:
            raise RuntimeError("API key não configurada para OCR multimodal")
        
        client = OpenAI(
            api_key=self.config.effective_ocr_api_key,
            base_url=api_base
        )
        
        text_parts: list[str] = []
        
        with fitz.open(path) as doc:
            total_pages = len(doc)
            LOGGER.debug("Iniciando OCR multimodal em PDF com %d páginas: %s", total_pages, path.name)
            
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                
                # Converte página para imagem
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Encode para base64
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                
                try:
                    # Chama LLM multimodal para extrair texto
                    response = client.chat.completions.create(
                        model=self.config.modelo_llm if "vision" in self.config.modelo_llm.lower() else "gpt-4-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extraia todo o texto visível nesta imagem de documento médico. Retorne apenas o texto, preservando a formatação."},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                                    }
                                ]
                            }
                        ],
                        max_tokens=self.config.llm_max_tokens * 2,  # Mais tokens para OCR
                        temperature=0.0  # Determinístico para OCR
                    )
                    
                    page_text = response.choices[0].message.content or ""
                    text_parts.append(page_text)
                    
                    if LOGGER.isEnabledFor(logging.DEBUG):
                        char_count = len(page_text.strip())
                        if char_count > 0:
                            preview = page_text[:150] + "..." if len(page_text) > 150 else page_text
                            LOGGER.debug("OCR multimodal página %d/%d (%d chars): %s", page_num + 1, total_pages, char_count, preview)
                        else:
                            LOGGER.debug("OCR multimodal página %d/%d: nenhum texto encontrado", page_num + 1, total_pages)
                
                except Exception as page_exc:
                    LOGGER.warning("Erro ao processar página %d com OCR multimodal: %s", page_num + 1, page_exc)
                    # Continuar com próxima página
        
        final_text = "\n".join(text_parts)
        LOGGER.info("OCR multimodal concluído para %s: %d caracteres extraídos", path.name, len(final_text))
        return final_text

    def _validate_file(self, file_path: Path) -> List[str]:
        """Valida um arquivo conforme as regras do SRS do CliniKondo."""
        errors = []
        
        if not file_path.exists():
            errors.append(f"Arquivo não encontrado: {file_path}")
            return errors
        
        # Verificar tamanho (limite de 50MB)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            errors.append(f"Arquivo muito grande: {size_mb:.1f}MB (máximo: 50MB)")
        
        # Verificar extensão suportada
        extension = file_path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            errors.append(f"Formato não suportado: {extension}")
        
        # Verificar caracteres perigosos no nome
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in file_path.name for char in dangerous_chars):
            errors.append(f"Nome de arquivo contém caracteres perigosos: {file_path.name}")
        
        # Verificar se nome não é muito longo (limite prático de 255 caracteres)
        if len(file_path.name) > 255:
            errors.append(f"Nome de arquivo muito longo: {len(file_path.name)} caracteres (máximo: 255)")
        
        # Verificar se arquivo não está vazio
        if file_path.stat().st_size == 0:
            errors.append("Arquivo está vazio")
        
        return errors
