# HackingPayara
# Instrucciones para la Configuración de la Base de Datos

Este archivo proporciona las instrucciones necesarias para configurar la base de datos `ecommerce` utilizando el script `scriptDB.sql`.

## Pasos de Configuración

1.  **Mover el script SQL a `/tmp/`:**
    Asegúrate de que el archivo `scriptDB.sql` (que se encuentra en el repositorio clonado o en tu directorio actual) esté en el directorio `/tmp/`. Si no lo está, puedes moverlo usando el comando `mv`.

    Por ejemplo, si descargaste `scriptDB.sql` en tu carpeta de inicio (`~`):

    ```bash
    mv ~/scriptDB.sql /tmp/
    ```

    O si está en un subdirectorio después de clonar un repositorio (ej. `HackingPayara/db/scriptDB.sql`):

    ```bash
    mv HackingPayara/db/scriptDB.sql /tmp/
    ```

    **Nota:** Asegúrate de reemplazar `HackingPayara/db/scriptDB.sql` con la ruta real donde se encuentra `scriptDB.sql` en tu sistema.

2.  **Ejecutar el script SQL como usuario `postgres`:**
    Una vez que el archivo `scriptDB.sql` esté en `/tmp/`, puedes ejecutarlo usando la utilidad `psql` de PostgreSQL. Esto creará la base de datos `ecommerce`, sus tablas y poblará algunos datos iniciales según el script.

    Abre una terminal y sigue estos pasos:

    a.  **Accede como el usuario `postgres`:**
        ```bash
        sudo -i -u postgres
        ```
        Se te pedirá la contraseña de tu usuario `ubuntu` (o el usuario con privilegios `sudo`).

    b.  **Ejecuta el script SQL:**
        Una vez que estés en el prompt de `postgres` (verás `postgres@Ubuntu:~$`), ejecuta el script:
        ```bash
        psql -f /tmp/scriptDB.sql
        ```

        Este comando ejecutará el contenido de `scriptDB.sql`. Verás mensajes indicando la creación de la base de datos, las tablas y la inserción de datos, similar a la siguiente salida:

        ```
        DROP DATABASE
        CREATE DATABASE
        You are now connected to database "ecommerce_db" as user "postgres".
        DO
        GRANT
        CREATE TABLE
        ... (y más mensajes de creación/inserción)
        ```

    c.  **Sal del usuario `postgres` (opcional):**
        Una vez que el script haya terminado de ejecutarse, puedes volver a tu usuario normal escribiendo `exit`:
        ```bash
        exit
        ```

¡Con estos pasos, tu base de datos `ecommerce` debería estar configurada y lista para usar!
