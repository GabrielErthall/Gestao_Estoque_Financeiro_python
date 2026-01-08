from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy.orm import sessionmaker
from models import Produto, Venda, ItemVenda
from db import engine
from datetime import datetime

app = Flask(__name__)
Session = sessionmaker(bind=engine)

@app.route("/produtos")
def listar_produtos():
    session = Session()
    query = session.query(Produto)

    nome = request.args.get("nome")
    categoria = request.args.get("categoria")
    cor = request.args.get("cor")
    preco = request.args.get("preco")
    produto_id = request.args.get("id")

    if nome:
        query = query.filter(Produto.nome.ilike(f"%{nome}%"))
    if categoria:
        query = query.filter(Produto.categoria.ilike(f"%{categoria}%"))
    if cor:
        query = query.filter(Produto.cor.ilike(f"%{cor}%"))
    if preco:
        try:
            query = query.filter(Produto.preco == float(preco))
        except ValueError:
            pass
    if produto_id:
        try:
            query = query.filter(Produto.id == int(produto_id))
        except ValueError:
            pass

    per_page = 20
    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * per_page

    produtos = query.order_by(Produto.id).limit(per_page).offset(offset).all()
    total = query.count()
    total_pages = (total + per_page - 1) // per_page

    categorias = [c[0] for c in session.query(Produto.categoria).distinct().all()]

    return render_template(
        "produtos.html",
        produtos=produtos,
        categorias=categorias,
        page=page,
        total_pages=total_pages
    )


@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar_produto():
    session = Session()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()
        tamanho = request.form.get("tamanho", "").strip()
        cor = request.form.get("cor", "").strip()
        quantidade_raw = request.form.get("quantidade", "").strip()
        preco_raw = request.form.get("preco", "").strip()

        # Valida campos obrigatórios
        if not nome or not categoria or not tamanho or not cor:
            return render_template("erro.html", mensagem="Todos os campos de texto são obrigatórios.", voltar="listar_produtos")

        # Valida quantidade
        if not quantidade_raw.isdigit():
            return render_template("erro.html", mensagem="Quantidade inválida. Digite um número inteiro.", voltar="listar_produtos")
        quantidade = int(quantidade_raw)

        # Valida preço
        try:
            preco = float(preco_raw)
        except ValueError:
            return render_template("erro.html", mensagem="Preço inválido. Digite um número válido.", voltar="listar_produtos")

        # Valida valores negativos
        if quantidade < 0 or preco < 0:
            return render_template("erro.html", mensagem="Quantidade e preço não podem ser negativos.", voltar="listar_produtos")

        # Cria e salva produto
        novo_produto = Produto(
            nome=nome,
            categoria=categoria,
            tamanho=tamanho,
            cor=cor,
            quantidade=quantidade,
            preco=preco
        )
        session.add(novo_produto)
        session.commit()
        return redirect(url_for("listar_produtos"))

    return render_template("formulario.html", titulo="Cadastrar Produto", produto={})

@app.route("/excluir/<int:id>")
def escluir_produto(id):
    session = Session()
    produto = session.query(Produto).get(id)

    if produto:
        session.delete(produto)
        session.commit()
        return redirect(url_for("listar_produtos"))
    else:
        return f"<h1>Produto com ID {id} não encontrado. </h1>"

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_produto(id):
    session = Session()
    produto = session.query(Produto).get(id)

    if not produto:
        return f"<h1>Produto com ID {id} não encontrado. </h1>"
    
    if request.method == "POST":
        produto.nome = request.form["nome"]
        produto.categoria = request.form["categoria"]
        produto.tamanho = request.form["tamanho"]
        produto.cor = request.form["cor"]
        produto.quantidade = int(request.form["quantidade"])
        produto.preco = float(request.form["preco"]) 
        session.commit()
        return redirect(url_for("listar_produtos"))
    return render_template("formulario.html", titulo="Editar Produto", produto=produto)

@app.route("/vender/<int:id>", methods =["GET", "POST"] )
def vender_produto(id):
    session = Session()
    produto = session.query(Produto).get(id)

    if not produto:
        return f"<h1>Produto com ID {id} não encontrado. </h1>"
    
    if request.method == "POST":
        qtd_venda = int(request.form["quantidade"])

        if qtd_venda <= 0:
            return "<h1>Quantidade inválida. </h1>"
        
        if qtd_venda > produto.quantidade:
            return "<h1>Estoque insuficiente.</h1>"
        
        produto.quantidade -= qtd_venda
        nova_venda = Venda(produto_id=produto.id, quantidade=qtd_venda)
        session.add(nova_venda)
        session.commit()

        return redirect(url_for("listar_produtos"))
    
    return f"""
        <h1>Vender Produto</h1>
        <p>{produto.nome} - Estoque atual: {produto.quantidade}</p>
        <form method="post">
            Qauntidade: <input type="number" name="quantidade" ><br>
            <input type="submit" value="Vender">
        </form>
    """

@app.route("/nova-venda", methods=["GET", "POST"])
def nova_venda():
    session = Session()
    try:
        if request.method == "POST":
            itens = []
            total = 0

            produtos_ids = request.form.getlist("produto_id[]")
            quantidades = request.form.getlist("quantidade[]")
            precos = request.form.getlist("preco_unitario[]")
            forma_pagamento = request.form.get("forma_pagamento")

            if not (len(produtos_ids) == len(quantidades) == len(precos)):
                return "<h1>Erro: dados incompletos no formulário.</h1>"

            for i in range(len(produtos_ids)):
                produto = session.query(Produto).get(int(produtos_ids[i]))
                qtd = int(quantidades[i])
                preco_unitario = float(precos[i])

                if qtd > produto.quantidade:
                    return f"<h1>Estoque insuficiente para {produto.nome}</h1>"

                produto.quantidade -= qtd
                item = ItemVenda(
                    produto_id=produto.id,
                    quantidade=qtd,
                    preco_unitario=preco_unitario
                )
                itens.append(item)
                total += qtd * preco_unitario

            if not itens or total <= 0:
                return render_template("erro_venda.html")

            venda = Venda(total=total, itens=itens, forma_pagamento=forma_pagamento)
            session.add(venda)
            session.commit()
            return redirect(url_for("relatorio_vendas"))

        return render_template("nova_venda.html")
    finally:
        session.close()


@app.route("/buscar-produto")
def buscar_produto():
    session = Session()
    termo = request.args.get("q", "")

    produto = None
    if termo.isdigit():
        produto = session.query(Produto).get(int(termo))
    else:
        produto = session.query(Produto).filter(Produto.nome.ilike(f"%{termo}%")).first()
    
    if produto:
        return {
            "id": produto.id,
            "nome": produto.nome,
            "categoria": produto.categoria,
            "tamanho": produto.tamanho,
            "cor": produto.cor,
            "quantidade": produto.quantidade,
            "preco": produto.preco
        }
    return {"erro": "Produto não encontrado"}

@app.route("/relatorio-vendas")
def relatorio_vendas():
    session = Session()
    query = session.query(Venda)

    # Filtros de data
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        query = query.filter(Venda.data_hora >= data_inicio)

    if data_fim:
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
        # incluir fim do dia, se quiser abranger o dia inteiro:
        data_fim = datetime.combine(data_fim, datetime.max.time())
        query = query.filter(Venda.data_hora <= data_fim)

    # Filtro de forma de pagamento
    forma_pagamento = request.args.get("forma_pagamento")
    if forma_pagamento:  # só aplica se veio algo
        # se quiser igualdade exata:
        query = query.filter(Venda.forma_pagamento == forma_pagamento)
        # ou, se precisar ser case-insensitive:
        # query = query.filter(Venda.forma_pagamento.ilike(forma_pagamento))

    # Ordenação
    ordenar_por = request.args.get("ordenar_por", "data")
    ordem = request.args.get("ordem", "desc")

    if ordenar_por == "id":
        coluna = Venda.id
    elif ordenar_por == "total":
        coluna = Venda.total
    else:
        coluna = Venda.data_hora

    query = query.order_by(coluna.asc() if ordem == "asc" else coluna.desc())

    # Paginação
    page = request.args.get("page", 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    total = query.count()
    vendas = query.limit(per_page).offset(offset).all()
    total_pages = (total + per_page - 1) // per_page

    # Resumos (com base nas vendas paginadas)
    soma_total = sum(v.total for v in vendas)

    resumo_pagamento = {}
    for v in vendas:
        resumo_pagamento[v.forma_pagamento] = resumo_pagamento.get(v.forma_pagamento, 0) + v.total

    resumo_categoria = {}
    for v in vendas:
        for item in v.itens:
            produto = session.query(Produto).get(item.produto_id)
            if produto:
                valor = item.quantidade * item.preco_unitario
                resumo_categoria[produto.categoria] = resumo_categoria.get(produto.categoria, 0) + valor

    return render_template("relatorio_vendas.html",
                           vendas=vendas,
                           soma_total=soma_total,
                           resumo_pagamento=resumo_pagamento,
                           resumo_categoria=resumo_categoria,
                           page=page,
                           total_pages=total_pages)

@app.route("/excluir-venda/<int:id>")
def excluir_venda(id):
    session = Session()
    venda = session.query(Venda).get(id)

    if not venda:
        return f"<h1>Venda com ID {id} não encontrada.</h1>"
    
    for item in venda.itens:
        session.delete(item)
    
    session.delete(venda)
    session.commit()
    return redirect(url_for("relatorio_vendas"))

@app.route("/editar-venda/<int:id>", methods=["GET", "POST"])
def editar_venda(id):
    session = Session()
    venda = session.query(Venda).get(id)

    if not venda:
        return f"<h1>Venda com ID {id} não encontrada.</h1>"

    if request.method == "POST":
        total = 0

        for item in venda.itens:
            qtd = int(request.form.get(f"quantidade_{item.id}", item.quantidade))
            preco = float(request.form.get(f"preco_{item.id}", item.preco_unitario))

            item.quantidade = qtd
            item.preco_unitario = preco
            total += qtd * preco

        
        if total <= 0:
            for item in venda.itens:
                session.delete(item)
            session.delete(venda)
            session.commit()
            return "<h1>Venda excluída porque o valor foi zerado.</h1>"

        venda.total = total
        session.commit()
        return redirect(url_for("relatorio_vendas"))

    return render_template("editar_venda.html", venda=venda)

 
if __name__ == "__main__":
    app.run(debug=True)