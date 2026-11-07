import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"

def test_app_title_and_header(page: Page):
    """Valida a renderização do título da aplicação no Streamlit."""
    page.goto(BASE_URL)
    expect(page.get_by_text("QA AI Assistant: Análise de Requisitos & Gerador de Testes")).to_be_visible()

def test_clear_button_resets_fields(page: Page):
    """Valida a funcionalidade do botão 'Nova Análise'."""
    page.goto(BASE_URL)
    
    # Preenche o campo primeiro
    textarea = page.locator("textarea").first
    textarea.fill("História de Usuário de Teste")
    
    # Clica no botão Nova Análise
    page.get_by_role("button", name="Nova Análise").click()
    page.wait_for_timeout(1000)
    
    # Garante que o campo limpou
    expect(textarea).to_have_value("")

def test_warning_alert_when_submitting_empty(page: Page):
    """Valida se o alerta de erro é exibido ao submeter sem texto."""
    page.goto(BASE_URL)
    
    # Limpa qualquer texto se houver
    textarea = page.locator("textarea").first
    textarea.fill("")
    
    # Clica no botão de análise
    page.get_by_role("button", name="Analisar Requisito e Gerar Testes").click()
    page.wait_for_timeout(1000)
    
    # Verifica a mensagem de validação
    expect(page.get_by_text("Por favor, insira uma História de Usuário ou Requisito para realizar a análise.")).to_be_visible()