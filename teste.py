import random
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, Produto

engine = create_engine("sqlite:///estoque.db")
Base.metadata.create_all(engine)
session = Session(bind=engine)

categorias = ["Roupas", "Calçados", "Acessórios"]
cores = ["Azul", "Vermelho", "Preto", "Branco", "Verde"]

for i in range(1, 101):  # 100 produtos
    nome_base = f"Produto{i}"
    categoria = random.choice(categorias)
    preco_base = round(random.uniform(20, 200), 2)

    if categoria == "Roupas":
        tamanhos = ["P", "M", "G"]
        acrescimos = [0, 10, 20]
        for cor in cores:
            for tamanho, acrescimo in zip(tamanhos, acrescimos):
                produto = Produto(
                    nome=nome_base,              # só o nome base
                    categoria=categoria,
                    tamanho=tamanho,
                    cor=cor,
                    quantidade=random.randint(5, 50),
                    preco=round(preco_base + acrescimo, 2)
                )
                session.add(produto)

    elif categoria == "Calçados":
        tamanhos = ["36", "38", "40"]
        acrescimos = [0, 10, 20]
        for cor in cores:
            for tamanho, acrescimo in zip(tamanhos, acrescimos):
                produto = Produto(
                    nome=nome_base,              # só o nome base
                    categoria=categoria,
                    tamanho=tamanho,
                    cor=cor,
                    quantidade=random.randint(5, 50),
                    preco=round(preco_base + acrescimo, 2)
                )
                session.add(produto)

    else:  # Acessórios
        produto = Produto(
            nome=nome_base,                      # só o nome base
            categoria=categoria,
            tamanho="Único",
            cor=None,                            # cor nula
            quantidade=random.randint(5, 50),
            preco=preco_base
        )
        session.add(produto)

session.commit()
print("✅ Produtos criados com nome base único; tamanho e cor separados nas colunas")