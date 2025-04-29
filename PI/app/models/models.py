# app/models/models.py
from . import db
from sqlalchemy import event
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'USUARIO'
    id_usuario = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    nome_user = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    foto_user = db.Column(db.LargeBinary)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=db.func.datetime('now'))
    ativo = db.Column(db.Boolean, default=True)
    pets = db.relationship('Pet', backref='usuario', lazy=True)
    agendamentos = db.relationship('Agendamento', backref='usuario', lazy=True)
    is_admin = db.Column(db.Boolean, default=False) 

    def get_id(self):
        return str(self.id_usuario)

    def set_password(self, senha):
        try:
            self.senha_hash = generate_password_hash(senha)
            logger.info(f"Senha definida com sucesso para o usuário {self.username}")
        except Exception as e:
            logger.error(f"Erro ao definir senha para o usuário {self.username}: {e}")
            raise ValueError(f"Não foi possível definir a senha: {str(e)}")

    def check_password(self, senha):
        try:
            return check_password_hash(self.senha_hash, senha)
        except Exception as e:
            logger.error(f"Erro ao verificar senha para o usuário {self.username}: {e}")
            return False

    def atualizar_usuario(self, dados, alterar_senha=False):
        try:
            # Backup do estado original para log de alterações significativas
            original_is_admin = self.is_admin
            original_ativo = self.ativo
            
            # Atualizar campos básicos
            if 'username' in dados and dados['username']:
                self.username = dados['username']
            if 'nome_user' in dados and dados['nome_user']:
                self.nome_user = dados['nome_user']
            if 'cpf' in dados and dados['cpf']:
                self.cpf = dados['cpf']
            if 'endereco' in dados:
                self.endereco = dados['endereco']
            if 'telefone' in dados:
                self.telefone = dados['telefone']
            if 'email' in dados and dados['email']:
                self.email = dados['email']
                
            # Atualizações de status administrativas
            if 'ativo' in dados:
                self.ativo = bool(dados['ativo'])
                if original_ativo != self.ativo:
                    logger.info(f"Status ativo do usuário {self.username} alterado: {original_ativo} -> {self.ativo}")
            
            if 'is_admin' in dados:
                new_is_admin = bool(dados['is_admin'])
                if original_is_admin != new_is_admin:
                    logger.info(f"Status de administrador do usuário {self.username} alterado: {original_is_admin} -> {new_is_admin}")
                self.is_admin = new_is_admin
            
            # Tratar a senha separadamente, apenas se explicitamente solicitado
            if alterar_senha and 'senha' in dados and dados['senha'] and dados['senha'].strip():
                self.set_password(dados['senha'])
                logger.info(f"Senha alterada para o usuário {self.username}")
                
            return True
        except Exception as e:
            # Registrar o erro e retornar falha
            logger.error(f"Erro ao atualizar usuário {self.username}: {e}")
            return False

    def __repr__(self):
        return f'<Usuario {self.username}>'

class Pet(db.Model):
    __tablename__ = 'PET'
    id_pet = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('USUARIO.id_usuario', ondelete='CASCADE'), nullable=False)
    nome_pet = db.Column(db.String(120), nullable=False)
    raca = db.Column(db.String(120))
    idade = db.Column(db.Integer)
    sexo = db.Column(db.String(20))
    peso = db.Column(db.Float)
    castrado = db.Column(db.Boolean)
    alimentacao = db.Column(db.Text)
    saude = db.Column(db.Text)
    foto_pet = db.Column(db.LargeBinary)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=db.func.datetime('now'))
    agendamentos = db.relationship('Agendamento', backref='pet', lazy=True)

    def __repr__(self):
        return f'<Pet {self.nome_pet}>'

class Servico(db.Model):
    __tablename__ = 'SERVICO'
    id_servico = db.Column(db.Integer, primary_key=True)
    nome_servico = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    valor_hora = db.Column(db.Float)
    valor_dia = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Servico {self.nome_servico}>'

class Agendamento(db.Model):
    __tablename__ = 'AGENDAMENTO'
    id_agendamento = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('USUARIO.id_usuario'), nullable=False)
    id_pet = db.Column(db.Integer, db.ForeignKey('PET.id_pet'), nullable=False)
    data_entrada = db.Column(db.DateTime, nullable=False)
    data_saida = db.Column(db.DateTime, nullable=False)
    observacoes = db.Column(db.Text)
    valor_total = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)
    servicos = db.relationship('AgendamentoServico', backref='agendamento', lazy=True)
    pagamento = db.relationship('Pagamento', backref='agendamento', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Agendamento {self.id_agendamento}>'

class AgendamentoServico(db.Model):
    __tablename__ = 'AGENDAMENTO_SERVICO'
    id_agendamento = db.Column(db.Integer, db.ForeignKey('AGENDAMENTO.id_agendamento'), primary_key=True)
    id_servico = db.Column(db.Integer, db.ForeignKey('SERVICO.id_servico'), primary_key=True)
    quantidade = db.Column(db.Integer)
    valor = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)
    servico = relationship("Servico")

    def __repr__(self):
        return f'<AgendamentoServico {self.id_agendamento}-{self.id_servico}>'

class Pagamento(db.Model):
    __tablename__ = 'PAGAMENTO'
    id_pagamento = db.Column(db.Integer, primary_key=True)
    id_agendamento = db.Column(db.Integer, db.ForeignKey('AGENDAMENTO.id_agendamento'), nullable=False)
    data_pagamento = db.Column(db.DateTime)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    tipo_pagamento = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=db.func.datetime('now'))
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Pagamento {self.id_pagamento}>'

# Versão melhorada do evento before_flush
@event.listens_for(db.Session, 'before_flush')
def before_flush(session, flush_context, instances):
    for instance in session.dirty:
        if isinstance(instance, Usuario):
            # Verificar se o objeto é um usuário e tem uma senha_hash
            if hasattr(instance, 'senha_hash') and instance.senha_hash:
                # IMPORTANTE: Este código é perigoso e deve ser removido após corrigir todos os usuários
                # Ele detecta senhas em texto puro e as converte para hash
                # Uma verificação mais segura poderia ser:
                if not instance.senha_hash.startswith(('pbkdf2:', 'scrypt:')):
                    try:
                        logger.warning(f"Convertendo senha em texto plano para hash para o usuário {instance.username}")
                        instance.senha_hash = generate_password_hash(instance.senha_hash)
                    except Exception as e:
                        logger.error(f"Erro ao converter senha para hash: {e}")