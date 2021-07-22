import service_drive
import service_gmail
import os
import io
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload

SERVICIO_DRIVE = service_drive.obtener_servicio()
SERVICIO_GMAIL = service_gmail.obtener_servicio()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def listar_remoto() -> None:
  print('''\n\n
  ============================''')
  lista_archivos = SERVICIO_DRIVE.files().list(orderBy='folder', spaces='drive',
                              fields='nextPageToken, files(id, name)').execute()
  for archivo in lista_archivos.get('files', []):
    nombre = archivo.get("name")
    print(f"{nombre}")

def listar_local(ruta = BASE_DIR) -> None:
  print(f'''\n\n{ruta}
  ============================''')
  for archivo in os.scandir(ruta):
    if archivo.is_dir(): tipo = "Carpeta"
    elif archivo.is_file(): tipo = "Archivo"
    else: tipo = "Desconocido"
    print(f"{archivo.name} \t Tipo: {tipo}")
  
  nueva_ruta = input("\nIngrese carpeta para seguir navegando (atras = .. | salir = .): ")
  while not nueva_ruta == ".":
    while nueva_ruta == ".." and ruta == BASE_DIR:
      print("\nYa se encuentra en el directorio principal")
      nueva_ruta = input("\nIngrese carpeta para seguir navegando (atras = .. | salir = .): ")
    
    if nueva_ruta == "..":
      nueva_ruta = os.path.abspath(os.path.dirname(ruta))
      listar_local(nueva_ruta)
    elif nueva_ruta != ".":
      try:
        nueva_ruta = os.path.join(ruta, nueva_ruta)
        listar_local(nueva_ruta)
        nueva_ruta = "."
      except FileNotFoundError:
        print("\nNo existe la ruta")
        nueva_ruta = input("\nIngrese carpeta para seguir navegando (atras = .. | salir = .): ")
      except NotADirectoryError:
        print("\nLa ruta debe ser una carpeta")
        nueva_ruta = input("\nIngrese carpeta para seguir navegando (atras = .. | salir = .): ")


def submenu_listar() -> None:
  print('''\n\n
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

def subir_archivo_remoto(nombre_archivo : str, ruta : str) -> None:
  '''
  Sube el archivo a la carpeta remota
  '''
  file_metadata = {'name': nombre_archivo}
  media = MediaFileUpload(ruta)
  SERVICIO_DRIVE.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()


def subir_archivo(nombre_archivo : str, cuerpo : str) -> None:
  '''
  Sube el archivo a la carpeta local
  '''
  with open(nombre_archivo, "w") as archivo:
    archivo.writelines(cuerpo)
  subir_archivo_remoto(nombre_archivo, os.path.abspath(nombre_archivo))


def crear_cuerpo_archivo() -> str:
  '''
  Crea el cuerpo de un archivo
  '''
  print("""\n
  Creando el cuerpo del archivo, para terminar ingrese una linea vacía""")
  cuerpo = ""
  i = 1
  print("[",i,"]", end = "")
  linea = input()
  while linea != "":
    cuerpo += linea
    i += 1

    print("[",i,"]", end = "")
    linea = input()
  return cuerpo

def crear_archivo() -> tuple:
  '''
  Crea un archivo en la ruta local
  '''
  nombre_arch = input("Ingrese el nombre del archivo con su extension: ")
  cuerpo = crear_cuerpo_archivo()
  subir_archivo(nombre_arch, cuerpo)

def seleccionar_archivo_remoto() -> str:
  '''
  Muestra todos los archivos del drive y devuelve el id del archivo seleccionado por el usuario
  '''
  lista_archivos = SERVICIO_DRIVE.files().list(orderBy='folder', spaces='drive',
                              fields='nextPageToken, files(id, name)').execute()
  for archivo in lista_archivos.get('files', []):
    nombre = archivo.get("name")
    print(f"{nombre}")
  
  seleccion = input("Ingrese nombre del archivo: ")
  for archivo in lista_archivos.get('files', []):
    if seleccion == archivo.get("name"):
      return archivo.get("id"), archivo.get("name")
  print("\nNo se encontraron coincidencias")
  return "0"

def descargar_archivo_remoto(id_archivo : str, nombre_archivo : str) -> None:
  '''
  Descarga el archivo del remoto al local
  '''
  ruta_descarga = input("Indicar ruta de descarga: ")
  if not ruta_descarga:
    ruta_descarga = BASE_DIR

  request = SERVICIO_DRIVE.files().get_media(fileId=id_archivo)
  fh = io.BytesIO()
  downloader = MediaIoBaseDownload(fh, request)
  done = False
  while done is False:
      status, done = downloader.next_chunk()
      progreso = status.progress() * 100
      print(f"Descarga %{progreso}")
  
  fh.seek(0)

  with open(os.path.join(ruta_descarga,nombre_archivo), "wb") as f:
    f.write(fh.read())
    f.close()

def main() -> None:
  continuar = True
  while continuar:
    print('''
    MENU
    ===============================
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
    elif opcion == "2":
      crear_archivo()
    elif opcion == "3":
      listar_local()
      nombre = input("\n\nIngrese el nombre del archivo con su extension: ")
      subir_archivo_remoto(nombre, os.path.abspath(nombre))
    elif opcion == "4":
      id_archivo, nombre_archivo = seleccionar_archivo_remoto()
      if id_archivo != "0":
        descargar_archivo_remoto(id_archivo, nombre_archivo)
    elif opcion == "8":
      continuar = False

main()
