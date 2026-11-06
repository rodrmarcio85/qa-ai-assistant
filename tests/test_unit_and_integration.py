import os
import json
import io
import pytest
import pandas as pd
import openpyxl
from unittest.mock import MagicMock, patch

from app import (
    parse_markdown_response,
    generate_excel_download,
    load_history,
    save_to_history,
    delete_from_history,
    generate_qa_analysis,
    HISTORY_FILE
)


@pytest.fixture(autouse=True)
def setup_teardown_history():
    """Garante ambiente limpo limpando o arquivo history.json antes e depois de cada teste."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    yield
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)


# --- 1. TESTES POSITIVOS (CAMINHO FELIZ) ---

def test_parse_markdown_response_success():
    """Valida se o parser extrai ambiguidades e cenários BDD corretamente."""
    raw_markdown = """
---AMBIGUIDADES---
- Regra de frete não especificada.
- Falta definição de timeout.

---CENARIO---
ID: CT01
TITULO: Pagamento aprovado
TIPO: Caminho Feliz
BDD:
Dado que estou na tela de pagamento
Quando preencho dados válidos
Então o pagamento é aprovado

---CENARIO---
ID: CT02
TITULO: Valor abaixo do mínimo
TIPO: Borda
BDD:
Dado um valor de R$ 10,00
Quando tento pagar
Então o sistema exibe erro
"""
    result = parse_markdown_response(raw_markdown)
    assert len(result["ambiguities"]) == 2
    assert len(result["test_scenarios"]) == 2
    assert result["test_scenarios"][0]["id"] == "CT01"
    assert result["test_scenarios"][0]["type"] == "Caminho Feliz"
    assert result["test_scenarios"][1]["type"] == "Borda"


def test_generate_excel_download_structure():
    """Valida geração de buffer Excel com formatação, cabeçalhos e ordenação corretas."""
    mock_df = pd.DataFrame([
        {"id": "CT01", "title": "Teste Login", "gherkin": "Dado... Quando... Então...", "type": "Caminho Feliz"}
    ])
    excel_bytes = generate_excel_download(mock_df)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert "Casos de Teste" in wb.sheetnames
    sheet = wb["Casos de Teste"]

    headers = [sheet.cell(row=1, column=col).value for col in range(1, 5)]
    assert headers == ["ID", "Título", "BDD (Gherkin)", "Tipo"]
    assert sheet.cell(row=2, column=1).value == "CT01"


def test_history_lifecycle():
    """Valida criação, leitura e exclusão no arquivo de histórico JSON."""
    mock_req = "História de Usuário de Teste de Integração"
    mock_result = {"ambiguities": ["Dúvida 1"], "test_scenarios": []}

    save_to_history(mock_req, mock_result, has_image=True)
    history = load_history()

    assert len(history) == 1
    assert "🖼️ [Com Imagem]" in history[0]["preview"]

    item_id = history[0]["id"]
    delete_from_history(item_id)
    updated_history = load_history()

    assert len(updated_history) == 0


# --- 2. TESTES NEGATIVOS E TRATAMENTO DE EXCEÇÕES ---

def test_parse_markdown_response_empty_or_malformed():
    """Valida se o parser trata textos sem os separadores esperados sem quebrar."""
    raw_markdown = "Texto simples sem separadores válidos de markdown."
    result = parse_markdown_response(raw_markdown)

    assert result["ambiguities"] == []
    assert result["test_scenarios"] == []


@patch("google.generativeai.GenerativeModel")
def test_generate_qa_analysis_api_failure(mock_model):
    """Valida se exceções de rede/API sobem corretamente para tratamento da UI."""
    instance = mock_model.return_value
    instance.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")

    with pytest.raises(Exception) as exc_info:
        generate_qa_analysis("Requisito válido para disparo de erro")

    assert "429" in str(exc_info.value)


def test_load_history_corrupted_json():
    """Valida se o carregamento do histórico lida graciosamente com JSON corrompido."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("{ json_invalido: true ")

    history = load_history()
    assert history == []