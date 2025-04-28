from flask import jsonify, request, render_template, redirect, url_for, flash
from app.routes.routes_usuarios import routes_bp
from app.models.models import Usuario, Pet, Servico, Agendamento, AgendamentoServico, Pagamento
from app.models import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import desc
import traceback

def validar_acesso_agendamento(agendamento):
    """Verifica se o usuário tem permissão para acessar o agendamento"""
    if agendamento is None:
        return False, jsonify({'message': 'Agendamento não encontrado'}), 404
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        return False, jsonify({'message': 'Acesso negado. Você não tem permissão para acessar este agendamento.'}), 403
    return True, None, None

def formatar_agendamento(agendamento):
    """Retorna um agendamento formatado para API"""
    usuario = Usuario.query.get(agendamento.id_usuario)
    pet = Pet.query.get(agendamento.id_pet)
    servicos_agendados = []
    
    for agendamento_servico in agendamento.servicos:
        if agendamento_servico.ativo:
            servico = Servico.query.get(agendamento_servico.id_servico)
            servicos_agendados.append({
                'id_servico': servico.id_servico,
                'nome_servico': servico.nome_servico,
                'quantidade': agendamento_servico.quantidade,
                'valor': agendamento_servico.valor
            })
    
    return {
        'id_agendamento': agendamento.id_agendamento,
        'usuario': {
            'id_usuario': usuario.id_usuario,
            'nome_user': usuario.nome_user
        },
        'pet': {
            'id_pet': pet.id_pet,
            'nome_pet': pet.nome_pet
        },
        'data_entrada': agendamento.data_entrada.strftime('%Y-%m-%d %H:%M'),
        'data_saida': agendamento.data_saida.strftime('%Y-%m-%d %H:%M'),
        'observacoes': agendamento.observacoes,
        'valor_total': agendamento.valor_total,
        'servicos': servicos_agendados,
        'status_pagamento': agendamento.pagamento.status if agendamento.pagamento else 'pendente'
    }

def calcular_dias_estadia(data_entrada, data_saida):
    """Calcula o total de dias entre duas datas"""
    delta = data_saida - data_entrada
    return max(1, delta.days + (1 if delta.seconds > 0 else 0))

def calcular_valor_servico(servico, quantidade, dias):
    """Calcula o valor de um serviço"""
    if servico.valor_hora and servico.valor_hora > 0:
        return servico.valor_hora * quantidade
    elif servico.valor_dia and servico.valor_dia > 0:
        return servico.valor_dia * quantidade * dias
    return 0.0

# -------------------- Rotas da API --------------------
@routes_bp.route('/api/agendamentos', methods=['GET'])
@login_required
def agendamentos_listar_api():
    if current_user.is_admin:
        agendamentos = Agendamento.query.filter_by(ativo=True).all()
    else:
        agendamentos = Agendamento.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()
    
    resultado = [formatar_agendamento(agendamento) for agendamento in agendamentos]
    return jsonify(resultado)

@routes_bp.route('/api/agendamentos/<int:id>', methods=['GET'])
@login_required
def agendamentos_obter_api(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    acesso_valido, resposta_erro, codigo_erro = validar_acesso_agendamento(agendamento)
    if not acesso_valido:
        return resposta_erro, codigo_erro
    
    return jsonify(formatar_agendamento(agendamento))

@routes_bp.route('/api/agendamentos', methods=['POST'])
@login_required
def agendamentos_criar_api():
    data = request.get_json()
    required_fields = ['id_usuario', 'id_pet', 'data_entrada', 'data_saida', 'servicos']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Campo {field} é obrigatório'}), 400
    
    id_usuario = int(data.get('id_usuario'))
    if not current_user.is_admin and id_usuario != current_user.id_usuario:
        return jsonify({'message': 'Acesso negado. Você só pode criar agendamentos para você mesmo.'}), 403
    
    id_pet = data.get('id_pet')
    observacoes = data.get('observacoes', '')
    servicos_agendados = data.get('servicos')
    
    try:
        data_entrada = datetime.strptime(data.get('data_entrada'), '%Y-%m-%d %H:%M')
        data_saida = datetime.strptime(data.get('data_saida'), '%Y-%m-%d %H:%M')
    except ValueError:
        return jsonify({'message': 'Formato de data inválido. Use YYYY-MM-DD HH:MM'}), 400
    
    dias_total = calcular_dias_estadia(data_entrada, data_saida)
    
    usuario = Usuario.query.get(id_usuario)
    pet = Pet.query.get(id_pet)
    
    if not usuario:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    if not pet:
        return jsonify({'message': 'Pet não encontrado'}), 404
    if pet.id_usuario != usuario.id_usuario:
        return jsonify({'message': 'Este pet não pertence ao usuário informado'}), 400
    
    try:
        valor_total = 0.0
        for servico_info in servicos_agendados:
            id_servico = servico_info.get('id_servico')
            quantidade = servico_info.get('quantidade', 1)
            dias = servico_info.get('dias', dias_total)
            
            servico = Servico.query.get(id_servico)
            if not servico:
                return jsonify({'message': f'Serviço com ID {id_servico} não encontrado'}), 404
            
            valor_total += calcular_valor_servico(servico, quantidade, dias)
        
        novo_agendamento = Agendamento(
            id_usuario=id_usuario,
            id_pet=id_pet,
            data_entrada=data_entrada,
            data_saida=data_saida,
            observacoes=observacoes,
            valor_total=valor_total,
            ativo=True
        )
        db.session.add(novo_agendamento)
        db.session.flush()
        
        for servico_info in servicos_agendados:
            id_servico = servico_info.get('id_servico')
            quantidade = servico_info.get('quantidade', 1)
            dias = servico_info.get('dias', dias_total)
            
            servico = Servico.query.get(id_servico)
            valor_servico = calcular_valor_servico(servico, quantidade, dias)
            
            novo_agendamento_servico = AgendamentoServico(
                id_agendamento=novo_agendamento.id_agendamento,
                id_servico=id_servico,
                quantidade=quantidade,
                valor=valor_servico,
                ativo=True
            )
            db.session.add(novo_agendamento_servico)
        
        # Verifique os campos disponíveis no modelo Pagamento antes de criar
        # Se não tiver forma_pagamento, ignore esse campo
        try:
            novo_pagamento = Pagamento(
                id_agendamento=novo_agendamento.id_agendamento,
                valor=valor_total,
                status='pendente',
                ativo=True
            )
        except Exception as e:
            print(f"Erro ao criar pagamento: {e}")
            raise
            
        db.session.add(novo_pagamento)
        db.session.commit()
        
        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'id_agendamento': novo_agendamento.id_agendamento,
            'valor_total': valor_total
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao criar agendamento: {str(e)}'}), 400

@routes_bp.route('/api/agendamentos/<int:id>', methods=['PUT'])
@login_required
def agendamentos_atualizar_api(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    acesso_valido, resposta_erro, codigo_erro = validar_acesso_agendamento(agendamento)
    if not acesso_valido:
        return resposta_erro, codigo_erro
    
    data = request.get_json()
    nova_data_entrada = agendamento.data_entrada
    nova_data_saida = agendamento.data_saida
    
    if 'data_entrada' in data:
        try:
            nova_data_entrada = datetime.strptime(data['data_entrada'], '%Y-%m-%d %H:%M')
            agendamento.data_entrada = nova_data_entrada
        except ValueError:
            return jsonify({'message': 'Formato de data de entrada inválido. Use YYYY-MM-DD HH:MM'}), 400
    
    if 'data_saida' in data:
        try:
            nova_data_saida = datetime.strptime(data['data_saida'], '%Y-%m-%d %H:%M')
            agendamento.data_saida = nova_data_saida
        except ValueError:
            return jsonify({'message': 'Formato de data de saída inválido. Use YYYY-MM-DD HH:MM'}), 400
    
    dias_total = calcular_dias_estadia(nova_data_entrada, nova_data_saida)
    
    if 'observacoes' in data:
        agendamento.observacoes = data['observacoes']
    
    if 'servicos' in data:
        servicos_agendados = data['servicos']
        
        # Desativa serviços antigos
        for agendamento_servico in agendamento.servicos:
            agendamento_servico.ativo = False
        
        valor_total = 0.0
        for servico_info in servicos_agendados:
            id_servico = servico_info.get('id_servico')
            quantidade = servico_info.get('quantidade', 1)
            dias = servico_info.get('dias', dias_total)
            
            servico = Servico.query.get(id_servico)
            if not servico:
                return jsonify({'message': f'Serviço com ID {id_servico} não encontrado'}), 404
            
            valor_servico = calcular_valor_servico(servico, quantidade, dias)
            valor_total += valor_servico
            
            novo_agendamento_servico = AgendamentoServico(
                id_agendamento=agendamento.id_agendamento,
                id_servico=id_servico,
                quantidade=quantidade,
                valor=valor_servico,
                ativo=True
            )
            db.session.add(novo_agendamento_servico)
        
        agendamento.valor_total = valor_total
        
        # Atualiza o valor do pagamento se estiver pendente
        if agendamento.pagamento and agendamento.pagamento.status == 'pendente':
            agendamento.pagamento.valor = valor_total
    
    try:
        db.session.commit()
        return jsonify({'message': 'Agendamento atualizado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao atualizar agendamento: {str(e)}'}), 400

@routes_bp.route('/api/agendamentos/<int:id>', methods=['DELETE'])
@login_required
def agendamentos_excluir_api(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    acesso_valido, resposta_erro, codigo_erro = validar_acesso_agendamento(agendamento)
    if not acesso_valido:
        return resposta_erro, codigo_erro
    
    agendamento.ativo = False
    for agendamento_servico in agendamento.servicos:
        agendamento_servico.ativo = False
    
    try:
        db.session.commit()
        return jsonify({'message': 'Agendamento cancelado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao cancelar agendamento: {str(e)}'}), 400

# -------------------- Rotas HTML --------------------
@routes_bp.route('/agendamentos-lista', methods=['GET'])
@login_required
def agendamentos_listar_html():
    try:
        print(f"Usuário atual: ID={current_user.id_usuario}, Admin={current_user.is_admin}")
        
        # Recuperar filtros da URL - mantendo os existentes e adicionando username
        data_filtro = request.args.get('data', '')
        status_filtro = request.args.get('status', '')
        pagamento_filtro = request.args.get('pagamento', '')
        username_filtro = request.args.get('username', '')
        
        print(f"Filtros aplicados: data='{data_filtro}', status='{status_filtro}', pagamento='{pagamento_filtro}', username='{username_filtro}'")
        
        # Obter lista de usuários para o filtro de username
        if current_user.is_admin:
            usuarios_filtro = Usuario.query.filter_by(ativo=True).all()
        else:
            usuarios_filtro = [current_user]
        
        # Construir a consulta base
        query = Agendamento.query.filter_by(ativo=True)
        
        # Aplicar filtro de usuário se não for admin
        if not current_user.is_admin:
            query = query.filter_by(id_usuario=current_user.id_usuario)
        
        # Aplicar filtro de username (novo filtro)
        if username_filtro:
            query = query.filter(Agendamento.id_usuario == username_filtro)
        
        # Aplicar filtro de data
        if data_filtro:
            try:
                data_obj = datetime.strptime(data_filtro, '%Y-%m-%d')
                query = query.filter(db.func.date(Agendamento.data_entrada) == data_obj.date())
            except ValueError:
                print(f"Erro: Data inválida: {data_filtro}")
        
        # Aplicar filtro de status
        if status_filtro:
            try:
                # Você pode implementar filtro de status se tiver no modelo
                pass
            except Exception as e:
                print(f"Erro ao aplicar filtro de status: {e}")
        
        # Aplicar filtro de pagamento
        if pagamento_filtro:
            try:
                query = query.join(Pagamento).filter(Pagamento.status == pagamento_filtro)
            except Exception as e:
                print(f"Erro ao aplicar filtro de pagamento: {e}")
        
        # Ordenar por data de entrada (mais recentes primeiro)
        query = query.order_by(desc(Agendamento.data_entrada))
        
        # Executar a consulta
        try:
            agendamentos = query.all()
            print(f"Total de agendamentos encontrados: {len(agendamentos)}")
        except Exception as e:
            print(f"Erro ao executar consulta: {e}")
            agendamentos = []
            
        # Calcular valores para os cards de resumo
        from datetime import date
        hoje = date.today()
        
        # Número total de agendamentos
        total_agendamentos = len(agendamentos)
        
        # Agendamentos de hoje
        agendamentos_hoje = sum(1 for a in agendamentos if a.data_entrada.date() == hoje)
        
        # Agendamentos dos próximos 7 dias
        proxima_semana = hoje + timedelta(days=7)
        agendamentos_semana = sum(1 for a in agendamentos if hoje <= a.data_entrada.date() <= proxima_semana)
        
        # Preparar a lista de agendamentos com as informações completas
        agendamentos_formatados = []
        
        for agendamento in agendamentos:
            # Obter o usuário e pet relacionados
            usuario = Usuario.query.get(agendamento.id_usuario)
            pet = Pet.query.get(agendamento.id_pet)
            
            # Obter informações de pagamento
            pagamento = Pagamento.query.filter_by(id_agendamento=agendamento.id_agendamento, ativo=True).first()
            
            # Definir formas de pagamento fictícias para agendamentos específicos para demonstração
            forma_pagamento = ""
            
            if pagamento:
                if agendamento.id_agendamento % 5 == 0:
                    forma_pagamento = "Cartão de Crédito"
                elif agendamento.id_agendamento % 5 == 1:
                    forma_pagamento = "Cartão de Débito"
                elif agendamento.id_agendamento % 5 == 2:
                    forma_pagamento = "Pix"
                elif agendamento.id_agendamento % 5 == 3:
                    forma_pagamento = "Dinheiro"
                elif agendamento.id_agendamento % 5 == 4:
                    forma_pagamento = "Boleto Bancário"
            
            # Criar o objeto de agendamento formatado para o template
            agendamento_formatado = {
                'id_agendamento': agendamento.id_agendamento,
                'id_usuario': agendamento.id_usuario,
                'usuario': {
                    'nome_user': usuario.nome_user if usuario else "Desconhecido"
                },
                'pet': {
                    'nome_pet': pet.nome_pet if pet else "Desconhecido"
                },
                'data_entrada': agendamento.data_entrada,
                'data_saida': agendamento.data_saida,
                'status': 'confirmado',  # Valor padrão para exibição
                'status_pagamento': pagamento.status if pagamento else 'pendente',
                'forma_pagamento': forma_pagamento  # Nova informação
            }
            
            agendamentos_formatados.append(agendamento_formatado)
            
        # Opções para o seletor de formas de pagamento
        formas_pagamento = ["Cartão de Crédito", "Cartão de Débito", "Pix", "Dinheiro", "Boleto Bancário"]
        
        # Opções para o seletor de status de pagamento
        status_pagamento = ["pendente", "pago"]
        
        # Renderizar o template com os dados formatados
        return render_template(
            'agendamentos_lista.html',
            agendamentos=agendamentos_formatados,
            data_filter=data_filtro,
            status_filter=status_filtro,
            pagamento_filter=pagamento_filtro,
            username_filter=username_filtro,
            formas_pagamento=formas_pagamento,
            status_pagamento=status_pagamento,
            usuarios_filtro=usuarios_filtro,  # Nova variável para o filtro de usuários
            current_page=1,
            total_pages=1,
            total_agendamentos=total_agendamentos,
            agendamentos_hoje=agendamentos_hoje,
            agendamentos_semana=agendamentos_semana
        )
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Erro ao listar agendamentos: {str(e)}")
        print(error_details)
        flash(f'Erro ao listar agendamentos: {str(e)}', 'danger')
        
        # Corrigir o redirecionamento
        return redirect(url_for('routes_bp.index'))

@routes_bp.route('/agendamentos-novo', methods=['GET'])
@login_required
def agendamentos_novo_html():
    # Listar todos os usuários (para o admin) ou apenas o usuário atual
    if current_user.is_admin:
        usuarios = Usuario.query.filter_by(ativo=True).all()
    else:
        usuarios = [current_user]
    
    # Listar todos os pets ou apenas os pets do usuário atual
    if current_user.is_admin:
        pets = Pet.query.filter_by(ativo=True).all()
    else:
        pets = Pet.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()
    
    # Listar todos os serviços ativos
    servicos = Servico.query.filter_by(ativo=True).all()
    
    return render_template(
        'form_agendamento.html',
        usuarios=usuarios,
        pets=pets,
        servicos=servicos,
        acao='novo',
        agendamento=None,
        servicos_selecionados=[],
        titulo="Novo Agendamento"
    )

# Função para visualizar detalhes de um agendamento - usando o formulário existente em modo somente leitura
@routes_bp.route('/agendamentos-detalhe/<int:id>', methods=['GET'])
@login_required
def agendamentos_detalhe_html(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    acesso_valido, _, _ = validar_acesso_agendamento(agendamento)
    if not acesso_valido:
        flash('Acesso negado ou agendamento não encontrado.', 'danger')
        return redirect(url_for('routes_bp.agendamentos_listar_html'))
    
    # Listar todos os usuários (para o admin) ou apenas o usuário atual
    if current_user.is_admin:
        usuarios = Usuario.query.filter_by(ativo=True).all()
    else:
        usuarios = [current_user]
    
    # Obter o pet e o usuário do agendamento
    pet = Pet.query.get(agendamento.id_pet)
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    # Listar todos os pets ou apenas os pets do usuário atual
    pets = Pet.query.filter_by(id_usuario=agendamento.id_usuario, ativo=True).all()
    
    # Listar todos os serviços ativos
    servicos = Servico.query.filter_by(ativo=True).all()
    
    # Obter serviços selecionados para este agendamento
    servicos_selecionados = []
    valor_total_servicos = 0
    
    for agendamento_servico in agendamento.servicos:
        if agendamento_servico.ativo:
            servico = Servico.query.get(agendamento_servico.id_servico)
            servicos_selecionados.append({
                'id_servico': servico.id_servico,
                'nome_servico': servico.nome_servico,
                'valor_hora': servico.valor_hora,
                'valor_dia': servico.valor_dia,
                'quantidade': agendamento_servico.quantidade,
                'valor': agendamento_servico.valor
            })
            valor_total_servicos += agendamento_servico.valor
    
    # Obter informações de pagamento
    pagamento = Pagamento.query.filter_by(id_agendamento=agendamento.id_agendamento, ativo=True).first()
    
    # Determinar a forma de pagamento fictícia
    forma_pagamento = ""
    if pagamento:
        if agendamento.id_agendamento % 5 == 0:
            forma_pagamento = "Cartão de Crédito"
        elif agendamento.id_agendamento % 5 == 1:
            forma_pagamento = "Cartão de Débito"
        elif agendamento.id_agendamento % 5 == 2:
            forma_pagamento = "Pix"
        elif agendamento.id_agendamento % 5 == 3:
            forma_pagamento = "Dinheiro"
        elif agendamento.id_agendamento % 5 == 4:
            forma_pagamento = "Boleto Bancário"
    
    return render_template(
        'form_agendamento.html',
        usuarios=usuarios,
        pets=pets,
        servicos=servicos,
        acao='visualizar',  # Modo somente leitura
        agendamento=agendamento,
        pet=pet,
        usuario=usuario,
        pagamento=pagamento,
        forma_pagamento=forma_pagamento,
        servicos_selecionados=servicos_selecionados,
        valor_total_servicos=valor_total_servicos,
        titulo="Detalhes do Agendamento"
    )

@routes_bp.route('/agendamentos-editar/<int:id>', methods=['GET'])
@login_required
def agendamentos_editar_html(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    acesso_valido, _, _ = validar_acesso_agendamento(agendamento)
    if not acesso_valido:
        flash('Acesso negado ou agendamento não encontrado.', 'danger')
        return redirect(url_for('routes_bp.agendamentos_listar_html'))
    
    # Listar todos os usuários (para o admin) ou apenas o usuário atual
    if current_user.is_admin:
        usuarios = Usuario.query.filter_by(ativo=True).all()
    else:
        usuarios = [current_user]
    
    # Listar todos os pets ou apenas os pets do usuário atual
    pets = Pet.query.filter_by(id_usuario=agendamento.id_usuario, ativo=True).all()
    
    # Listar todos os serviços ativos
    servicos = Servico.query.filter_by(ativo=True).all()
    
    # Obter serviços selecionados para este agendamento
    servicos_selecionados = []
    for agendamento_servico in agendamento.servicos:
        if agendamento_servico.ativo:
            servico = Servico.query.get(agendamento_servico.id_servico)
            servicos_selecionados.append({
                'id_servico': servico.id_servico,
                'nome_servico': servico.nome_servico,
                'valor_hora': servico.valor_hora,
                'valor_dia': servico.valor_dia,
                'quantidade': agendamento_servico.quantidade,
                'valor': agendamento_servico.valor
            })
    
    return render_template(
        'form_agendamento.html',
        usuarios=usuarios,
        pets=pets,
        servicos=servicos,
        acao='editar',
        agendamento=agendamento,
        servicos_selecionados=servicos_selecionados,
        titulo="Editar Agendamento"
    )

# Adicionando a rota para cancelar agendamento
@routes_bp.route('/agendamento/<int:id>/cancelar', methods=['GET'])
@login_required
def agendamento_cancelar_html(id):
    """Cancela um agendamento via interface web"""
    try:
        # Buscar o agendamento
        agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
        
        # Verificar permissões
        acesso_valido, _, _ = validar_acesso_agendamento(agendamento)
        if not acesso_valido:
            flash('Acesso negado ou agendamento não encontrado.', 'danger')
            return redirect(url_for('routes_bp.agendamentos_listar_html'))
        
        # Marcar agendamento como inativo (cancelado)
        agendamento.ativo = False
        
        # Marcar serviços do agendamento como inativos
        for agendamento_servico in agendamento.servicos:
            agendamento_servico.ativo = False
        
        # Salvar as alterações
        db.session.commit()
        
        # Mensagem de sucesso
        flash('Agendamento cancelado com sucesso!', 'success')
    except Exception as e:
        # Em caso de erro, fazer rollback e mostrar mensagem
        db.session.rollback()
        print(f"Erro ao cancelar agendamento: {str(e)}")
        flash(f'Erro ao cancelar agendamento: {str(e)}', 'danger')
    
    # Redirecionar para a lista de agendamentos
    return redirect(url_for('routes_bp.agendamentos_listar_html'))

# Rota alternativa (plural) para compatibilidade
@routes_bp.route('/agendamentos/<int:id>/cancelar', methods=['GET'])
@login_required
def agendamentos_cancelar_html(id):
    """Rota alternativa para cancelar agendamentos"""
    return agendamento_cancelar_html(id)