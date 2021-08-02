import service_drive
import service_gmail
import os
import zipfile
import io
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
import base64
import csv
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, timedelta
from zipfile import ZipFile

SERVICIO_DRIVE = service_drive.obtener_servicio()
SERVICIO_GMAIL = service_gmail.obtener_servicio()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def obtener_nombres_csv(info_mail_elegido: list, nombre_evaluacion: list) -> str:
    '''
    Obtiene, revisando los archivos csv, los nombres apropiados para ubicar el directorio local en el 
    cual corresponde la extraccion de los archivos.
    '''
    nombre_eval = nombre_evaluacion[0]

    titulos = []
    filas = []
    titulos2 = []
    filas2 = []

    with open(os.path.join(BASE_DIR,'alumnos.csv'), 'r') as csvfile:
        print('================================')
        print('Revisando alumnos.csv:\n\n')
        leer_csv = csv.reader(csvfile)

        titulos = next(leer_csv)

        for fila in leer_csv:
            filas.append(fila)

        print('Los Titulos son: ' + ', '.join(titulo for titulo in titulos))
        print('\nLas primeras 5 filas son:\n')
        for fila in filas[:5]:

            for columna in fila:
                print(columna)
        print('\n')

        padron = info_mail_elegido[0]

        ubicacion_padron = [fila[1] for fila in filas].index(padron)

        nombre_alumno = filas[ubicacion_padron][0]
        print('El alumno es:',nombre_alumno)

    with open(os.path.join(BASE_DIR,'docente-alumnos.csv'), 'r') as csvfile2:
        print('================================')
        print('Revisando docente-alumnos.csv:\n\n')
        leer_csv = csv.reader(csvfile2)

        titulos2 = next(leer_csv)

        for fila in leer_csv:
            filas2.append(fila)

        print('Los Titulos son: ' + ', '.join(titulo for titulo in titulos))
        print('\nLas primeras 5 filas son:\n')
        for fila in filas2[:5]:

            for columna in fila:
                print(columna)
        print('\n')

        ubicacion_docente = [fila[1] for fila in filas2].index(nombre_alumno)

        nombre_docente = filas2[ubicacion_docente][0]
        print('El docente es:',nombre_docente)

    return nombre_eval, nombre_docente, nombre_alumno

def crear_directorio(ubicacion_entrega: str) -> None:
    '''
    Crea el directorio apropiado en el cual se guarda la entrega del alumno, 
    en caso de que no exista.
    '''
    os.makedirs(ubicacion_entrega)
    print('Directorio creado.')

def descomprimir_entrega(ubicacion_zip: list, ubicacion_entrega: str) -> None:
    '''
    Coloca los archivos del zip en la carpeta del alumno correspondiente.
    '''
    print('Extrayendo los archivos comprimidos en el zip:\n')
    archivo_zip = ubicacion_zip[0]
    with ZipFile(archivo_zip, 'r') as zip:
        for informacion in zip.infolist():
            print(informacion.filename)
        print('\nExtaccion en proceso.')
        zip.extractall(path = ubicacion_entrega)
        print('Extraccion completada.')
        print('================================')
        print('Actualizacion de entrega completada.')
        print('================================')

def guardar_entrega_alumno(ubicacion_zip: list, info_mail_elegido: list, nombre_evaluacion: list) -> None:
    '''
    Recibe los nombres de la evaluacion, el docente y el alumno, y guarda 
    la entrega del alumno, revisando si la ubicacion correcta existe. Si no existe, la genera.
    '''
    nombre_eval, nombre_docente, nombre_alumno = obtener_nombres_csv(info_mail_elegido, nombre_evaluacion)

    ubicacion_entrega = (os.path.abspath(os.path.join(BASE_DIR,nombre_eval,nombre_docente,nombre_alumno)))

    if os.path.isdir(ubicacion_entrega):
        print(ubicacion_entrega) 
        print("existe, se guardara alli la entrega.")
        descomprimir_entrega(ubicacion_zip, ubicacion_entrega)
    else:
        print(ubicacion_entrega) 
        print("no existe, se creara el directorio para que se extraiga alli la entrega.")
        crear_directorio(ubicacion_entrega)
        descomprimir_entrega(ubicacion_zip, ubicacion_entrega)

def enviar_mensaje(mensaje_a_enviar: str) -> None:
    '''
    Termina el envio del mail en respuesta al alumno.
    '''
    envio = SERVICIO_GMAIL.users().messages().send(userId = 'me', body = {'raw': mensaje_a_enviar}).execute()

def crear_mensaje(destinatario: str, asunto: str, texto_mensaje: str) -> str:
    '''
    Crea las partes basicas del mail a enviar, adjuntandole al cuerpo del mensaje 
    el texto que indica el formato de entrega del alumno. 
    Devuelve la informacion codificada del mail, para que sea enviado.
    '''
    msj_mime = MIMEMultipart()
    msj_mime['to'] = destinatario
    msj_mime['subject'] = asunto
    msj_mime.attach(MIMEText(texto_mensaje, 'plain'))
    raw = base64.urlsafe_b64encode(msj_mime.as_bytes()).decode()
    return raw

def revisar_csv(info_mail_elegido: list, lista_errores: list) -> None:
    '''
    Compara el contenido de alumnos.csv con la entrega, utilizando el 
    asunto (que contiene el padron) y la direccion del alumno remitente.
    '''
    titulos = []
    filas = []

    with open(os.path.join(BASE_DIR,'alumnos.csv'), 'r') as csvfile:
        print('================================')
        print('Comparando entrega con alumnos.csv\n')
        leer_csv = csv.reader(csvfile)

        titulos = next(leer_csv)

        for fila in leer_csv:
            filas.append(fila)

        print('Los Titulos son: ' + ', '.join(titulo for titulo in titulos))
        print('\nLas primeras 5 filas son:\n')
        for fila in filas[:5]:

            for columna in fila:
                print(columna)
        print('\n')
        
        #Ver si el padron del alumno coincide con su mail:
        padron = info_mail_elegido[0]
        mail_enviado = info_mail_elegido[3]
        if padron in ([fila[1] for fila in filas]):
            print('El Padron en el asunto del mail SI existe en alumnos.csv')
            ubicacion_padron = [fila[1] for fila in filas].index(padron)
            if mail_enviado in ([fila[2] for fila in filas]):
                print('El Mail SI existe en el archivo.')
                if filas[ubicacion_padron][2] == mail_enviado:
                    print('El Mail de envio SI concuerda con el Mail del alumno en el archivo.')
                    lista_errores.append("No hay problemas con el formato de envio.")
                else:
                    print('El Mail de envio NO concuerda con el Mail del alumno en el archivo.')
                    lista_errores.append("Mail de envio NO concuerda con Mail de Alumno.")
            else:
                print('El mail NO existe en el archivo:')
                print(mail_enviado)
                lista_errores.append("Mail de envio NO existe en el archivo de alumnos.")
        else:
            print('El Padron en el asunto del mail NO existe en alumnos.csv')
            lista_errores.append("Padron NO concuerda con Mail de Alumno.")

def notificar_alumno(info_mail_elegido: list, lista_errores: list, ubicacion_zip: list, nombre_evaluacion: list) -> None:
    '''
    Notifica al alumno por mail sobre su entrega, previamente 
    revisando su formato en caso de que haya errores, para luego 
    proceder con el envio del mail.
    '''

    if 'El archivo adjunto enviado es ZIP.' in lista_errores:
        lista_errores = []
    else:
        lista_errores.append('El archivo adjunto enviado NO es ZIP.')

    revisar_csv(info_mail_elegido, lista_errores)

    if lista_errores == ["No hay problemas con el formato de envio."]:
        entrega_correcta = True
    else:
        entrega_correcta = False

    if entrega_correcta == True:
        veredicto = 'Entrega exitosa, no se presento ningun inconveniente.'
    else:
        veredicto = 'Esos son los inconvenientes con tu entrega.\n'

    separador = '\n'
    x = separador.join(lista_errores)

    texto_mensaje = x + veredicto

    #Envio mail.
    print('Se enviara un mail notificando el estado de la entrega al alumno.\n')

    mensaje_a_enviar = crear_mensaje(info_mail_elegido[3], info_mail_elegido[0], texto_mensaje)

    enviar_mensaje(mensaje_a_enviar)

    if entrega_correcta == True:
        print('Se guardara el archivo del alumno en su carpeta correspondiente.\n')
        guardar_entrega_alumno(ubicacion_zip, info_mail_elegido, nombre_evaluacion)
    else:
        print('El formato de entrega es incorrecto, no se guardara la entrega del alumno en su carpeta.')

def submenu_actualizar(nombre_evaluacion) -> None:
  existen_archivos_csv = (os.path.exists(os.path.join(BASE_DIR,'alumnos.csv')) 
    and os.path.exists(os.path.join(BASE_DIR,'docentes.csv')) and os.path.exists(os.path.join(BASE_DIR,'docente-alumnos.csv')))
  
  if existen_archivos_csv == True:
    print('Los archivos csv existen, continuando con el procedimiento.')
    print('''\n\nVer Mails para recibir la entrega de un Alumno.
    ================================
    1. Lista Completa
    2. Busqueda por filtros
    ''')
    lista_mails_numerada = []
    accion = "Actualizar"

    opcion = input("Ingrese opción: ")
    while not opcion in ["1", "2"]:
        opcion = input("Ingrese opción: ")

    if opcion == "1":
        lista_completa(lista_mails_numerada, accion, nombre_evaluacion)

    elif opcion == "2":
        buscar_mail(lista_mails_numerada, accion, nombre_evaluacion)

  else:
      print('''Los archivos csv no existen. Por favor, ejecute la opcion 6 "Generar 
          carpetas de una evaluacion" para que los archivos csv necesarios esten disponibles.''')

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
          if local['archivos'][i]['carpeta'] == BASE_DIR.rsplit('\\', 1)[1]:
              media = MediaFileUpload(BASE_DIR+'\\'+i)
              SERVICIO_DRIVE.files().create(body=archivo_metadata, media_body = media).execute()
          else:
              media = MediaFileUpload(BASE_DIR+'\\'+str(local['archivos'][i]['carpeta'])+'\\'+i)
              SERVICIO_DRIVE.files().create(body=archivo_metadata, media_body = media).execute()

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
  
  actualizar(local, remoto, BASE_DIR)

def loop_carpeta_local(BASE_DIR : str) -> dict:
  print('SINCRONIZANDO..')
  diccionario_local = {'carpetas':[],'archivos':{}}
  for archivo in os.scandir(BASE_DIR): #loop los archivos locales
      if os.path.isdir(str(BASE_DIR)+'\\'+str(archivo.name)) == False: #Archivos
          print('SINCRONIZANDO.')
          get_time = os.path.getmtime(BASE_DIR+'\\'+archivo.name) #consigo la fecha de modificacion
          modify_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(get_time)) #lo paso a formato fecha
          fecha_mod_local = datetime.strptime(modify_date, '%Y-%m-%d %H:%M:%S') #lo paso a type date
          diccionario_local['archivos'][str(archivo.name)] = {}
          diccionario_local['archivos'][str(archivo.name)]['modificacion'] = fecha_mod_local
          diccionario_local['archivos'][str(archivo.name)]['carpeta'] = BASE_DIR.rsplit('\\', 1)[1]
      else:
          diccionario_local['carpetas'].append(str(archivo.name))
          for i in os.scandir(BASE_DIR+'\\'+str(archivo.name)):
              if os.path.isdir(str(BASE_DIR)+'\\'+str(archivo.name)+'\\'+i.name) == False:
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

def accion_apropiada(info_mail_elegido: list, accion: str, lista_errores: list, ubicacion_zip: list, nombre_evaluacion: list) -> None:
    '''
    Determina si se debe continuar con el programa
    (en caso de que se haya elegido la funcion 7, Actualizar Entrega).
    '''
    if accion == 'Generar':
        print('Archivos guardados en el directorio actual.')
    elif accion == 'Actualizar':
        print('\nSe determinara si la entrega tiene el formato correcto.')
        notificar_alumno(info_mail_elegido, lista_errores, ubicacion_zip, nombre_evaluacion)

def elegir_mail(numerada: list, accion: str, nombre_evaluacion: list) -> None:
    '''
    Recibe la eleccion del mail indicado por el usuario y crea info_mail_elegido, lista 
    que contiene informacion clave del mail elegido.
    Luego, lleva el usuario a la descarga del archivo adjunto del mail.
    '''
    eleccion_mail = int(input('Inserte el numero del mail a elegir: '))-1
    while type(eleccion_mail) != int:
        eleccion_mail = int(input('Inserte el numero del mail a elegir: '))-1
    #info_mail_elegido[0] contiene el Asunto, [1] el Cuerpo, [2] la id del mensaje y [3] el remitente.
    info_mail_elegido = numerada[eleccion_mail]

    print('================================')
    if accion == 'Generar':
        print('Se Generaran las Carpetas a partir del mail con Asunto: ', info_mail_elegido[0], '.')
    elif accion == 'Actualizar':
        print('Se recibira la entrega del Alumno a partir del mail con Asunto: ', info_mail_elegido[0], '.')

    lista_errores = []
    ubicacion_zip = []
    
    descargar_adjunto(SERVICIO_GMAIL, 'me', info_mail_elegido[2], BASE_DIR, 
      lista_errores, ubicacion_zip, nombre_evaluacion, accion)

    accion_apropiada(info_mail_elegido, accion, lista_errores, ubicacion_zip, nombre_evaluacion)

def procesar_mostrar_mails(mails, numerada: list) -> None:
    '''
    Procesa e imprime los mails de la lista de mails recibida(en orden de mas a menos recientes), y crea una lista 
    con la informacion clave de cada mail (su asunto, cuerpo, id y mail remitente).
    '''
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
                        cuerpo = "(Mail SI contiene archivo adjunto.)\n"
                    else:
                        cuerpo = "(Mail NO contiene archivo adjunto.)\n"
                elif content_type == 'text':
                    cuerpo = mensaje_email.get_payload()
                else:
                    cuerpo = ""
                    print("\nMensaje no es multipart ni texto, el cuerpo del mail esta vacio.")

                if "<" in mensaje_email['from']:
                    mail_remitente = mensaje_email['from'].split(" ")[2].split("<")[1].split(">")[0]
                else:
                    mail_remitente = mensaje_email['from']

                numerada.append([mensaje_email['Subject'], cuerpo, mensaje['id'], mail_remitente])
                
                print('Mail', n+1, '- De:',mensaje_email['from'],'Asunto:' , mensaje_email['Subject'], 
                    '\nCuerpo del mail:', cuerpo)
            
                n = n + 1

                eleccion_procesar = False

def unzip(fileName: str):
    with zipfile.ZipFile(BASE_DIR+'//'+fileName, 'r') as zip_ref:
        zip_ref.extractall(BASE_DIR)

def main_folder(asunto_mail: str):
    os.chdir(BASE_DIR)
    try:
        os.makedirs(asunto_mail)
    except Exception:
        pass

def profesor_folders(asunto_mail: str):
    with open('docentes.csv', 'r', encoding='utf-8-sig') as read_obj:
        csv_reader = csv.reader(read_obj)
        for row in csv_reader:
            os.chdir(BASE_DIR+'//'+asunto_mail)
            try:
                os.makedirs(row[0])
            except Exception:
                pass

def alumnos_folders(asunto_mail: str):
    with open(BASE_DIR+'//'+'docente-alumnos.csv', 'r', encoding='utf-8-sig') as read_obj:
        csv_reader = csv.reader(read_obj)
        for row in csv_reader:
            os.chdir(BASE_DIR+'//'+asunto_mail+'//'+row[0])
            try:
                os.makedirs(row[1])
            except Exception:
                pass

def descargar_adjunto(servicio, id_usuario: str, id_msj: str, directorio: str, lista_errores: list, 
  ubicacion_zip: list, nombre_evaluacion: list, accion: str) -> None:
    '''
    Descarga los archivos adjuntos al mail seleccionado por el usuario, y reconoce si 
    el archivo es de formato comprimido zip. Devuelve el nombre de la evaluacion, dado en el asunto.
    '''
    texto = SERVICIO_GMAIL.users().messages().get(userId=id_usuario,id=id_msj,format='raw', metadataHeaders=None).execute()
    mensaje_email = email.message_from_bytes(base64.urlsafe_b64decode(texto['raw']))
    for part in mensaje_email.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        fileName = part.get_filename()
        if bool(fileName):
            filePath = os.path.join(BASE_DIR, fileName)
            if not os.path.isfile(filePath) :
                fp = open(filePath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

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
                if ubicacion.endswith('.zip'):
                    print('El archivo adjunto es ZIP.')
                    lista_errores.append('El archivo adjunto enviado es ZIP.')
                    ubicacion_zip.append(ubicacion)
                else:
                    print('El archivo adjunto NO es ZIP.')
                with open(ubicacion, 'wb') as f:
                    f.write(datos_archivo)

    unzip(fileName)
    asunto_mail = mensaje_email['Subject']
    if accion == 'Generar': 
      #Si el asunto del mail contiene el nombre de la evaluacion, guardarlo en la lista.
      nombre_evaluacion.append(asunto_mail)
      main_folder(asunto_mail)
      profesor_folders(asunto_mail)
      alumnos_folders(asunto_mail)
      print('Carpetas generadas.')
    else:
      print('Descarga Completa.')

def buscar_mail(lista_numerada: list, accion: str, nombre_evaluacion: list) -> None:
    '''
    Muestra los mails que Gmail reconoce como resultados de su 
    busqueda, utilizando una palabra elegida por el usuario. Luego, lleva 
    el usuario a la eleccion del mail correcto.
    '''
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
            eleccion_busqueda = input("(S/N): ")

        if eleccion_busqueda == "S":
            eleccion_busqueda = True
        else:
            if lista_numerada == []:
                eleccion_busqueda = True
            else:
                elegir_mail(lista_numerada, accion, nombre_evaluacion)
                eleccion_busqueda = False

def lista_completa(lista_numerada: list, accion: str, nombre_evaluacion: list) -> None:
    '''
    Muestra la cantidad de mails seleccionada, y lleva 
    el usuario a la eleccion del mail correcto.
    '''
    max_mails = int(input('Seleccione la cantidad de mails a mostrar: '))
    while type(max_mails) != int:
        max_mails = int(input('Seleccione la cantidad de mails a mostrar: '))
    print('Cargando mails.')

    lista_mails = SERVICIO_GMAIL.users().messages().list(userId = 'me', maxResults = max_mails).execute()

    procesar_mostrar_mails(lista_mails, lista_numerada)

    elegir_mail(lista_numerada, accion, nombre_evaluacion)

def submenu_generar(nombre_evaluacion: list):
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
        lista_completa(lista_mails_numerada, accion, nombre_evaluacion)
    elif opcion == "2":
        buscar_mail(lista_mails_numerada, accion, nombre_evaluacion)

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
      print('Sincronizando....')  
      diccionario_local = loop_carpeta_local(BASE_DIR)
      diccionario_remoto = loop_carpeta_remota(BASE_DIR)
      sincronizar(diccionario_local, diccionario_remoto, BASE_DIR)
      print('Sincronizado con éxito!')
    elif opcion == "6":
      nombre_evaluacion = []
      submenu_generar(nombre_evaluacion)
    elif opcion == "7":
      submenu_actualizar(nombre_evaluacion)
    elif opcion == "8":
      continuar = False

main()