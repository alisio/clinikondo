"""Interface de linha de comando do CliniKondo - onde a magia começa! ✨"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from . import load_config_from_args, run_pipeline
from .config import Config
from .models import Patient
from .patients import PatientRegistry
from .processing import SUPPORTED_EXTENSIONS


def validate_file(file_path: Path) -> List[str]:
    """Valida um arquivo conforme regras do SRS."""
    errors = []
    
    if not file_path.exists():
        errors.append(f"Arquivo não encontrado: {file_path}")
        return errors
    
    # Verificar tamanho (limite de 50MB)
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        errors.append(f"Arquivo muito grande: {size_mb:.1f}MB (máximo: 50MB)")
    
    # Verificar extensão
    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        errors.append(f"Formato não suportado: {extension}")
    
    # Verificar caracteres perigosos no nome
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
    if any(char in file_path.name for char in dangerous_chars):
        errors.append(f"Nome de arquivo contém caracteres perigosos: {file_path.name}")
    
    return errors


def calculate_file_hash(file_path: Path) -> str:
    """Calcula hash SHA-256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def find_duplicates(directory: Path) -> Dict[str, List[Path]]:
    """Encontra arquivos duplicados por hash."""
    file_hashes = {}
    duplicates = {}
    
    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                file_hash = calculate_file_hash(file_path)
                if file_hash in file_hashes:
                    if file_hash not in duplicates:
                        duplicates[file_hash] = [file_hashes[file_hash]]
                    duplicates[file_hash].append(file_path)
                else:
                    file_hashes[file_hash] = file_path
            except Exception as e:
                logging.warning(f"Erro ao processar {file_path}: {e}")
    
    return duplicates


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos com comandos avançados do CliniKondo."""
    parser = argparse.ArgumentParser(
        prog="clinikondo",
        description="CliniKondo: O assistente que transforma o caos de exames, receitas e laudos em pura harmonia digital! 🏥✨",
        epilog="Organize documentos médicos com leveza, humor e método - cada PDF encontra seu lugar! 📁"
    )

    # Usar subparsers para comandos avançados
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Comando principal: processar
    processar_parser = subparsers.add_parser(
        "processar",
        help="Organizar documentos médicos (comando padrão)",
        description="Processa e organiza documentos médicos"
    )
    
    processar_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Diretório de entrada com os documentos a processar"
    )
    processar_parser.add_argument(
        "--output", "-o", 
        required=True,
        help="Diretório base onde os documentos serão organizados"
    )
    processar_parser.add_argument("--model", help="Modelo LLM principal (obrigatório)")
    processar_parser.add_argument("--api-key", help="Chave de API para o provedor LLM")
    processar_parser.add_argument("--api-base", help="Endpoint alternativo para a API LLM")
    processar_parser.add_argument("--temperature", type=float, help="Temperatura da inferência LLM (0-2)")
    processar_parser.add_argument("--max-tokens", type=int, help="Quantidade máxima de tokens do LLM")
    processar_parser.add_argument("--prompt-template", help="Caminho para o template de prompt")
    processar_parser.add_argument("--ocr-strategy", choices=["hybrid", "multimodal", "traditional"], default="hybrid", help="Estratégia de OCR (hybrid, multimodal, traditional)")
    # Multi-model configuration (SRS v2.0)
    processar_parser.add_argument("--ocr-model", help="Modelo LLM para OCR (opcional, fallback: --model)")
    processar_parser.add_argument("--ocr-api-key", help="Chave API para OCR (opcional, fallback: --api-key)")
    processar_parser.add_argument("--ocr-api-base", help="Endpoint API para OCR (opcional, fallback: --api-base)")
    processar_parser.add_argument("--classification-model", help="Modelo LLM para classificação (opcional, fallback: --model)")
    processar_parser.add_argument("--classification-api-key", help="Chave API para classificação (opcional, fallback: --api-key)")
    processar_parser.add_argument("--classification-api-base", help="Endpoint API para classificação (opcional, fallback: --api-base)")
    processar_parser.add_argument("--log-level", help="Nível de log (debug, info, warning, error)")
    processar_parser.add_argument("--dry-run", action="store_true", help="Simula sem mover arquivos")
    processar_parser.add_argument("--match-patient", action=argparse.BooleanOptionalAction, default=None)
    processar_parser.add_argument("--create-patient", action=argparse.BooleanOptionalAction, default=None)
    processar_parser.add_argument("--move-to-shared", action=argparse.BooleanOptionalAction, default=None)
    processar_parser.add_argument("--copy-on-error", action=argparse.BooleanOptionalAction, default=None)
    processar_parser.add_argument("--mover", action="store_true", help="Move arquivos em vez de copiar")

    # Comando: listar pacientes
    listar_parser = subparsers.add_parser(
        "listar-pacientes",
        help="Lista todos os pacientes registrados",
        description="Exibe informações dos pacientes no sistema"
    )
    listar_parser.add_argument("--formato", choices=["tabela", "json", "csv"], default="tabela", help="Formato de saída")
    listar_parser.add_argument("--filtro", help="Filtrar pacientes por nome (busca parcial)")
    listar_parser.add_argument("--output-dir", help="Diretório para buscar pacientes (padrão: diretório atual)")

    # Comando: verificar duplicatas
    duplicatas_parser = subparsers.add_parser(
        "verificar-duplicatas",
        help="Verifica documentos duplicados",
        description="Identifica possíveis documentos duplicados no sistema"
    )
    duplicatas_parser.add_argument("pasta", help="Pasta para verificar duplicatas")
    duplicatas_parser.add_argument("--acao", choices=["listar", "remover", "mover"], default="listar", help="Ação com duplicatas")
    duplicatas_parser.add_argument("--pasta-backup", help="Pasta para mover duplicatas (se ação=mover)")

    # Comando: relatório de processamento
    relatorio_parser = subparsers.add_parser(
        "relatorio-processamento",
        help="Gera relatório de documentos processados",
        description="Cria relatório detalhado do processamento"
    )
    relatorio_parser.add_argument("--periodo", type=int, default=30, help="Período em dias (padrão: 30)")
    relatorio_parser.add_argument("--formato", choices=["texto", "json", "html"], default="texto", help="Formato do relatório")
    relatorio_parser.add_argument("--output-dir", help="Diretório para analisar (padrão: diretório atual)")

    # Comando: validar estrutura
    validar_parser = subparsers.add_parser(
        "validar-estrutura",
        help="Valida estrutura de pastas organizadas",
        description="Verifica se a estrutura de pastas está correta"
    )
    validar_parser.add_argument("pasta", help="Pasta para validar")
    validar_parser.add_argument("--corrigir", action="store_true", help="Corrige problemas automaticamente")

    # Comando: mostrar log
    log_parser = subparsers.add_parser(
        "mostrar-log",
        help="Exibe logs do sistema",
        description="Mostra logs de processamento e erros"
    )
    log_parser.add_argument("--nivel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Nível mínimo dos logs")
    log_parser.add_argument("--linhas", type=int, default=50, help="Número de linhas (padrão: 50)")

    # Comando: gerenciar pacientes
    pacientes_parser = subparsers.add_parser(
        "gerenciar-pacientes",
        help="Gerencia cadastro de pacientes",
        description="Adiciona, edita, remove e fusiona pacientes"
    )
    pacientes_subparsers = pacientes_parser.add_subparsers(dest="acao_paciente", help="Ações disponíveis")

    # Subcomando: adicionar paciente
    add_patient_parser = pacientes_subparsers.add_parser("adicionar", help="Adiciona novo paciente")
    add_patient_parser.add_argument("nome", help="Nome completo do paciente")
    add_patient_parser.add_argument("--genero", choices=["M", "F", "O"], help="Gênero do paciente")
    add_patient_parser.add_argument("--aliases", nargs="*", help="Nomes alternativos")
    add_patient_parser.add_argument("--output-dir", help="Diretório de dados (padrão: diretório atual)")

    # Subcomando: editar paciente
    edit_patient_parser = pacientes_subparsers.add_parser("editar", help="Edita paciente existente")
    edit_patient_parser.add_argument("slug", help="Identificador do paciente")
    edit_patient_parser.add_argument("--nome", help="Novo nome completo")
    edit_patient_parser.add_argument("--genero", choices=["M", "F", "O"], help="Novo gênero")
    edit_patient_parser.add_argument("--add-alias", action="append", help="Adicionar alias")
    edit_patient_parser.add_argument("--output-dir", help="Diretório de dados (padrão: diretório atual)")

    # Subcomando: remover paciente
    remove_patient_parser = pacientes_subparsers.add_parser("remover", help="Remove paciente")
    remove_patient_parser.add_argument("slug", help="Identificador do paciente")
    remove_patient_parser.add_argument("--confirmar", action="store_true", help="Confirma remoção sem prompt")
    remove_patient_parser.add_argument("--output-dir", help="Diretório de dados (padrão: diretório atual)")

    # Subcomando: fusionar pacientes
    merge_patient_parser = pacientes_subparsers.add_parser("fusionar", help="Fusiona dois pacientes")
    merge_patient_parser.add_argument("source_slug", help="Paciente a ser mesclado (será removido)")
    merge_patient_parser.add_argument("target_slug", help="Paciente que receberá os aliases")
    merge_patient_parser.add_argument("--output-dir", help="Diretório de dados (padrão: diretório atual)")

    # Subcomando: detectar duplicatas
    duplicates_patient_parser = pacientes_subparsers.add_parser("detectar-duplicatas", help="Detecta possíveis duplicatas")
    duplicates_patient_parser.add_argument("--threshold", type=float, default=0.85, help="Limiar de similaridade (0-1)")
    duplicates_patient_parser.add_argument("--output-dir", help="Diretório de dados (padrão: diretório atual)")

    return parser


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def cmd_listar_pacientes(args) -> int:
    """Lista pacientes registrados no sistema."""
    try:
        output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
        # Procurar arquivo de registro de pacientes
        patient_file = output_dir / "patients.json"
        
        registry = PatientRegistry(patient_file if patient_file.exists() else None)
        
        pacientes = list(registry.list())
        
        if args.filtro:
            filtro_lower = args.filtro.lower()
            pacientes = [p for p in pacientes if filtro_lower in p.nome_completo.lower()]
        
        if not pacientes:
            print("Nenhum paciente encontrado.")
            if not patient_file.exists():
                print(f"Arquivo de pacientes não encontrado: {patient_file}")
                print("Execute o comando 'processar' primeiro para registrar pacientes.")
            return 0
        
        if args.formato == "json":
            dados = [{"nome": p.nome_completo, "slug": p.slug_diretorio, "aliases": p.nomes_alternativos} for p in pacientes]
            print(json.dumps(dados, indent=2, ensure_ascii=False))
        elif args.formato == "csv":
            print("Nome,Slug,Aliases")
            for p in pacientes:
                aliases = ";".join(p.nomes_alternativos)
                print(f'"{p.nome_completo}","{p.slug_diretorio}","{aliases}"')
        else:  # tabela
            print(f"{'Nome':<30} {'Slug':<15} {'Aliases'}")
            print("-" * 70)
            for p in pacientes:
                aliases = ", ".join(p.nomes_alternativos[:2])  # Mostrar apenas primeiros 2
                if len(p.nomes_alternativos) > 2:
                    aliases += f" (+{len(p.nomes_alternativos)-2} mais)"
                print(f"{p.nome_completo:<30} {p.slug_diretorio:<15} {aliases}")
        
        print(f"\nTotal: {len(pacientes)} paciente(s)")
        return 0
        
    except Exception as e:
        print(f"Erro ao listar pacientes: {e}")
        return 1


def cmd_verificar_duplicatas(args) -> int:
    """Verifica e gerencia documentos duplicados."""
    try:
        pasta = Path(args.pasta)
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            return 1
        
        print("🔍 Procurando duplicatas...")
        duplicates = find_duplicates(pasta)
        
        if not duplicates:
            print("✅ Nenhuma duplicata encontrada!")
            return 0
        
        total_duplicatas = sum(len(files) - 1 for files in duplicates.values())
        print(f"⚠️  Encontradas {total_duplicatas} duplicata(s) em {len(duplicates)} grupo(s)")
        
        for i, (file_hash, files) in enumerate(duplicates.items(), 1):
            print(f"\nGrupo {i} (hash: {file_hash[:12]}...):")
            for j, file_path in enumerate(files):
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  {j+1}. {file_path} ({size_mb:.1f}MB)")
        
        if args.acao == "remover":
            removed_count = 0
            for files in duplicates.values():
                # Manter o primeiro arquivo, remover os demais
                for file_path in files[1:]:
                    try:
                        file_path.unlink()
                        print(f"🗑️  Removido: {file_path}")
                        removed_count += 1
                    except Exception as e:
                        print(f"❌ Erro ao remover {file_path}: {e}")
            print(f"\n✅ {removed_count} arquivo(s) duplicado(s) removido(s)")
        
        elif args.acao == "mover":
            if not args.pasta_backup:
                print("❌ Especifique --pasta-backup para mover duplicatas")
                return 1
            
            backup_dir = Path(args.pasta_backup)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            moved_count = 0
            for files in duplicates.values():
                for file_path in files[1:]:
                    try:
                        dest_path = backup_dir / file_path.name
                        # Garantir nome único
                        counter = 1
                        while dest_path.exists():
                            stem = file_path.stem
                            suffix = file_path.suffix
                            dest_path = backup_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        file_path.rename(dest_path)
                        print(f"📦 Movido: {file_path} -> {dest_path}")
                        moved_count += 1
                    except Exception as e:
                        print(f"❌ Erro ao mover {file_path}: {e}")
            print(f"\n✅ {moved_count} arquivo(s) duplicado(s) movido(s)")
        
        return 0
        
    except Exception as e:
        print(f"Erro ao verificar duplicatas: {e}")
        return 1


def cmd_relatorio_processamento(args) -> int:
    """Gera relatório de processamento de documentos."""
    try:
        output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
        
        # Coletar estatísticas
        stats = {
            "total_arquivos": 0,
            "por_tipo": {},
            "por_paciente": {},
            "erros": 0,
            "data_inicio": datetime.now() - timedelta(days=args.periodo),
            "data_fim": datetime.now()
        }
        
        # Analisar estrutura de arquivos
        for file_path in output_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Verificar se arquivo foi modificado no período
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime >= stats["data_inicio"]:
                    stats["total_arquivos"] += 1
                    
                    # Contar por tipo
                    ext = file_path.suffix.lower()
                    stats["por_tipo"][ext] = stats["por_tipo"].get(ext, 0) + 1
                    
                    # Tentar identificar paciente pela estrutura de pastas
                    parts = file_path.parts
                    for part in parts:
                        if any(keyword in part.lower() for keyword in ["paciente", "patient"]):
                            stats["por_paciente"][part] = stats["por_paciente"].get(part, 0) + 1
                            break
        
        if args.formato == "json":
            # Converter datetime para string para JSON
            stats_json = stats.copy()
            stats_json["data_inicio"] = stats["data_inicio"].isoformat()
            stats_json["data_fim"] = stats["data_fim"].isoformat()
            print(json.dumps(stats_json, indent=2, ensure_ascii=False))
        
        elif args.formato == "html":
            html = f"""
            <html>
            <head><title>Relatório CliniKondo</title></head>
            <body>
            <h1>📊 Relatório de Processamento - CliniKondo</h1>
            <p><strong>Período:</strong> {stats["data_inicio"].strftime("%d/%m/%Y")} a {stats["data_fim"].strftime("%d/%m/%Y")}</p>
            <p><strong>Total de arquivos:</strong> {stats["total_arquivos"]}</p>
            
            <h2>📁 Por Tipo de Arquivo</h2>
            <ul>
            """
            for tipo, count in stats["por_tipo"].items():
                html += f"<li>{tipo}: {count} arquivo(s)</li>"
            
            html += """
            </ul>
            <h2>👥 Por Paciente</h2>
            <ul>
            """
            for paciente, count in stats["por_paciente"].items():
                html += f"<li>{paciente}: {count} arquivo(s)</li>"
            
            html += """
            </ul>
            </body>
            </html>
            """
            print(html)
        
        else:  # texto
            print("📊 RELATÓRIO DE PROCESSAMENTO - CLINIKONDO")
            print("=" * 50)
            print(f"Período: {stats['data_inicio'].strftime('%d/%m/%Y')} a {stats['data_fim'].strftime('%d/%m/%Y')}")
            print(f"Total de arquivos processados: {stats['total_arquivos']}")
            
            if stats["por_tipo"]:
                print("\n📁 Arquivos por tipo:")
                for tipo, count in sorted(stats["por_tipo"].items()):
                    print(f"  {tipo}: {count} arquivo(s)")
            
            if stats["por_paciente"]:
                print("\n👥 Arquivos por paciente:")
                for paciente, count in sorted(stats["por_paciente"].items()):
                    print(f"  {paciente}: {count} arquivo(s)")
        
        return 0
        
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return 1


def cmd_validar_estrutura(args) -> int:
    """Valida estrutura de pastas organizadas."""
    try:
        pasta = Path(args.pasta)
        if not pasta.exists():
            print(f"Pasta não encontrada: {pasta}")
            return 1
        
        print("🔍 Validando estrutura de pastas...")
        
        problemas = []
        arquivos_validados = 0
        
        # Filtros para excluir diretórios desnecessários
        exclude_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache'}
        
        # Validar apenas arquivos relevantes
        for file_path in pasta.rglob("*"):
            # Pular se estiver em diretório excluído
            if any(part in exclude_dirs for part in file_path.parts):
                continue
                
            if file_path.is_file():
                # Só validar arquivos médicos ou relacionados ao projeto
                extension = file_path.suffix.lower()
                
                # Verificar se é um documento médico suportado
                if extension in SUPPORTED_EXTENSIONS:
                    arquivos_validados += 1
                    errors = validate_file(file_path)
                    if errors:
                        problemas.extend([(file_path, error) for error in errors])
                
                # Ou arquivos de projeto importantes
                elif file_path.name in ['patients.json', 'config.json', 'clinikondo.log']:
                    arquivos_validados += 1
                    # Validação específica para arquivos de configuração
                    if not file_path.exists():
                        problemas.append((file_path, "Arquivo de configuração não encontrado"))
        
        print(f"📁 {arquivos_validados} arquivo(s) de documento médico analisado(s)")
        
        if not problemas:
            print("✅ Estrutura válida! Nenhum problema encontrado.")
            return 0
        
        print(f"⚠️  {len(problemas)} problema(s) encontrado(s):")
        
        for file_path, error in problemas[:10]:  # Mostrar apenas os primeiros 10
            print(f"  ❌ {file_path.name}: {error}")
        
        if len(problemas) > 10:
            print(f"  ... e mais {len(problemas) - 10} problema(s)")
        
        if args.corrigir:
            print("\n🔧 Tentando corrigir problemas...")
            corrigidos = 0
            
            for file_path, error in problemas:
                if "caracteres perigosos" in error:
                    try:
                        # Renomear arquivo removendo caracteres perigosos
                        new_name = file_path.name
                        for char in ['<', '>', ':', '"', '|', '?', '*']:
                            new_name = new_name.replace(char, '_')
                        
                        new_path = file_path.parent / new_name
                        file_path.rename(new_path)
                        print(f"  ✅ Renomeado: {file_path.name} -> {new_name}")
                        corrigidos += 1
                    except Exception as e:
                        print(f"  ❌ Erro ao renomear {file_path}: {e}")
            
            print(f"\n✅ {corrigidos} problema(s) corrigido(s)")
        
        return 1 if problemas else 0
        
    except Exception as e:
        print(f"Erro ao validar estrutura: {e}")
        return 1


def cmd_mostrar_log(args) -> int:
    """Exibe logs do sistema."""
    try:
        # Procurar arquivos de log comuns
        log_paths = [
            Path.cwd() / "clinikondo.log",
            Path.home() / ".clinikondo" / "clinikondo.log",
            Path("/tmp/clinikondo.log"),
        ]
        
        log_file = None
        for path in log_paths:
            if path.exists():
                log_file = path
                break
        
        if not log_file:
            print("❌ Nenhum arquivo de log encontrado")
            print("Locais verificados:")
            for path in log_paths:
                print(f"  - {path}")
            return 1
        
        print(f"📋 Exibindo logs de: {log_file}")
        print(f"Nível mínimo: {args.nivel}")
        print("-" * 60)
        
        nivel_prioridade = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        min_prioridade = nivel_prioridade.get(args.nivel, 1)
        
        linhas_mostradas = 0
        with open(log_file, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
            
            # Mostrar últimas N linhas
            for linha in linhas[-args.linhas:]:
                linha = linha.strip()
                if not linha:
                    continue
                
                # Verificar nível do log
                mostrar = True
                for nivel, prioridade in nivel_prioridade.items():
                    if nivel in linha and prioridade < min_prioridade:
                        mostrar = False
                        break
                
                if mostrar:
                    print(linha)
                    linhas_mostradas += 1
        
        print("-" * 60)
        print(f"📊 {linhas_mostradas} linha(s) exibida(s)")
        return 0
        
    except Exception as e:
        print(f"Erro ao mostrar logs: {e}")
        return 1


def cmd_gerenciar_pacientes(args) -> int:
    """Gerencia cadastro de pacientes."""
    try:
        output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
        patient_file = output_dir / "patients.json"
        
        registry = PatientRegistry(patient_file if patient_file.exists() else patient_file)
        
        if not args.acao_paciente:
            print("❌ Especifique uma ação: adicionar, editar, remover, fusionar, detectar-duplicatas")
            return 1
        
        if args.acao_paciente == "adicionar":
            return cmd_adicionar_paciente(args, registry)
        elif args.acao_paciente == "editar":
            return cmd_editar_paciente(args, registry)
        elif args.acao_paciente == "remover":
            return cmd_remover_paciente(args, registry) 
        elif args.acao_paciente == "fusionar":
            return cmd_fusionar_pacientes(args, registry)
        elif args.acao_paciente == "detectar-duplicatas":
            return cmd_detectar_duplicatas_pacientes(args, registry)
        else:
            print(f"❌ Ação desconhecida: {args.acao_paciente}")
            return 1
            
    except Exception as e:
        print(f"Erro ao gerenciar pacientes: {e}")
        return 1


def cmd_adicionar_paciente(args, registry: PatientRegistry) -> int:
    """Adiciona novo paciente."""
    # Verificar se já existe paciente similar
    similar = registry.find_similar_patients(args.nome, threshold=0.85)
    if similar:
        print("⚠️  Pacientes similares encontrados:")
        for patient, similarity in similar[:3]:
            print(f"  - {patient.nome_completo} (similaridade: {similarity:.2f})")
        
        response = input("\nContinuar mesmo assim? (s/N): ").lower().strip()
        if response != 's':
            print("Operação cancelada.")
            return 0
    
    # Criar paciente
    patient = registry.ensure_patient(args.nome, create_if_missing=True)
    if not patient:
        print(f"❌ Erro ao criar paciente: {args.nome}")
        return 1
    
    # Adicionar informações opcionais
    if args.genero:
        patient.genero = args.genero
    
    if args.aliases:
        for alias in args.aliases:
            registry.add_alias(patient.slug_diretorio, alias)
    
    registry.save()
    print(f"✅ Paciente adicionado: {patient.nome_completo} (slug: {patient.slug_diretorio})")
    return 0


def cmd_editar_paciente(args, registry: PatientRegistry) -> int:
    """Edita paciente existente."""
    patient = registry.get_by_slug(args.slug)
    if not patient:
        print(f"❌ Paciente não encontrado: {args.slug}")
        return 1
    
    print(f"📝 Editando paciente: {patient.nome_completo}")
    
    # Atualizar campos
    updated = False
    
    if args.nome:
        old_name = patient.nome_completo
        patient.nome_completo = args.nome
        print(f"  Nome: {old_name} -> {args.nome}")
        updated = True
    
    if args.genero:
        old_genero = patient.genero or "Não definido"
        patient.genero = args.genero
        print(f"  Gênero: {old_genero} -> {args.genero}")
        updated = True
    
    if args.add_alias:
        for alias in args.add_alias:
            if registry.add_alias(patient.slug_diretorio, alias):
                print(f"  Alias adicionado: {alias}")
                updated = True
            else:
                print(f"  ❌ Erro ao adicionar alias: {alias}")
    
    if updated:
        registry.save()
        print("✅ Paciente atualizado com sucesso!")
    else:
        print("ℹ️  Nenhuma alteração realizada.")
    
    return 0


def cmd_remover_paciente(args, registry: PatientRegistry) -> int:
    """Remove paciente."""
    patient = registry.get_by_slug(args.slug)
    if not patient:
        print(f"❌ Paciente não encontrado: {args.slug}")
        return 1
    
    print(f"⚠️  Remover paciente: {patient.nome_completo}")
    print(f"   Slug: {patient.slug_diretorio}")
    print(f"   Aliases: {', '.join(patient.nomes_alternativos) if patient.nomes_alternativos else 'Nenhum'}")
    
    if not args.confirmar:
        response = input("\nConfirma remoção? (s/N): ").lower().strip()
        if response != 's':
            print("Operação cancelada.")
            return 0
    
    if registry.remove_patient(args.slug):
        registry.save()
        print("✅ Paciente removido com sucesso!")
        return 0
    else:
        print("❌ Erro ao remover paciente.")
        return 1


def cmd_fusionar_pacientes(args, registry: PatientRegistry) -> int:
    """Fusiona dois pacientes."""
    source = registry.get_by_slug(args.source_slug)
    target = registry.get_by_slug(args.target_slug)
    
    if not source:
        print(f"❌ Paciente origem não encontrado: {args.source_slug}")
        return 1
    
    if not target:
        print(f"❌ Paciente destino não encontrado: {args.target_slug}")
        return 1
    
    print(f"🔄 Fusionar pacientes:")
    print(f"   Origem: {source.nome_completo} (será removido)")
    print(f"   Destino: {target.nome_completo} (receberá aliases)")
    print(f"   Aliases origem: {', '.join(source.nomes_alternativos) if source.nomes_alternativos else 'Nenhum'}")
    
    response = input("\nConfirma fusão? (s/N): ").lower().strip()
    if response != 's':
        print("Operação cancelada.")
        return 0
    
    if registry.merge_patients(args.source_slug, args.target_slug):
        registry.save()
        print("✅ Pacientes fusionados com sucesso!")
        return 0
    else:
        print("❌ Erro ao fusionar pacientes.")
        return 1


def cmd_detectar_duplicatas_pacientes(args, registry: PatientRegistry) -> int:
    """Detecta possíveis duplicatas de pacientes."""
    duplicates = registry.detect_possible_duplicates(threshold=args.threshold)
    
    if not duplicates:
        print("✅ Nenhuma duplicata detectada!")
        return 0
    
    print(f"⚠️  {len(duplicates)} possível(is) duplicata(s) encontrada(s):")
    print("-" * 70)
    
    for i, (patient1, patient2, similarity) in enumerate(duplicates, 1):
        print(f"{i}. Similaridade: {similarity:.2f}")
        print(f"   A: {patient1.nome_completo} (slug: {patient1.slug_diretorio})")
        print(f"   B: {patient2.nome_completo} (slug: {patient2.slug_diretorio})")
        print(f"   Aliases A: {', '.join(patient1.nomes_alternativos) if patient1.nomes_alternativos else 'Nenhum'}")
        print(f"   Aliases B: {', '.join(patient2.nomes_alternativos) if patient2.nomes_alternativos else 'Nenhum'}")
        print()
    
    print(f"💡 Use 'gerenciar-pacientes fusionar {duplicates[0][0].slug_diretorio} {duplicates[0][1].slug_diretorio}' para fusionar")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal do CliniKondo - onde a magia da organização acontece! ✨"""
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Se nenhum comando foi especificado, assumir 'processar'
    if not args.comando:
        print("❌ Comando não especificado. Use --help para ver opções disponíveis.")
        print("\nComandos disponíveis:")
        print("  processar            - Organizar documentos médicos")  
        print("  listar-pacientes     - Listar pacientes registrados")
        print("  verificar-duplicatas - Verificar documentos duplicados")
        print("  relatorio-processamento - Gerar relatório de processamento")
        print("  validar-estrutura    - Validar estrutura de pastas")
        print("  mostrar-log         - Exibir logs do sistema")
        print("  gerenciar-pacientes  - Gerenciar cadastro de pacientes")
        return 1
    
    # Configurar logging padrão
    configure_logging("INFO")
    
    # Executar comando específico
    if args.comando == "processar":
        try:
            config = load_config_from_args(args)
            configure_logging(config.log_nivel)
            logging.getLogger(__name__).debug("Configuração carregada: %s", config)
            
            documents = run_pipeline(config)
            
            print("📄 RESULTADOS DO PROCESSAMENTO")
            print("=" * 40)
            
            for document in documents:
                destino_final = document.caminho_destino if document.caminho_destino else "(sem destino)"
                print(f"✅ {document.nome_arquivo_original} -> {destino_final}")
            
            if not documents:
                print("ℹ️  Nenhum documento processado.")
            else:
                print(f"\n🎉 {len(documents)} documento(s) processado(s) com sucesso!")
            
            return 0
            
        except Exception as exc:
            print(f"❌ Erro durante processamento: {exc}")
            return 2
    
    elif args.comando == "listar-pacientes":
        return cmd_listar_pacientes(args)
    
    elif args.comando == "verificar-duplicatas":
        return cmd_verificar_duplicatas(args)
    
    elif args.comando == "relatorio-processamento":
        return cmd_relatorio_processamento(args)
    
    elif args.comando == "validar-estrutura":
        return cmd_validar_estrutura(args)
    
    elif args.comando == "mostrar-log":
        return cmd_mostrar_log(args)
    
    elif args.comando == "gerenciar-pacientes":
        return cmd_gerenciar_pacientes(args)
    
    else:
        print(f"❌ Comando desconhecido: {args.comando}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

