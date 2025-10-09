FROM python:3.10-slim

# Directorio de trabajo (la raíz del proyecto)
WORKDIR /NSXVEDGEMIGRATION

# Copiar todo el contenido del proyecto al contenedor
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Flask
EXPOSE 5000

# Variables de entorno (opcional)
ENV FLASK_ENV=production

# Comando de inicio: lo mismo que usás localmente
CMD ["python", "-m", "apps.api.run", "--host=0.0.0.0"]
