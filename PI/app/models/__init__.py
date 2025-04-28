# app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)

from .models import Usuario, Pet, Servico, Agendamento, AgendamentoServico, Pagamento

__all__ = ['db', 'Usuario', 'Pet', 'Servico', 'Agendamento', 'AgendamentoServico', 'Pagamento']