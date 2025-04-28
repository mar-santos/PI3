from flask import jsonify, request, render_template, redirect, url_for, current_app, flash
from app.models.models import Usuario
from app.models import db
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aplicar melhorias de segurança e robustez nos métodos de senha
# Isso garante que os métodos estejam implementados corretamente no modelo
def _fix_password_methods():
    # Implementação robusta de check_password com tratamento de erro
    def secure_check_password(self, senha):
        try:
            return check_password_hash(self.senha_hash, senha)
        except Exception as e:
            logger.error(f"Erro ao verificar senha para {self.username}: {e}")
            return False
    
    # Implementação robusta de set_password
    def secure_set_password(self, senha):
        try:
            self.senha_hash = generate_password_hash(senha)
        except Exception as e:
            logger.error(f"Erro ao definir senha para {self.username}: {e}")
            raise

    # Adicionar os métodos melhorados ao modelo
    Usuario.check_password = secure_check_password
    Usuario.set_password = secure_set_password

# Aplicar as melhorias ao iniciar
_fix_password_methods()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error_detail = None
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        
        logger.info(f"Tentativa de login para usuário: {username}")
        
        try:
            # Buscar usuário sem filtro de ativo primeiro para diagnóstico
            usuario_check = Usuario.query.filter_by(username=username).first()
            if usuario_check:
                logger.info(f"Usuário encontrado no banco: {username}, ativo={usuario_check.ativo}, admin={usuario_check.is_admin}")
                
                # Verificar se usuário não está ativo
                if not usuario_check.ativo:
                    error_detail = f"Usuário '{username}' está inativo"
                    logger.warning(error_detail)
                    return render_template('login.html', message='Credenciais inválidas', error_detail=error_detail)
                
                # Verificar senha diretamente com o usuário encontrado
                senha_valida = usuario_check.check_password(senha)
                if not senha_valida:
                    error_detail = f"Senha incorreta para '{username}'"
                    logger.warning(error_detail)
                    return render_template('login.html', message='Credenciais inválidas', error_detail=error_detail)
                
                # Se chegou aqui, usuário e senha são válidos
                logger.info(f"Login bem-sucedido: {username}, is_admin={usuario_check.is_admin}, id={usuario_check.id_usuario}")
                
                # Login
                login_user(usuario_check)
                logger.info(f"Sessão de login criada para {username}")
                
                # Redirecionar para a página de agendamentos em vez da página de usuários
                return redirect(url_for('routes_bp.agendamentos_listar_html'))
            else:
                error_detail = f"Usuário '{username}' não encontrado no banco de dados"
                logger.warning(error_detail)
                return render_template('login.html', message='Credenciais inválidas', error_detail=error_detail)
            
        except Exception as e:
            error_detail = f"Erro durante login: {str(e)}"
            logger.error(error_detail)
            return render_template('login.html', message='Erro interno no sistema', error_detail=error_detail)

    return render_template('login.html', error_detail=error_detail)

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        username = "desconhecido"
        if hasattr(current_user, 'username'):
            username = current_user.username
        
        logger.info(f"Realizando logout do usuário: {username}")
        logout_user()
        flash('Logout realizado com sucesso', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Erro durante o logout: {e}")
        flash('Erro ao realizar logout', 'error')
        return redirect(url_for('routes_bp.index'))

# Função auxiliar para rotas administrativas de recuperação
@auth_bp.route('/reset_user_password/<username>/<nova_senha>')
@login_required
def reset_user_password(username, nova_senha):
    # Verificar permissões administrativas
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Permissão negada', 'error')
        return redirect(url_for('routes_bp.index'))
    
    usuario = Usuario.query.filter_by(username=username).first()
    if not usuario:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    
    try:
        # Redefinir a senha
        usuario.set_password(nova_senha)
        db.session.commit()
        
        flash(f'Senha para {username} redefinida com sucesso', 'success')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao redefinir senha para {username}: {e}")
        flash(f'Erro ao redefinir senha: {str(e)}', 'error')
        return redirect(url_for('routes_bp.listar_usuarios_html'))
