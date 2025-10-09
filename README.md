# nsxtEdgeMigration

¡Bienvenido! 🎉  
Esta es una aplicación para **migrar Edge Gateways entre diferentes versiones de NSX**.  

Por el momento la app está en desarrollo y **solo se puede migrar desde NSX-V hacia NSX-T**.  

La aplicación está pensada para ofrecer tanto una **GUI web** como una **CLI**, aunque actualmente esas funcionalidades se encuentran en construcción.  

---

## 🚀 Estado del proyecto
- ✅ Migración de NSX-V a NSX-T con script
- 🛠️ Desarrollo de GUI web
- 🛠️ Desarrollo de CLI

---

## 📂 Uso del script

Si necesitas migrar un Edge ahora mismo, ¡no te preocupes!  
Puedes usar el script que se encuentra en:

```
src/edge_migrator/testing/unit/core/services
```

Dentro encontrarás opciones que te permiten elegir **qué componentes migrar** (firewall rules, NAT rules, static routes, etc.).

---

## ⚙️ Instalación y ejecución rápida

1. Clona el repositorio:

   ```bash
   git clone https://github.com/gerapereiravillar/nsxtEdgeMigration
   cd nsxtEdgeMigration/src
   ```

2. Crea y activa un entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate   # En Linux / MacOS
   venv\Scripts\activate    # En Windows
   ```

3. Instala dependencias:

   ```bash
   pip install requests
   ```

4. Ejecuta el script desde src de migración con las opciones que necesites.
   
    ```
    python -m
     edge_migrator.testing.unit.core.services.edge_migration_test
   ```
---

## 📌 Notas
- Este proyecto está en fase temprana de desarrollo.
- Cualquier feedback o contribución es bienvenida. 🙌
- Próximamente: interfaz web y línea de comandos.

---

## 📄 Licencia
Pendiente de definir.
