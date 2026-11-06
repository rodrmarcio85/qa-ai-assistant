import os
import sys
import io
import pytest
import pandas as pd
import openpyxl

# Injeta a pasta raiz do projeto no sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import parse_markdown_response, generate_excel_download


def test_parse_markdown_response_valid():
    """Valida se a função de parser converte o Markdown da IA corretamente em dicionário."""
    mock_markdown = """
---AMBIGUIDADES---
- Requisito não especifica o comportamento para bandeira Elo.
- Não há definição de limite de tentativas.

---CENARIO---
ID: CT01
TITULO: Pagamento aprovado via Visa
TIPO: Caminho Feliz
BDD:
Dado que o cliente está na tela de checkout
Quando preenche os dados do cartão Visa
Então o pagamento é processado com sucesso

---CENARIO---
ID: CT02
TITULO: Valor abaixo do mínimo
TIPO: Borda
BDD:
Dado que o valor é R$ 10,00
Quando tenta finalizar
Então o sistema bloqueia
"""
    result = parse_markdown_response(mock_markdown)

    assert "ambiguities" in result
    assert "test_scenarios" in result
    assert len(result["ambiguities"]) == 2
    assert len(result["test_scenarios"]) == 2
    assert result["test_scenarios"][0]["id"] == "CT01"
    assert result["test_scenarios"][0]["type"] == "Caminho Feliz"
    assert "Dado que o cliente" in result["test_scenarios"][0]["gherkin"]


def test_generate_excel_download():
    """Valida se a geração do buffer do Excel em memória gera um arquivo válido com os cabeçalhos corretos."""
    mock_data = [{
        "id": "CT01",
        "title": "Teste de Exemplo",
        "gherkin": "Dado algo\nQuando faço algo\nEntão acontece algo",
        "type": "Caminho Feliz",
    }]
    df = pd.DataFrame(mock_data)
    excel_bytes = generate_excel_download(df)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    # Valida se o Excel gerado pode ser lido pelo openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    sheet = wb["Casos de Teste"]

    headers = [sheet.cell(row=1, column=i).value for i in range(1, 5)]
    assert headers == ["ID", "Título", "BDD (Gherkin)", "Tipo"]
    assert sheet.cell(row=2, column=1).value == "CT01"