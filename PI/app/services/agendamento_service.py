# app/services/agendamento_service.py
from app.models.models import Agendamento, AgendamentoServico, Servico
from app.models import db

def calcular_valor_total_agendamento(servicos_agendados):
    valor_total = 0.0
    for servico_info in servicos_agendados:
        id_servico = servico_info.get('id_servico')
        quantidade = servico_info.get('quantidade')

        servico = Servico.query.get(id_servico)
        if not servico:
            raise ValueError(f'Serviço com ID {id_servico} não encontrado')

        # Verificar se o serviço é por hora ou por dia
        if servico.valor_hora:
            valor_total += servico.valor_hora * quantidade
        elif servico.valor_dia:
            valor_total += servico.valor_dia * quantidade

    return valor_total

def criar_agendamento(id_usuario, id_pet, data_entrada, data_saida, observacoes, servicos_agendados):
    novo_agendamento = Agendamento(
        id_usuario=id_usuario,
        id_pet=id_pet,
        data_entrada=data_entrada,
        data_saida=data_saida,
        observacoes=observacoes,
        valor_total=calcular_valor_total_agendamento(servicos_agendados)
    )
    db.session.add(novo_agendamento)
    db.session.flush()

    for servico_info in servicos_agendados:
        id_servico = servico_info.get('id_servico')
        quantidade = servico_info.get('quantidade')

        servico = Servico.query.get(id_servico)
        valor_servico = 0.0
        if servico.valor_hora:
            valor_servico = servico.valor_hora * quantidade
        elif servico.valor_dia:
            valor_servico = servico.valor_dia * quantidade

        novo_agendamento_servico = AgendamentoServico(
            id_agendamento=novo_agendamento.id_agendamento,
            id_servico=id_servico,
            quantidade=quantidade,
            valor=valor_servico
        )
        db.session.add(novo_agendamento_servico)

    return novo_agendamento