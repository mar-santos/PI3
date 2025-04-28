# app/routes/routes_servicos.py
from flask import jsonify, request, render_template, flash, redirect, url_for
from app.routes import routes_bp
from app.models.models import Servico
from app.models import db
from flask_login import login_required, current_user
from functools import wraps

# Decorator para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso permitido apenas para administradores', 'error')
            return redirect(url_for('routes_bp.index'))
        return f(*args, **kwargs)
    return decorated_function

@routes_bp.route('/servicos', methods=['GET'])
@login_required
@admin_required
def listar_servicos():
    servicos = Servico.query.filter_by(ativo=True).all()
    resultado = []
    for servico in servicos:
        servico_data = {
            'id_servico': servico.id_servico,
            'nome_servico': servico.nome_servico,
            'descricao': servico.descricao,
            'valor_hora': servico.valor_hora,
            'valor_dia': servico.valor_dia
        }
        resultado.append(servico_data)
    return jsonify(resultado)

@routes_bp.route('/servicos/<int:id>', methods=['GET'])
@login_required
@admin_required
def obter_servico(id):
    servico = Servico.query.filter_by(id_servico=id, ativo=True).first()
    if servico is None:
        return jsonify({'message': 'Serviço não encontrado'}), 404

    servico_data = {
        'id_servico': servico.id_servico,
        'nome_servico': servico.nome_servico,
        'descricao': servico.descricao,
        'valor_hora': servico.valor_hora,
        'valor_dia': servico.valor_dia
    }
    return jsonify(servico_data)

@routes_bp.route('/servicos', methods=['POST'])
@login_required
@admin_required
def cadastrar_servico():
    data = request.get_json()
    
    # Verifica se os dados necessários foram enviados
    if not data or 'nome_servico' not in data:
        return jsonify({'message': 'Dados incompletos. Nome do serviço é obrigatório'}), 400
    
    # Cria uma nova instância de Serviço
    novo_servico = Servico(
        nome_servico=data['nome_servico'],
        descricao=data.get('descricao', ''),
        valor_hora=data.get('valor_hora', 0.0),
        valor_dia=data.get('valor_dia', 0.0),
        ativo=True
    )
    
    try:
        # Adiciona à sessão e comita
        db.session.add(novo_servico)
        db.session.commit()
        
        # Retorna o serviço criado
        servico_data = {
            'id_servico': novo_servico.id_servico,
            'nome_servico': novo_servico.nome_servico,
            'descricao': novo_servico.descricao,
            'valor_hora': novo_servico.valor_hora,
            'valor_dia': novo_servico.valor_dia
        }
        
        return jsonify(servico_data), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao cadastrar serviço: {str(e)}'}), 400
    
@routes_bp.route('/servicos/<int:id>', methods=['PUT'])
@login_required
@admin_required
def atualizar_servico(id):
    servico = Servico.query.filter_by(id_servico=id, ativo=True).first()
    if servico is None:
        return jsonify({'message': 'Serviço não encontrado'}), 404

    data = request.get_json()
    
    # Atualiza os campos se fornecidos
    if 'nome_servico' in data:
        servico.nome_servico = data['nome_servico']
    if 'descricao' in data:
        servico.descricao = data['descricao']
    if 'valor_hora' in data:
        servico.valor_hora = data['valor_hora']
    if 'valor_dia' in data:
        servico.valor_dia = data['valor_dia']
    
    try:
        db.session.commit()
        
        servico_data = {
            'id_servico': servico.id_servico,
            'nome_servico': servico.nome_servico,
            'descricao': servico.descricao,
            'valor_hora': servico.valor_hora,
            'valor_dia': servico.valor_dia
        }
        
        return jsonify(servico_data), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao atualizar serviço: {str(e)}'}), 400


@routes_bp.route('/servicos/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def excluir_servico(id):
    servico = Servico.query.filter_by(id_servico=id, ativo=True).first()
    if servico is None:
        return jsonify({'message': 'Serviço não encontrado'}), 404

    servico.ativo = False
    try:
        db.session.commit()
        return jsonify({'message': 'Serviço marcado como inativo'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao marcar serviço como inativo: {str(e)}'}), 400

# Novas rotas para renderizar as páginas HTML

@routes_bp.route('/servicos/html', methods=['GET'])
@login_required
@admin_required
def listar_servicos_html():
    servicos = Servico.query.filter_by(ativo=True).all()
    return render_template('lista_servicos.html', servicos=servicos)

@routes_bp.route('/servicos/cadastrar', methods=['GET'])
@login_required
@admin_required
def cadastrar_servico_form():
    return render_template('form_servico.html', titulo='Cadastrar Novo Serviço', servico=None)

@routes_bp.route('/servicos/<int:id>/editar', methods=['GET'])
@login_required
@admin_required
def editar_servico_form(id):
    servico = Servico.query.filter_by(id_servico=id, ativo=True).first()
    if servico is None:
        # Caso não encontre o serviço, retorna uma mensagem de erro
        return render_template('error.html', mensagem='Serviço não encontrado'), 404
    return render_template('form_servico.html', titulo='Editar Serviço', servico=servico)