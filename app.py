from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy.orm import sessionmaker
from models import Produto, Venda, ItemVenda
from db import engine

app = Flask(__name__)
Session = sessionmaker(bind=engine)

@app.route("/produtos")
def listar_produtos():
    session = Session()
    query = session.query(Produto)

    nome = request.args.get("nome")
    categoria = request.args.get("cateegoria")
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
        query = query.filter(Produto.preco == float(preco))
    if produto_id:
        query = query.filter(Produto.id == int(produto_id))
    
    produtos = query.all()
    categorias = [c[0] for c in session.query(Produto.categoria).distinct().all()]
    return render_template("produtos.html", produtos=produtos)


@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar_produto():
    session = Session()
    if request.method == "POST":
        nome = request.form["nome"]
        categoria = request.form["categoria"]
        tamanho = request.form["tamanho"]
        cor = request.form["cor"]
        quantidade = int(request.form["quantidade"])
        preco = float(request.form["preco"])

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

    produto_vazio = Produto(nome="", categoria="", tamanho="", cor="", quantidade=0)
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

    if request.method == "POST":
        itens = []
        total = 0

        produtos_ids = request.form.getlist("produto_id")
        quantidades = request.form.getlist("quantidade")
        precos = request.form.getlist("preco_unitario")

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

        venda = Venda(total=total, itens=itens)
        session.add(venda)
        session.commit()
        return redirect(url_for("listar_produtos"))

    return render_template("nova_venda.html")

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

    # filtros
    venda_id = request.args.get("id")
    preco = request.args.get("preco")
    data = request.args.get("data")  # exemplo: "2026-01-06"

    if venda_id:
        query = query.filter(Venda.id == int(venda_id))
    if preco:
        query = query.filter(Venda.total == float(preco))
    if data:
        query = query.filter(Venda.data.like(f"%{data}%"))

    vendas = query.order_by(Venda.data.desc()).limit(50).all()
    return render_template("relatorio_vendas.html", vendas=vendas)

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
        return f"<h1>Venda com ID {id} não encontrada</h1>"
    
    if request.method == "POST":
        total = 0
        for item in venda.itens:
            qtd = int(request.form.get(f"quantidade_{item.id}", item.quantidade))
            preco = float(request.form.get(f"preco_{item.id}", item.preco_unitario))

            item.quantidade = qtd
            item.preco_unitario = preco
            total += qtd * preco
        
        venda.total = total
        session.commit()
        return redirect(url_for("relatorio_vendas"))
    return render_template("editar_venda.html", venda=venda)

 
if __name__ == "__main__":
    app.run(debug=True)