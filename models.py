from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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

class Venda(Base):
    __tablename__ = "vendas"
    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Integer, nullable=False)
    data = Column(DateTime, default=datetime.now)

    produto = relationship("Produto")