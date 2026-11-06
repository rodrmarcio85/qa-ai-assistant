import subprocess
import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="module", autouse=True)
def run_streamlit_server():
    """Inicia o servidor do Streamlit automaticamente antes dos testes E2E e encerra ao final."""
    process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.headless=true", "--server.port=8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    yield
    process.terminate()
    process.wait()


def test_app_title_and_elements_render(page: Page):
    """Valida a renderização dos componentes principais da interface."""
    page.goto(BASE_URL)
    expect(page.locator("h1")).to_contain_text("QA AI Assistant")
    btn_analyze = page.get_by_role("button", name="Analisar Requisito e Gerar Testes")
    expect(btn_analyze).to_be_visible()


def test_validation_short_requirement_warning(page: Page):
    """Valida se a mensagem de aviso é exibida ao inserir menos de 30 caracteres."""
    page.goto(BASE_URL)
    
    textarea = page.locator("textarea").first
    textarea.fill("Texto curto")
    
    # Clica no botão e aguarda o elemento de alerta na tela
    page.get_by_role("button", name="Analisar Requisito e Gerar Testes").click()
    
    # Usa o seletor por role alert capturado no log do Playwright
    warning_box = page.get_by_role("alert")
    expect(warning_box).to_contain_text("Requisito muito curto")


def test_clear_button_resets_fields(page: Page):
    """Valida a funcionalidade do botão 'Nova Análise'."""
    page.goto(BASE_URL)
    
    # Clica no botão Nova Análise
    page.get_by_role("button", name="Nova Análise").click()
    
    # Aguarda o websocket do Streamlit reprocessar a página
    page.wait_for_timeout(1500)
    
    textarea = page.locator("textarea").first
    expect(textarea).to_have_value("")