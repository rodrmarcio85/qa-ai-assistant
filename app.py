import os
import json
import io
import re
import time
from datetime import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da página Streamlit
st.set_page_config(
    page_title="QA Requirements & Test Generator AI",
    page_icon="🧪",
    layout="wide"
)

HISTORY_FILE = "history.json"

# --- FUNÇÕES DE HISTÓRICO PERSISTENTE ---
def load_history():
    """Carrega o histórico salvo do arquivo JSON local."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_to_history(requirement_text: str, analysis_result: dict, has_image: bool = False):
    """Salva uma nova análise no histórico local."""
    history = load_history()
    new_entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "preview": ("🖼️ [Com Imagem] " if has_image else "") + requirement_text[:40].replace("\n", " ") + "...",
        "requirement_text": requirement_text,
        "result": analysis_result
    }
    history.insert(0, new_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def delete_from_history(item_id: str):
    """Remove um item específico do histórico local."""
    history = load_history()
    updated_history = [item for item in history if item["id"] != item_id]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_history, f, ensure_ascii=False, indent=2)

# Inicialização da API Key
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

if api_key:
    genai.configure(api_key=api_key)

# Estado da Sessão
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "user_requirement_text" not in st.session_state:
    st.session_state["user_requirement_text"] = """História de Usuário:
Como cliente cadastrado no e-commerce, quero realizar o pagamento da minha compra utilizando cartão de crédito para concluir meu pedido.

Regras de Negócio:
- Deve aceitar bandeiras Visa e Mastercard.
- Valor mínimo do pedido para cartão de crédito é R$ 20,00.
- O sistema deve validar o código de segurança (CVV) e data de validade.
- Se o pagamento for aprovado, o pedido muda para o status "Aguardando Envio" e dispara e-mail de confirmação.
"""

SYSTEM_INSTRUCTION = """
Você é um Especialista em Quality Assurance (QA) e Engenharia de Requisitos focado em alta produtividade.
Análise a História de Usuário (e o layout de UX anexado, se houver) de forma direta e ágil.
Retorne a resposta ESTRITAMENTE no seguinte formato Markdown:

---AMBIGUIDADES---
- Ponto 1...
- Ponto 2...

---CENARIO---
ID: CT01
TITULO: Pagamento aprovado via Visa
TIPO: Caminho Feliz
BDD:
Dado que o cliente está na tela de pagamento
Quando preenche dados válidos do cartão Visa acima de R$ 20,00
Então o pedido é finalizado com status "Aguardando Envio"

---CENARIO---
ID: CT02
TITULO: Tentativa abaixo do valor mínimo
TIPO: Borda
BDD:
Dado que o cliente selecionou o valor de R$ 19,99
Quando tenta finalizar via cartão de crédito
Então o sistema exibe mensagem de valor mínimo insuficiente
"""

def parse_markdown_response(text: str) -> dict:
    """Converte o texto retornado pela IA em uma estrutura limpa em Python."""
    ambiguities = []
    scenarios = []

    amb_match = re.search(r"---AMBIGUIDADES---(.*?)---CENARIO---", text, re.DOTALL)
    if amb_match:
        amb_text = amb_match.group(1).strip()
        ambiguities = [line.strip("- ").strip() for line in amb_text.split("\n") if line.strip().startswith("-")]

    raw_scenarios = text.split("---CENARIO---")[1:]
    for raw in raw_scenarios:
        if not raw.strip():
            continue
        
        id_m = re.search(r"ID:\s*(.+)", raw)
        title_m = re.search(r"TITULO:\s*(.+)", raw)
        type_m = re.search(r"TIPO:\s*(.+)", raw)
        bdd_m = re.search(r"BDD:\s*(.+)", raw, re.DOTALL)

        sc_id = id_m.group(1).strip() if id_m else "CT01"
        sc_title = title_m.group(1).strip() if title_m else "Cenário de Teste"
        sc_type = type_m.group(1).strip() if type_m else "Geral"
        sc_bdd = bdd_m.group(1).strip() if bdd_m else "Gherkin não gerado."

        scenarios.append({
            "id": sc_id,
            "title": sc_title,
            "type": sc_type,
            "gherkin": sc_bdd
        })

    return {
        "ambiguities": ambiguities,
        "test_scenarios": scenarios
    }

def get_available_gemini_model():
    preferred_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
    try:
        available = [m.name.replace("models/", "") for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        for pref in preferred_models:
            if pref in available:
                return pref
        for m in available:
            if "gemini" in m:
                return m
    except Exception:
        pass
    return "gemini-3.5-flash-lite"

def generate_qa_analysis(requirement_text: str, uploaded_image=None):
    selected_model_name = get_available_gemini_model()
    model = genai.GenerativeModel(
        model_name=selected_model_name,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 2048
        }
    )
    
    contents = []
    if uploaded_image:
        image = Image.open(uploaded_image)
        contents.append(image)
        prompt = f"Analise o layout anexado e o seguinte requisito funcional:\n\n{requirement_text}"
    else:
        prompt = f"Analise o seguinte requisito funcional:\n\n{requirement_text}"
        
    contents.append(prompt)
    
    response = model.generate_content(contents)
    return parse_markdown_response(response.text)

def generate_excel_download(df_scenarios: pd.DataFrame) -> bytes:
    cols_order = ['id', 'title', 'gherkin', 'type']
    existing_cols = [c for c in cols_order if c in df_scenarios.columns]
    df_export = df_scenarios[existing_cols].copy()
    
    df_export = df_export.rename(columns={'id': 'ID', 'title': 'Título', 'gherkin': 'BDD (Gherkin)', 'type': 'Tipo'})

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Casos de Teste')
        worksheet = writer.sheets['Casos de Teste']
        
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
        
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        body_font = Font(name="Calibri", size=10)
        top_left_align = Alignment(vertical="top", horizontal="left", wrap_text=True)
        center_align = Alignment(vertical="top", horizontal="center")
        thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'), top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))

        for col_idx in range(1, len(df_export.columns) + 1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center", horizontal="center")
        
        col_widths = {'A': 12, 'B': 35, 'C': 65, 'D': 20}
        for col_letter, width in col_widths.items():
            worksheet.column_dimensions[col_letter].width = width

        for row in range(2, len(df_export) + 2):
            worksheet.cell(row=row, column=1).alignment = center_align
            worksheet.cell(row=row, column=1).font = Font(name="Calibri", size=10, bold=True)
            worksheet.cell(row=row, column=1).border = thin_border
            
            worksheet.cell(row=row, column=2).alignment = top_left_align
            worksheet.cell(row=row, column=2).font = body_font
            worksheet.cell(row=row, column=2).border = thin_border
            
            worksheet.cell(row=row, column=3).alignment = top_left_align
            worksheet.cell(row=row, column=3).font = Font(name="Consolas", size=9)
            worksheet.cell(row=row, column=3).border = thin_border
            
            worksheet.cell(row=row, column=4).alignment = center_align
            worksheet.cell(row=row, column=4).font = body_font
            worksheet.cell(row=row, column=4).border = thin_border

    return output.getvalue()

def clear_analysis():
    st.session_state["analysis_result"] = None
    st.session_state["user_requirement_text"] = ""
    if "user_requirement_input" in st.session_state:
        st.session_state["user_requirement_input"] = ""

def load_from_history_item(item):
    st.session_state["user_requirement_text"] = item["requirement_text"]
    st.session_state["analysis_result"] = item["result"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("📌 Sobre o Projeto")
    st.markdown("Esta aplicação utiliza IA Generativa Multimodal para análise prévia de requisitos, layouts de UX e geração de BDD.")
    st.divider()
    st.header("🕒 Histórico de Análises")
    
    history_items = load_history()
    if history_items:
        for item in history_items:
            col_hist_btn, col_hist_del = st.columns([5, 1])
            with col_hist_btn:
                button_label = f"📅 {item['timestamp']}\n📝 {item['preview']}"
                if st.button(button_label, key=f"hist_{item['id']}", use_container_width=True):
                    load_from_history_item(item)
                    st.rerun()
            with col_hist_del:
                if st.button("🗑️", key=f"del_{item['id']}", help="Excluir do histórico"):
                    delete_from_history(item["id"])
                    if st.session_state.get("analysis_result") == item["result"]:
                        clear_analysis()
                    st.rerun()
    else:
        st.info("Nenhuma análise salva no histórico.")

# --- INTERFACE PRINCIPAL ---
st.title("🧪 QA AI Assistant: Análise de Requisitos & Gerador de Testes")
st.caption("Ferramenta de apoio a desenvolvimento e qualidade para otimização do ciclo de software (SDLC).")

if not api_key:
    st.warning("⚠️ Chave da API do Gemini não encontrada. Configure a variável GEMINI_API_KEY no arquivo .env.")

col_text, col_img = st.columns([2, 1])

with col_text:
    user_requirement = st.text_area(
        "Insira a História de Usuário / Requisito Funcional (Suporta textos longos):",
        value=st.session_state["user_requirement_text"],
        height=220,
        key="user_requirement_input"
    )
    st.session_state["user_requirement_text"] = user_requirement

with col_img:
    st.markdown("**🖼️ Anexar Tela / Wireframe de UX (Opcional):**")
    uploaded_ux_image = st.file_uploader(
        "Selecione uma imagem do layout:",
        type=["png", "jpg", "jpeg"],
        help="A IA vai analisar o layout visual junto com as regras de negócio."
    )
    if uploaded_ux_image:
        st.image(uploaded_ux_image, caption="Layout de UX anexado", use_container_width=True)

col_action1, col_action2 = st.columns([3, 1])
with col_action1:
    btn_analyze = st.button("🚀 Analisar Requisito e Gerar Testes", type="primary", use_container_width=True)
with col_action2:
    st.button("🔄 Nova Análise", on_click=clear_analysis, use_container_width=True)

if btn_analyze:
    text_content = user_requirement.strip()
    
    if not text_content:
        st.error("⚠️ O campo de requisito não pode estar vazio.")
    elif len(text_content) < 30:
        st.warning("⚠️ Requisito muito curto! Forneça uma descrição com pelo menos 30 caracteres para mapear os cenários adequadamente.")
    elif not api_key:
        st.error("🔑 Chave da API não configurada. Verifique o arquivo .env.")
    else:
        start_time = time.time()
        with st.status("⚡ Processando análise e mapeando regras de negócio...", expanded=True) as status:
            try:
                st.write("🔍 Identificando ambiguidades e validando regras de interface...")
                res = generate_qa_analysis(user_requirement, uploaded_ux_image)
                
                st.session_state["analysis_result"] = res
                save_to_history(user_requirement, res, has_image=(uploaded_ux_image is not None))
                
                elapsed = round(time.time() - start_time, 2)
                status.update(label=f"✅ Análise concluída com sucesso em apenas {elapsed} segundos!", state="complete", expanded=False)
                st.rerun()
            except Exception as e:
                status.update(label="❌ Erro no processamento", state="error", expanded=True)
                err_msg = str(e)
                if "API_KEY_INVALID" in err_msg or "403" in err_msg:
                    st.error("🔒 Chave de API inválida ou sem permissão.")
                elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                    st.error("⏳ Limite de requisições excedido. Aguarde alguns segundos.")
                else:
                    st.error(f"Ocorreu um erro durante a execução: {e}")

result = st.session_state.get("analysis_result")

if result:
    st.divider()
    st.subheader("🔍 1. Pontos de Atenção & Ambiguidades no Requisito")
    ambiguities = result.get("ambiguities", [])
    if ambiguities:
        for idx, amb in enumerate(ambiguities, 1):
            st.warning(f"**Ponto {idx}:** {amb}")
    else:
        st.success("Nenhuma ambiguidade crítica detectada no texto fornecido.")
    
    st.subheader("📋 2. Casos de Teste Mapeados (BDD)")
    scenarios = result.get("test_scenarios", [])
    df_scenarios = pd.DataFrame(scenarios)
    
    tab1, tab2 = st.tabs(["Visão em Cards", "Tabela de Dados (Editável)"])
    
    with tab1:
        for sc in scenarios:
            sc_id = sc.get('id', 'N/A')
            sc_title = sc.get('title', 'Sem título')
            sc_type = sc.get('type', 'Geral')
            sc_gherkin = sc.get('gherkin', 'Gherkin não gerado.')
            
            with st.expander(f"**[{sc_id}] {sc_title}** — *({sc_type})*"):
                st.code(str(sc_gherkin), language="gherkin")
    
    with tab2:
        st.info("💡 **Dica de Produtividade:** Você pode dar um duplo clique em qualquer célula abaixo para editar os cenários. Os downloads abaixo serão atualizados com as suas alterações!")
        
        # Tabela interativa com st.data_editor
        edited_df = st.data_editor(
            df_scenarios,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "id": st.column_config.TextColumn("ID", help="Identificador único do caso de teste", width="small"),
                "title": st.column_config.TextColumn("Título", help="Resumo do teste", width="medium"),
                "gherkin": st.column_config.TextColumn("BDD (Gherkin)", help="Instruções em formato Gherkin", width="large"),
                "type": st.column_config.SelectboxColumn("Tipo", help="Categoria do cenário", options=["Caminho Feliz", "Exceção", "Borda", "Geral"], width="small")
            },
            key="scenarios_editor"
        )
    
    st.subheader("💾 3. Exportação")
    col1, col2 = st.columns(2)
    
    # Gera o Excel usando o DataFrame editado pelo usuário
    excel_bytes = generate_excel_download(edited_df)
    col1.download_button(
        label="📊 Baixar Casos de Teste (.XLSX)",
        data=excel_bytes,
        file_name="casos_de_teste_qa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    # Gera o Markdown usando os dados editados pelo usuário
    md_content = "# Relatório de Análise e Casos de Teste\n\n## Ambiguidades Mapeadas\n"
    for amb in ambiguities:
        md_content += f"- {amb}\n"
    md_content += "\n## Casos de Teste (BDD)\n"
    
    # Itera sobre o DataFrame editado
    for _, row in edited_df.iterrows():
        md_content += f"### [{row.get('id', 'N/A')}] {row.get('title', 'Sem título')} ({row.get('type', 'Geral')})\n```gherkin\n{row.get('gherkin', '')}\n```\n\n"
    
    col2.download_button(
        label="📥 Baixar Relatório Completo (.MD)",
        data=md_content.encode('utf-8'),
        file_name="relatorio_qa.md",
        mime="text/markdown",
        use_container_width=True
    )