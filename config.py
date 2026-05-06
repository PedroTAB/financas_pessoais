"""config.py — Configurações centralizadas."""

USUARIO_NOME   = "Pedro"
USUARIO_AVATAR = "P"
APP_TITULO     = "Finanças Pessoais"
APP_ICONE      = "📈"
ANO_MINIMO     = 2025

LIMITE_NECESSIDADES = 0.50
LIMITE_DESEJOS      = 0.30
LIMITE_POUPANCA     = 0.20

# Devem bater com os buckets do dashboard.py (regra 50/30/20)
CATEGORIAS_NECESSIDADES = [
    "Moradia", "Subsistência", "Transporte", "Saúde",
    "Conta", "Educação", "Pets",
]
CATEGORIAS_DESEJOS = [
    "Lazer", "Vestuário", "Streaming", "Eletrônicos",
    "Restaurantes", "Viagem", "Assinaturas", "Presentes",
]
