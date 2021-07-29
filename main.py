import service_drive
import service_gmail
import os
import io
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
import base64
import email
import time
from datetime import datetime, timedelta

SERVICIO_DRIVE = service_drive.obtener_servicio()
SERVICIO_GMAIL = service_gmail.obtener_servicio()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def enontrar_id(carpeta : str) -> str:
  lista_archivos = SERVICIO_DRIVE.files().list(orderBy='folder', spaces='drive', fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute() #Lo uso para encontrar el id de la carpeta
  for archivo in lista_archivos.get('files', []): #Loop hasta encontrar la carpeta remota
      nombre = archivo.get("name")
      if nombre == carpeta: #reviso si la carpeta existe en el remoto
          if archivo.get("mimeType") == 'application/vnd.google-apps.folder': #reviso que sea una carpeta y no un archivo...
              id_carpeta = archivo.get("id")
  return id_carpeta

def crear(local : dict, remoto : dict, BASE_DIR : str) -> None:
  id_carpeta = enontrar_id(BASE_DIR.rsplit('\\', 1)[1])
  #primero arranco por las carpetas
  for i in local['carpetas']: #Creo carpetas en el remoto
      if i not in remoto['carpetas']:
          archivo_metadata = {
          'name': i,
          'mimeType': 'application/vnd.google-apps.folder',
          'parents': [id_carpeta]
          }
          SERVICIO_DRIVE.files().create(body=archivo_metadata).execute()

  for i in remoto['carpetas']: #Creo carpetas en el local
      if i not in local['carpetas']:
          os.chdir(BASE_DIR)
          os.makedirs(i)

  #Segundo, voy por los archivos
  for i in local['archivos']:#Si no esta en remoto, lo agrego
      carpeta_del_archivo_local = local['archivos'][i]['carpeta']
      if i not in remoto['archivos']:
          id_carpeta = enontrar_id(carpeta_del_archivo_local)
          archivo_metadata = {
              'name': i,
              'parents': [id_carpeta]
              }
          SERVICIO_DRIVE.files().create(body=archivo_metadata).execute()

  for i in remoto['archivos']:#Si no esta en local, lo agrego
      if i not in local['archivos']:
          request = SERVICIO_DRIVE.files().get_media(fileId = remoto['archivos'][i]['archivo_id'])
          fh = io.BytesIO()
          downloader = MediaIoBaseDownload(fd=fh, request=request)
          listo = False
          while not listo:
              listo = downloader.next_chunk()
          fh.seek(0)
          if remoto['archivos'][i]['carpeta'] == BASE_DIR.rsplit('\\', 1)[1]:
              with open(os.path.join(BASE_DIR+'\\', i),'wb') as f:
                  f.write(fh.read())
                  f.close()
          else:
              with open(os.path.join(BASE_DIR+'\\'+str(remoto['archivos'][i]['carpeta']), i),'wb') as f:
                  f.write(fh.read())
                  f.close()

def actualizar(local : dict, remoto : dict, BASE_DIR : str) -> None:
  for i in remoto['archivos']:
      for x in local['archivos']:
          if i == x and remoto['archivos'][i]['carpeta'] == local['archivos'][x]['carpeta']:
              if remoto['archivos'][i]['modificacion'] > local['archivos'][x]['modificacion']:
                  request = SERVICIO_DRIVE.files().get_media(fileId = remoto['archivos'][i]['archivo_id'])
                  fh = io.BytesIO()
                  downloader = MediaIoBaseDownload(fd=fh, request=request)
                  listo = False
                  while not listo:
                      listo = downloader.next_chunk()
                  fh.seek(0)
                  if remoto['archivos'][i]['carpeta'] == BASE_DIR.rsplit('\\', 1)[1]:
                      with open(os.path.join(BASE_DIR+'\\', i),'wb') as f:
                          f.write(fh.read())
                          f.close()
                  else:
                      with open(os.path.join(BASE_DIR+'\\'+str(remoto['archivos'][i]['carpeta']), i),'wb') as f:
                          f.write(fh.read())
                          f.close()
              elif remoto['archivos'][i]['modificacion'] < local['archivos'][x]['modificacion']:
                  if local['archivos'][i]['carpeta'] == BASE_DIR.rsplit('\\', 1)[1]:
                      contenido_actualizar = MediaFileUpload(BASE_DIR+'\\'+x)
                      SERVICIO_DRIVE.files().update(fileId=remoto['archivos'][i]['archivo_id'], media_body=contenido_actualizar).execute()
                  else:
                      contenido_actualizar = MediaFileUpload(BASE_DIR+'\\'+str(remoto['archivos'][x]['carpeta']+'\\'+x))
                      SERVICIO_DRIVE.files().update(fileId=remoto['archivos'][i]['archivo_id'], media_body=contenido_actualizar).execute()

def sincronizar(local : dict, remoto : dict, BASE_DIR : str) -> None:
  print('SINCRONIZANDO.')
  #primero reviso que exista el directorio, si no esta, lo creo
  existe_carpeta = False
  lista_archivos = SERVICIO_DRIVE.files().list(orderBy='folder', spaces='drive', fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute()
  for archivo in lista_archivos.get('files', []): #Loop hasta encontrar la carpeta remota
      nombre = archivo.get("name")
      if nombre == BASE_DIR.rsplit('\\', 1)[1]: #reviso si la carpeta existe en el remoto
          if archivo.get("mimeType") == 'application/vnd.google-apps.folder': #reviso que sea una carpeta y no un archivo...
              existe_carpeta = True
  if existe_carpeta == False:
      archivo_metadata = {
          'name': BASE_DIR.rsplit('\\', 1)[1],
          'mimeType': 'application/vnd.google-apps.folder'
          }
      SERVICIO_DRIVE.files().create(body=archivo_metadata).execute()
  print('SINCRONIZANDO..')
  crear(local, remoto, BASE_DIR)
  print('SINCRONIZANDO...')
  actualizar(local, remoto, BASE_DIR)
  print('SINCRONIZANDO..')

def loop_carpeta_local(BASE_DIR : str) -> dict:
  print('SINCRONIZANDO.')
  diccionario_local = {'carpetas':[],'archivos':{}}
  for archivo in os.scandir(BASE_DIR): #loop los archivos locales
      if os.path.isdir(str(BASE_DIR)+'\\'+str(archivo.name)) == False: #Archivos
          get_time = os.path.getmtime(BASE_DIR+'\\'+archivo.name) #consigo la fecha de modificacion
          modify_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(get_time)) #lo paso a formato fecha
          fecha_mod_local = datetime.strptime(modify_date, '%Y-%m-%d %H:%M:%S') #lo paso a type date
          diccionario_local['archivos'][str(archivo.name)] = {}
          diccionario_local['archivos'][str(archivo.name)]['modificacion'] = fecha_mod_local
          diccionario_local['archivos'][str(archivo.name)]['carpeta'] = BASE_DIR.rsplit('\\', 1)[1]
      else:
          diccionario_local['carpetas'].append(str(archivo.name))
          for i in os.scandir(BASE_DIR+'\\'+str(archivo.name)):
              get_time = os.path.getmtime(BASE_DIR+'\\'+archivo.name+'\\'+i.name) #consigo la fecha de modificacion
              modify_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(get_time)) #lo paso a formato fecha
              fecha_mod_local = datetime.strptime(modify_date, '%Y-%m-%d %H:%M:%S') #lo paso a type date
              diccionario_local['archivos'][str(i.name)] = {}
              diccionario_local['archivos'][str(i.name)]['modificacion'] = fecha_mod_local
              diccionario_local['archivos'][str(i.name)]['carpeta'] = archivo.name
  return diccionario_local

def loop_carpeta_remota(BASE_DIR : str) -> dict:
  diccionario_remoto = {'carpetas':[],'archivos':{}}
  lista_archivos = SERVICIO_DRIVE.files().list(orderBy='folder', spaces='drive', fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute()
  for archivo in lista_archivos.get('files', []): #Loop hasta encontrar la carpeta remota
      nombre = archivo.get("name")
      if nombre == BASE_DIR.rsplit('\\', 1)[1]: #reviso si la carpeta existe en el remoto
          if archivo.get("mimeType") == 'application/vnd.google-apps.folder': #reviso que sea una carpeta y no un archivo...
              carpeta_principal_id = archivo.get("id")
              query = f"parents = '{carpeta_principal_id}'"
              respuesta = SERVICIO_DRIVE.files().list(q=query,orderBy='folder', spaces='drive', fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute()
              for i in respuesta.get('files', []):
                  if i.get("mimeType") == 'application/vnd.google-apps.folder': #Si es carpeta
                      diccionario_remoto['carpetas'].append(str(i.get("name")))
                      carpeta_id = i.get("id")
                      query = f"parents = '{carpeta_id}'"
                      in_folder = SERVICIO_DRIVE.files().list(q=query,orderBy='folder', spaces='drive', fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute()
                      for x in in_folder.get('files', []):#archivos dentro de las carpetas
                          modificacion_de_archivo_remoto = datetime.strptime(i.get("modifiedTime")[:-5], '%Y-%m-%dT%H:%M:%S')-timedelta(hours=3)# quito 3 porque es cet
                          diccionario_remoto['archivos'][x.get("name")] = {}
                          diccionario_remoto['archivos'][x.get("name")]['modificacion'] = modificacion_de_archivo_remoto
                          diccionario_remoto['archivos'][x.get("name")]['carpeta'] = i.get("name")
                          diccionario_remoto['archivos'][x.get("name")]['carpeta_id'] = carpeta_id
                          diccionario_remoto['archivos'][x.get("name")]['archivo_id'] = x.get("id")
                  else:
                      modificacion_de_archivo_remoto = datetime.strptime(i.get("modifiedTime")[:-5], '%Y-%m-%dT%H:%M:%S')-timedelta(hours=3)
                      diccionario_remoto['archivos'][i.get("name")] = {}
                      diccionario_remoto['archivos'][i.get("name")]['modificacion'] = modificacion_de_archivo_remoto
                      diccionario_remoto['archivos'][i.get("name")]['carpeta'] = nombre
                      diccionario_remoto['archivos'][i.get("name")]['carpeta_id'] = carpeta_principal_id
                      diccionario_remoto['archivos'][i.get("name")]['archivo_id'] = i.get("id")
  return diccionario_remoto

def accion_apropiada(accion):
    if accion == 'Generar':
        print('Archivos guardados en el directorio actual.')
    elif accion == 'Actualizar':
         print('Se enviara un mail notificadando el estado de la entrega al alumno.')

def elegir_mail(numerada, accion):
    eleccion_mail = int(input('Inserte el numero del mail a elegir: '))-1
    while type(eleccion_mail) != int:
        eleccion_mail = int(input('Inserte el numero del mail a elegir: '))-1
    #info_mail_elegido[0] contiene el Asunto, [1] el Cuerpo, y [2] la id del mensaje.
    info_mail_elegido = numerada[eleccion_mail]

    print('================================')
    print('Se Generaran las Carpetas a partir del mail con Asunto: ', info_mail_elegido[0], '.')

    descargar_adjunto(SERVICIO_GMAIL, 'me', info_mail_elegido[2], BASE_DIR)

    accion_apropiada(accion)

def procesar_mostrar_mails(mails, numerada):

    mensajes = mails.get('messages')

    n = 0
    eleccion_procesar = True
    while eleccion_procesar == True:
        if mensajes == None:
            print('No hay resultados de mails con esa palabra clave.')
            eleccion_procesar = False
        else:
            for mensaje in mensajes:
                
                texto = SERVICIO_GMAIL.users().messages().get(userId='me', 
                    id=mensaje['id'],format='raw', metadataHeaders=None).execute()
            
                mensaje_email = email.message_from_bytes(base64.urlsafe_b64decode(texto['raw']))
            
                tipo_contenido = mensaje_email.get_content_maintype()
                if tipo_contenido == 'multipart':
                    partes = mensaje_email.get_payload()
                    cuerpo = partes[0].get_payload()
                    if type(cuerpo) == list:
                        cuerpo = "\n"
                    else:
                        cuerpo = cuerpo
                elif tipo_contenido == 'text':
                    cuerpo = mensaje_email.get_payload()
                else:
                    cuerpo = ""
                    print("\nMensaje no es multipart ni texto, el cuerpo del mail esta vacio.")
            
                numerada.append([mensaje_email['Subject'], cuerpo, mensaje['id']])
                
                print('Mail', n+1, '- De:',mensaje_email['from'],'Asunto:' , mensaje_email['Subject'], 
                    '\nCuerpo del mail:', cuerpo)
            
                n = n + 1

                eleccion_procesar = False

def descargar_adjunto(servicio, id_usuario, id_msj, directorio=""):
    
    mensaje_adj = servicio.users().messages().get(userId=id_usuario, id=id_msj).execute()
    partes = [mensaje_adj['payload']]
    while partes:
        parte = partes.pop()
        if parte.get('parts'):
            partes.extend(parte['parts'])

        if parte.get('filename'):

            if 'data' in parte['body']:
                datos_archivo = base64.urlsafe_b64decode(parte['body']['data'].encode('UTF-8'))
            elif 'attachmentId' in parte['body']:
                adjunto = servicio.users().messages().attachments().get(
                    userId=id_usuario, messageId=mensaje_adj['id'], 
                    id=parte['body']['attachmentId']).execute()
                datos_archivo = base64.urlsafe_b64decode(adjunto['data'].encode('UTF-8'))
            else:
                datos_archivo = None

            if datos_archivo:
                ubicacion = ''.join([directorio, parte['filename']])
                print(ubicacion)
                with open(ubicacion, 'wb') as f:
                    f.write(datos_archivo)

    print('Descarga Completa.')

def buscar_mail(lista_numerada, accion):
    print('''\n\nBuscar Mails por medio de palabras clave:
    ================================
    ''')
    eleccion_busqueda = True
    while eleccion_busqueda == True:

        palabra_clave = input('Inserte su palabra clave: ')
        print('Cargando mails.')
        lista_mails = SERVICIO_GMAIL.users().messages().list(userId = 'me', q=palabra_clave).execute()

        procesar_mostrar_mails(lista_mails, lista_numerada)

        print('Desea ingresar otra busqueda?')
        eleccion_busqueda = input('(S/N): ')
        while not eleccion_busqueda in ["S", "N"]:
            eleccion_busqueda = input("Ingrese opción: ")

        if eleccion_busqueda == "S":
            eleccion_busqueda = True
        else:
            if lista_numerada == []:
              eleccion_busqueda = True
            else:
                elegir_mail(lista_numerada, accion)
                eleccion_busqueda = False

def lista_completa(lista_numerada, accion):
    
    max_mails = int(input('Seleccione la cantidad de mails a mostrar: '))
    while type(max_mails) != int:
        max_mails = int(input('Seleccione la cantidad de mails a mostrar: '))
    print('Cargando mails.')

    lista_mails = SERVICIO_GMAIL.users().messages().list(userId = 'me', maxResults = max_mails).execute()

    procesar_mostrar_mails(lista_mails, lista_numerada)

    elegir_mail(lista_numerada, accion)

def submenu_generar():
    print('''\n\nVer Mails para la Generacion de Carpetas
    ================================
    1. Lista Completa
    2. Busqueda por filtros
    ''')
    lista_mails_numerada = []
    accion = "Generar"

    opcion = input("Ingrese opción: ")
    while not opcion in ["1", "2"]:
        opcion = input("Ingrese opción: ")

    if opcion == "1":
        lista_completa(lista_mails_numerada, accion)
    elif opcion == "2":
        buscar_mail(lista_mails_numerada, accion)

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
    elif opcion == "5":
      diccionario_local = loop_carpeta_local(BASE_DIR)
      diccionario_remoto = loop_carpeta_remota(BASE_DIR)
      sincronizar(diccionario_local, diccionario_remoto, BASE_DIR)
      print('Sincronizado con éxito!')
    elif opcion == "7":
      submenu_generar()
    elif opcion == "8":
      continuar = False

main()
