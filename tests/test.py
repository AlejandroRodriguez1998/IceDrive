import Ice
import sys
import os
import uuid
import logging

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_iceDrive = os.path.join(ruta_actual, "..", "icedrive_blob", "icedrive.ice")
ruta_BlobService = os.path.join(ruta_actual, "..", "icedrive_blob")

Ice.loadSlice(ruta_iceDrive)
import IceDrive
import IceStorm

sys.path.append(ruta_BlobService)
from blob import DataTransfer
from blob import BlobService
from discovery import Discovery
from delayed_response import BlobQuery

logging.basicConfig(level=logging.INFO, format='%(message)s')

class User(IceDrive.User):    
    def __init__(self, username):
        self.username = username
    
    def getUsername(self, current: Ice.Current = None) -> str:
        return self.username

    def isAlive(self, current: Ice.Current = None) -> bool:
        return True

    def refresh(self, current: Ice.Current = None) -> None:
        pass

class Authentication(IceDrive.Authentication):
    def __init__(self, adapter):
        self.users = {}  # Store users as {username: password}
        self.adapter = adapter

    def login(self, username: str, password: str, current: Ice.Current = None) -> IceDrive.UserPrx:
        pass

    def newUser(self, username: str, password: str, current: Ice.Current = None) -> IceDrive.UserPrx:
        user = User(username)
        proxy = IceDrive.UserPrx.uncheckedCast(self.adapter.addWithUUID(user))
        self.users[proxy] = user
        return proxy

    def removeUser(self, username: str, password: str, current: Ice.Current = None) -> None:     
        pass

    def verifyUser(self, user: IceDrive.UserPrx, current: Ice.Current = None) -> bool:  
        return user in self.users

def create_file(file_path, text):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write(text)

def test_blob_service():
    with Ice.initialize(sys.argv) as communicator:
        serviceId = str(uuid.uuid4()) # Identificador único del servicio

        #Crear adaptadores
        adapterBlob = communicator.createObjectAdapter("BlobAdapter")
        adapterBlob1 = communicator.createObjectAdapterWithEndpoints("BlobAdapter1", "tcp -h localhost -p 10003")
        adapterAuth = communicator.createObjectAdapterWithEndpoints("AuthAdapter", "tcp -h localhost -p 10004")
        adapterClie = communicator.createObjectAdapterWithEndpoints("ClientAdapter", "tcp -h localhost -p 10005")
        
        #Activar adaptadores
        adapterBlob.activate()
        adapterBlob1.activate()
        adapterAuth.activate()
        adapterClie.activate()

        logging.info("\nPara estos test se crean:")

        #Crear servicio autenticación
        authService = Authentication(adapterAuth)
        authService_proxy = IceDrive.AuthenticationPrx.checkedCast(adapterAuth.addWithUUID(authService))

        logging.info(f"· Un servicio de autenticación:\n {authService_proxy}\n")

        #Crear servicio descubrimiento
        discovery = Discovery(serviceId)
        discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(adapterBlob.addWithUUID(discovery))

        logging.info(f"· Un servicio de descubrimiento:\n {discovery_proxy}\n")
        logging.info("· Donde se anuncia el autenticador:")

        #Anunciar servicio autenticación
        discovery.announceAuthentication(authService_proxy) # Anuncio el servicio de autenticación

        #Crear servicio blob donde subiremos cosas para luego diferido
        blobService = BlobService(adapterBlob, discovery)
        blobService_proxy = IceDrive.BlobServicePrx.checkedCast(adapterBlob.addWithUUID(blobService))

        logging.info(f"\n· Un blob service:\n{blobService_proxy}\n")

        #Crear otro servicio blob donde descargaremos cosas para luego diferido
        blobService1 = BlobService(adapterBlob1, discovery)
        blobService1_proxy = IceDrive.BlobServicePrx.checkedCast(adapterBlob1.addWithUUID(blobService1))

        logging.info(f"· Otro blob service:\n{blobService1_proxy}\n")

        #Crear servicio blob query para diferido
        blobQuery = BlobQuery(blobService)
        blobQuery_proxy = IceDrive.BlobQueryPrx.checkedCast(adapterBlob.addWithUUID(blobQuery))

        logging.info(f"· Un blob query:\n{blobQuery_proxy}\n" )

        #Creamos nuestro servicio iceStorm
        topic_manager = communicator.propertyToProxy("IceStorm.TopicManager.Proxy")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager)

        #Obtenemos el topic de diferido
        try:
            topicQuery = topic_manager.retrieve("blob")
        except IceStorm.NoSuchTopic:
            topicQuery = topic_manager.create("blob")

        #Obtenemos el publisher de diferido
        publisher_blobQuery = IceDrive.BlobQueryPrx.uncheckedCast(topicQuery.getPublisher().ice_oneway())
        
        #Añadimos el publisher a los servicios
        blobService.pub_deferred = publisher_blobQuery
        blobService1.pub_deferred = publisher_blobQuery
    
        #Subscribimos los servicios al topic de diferido
        topicQuery.subscribeAndGetPublisher({}, blobQuery_proxy)

        # Creamos un usuario para los test
        user = authService.newUser("user_existente", "password123")
        user2 = authService.newUser("user_no_existente", "password123")
        authService.users.pop(user2) # Borro de la lista el usuario creado hace un momento

        logging.info("·TEST 1: Verificar usuario que existe --> test_user")

        # Verificamos que el usuario existe
        assert blobService.verify_user(user), f"User {user.getUsername()} not verified\n"
        logging.info(f"User {user.getUsername()} verified\n")

        logging.info("·TEST 2: Verificar usuario que no existe --> test_user2")

        # Verificamos que el usuario no existe
        assert not blobService.verify_user(user2), f"User {user.getUsername()} verified\n"
        logging.info(f"User {user2.getUsername()} not verified\n")

        # EMPIEZA LOS METODOS DE BLOB SERVICE

        current_directory = os.getcwd()
        file_path = current_directory+"/fileForUpload.txt"

        #Crea un archivo de prueba si no existe.
        create_file(file_path,"Contenido de prueba\n")

        # Crear una instancia de DataTransfer en el cliente
        client_data = DataTransfer(file_path)
        data_transfer = adapterClie.addWithUUID(client_data).ice_toString()
        data_transfer_proxy = IceDrive.DataTransferPrx.checkedCast(communicator.stringToProxy(data_transfer))

        logging.info("·TEST 3: Simular la subida de un blob con el usuario (user_existente)")

        blob_id = blobService_proxy.upload(user,data_transfer_proxy) # Subimos
        
        assert blob_id is not None, "Blob not uploaded\n"
        logging.info(f"Blob uploaded with ID: {blob_id}\n")

        logging.info("·TEST 4: Simular la subida de un blob con el usuario (user_no_existente)")

        blob_id_mal = blobService_proxy.upload(user2,data_transfer_proxy) #Subimos

        assert blob_id_mal is not None, "Blob uploaded\n"
        logging.info(f"Blob not uploaded with ID: {str(blob_id_mal)}\n")

        logging.info("·TEST 5: Simular la descarga de un blob con el usuario (user_existente)")

        download_blob_proxy = blobService_proxy.download(user,blob_id) #Descargamos

        assert download_blob_proxy is not None, "Blob not downloaded\n"
        logging.info(f"DataTransferPrx: {download_blob_proxy}\n")

        logging.info("·TEST 6: Simular la descarga de un blob con el usuario (user_no_existente)")

        download_blob_proxy_mal = blobService_proxy.download(user2,blob_id) #Descargamos

        assert str(download_blob_proxy_mal) is not None, "Blob downloaded\n"
        logging.info(f"DataTransferPrx: {download_blob_proxy_mal}\n")

        # EMPIEZA LOS METODOS DE DIFERIDO

        logging.info("·TEST 7: Descargar un blob por diferido")

        download_blob_proxy = blobService1_proxy.download(user,blob_id) # Descargamos

        assert download_blob_proxy is not None, "Blob not downloaded\n"
        logging.info(f"DataTransferPrx: {download_blob_proxy}\n")

        logging.info("·TEST 8: Link de un blob por diferido")
        blobService_proxy.link(blob_id) # Linkamos
        logging.info(f"Antes de la llamada el blob tiene: {blobService.blobs[blob_id]['ref_count']}")

        blobService1_proxy.link(blob_id) # Linkamos

        assert blobService.blobs[blob_id]['ref_count'] == 2, "Blob not linked\n"
        logging.info(f"Después de la llamada el blob tiene: {blobService.blobs[blob_id]['ref_count']}\n")

        logging.info("·TEST 9: Unlink de un blob por diferido")
        logging.info(f"Antes de la llamada el blob tiene: {blobService.blobs[blob_id]['ref_count']}")

        blobService1_proxy.unlink(blob_id) # Unlinkamos

        assert blobService.blobs[blob_id]['ref_count'] == 1, "Blob not unlinked\n"
        logging.info(f"Blob unliked con exito: {blobService.blobs[blob_id]['ref_count']}\n")

        try:
            os.remove(file_path) # Borramos el archivo de prueba
        except OSError as e:
            logging.info(f"Error al eliminar el archivo: {e}")
        
        communicator.destroy() # Destruimos el comunicador

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: test_blob.py --Ice.Config=../config/blob.config")
        sys.exit(1)

    test_blob_service()