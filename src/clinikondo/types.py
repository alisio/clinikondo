"""Catálogo de tipos de documentos médicos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .models import DocumentType
from .utils import sanitize_token


def _default_types() -> list[DocumentType]:
    return [
        DocumentType(
            nome_tipo="exame",
            subpasta_destino="exames",
            palavras_chave=["exame", "resultado", "imagem", "ultrassom", "laboratorio"],
            especialidades_rel=[
                "radiologia",
                "laboratorial",
                "cardiologia",
                "endocrinologia",
                "ginecologia",
                "otorrinolaringologia",
                "infectologia",
            ],
        ),
        DocumentType(
            nome_tipo="receita",
            subpasta_destino="receitas_medicas",
            palavras_chave=["receita", "prescricao", "uso continuo", "medicamento"],
        ),
        DocumentType(
            nome_tipo="vacina",
            subpasta_destino="vacinas",
            palavras_chave=["vacina", "imunizacao", "dose", "cartao"],
        ),
        DocumentType(
            nome_tipo="controle",
            subpasta_destino="controle_de_pressao_e_glicose",
            palavras_chave=["pressao", "glicose", "monitoramento", "controle"],
        ),
        DocumentType(
            nome_tipo="contato",
            subpasta_destino="contatos_medicos",
            palavras_chave=["contato", "telefone", "endereco", "clinica"],
            requer_data=False,
        ),
        DocumentType(
            nome_tipo="laudo",
            subpasta_destino="laudos",
            palavras_chave=["laudo", "relatorio", "atestado"],
        ),
        DocumentType(
            nome_tipo="agenda",
            subpasta_destino="agendas",
            palavras_chave=["agenda", "consulta", "agendamento"],
        ),
        DocumentType(
            nome_tipo="documento",
            subpasta_destino="documentos",
            palavras_chave=["documento", "formulario"],
        ),
    ]


# Mapeamento de sinônimos para melhorar resolução de tipos
_TYPE_SYNONYMS = {
    "relatorio": "laudo",
    "resultado": "exame", 
    "exame_laboratorial": "exame",
    "exame_sangue": "exame",
    "teste": "exame",
    "atestado": "laudo",
    "declaracao": "documento",
    "formulario": "documento",
    "comprovante": "documento",
}


class DocumentTypeCatalog:
    """Catálogo com estratégias para mapear um nome de tipo para uma subpasta."""

    def __init__(self, types: Iterable[DocumentType] | None = None) -> None:
        self._types: Dict[str, DocumentType] = {}
        for doc_type in types or _default_types():
            self._types[self._key(doc_type.nome_tipo)] = doc_type

    @staticmethod
    def _key(name: str) -> str:
        return sanitize_token(name, separator="_")

    def resolve(self, name: str | None) -> DocumentType:
        if not name:
            return self._types[self._key("documento")]
        
        # Normalizar nome para busca
        key = self._key(name)
        
        # Tentar busca direta primeiro
        if key in self._types:
            return self._types[key]
        
        # Usar mapeamento de sinônimos se disponível
        if key in _TYPE_SYNONYMS:
            synonym_key = self._key(_TYPE_SYNONYMS[key])
            if synonym_key in self._types:
                return self._types[synonym_key]
        
        # Busca fuzzy nas palavras-chave dos tipos
        for doc_type in self._types.values():
            for keyword in doc_type.palavras_chave:
                if sanitize_token(keyword, separator="_") == key:
                    return doc_type
        
        # Fallback para documento padrão
        return self._types[self._key("documento")]

    def infer_from_text(self, text: str) -> DocumentType:
        text_clean = sanitize_token(text, separator=" ")
        for doc_type in self._types.values():
            for keyword in doc_type.palavras_chave:
                if sanitize_token(keyword, separator=" ") in text_clean:
                    return doc_type
        return self.resolve("documento")

