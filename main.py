import service_drive
import service_gmail

SERVICIO_DRIVE = service_drive.obtener_servicio()
SERVICIO_GMAIL = service_gmail.obtener_servicio()

def main() -> None:
  continuar = True
  while continuar:
    print('''
    1. Listar archivos de carpeta actual
    2. Crear un archivo
    3. Subir un archivo
    4. Descargar un archivo
    5. Sincronizar
    6. Generar carpeta de una evaluacion
    7. Actualizar entregas de alumnos via mail
    8. Salir
    ''')

    opcion = input("Ingrese opcion: ")
    if opcion == "8":
      continuar = False

main()
