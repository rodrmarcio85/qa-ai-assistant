# 🧪 QA AI Assistant: Análise de Requisitos & Gerador de Testes (BDD)

O **QA AI Assistant** é uma aplicação web voltada para Engenharia de Requisitos e Quality Assurance (Shift-Left Testing). A solução utiliza a API do Google Gemini para identificar ambiguidades e regras ausentes em Histórias de Usuário antes do início do desenvolvimento, além de mapear automaticamente cenários de teste funcionais no formato BDD (Gherkin).

---

## 📌 Principais Funcionalidades

- **Análise Prévia de Requisitos (Shift-Left Testing):** Mapeamento automático de regras ausentes, ambiguidades e riscos de negócio antes da fase de desenvolvimento.
- **Geração Automática de BDD:** Criação de cenários cobrindo Caminho Feliz, Exceções/Erros e Validações de Borda.
- **Análise Multimodal (UX/UI):** Suporte ao envio de telas e wireframes de UX (`.png`, `.jpg`) para validação visual conjunta com o requisito textual.
- **Edição Interativa (`st.data_editor`):** Tabela editável diretamente na interface, permitindo ajustar os cenários gerados antes do download.
- **Exportação Formatada:** Download dos cenários em Excel (`.xlsx`) estilizado via `openpyxl` e relatório completo em Markdown (`.md`).
- **Histórico Persistente:** Armazenamento local de análises anteriores (`history.json`) com recarregamento rápido e exclusão individual.
- **Execução Ultrarrápida (< 10s):** Processamento otimizado para textos extensos com progresso visual em tempo real (`st.status`).

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Interface Web:** Streamlit
- **Motor de IA:** Google Gemini API (`gemini-3.5-flash-lite`)
- **Processamento de Dados & Exportação:** Pandas & OpenPyXL
- **Processamento Multimodal de Imagens:** Pillow (PIL)
- **Testes Automatizados:** Pytest

---

## 🚀 Como Executar o Projeto

### 1. Clonar o Repositório e Criar o Ambiente Virtual

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

python -m venv venv
```

Ative o ambiente virtual:
- **Windows:** `venv\Scripts\activate`
- **Linux/Mac:** `source venv/bin/activate`

### 2. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto e insira a sua chave da API do Gemini:

```env
GEMINI_API_KEY=sua_chave_aqui
```

### 4. Iniciar a Aplicação

```bash
streamlit run app.py
```

---

## 🧪 Testes Automatizados

A aplicação conta com uma suíte de testes unitários para validar a estrutura do parser e a geração dos arquivos de exportação.

Para rodar a suíte de testes:

```bash
pytest
```

---

## 🔮 Roadmap de Evolução

- [ ] **Integração com Jira e Azure DevOps:** Importação automática de requisitos e exportação dos cenários gerados.
- [ ] **Exportação para Automação:** Geração de scripts base para Robot Framework e Cypress a partir do BDD.
- [ ] **Suporte Multi-idiomas:** Opção para alternar a saída do Gherkin entre Português e Inglês.
- [ ] **Métricas de Cobertura:** Painel visual indicando a distribuição dos testes por tipo de cenário.

---

## 📄 Licença

Este projeto é de uso livre para fins educacionais, demonstrativos e de portfólio profissional.