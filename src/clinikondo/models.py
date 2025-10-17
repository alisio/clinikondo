"""Definição das entidades principais do CliniKondo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


class DocumentProcessingError(Exception):
    """Erro lançado durante o processamento de um documento médico."""


@dataclass(slots=True)
class LLMExtractionResult:
    """Resultado estruturado retornado por um extrator LLM ou heurístico."""

    nome_paciente: str
    data_documento: date
    tipo_documento: str
    especialidade: str | None = None
    descricao_curta: str | None = None
    classificar_como_compartilhado: bool = False
    extras: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Document:
    """Representa um documento médico a ser processado."""

    caminho_entrada: Path
    texto_extraido: str = ""
    nome_paciente_inferido: str | None = None
    data_documento: date | None = None
    tipo_documento: str | None = None
    especialidade: str | None = None
    descricao_curta: str | None = None
    nome_arquivo_final: str | None = None
    caminho_destino: Path | None = None
    classificado_como_compartilhado: bool = False
    log_processamento: str = ""
    resposta_bruta_llm: str | None = None
    dados_extraidos: Dict[str, str] = field(default_factory=dict)
    # Campos adicionados conforme SRS
    hash_sha256: str | None = None
    metodo_extracao: str = "pypdf2"  # pypdf2, ocr_traditional, ocr_multimodal
    ocr_aplicado: bool = False
    paginas_processadas: int | None = None
    chars_extraidos: int = 0
    confianca_extracao: float = 0.0
    tempo_processamento_ms: int = 0
    tentativas_llm: int = 0

    @property
    def nome_arquivo_original(self) -> str:
        return self.caminho_entrada.name

    @property
    def formato(self) -> str:
        return self.caminho_entrada.suffix.lower().lstrip(".")

    def aplicar_extracao(self, resultado: LLMExtractionResult) -> None:
        """Atualiza o documento com o resultado da extração."""
        self.nome_paciente_inferido = resultado.nome_paciente
        self.data_documento = resultado.data_documento
        self.tipo_documento = resultado.tipo_documento
        self.especialidade = resultado.especialidade
        self.descricao_curta = resultado.descricao_curta
        self.classificado_como_compartilhado = resultado.classificar_como_compartilhado
        self.dados_extraidos.update(resultado.extras)

    def validar_campos_obrigatorios(self) -> None:
        """Garante que os campos obrigatórios estejam presentes."""
        if not self.nome_paciente_inferido:
            raise DocumentProcessingError("Nome do paciente não pôde ser inferido.")
        if not self.data_documento:
            raise DocumentProcessingError("Data do documento não encontrada.")
        if not self.tipo_documento:
            raise DocumentProcessingError("Tipo de documento não identificado.")


@dataclass(slots=True)
class Patient:
    """Representa um paciente conhecido pelo sistema."""

    nome_completo: str
    slug_diretorio: str
    nomes_alternativos: List[str] = field(default_factory=list)
    data_nascimento: Optional[date] = None
    genero: Optional[str] = None
    documentos_associados: List[str] = field(default_factory=list)
    # Campos adicionados conforme SRS
    data_criacao: datetime = field(default_factory=datetime.now)
    data_ultima_atualizacao: datetime = field(default_factory=datetime.now)
    documentos_count: int = 0
    confianca_nome: float = 1.0
    origem_criacao: str = "manual_add"  # llm_extraction, manual_add, fuzzy_match

    def nomes_normalizados(self) -> List[str]:
        """Lista os nomes possíveis normalizados."""
        return [self.nome_completo, *self.nomes_alternativos]


@dataclass(slots=True)
class DocumentType:
    """Representa um tipo de documento e seu destino."""

    nome_tipo: str
    subpasta_destino: str
    palavras_chave: List[str] = field(default_factory=list)
    especialidades_rel: List[str] = field(default_factory=list)
    requer_data: bool = True


@dataclass(slots=True)
class LLMCallLog:
    """Mantém metadados sobre uma interação com o LLM."""

    documento: Path
    prompt_utilizado: str
    data_extracao: datetime
    modelo_utilizado: str
    tempo_resposta_ms: int
    sucesso: bool
    mensagem_erro: str | None = None

