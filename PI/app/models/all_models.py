from . import db
from sqlalchemy import event
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

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

    def get_id(self):
        return str(self.id_usuario)

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario {self.username}>'

# ... (o resto das classes permanecem as mesmas)

@event.listens_for(db.Session, 'before_flush')
def before_flush(session, flush_context, instances):
    for instance in session.dirty:
        if isinstance(instance, Usuario):
            if instance.senha_hash and not instance.senha_hash.startswith('pbkdf2:'):
                instance.senha_hash = generate_password_hash(instance.senha_hash)