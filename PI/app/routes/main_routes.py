from flask import render_template
from app.routes import routes_bp

@routes_bp.route('/')
def index():
    return render_template('index.html')