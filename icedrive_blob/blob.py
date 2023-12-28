"""Module for servants implementations."""
import os
import Ice
import time
import uuid
import hashlib
import logging
import IceDrive
import IceStorm
import tempfile

class DataTransfer(IceDrive.DataTransfer):
    def __init__(self, file_path, mode='rb'):
        self.file_path = file_path
        self.file = open(file_path, mode)

    def read(self, size: int, current: Ice.Current = None) -> bytes:
        try:
            data = self.file.read(size)
            if data:
                return data
            else:
                return None  # Indica el final de la transferencia
        except Exception as e:
            raise IceDrive.FailedToReadData()

    def close(self, current: Ice.Current = None) -> None:
        self.file.close()

class BlobService(IceDrive.BlobService):
    def __init__(self, adapter, discovery):
        self.storage_path = tempfile.mkdtemp()
        os.environ["STORAGE_PATH"] = self.storage_path
        # Inicializar las variables de instancia
        self.serviceId = str(uuid.uuid4()) # Identificador único del servicio
        self.discovery = discovery
        self.adapter = adapter
        self.publisher = None
        self.running = True  # Variable de control para el hilo
        self.blobs = {}  # Dicionario donde almacenar blobId y rutas de archivo
        
    # Implementación de la función de publicación
    def publish_announcement(self, topic_manager, blobService_proxy, discovery_proxy, interval=5):
        if self.publisher is None:
            try:
                announcementTopic = topic_manager.retrieve("Discovery")
            except IceStorm.NoSuchTopic:
                logging.error(f"Error: The topic 'Discovery' was not found. Details: {e}")

            self.publisher = IceDrive.DiscoveryPrx.uncheckedCast(announcementTopic.getPublisher())
            announcementTopic.subscribeAndGetPublisher({}, discovery_proxy)
            
        while self.running:
            try:
                self.discovery.registeredServices[blobService_proxy] = self.serviceId
                self.publisher.announceBlobService(blobService_proxy)
                time.sleep(interval)
            except Exception as e:
                logging.error("Error publishing BlobService announcement: %s", e)


    def verify_user(self, user_proxy):
        auth_service_proxy = self.discovery.get_authenticationService()
        if not auth_service_proxy:
            raise Exception("No authentication service available")

        try:
            if not auth_service_proxy.verifyUser(user_proxy):
                raise IceDrive.UserNotExist(user_proxy)
        except Exception as e:
            logging.warning("Authentication service error: %s", e)

    def calculate_hash(self, file_path):
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
    
    def link(self, blob_id: str, current: Ice.Current = None) -> None:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob("Blob not found")

        self.blobs[blob_id]['ref_count'] += 1

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob("Blob not found")

        self.blobs[blob_id]['ref_count'] -= 1

        if self.blobs[blob_id]['ref_count'] == 0:
            os.remove(self.blobs[blob_id]['file_path'])
            del self.blobs[blob_id]

    def upload(self, user: IceDrive.UserPrx, blob: IceDrive.DataTransferPrx, current: Ice.Current = None) -> str:
        self.verify_user(user) #Verifica el usuario
        
        # Ruta temporal del archivo
        temp_file_path = os.path.join(self.storage_path, "temp_upload")

        # Recibe y escribe los datos en un archivo temporal
        with open(temp_file_path, "wb") as f:
            while True:
                data = blob.read(4096)
                if not data:
                    break
                f.write(data)
        blob.close()

        # Calcula el hash del archivo y verifica si ya existe
        blob_id = self.calculate_hash(temp_file_path)
        final_path = os.path.join(self.storage_path, blob_id)

        if blob_id not in self.blobs:
            os.rename(temp_file_path, final_path)
            self.blobs[blob_id] = {'file_path': final_path, 'ref_count': 0}
        else:
            os.remove(temp_file_path)  # Elimina el archivo temporal si el blob ya existe
            
        return blob_id

    def download(self, user: IceDrive.UserPrx, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        self.verify_user(user) #Verifica el usuario

        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob("Blob not found")

        file_path = self.blobs[blob_id]['file_path']
        data_transfer = DataTransfer(file_path, 'rb')

        # Registra la instancia de DataTransfer con el adaptador y obtiene su proxy
        proxyDataTransfer = self.adapter.addWithUUID(data_transfer)

        return IceDrive.DataTransferPrx.uncheckedCast(proxyDataTransfer)
