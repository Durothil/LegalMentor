# Usa uma imagem oficial do Python como base
FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . /app

# Instala bibliotecas do sistema necessárias para OCR (Tesseract + dependências de imagem)
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

# Instala as dependências Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo Streamlit
EXPOSE 8501

# Comando padrão: roda o app Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]