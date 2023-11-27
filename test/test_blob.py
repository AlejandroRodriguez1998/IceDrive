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

        # Crear un adaptador de objetos para el cliente
        adapter = communicator.createObjectAdapterWithEndpoints("ClientAdapter", "default -p 10003")
        adapter.activate()

        # Obtener el directorio de trabajo actual y ruta de donde va a estar el archivo
        current_directory = os.getcwd()
        file_path = current_directory+"/fileForUpload.txt"
        file_path1 = current_directory+"/fileForUpload1.txt"

        #Crea un archivo de prueba si no existe.
        create_file(file_path,"Contenido de prueba\n")
        create_file(file_path1,"Contenido de prueba\n")

        # Crear una instancia de DataTransfer en el cliente
        client_data = DataTransfer(file_path)
        data_transfer = adapter.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))

        # Simular la subida de un blob
        print("TEST 1: Simular la subida de un blob")

        blob_id = blob_service.upload(data_transfer_proxy)
        print(f"Blob uploaded with ID: {blob_id}\n")

        # Simular la subida de un blob con diferente nombre pero con mismo contenido
        print("TEST 2: Simular la subida de un blob con diferente nombre pero con mismo contenido")

        client_data = DataTransfer(file_path1)
        data_transfer = adapter.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))

        blob_id1 = blob_service.upload(data_transfer_proxy)

        if(blob_id == blob_id1):
            print("Los blobIds son iguales entonces subida no realizada")
            print(blob_id + " == " + blob_id1 + "\n")           
        else:   
            print("Los blobIds deben ser iguales al subir el mismo archivo\n")
            print(blob_id + " != " + blob_id1 + "\n")

        # Subir el mismo archivo dos veces
        print("TEST 3: Simular la subida del blob del test 1")

        # Crear una instancia de DataTransfer en el cliente de nuevo
        client_data = DataTransfer(file_path)
        data_transfer = adapter.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))
        blob_id2 = blob_service.upload(data_transfer_proxy)

        if(blob_id == blob_id2):
            print("Los blobIds son iguales entonces subida no realizada")
            print(blob_id + " == " + blob_id2 + "\n")
            
        else:   
            print("Los blobIds deben ser iguales al subir el mismo archivo")
            print(blob_id + " != " + blob_id2 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: test_blob.py <proxy_del_servicio>")
        sys.exit(1)

    proxy_str = sys.argv[1]
    test_blob_service(proxy_str)