# app/routes/routes_pets.py
from flask import jsonify, request, render_template, redirect, url_for, Blueprint, flash
from app.models.models import Pet, Usuario
from app.models import db
from flask_login import login_required, current_user
from base64 import b64encode

print("Carregando routes_pets.py")

routes_pets_bp = Blueprint('routes_pets_bp', __name__, template_folder='../templates')

print("Blueprint routes_pets_bp criado")

@routes_pets_bp.route('/test')
def test_route():
    print("Acessando rota de teste de pets")
    return "Rota de teste de pets funcionando!"

# Rotas HTML
@routes_pets_bp.route('/', methods=['GET'])
@login_required
def listar_pets_html():
    # Se for administrador, mostra todos os pets
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        pets = Pet.query.filter_by(ativo=True).all()
    # Se não for administrador, mostra apenas os pets do usuário
    else:
        pets = Pet.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()
    
    return render_template('lista_pets.html', pets=pets, b64encode=b64encode)

@routes_pets_bp.route('/<int:id>', methods=['GET'])
@login_required
def obter_pet_html(id):
    pet = Pet.query.filter_by(id_pet=id, ativo=True).first()
    if pet is None:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))
    
    # Verificar se o usuário é administrador ou dono do pet
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != pet.id_usuario):
        flash('Acesso negado. Você só pode visualizar seus próprios pets.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))
        
    return render_template('pet_detalhe.html', pet=pet, b64encode=b64encode)

@routes_pets_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastrar_pet():
    if request.method == 'GET':
        # Se for administrador, pode selecionar qualquer usuário
        if hasattr(current_user, "is_admin") and current_user.is_admin:
            usuarios = Usuario.query.filter_by(ativo=True).all()
        # Se não for administrador, só pode cadastrar pet para si mesmo
        else:
            usuarios = [Usuario.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).first()]
            
        return render_template('cadastro_pet.html', usuarios=usuarios)
    
    elif request.method == 'POST':
        nome_pet = request.form.get('nome_pet')
        id_usuario = request.form.get('id_usuario')
        
        # Verificar se o usuário está tentando cadastrar pet para outro usuário
        if not hasattr(current_user, "is_admin") or not current_user.is_admin:
            if int(id_usuario) != current_user.id_usuario:
                flash('Acesso negado. Você só pode cadastrar pets para si mesmo.', 'error')
                return redirect(url_for('routes_pets_bp.listar_pets_html'))
                
        raca = request.form.get('raca')
        idade = int(request.form.get('idade')) if request.form.get('idade') else None
        sexo = request.form.get('sexo')
        peso = float(request.form.get('peso')) if request.form.get('peso') else None
        castrado = request.form.get('castrado') == 'true'
        alimentacao = request.form.get('alimentacao')
        saude = request.form.get('saude')

        novo_pet = Pet(
            nome_pet=nome_pet,
            id_usuario=id_usuario,
            raca=raca,
            idade=idade,
            sexo=sexo,
            peso=peso,
            castrado=castrado,
            alimentacao=alimentacao,
            saude=saude,
            ativo=True
        )

        if 'foto_pet' in request.files:
            foto = request.files['foto_pet']
            if foto.filename != '':
                novo_pet.foto_pet = foto.read()

        try:
            db.session.add(novo_pet)
            db.session.commit()
            flash('Pet cadastrado com sucesso!', 'success')
            return redirect(url_for('routes_pets_bp.listar_pets_html'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar pet: {str(e)}', 'error')
            return redirect(url_for('routes_pets_bp.cadastrar_pet'))

@routes_pets_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_pet(id):
    pet = Pet.query.filter_by(id_pet=id, ativo=True).first()
    if pet is None:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))
        
    # Verificar se o usuário é administrador ou dono do pet
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != pet.id_usuario):
        flash('Acesso negado. Você só pode editar seus próprios pets.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))

    if request.method == 'GET':
        # Se for administrador, pode selecionar qualquer usuário
        if hasattr(current_user, "is_admin") and current_user.is_admin:
            usuarios = Usuario.query.filter_by(ativo=True).all()
        # Se não for administrador, só pode manter o pet associado a si mesmo
        else:
            usuarios = [Usuario.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).first()]
            
        return render_template('editar_pet.html', pet=pet, usuarios=usuarios, b64encode=b64encode)
    
    elif request.method == 'POST':
        pet.nome_pet = request.form.get('nome_pet')
        id_usuario = request.form.get('id_usuario')
        
        # Verificar se o usuário está tentando alterar o dono do pet
        if not hasattr(current_user, "is_admin") or not current_user.is_admin:
            if int(id_usuario) != current_user.id_usuario:
                flash('Acesso negado. Você não pode transferir o pet para outro usuário.', 'error')
                return redirect(url_for('routes_pets_bp.listar_pets_html'))
                
        pet.id_usuario = id_usuario
        pet.raca = request.form.get('raca')
        pet.idade = int(request.form.get('idade')) if request.form.get('idade') else None
        pet.sexo = request.form.get('sexo')
        pet.peso = float(request.form.get('peso')) if request.form.get('peso') else None
        pet.castrado = request.form.get('castrado') == 'true'
        pet.alimentacao = request.form.get('alimentacao')
        pet.saude = request.form.get('saude')

        if 'foto_pet' in request.files:
            foto = request.files['foto_pet']
            if foto.filename != '':
                pet.foto_pet = foto.read()

        try:
            db.session.commit()
            flash('Pet atualizado com sucesso!', 'success')
            return redirect(url_for('routes_pets_bp.obter_pet_html', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar pet: {str(e)}', 'error')
            return redirect(url_for('routes_pets_bp.editar_pet', id=id))

@routes_pets_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_pet(id):
    pet = Pet.query.filter_by(id_pet=id, ativo=True).first()
    if pet is None:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))
        
    # Verificar se o usuário é administrador ou dono do pet
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != pet.id_usuario):
        flash('Acesso negado. Você só pode excluir seus próprios pets.', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))

    try:
        pet.ativo = False  # Soft delete
        db.session.commit()
        flash('Pet excluído com sucesso!', 'success')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir pet: {str(e)}', 'error')
        return redirect(url_for('routes_pets_bp.listar_pets_html'))

# Rotas API
@routes_pets_bp.route('/api/pets', methods=['GET'])
@login_required
def listar_pets():
    # Se for administrador, mostra todos os pets
    if hasattr(current_user, "is_admin") and current_user.is_admin:
        pets = Pet.query.filter_by(ativo=True).all()
    # Se não for administrador, mostra apenas os pets do usuário
    else:
        pets = Pet.query.filter_by(id_usuario=current_user.id_usuario, ativo=True).all()
        
    resultado = [{
        'id_pet': pet.id_pet,
        'nome_pet': pet.nome_pet,
        'id_usuario': pet.id_usuario,
        'data_cadastro': pet.data_cadastro.isoformat()
    } for pet in pets]
    return jsonify(resultado)

@routes_pets_bp.route('/api/pets/<int:id>', methods=['GET'])
@login_required
def obter_pet(id):
    pet = Pet.query.filter_by(id_pet=id, ativo=True).first()
    if pet is None:
        return jsonify({'message': 'Pet não encontrado'}), 404
        
    # Verificar se o usuário é administrador ou dono do pet
    if not hasattr(current_user, "is_admin") or (not current_user.is_admin and current_user.id_usuario != pet.id_usuario):
        return jsonify({'message': 'Acesso negado. Você só pode visualizar seus próprios pets.'}), 403
        
    pet_data = {
        'id_pet': pet.id_pet,
        'nome_pet': pet.nome_pet,
        'id_usuario': pet.id_usuario,
        'data_cadastro': pet.data_cadastro.isoformat()
    }
    return jsonify(pet_data)

@routes_pets_bp.route('/api/pets', methods=['POST'])
@login_required
def criar_pet():
    data = request.get_json()
    nome_pet = data.get('nome_pet')
    id_usuario = data.get('id_usuario')
    
    # Verificar se o usuário está tentando cadastrar pet para outro usuário
    if not hasattr(current_user, "is_admin") or not current_user.is_admin:
        if int(id_usuario) != current_user.id_usuario:
            return jsonify({'message': 'Acesso negado. Você só pode cadastrar pets para si mesmo.'}), 403

    novo_pet = Pet(nome_pet=nome_pet, id_usuario=id_usuario)

    try:
        db.session.add(novo_pet)
        db.session.commit()
        return jsonify({'message': 'Pet criado com sucesso'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao criar pet: {str(e)}'}), 400