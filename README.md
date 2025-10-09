# nsxtEdgeMigration

¡Bienvenido! 🎉  
Esta es una aplicación para **migrar Edge Gateways entre diferentes versiones de NSX**.  

Por el momento la app está en desarrollo y **solo se puede migrar desde NSX-V hacia NSX-T**.  

La aplicación está pensada para ofrecer tanto una **GUI web** como una **CLI**, aunque actualmente la funcionalidad de CLI está en desarrollo. 

---

## 🚀 Estado del proyecto
- ✅ Migración de NSX-V a NSX-T con script  
- ✅ Migración de NSX-V a NSX-T con GUI  
- 🛠️ Desarrollo de CLI  

---

## ⚙️ Instalación y ejecución rápida

1. Clona el repositorio:

   ```bash
   git clone https://github.com/gerapereiravillar/nsxvEdgeMigration/
   cd nsxvEdgeMigration/
   ```

2. Crea y activa un entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate   # En Linux / MacOS
   venv\Scripts\activate      # En Windows
   ```

3. Instala dependencias:

   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

4. Ejecuta la app:
   
   ```bash
   python -m apps.api.run
   ```

---

## 🐳 Ejecución con Docker

Este proyecto incluye un **Dockerfile listo para usar**, por lo que podés construir y ejecutar la app directamente con Docker:

1. **Construir la imagen:**

   ```bash
   docker build -t nsxt-edge-migration .
   ```

2. **Ejecutar el contenedor:**

   ```bash
   docker run -d -p 5000:5000 nsxt-edge-migration
   ```

3. **Abrir la aplicación:**

   👉 [http://localhost:5000](http://localhost:5000)

---

## 📌 Notas
- Este proyecto está en fase temprana de desarrollo.  
- Cualquier feedback o contribución es bienvenida. 🙌  
- Próximamente: línea de comandos y más versiones de API compatibles.  

---

## 📄 Licencia

Este proyecto está licenciado bajo los términos de la [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).  
Puedes usarlo, modificarlo y distribuirlo libremente siempre que cumplas con los términos de dicha licencia.