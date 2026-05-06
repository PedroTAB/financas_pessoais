# 🔬 Finanças Pessoais — Documentação Técnica para Desenvolvedores

> **Versão:** 2.0  
> **Data:** Maio 2026  
> **Audience:** Desenvolvedores e mantenedores

---

## 📖 Índice

1. [Setup de Desenvolvimento](#setup-de-desenvolvimento)
2. [Entendendo o Fluxo de Dados](#entendendo-o-fluxo-de-dados)
3. [Padrões de Código](#padrões-de-código)
4. [Adicionando uma Nova View](#adicionando-uma-nova-view)
5. [Estendendo Storage](#estendendo-storage)
6. [Trabalhando com Autenticação](#trabalhando-com-autenticação)
7. [Debugging e Testes](#debugging-e-testes)
8. [Deploy](#deploy)
9. [Estrutura de Commits](#estrutura-de-commits)

---

## 🛠️ Setup de Desenvolvimento

### Pré-requisitos

- Python 3.9+
- Git
- VS Code (recomendado)
- Conta Google (para Sheets)

### Clonar e configurar

```bash
# 1. Clonar
git clone <repo-url>
cd financas_pessoais

# 2. Virtual env
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# 3. Instalar dependências
pip install -r requirements.txt
pip install pytest pytest-cov black flake8  # Dev dependencies

# 4. Criar .env local
cp .env.example .env

# 5. Configurar secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar com suas credenciais Google

# 6. Rodar local
streamlit run app.py
```

### Estrutura de pasta recomendada

```
~/projects/
└── financas_pessoais/
    ├── venv/                 ← Virtual environment
    ├── .git/                 ← Git repository
    ├── app.py
    ├── requirements.txt
    └── [outros arquivos]
```

### Pre-commit hooks (opcional mas recomendado)

```bash
pip install pre-commit

# Criar .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]
EOF

pre-commit install
```

---

## 🔄 Entendendo o Fluxo de Dados

### Fluxo Completo de uma Transação

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Usuário acessa app.py                                     │
├──────────────────────────────────────────────────────────────┤
│   app.py → require_perfil() → auth.py (validação)            │
│   ✓ Session state recebe username                            │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 2. Sidebar renderizada (app.py)                              │
├──────────────────────────────────────────────────────────────┤
│   Logo, menu de navegação, footer com avatar                 │
│   st.session_state.aba controlada por botões                 │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 3. View selecionada chamada com username (app.py)            │
├──────────────────────────────────────────────────────────────┤
│   if aba == "Lancamentos":                                   │
│       show_lancamentos(username)  ← views/lancamentos.py     │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 4. View carrega dados via storage.py (functools.partial)     │
├──────────────────────────────────────────────────────────────┤
│   get_lancamentos = partial(st_get_lancamentos, username)    │
│   df_all = get_lancamentos()  ← Chamada sem username         │
│   storage.py → Google Sheets API → DataFrame                 │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 5. Dados transformados e exibidos (view)                     │
├──────────────────────────────────────────────────────────────┤
│   Aplicar filtros, agregações, formatar com utils/helpers    │
│   Renderizar tabelas, gráficos, formulários                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 6. Usuário interage (preenche form, clica botão, etc.)       │
├──────────────────────────────────────────────────────────────┤
│   st.form() captura input → st.session_state atualizado      │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 7. Validação e persistência (storage.py)                     │
├──────────────────────────────────────────────────────────────┤
│   add_lancamento(username, categoria, valor, ...)            │
│   → _wsl().append_row([...]) → Google Sheets                 │
│   → _cached_records.clear() (invalida cache)                 │
│   → Mensagem de sucesso ou erro                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│ 8. st.rerun() → Volta para passo 4                           │
├──────────────────────────────────────────────────────────────┤
│   Cache foi invalidado → Nova leitura do Google Sheets       │
│   Dados atualizados aparecem na view                         │
└──────────────────────────────────────────────────────────────┘
```

### Ciclo de Cache

```
┌─────────────────────────────────────────────────────┐
│ @st.cache_data(ttl=60)                              │
│ def _cached_records(sheet_kind: str)                │
└─────────────────────┬───────────────────────────────┘
                      │
        Chamada 1 (t=0s)
                      │
        ┌─────────────▼─────────────┐
        │ Lê Google Sheets          │
        │ Cria DataFrame            │
        │ Salva em cache (TTL=60s)  │
        └─────────────┬─────────────┘
                      │
    ┌──────────────────┴──────────────────┐
    │                                     │
Chamada 2 (t=10s)                  Chamada 3 (t=70s)
    │                                     │
    ├─ Retorna do cache              ├─ Cache expirou
    │  (sem I/O)                     │  Lê Google Sheets novamente
    │                                     │
    └─ Instantâneo                    └─ Novo período de 60s
```

**Invalidação manual:**

```python
# Ao salvar/editar/deletar:
_cached_records.clear()  # Força nova leitura na próxima chamada
```

---

## 📏 Padrões de Código

### 1. Naming Conventions

**Python:**
```python
# Classes: PascalCase
class LancamentoHandler:
    pass

# Funções públicas: snake_case
def get_lancamentos(username: str) -> pd.DataFrame:
    pass

# Funções privadas: _snake_case (prefixo underscore)
def _parse_linha_sheets(row: list) -> dict:
    pass

# Constantes: UPPER_SNAKE_CASE
LIMITES_INSS = [1518.00, 2793.88, ...]
CATEGORIAS_DEBITO = ["Moradia", "Transporte", ...]
```

**CSS:**
```css
/* Classes: kebab-case */
.kpi-card { }
.nav-active { }

/* Data attributes: kebab-case */
data-test-id="form-submit-btn"
```

**React/JavaScript (futuro):**
```javascript
// Componentes: PascalCase
function KPICard() { }

// Funções: camelCase
function formatBRL(value) { }

// Constantes: UPPER_SNAKE_CASE
const API_BASE_URL = "..."
```

### 2. Type Hints

Sempre usar type hints em functions:

```python
from typing import Tuple, Optional, List, Dict
import pandas as pd

def get_lancamentos(
    username: str,
    ano: Optional[int] = None,
    mes: Optional[int] = None,
) -> pd.DataFrame:
    """Retorna lançamentos filtrados."""
    pass

def add_lancamento(
    username: str,
    categoria: str,
    valor: float,
    **extras
) -> Tuple[bool, Optional[str]]:
    """Adiciona lançamento. Retorna (sucesso, erro)."""
    pass

def get_categorias() -> List[str]:
    """Retorna lista de categorias."""
    pass

def parse_config() -> Dict[str, any]:
    """Carrega configuração."""
    pass
```

### 3. Docstrings

Seguir Google style guide:

```python
def calc_inss(bruto: float, anno: int = 2025) -> float:
    """Calcula INSS a partir de salário bruto.
    
    Usa tabela regressiva conforme ano fiscal.
    
    Args:
        bruto: Salário bruto em reais
        anno: Ano fiscal (padrão: ano atual)
    
    Returns:
        Valor de INSS em reais, limitado ao teto anual
    
    Raises:
        ValueError: Se bruto negativo
    
    Example:
        >>> calc_inss(5000.0)
        662.50
    """
    if bruto < 0:
        raise ValueError("Salário bruto não pode ser negativo")
    # ... implementação
```

### 4. Error Handling

Sempre retornar tuple `(sucesso: bool, mensagem_erro: str | None)`:

```python
def add_lancamento(username: str, **dados) -> Tuple[bool, Optional[str]]:
    try:
        # Validações
        if not username or not username.strip():
            return False, "Username obrigatório"
        
        if dados.get("valor", 0) <= 0:
            return False, "Valor deve ser positivo"
        
        # Operação
        row = [username, dados["ano"], dados["mes"], ...]
        _wsl().append_row(_safe_row(row), value_input_option="RAW")
        _cached_records.clear()
        
        return True, None  # Sucesso, sem erro
        
    except Exception as e:
        return False, f"Erro ao salvar: {str(e)}"
```

**Na view:**

```python
success, error = add_lancamento(username, **form_data)

if success:
    st.success("✅ Lançamento salvo com sucesso!")
else:
    st.error(f"❌ {error}")
```

### 5. Função Auxiliar de Feedback

```python
def _show_feedback(success: bool, message: str) -> None:
    """Exibe mensagem de sucesso ou erro."""
    if success:
        st.success(f"✅ {message}")
    else:
        st.error(f"❌ {message}")

# Uso:
ok, msg = add_lancamento(...)
_show_feedback(ok, msg or "Lançamento criado")
```

### 6. Formato de Função Storage

```python
def get_lancamentos(username: str) -> pd.DataFrame:
    """Busca todos os lançamentos do usuário."""
    recs = _cached_records("lanc") or []
    if not recs:
        return pd.DataFrame(columns=COLS_LANC)
    
    df = pd.DataFrame(recs)
    return df[df["username"] == username][COLS_LANC]

def add_lancamento(
    username: str,
    ano: int,
    mes: int,
    categoria: str,
    valor: float,
    **extras
) -> Tuple[bool, Optional[str]]:
    """Adiciona novo lançamento."""
    try:
        # 1. Validação
        if not all([username, categoria]):
            return False, "Campos obrigatórios"
        
        # 2. Processamento
        id_novo = _next_id(_cached_records("lanc") or [], "id")
        row = [
            id_novo,
            _safe_username(username),
            ano,
            mes,
            category.title(),
            valor,
            extras.get("forma_pagamento", "Pix"),
            extras.get("grupo_id")
        ]
        
        # 3. Persistência
        _wsl().append_row(_safe_row(row), value_input_option="RAW")
        _cached_records.clear()
        
        return True, None
    except Exception as e:
        return False, str(e)

def delete_lancamento(username: str, id: int) -> Tuple[bool, Optional[str]]:
    """Deleta lançamento por ID."""
    try:
        ws = _wsl()
        recs = _cached_records("lanc") or []
        
        # Encontrar índice da linha
        for i, r in enumerate(recs, start=2):
            if int(r.get("id", 0)) == id and r.get("username") == username:
                ws.delete_rows(i, 1)  # Deletar apenas esta linha
                _cached_records.clear()
                return True, None
        
        return False, "Lançamento não encontrado"
    except Exception as e:
        return False, str(e)
```

---

## 🎨 Adicionando uma Nova View

### Passo 1: Criar arquivo em `views/`

```python
# views/nova_funcionalidade.py
"""views/nova_funcionalidade.py - Nova funcionalidade."""

import streamlit as st
import pandas as pd
import functools as _ft
from data import storage as _st
from utils.helpers import brl, _show_feedback

def show_nova_funcionalidade(username: str):
    """Exibe painel de nova funcionalidade."""
    
    # ── Injetar dependências ──────────────────────────────────
    get_dados = _ft.partial(_st.get_dados, username)
    add_dados = _ft.partial(_st.add_dados, username)
    # ... mais injeções conforme necessário
    
    # ── Header ────────────────────────────────────────────────
    st.markdown("""
        <div class='dash-header'>
            <div class='dash-title'>🆕 Nova Funcionalidade</div>
            <div class='dash-subtitle'>Descrição breve</div>
        </div>""", unsafe_allow_html=True)
    
    # ── Lógica da view ────────────────────────────────────────
    df_dados = get_dados()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", len(df_dados))
    
    with col2:
        st.metric("Valor", brl(df_dados["valor"].sum() if not df_dados.empty else 0))
    
    # ── Formulário de entrada ─────────────────────────────────
    with st.form("form_nova"):
        nome = st.text_input("Nome")
        valor = st.number_input("Valor", min_value=0.0)
        
        if st.form_submit_button("Salvar", use_container_width=True):
            ok, msg = add_dados(username, nome=nome, valor=valor)
            _show_feedback(ok, msg or "Salvo com sucesso!")
    
    # ── Exibição de dados ─────────────────────────────────────
    if not df_dados.empty:
        st.dataframe(df_dados, use_container_width=True)
    else:
        st.info("Nenhum dado ainda")
```

### Passo 2: Registrar no `app.py`

```python
# No topo do app.py
from views.nova_funcionalidade import show_nova_funcionalidade

# Na sidebar (dentro do `with st.sidebar:`)
_nav_button("🆕 Nova", "Nova", "nav_nova")

# No bloco de roteamento
aba = st.session_state.get("aba", "Dashboard")
if aba == "Dashboard":
    show_dashboard(_username)
elif aba == "Nova":
    show_nova_funcionalidade(_username)
# ... outras abas
```

### Passo 3: Estender `storage.py`

```python
# data/storage.py

COLS_NOVA = ["id", "username", "nome", "valor", "created_at"]

def _wsn():  # Worksheet Nova
    return _get_worksheets()[9]  # Ajustar índice

@st.cache_data(ttl=60, show_spinner=False)
def _cached_records(sheet_kind: str):
    mapping = {
        # ... mapeamentos existentes
        "nova": (_wsn, COLS_NOVA),
    }
    # ... resto da função

def get_dados(username: str) -> pd.DataFrame:
    """Busca dados do usuário."""
    recs = _cached_records("nova") or []
    if not recs:
        return pd.DataFrame(columns=COLS_NOVA)
    
    df = pd.DataFrame(recs)
    return df[df["username"] == username][COLS_NOVA]

def add_dados(username: str, nome: str, valor: float) -> Tuple[bool, Optional[str]]:
    """Adiciona novo registro."""
    try:
        from datetime import datetime
        id_novo = _next_id(_cached_records("nova") or [], "id")
        row = [
            id_novo,
            _safe_username(username),
            nome,
            float(valor),
            datetime.now().isoformat()
        ]
        _wsn().append_row(_safe_row(row), value_input_option="RAW")
        _cached_records.clear()
        return True, None
    except Exception as e:
        return False, str(e)
```

### Passo 4: Testar

```bash
# Rodar localmente
streamlit run app.py

# Verificar:
# 1. Nova view aparece na sidebar
# 2. Dados são salvos no Google Sheets
# 3. Sem erros no console
```

---

## 🗄️ Estendendo Storage

### Adicionar nova tabela no Google Sheets

```python
# data/storage.py

# 1. Definir colunas
COLS_MINHA_ENTIDADE = ["id", "username", "campo1", "campo2", "created_at"]

# 2. Criar função de worksheet
def _wsme():  # Worksheet Minha Entidade
    return _get_worksheets()[10]  # Ajustar índice no retorno de _get_worksheets()

# 3. Registrar no mapeamento de cache
def _cached_records(sheet_kind: str):
    mapping = {
        # ... existentes
        "minha_entidade": (_wsme, COLS_MINHA_ENTIDADE),
    }
    # ... resto

# 4. CRUD completo
def get_minha_entidade(username: str) -> pd.DataFrame:
    recs = _cached_records("minha_entidade") or []
    if not recs:
        return pd.DataFrame(columns=COLS_MINHA_ENTIDADE)
    df = pd.DataFrame(recs)
    return df[df["username"] == username]

def add_minha_entidade(username: str, **dados) -> Tuple[bool, Optional[str]]:
    try:
        id_novo = _next_id(_cached_records("minha_entidade") or [], "id")
        row = [id_novo, _safe_username(username), ...]
        _wsme().append_row(_safe_row(row), value_input_option="RAW")
        _cached_records.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def update_minha_entidade(username: str, id: int, **dados) -> Tuple[bool, Optional[str]]:
    try:
        ws = _wsme()
        recs = _cached_records("minha_entidade") or []
        for i, r in enumerate(recs, start=2):
            if int(r.get("id")) == id and r.get("username") == username:
                nova_row = [id, username, dados["campo1"], ...]
                ws.update(f"A{i}:Z{i}", [_safe_row(nova_row)], value_input_option="RAW")
                _cached_records.clear()
                return True, None
        return False, "Não encontrado"
    except Exception as e:
        return False, str(e)

def delete_minha_entidade(username: str, id: int) -> Tuple[bool, Optional[str]]:
    try:
        ws = _wsme()
        recs = _cached_records("minha_entidade") or []
        for i, r in enumerate(recs, start=2):
            if int(r.get("id")) == id and r.get("username") == username:
                ws.delete_rows(i, 1)
                _cached_records.clear()
                return True, None
        return False, "Não encontrado"
    except Exception as e:
        return False, str(e)
```

### Importante: Atualizar `_get_worksheets()`

```python
def _get_worksheets():
    # ... código existente
    return (
        _ws("lancamentos",       COLS_LANC),         # [0]
        _ws("ganhos",            COLS_GANHO),        # [1]
        _ws("cartao_compras",    COLS_CARTAO),       # [2]
        _ws("cartao_config",     COLS_CARTAO_CFG),   # [3]
        _ws("perfis",            COLS_PERFIS),       # [4]
        _ws("categorias",        COLS_CATEGORIAS),   # [5]
        _ws("user_config",       COLS_USER_CFG),     # [6]
        _ws("historico",         COLS_HISTORICO),    # [7]
        _ws("metas",             COLS_METAS),        # [8]
        _ws("minha_entidade",    COLS_MINHA_ENTIDADE),  # [9] ← Nova
    )
```

---

## 🔐 Trabalhando com Autenticação

### Entender o fluxo de autenticação

```python
# auth.py

def require_perfil() -> Tuple[str, str]:
    """Requer login. Retorna (username, nome_completo)."""
    if not st.session_state.get("username"):
        _show_perfil_selector()  # Exibe tela de seleção de perfis
        st.stop()  # Para execução aqui
    
    username = st.session_state.username
    perfil = _get_perfis().get(username, {})
    return username, perfil.get("nome", username.title())

def logout() -> None:
    """Limpa session state e força rerun."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
```

### Gerenciamento de senhas

**Hashing:** Usa bcrypt para senhas opcionais

```python
import bcrypt

# Hash nova senha
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Verificar senha
valid = bcrypt.checkpw(input_password.encode(), stored_hash.encode())
```

**Armazenamento:** Campo `password` na tabela `perfis` do Google Sheets

**Validação:**
- Senhas opcionais (campo vazio = sem senha)
- Mínimo 6 caracteres quando definida
- Alteração via `update_perfil(username, ..., password_hash)`

### Modificar permissões/papéis (futuro)

Para adicionar roles, estender estrutura de perfis com campo `role`.
```

Depois, adicionar check nas views:

```python
def require_perfil() -> Tuple[str, str, str]:
    """Retorna (username, nome, role)."""
    # ... validação
    role = _get_perfis().get(username, {}).get("role", "user")
    return username, perfil.get("nome"), role

# Em view admin
_username, _name, _role = require_perfil()
if _role != "admin":
    st.error("Acesso negado")
    st.stop()
```

---

## 🧪 Debugging e Testes

### Debugging local

```bash
# 1. Ativar modo debug
DEBUG=True streamlit run app.py

# 2. Adicionar prints estratégicos
import streamlit as st

def get_lancamentos(username: str) -> pd.DataFrame:
    print(f"🔍 [DEBUG] get_lancamentos chamado com username={username}")
    recs = _cached_records("lanc") or []
    print(f"🔍 [DEBUG] Registros retornados: {len(recs)}")
    # ... resto

# 3. Usar st.write() para inspecionar valores
st.write("Estado da session:", st.session_state)
st.write("DataFrame shape:", df_all.shape)
```

### Testes unitários

```python
# tests/test_storage.py
import pytest
import pandas as pd
from data.storage import (
    add_lancamento,
    get_lancamentos,
    delete_lancamento,
)

@pytest.fixture
def username():
    return "test_user"

def test_add_lancamento_success(username):
    """Testa adição bem-sucedida de lançamento."""
    ok, err = add_lancamento(
        username=username,
        ano=2026,
        mes=5,
        categoria="Moradia",
        valor=150.50,
        forma_pagamento="Pix"
    )
    assert ok is True
    assert err is None

def test_add_lancamento_invalid_valor(username):
    """Testa validação de valor negativo."""
    ok, err = add_lancamento(
        username=username,
        ano=2026,
        mes=5,
        categoria="Moradia",
        valor=-100.0,  # Inválido
        forma_pagamento="Pix"
    )
    assert ok is False
    assert "positivo" in err.lower()

def test_get_lancamentos_empty(username):
    """Testa retorno vazio."""
    df = get_lancamentos(username)
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 0  # Pode estar vazio

def test_delete_lancamento_success(username):
    """Testa deleção bem-sucedida."""
    # Assumindo que existe um lançamento com id=1
    ok, err = delete_lancamento(username, id=1)
    assert ok is True
```

Rodar testes:

```bash
pytest tests/
pytest tests/test_storage.py -v
pytest tests/ --cov=data  # Com coverage
```

### Logs estruturados

```python
# utils/logger.py
import logging
import sys
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """Retorna logger formatado."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    
    fmt = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

# Uso:
from utils.logger import get_logger
logger = get_logger(__name__)

logger.info(f"Usuário {username} fez login")
logger.error(f"Erro ao salvar: {error}")
```

---

## 🚀 Deploy

### Deploy local

Já coberto no README. Para referência:

```bash
pip install -r requirements.txt
streamlit run app.py --logger.level=info
```

### Deploy no Streamlit Cloud

1. Push para GitHub
2. Ir em [share.streamlit.io](https://share.streamlit.io)
3. Conectar repositório
4. Selecionar `app.py`
5. Em "Advanced settings" → "Secrets", colar conteúdo de `.streamlit/secrets.toml`

**Secrets in Cloud:**

```toml
# Paste conteúdo inteiro do seu secrets.toml local
[gcp_service_account]
type = "service_account"
project_id = "meu-projeto"
private_key_id = "..."
private_key = "..."
client_email = "..."
# ... resto dos campos

sheet_name = "Finanças Pessoais"
```

### Deploy com Docker (opcional)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build e run:

```bash
docker build -t financas-app .
docker run -p 8501:8501 \
  -v ~/.streamlit/secrets.toml:/root/.streamlit/secrets.toml:ro \
  financas-app
```

### Deploy em produção (futuro)

Opções consideradas:
- Vercel + FastAPI backend
- Heroku
- AWS ECS + RDS
- Google Cloud Run + Cloud SQL
- DigitalOcean App Platform

---

## 📝 Estrutura de Commits

Seguir Conventional Commits:

```
<tipo>(<escopo>): <descrição>

<corpo>

<rodapé>
```

### Tipos

- `feat` — Nova funcionalidade
- `fix` — Correção de bug
- `docs` — Apenas documentação
- `style` — Sem impacto lógico (formatting, etc.)
- `refactor` — Reorganização sem alterar behavior
- `perf` — Melhoria de performance
- `test` — Adição/modificação de testes
- `chore` — Atualizações de dependências, build, etc.

### Exemplos

```
feat(lancamentos): adicionar filtro por forma de pagamento

Permite filtrar lançamentos por forma de pagamento (Pix, Boleto, etc.).
Adiciona multiselect na view de lançamentos.

Closes #42
```

```
fix(dashboard): corrigir cálculo de saldo com múltiplos meses

Saldo estava sendo calculado apenas para primeiro mês selecionado.
Agora agrupa corretamente todos os meses.
```

```
docs(readme): atualizar instruções de setup
```

```
refactor(storage): extrair lógica de cache em função auxiliar

Reduz duplicação entre get_lancamentos, get_ganhos, etc.
Sem mudança de comportamento externo.
```

### Push

```bash
git add .
git commit -m "feat(ganhos): implementar cálculo de IRRF por dependente"
git push origin main
```

---

## 📚 Recursos Técnicos

### Documentação externa

- [Streamlit Docs](https://docs.streamlit.io)
- [Plotly Docs](https://plotly.com/python/)
- [Pandas Docs](https://pandas.pydata.org/docs/)
- [gspread Docs](https://docs.gspread.org)
- [Google Sheets API](https://developers.google.com/sheets/api)

### Ferramentas recomendadas

- **VS Code Extensions:**
  - Python (Microsoft)
  - Pylance
  - REST Client
  - Thunder Client (testes de API)

- **CLI Tools:**
  - `black` — Code formatter
  - `flake8` — Linter
  - `pytest` — Test runner
  - `pre-commit` — Git hooks

---

## 🔗 Links Internos

- [DOCUMENTACAO.md](DOCUMENTACAO.md) — Documentação para usuários
- [README.md](README.md) — Guia rápido
- [plano_reestruturacao.md](plano_reestruturacao.md) — Histórico de evolução

---

**Última atualização:** Maio 2026  
**Versão:** 2.0
