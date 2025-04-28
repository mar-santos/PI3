from flask import jsonify, request, render_template, redirect, url_for, Blueprint, flash
from app.models.models import Usuario, Pet
from app.models import db
from flask_login import login_required, current_user
import logging

# Configurar logging
logger = logging.getLogger(__name__)

routes_bp = Blueprint('routes_bp', __name__, template_folder='../templates')

@routes_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@routes_bp.route('/usuarios_html', methods=['GET'])
@login_required
def listar_usuarios_html():
    # Se for administrador, mostra todos os usuários
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        # Mostra todos os usuários, incluindo os inativos para administradores
        usuarios = Usuario.query.all()
        return render_template('lista_usuarios.html', usuarios=usuarios)
    # Se não for administrador, mostra apenas o próprio usuário
    else:
        usuarios = [Usuario.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).first()]
        if usuarios[0] is None:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('routes_bp.index'))
        return render_template('lista_usuarios.html', usuarios=usuarios)

@routes_bp.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    # Verificar se o usuário é administrador para listar todos, ou apenas seus próprios dados
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        usuarios = Usuario.query.all()  # Administradores veem todos os usuários
    else:
        usuarios = [Usuario.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).first()]

    resultado = []
    for usuario in usuarios:
        if usuario is None:
            continue
        pets = [pet.nome_pet for pet in usuario.pets if pet.ativo]
        usuario_data = {
            'id_usuario': usuario.id_usuario,
            'username': usuario.username,
            'nome_user': usuario.nome_user,
            'cpf': usuario.cpf,
            'endereco': usuario.endereco,
            'telefone': usuario.telefone,
            'email': usuario.email,
            'data_cadastro': usuario.data_cadastro.isoformat(),
            'ativo': usuario.ativo,  # Incluir status ativo
            'is_admin': usuario.is_admin,  # Incluir status de admin
            'pets': pets
        }
        resultado.append(usuario_data)
    return jsonify(resultado)

@routes_bp.route('/usuarios_html/<int:id>', methods=['GET'])
@login_required
def obter_usuario_html(id):
    # Verificar se o usuário é administrador ou está acessando seus próprios dados
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != id):
        flash('Acesso negado. Você só pode visualizar seu próprio cadastro.', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    # Administradores podem ver qualquer usuário, incluindo inativos
    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if usuario is None:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    pets = [pet.nome_pet for pet in usuario.pets if pet.ativo]
    usuario_data = {
        'id_usuario': usuario.id_usuario,
        'username': usuario.username,
        'nome_user': usuario.nome_user,
        'cpf': usuario.cpf,
        'endereco': usuario.endereco,
        'telefone': usuario.telefone,
        'email': usuario.email,
        'data_cadastro': usuario.data_cadastro.isoformat(),
        'ativo': usuario.ativo,
        'is_admin': usuario.is_admin,
        'pets': pets
    }

    return render_template('usuario_detalhe.html', usuario=usuario_data)

@routes_bp.route('/usuarios/<int:id>', methods=['GET'])
@login_required
def obter_usuario(id):
    # Verificar se o usuário é administrador ou está acessando seus próprios dados
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != id):
        return jsonify({'message': 'Acesso negado. Você só pode visualizar seu próprio cadastro.'}), 403

    # Administradores podem ver qualquer usuário
    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if usuario is None:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    pets = [pet.nome_pet for pet in usuario.pets if pet.ativo]
    usuario_data = {
        'id_usuario': usuario.id_usuario,
        'username': usuario.username,
        'nome_user': usuario.nome_user,
        'cpf': usuario.cpf,
        'endereco': usuario.endereco,
        'telefone': usuario.telefone,
        'email': usuario.email,
        'data_cadastro': usuario.data_cadastro.isoformat(),
        'ativo': usuario.ativo,
        'is_admin': usuario.is_admin,
        'pets': pets
    }
    return jsonify(usuario_data)

@routes_bp.route('/usuarios/cadastro', methods=['GET'])
def exibir_form_cadastro():
    return render_template('cadastro_usuario.html')

@routes_bp.route('/usuarios/cadastro', methods=['POST'])
def criar_usuario_html():
    # Coletar dados do formulário
    username = request.form.get('username')
    nome_user = request.form.get('nome_user')
    cpf = request.form.get('cpf')
    endereco = request.form.get('endereco')
    telefone = request.form.get('telefone')
    email = request.form.get('email')
    senha = request.form.get('senha')
    pets_str = request.form.get('pets', '')
    nomes_pets = [pet.strip() for pet in pets_str.split(',') if pet.strip()]

    # Verificar se o CPF já existe
    cpf_existente = Usuario.query.filter_by(cpf=cpf).first()
    if cpf_existente:
        valores_preenchidos = {
            'username': username,
            'nome_user': nome_user,
            'endereco': endereco,
            'telefone': telefone,
            'email': email,
            'pets': pets_str
        }
        flash('Este CPF já está cadastrado no sistema.', 'error')
        return render_template('cadastro_usuario.html', valores_preenchidos=valores_preenchidos)

    # Verificar se o username já existe
    username_existente = Usuario.query.filter_by(username=username).first()
    if username_existente:
        valores_preenchidos = {
            'nome_user': nome_user,
            'cpf': cpf,
            'endereco': endereco,
            'telefone': telefone,
            'email': email,
            'pets': pets_str
        }
        flash('Este nome de usuário já está em uso. Escolha outro.', 'error')
        return render_template('cadastro_usuario.html', valores_preenchidos=valores_preenchidos)

    # Verificar se o email já existe
    email_existente = Usuario.query.filter_by(email=email).first()
    if email_existente:
        valores_preenchidos = {
            'username': username,
            'nome_user': nome_user,
            'cpf': cpf,
            'endereco': endereco,
            'telefone': telefone,
            'pets': pets_str
        }
        flash('Este e-mail já está cadastrado. Utilize outro ou recupere sua senha.', 'error')
        return render_template('cadastro_usuario.html', valores_preenchidos=valores_preenchidos)

    # Se passou por todas as verificações, criar o usuário
    novo_usuario = Usuario(username=username, nome_user=nome_user, cpf=cpf, endereco=endereco,
                          telefone=telefone, email=email)
    novo_usuario.set_password(senha)

    try:
        db.session.add(novo_usuario)
        db.session.flush()  # Executa o SQL para obter o ID do usuário sem commitar a transação

        # Adicionar pets se houver
        for nome_pet in nomes_pets:
            novo_pet = Pet(id_usuario=novo_usuario.id_usuario, nome_pet=nome_pet)
            db.session.add(novo_pet)

        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {e}")
        flash(f'Erro ao criar usuário: {str(e)}', 'error')
        valores_preenchidos = {
            'username': username,
            'nome_user': nome_user,
            'cpf': cpf,
            'endereco': endereco,
            'telefone': telefone,
            'email': email,
            'pets': pets_str
        }
        return render_template('cadastro_usuario.html', valores_preenchidos=valores_preenchidos)

@routes_bp.route('/usuarios', methods=['POST'])
def criar_usuario():
    data = request.get_json()
    username = data.get('username')
    nome_user = data.get('nome_user')
    cpf = data.get('cpf')
    endereco = data.get('endereco')
    telefone = data.get('telefone')
    email = data.get('email')
    senha = data.get('senha')
    nomes_pets = data.get('pets', [])

    # Verificar se o CPF já existe
    cpf_existente = Usuario.query.filter_by(cpf=cpf).first()
    if cpf_existente:
        return jsonify({'message': 'Este CPF já está cadastrado no sistema.'}), 400

    # Verificar se o username já existe
    username_existente = Usuario.query.filter_by(username=username).first()
    if username_existente:
        return jsonify({'message': 'Este nome de usuário já está em uso. Escolha outro.'}), 400

    # Verificar se o email já existe
    email_existente = Usuario.query.filter_by(email=email).first()
    if email_existente:
        return jsonify({'message': 'Este e-mail já está cadastrado. Utilize outro ou recupere sua senha.'}), 400

    # Criar o usuário
    novo_usuario = Usuario(username=username, nome_user=nome_user, cpf=cpf, endereco=endereco,
                          telefone=telefone, email=email)
    novo_usuario.set_password(senha)

    try:
        db.session.add(novo_usuario)
        db.session.flush()

        for nome_pet in nomes_pets:
            novo_pet = Pet(id_usuario=novo_usuario.id_usuario, nome_pet=nome_pet)
            db.session.add(novo_pet)

        db.session.commit()
        return jsonify({'message': 'Usuário criado com sucesso'}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário API: {e}")
        return jsonify({'message': f'Erro ao criar usuário: {str(e)}'}), 400

@routes_bp.route('/usuarios/<int:id>/editar', methods=['GET'])
@login_required
def exibir_form_edicao(id):
    # Verificar se o usuário é administrador ou está editando seus próprios dados
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != id):
        flash('Acesso negado. Você só pode editar seu próprio cadastro.', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    # Administradores podem editar qualquer usuário, incluindo inativos
    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if usuario is None:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    pets = ', '.join([pet.nome_pet for pet in usuario.pets if pet.ativo])
    return render_template('editar_usuario.html', usuario=usuario, pets=pets)

@routes_bp.route('/usuarios/<int:id>', methods=['POST'])
@login_required
def atualizar_usuario(id):
    # Verificar permissões
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != id):
        flash('Acesso negado. Você só pode editar seu próprio cadastro.', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    
    # Buscar o usuário sem filtro de ativo
    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if not usuario:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    
    logger.info(f"Atualizando usuário {usuario.username} (ID: {id})")
    
    # Coletar os dados do formulário
    dados = {
        'username': request.form.get('username'),
        'nome_user': request.form.get('nome_user'),
        'cpf': request.form.get('cpf'),
        'endereco': request.form.get('endereco'),
        'telefone': request.form.get('telefone'),
        'email': request.form.get('email')
    }
    
    # Apenas administradores podem alterar status administrativos
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        dados['is_admin'] = 'is_admin' in request.form
        dados['ativo'] = 'ativo' in request.form
        logger.info(f"Status admin definido para: {dados['is_admin']}, status ativo definido para: {dados['ativo']}")
    
    # Verificar se deve alterar a senha
    alterar_senha = request.form.get('senha') and request.form.get('senha').strip()
    if alterar_senha:
        dados['senha'] = request.form.get('senha')
        logger.info(f"Solicitada alteração de senha para o usuário {usuario.username}")
    
    # Atualizar o usuário de forma segura usando o novo método
    if usuario.atualizar_usuario(dados, alterar_senha):
        try:
            db.session.commit()
            logger.info(f"Usuário {usuario.username} atualizado com sucesso")
            flash('Usuário atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar atualizações do usuário {usuario.username}: {e}")
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    else:
        logger.error(f"Falha ao atualizar dados do usuário {usuario.username}")
        flash('Erro ao atualizar usuário', 'error')
    
    return redirect(url_for('routes_bp.obter_usuario_html', id=id))

@routes_bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_usuario(id):
    # Verificar se o usuário é administrador ou está excluindo seu próprio cadastro
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != id):
        flash('Acesso negado. Você só pode excluir seu próprio cadastro.', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if usuario is None:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

    try:
        # Marcar o usuário como inativo em vez de excluí-lo
        usuario.ativo = False
        logger.info(f"Marcando usuário {usuario.username} como inativo")

        # Marcar todos os pets associados como inativos
        for pet in usuario.pets:
            pet.ativo = False
            logger.info(f"Marcando pet {pet.nome_pet} como inativo")

        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir usuário {usuario.username}: {e}")
        flash(f'Erro ao excluir usuário: {str(e)}', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))

# Rota de reset de senha para administradores
@routes_bp.route('/usuarios/<int:id>/reset_senha', methods=['POST'])
@login_required
def reset_senha_admin(id):
    # Apenas administradores podem redefinir senhas
    if not hasattr(current_user, "is_admin") or not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem redefinir senhas.', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    
    usuario = Usuario.query.filter_by(id_usuario=id).first()
    if not usuario:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    
    nova_senha = request.form.get('nova_senha')
    if not nova_senha or not nova_senha.strip():
        flash('A nova senha não pode estar vazia', 'error')
        return redirect(url_for('routes_bp.obter_usuario_html', id=id))
    
    try:
        usuario.set_password(nova_senha)
        db.session.commit()
        logger.info(f"Senha do usuário {usuario.username} redefinida por {current_user.username}")
        flash('Senha redefinida com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao redefinir senha para {usuario.username}: {e}")
        flash(f'Erro ao redefinir senha: {str(e)}', 'error')
    
    return redirect(url_for('routes_bp.obter_usuario_html', id=id))
