#app/auth/__init__.py
from flask import Blueprint

print("Executando app/auth/__init__.py")  # Mensagem de diagnóstico

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

print("Blueprint auth_bp criado")  # Mensagem de diagnóstico

from . import routes
print("Importado app.auth.routes")  # Mensagem de diagnóstico





"""from flask import Blueprint
import os

print("Executando app/auth/__init__.py")  # Mensagem de diagnóstico

auth_bp = Blueprint('auth', __name__, 
                    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                    url_prefix='/auth')

print("Blueprint auth_bp criado")  # Mensagem de diagnóstico

from . import routes
print("Importado app.auth.routes")  # Mensagem de diagnóstico

from . import models
print("Importado app.auth.models")  # Mensagem de diagnóstico"""