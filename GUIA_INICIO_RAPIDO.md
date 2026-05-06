# ⚡ Guia de Início Rápido — Finanças Pessoais

> **Versão:** 2.0  
> **Data:** Maio 2026  
> **Tempo de leitura:** 5 minutos

---

## 🚀 Comece em 5 minutos

### Opção 1: Usar online (mais rápido)

1. Acesse: [share.streamlit.io/[seu-repo-aqui]](https://share.streamlit.io)
2. Faça login com suas credenciais
3. Use o app! 🎉

---

### Opção 2: Instalar localmente

#### Pré-requisitos
- Python 3.9+
- Git
- Conta Google

#### Passo 1: Clonar e instalar

```bash
# Clone o projeto
git clone <seu-repositorio>
cd financas_pessoais

# Crie virtualenv
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instale dependências
pip install -r requirements.txt
```

#### Passo 2: Configurar Google Sheets

1. Crie uma planilha em [sheets.google.com](https://sheets.google.com)
2. Nomeie como: **"Finanças Pessoais"**
3. Crie Service Account em [console.cloud.google.com](https://console.cloud.google.com):
   - **Projeto novo** → crie uma
   - Ative: Google Sheets API + Google Drive API
   - **IAM & Admin** → **Service Accounts** → Crie conta
   - Gere JSON key (baixe)
4. Compartilhe planilha com o email da Service Account (Editor)

#### Passo 3: Configurar secrets

```bash
# Crie arquivo de secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Abra e edite com dados do JSON
# Copie campo por campo
```

#### Passo 4: Rodar

```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

---

## 📚 Documentação por Tipo de Usuário

### 👤 Sou usuário final — Quero usar o app

**Tempo:** 10 min

1. ✅ Instale conforme acima
2. ✅ Leia: [README.md](README.md) seção rápida
3. ✅ Leia: [DOCUMENTACAO.md](DOCUMENTACAO.md) seção "Funcionalidades Principais"
4. ✅ Comece! Use o app naturalmente

**Guia de primeiros passos:**
1. Dashboard → Conheça os KPIs
2. Ganhos → Registre seu salário
3. Lançamentos → Registre um gasto
4. Extrato → Veja tudo consolidado
5. Metas → Crie uma meta de economia
6. Configurações → 🔐 Senha (opcional) para proteger seu perfil

---

### 👨‍💻 Sou desenvolvedor — Quero codar

**Tempo:** 20 min

1. ✅ Setup conforme acima
2. ✅ Leia: [DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md)
3. ✅ Explore:
   - `views/dashboard.py` — primeiro exemplo
   - `data/storage.py` — CRUD
   - `app.py` — roteador principal
4. ✅ Rode: `streamlit run app.py`
5. ✅ Comece com pequenas correções

**Primeira tarefa sugerida:**
- Adicionar nova categoria em `config.py`
- Criar nova view em `views/` (copie estrutura de `lancamentos.py`)
- Adicionar teste unitário para `storage.py`

---

### 👔 Sou gerente/PM — Quero aprovar recursos

**Tempo:** 25 min

1. ✅ Leia: [ANALISE_EXECUTIVA_ROADMAP.md](ANALISE_EXECUTIVA_ROADMAP.md)
2. ✅ Foco em:
   - Sumário Executivo
   - Roadmap de Evolução
   - Métricas de Sucesso
   - Análise de Riscos

---

## ❓ FAQ Rápido

### P: Por que tenho que criar um Google Sheets?

**R:** É o banco de dados. Pode ser Sheets, PostgreSQL, MongoDB — a escolha foi Sheets por:
- Zero DevOps
- Backup automático
- Dados visíveis direto

### P: É seguro guardar dados no Google Sheets?

**R:** Sim! Google Sheets usa SSL/TLS e você controla o acesso. Mas em produção com dados sensíveis, recomenda-se PostgreSQL.

### P: Posso usar sem criar usuário?

**R:** Não. Login é obrigatório. Crie um com `scripts/add_user.py`

### P: Como compartilho com meu cônjuge?

**R:** Atualmente, cada usuário tem dados isolados. Funcionalidade de contas conjuntas está no roadmap (P2).

### P: Como exporto meus dados?

**R:** Vá em Extrato → "Exportar como CSV"

### P: Posso usar em mobile?

**R:** Sim, mas não é otimizado. App mobile nativo está no roadmap (P3).

### P: Quem tem acesso aos meus dados?

**R:** Apenas você (o proprietário da conta Google). Ninguém da equipe acessa.

### P: Há backup automático?

**R:** Sim! Google Sheets faz backup contínuo. Você pode também exportar em Dados → Exportar.

### P: Como reporto um bug?

**R:** Abra issue no GitHub com: versão, passos para reproduzir, screenshot.

### P: Posso contribuir?

**R:** Claro! Faça fork, crie branch, submeta PR. Leia DOCUMENTACAO_TECNICA.md primeiro.

---

## 🎯 Próximos Passos Sugeridos

### Próxima hora (depois de instalar)

- [ ] Registre um lançamento manual
- [ ] Registre um ganho/salário
- [ ] Veja o Dashboard atualizado
- [ ] Explore cada seção

### Próximo dia

- [ ] Importe um extrato (CSV)
- [ ] Crie uma meta de economia
- [ ] Explore relatórios
- [ ] Customize suas preferências

### Próxima semana

- [ ] Registre todos os lançamentos da última semana
- [ ] Acompanhe o progresso das metas
- [ ] Revise se categorias fazem sentido
- [ ] Faça um backup dos dados

### Próximo mês

- [ ] Analise padrões de gastos
- [ ] Ajuste orçamento para próximo mês
- [ ] Revise metas
- [ ] Compartilhe feedback!

---

## 🗂️ Estrutura de Arquivos Importante

```
financas_pessoais/
├── app.py                    ← Inicie daqui (streamlit run app.py)
├── README.md                 ← Guia rápido
├── requirements.txt          ← Dependências
│
├── DOCUMENTACAO.md           ← 📖 Leia isto (referência completa)
├── DOCUMENTACAO_TECNICA.md   ← 👨‍💻 Para desenvolvedores
├── ANALISE_EXECUTIVA_ROADMAP.md ← 👔 Para líderes
├── INDICE_DOCUMENTACAO.md    ← 📚 Mapa de navegação
├── GUIA_INICIO_RAPIDO.md     ← ⚡ Este arquivo
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml          ← Suas credenciais (SECRETO!)
│
├── views/                    ← 9 funcionalidades da aplicação
│   ├── dashboard.py
│   ├── ganhos.py
│   ├── lancamentos.py
│   ├── cartao.py
│   ├── extrato.py
│   ├── metas.py
│   ├── relatorio.py
│   ├── importar.py
│   └── configuracoes.py
│
├── utils/                    ← Funções compartilhadas
│   ├── color.py
│   ├── charts.py
│   ├── helpers.py
│   ├── tokens.py
│   ├── styles.py
│   └── pdf_report.py
│
├── data/                     ← Acesso a dados
│   ├── storage.py            ← CRUD principal
│   └── metas_storage.py
│
├── importers/                ← Importação de CSVs
│   ├── csv_importer.py
│   ├── category_matcher.py
│   └── ofx_importer.py
│
├── scripts/                  ← Utilitários CLI
│   ├── add_user.py
│   └── migrate_to_users.py
│
└── assets/
    └── styles.css            ← Estilos globais
```

---

## 🎨 Primeiras Impressões

### Dashboard
- 4 cards com KPIs principais
- Fluxo de receitas e despesas
- Capacidade de gasto (regra 50/30/20)
- Gráficos de tendência

### Ganhos
- Registre salários, investimentos, aluguéis
- Cálculos automáticos de INSS/IRRF
- Copiar salário para o ano inteiro

### Lançamentos
- Créditos e débitos manuais
- Múltiplas formas de pagamento
- Categorias dinâmicas

### Cartão
- Controle de compras parceladas
- Projeção de 6 meses
- Múltiplos cartões

### Extrato
- Consolidação de tudo
- Filtros avançados
- Exportar para CSV

---

## 💡 Dicas Rápidas

### Tip 1: Use Enter para confirmar
Na maioria dos formulários, pressione Enter para salvar.

### Tip 2: Modo dark é automático
O app usa tema escuro. Personalize em Configurações.

### Tip 3: Dados sincronizam em tempo real
Abra em duas abas — vê as mudanças instantaneamente!

### Tip 4: Categorias customizáveis
Vá em Configurações → Categorias Personalizadas

### Tip 5: Backup é automático
Google Sheets faz backup contínuo. Mas exporte mensalmente para ter cópia local.

---

## 🆘 Tenho um Problema!

### O app não inicia

```bash
# Verifique Python
python --version  # Precisa ser 3.9+

# Verifique se dependências foram instaladas
pip list | grep streamlit

# Tente reinstalar
pip install -r requirements.txt --force-reinstall
```

### Erro: "Sheet not found"

- Verifique se planilha se chama **exatamente** "Finanças Pessoais"
- Verifique se Service Account foi adicionada com permissão "Editor"

### Erro de autenticação

```bash
# Redefina as credenciais
rm .streamlit/secrets.toml
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite novamente com dados corretos
```

### Dados não aparecem

- Limpe cache: `streamlit cache clear`
- Aguarde 60s (TTL do cache)
- Verifique se há dados no Google Sheets

### Mais ajuda?

→ Leia [DOCUMENTACAO.md — Troubleshooting](DOCUMENTACAO.md#troubleshooting)

---

## 🚀 Pronto para Começar?

```bash
# 1. Clone
git clone <seu-repo>
cd financas_pessoais

# 2. Setup (5 min)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure Google Sheets
# (Siga passo a passo acima)

# 4. Rode!
streamlit run app.py

# 5. Abra http://localhost:8501 no navegador
```

**Você está pronto! 🎉**

---

## 📖 Leitura Recomendada (por ordem)

1. **Este arquivo** (5 min) ← Você está aqui
2. [README.md](README.md) (5 min)
3. [DOCUMENTACAO.md](DOCUMENTACAO.md) - Funcionalidades (30 min)
4. [Código em views/](views/) - Exploração livre

---

## 🤝 Comunidade

- 🐛 **Encontrou bug?** Abra issue no GitHub
- 💡 **Tem sugestão?** Discussão no GitHub
- 👋 **Quer contribuir?** Fork + PR + Leia DOCUMENTACAO_TECNICA.md

---

## 📞 Links Úteis

- **Documentação completa:** [DOCUMENTACAO.md](DOCUMENTACAO.md)
- **Para devs:** [DOCUMENTACAO_TECNICA.md](DOCUMENTACAO_TECNICA.md)
- **Para líderes:** [ANALISE_EXECUTIVA_ROADMAP.md](ANALISE_EXECUTIVA_ROADMAP.md)
- **Índice de docs:** [INDICE_DOCUMENTACAO.md](INDICE_DOCUMENTACAO.md)
- **GitHub:** [seu-repo-aqui]

---

## ✨ Bom uso! 🎉

Aproveite controlar suas finanças pessoais com estilo!

Qualquer dúvida, a documentação completa está esperando por você.

**Última atualização:** Maio 2026  
**Versão:** 2.0
