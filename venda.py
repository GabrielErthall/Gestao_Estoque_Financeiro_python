import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Venda, Base

# Conexão com o banco
engine = create_engine("sqlite:///estoque.db")
Base.metadata.create_all(engine)
session = Session(bind=engine)

# Feriados e emendas
feriados = [
    datetime(2025, 12, 24),
    datetime(2025, 12, 25),
    datetime(2025, 12, 31),
]

def dias_uteis_dezembro():
    inicio = datetime(2025, 12, 1)
    fim = datetime(2025, 12, 31)
    dias = []
    while inicio <= fim:
        if inicio.weekday() < 5 and inicio not in feriados:  # segunda a sexta
            dias.append(inicio)
        inicio += timedelta(days=1)
    return dias

def simular_vendas():
    dias = dias_uteis_dezembro()
    formas_pagamento = ["Dinheiro", "Cartão Débito", "Cartão Crédito", "Pix"]

    for dia in dias:
        num_vendas = random.randint(5, 20)  # número de vendas por dia
        for _ in range(num_vendas):
            hora = random.randint(9, 18)
            minuto = random.randint(0, 59)
            data_hora = datetime(dia.year, dia.month, dia.day, hora, minuto)

            total = round(random.uniform(50, 500), 2)
            forma_pagamento = random.choice(formas_pagamento)

            venda = Venda(
                data_hora=data_hora,
                total=total,
                forma_pagamento=forma_pagamento
            )
            session.add(venda)

    session.commit()
    print("✅ Vendas simuladas adicionadas ao estoque.db")

# Executar simulação
simular_vendas()