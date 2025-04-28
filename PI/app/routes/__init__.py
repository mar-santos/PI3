# app/routes/__init__.py
from app.routes.routes_usuarios import routes_bp
from app.routes import routes_pets, routes_servicos, routes_agendamentos, routes_pagamentos

# Importe todas as rotas aqui
from app.routes.routes_usuarios import *
from app.routes.routes_pets import *
from app.routes.routes_servicos import *
from app.routes.routes_agendamentos import *
from app.routes.routes_pagamentos import *