from flask import Flask, request, redirect, url_for, render_template
from sqlalchemy.orm import sessionmaker
from models import Produto, Venda
from db import engine

app = Flask(__name__)
Session = sessionmaker(bind=engine)

@app.route("/produtos")
def listar_produtos():
    session = Session()
    produtos = session.query(Produto).all()
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
    produtos = session.query(Produto).all()

    if request.method == "POST":
        itens = []
        total = 0

        for produto in produtos:
            qtd= int(request.form.get(f"quantidade_{produto.id}", 0))
            if qtd > 0:
                if qtd > produto.quantidade:
                    return f"Estoque insuficiente para {produto.nome}"
                produto.quantidade -= qtd
                item = ItemVenda(
                    produto_id=produto.id,
                    quantidade=qtd,
                    preco_unitario=produto.preco
                )

                itens.append(item)
                total += qtd * produto.preco
        
        venda = Venda(total=total, itens=itens)
        session.add(venda)
        session.commit()
        return redirect(url_for("lsitar_produtos"))
    return render_template("nova_venda.html", produtos=produtos)
    
if __name__ == "__main__":
    app.run(debug=True)