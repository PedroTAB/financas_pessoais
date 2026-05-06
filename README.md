# � Finanças Pessoais — Controle Financeiro Completo

> **Versão:** 2.0 | **Status:** ✅ Produção | **Última atualização:** Maio 2026

Aplicação web de gestão financeira pessoal desenvolvida em **Streamlit** com persistência em **Google Sheets**. Multi-usuário, modular, e pronta para crescer.

---

## ✨ Funcionalidades Principais

| Feature | Descrição |
|---|---|
| 📊 **Dashboard** | KPIs em tempo real, fluxo de caixa, capacidade de gasto (50/30/20) |
| 💸 **Ganhos** | Salário com cálculo automático de INSS/IRRF, investimentos, aluguéis |
| 📝 **Lançamentos** | Créditos e débitos com múltiplas formas de pagamento |
| 💳 **Cartão de Crédito** | Parcelamentos, projeção de 6 meses, múltiplos cartões |
| 📋 **Extrato** | Consolidação com filtros avançados e exportação CSV |
| 🎯 **Metas** | Acompanhamento visual de objetivos de economia |
| 📈 **Relatórios** | Exportação em PDF, Excel e JSON |
| 📥 **Importador CSV** | Detecção automática de banco, sugestão de categorias |
| ⚙️ **Configurações** | Customização de preferências, categorias, perfil |

---

## 🚀 Comece em 5 Minutos

### Opção 1: Localmente (recomendado para começar)

```bash
# 1. Clone e instale
git clone <seu-repositorio>
cd financas_pessoais
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure Google Sheets (veja seção abaixo)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite com suas credenciais

# 3. Rode!
streamlit run app.py
```

**Acesse:** `http://localhost:8501`

**Primeiro uso:** Crie seu perfil em "Novo perfil". Senhas são opcionais (mínimo 6 caracteres).

### Opção 2: Online (Streamlit Cloud)

1. Push para GitHub
2. Vá em [share.streamlit.io](https://share.streamlit.io)
3. Selecione seu repositório e `app.py`
4. Em Advanced Settings, adicione seus secrets
5. Deploy! 🎉

---

## ⚙️ Configuração do Google Sheets

### Passo 1: Criar planilha

1. Acesse [sheets.google.com](https://sheets.google.com)
2. Crie uma nova planilha
3. **Nomeie exatamente:** `Finanças Pessoais`

### Passo 2: Service Account

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie projeto (ou use existente)
3. Ative: **Google Sheets API** + **Google Drive API**
4. **IAM & Admin** → **Service Accounts** → Criar
5. Na conta criada: **Keys** → **Add Key** → **JSON** → Baixe

### Passo 3: Compartilhar

1. Abra JSON baixado, copie `client_email`
2. Abra sua planilha no Sheets
3. Clique **Compartilhar**, adicione o email como **Editor**

### Passo 4: Secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edite `.streamlit/secrets.toml` com dados do JSON:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "financas@seu-projeto.iam.gserviceaccount.com"
# ... complete com outros campos

sheet_name = "Finanças Pessoais"
```

⚠️ **Nunca commitar** `secrets.toml` — está em `.gitignore`

---

## 📚 Documentação

| Documento | Para Quem | Tempo |
|---|---|---|
| **[GUIA_INICIO_RAPIDO.md](GUIA_INICIO_RAPIDO.md)** | Todos (primeiros passos) | 5 min |
| **[DOCUMENTACAO.md](DOCUMENTACAO.md)** | Usuários (referência completa) | 30-45 min |
| **[DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md)** | Desenvolvedores | 20-30 min |
| **[ANALISE_EXECUTIVA_ROADMAP.md](ANALISE_EXECUTIVA_ROADMAP.md)** | Líderes/PMs | 20-25 min |
| **[INDICE_DOCUMENTACAO.md](INDICE_DOCUMENTACAO.md)** | Navegação geral | 5 min |

**→ [Clique aqui para índice completo](INDICE_DOCUMENTACAO.md)**

---

## 🗂️ Estrutura do Projeto

```
financas_pessoais/
├── app.py                         ← Inicie aqui: streamlit run app.py
├── auth.py                        ← Autenticação multi-usuário
├── config.py                      ← Configurações globais
│
├── views/                         ← 9 funcionalidades principais
│   ├── dashboard.py, ganhos.py, lancamentos.py, cartao.py,
│   ├── extrato.py, metas.py, relatorio.py, importar.py,
│   └── configuracoes.py
│
├── utils/                         ← Utilitários compartilhados
│   ├── color.py, charts.py, helpers.py, tokens.py, styles.py
│   └── pdf_report.py
│
├── data/                          ← Camada de dados
│   ├── storage.py                 ← CRUD + Google Sheets
│   └── metas_storage.py
│
├── importers/                     ← Importação de CSVs
│   ├── csv_importer.py, category_matcher.py, ofx_importer.py
│
├── assets/
│   └── styles.css                 ← CSS global
│
├── .streamlit/
│   ├── config.toml                ← Config Streamlit
│   └── secrets.toml               ← Credenciais (SECRETO!)
│
└── [Documentação]
    ├── DOCUMENTACAO.md, DOCUMENTACAO_TECNICA.md,
    ├── ANALISE_EXECUTIVA_ROADMAP.md, INDICE_DOCUMENTACAO.md
    └── GUIA_INICIO_RAPIDO.md
```

---

## 🎯 Principais Conceitos

### Dashboard
Visão consolidada com 4 KPIs (Entradas, Saídas, Saldo, Fatura Cartão), fluxo de receitas/despesas, capacidade de gasto, e tendências de 12 meses.

### Multi-usuário
Cada usuário autenticado tem dados isolados. Suporta até 50 usuários simultaneamente. Escalável para PostgreSQL em produção.

### Importador
Detecta automaticamente o banco (Nubank, Itaú, Bradesco, etc.), mapeia colunas, sugere categorias e evita duplicatas.

### Cálculos Automáticos
INSS e IRRF 2025 com alíquotas progressivas, dependentes configuráveis, e exportação de recibos.

### Metas
Acompanhamento visual com barras de progresso, alertas por percentual, e projeção de data de conclusão.

---

## 💻 Stack Técnica

| Camada | Tecnologia |
|---|---|
| Frontend | Streamlit 1.35+ |
| Visualização | Plotly 5.20+ |
| Dados | Pandas 2.2+, NumPy 1.26+ |
| Backend | Python 3.9+ |
| BD | Google Sheets API |
| Auth | streamlit-authenticator 0.3.3+ |
| Segurança | bcrypt 4.0.1+ |

---

## 🚀 Próximos Passos

### 1️⃣ Primeiro Acesso

```bash
streamlit run app.py
# Crie usuário: python scripts/add_user.py
# Use o app!
```

### 2️⃣ Primeiros Dados

1. Registre um ganho (Dashboard → Ganhos)
2. Registre um lançamento (Dashboard → Lançamentos)
3. Observe atualização no Dashboard

### 3️⃣ Exploração

- [ ] Importe extrato (Importar)
- [ ] Crie metas (Metas)
- [ ] Confira relatórios (Relatório)
- [ ] Customize (Configurações)

### 4️⃣ Documentação

Leia [DOCUMENTACAO.md](DOCUMENTACAO.md) para referência completa de cada feature.

---

## 🐛 Troubleshooting

### "Sheet not found"
Verifique se planilha se chama **exatamente** "Finanças Pessoais"

### "Auth config not found"
Execute `python scripts/add_user.py`

### Dados não aparecem
- Limpe cache: `streamlit cache clear`
- Aguarde 60s (TTL do cache)

**→ [Mais soluções em DOCUMENTACAO.md](DOCUMENTACAO.md#troubleshooting)**

---

## 📈 Roadmap

### Curto Prazo (Jun 2026) — Performance & Testes
- Performance de gráficos
- Cobertura de testes
- Melhorias de UX

### Médio Prazo (Jul-Set 2026) — Segurança & Escala
- 2FA
- Open Banking (PIX automático)
- Migração para PostgreSQL

### Longo Prazo (Out-Dez 2026) — Plataforma
- Apps iOS/Android
- PWA
- Marketplace de integrações

**→ [Roadmap detalhado](ANALISE_EXECUTIVA_ROADMAP.md#roadmap-de-evolução)**

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch: `git checkout -b feature/sua-feature`
3. Commit: `git commit -m "feat: descrição"`
4. Push: `git push origin feature/sua-feature`
5. Abra um Pull Request

**Leia [DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md) antes de codar!**

---

## 📄 Licença

[Adicione sua licença aqui]

---

## 📞 Suporte

- 🐛 **Bugs:** Abra issue no GitHub
- 💡 **Sugestões:** Discussão no GitHub
- 📖 **Dúvidas:** Veja [DOCUMENTACAO.md](DOCUMENTACAO.md)

---

## 📊 Status do Projeto

| Aspecto | Status |
|---|---|
| Funcionalidades Core | ✅ Completo |
| Testes | 🟡 Parcial |
| Documentação | ✅ Completa |
| Performance | 🟡 Boa |
| Segurança | 🟡 Adequada |
| Pronto para Produção | ✅ Sim |

---

**Made with ❤️**  
**Última atualização:** Maio 2026 | **Versão:** 2.0
