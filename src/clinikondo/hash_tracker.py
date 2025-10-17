"""Rastreamento de hashes de arquivos processados para detecção de duplicatas."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFileRecord:
    """Registro de arquivo processado."""
    hash_sha256: str
    arquivo_original: str
    arquivo_destino: str
    timestamp: str
    paciente_slug: str
    tipo_documento: str


class HashTracker:
    """Gerencia rastreamento de hashes de arquivos processados."""
    
    def __init__(self, storage_path: Path):
        """Inicializa o rastreador de hashes.
        
        Args:
            storage_path: Caminho para arquivo JSON de armazenamento
        """
        self.storage_path = storage_path
        self._records: Dict[str, ProcessedFileRecord] = {}
        self._load()
    
    def _load(self) -> None:
        """Carrega registros do arquivo de armazenamento."""
        if not self.storage_path.exists():
            logger.debug(f"Arquivo de hashes não existe, criando novo: {self.storage_path}")
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._records = {
                    hash_val: ProcessedFileRecord(**record)
                    for hash_val, record in data.items()
                }
            logger.debug(f"Carregados {len(self._records)} hashes processados")
        except Exception as e:
            logger.warning(f"Erro ao carregar hashes processados: {e}. Iniciando com registro vazio.")
            self._records = {}
    
    def save(self) -> None:
        """Salva registros no arquivo de armazenamento."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                data = {
                    hash_val: asdict(record)
                    for hash_val, record in self._records.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Salvos {len(self._records)} hashes processados")
        except Exception as e:
            logger.error(f"Erro ao salvar hashes processados: {e}")
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calcula hash SHA-256 de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Hash SHA-256 em hexadecimal
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {file_path}: {e}")
            raise
    
    def is_processed(self, file_hash: str) -> bool:
        """Verifica se arquivo com este hash já foi processado.
        
        Args:
            file_hash: Hash SHA-256 do arquivo
            
        Returns:
            True se já foi processado, False caso contrário
        """
        return file_hash in self._records
    
    def get_record(self, file_hash: str) -> Optional[ProcessedFileRecord]:
        """Obtém registro de arquivo processado.
        
        Args:
            file_hash: Hash SHA-256 do arquivo
            
        Returns:
            Registro se encontrado, None caso contrário
        """
        return self._records.get(file_hash)
    
    def add_record(
        self,
        file_hash: str,
        arquivo_original: str,
        arquivo_destino: str,
        paciente_slug: str,
        tipo_documento: str
    ) -> None:
        """Adiciona registro de arquivo processado.
        
        Args:
            file_hash: Hash SHA-256 do arquivo
            arquivo_original: Caminho do arquivo original
            arquivo_destino: Caminho do arquivo de destino
            paciente_slug: Slug do paciente associado
            tipo_documento: Tipo do documento
        """
        record = ProcessedFileRecord(
            hash_sha256=file_hash,
            arquivo_original=arquivo_original,
            arquivo_destino=arquivo_destino,
            timestamp=datetime.now().isoformat(),
            paciente_slug=paciente_slug,
            tipo_documento=tipo_documento
        )
        self._records[file_hash] = record
        logger.debug(f"Registrado hash {file_hash[:12]}... para {arquivo_original}")
    
    def log_duplicate_detection(
        self,
        file_hash: str,
        arquivo_novo: str,
        arquivo_original: str,
        tipo_duplicata: str,
        acao: str,
        **extra_info
    ) -> None:
        """Registra detecção de duplicata com log auditável.
        
        Args:
            file_hash: Hash SHA-256 do arquivo
            arquivo_novo: Caminho do novo arquivo
            arquivo_original: Caminho do arquivo original
            tipo_duplicata: Tipo de duplicata ('hash_identico' ou 'nome_duplicado')
            acao: Ação tomada ('processamento_pulado', 'versao_numerada_criada')
            **extra_info: Informações adicionais para o log
        """
        log_entry = {
            "evento": "duplicata_detectada",
            "tipo_duplicata": tipo_duplicata,
            "arquivo_novo": arquivo_novo,
            "arquivo_original": arquivo_original,
            "hash_sha256": file_hash,
            "acao": acao,
            "timestamp": datetime.now().isoformat(),
            **extra_info
        }
        
        logger.info(f"DUPLICATA: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas de arquivos processados.
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "total_processados": len(self._records),
            "por_tipo": {},
            "por_paciente": {}
        }
        
        for record in self._records.values():
            # Contar por tipo
            stats["por_tipo"][record.tipo_documento] = \
                stats["por_tipo"].get(record.tipo_documento, 0) + 1
            
            # Contar por paciente
            stats["por_paciente"][record.paciente_slug] = \
                stats["por_paciente"].get(record.paciente_slug, 0) + 1
        
        return stats
