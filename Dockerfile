FROM python:3.12-slim

# Definir o diretório de trabalho - ajuste conforme necessário
WORKDIR /app

# Copiar apenas os arquivos necessários
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto da aplicação
COPY . .

# Configurar variáveis de ambiente
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expor a porta
EXPOSE 5000

# Comando para iniciar a aplicação - ajuste o caminho conforme necessário
CMD ["python", "./PI/app.py"]