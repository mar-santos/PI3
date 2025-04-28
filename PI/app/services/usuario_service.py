# app/services/usuario_service.py
from app.models.models import Usuario
from werkzeug.security import generate_password_hash

def criar_usuario(username, nome_user, cpf, endereco, telefone, email, senha):
    novo_usuario = Usuario(
        username=username,
        nome_user=nome_user,
        cpf=cpf,
        endereco=endereco,
        telefone=telefone,
        email=email
    )
    novo_usuario.set_password(senha)
    return novo_usuario