// app/static/js/auth.js

// Script para controlar o estado dos links baseado no login
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Obter o estado de autenticação do elemento oculto
        const authElement = document.getElementById('auth-state');
        const isLoggedIn = authElement && authElement.dataset.isAuthenticated === 'true';
        
        // Atualizar o estado da UI baseado no login
        updateUIState(isLoggedIn);
        console.log('Auth state processed:', isLoggedIn);
    } catch (error) {
        console.error('Error in auth processing:', error);
    }
});

// Função para atualizar a UI com base no estado de login
function updateUIState(isLoggedIn) {
    try {
        // Selecionando todos os links restritos
        const restrictedLinks = document.querySelectorAll('.restricted-link');
        
        if (isLoggedIn) {
            // Usuário logado: habilita os links
            restrictedLinks.forEach(link => {
                link.classList.remove('disabled-link');
            });
            console.log('Links enabled for logged in user');
        } else {
            // Usuário não logado: desabilita os links
            restrictedLinks.forEach(link => {
                link.classList.add('disabled-link');
            });
            console.log('Links disabled for guest user');
        }
    } catch (error) {
        console.error('Error in updateUIState:', error);
    }
}