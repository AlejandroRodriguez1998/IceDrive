import Ice
import sys
import os
import tempfile

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_iceDrive = os.path.join(ruta_actual, "..", "icedrive_blob", "icedrive.ice")
ruta_BlobService = os.path.join(ruta_actual, "..", "icedrive_blob")

Ice.loadSlice(ruta_iceDrive)
import IceDrive

sys.path.append(ruta_BlobService)
from blob import DataTransfer

def create_file(file_path, text):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write(text)

def test_blob_service(proxy_str):
    with Ice.initialize(sys.argv) as communicator:
        base = communicator.stringToProxy(proxy_str)
        blob_service = IceDrive.BlobServicePrx.checkedCast(base)
            
        # Verifica que la conversión de proxy sea exitosa
        if not blob_service:
            raise RuntimeError("Invalid proxy")

        # Obtener el directorio de trabajo actual y ruta de donde va a estar el archivo
        current_directory = os.getcwd()
        file_path = current_directory+"/fileForUpload.txt"
        file_path1 = current_directory+"/fileForUpload1.txt"

        #Crea un archivo de prueba si no existe.
        create_file(file_path,"Contenido de prueba\n")
        create_file(file_path1,"Contenido de prueba\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: test_blob.py <proxy_del_servicio>")
        sys.exit(1)

    proxy_str = sys.argv[1]
    test_blob_service(proxy_str)