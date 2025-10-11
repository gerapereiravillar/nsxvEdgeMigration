
# nsxvEdgeMigration: Herramienta de Migración de Edge Gateway (VCD Multi-Instancia)

¡Bienvenido! 🎉

Esta es una herramienta de código abierto para automatizar la **Migración de Servicios de Edge Gateways entre diferentes instancias de VMware Cloud Director (VCD)**, abordando el desafío de la incompatibilidad de APIs entre las versiones de NSX.

Por el momento la app está en desarrollo y **solo se puede migrar desde Edge Gateways basados en NSX-V hacia Gateways basados en NSX-T**.

La aplicación está pensada para ofrecer tanto una **GUI web** como una **CLI**, aunque actualmente la funcionalidad de CLI está en desarrollo.

---

## 🎯 Escenario de Uso Principal (Problema que Resuelve)

Esta herramienta llena un vacío en las soluciones de migración de VMware, enfocándose en el movimiento de la configuración de red más compleja:

* **Objetivo:** Migrar los servicios de un Edge Gateway de un **VDC de origen (en VCD Instancia A)** que utiliza NSX-V, para recrearlos en un Tier-1 Gateway de un **VDC de destino (en VCD Instancia B)** que utiliza NSX-T.
* **Servicios Cubiertos:** Automatiza la traducción y recreación de reglas de **NAT (DNAT/SNAT) y  Firewall.**
* **Beneficio:** Permite a los proveedores de servicios (CSPs) o administradores automatizar la consolidación de infraestructuras o la migración completa de un Org VDC de un ambiente NSX-V a un nuevo ambiente NSX-T en una plataforma VCD diferente.

---
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
