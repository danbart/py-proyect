FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Exponer el puerto que utilizará la aplicación
EXPOSE 5000

# Comando para ejecutar las migraciones y la aplicación
CMD ["./entrypoint.sh"]
