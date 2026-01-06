from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    categoria = Column(String)
    tamanho = Column(String)
    cor = Column(String)
    quantidade = Column(Integer)
    preco = Column(Float, nullable=False)

class Venda(Base):
    __tablename__ = "vendas"
    id = Column(Integer, primary_key=True)
    data = Column(DateTime, default=datetime.now)
    total = Column(Float)

    itens = relationship("ItemVenda", back_populates="venda")


class ItemVenda(Base):
    __tablename__ = "itens_venda"
    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    venda_id = Column(Integer, ForeignKey("vendas.id"))
    quantidade = Column(Integer)
    preco_unitario = Column(Float)

    venda = relationship("Venda", back_populates="itens")
