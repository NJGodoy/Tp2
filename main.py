import service_drive
import service_gmail
import os

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
  print('''\n\n
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
  metadata = {'name' : nombre_archivo}
  SERVICIO_DRIVE.files().create(body = metadata,
                                fields = "id").execute()


def subir_archivo(nombre_archivo : str, cuerpo : str) -> None:
  '''
  Sube el archivo a la carpeta local
  '''
  with open(nombre_archivo, "w") as archivo:
    archivo.writelines(cuerpo)
  ruta = os.path.join(BASE_DIR, nombre_archivo)
  subir_archivo_remoto(nombre_archivo, ruta)


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
    elif opcion == "2":
      crear_archivo()
    elif opcion == "8":
      continuar = False

main()
