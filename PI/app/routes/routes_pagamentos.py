from flask import jsonify, request, render_template, redirect, url_for, flash
from app.routes.routes_usuarios import routes_bp
from app.models.models import Usuario, Agendamento, Pagamento, Pet
from app.models import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import case

# API routes
@routes_bp.route('/api/pagamentos', methods=['GET'])
@login_required
def pagamentos_listar_api():
    # Obter filtros da query
    status_filter = request.args.get('status', '')
    data_inicial = request.args.get('data_inicial', '')
    data_final = request.args.get('data_final', '')
    
    # Base query
    query = Pagamento.query.filter_by(ativo=True)
    
    # Aplicar filtros
    if status_filter and status_filter != 'todos':
        query = query.filter(Pagamento.status == status_filter)
    
    if data_inicial:
        data_inicial_dt = datetime.strptime(data_inicial, '%Y-%m-%d')
        query = query.filter(Pagamento.data_pagamento >= data_inicial_dt)
    
    if data_final:
        data_final_dt = datetime.strptime(data_final, '%Y-%m-%d')
        # Adicionar 1 dia para incluir o último dia completo
        data_final_dt = data_final_dt + timedelta(days=1)
        query = query.filter(Pagamento.data_pagamento < data_final_dt)
    
    # Verificar permissões
    if not current_user.is_admin:
        # Para usuários normais, buscar apenas pagamentos dos próprios agendamentos
        agendamentos_ids = [a.id_agendamento for a in Agendamento.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()]
        query = query.filter(Pagamento.id_agendamento.in_(agendamentos_ids))
    
    pagamentos = query.all()
    
    resultado = []
    for pagamento in pagamentos:
        agendamento = Agendamento.query.get(pagamento.id_agendamento)
        usuario = Usuario.query.get(agendamento.id_usuario)
        
        pagamento_data = {
            'id_pagamento': pagamento.id_pagamento,
            'agendamento': {
                'id_agendamento': agendamento.id_agendamento,
                'data_entrada': agendamento.data_entrada.strftime('%Y-%m-%d %H:%M'),
                'data_saida': agendamento.data_saida.strftime('%Y-%m-%d %H:%M')
            },
            'usuario': {
                'id_usuario': usuario.id_usuario,
                'nome_user': usuario.nome_user
            },
            'valor': pagamento.valor,
            'status': pagamento.status,
            'data_pagamento': pagamento.data_pagamento.strftime('%Y-%m-%d %H:%M') if pagamento.data_pagamento else None
        }
        resultado.append(pagamento_data)
    
    return jsonify(resultado)

@routes_bp.route('/api/pagamentos/<int:id>', methods=['GET'])
@login_required
def pagamentos_obter_api(id):
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    
    if pagamento is None:
        return jsonify({'message': 'Pagamento não encontrado'}), 404
    
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verifica se o usuário tem permissão para ver este pagamento
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        return jsonify({'message': 'Acesso negado. Você não tem permissão para ver este pagamento.'}), 403
    
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    pagamento_data = {
        'id_pagamento': pagamento.id_pagamento,
        'agendamento': {
            'id_agendamento': agendamento.id_agendamento,
            'data_entrada': agendamento.data_entrada.strftime('%Y-%m-%d %H:%M'),
            'data_saida': agendamento.data_saida.strftime('%Y-%m-%d %H:%M')
        },
        'usuario': {
            'id_usuario': usuario.id_usuario,
            'nome_user': usuario.nome_user
        },
        'valor': pagamento.valor,
        'status': pagamento.status,
        'data_pagamento': pagamento.data_pagamento.strftime('%Y-%m-%d %H:%M') if pagamento.data_pagamento else None
    }
    
    return jsonify(pagamento_data)

@routes_bp.route('/api/pagamentos/<int:id>/confirmar', methods=['PUT'])
@login_required
def pagamentos_confirmar_api(id):
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    
    if pagamento is None:
        return jsonify({'message': 'Pagamento não encontrado'}), 404
    
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Permitir que usuários confirmem seus próprios pagamentos
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        return jsonify({'message': 'Acesso negado. Você não tem permissão para confirmar este pagamento.'}), 403
    
    pagamento.status = 'pago'
    pagamento.data_pagamento = datetime.now()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Pagamento confirmado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao confirmar pagamento: {str(e)}'}), 400

@routes_bp.route('/api/pagamentos/<int:id>/recibo', methods=['GET'])
@login_required
def pagamento_recibo_api(id):
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    
    if pagamento is None:
        return jsonify({'status': 'error', 'message': 'Pagamento não encontrado'}), 404
    
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verificar permissão
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        return jsonify({'status': 'error', 'message': 'Acesso não autorizado'}), 403
    
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    # Formatar os dados para o recibo
    pagamento_data = {
        'id_pagamento': pagamento.id_pagamento,
        'id_agendamento': pagamento.id_agendamento,
        'cliente': usuario.nome_user,
        'valor': pagamento.valor,
        'status': pagamento.status,
        'tipo_pagamento': pagamento.tipo_pagamento if hasattr(pagamento, 'tipo_pagamento') else None,
        'data_pagamento': pagamento.data_pagamento.isoformat() if pagamento.data_pagamento else None,
        'data_criacao': pagamento.data_criacao.isoformat() if hasattr(pagamento, 'data_criacao') else datetime.now().isoformat()
    }
    
    return jsonify({
        'status': 'success',
        'pagamento': pagamento_data
    })

# HTML routes
@routes_bp.route('/pagamentos-lista', methods=['GET'])
@login_required
def pagamentos_listar_html():
    try:
        # Adicionar logs para diagnóstico
        print("\n=== LISTAGEM DE PAGAMENTOS ===")
        print(f"Usuário: ID={current_user.id_usuario}, Admin={current_user.is_admin}")
        
        # Obter filtros da query
        status_filter = request.args.get('status', '')
        data_inicial = request.args.get('data_inicial', '')
        data_final = request.args.get('data_final', '')
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Itens por página
        
        print(f"Filtros: status='{status_filter}', data_inicial='{data_inicial}', data_final='{data_final}'")
        
        # Iniciar a query base - MODIFICAÇÃO: Remover filtro inicial
        # Em vez de filtrar por ativo=True inicialmente, vamos buscar todos os pagamentos
        query = Pagamento.query
        
        # Verificar total de pagamentos no banco antes de aplicar filtros
        total_pagamentos = query.count()
        print(f"Total de pagamentos no banco: {total_pagamentos}")
        
        # Agora aplicamos o filtro ativo
        query = query.filter_by(ativo=True)
        total_ativos = query.count()
        print(f"Total de pagamentos ativos: {total_ativos}")
        
        # Aplicar filtros
        if status_filter and status_filter != 'todos':
            query = query.filter(Pagamento.status == status_filter)
            print(f"Após filtro de status: {query.count()} pagamentos")
        
        if data_inicial:
            try:
                data_inicial_dt = datetime.strptime(data_inicial, '%Y-%m-%d')
                query = query.filter(db.or_(
                    Pagamento.data_pagamento >= data_inicial_dt,
                    Pagamento.data_pagamento == None
                ))
                print(f"Após filtro de data inicial: {query.count()} pagamentos")
            except ValueError:
                flash('Formato de data inicial inválido. Use YYYY-MM-DD.', 'warning')
        
        if data_final:
            try:
                data_final_dt = datetime.strptime(data_final, '%Y-%m-%d')
                # Adicionar 1 dia ao final para incluir todo o último dia
                data_final_dt = data_final_dt + timedelta(days=1)
                query = query.filter(db.or_(
                    Pagamento.data_pagamento < data_final_dt,
                    Pagamento.data_pagamento == None
                ))
                print(f"Após filtro de data final: {query.count()} pagamentos")
            except ValueError:
                flash('Formato de data final inválido. Use YYYY-MM-DD.', 'warning')
        
        # Verificar permissões
        if not current_user.is_admin:
            # Para usuários normais, buscar apenas pagamentos dos próprios agendamentos
            agendamentos_ids = [a.id_agendamento for a in Agendamento.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()]
            query = query.filter(Pagamento.id_agendamento.in_(agendamentos_ids))
            print(f"Após filtro de permissão: {query.count()} pagamentos")
        
        # Ordenação: pagamentos pendentes primeiro, depois por data mais recente
        query = query.order_by(
            case((Pagamento.status == 'pendente', 1), else_=2),
            Pagamento.id_pagamento.desc()  # Simplificar a ordenação para evitar erros
        )
        
        # Calcular totais (todos os pagamentos que atendem aos filtros, sem paginação)
        all_pagamentos = query.all()
        print(f"Total de pagamentos após aplicar todos os filtros: {len(all_pagamentos)}")
        
        total_pago = sum(p.valor for p in all_pagamentos if p.status == 'pago')
        total_pendente = sum(p.valor for p in all_pagamentos if p.status == 'pendente')
        
        print(f"Total pago: R$ {total_pago}, Total pendente: R$ {total_pendente}")
        
        # Aplicar paginação
        paginated_pagamentos = query.paginate(page=page, per_page=per_page)
        
        # Preparar dados para a view
        pagamentos_data = []
        for pagamento in paginated_pagamentos.items:
            try:
                # Garantir dados atualizados
                db.session.refresh(pagamento)
                agendamento = Agendamento.query.get(pagamento.id_agendamento)
                
                if agendamento:
                    usuario = Usuario.query.get(agendamento.id_usuario)
                    
                    pagamento_data = {
                        'id_pagamento': pagamento.id_pagamento,
                        'agendamento': agendamento,
                        'usuario': usuario,
                        'valor': pagamento.valor,
                        'status': pagamento.status,
                        'data_pagamento': pagamento.data_pagamento
                    }
                    pagamentos_data.append(pagamento_data)
                    print(f"Adicionado pagamento ID={pagamento.id_pagamento} ao resultado")
                else:
                    print(f"ATENÇÃO: Agendamento não encontrado para o pagamento ID={pagamento.id_pagamento}")
            except Exception as item_e:
                print(f"Erro ao processar pagamento: {str(item_e)}")
        
        print(f"Total de pagamentos para exibição: {len(pagamentos_data)}")
        print("=== FIM DA LISTAGEM DE PAGAMENTOS ===\n")
        
        return render_template(
            'lista_pagamentos.html',
            pagamentos=pagamentos_data,
            total_pagamentos=len(all_pagamentos),
            total_pago=total_pago,
            total_pendente=total_pendente,
            current_page=page,
            total_pages=paginated_pagamentos.pages or 1,
            status_filter=status_filter,
            data_inicial=data_inicial,
            data_final=data_final
        )
    except Exception as e:
        import traceback
        print(f"ERRO ao listar pagamentos: {str(e)}")
        print(traceback.format_exc())
        flash(f'Erro ao listar pagamentos: {str(e)}', 'error')
        return render_template('lista_pagamentos.html', 
                               pagamentos=[], 
                               total_pagamentos=0,
                               total_pago=0, 
                               total_pendente=0, 
                               current_page=1, 
                               total_pages=1,
                               status_filter='',
                               data_inicial='',
                               data_final='')

@routes_bp.route('/pagamentos/<int:id>/detalhes', methods=['GET'])
@login_required
def pagamentos_detalhar_html(id):
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    
    if pagamento is None:
        flash('Pagamento não encontrado', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verifica se o usuário tem permissão para ver este pagamento
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        flash('Acesso negado. Você não tem permissão para ver este pagamento.', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Buscar usuário do agendamento - SOLUÇÃO DO ERRO
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    # Pet associado ao agendamento (se existir)
    pet = None
    if agendamento.id_pet:
        pet = Pet.query.get(agendamento.id_pet)
    
    return render_template('form_pagamento.html',
                          pagamento=pagamento,
                          agendamento=agendamento,
                          usuario=usuario,  # Adicionando usuário ao contexto
                          pet=pet,
                          modo='visualizar')

@routes_bp.route('/pagamentos/<int:id>/confirmar', methods=['POST'])
@login_required
def pagamentos_confirmar_post(id):
    # Obter o pagamento
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    if not pagamento:
        flash('Pagamento não encontrado.', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Obter o agendamento associado
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verificar permissões - Usuários normais podem confirmar seus próprios pagamentos
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        flash('Acesso negado. Você não tem permissão para confirmar este pagamento.', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Verificar se já foi pago
    if pagamento.status == 'pago':
        flash('Este pagamento já foi confirmado.', 'warning')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Obter dados do formulário
    tipo_pagamento = request.form.get('tipo_pagamento')
    observacoes = request.form.get('observacoes', '')
    
    # Atualizar o pagamento
    pagamento.status = 'pago'
    pagamento.tipo_pagamento = tipo_pagamento
    pagamento.observacoes = observacoes
    pagamento.data_pagamento = datetime.now()
    
    try:
        db.session.commit()
        flash('Pagamento confirmado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao confirmar pagamento: {str(e)}', 'danger')
    
    return redirect(url_for('routes_bp.pagamentos_listar_html'))

@routes_bp.route('/pagamentos/<int:id>/confirmar', methods=['GET'])
@login_required
def pagamentos_confirmar_html(id):
    # Obter o pagamento
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    if not pagamento:
        flash('Pagamento não encontrado.', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Obter o agendamento associado
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verificar permissões
    # Usuários normais podem confirmar seus próprios pagamentos
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        flash('Acesso negado. Você não tem permissão para confirmar este pagamento.', 'danger')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    # Obter usuário associado ao agendamento
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    return render_template('form_confirmar_pagamento.html',
                          pagamento=pagamento,
                          agendamento=agendamento,
                          usuario=usuario,
                          titulo="Confirmar Pagamento")

@routes_bp.route('/pagamentos/<int:id>/recibo', methods=['GET'])
@login_required
def pagamento_recibo_html(id):
    pagamento = Pagamento.query.filter_by(id_pagamento=id, ativo=True).first()
    
    if pagamento is None:
        flash('Pagamento não encontrado', 'error')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    agendamento = Agendamento.query.get(pagamento.id_agendamento)
    
    # Verificar permissão
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        flash('Acesso negado. Você não tem permissão para ver este recibo.', 'error')
        return redirect(url_for('routes_bp.pagamentos_listar_html'))
    
    usuario = Usuario.query.get(agendamento.id_usuario)
    
    return render_template('recibo_pagamento.html',
                          pagamento=pagamento,
                          agendamento=agendamento,
                          cliente=usuario.nome_user)

# Rota para processar pagamento a partir da lista de agendamentos
@routes_bp.route('/agendamento/<int:id>/pagamento', methods=['GET'])
@login_required
def agendamento_pagamento_html(id):
    agendamento = Agendamento.query.filter_by(id_agendamento=id, ativo=True).first()
    
    if agendamento is None:
        flash('Agendamento não encontrado.', 'danger')
        return redirect(url_for('routes_bp.agendamentos_listar_html'))
    
    if not current_user.is_admin and agendamento.id_usuario != current_user.id_usuario:
        flash('Acesso negado. Você não tem permissão para pagar este agendamento.', 'danger')
        return redirect(url_for('routes_bp.agendamentos_listar_html'))
    
    # Se o agendamento já tem um pagamento
    pagamento = Pagamento.query.filter_by(id_agendamento=id, ativo=True).first()
    if pagamento:
        # Se o pagamento já foi feito, redireciona para o recibo
        if pagamento.status == 'pago':
            flash('Este agendamento já foi pago!', 'info')
            return redirect(url_for('routes_bp.pagamento_recibo_html', id=pagamento.id_pagamento))
        
        # Se o pagamento está pendente, redireciona para a tela de confirmação
        return redirect(url_for('routes_bp.pagamentos_confirmar_html', id=pagamento.id_pagamento))
    
    # Se chegou aqui, o agendamento não tem pagamento (o que não deveria acontecer)
    flash('Não foi encontrado pagamento para este agendamento!', 'warning')
    return redirect(url_for('routes_bp.agendamentos_listar_html'))

# Função auxiliar para validar acesso ao agendamento
def validar_acesso_agendamento(agendamento):
    if not agendamento:
        return False, "Agendamento não encontrado.", 404
    
    # Administradores podem acessar qualquer agendamento
    if current_user.is_admin:
        return True, "", 200
    
    # Usuários normais só podem acessar seus próprios agendamentos
    if agendamento.id_usuario != current_user.id_usuario:
        return False, "Você não tem permissão para acessar este agendamento.", 403
    
    return True, "", 200