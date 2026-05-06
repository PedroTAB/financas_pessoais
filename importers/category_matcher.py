"""importers/category_matcher.py — Sugestão automática de categoria e forma de pagamento."""

import re

_RULES: list[tuple[list[str], str, str]] = [
    (["salario", "salário", "folha", "pagamento empresa",
      "holerite", "remuneracao", "remuneração"],              "Salário",       "Crédito"),
    (["freelance", "freela", "prestacao", "prestação",
      "servico", "serviço", "honorario", "honorário"],        "Freelance",     "Crédito"),
    (["dividendo", "jcp", "lucro distribuido",
      "rendimento", "yield", "proventos", "aplicacao",
      "aplicação"],                                           "Investimentos", "Crédito"),
    (["pix recebido", "transferencia recebida",
      "ted recebida", "doc recebido", "deposito",
      "depósito", "reembolso", "estorno"],                    "Transferência", "Crédito"),
    (["ifood", "rappi", "uber eats", "james",
      "mcdonalds", "mcdonald", "burger", "pizza",
      "restaurante", "lanchonete", "padaria",
      "sushi", "churrasco", "pastel", "acai", "açaí",
      "food", "delivery", "refeicao", "refeição"],            "Restaurantes",  "Débito"),
    (["mercado", "supermercado", "atacadao", "atacadão",
      "carrefour", "extra", "pao de acucar",
      "pão de açúcar", "hortifruti", "hortifrutti",
      "mercearia", "sacolao", "sacolão", "feira",
      "cesta basica"],                                        "Subsistência",  "Débito"),
    (["farmacia", "farmácia", "drogaria", "ultrafarma",
      "droga raia", "drogaraia", "drogasil", "pacheco",
      "remedios", "remédios", "medicamento"],                 "Saúde",         "Débito"),
    (["hospital", "clinica", "clínica", "medico",
      "médico", "consulta", "odonto", "dentista",
      "laboratorio", "laboratório", "exame", "plano saude",
      "amil", "unimed", "bradesco saude", "sulamerica",
      "academia", "crossfit", "smart fit", "smartfit",
      "bluefit", "gym", "ginasio", "ginásio"],               "Saúde",         "Débito"),
    (["uber", "99", "cabify", "taxi", "táxi",
      "99app", "indrive", "corrida"],                         "Transporte",    "Débito"),
    (["combustivel", "combustível", "gasolina", "etanol",
      "posto", "shell", "ipiranga", "br distribuidora",
      "ale combustiveis"],                                    "Transporte",    "Débito"),
    (["onibus", "ônibus", "metro", "metrô", "trem",
      "bilhete unico", "bilhetagem", "sptrans"],              "Transporte",    "Débito"),
    (["netflix", "spotify", "amazon prime", "hbo",
      "disney", "apple tv", "globoplay", "paramount",
      "youtube premium", "deezer", "crunchyroll",
      "pluto", "twitch"],                                     "Streaming",     "Débito"),
    (["amazon", "shopee", "mercado livre", "aliexpress",
      "americanas", "magalu", "magazine luiza",
      "casas bahia", "submarino", "netshoes",
      "zattini", "shein", "wish", "livraria"],                "Compras",       "Débito"),
    (["apple", "samsung", "xiaomi", "dell", "lenovo",
      "hp ", "asus", "acer", "kabum", "pichau",
      "terabyte", "info store", "fast shop",
      "eletrônico", "eletronico", "computador",
      "notebook", "celular", "smartphone", "tablet",
      "fone", "headphone"],                                   "Eletrônicos",   "Débito"),
    (["aluguel", "condominio", "condomínio",
      "agua ", "água ", "energia", "celesc",
      "sabesp", "copel", "cemig", "cosern",
      "internet", "vivo", "claro", "tim", "oi ",
      "net ", "iptu", "boleto"],                              "Moradia",       "Débito"),
    (["escola", "faculdade", "universidade", "curso",
      "udemy", "alura", "coursera", "duolingo",
      "mentoria", "livro", "apostila", "mensalidade"],        "Educação",      "Débito"),
    (["cinema", "teatro", "show", "ingresso",
      "ticketmaster", "eventim", "sympla",
      "bilheteria", "parque", "zoo"],                         "Lazer",         "Débito"),
    (["viagem", "hotel", "pousada", "airbnb",
      "booking", "expedia", "latam", "gol ",
      "azul ", "rodoviaria", "rodoviária",
      "passagem", "mochila"],                                 "Viagem",        "Débito"),
    (["roupa", "vestuario", "vestuário", "calçado",
      "calcado", "renner", "riachuelo", "c&a",
      "hering", "zara", "forever", "nike", "adidas",
      "puma", "havaianas"],                                   "Vestuário",     "Débito"),
    (["pet", "animal", "veterinário", "veterinario",
      "racao", "ração", "cobasi", "petz"],                    "Pets",          "Débito"),
    (["poupanca", "poupança", "cdb", "lci", "lca",
      "tesouro", "fundo", "acao", "ação", "fii",
      "investimento", "xp ", "clear", "btg", "rico ",
      "modal", "inter invest"],                               "Investimentos", "Débito"),
    (["nubank", "inter", "itau", "itaú", "bradesco",
      "santander", "bb ", "banco do brasil", "caixa",
      "c6", "original", "next", "neon", "picpay",
      "pagbank", "mercado pago"],                             "Conta",         "Débito"),
    (["seguro", "insurance", "porto", "tokio",
      "sulamerica", "allianz"],                               "Conta",         "Débito"),
    (["presente", "gift", "aniversario", "aniversário",
      "natal", "casamento"],                                  "Presentes",     "Débito"),
    (["assinatura", "subscription", "plano"],                 "Assinaturas",   "Débito"),
]

_DEFAULT_DEBITO  = "Outros"
_DEFAULT_CREDITO = "Outros"

# Ordem importa: mais específico primeiro
_FP_RULES: list[tuple[list[str], str]] = [
    (["pix recebido", "pix enviado", "pix ", " pix"],           "Pix"),
    (["compra cartao", "compra cartão", "compra no cartao",
      "compra no cartão", "cartao credito", "cartão crédito",
      "cartao debito", "cartão débito"],                        "Crédito"),
    (["ted recebida", "ted enviada", "transf ted",
      "transferencia ted", "transferência ted"],                 "TED"),
    (["doc recebido", "doc enviado", "transf doc",
      "transferencia doc", "transferência doc"],                 "DOC"),
    (["boleto", "pagamento boleto", "pgto boleto"],             "Outros"),
    (["debito automatico", "débito automático",
      "debito em conta", "débito em conta"],                    "Débito"),
    (["dinheiro", "saque", "deposito dinheiro",
      "depósito dinheiro"],                                     "Dinheiro"),
]


def sugerir_categoria(descricao: str, tipo: str = "Débito") -> str:
    """Retorna a categoria sugerida com base na descrição da transação."""
    desc = descricao.lower()
    for keywords, categoria, tipo_esperado in _RULES:
        if tipo_esperado == tipo or tipo_esperado == "":
            if any(kw in desc for kw in keywords):
                return categoria
    return _DEFAULT_DEBITO if tipo == "Débito" else _DEFAULT_CREDITO


def sugerir_forma_pagamento(descricao: str, tipo: str = "Débito") -> str:
    """
    Infere a forma de pagamento a partir da descrição do extrato.
    Retorna: Pix | Crédito | Débito | TED | DOC | Dinheiro | Outros | ""
    """
    desc = descricao.lower()
    for keywords, forma in _FP_RULES:
        if any(kw in desc for kw in keywords):
            return forma
    # Créditos sem forma identificada ficam em branco
    if tipo == "Crédito":
        return ""
    return "Outros"


def sugerir_tipo(descricao: str, valor: float) -> str:
    """Infere Débito/Crédito pelo sinal do valor e por keywords."""
    if valor > 0:
        desc = descricao.lower()
        cred_kws = ["recebido", "receb", "salario", "salário", "deposito",
                    "depósito", "transferencia recebida", "dividendo",
                    "rendimento", "estorno", "devolucao", "reembolso",
                    "aplicacao", "rendimento"]
        if any(k in desc for k in cred_kws):
            return "Crédito"
    return "Débito" if valor <= 0 else "Crédito"
