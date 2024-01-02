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
        pass

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


    content = ""

    with open(file_path, 'r') as file:
            # Lee el contenido del archivo
            content = file.read()

    return content
   
def test_blob_service():
    with Ice.initialize(sys.argv) as communicator:
        serviceId = str(uuid.uuid4())

        adapterBlob = communicator.createObjectAdapter("BlobAdapter")
        adapterBlob1 = communicator.createObjectAdapterWithEndpoints("BlobAdapter1", "tcp -p 10003")
        adapterAuth = communicator.createObjectAdapterWithEndpoints("AuthAdapter", "tcp -p 10004")
        adapterClie = communicator.createObjectAdapterWithEndpoints("ClientAdapter", "tcp -p 10005")
        
        adapterBlob.activate()
        adapterBlob1.activate()
        adapterAuth.activate()
        adapterClie.activate()

        discovery = Discovery(serviceId)
        #discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(adapterBlob.addWithUUID(discovery))

        authService = Authentication(adapterAuth)
        authService_proxy = IceDrive.AuthenticationPrx.checkedCast(adapterAuth.addWithUUID(authService))

        blobService = BlobService(adapterBlob, discovery)
        blobService_proxy = IceDrive.BlobServicePrx.checkedCast(adapterBlob.addWithUUID(blobService))

        blobService1 = BlobService(adapterBlob1, discovery)
        blobService1_proxy = IceDrive.BlobServicePrx.checkedCast(adapterBlob1.addWithUUID(blobService1))

        logging.info("Proxy: %s\n", blobService_proxy)
        discovery.announceAuthentication(authService_proxy)

        blobQuery = BlobQuery(blobService)
        blobQuery_proxy = IceDrive.BlobQueryPrx.checkedCast(adapterBlob.addWithUUID(blobQuery))

        topic_manager = communicator.propertyToProxy("IceStorm.TopicManager.Proxy")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager)

        try:
            topicQuery = topic_manager.retrieve("blob")
        except IceStorm.NoSuchTopic:
            topicQuery = topic_manager.create("blob")

        publisher_blobQuery = IceDrive.BlobQueryPrx.uncheckedCast(topicQuery.getPublisher().ice_oneway())

        blobService1.blob_query_publisher = publisher_blobQuery

        topicQuery.subscribeAndGetPublisher({}, blobQuery_proxy)

        user = authService.newUser("test_user", "password123")
        user2 = authService.newUser("test_user2", "password123")

        logging.info("\n·TEST : Verificar usuario que existe --> test_user")

        if blobService.verify_user(user):
            logging.info(f"User {user.getUsername()} verified\n")
        else:
            logging.info(f"User {user.getUsername()} not verified\n")
    
        logging.info("·TEST : Verificar usuario que no existe --> test_user2")

        authService.users.pop(user2)
        if blobService.verify_user(user2):
            logging.info(f"User {user2.getUsername()} verified\n")
        else:
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

        logging.info("·TEST : Simular la subida de un blob con el usuario 'test_user'")

        blob_id = blobService_proxy.upload(user,data_transfer_proxy)
        logging.info(f"Blob uploaded with ID: {blob_id}\n")

        # EMPIEZA LOS METODOS DE DIFERIDO

        logging.info("·TEST : Descargar un blob por diferido")

        download_blob_proxy = blobService1_proxy.download(user,blob_id)
        logging.info(download_blob_proxy)


        communicator.waitForShutdown()



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: test_blob.py --Ice.Config=../config/config.blob")
        sys.exit(1)

    test_blob_service()