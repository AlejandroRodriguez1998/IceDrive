import Ice
import sys
import os

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

def leerContenidoDescargado(file_path):
    content = ""

    with open(file_path, 'r') as file:
            # Lee el contenido del archivo
            content = file.read()

    return content
            
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
        print("\n·TEST 1: Simular la subida de un blob")

        blob_id = blob_service.upload(data_transfer_proxy)
        print(f"Blob uploaded with ID: {blob_id}\n")

        # Simular la subida de un blob con diferente nombre pero con mismo contenido
        print("·TEST 2: Simular la subida de un blob con diferente nombre pero con mismo contenido")

        client_data = DataTransfer(file_path1)
        data_transfer = adapter.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))

        blob_id1 = blob_service.upload(data_transfer_proxy)

        if(blob_id == blob_id1):
            print("Los BlobIds son iguales entonces subida no realizada")
            print(blob_id + " == " + blob_id1 + "\n")           
        else:   
            print("Los BlobIds deben ser iguales al subir el mismo archivo\n")
            print(blob_id + " != " + blob_id1 + "\n")

        # Subir el mismo archivo dos veces
        print("·TEST 3: Simular la subida del blob del test 1")

        # Crear una instancia de DataTransfer en el cliente de nuevo
        client_data = DataTransfer(file_path)
        data_transfer = adapter.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))
        blob_id2 = blob_service.upload(data_transfer_proxy)

        if(blob_id == blob_id2):
            print("Los BlobIds son iguales entonces subida no realizada")
            print(blob_id + " == " + blob_id2 + "\n")
            
        else:   
            print("Los BlobIds deben ser iguales al subir el mismo archivo")
            print(blob_id + " != " + blob_id2 + "\n")

        # Simular la descarga de un blob
        print("·TEST 4: Simulacion de descarga del ID --> " + blob_id)

        file_path_download = current_directory+"/fileForDownload.txt"

        download_blob_proxy = blob_service.download(blob_id)
        download_blob = DataTransfer(file_path_download, 'wb')

        while True:
            data = download_blob_proxy.read(4096)
            if not data:
                break
            download_blob.file.write(data)
            
        download_blob_proxy.close()
        download_blob.close()

        # Muestra el contenido
        # download_blob.file.name --> dowloand_blob tiene un file que a su vez file tiene un nombre de la ruta por eso .name
        # lo que contiene download_blob.file = <_io.BufferedWriter name='ruta'>
        print(f"Contenido del fichero descargado: {leerContenidoDescargado(download_blob.file.name)}", end="")
        print(f"Blob downloaded with proxy: {download_blob_proxy}\n")

        # Ver si se ha eliminado las instancias de DataTransfer
        print("·TEST 5: Comprobar si close() de DataTransfer elimina la instancia")

        try:
            data = download_blob_proxy.read(4096)
            print("Se esperaba una excepción de read no encontrando el fichero\n")
        except Exception:
            print("Correctamente manejado el intento de leer una instancia de DataTransfer ya cerrada\n")

        # Intentar descargar un archivo que no existe
        print("·TEST 6: Simulacion de descarga del ID --> 1 (no existe)")

        try:
            blob_service.download("1")
            # Intenta leer o realizar alguna operación con inexistente_blob_proxy
            raise Exception("Se esperaba una excepción de blob no encontrado\n")
        except IceDrive.UnknownBlob:
            print("Correctamente manejado el intento de descargar un blob inexistente\n")

        # Simular el enlace de un blob
        print("·TEST 7: Simulacion el enlace del ID --> " + blob_id)

        blob_service.link(blob_id)
        print(f"Blob {blob_id} linked.\n")

        # Intentar enlazar un blob inexistente
        print("TEST 8: Simulacion el enlace del ID --> 1 (no existe)")

        try:
            blob_service.link("1")
            raise Exception("Se esperaba una excepción de blob no encontrado al enlazar\n")
        except IceDrive.UnknownBlob:
            print("Correctamente manejado el intento de enlazar un blob inexistente\n")

        # Simular el desenlace de un blob
        print("·TEST 9: Simulacion el desenlance del ID --> " + blob_id)

        blob_service.unlink(blob_id)
        print(f"Blob {blob_id} unlinked.\n")

        # Volver a hacer el desenlance
        print("·TEST 10: Simulacion el desenlance del ID --> " + blob_id)

        try:
            blob_service.unlink(blob_id)
        except IceDrive.UnknownBlob:
            print("Blob ya no existe por lo tanto exception UnknownBlob.\n")

        # Intentar desenlazar un blob inexistente
        print("·TEST 11: Simulacion el desenlance del ID --> 1 (no existe)")

        try:
            blob_service.unlink("1")
            raise Exception("Se esperaba una excepción de blob no encontrado al desenlazar\n")
        except IceDrive.UnknownBlob:
            print("Correctamente manejado el intento de desenlazar un blob inexistente\n")

        # Eliminacion de los archivos para este testing
        respuesta = input("¿Desea eliminar los archivos? (s/n): ")

        if respuesta.lower() == 's':
            try:
                os.remove(file_path)
                os.remove(file_path1)
                os.remove(file_path_download)
                print("Archivos eliminados correctamente.")
            except OSError as e:
                print(f"Error al eliminar el archivo: {e}")
        else:
            print("No se eliminaron archivos.")

        communicator.destroy()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: test_blob.py <proxy_del_servicio>")
        sys.exit(1)

    proxy_str = sys.argv[1]
    test_blob_service(proxy_str)