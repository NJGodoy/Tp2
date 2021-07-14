import service_drive
import service_gmail
import os

SERVICIO_DRIVE = service_drive.obtener_servicio()
SERVICIO_GMAIL = service_gmail.obtener_servicio()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def listar_remoto() -> None:
  print('''\n\nListando archivos remotos
  ============================''')
  lista_archivos = SERVICIO_DRIVE.files().list(spaces='drive',
                              fields='nextPageToken, files(id, name)').execute()
  for archivo in lista_archivos.get('files', []):
    print(archivo.get("name"))

def listar_local(ruta = BASE_DIR) -> None:
  print('''\n\nListando archivos locales
  ============================''')
  for archivo in os.scandir(ruta):
    print(archivo.name)
  
def submenu_listar() -> None:
  print('''\n\nUbicacion de archivos
  ================================
  1. Local
  2. Remoto
  ''')
  opcion = input("Ingrese opción: ")
  while not opcion in ["1", "2"]:
    opcion = input("Ingrese opción: ")
  
  if opcion == "1":
    listar_local()
  elif opcion == "2":
    listar_remoto()

def main() -> None:
  continuar = True
  while continuar:
    print('''
    1. Listar archivos de carpeta
    2. Crear un archivo
    3. Subir un archivo
    4. Descargar un archivo
    5. Sincronizar
    6. Generar carpeta de una evaluacion
    7. Actualizar entregas de alumnos via mail
    8. Salir
    ''')

    opcion = input("Ingrese opcion: ")
    if opcion == "1":
      submenu_listar()
    elif opcion == "8":
      continuar = False

main()
