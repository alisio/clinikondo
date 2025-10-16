from __future__ import annotations

from datetime import date
from pathlib import Path

from clinikondo import Config, run_pipeline


def build_config(input_dir: Path, output_dir: Path, **overrides):
    config = Config(
        input_dir=input_dir,
        output_dir=output_dir,
        modelo_llm="gpt-4",
        openai_api_key=None,
        openai_api_base=None,
        llm_temperature=0.2,
        llm_max_tokens=512,
        prompt_template_path=None,
        match_nome_paciente_auto=True,
        criar_paciente_sem_match=True,
        mover_para_compartilhado_sem_match=False,
        executar_copia_apos_erro=False,
        log_nivel="warning",
        dry_run=False,
        estrategia_extracao="heuristico",
    )
    for key, value in overrides.items():
        setattr(config, key, value)
    config.validar()
    return config


def test_rule_based_processing_creates_expected_structure(tmp_path):
    input_dir = tmp_path / "entrada"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    output_dir.mkdir()

    texto = (
        "Paciente: José da Silva\n"
        "Data: 12/03/2023\n"
        "Exame de sangue realizado em clínica de cardiologia."
    )
    arquivo = input_dir / "exame_lab.txt"
    arquivo.write_text(texto, encoding="utf-8")

    config = build_config(input_dir, output_dir)
    documentos = run_pipeline(config)

    assert len(documentos) == 1
    documento = documentos[0]
    assert documento.nome_paciente_inferido == "José da Silva"
    assert documento.data_documento == date(2023, 3, 12)
    assert documento.tipo_documento == "exame"
    assert documento.especialidade in {"cardiologia", "clinica_geral"}
    assert documento.caminho_destino is not None
    assert documento.caminho_destino.exists()
    # Verifica estrutura final: saida/jose_da_silva/exames/arquivo
    partes = documento.caminho_destino.parts
    assert "jose_da_silva" in partes
    assert "exames" in partes
    assert documento.nome_arquivo_final is not None
    assert documento.nome_arquivo_final.startswith("2023-03-jose_da_silva-exame")


def test_document_without_patient_goes_to_shared_when_configured(tmp_path):
    input_dir = tmp_path / "entrada"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    output_dir.mkdir()

    texto = "Relatório anual de vacinação realizado em 2022-11-05."
    arquivo = input_dir / "relatorio.txt"
    arquivo.write_text(texto, encoding="utf-8")

    config = build_config(
        input_dir,
        output_dir,
        match_nome_paciente_auto=False,
        mover_para_compartilhado_sem_match=True,
    )
    documentos = run_pipeline(config)

    assert len(documentos) == 1
    documento = documentos[0]
    assert documento.classificado_como_compartilhado is True
    assert documento.caminho_destino is not None
    destino = documento.caminho_destino
    assert "compartilhado" in destino.parts
    assert destino.exists()
