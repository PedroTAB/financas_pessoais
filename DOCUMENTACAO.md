# 📊 Finanças Pessoais — Documentação Completa v2.0

> **Versão:** 2.0  
> **Data:** Maio 2026  
> **Status:** Produção  
> **Autores:** Desenvolvimento financeiro pessoal  
> **Última atualização:** Maio 2026

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Objetivo e Propósito](#objetivo-e-propósito)
3. [Stack Técnica](#stack-técnica)
4. [Arquitetura](#arquitetura)
5. [Guia de Instalação](#guia-de-instalação)
6. [Funcionalidades Principais](#funcionalidades-principais)
7. [Estrutura de Dados](#estrutura-de-dados)
8. [Fluxos de Negócio](#fluxos-de-negócio)
9. [Sistema Multi-Usuário](#sistema-multi-usuário)
10. [Módulos Detalhados](#módulos-detalhados)
11. [Configurações e Customização](#configurações-e-customização)
12. [Limitações Conhecidas](#limitações-conhecidas)
13. [Futuras Evoluções](#futuras-evoluções)
14. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

**Finanças Pessoais** é uma aplicação web completa de gestão financeira pessoal, desenvolvida em **Streamlit**, com persistência de dados no **Google Sheets**. O sistema oferece uma plataforma moderna, multi-usuário e totalmente responsiva para controle e análise de receitas, despesas, investimentos e planejamento financeiro.

### Principais características

✅ **Dashboard inteligente** com KPIs e tendências  
✅ **Multi-usuário** com autenticação segura e perfis customizáveis  
✅ **Persistência em nuvem** — dados salvos no Google Sheets  
✅ **Cálculo automático** de INSS, IRRF e impostos  
✅ **Controle de cartão de crédito** com parcelamento e projeções  
✅ **Sistema de metas** com acompanhamento progredido  
✅ **Importador de CSV** com detecção automática de banco  
✅ **Relatórios avançados** com exportação em múltiplos formatos  
✅ **Design moderno** com componentes Apple-like  
✅ **Responsivo** — funciona em desktop, tablet e mobile

---

## 🎯 Objetivo e Propósito

O aplicativo foi concebido para resolver três desafios principais:

### 1. **Centralização de dados financeiros**
Consolidar todas as transações financeiras (receitas, despesas, cartão de crédito, investimentos) em um único lugar, eliminando a necessidade de planilhas espalhadas.

### 2. **Visibilidade em tempo real**
Oferecer visão instantânea da saúde financeira através de dashboards com KPIs, gráficos e análises automáticas.

### 3. **Planejamento e controle**
Permitir acompanhamento de metas de economia, capacidade de gasto e projeções de fluxo de caixa para os próximos meses.

### Público-alvo

- Indivíduos que desejam controlar suas finanças pessoais de forma organizada
- Casais/famílias que precisam compartilhar dados financeiros
- Freelancers e autônomos com múltiplas fontes de receita
- Pessoas interessadas em análise financeira avançada

---

## 💻 Stack Técnica

### Frontend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **Streamlit** | ≥1.35.0 | Framework web com componentes interativos |
| **Plotly** | ≥5.20.0 | Gráficos e visualizações interativas |
| **Pandas** | ≥2.2.0 | Manipulação e análise de dados tabulares |

### Backend

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **Python** | 3.9+ | Linguagem principal |
| **gspread** | ≥6.0.0 | Integração com Google Sheets API |
| **google-auth** | ≥2.28.0 | Autenticação OAuth2 com Google Cloud |

### Autenticação & Segurança

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **streamlit-authenticator** | ≥0.3.3 | Sistema de login e gerenciamento de sessão |
| **bcrypt** | ≥4.0.1 | Hash seguro de senhas |

### Persistência

- **Google Sheets API** — banco de dados relacional em nuvem
- **Estrutura de worksheets** — separação lógica por entidade (lançamentos, ganhos, cartão, etc.)

### Deployment

- **Streamlit Community Cloud** — hosting gratuito com suporte a secrets
- **Docker** (opcional) — containerização para ambientes personalizados

---

## 🏗️ Arquitetura

### Estrutura de diretórios

```
financas_pessoais/
├── app.py                         ← Roteador principal e sidebar
├── auth.py                        ← Autenticação e gerenciamento de perfis
├── config.py                      ← Configurações centralizadas
├── requirements.txt               ← Dependências Python
├── README.md                      ← Guia rápido
│
├── assets/
│   └── styles.css                 ← CSS global compartilhado
│
├── utils/
│   ├── __init__.py
│   ├── color.py                   ← Utilitários de conversão de cores (hex ↔ rgba)
│   ├── charts.py                  ← Funções reutilizáveis de gráficos Plotly
│   ├── helpers.py                 ← Helpers de formatação, parsing e constantes
│   ├── tokens.py                  ← Design tokens (cores, espaçamento)
│   ├── pdf_report.py              ← Gerador de relatórios PDF
│   └── styles.py                  ← Carregador de CSS
│
├── views/
│   ├── __init__.py
│   ├── dashboard.py               ← Dashboard principal com KPIs
│   ├── ganhos.py                  ← Cadastro e gestão de receitas
│   ├── lancamentos.py             ← CRUD de lançamentos (crédito/débito)
│   ├── cartao.py                  ← Gestão de cartão de crédito
│   ├── extrato.py                 ← Extrato consolidado e filtros
│   ├── metas.py                   ← Sistema de metas e reservas
│   ├── relatorio.py               ← Relatórios avançados
│   ├── importar.py                ← Importador de CSV multi-banco
│   └── configuracoes.py           ← Painel de configurações
│
├── data/
│   ├── __init__.py
│   ├── storage.py                 ← CRUD com Google Sheets
│   ├── metas_storage.py           ← Persistência de metas
│   ├── profiles.json              ← Perfis padrão (fallback)
│   └── users/                     ← Dados por usuário (estrutura preparada)
│       └── {username}/
│           ├── lancamentos.json
│           ├── ganhos.json
│           └── config.json
│
├── importers/
│   ├── csv_importer.py            ← Parser CSV com detecção de banco
│   ├── category_matcher.py        ← Mapeamento automático de categorias
│   └── ofx_importer.py            ← Parser OFX (extensível)
│
├── scripts/
│   ├── add_user.py                ← CLI para cadastrar novos usuários
│   └── migrate_to_users.py        ← Migração de dados legados
│
├── output/
│   ├── dashboard.py               ← Exportadores e geradores
│   └── ...
│
├── .streamlit/
│   ├── config.toml                ← Configuração Streamlit (tema, layout)
│   └── secrets.toml               ← Credenciais (NUNCA commitar)
│
├── .gitignore
├── .env                           ← Variáveis de ambiente
└── [documentação]/
    ├── DOCUMENTACAO.md            ← Esta documentação
    ├── documentacao_antiga.md     ← Histórico para referência
    └── plano_reestruturacao.md    ← Plano de evolução
```

### Modelo de camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Web (Streamlit)                 │
│  app.py → sidebar + roteamento → views/dashboard.py, etc.   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Camada de Lógica                          │
│  views/*.py → validação, cálculos, transformações           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Camada de Dados                            │
│  storage.py → Google Sheets API → Cloud SQL/Drive           │
│  metas_storage.py → persistência local + Sheets             │
└─────────────────────────────────────────────────────────────┘
```

### Padrões arquiteturais

**MVC-like sem Model explícito** — A camada `views/` contém lógica e UI, enquanto `storage.py` funciona como repository pattern.

**Multi-tenancy por workspace** — Cada usuário autenticado tem seus dados isolados no Google Sheets, identificados pela coluna `username`.

**Lazy loading e cache** — Dados são carregados sob demanda com `@st.cache_data` e `@st.cache_resource` para minimizar chamadas à API.

**Composição de funções** — Cada view recebe `username` como parâmetro e usa `functools.partial` para "injetar" dependências sem estado global.

---

## 🚀 Guia de Instalação

### Pré-requisitos

- **Python 3.9+**
- **Git**
- **Conta Google** (para Google Sheets API)
- **pip** ou **poetry**

### Passo 1: Clonar o repositório

```bash
git clone <seu-repositorio>
cd financas_pessoais
```

### Passo 2: Criar ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Google Sheets API

#### 4.1 Criar uma planilha no Google Drive

1. Acesse [sheets.google.com](https://sheets.google.com)
2. Clique em "Nova planilha"
3. Nomeie como **"Finanças Pessoais"** (deve ser exato)

#### 4.2 Criar Service Account

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto ou selecione um existente
3. Ative as APIs:
   - Google Sheets API
   - Google Drive API
4. Vá para **IAM & Admin → Service Accounts**
5. Clique em **"Create Service Account"**
6. Preencha nome e clique em **"Create"**
7. Na conta criada, vá em **"Keys"** → **"Add Key"** → **"Create new key"** → **"JSON"**
8. Salve o arquivo JSON em local seguro

#### 4.3 Compartilhar planilha com Service Account

1. Abra o JSON baixado e copie o valor de `client_email`
2. Abra sua planilha do Google Sheets
3. Clique em **"Share"**
4. Cole o email e adicione como **Editor**

#### 4.4 Configurar secrets

```bash
# Copiar template de secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Editar .streamlit/secrets.toml e preencher com dados do JSON
# Exemplo:
# [gcp_service_account]
# type = "service_account"
# project_id = "seu-projeto-id"
# private_key_id = "..."
# private_key = "..."
# client_email = "..."
# ...
#
# sheet_name = "Finanças Pessoais"
```

⚠️ **IMPORTANTE:** Nunca commitar `.streamlit/secrets.toml` — está no `.gitignore`

### Passo 5: Rodar localmente

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

### Passo 6: Criar primeiro usuário (opcional)

```bash
python scripts/add_user.py
# Siga os prompts para username, nome e senha
```

---

## ✨ Funcionalidades Principais

### 1. 📊 Dashboard

**Objetivo:** Oferecer visão consolidada das finanças no período selecionado.

**Seções:**

#### 1.1 Filtros
- Seleção de **ano(s)** e **mês(es)** com multiselect
- Filtros sincronizados globalmente em `st.session_state`

#### 1.2 Visão Geral (KPI Cards)
Quatro cards principais com informações resumidas:

| Card | Métrica | Cálculo | Subtítulo |
|---|---|---|---|
| 💰 Entradas | Ganhos líquidos + créditos | Soma de `valor_liquido` + créditos | Acumulado no ano + sparkline |
| 📉 Saídas | Débitos + parcelas de cartão | Soma de débitos + cartão | Acumulado no ano + sparkline |
| 💵 Saldo | Entradas - Saídas | Cálculo em tempo real | Cor verde/vermelha conforme sinal |
| 💳 Fatura Cartão | Parcelas do mês | Soma de `valor_parcela` | Peso percentual nas saídas |

Cada card exibe:
- Valor principal em BRL formatado
- Sparkline de tendência mensal (12 meses)
- Indicador visual (ícone + cor)

#### 1.3 Fluxo de Dinheiro
Análise de receitas e despesas por categoria em duas colunas:

**À esquerda: Entradas por Tipo**
- Agrupamento por `tipo_ganho` (Salário, Investimento, etc.)
- Barra proporcional ao total
- Percentual relativo

**À direita: Saídas por Categoria**
- Débitos manuais por categoria
- Parcelas de cartão por categoria
- Expansível para ver detalhes (descrição, forma de pagamento, etc.)

#### 1.4 Capacidade de Gasto (Regra 50/30/20)
Análise baseada na metodologia de alocação de renda:

| Bucket | % | Limite | Cálculo |
|---|---|---|---|
| 🏠 Necessidades | 50% | 50% da renda líquida | Inclui moradia, transporte, saúde, etc. |
| 😊 Desejos | 30% | 30% da renda líquida | Lazer, vestuário, restaurantes, etc. |
| 🏦 Poupança | 20% | 20% da renda líquida | O que sobra de necessidades e desejos |

**Exibição:**
- Barras de progresso com gasto atual vs. limite
- Capacidade restante em BRL
- Capacidade diária restante (até fim do mês)
- Cor de alerta quando ultrapassado

#### 1.5 Tendências do Ano
Análise consolidada de 12 meses com gráficos:

- **Gráfico de linha** — Evolução de entradas, saídas e saldo ao longo dos meses
- **KPIs resumidos** — Total anual, média mensal, mês mais positivo, etc.
- **Heatmap opcional** — Visualizar meses positivos/negativos

---

### 2. 💸 Ganhos

**Objetivo:** Cadastrar e gerenciar todas as formas de receita.

**Tipos de ganho suportados:**

#### 2.1 Salário
O tipo mais rico, com cálculos automáticos de impostos:

**Campos:**
- Salário bruto
- Número de dependentes (para IRRF)
- Outros descontos (vale refeição, convênio médico, etc.)

**Cálculos automáticos:**
- **INSS** — Alíquota progressiva conforme tabela 2025
  - Faixa 1: até R$ 1.518,00 → 7,5%
  - Faixa 2: até R$ 2.793,88 → 9%
  - Faixa 3: até R$ 4.190,83 → 12%
  - Faixa 4: até R$ 8.157,41 → 14%
  - Teto: R$ 908,86
- **IRRF** — Alíquota progressiva com deduções por dependente
- **Salário líquido** — Bruto - INSS - IRRF - outros descontos

**Recursos especiais:**
- Tabelas interativas de INSS e IRRF expandíveis
- Opção "Replicar para o ano inteiro" — copia o salário para todos os 12 meses
- Histórico de salários registrados com ações de editar/excluir

#### 2.2 Investimento
Para registrar rendimentos de investimentos:

**Campos:**
- Tipo de investimento (Renda Fixa, Ações, FII, Cripto, etc.)
- Onde está investido (instituição/corretora)
- Valor investido (principal)
- Rendimento (o que entra como receita)

**Nota:** O valor considerado como ganho é o **rendimento**, não o capital.

#### 2.3 Aluguel
Para proprietários/locadores:

**Campos:**
- Imóvel/Endereço
- Valor do aluguel

#### 2.4 Freelance
Para trabalhos autônomos/projetos:

**Campos:**
- Cliente/Projeto
- Valor recebido

#### 2.5 Outros
Ganhos que não se encaixam nas categorias acima:

**Campos:**
- Descrição
- Valor
- Observação (opcional)

**Listagem e edição:**
- Todos os ganhos filtrados por ano/mês selecionado
- Ações de editar, visualizar detalhes, excluir
- Indicador visual por tipo (ícone + cor)

---

### 3. 📝 Lançamentos

**Objetivo:** CRUD completo de transações manuais (créditos e débitos).

**Campos principais:**

| Campo | Tipo | Exemplo |
|---|---|---|
| Ano/Mês | Seletor | 2026 / Maio |
| Tipo | Radio | Débito ou Crédito |
| Categoria | Multiselect dinâmico | "Moradia", "Restaurante", etc. |
| Descrição | Text input | "Conta de luz", "Venda de notebook" |
| Forma de pagamento | Seletor | Pix, Boleto, TED, Cartão débito |
| Valor | Input | "R$ 150,00" com parsing automático |

**Validações:**
- Todos os campos obrigatórios antes de salvar
- Valor deve ser numérico positivo
- Categoria deve estar na lista pré-definida

**Recorrência (experimental):**
- Opção para criar lançamento recorrente até mês/ano especificado
- Cria registros para cada mês no intervalo
- Marcação de grupo para edição em lote

**Listagem:**
- Tabela filtrável por período
- Totalizadores (soma de créditos, débitos, saldo)
- Ações por linha (editar, excluir, duplicar)
- Busca por descrição (opcional)

---

### 4. 💳 Cartão de Crédito

**Objetivo:** Controlar compras parceladas e gerenciar múltiplos cartões.

Dividido em duas abas: **Compras & Fatura** e **Meus Cartões**.

#### 4.1 Compras & Fatura

**Filtros:**
- Seleção de cartão (individual ou "Todos")
- Filtro de ano e mês

**KPIs:**

| KPI | Significado | Fórmula |
|---|---|---|
| 💰 Fatura do Mês | Parcelas vencendo agora | SUM(parcelas WHERE mes == selecionado) |
| 📊 Limite Utilizado | % do limite do cartão | fatura / limite |
| 🛍️ Compras em Aberto | Quantidade de compras ainda não pagas | COUNT(compras WHERE ultima_parcela > agora) |
| 📅 Comprometido 6M | Valor que será gasto nos próx. 6 meses | SUM(parcelas próx. 6 meses) |

**Formulário de compra parcelada:**

Campos:
- Cartão (seletor)
- Categoria (dinâmica conforme banco de dados)
- Descrição
- Valor total
- Número de parcelas
- Mês/Ano de início

Cálculos em tempo real:
- Valor por parcela = valor_total / num_parcelas
- Mês final = mes_inicio + num_parcelas - 1
- Validação automática (não permitir parcelas em meses passados)

**Listagem de parcelas do mês:**

Tabela com:
- Descrição da compra
- Cartão (com cor de código)
- Valor da parcela
- Valor total (original)
- Fração (parcela atual / total)
- Categoria (ícone + nome)
- Ações (editar, excluir)

**Projeção de 6 meses:**

Gráfico de barras empilhadas mostrando:
- Eixo X: Próximos 6 meses
- Eixo Y: Valor em BRL
- Série: Um cartão por cor
- Hover: Detalhes das compras daquele mês

#### 4.2 Meus Cartões

**Cadastro de cartão:**

Campos:
- Banco/Bandeira (seletor com 20+ bancos brasileiros)
- Últimos 4 dígitos (validação de entrada)
- Limite de crédito em BRL
- Dia de vencimento (1-31)
- Apelido (opcional)

**Cor automática:**

Cada banco tem cor pré-definida no dicionário `CARTOES_CORES`:
- Nu → Roxo
- Itaú → Azul
- Bradesco → Vermelho
- Inter → Laranja
- etc.

**Visualização:**

Cards com design de cartão real:
- Gradiente baseado na cor do banco
- Nome do cartão em destaque
- 4 dígitos criptografados (últimos dígitos)
- Limite exibido
- Dia de vencimento
- Ações (editar, excluir)

**Comportamento ao deletar:**

Ao remover um cartão, o sistema automaticamente:
1. Exclui todas as compras vinculadas
2. Remove a configuração do cartão
3. Atualiza dados no Google Sheets

⚠️ **Cuidado:** Essa operação é irreversível — não há soft-delete.

---

### 5. 📊 Extrato

**Objetivo:** Consolidar todas as transações em uma única view filtrável e exportável.

**Filtros:**

- **Ano** — seleção única
- **Mês(es)** — multiselect (permite múltiplos meses)
- **Tipo** — multiselect com opções:
  - Entrada
  - Saída
  - Cartão
  - Ganho
- **Categoria** — multiselect dinâmico conforme banco de dados

**KPIs resumidos (topo):**

| KPI | Cálculo |
|---|---|
| Ganhos | SUM(ganhos_liquidos) no período |
| Entradas | SUM(créditos_manuais) no período |
| Saídas | SUM(débitos_manuais) no período |
| Cartão | SUM(parcelas_de_cartao) no período |
| Saldo | Ganhos + Entradas - Saídas - Cartão |

**Tabela consolidada:**

Colunas:
- Data (ano-mês para agrupamento visual)
- Descrição
- Tipo (com ícone e cor)
- Categoria
- Valor (em BRL, formatado)
- Forma de pagamento (quando aplicável)

Ordenação:
- Padrão: data decrescente (mais recente primeiro)
- Agrupamento visual: por mês

**Exportação:**

Botão "📥 Exportar como CSV" que:
- Gera arquivo com dados filtrados
- Nomeado com padrão `extrato_YYYYMM_YYYYMM.csv`
- Formatação: ponto decimal em número, vírgula em separador

---

### 6. 🎯 Metas

**Objetivo:** Estabelecer objetivos de economia e acompanhar o progresso.

**Tipos de meta:**

| Tipo | Ícone | Exemplo |
|---|---|---|
| 💰 Economia | 💰 | "Juntar R$ 5000 em 6 meses" |
| 🏠 Imóvel | 🏠 | "Dar entrada em imóvel" |
| ✈️ Viagem | ✈️ | "Viajar para Europa" |
| 🎓 Educação | 🎓 | "Fazer curso de especialização" |
| 🚗 Veículo | 🚗 | "Comprar carro novo" |
| 💍 Pessoal | 💍 | "Casamento" |
| 📱 Eletrônico | 📱 | "Novo smartphone" |

**Campos de uma meta:**

| Campo | Tipo | Obrigatório |
|---|---|---|
| Nome | Text | ✅ |
| Tipo | Select | ✅ |
| Valor alvo | Numérico | ✅ |
| Valor atual | Numérico | ✅ |
| Data limite | Data ou "Sem prazo" | ✅ |
| Cor identificadora | Cor | ✅ |
| Descrição | Text longo | ❌ |

**Visualização de metas:**

Cards com design moderno:
- Ícone do tipo em destaque
- Nome e tipo da meta
- Barra de progresso visual (0-100%)
- Valor atual e valor alvo lado a lado
- Percentual de conclusão
- Badge de status (on track, warning, concluído)
- Cálculo de "por dia" quando há prazo definido

**Acompanhamento:**

- Listagem com filtros por status (em progresso, concluído, atrasada)
- Gráfico consolidado de progresso de todas as metas
- KPIs: total em metas, % médio de progresso, projeção de conclusão
- Ações por meta: editar valor atual, editar meta, marcar como concluída, excluir

---

### 7. 📈 Relatórios

**Objetivo:** Gerar relatórios avançados e exportáveis em múltiplos formatos.

**Tipos de relatório:**

#### 7.1 Relatório Mensal
Resumo de um mês específico com:
- Fluxo de caixa (entradas vs saídas)
- Comparação com meses anteriores
- Gráficos por categoria
- Tabela de transações
- Recomendações (opcional)

**Exportação:** PDF, CSV, JSON

#### 7.2 Relatório Anual
Análise de todo o ano com:
- Comparação mês a mês
- Evolução mensal de receitas/despesas
- Gráfico de metas alcançadas
- Resumo por categoria (anualizado)
- Indicadores financeiros (poupança %, dívida %, etc.)

**Exportação:** PDF, Excel, JSON

#### 7.3 Relatório Comparativo
Comparação entre múltiplos períodos:
- Seleção de períodos a comparar
- Gráficos lado a lado
- Variação percentual
- Tendências

#### 7.4 Relatório de Investimentos
Análise específica de investimentos:
- Rendimento total
- Rendimento por tipo
- Performance vs. inflação
- Recomendações de realocação

**Geração de PDF:**

Utiliza `utils/pdf_report.py` com:
- Logo da aplicação
- Período do relatório
- Gráficos embutidos
- Tabelas formatadas
- Assinatura digital (hash do arquivo)

---

### 8. 📥 Importador de CSV

**Objetivo:** Importar transações de extratos bancários automaticamente.

**Bancos suportados:**

- **Nubank** (crédito e conta corrente)
- **Banco Inter**
- **Itaú**
- **Bradesco**
- **C6 Bank**

**Fluxo de importação:**

1. **Upload do arquivo** — seletor de arquivo CSV
2. **Detecção automática** — identifica banco pela estrutura do cabeçalho
3. **Pré-visualização** — mostra primeiras linhas com mapeamento
4. **Mapeamento de colunas** — usuário confirma quais colunas usar
5. **Classificação de categorias** — sistema sugere categoria para cada transação
6. **Review e confirmação** — revisar transações antes de importar
7. **Importação** — gravar no banco de dados

**Recursos inteligentes:**

- **Auto-mapper de categorias** — usa palavras-chave para sugerir categoria correta
  - Ex: "Netflix" → "Streaming"
  - Ex: "Uber" → "Transporte"
  - Ex: "Supermercado" → "Subsistência"

- **Deduplicação** — detecta transações já importadas para evitar duplicatas
  - Usa hash de (data + descrição + valor)

- **Forma de pagamento** — infere tipo de transação (débito, crédito, TED, etc.)

- **Tratamento de moeda** — converte se necessário (R$, USD, etc.)

**Limitações atuais:**

- Não detecta automaticamente cartão de crédito em extrato bancário
- Não reconcilia com lançamentos manuais automaticamente
- OFX suportado apenas parcialmente

---

### 9. ⚙️ Configurações

**Objetivo:** Painel de customização e ajustes do aplicativo.

**Seções:**

#### 9.1 Perfil do Usuário
- Nome
- Avatar (emoji ou foto)
- Cor identificadora
- Email (opcional)

#### 9.2 Preferências Financeiras
- Regra de alocação (50/30/20 customizável)
  - % necessidades
  - % desejos
  - % poupança
- Moeda principal (BRL configurado como padrão)
- Data de início do ano fiscal

#### 9.3 Categorias Personalizadas
- Gerenciar lista de categorias de débito
- Gerenciar lista de categorias de crédito
- Adicionar/remover/renomear

#### 9.4 Notificações
- Alerta de limite de gasto ultrapassado
- Alerta de meta alcançada
- Notificações de transações grandes

#### 9.5 Segurança
- **Alterar senha**: Acesse Configurações > 🔐 Senha para definir ou alterar sua senha. Senhas são opcionais e devem ter pelo menos 6 caracteres. Perfis sem senha permitem acesso direto.
- Ativar autenticação de dois fatores (2FA) — planejado
- Ver dispositivos/sessões ativas
- Logout de todas as sessões

#### 9.6 Dados
- Backup manual
- Exportar todos os dados (JSON/CSV)
- Deletar conta e dados permanentemente

---

## 📦 Estrutura de Dados

### 1. Lançamentos

Tabela: `lancamentos` no Google Sheets

```python
{
    "id": 1,                          # Auto-incrementado
    "username": "pedro",              # Identificador do usuário
    "ano": 2026,
    "mes": 5,
    "descricao": "Conta de luz",
    "categoria": "Conta",
    "tipo": "Débito",                 # Débito ou Crédito
    "forma_pagamento": "Pix",         # Pix, Boleto, TED, Cartão débito, etc.
    "valor": 150.50,
    "grupo_id": null                  # Para recorrências futuras
}
```

### 2. Ganhos

Tabela: `ganhos` no Google Sheets

```python
{
    "id": 1,
    "username": "pedro",
    "ano": 2026,
    "mes": 5,
    "tipo_ganho": "Salário",          # Salário, Investimento, Aluguel, Freelance, Outros
    "descricao": "Salário Maio",
    "valor_liquido": 4500.00,
    "extras": {                       # JSON string com info extra
        "bruto": 5500.00,
        "inss": 687.50,
        "irrf": 312.50,
        "descontos": 0.00,
        "dependentes": 0,
        "tipo_inv": "Renda Fixa",     # Para investimentos
        "local_inv": "Nubank",
        "valor_principal": 10000.00
    }
}
```

### 3. Compras de Cartão

Tabela: `cartao_compras` no Google Sheets

```python
{
    "id": 1,
    "username": "pedro",
    "cartao": "1",                    # ID do cartão configurado
    "descricao": "PlayStation 5",
    "categoria": "Eletrônicos",
    "valor_total": 3000.00,
    "num_parcelas": 12,
    "ano_inicio": 2026,
    "mes_inicio": 5,
    "data_registro": "2026-05-15"     # Para ordenação
}
```

**Cálculos derivados:**
- `valor_parcela` = `valor_total` / `num_parcelas`
- `mes_final` = `mes_inicio` + `num_parcelas` - 1
- `parcelas` = lista de `{mes, ano, valor_parcela}` para cada mês

### 4. Configuração de Cartões

Tabela: `cartao_config` no Google Sheets

```python
{
    "id": 1,
    "username": "pedro",
    "nome": "Nubank",
    "digitos": "1234",                # Últimos 4 dígitos
    "limite": 5000.00,
    "vencimento": 10,                 # Dia do mês
    "cor": "#FF00FF"                  # Cor identificadora
}
```

### 5. Metas

Tabela: `metas` (JSON local)

```python
{
    "id": 1,
    "username": "pedro",
    "nome": "Viagem para Europa",
    "tipo": "viagem",                 # Enum: economia, imovel, viagem, educacao, veiculo, pessoal, eletronico
    "valor_alvo": 15000.00,
    "valor_atual": 3500.00,
    "data_limite": "2026-12-31",      # ou null para "sem prazo"
    "cor": "#FF9F0A",
    "descricao": "Aproveitar Black Friday para comprar passagens",
    "criada_em": "2026-01-15",
    "atualizada_em": "2026-05-10",
    "concluida": false
}
```

### 6. Perfis de Usuário

Tabela: `perfis` no Google Sheets

```python
{
    "username": "pedro",
    "nome": "Pedro Silva",
    "avatar": "💰",                   # Emoji ou URL
    "cor": "#0A84FF"                  # Cor da conta
}
```

### 7. Configuração do Usuário

Tabela: `user_config` no Google Sheets

```python
{
    "username": "pedro",
    "necessidades": 50,               # % da renda para necessidades (padrão 50)
    "desejos": 30,                    # % da renda para desejos (padrão 30)
    "poupanca": 20                    # % da renda para poupança (padrão 20)
}
```

### 8. Histórico de Auditoria

Tabela: `historico` no Google Sheets (estrutura preparada)

```python
{
    "id": 1,
    "username": "pedro",
    "timestamp": "2026-05-10T14:30:00",
    "entidade": "lancamento",         # lancamento, ganho, cartao, etc.
    "operacao": "create",             # create, update, delete
    "registro_id": 123,
    "snapshot": "{...}"               # JSON do estado anterior
}
```

---

## 🔄 Fluxos de Negócio

### Fluxo 1: Registrar Ganho Mensal

```
1. Usuário acessa "Ganhos"
2. Seleciona tipo "Salário"
3. Insere salário bruto e dependentes
4. Sistema calcula INSS e IRRF automaticamente
5. Exibe salário líquido
6. Usuário clica "Salvar"
7. Registro gravado em Google Sheets
8. Sucesso: Dashboard atualiza automaticamente
```

**Atores envolvidos:**
- `views/ganhos.py` — Interface
- `storage.py` — Persistência
- `utils/helpers.py` — Cálculos INSS/IRRF

---

### Fluxo 2: Fazer Compra Parcelada

```
1. Usuário acessa "Cartão" → "Compras & Fatura"
2. Preenche formulário:
   - Cartão: "Nubank"
   - Categoria: "Eletrônicos"
   - Descrição: "Notebook"
   - Valor: R$ 3000
   - Parcelas: 12
3. Sistema valida e mostra preview
4. Usuário confirma
5. 12 registros de parcelas criados no banco
6. Dashboard atualiza com novas projeções
7. Fatura do mês aumenta com primeira parcela
```

**Atores envolvidos:**
- `views/cartao.py` — Interface
- `storage.py` — CRUD de compras e cálculo de parcelas
- `utils/charts.py` — Gráficos de projeção

---

### Fluxo 3: Importar Extrato do Banco

```
1. Usuário acessa "Importar"
2. Faz upload de CSV
3. Sistema detecta banco (ex: Nubank)
4. Usuário revisa mapeamento de colunas
5. Sistema sugere categorias para cada transação
6. Usuário revisa e confirma
7. Sistema deduplica (verifica se já existe)
8. Transações importadas para Google Sheets
9. Dashboard atualiza em tempo real
10. Mensagem de sucesso com quantidade importada
```

**Atores envolvidos:**
- `views/importar.py` — Interface
- `importers/csv_importer.py` — Parse e detecção
- `importers/category_matcher.py` — Sugestão de categoria
- `storage.py` — Persistência

---

### Fluxo 4: Acompanhar Meta de Economia

```
1. Usuário cria meta "Viagem" com valor alvo R$ 15.000
2. A cada transação de crédito/ganho, valor é adicionado à meta
3. Dashboard exibe progresso em card específico
4. Quando atinge 100%, exibe badge "Concluída"
5. Notificação opcional ao atingir 80%, 100%
6. Relatório mensal inclui metas progredidas
```

**Atores envolvidos:**
- `views/metas.py` — Interface
- `data/metas_storage.py` — Persistência local
- `utils/charts.py` — Visualização de progresso

---

## 👥 Sistema Multi-Usuário

O aplicativo foi redesenhado para suportar múltiplos usuários isolados por dados.

### Autenticação

**Mecanismo:** Sistema de perfis com senhas opcionais usando bcrypt

**Fluxo:**

```
1. Usuário acessa app
2. Se não logado → tela de seleção de perfis
3. Usuário seleciona perfil
4. Se perfil tem senha → prompt para senha
5. Validação com bcrypt contra hash armazenado
6. Se válido ou sem senha → `st.session_state.username` definido
7. App rerun → carrega dados do usuário
```

**Armazenamento:** Senhas hasheadas na tabela `perfis` do Google Sheets

```python
# Estrutura da tabela perfis
{
    "username": "pedro",
    "nome": "Pedro Silva",
    "avatar": "💰",
    "cor": "#0A84FF",
    "password": "$2b$12$...hashedbcrypt..."  # Opcional
}
```

**Requisitos de senha:**
- Mínimo 6 caracteres
- Opcional (perfis sem senha permitem acesso direto)
- Alterável em Configurações > 🔐 Senha ou Gerenciar Perfis
  key: CHAVE_SECRETA_ALEATORIA_MINIMO_64_CHARS
  expiry_days: 30
```

⚠️ **NUNCA** commitar esse arquivo — está no `.gitignore`

### Isolamento de Dados

Toda função de armazenamento recebe `username` como parâmetro:

```python
# storage.py
def get_lancamentos(username: str) -> pd.DataFrame:
    """Retorna lançamentos apenas deste usuário."""
    recs = _cached_records("lanc") or []
    df = pd.DataFrame(recs)
    if df.empty:
        return df[COLS_LANC]
    return df[df["username"] == username][COLS_LANC]
```

### Injeção de Dependência

Nas views, o pattern `functools.partial` injeta `username` automaticamente:

```python
# views/dashboard.py
def show_dashboard(username: str):
    # Injetar username em todas as funções
    import functools as _ft
    from data import storage as _st
    
    get_lancamentos     = _ft.partial(_st.get_lancamentos, username)
    add_lancamento      = _ft.partial(_st.add_lancamento, username)
    # ... resto do código usa get_lancamentos() sem passar username
```

### Perfis Customizáveis

Cada usuário tem perfil com avatar, nome e cor:

```python
# Stored in Google Sheets
{
    "username": "pedro",
    "nome": "Pedro Silva",
    "avatar": "💰",
    "cor": "#0A84FF"
}
```

Personaliza a UI (cor da sidebar, avatar no header).

---

## 🎨 Módulos Detalhados

### utils/color.py

Conversão bidirecional entre formatos de cor.

```python
def to_rgba(color: str, alpha: float = 0.1) -> str:
    """
    Converte hex (#RRGGBB) ou rgb/rgba() para rgba com alpha ajustável.
    
    Args:
        color: "#FF0000" ou "rgb(255,0,0)" ou "rgba(255,0,0,0.5)"
        alpha: Valor de transparência (0.0 - 1.0)
    
    Returns:
        "rgba(R,G,B,A)"
    """
```

Usado em gráficos para criar desgradês e transparências.

### utils/charts.py

Funções reutilizáveis de gráficos Plotly.

```python
def spark(vals: list, color: str, height: int = 48) -> go.Figure:
    """Cria sparkline (mini gráfico de linha)."""

def bar_mensal(dados: list, labels: list, cores: list, title: str) -> go.Figure:
    """Gráfico de barras mensal."""

def donut(labels: list, values: list, hole: float = 0.4) -> go.Figure:
    """Gráfico de rosca."""

def linha_acumulada(meses: list, valores: list, color: str) -> go.Figure:
    """Gráfico de linha com preenchimento acumulado."""
```

### utils/helpers.py

Funções auxiliares de formatação e parsing.

```python
def brl(valor: float) -> str:
    """Formata número para BRL.
    
    1500.5 → "R$ 1.500,50"
    """

def _parse_brl(s: str) -> float:
    """Parse reverso de BRL para float.
    
    "R$ 1.500,50" → 1500.5
    """

def pbg(cor_hex: str) -> str:
    """Padding de background — cria estilo CSS."""

MESES_PT = {1: "Janeiro", 2: "Fevereiro", ...}
MESES_ABR = {1: "Jan", 2: "Fev", ...}
CARTOES_CORES = {"Nubank": "#820AD1", "Itau": "#0066CC", ...}
```

### utils/tokens.py

Design tokens centralizados.

```python
CORES = {
    "positivo": "#30D158",      # Verde
    "negativo": "#FF453A",      # Vermelho
    "neutro": "#8E8E93",        # Cinza
    "secundario": "#0A84FF",    # Azul
    "estrutura": "rgba(...)",
    "texto": "rgba(...)",
}

CORES_CAT = ["#FF453A", "#0A84FF", "#ffa657", ...]  # Cores para categorias
```

### utils/pdf_report.py

Gerador de relatórios em PDF.

```python
def gerar_pdf_mensal(username: str, ano: int, mes: int) -> bytes:
    """Gera PDF com relatório mensal."""

def gerar_pdf_anual(username: str, ano: int) -> bytes:
    """Gera PDF com relatório anual."""
```

Usa `reportlab` para layout profissional com gráficos embutidos.

### data/storage.py

Camada de persistência com Google Sheets.

**Padrão:**

```python
def get_<entidade>(username: str) -> pd.DataFrame:
    """Busca todos os registros da entidade para o usuário."""

def add_<entidade>(username: str, **dados) -> tuple[bool, str]:
    """Cria novo registro. Retorna (sucesso, mensagem_erro)."""

def update_<entidade>(username: str, id: int, **dados) -> tuple[bool, str]:
    """Atualiza registro existente."""

def delete_<entidade>(username: str, id: int) -> tuple[bool, str]:
    """Deleta registro por ID."""
```

**Cache:**

- `@st.cache_data(ttl=60)` para leitura de dados
- `@st.cache_resource(ttl=600)` para conexão Google Sheets

**Rate limiting:**

Retry automático com backoff exponencial quando API retorna 429 (Too Many Requests).

### data/metas_storage.py

Persistência local de metas (JSON na pasta `data/`).

```python
def get_metas(username: str) -> list[dict]:
    """Carrega metas do usuário."""

def add_meta(username: str, nome: str, tipo: str, valor_alvo: float, ...) -> bool:
    """Cria nova meta."""

def update_meta_valor_atual(username: str, meta_id: int, novo_valor: float) -> bool:
    """Atualiza valor atual (progresso)."""
```

### importers/csv_importer.py

Parser multi-banco com detecção automática.

```python
def _detect_bank(header: str, sample: str) -> str | None:
    """Detecta banco pelo padrão do cabeçalho."""

def parse_nubank_credito(df: pd.DataFrame) -> list[dict]:
    """Parse específico para extrato de crédito Nubank."""

def parse_nubank_conta(df: pd.DataFrame) -> list[dict]:
    """Parse específico para extrato de conta corrente Nubank."""

# ... mais parse_*
```

### importers/category_matcher.py

Mapeamento automático de transações para categorias.

```python
def sugerir_categoria(descricao: str) -> str:
    """
    Sugere categoria baseada em palavras-chave.
    
    "Netflix" → "Streaming"
    "Supermercado Carrefour" → "Subsistência"
    "Ginásio" → "Lazer"
    """

def sugerir_forma_pagamento(descricao: str, headers: list) -> str:
    """Sugere forma de pagamento conforme descrição e contexto."""
```

Usa dicionário de padrões regex e lista de stopwords.

---

## ⚙️ Configurações e Customização

### config.py

Centraliza configurações aplicáveis globalmente.

```python
USUARIO_NOME = "Pedro"              # Nome padrão (usado em fallback)
USUARIO_AVATAR = "P"                # Avatar padrão
APP_TITULO = "Finanças Pessoais"   # Título na aba do navegador
APP_ICONE = "📈"                    # Ícone da página

ANO_MINIMO = 2025                   # Ano mínimo no seletor

# Regra 50/30/20
LIMITE_NECESSIDADES = 0.50
LIMITE_DESEJOS = 0.30
LIMITE_POUPANCA = 0.20

# Categorias por bucket
CATEGORIAS_NECESSIDADES = ["Moradia", "Subsistência", "Transporte", ...]
CATEGORIAS_DESEJOS = ["Lazer", "Vestuário", "Streaming", ...]
```

### .streamlit/config.toml

Configuração do Streamlit (tema, layout, etc.).

```toml
[theme]
base = "dark"
primaryColor = "#0A84FF"
backgroundColor = "#000000"
secondaryBackgroundColor = "#1C1C1E"
textColor = "#EBEBF5"

[client]
maxUploadSize = 200  # MB

[logger]
level = "info"
```

### .env

Variáveis de ambiente (local).

```
FIN_USER_NAME=Pedro
FIN_APP_TITLE=Finanças Pessoais
DEBUG=False
LOG_LEVEL=INFO
```

### auth_config.yaml

Configuração de autenticação (não versionado, secreto).

```yaml
credentials:
  usernames:
    pedro:
      name: Pedro Silva
      password: $2b$12$...bcrypt_hash...

cookie:
  name: fin_auth
  key: CHAVE_MUITO_LONGA_E_ALEATORIA_MIN_64_CHARS
  expiry_days: 30
```

---

## ⚠️ Limitações Conhecidas

### 1. **Performance com Google Sheets**

- **Problema:** API do Google Sheets tem limite de 300 requisições/min/user
- **Impacto:** Com muitos usuários simultâneos, pode haver throttling (erro 429)
- **Solução atual:** Cache automático com retry exponencial
- **Solução futura:** Migrar para PostgreSQL/Firebase Realtime Database

### 2. **Sem offline-first**

- **Problema:** Aplicação exige conexão com internet sempre
- **Impacto:** Não funciona sem internet
- **Solução futura:** Implementar sincronização local com IndexedDB (PWA)

### 3. **Soft-delete não implementado**

- **Problema:** Deletar cartão remove todas as compras associadas
- **Impacto:** Histórico é perdido permanentemente
- **Solução futura:** Implementar soft-delete com `deleted_at` timestamp

### 4. **Importador de OFX parcialmente implementado**

- **Problema:** Parser OFX está estruturado mas sem testes
- **Impacto:** Bancos OFX não funcionam confiávelmente
- **Solução futura:** Adicionar testes e suportar mais bancos

### 5. **2FA não implementado**

- **Problema:** Apenas senha, sem segundo fator
- **Impacto:** Segurança limitada
- **Solução futura:** Integrar TOTP via QR code

### 6. **Categorias hardcoded**

- **Problema:** Lista de categorias está em `storage.py`
- **Impacto:** Adicionar categoria requer alteração de código
- **Solução futura:** Interface na "Configurações" para gerenciar categorias

### 7. **Relatórios básicos**

- **Problema:** PDF gerado é simples, sem dados muito complexos
- **Impacto:** Análises avançadas exigem exportar e processar externamente
- **Solução futura:** Adicionar mais tipos de relatório (comparativo, benchmark, etc.)

### 8. **Mobile experience aprimorada**

- **Impacto:** A interface agora oferece melhor usabilidade em smartphone
- **Melhoria aplicada:** Barra lateral compacta em telas menores, formulários com largura total e gráficos adaptados em cards empilhados
- **Limitação atual:** Alguns componentes muito largos, como tabelas extensas ou grids complexos, podem exigir scroll horizontal em celulares pequenos
- **Próximo passo:** Top nav móvel e PWA/mobile native no roadmap

### 9. **Sem integração bancária direta**

- **Problema:** Precisa fazer upload de CSV manualmente
- **Impacto:** Sem sincronização automática de transações
- **Solução futura:** Integrar com APIs abertas (Open Banking)

### 10. **Compartilhamento de dados limitado**

- **Problema:** Múltiplos usuários não compartilham dados (isolamento total)
- **Impacto:** Casal precisa de solução alternativa para dados conjuntos
- **Solução futura:** Implementar "contas conjuntas" com permissões

---

## 🚀 Futuras Evoluções

### Curto Prazo (1-2 meses)

#### 1.1 **Melhorias de UX**
- [ ] Dark mode mais consistente
- [ ] Animações de transição
- [ ] Tooltips informativos
- [ ] Modo mobile otimizado

#### 1.2 **Mais bancos no importador**
- [ ] Santander
- [ ] Caixa Econômica Federal
- [ ] Banco do Brasil
- [ ] BNDES
- [ ] Corretoras (renda variável)

#### 1.3 **Relatórios aprimorados**
- [ ] Comparação ano-a-ano
- [ ] Análise de tendências
- [ ] Projeções de fluxo de caixa
- [ ] Insights automáticos com IA

### Médio Prazo (3-6 meses)

#### 2.1 **Segurança avançada**
- [ ] 2FA (TOTP)
- [ ] Biometria (fingerprint)
- [ ] Audit log completo
- [ ] Encryption at-rest para dados sensíveis

#### 2.2 **Compartilhamento e colaboração**
- [ ] Contas conjuntas (casal/família)
- [ ] Permissões granulares (leitura, escrita, admin)
- [ ] Histórico de quem editou o quê
- [ ] Notificações em tempo real para mudanças

#### 2.3 **Automação**
- [ ] Regras de categorização automática
- [ ] Alertas customizáveis (limite, meta, etc.)
- [ ] Agendamento de lançamentos recorrentes
- [ ] Webhooks para integrações externas

#### 2.4 **Integração bancária aberta**
- [ ] Open Banking (PIX, API's bancárias)
- [ ] Sincronização automática de transações
- [ ] Reconciliação automática

### Longo Prazo (6-12 meses)

#### 3.1 **Inteligência Artificial**
- [ ] Recomendações de economia
- [ ] Detecção de anomalias/fraude
- [ ] Classificação automática com NLP
- [ ] Chatbot de dúvidas financeiras

#### 3.2 **Análise avançada**
- [ ] Análise de padrões de gastos
- [ ] Previsão de fluxo de caixa (ML)
- [ ] Simulação de cenários
- [ ] Benchmark com média nacional

#### 3.3 **Integração com APIs externas**
- [ ] CVM (dados de fundos/ações)
- [ ] Receita Federal (IR, refil automático)
- [ ] Inflationário (IPCA, IGP-M)
- [ ] Corretor automático de carteiras

#### 3.4 **App nativo**
- [ ] iOS app (React Native ou Swift)
- [ ] Android app (React Native ou Kotlin)
- [ ] Sincronização em tempo real
- [ ] Notificações push

#### 3.5 **Plataforma B2B**
- [ ] SaaS multi-tenancy completo
- [ ] Gestão de despesas empresariais
- [ ] Relatórios para departamento financeiro
- [ ] Integração com ERP

---

## 🔧 Troubleshooting

### Problema: "Auth config not found"

**Causa:** `auth_config.yaml` não existe ou não foi encontrado.

**Solução:**

```bash
python scripts/add_user.py
# Siga o prompt para criar o primeiro usuário
```

### Problema: "Error 429: Too Many Requests"

**Causa:** Atingiu limite de API do Google Sheets (300 req/min/user).

**Solução:**

1. Aguardar alguns minutos (cache ajuda)
2. Usar menos multiselects/filtros
3. Implementar batching em grandes operações

Futuro: Migrar para banco de dados com limite maior.

### Problema: "ValueError: invalid literal for int() with base 16"

**Causa:** Função de conversão de cor recebeu formato inesperado.

**Solução:**

Verificar se `to_rgba()` está sendo usada em lugar de função antiga.

```python
# ❌ Errado (função antiga)
cor_rgba = _hex_to_rgba(cor_hex)

# ✅ Correto
from utils.color import to_rgba
cor_rgba = to_rgba(cor_hex, alpha=0.1)
```

### Problema: "Sheet not found: Finanças Pessoais"

**Causa:** Nome da planilha não coincide com config.

**Solução:**

1. Verificar se planilha existe no Google Drive
2. Confirmar nome exato (case-sensitive em alguns casos)
3. Verificar se Service Account tem permissão

```bash
# Em .streamlit/secrets.toml:
[gcp_service_account]
# ... dados do JSON

sheet_name = "Finanças Pessoais"  # ← Exatamente assim
```

### Problema: Dados desapareceram após deletar usuário

**Causa:** Não há soft-delete implementado — exclusão é permanente.

**Solução:**

1. Não há solução no app
2. Recuperar do backup do Google Sheets (versões anteriores)
3. Implementar soft-delete no futuro

### Problema: Importador não reconhece banco

**Causa:** Estrutura do CSV não corresponde aos padrões conhecidos.

**Solução:**

1. Verificar cabeçalho do CSV
2. Se banco é suportado, ajustar formatação para padrão esperado
3. Se banco não é suportado, abrir issue no GitHub

Padrões suportados:
- Nubank: `date, title, amount, category`
- Itaú: `data, historico, débito, crédito`
- Bradesco: `data, historico, docto, valor`

---

## 📚 Recursos Adicionais

- **Documentação antiga:** `documentacao_financas_pessoais_completa.md`
- **Plano de reestruturação:** `plano_reestruturacao.md`
- **README rápido:** `README.md`
- **Issues/PRs:** GitHub repository

---

## 📝 Notas Finais

Este aplicativo é um projeto em constante evolução. A documentação será atualizada conforme novas funcionalidades forem adicionadas.

**Contribuições e feedback são bem-vindos!**

Se encontrar bugs ou tiver sugestões, abra uma issue no GitHub.

---

**Última atualização:** Maio 2026  
**Versão:** 2.0  
**Status:** ✅ Produção estável
