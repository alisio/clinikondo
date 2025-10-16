"""Interface de linha de comando do Medifolder."""

from __future__ import annotations

import argparse
import logging
import sys

from . import load_config_from_args, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classificador automatizado de documentos médicos familiares."
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Diretório de entrada com os documentos a processar.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Diretório base onde os documentos serão organizados.",
    )
    parser.add_argument("--model", help="Modelo LLM a ser utilizado (ex: gpt-4).")
    parser.add_argument("--api-key", help="Chave de API para o provedor LLM.")
    parser.add_argument("--api-base", help="Endpoint alternativo para a API LLM.")
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperatura da inferência LLM (0-2).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Quantidade máxima de tokens a serem retornados pelo LLM.",
    )
    parser.add_argument(
        "--prompt-template",
        help="Caminho para o template de prompt a ser utilizado.",
    )
    parser.add_argument(
        "--log-level",
        help="Nível de log (debug, info, warning, error).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa o pipeline sem mover os arquivos.",
    )
    parser.add_argument(
        "--match-patient",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Habilita ou desabilita a correspondência automática de pacientes.",
    )
    parser.add_argument(
        "--create-patient",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Cria novos pacientes automaticamente quando não houver correspondência.",
    )
    parser.add_argument(
        "--move-to-shared",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Move documentos sem paciente identificado para a pasta Compartilhado.",
    )
    parser.add_argument(
        "--copy-on-error",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Copia documentos com erro para a pasta de falhas.",
    )
    parser.add_argument(
        "--mover",
        action="store_true",
        help="Move arquivos originais (deletando-os) em vez de copiá-los (comportamento padrão é preservar originais).",
    )
    return parser


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config_from_args(args)
    except Exception as exc:
        parser.error(str(exc))
        return 2
    configure_logging(config.log_nivel)
    logging.getLogger(__name__).debug("Configuração carregada: %s", config)
    documents = run_pipeline(config)
    for document in documents:
        destino_final = document.caminho_destino if document.caminho_destino else "(sem destino)"
        print(f"{document.nome_arquivo_original} -> {destino_final}")
    if not documents:
        print("Nenhum documento processado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

