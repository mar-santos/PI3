# app/services/servicos_service.py
from app.models.models import Servico

def criar_servico(nome_servico, descricao, valor_hora, valor_dia):
    novo_servico = Servico(
        nome_servico=nome_servico,
        descricao=descricao,
        valor_hora=valor_hora,
        valor_dia=valor_dia
    )
    return novo_servico