"""Module for servants implementations."""
import os
import sys
import Ice
import hashlib
import logging
import IceDrive
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # Para poder ejecutar desde app.py y test.py
from delayed_response import BlobQueryResponse

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
        except Exception:
            raise IceDrive.FailedToReadData()

    def close(self, current: Ice.Current = None) -> None:
        self.file.close()

class BlobService(IceDrive.BlobService):
    def __init__(self, adapter, discovery):
        self.storage_path = tempfile.mkdtemp()
        os.environ["STORAGE_PATH"] = self.storage_path
        # Inicializar las variables de instancia
        self.discovery = discovery
        self.pub_deferred = None
        self.adapter = adapter
        self.blobs = {}  # Dicionario donde almacenar blobId y rutas de archivo
        
    def verify_user(self, user: IceDrive.UserPrx) -> bool:
        auth_service_proxy = self.discovery.get_authenticationService()
        result = False

        if auth_service_proxy is None:
            raise IceDrive.TemporaryUnavailable("Authentication service") 

        try:
           result = auth_service_proxy.verifyUser(user)
        except (Ice.ConnectionRefusedException, ConnectionError):
            self.discovery.authenticationServices.remove(auth_service_proxy)
            logging.warning("Connection refused")
        except Exception:
            #logging.warning("Error desde Exception")
            pass
            
        return result

    def calculate_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
    
    def link(self, blob_id: str, current: Ice.Current = None) -> None:    
        if blob_id in self.blobs:
            self.linkQuery(blob_id)
        else:
            response = BlobQueryResponse()
            response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

            self.pub_deferred.linkBlob(blob_id, response_proxy)

            response.start()

            if response.response:
                logging.info("Blob linked with BlobQuery")
            else:
                raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")
    
    def linkQuery(self, blob_id: str, current: Ice.Current = None) -> None:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")

        self.blobs[blob_id]['ref_count'] += 1

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        if blob_id in self.blobs:
            self.unlinkQuery(blob_id)
        else:
            response = BlobQueryResponse()
            response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

            self.pub_deferred.unlinkBlob(blob_id, response_proxy)

            response.start()

            if response.response:
                logging.info("Blob unlinked with BlobQuery")
            else:
                raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")

    def unlinkQuery(self, blob_id: str, current: Ice.Current = None) -> None:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")

        self.blobs[blob_id]['ref_count'] -= 1

        if self.blobs[blob_id]['ref_count'] == 0:
            os.remove(self.blobs[blob_id]['file_path'])
            del self.blobs[blob_id]

    def upload(self, user: IceDrive.UserPrx, blob: IceDrive.DataTransferPrx, current: Ice.Current = None) -> str:
        blob_id = None

        if self.verify_user(user): #Verifica el usuario
            temp_file_path = os.path.join(self.storage_path, "temp_upload")

            with open(temp_file_path, "wb") as f:
                while True:
                    data = blob.read(4096)
                    if not data:
                        break
                    f.write(data)
            blob.close()

            blob_id = self.calculate_hash(temp_file_path)
            final_path = os.path.join(self.storage_path, blob_id)

            if blob_id in self.blobs:
                os.remove(temp_file_path)  # Elimina el archivo temporal si el blob ya existe

                if not user.isAlive():
                    raise IceDrive.Unauthorized(user.getUsername())
            else:
                response = BlobQueryResponse()
                reponse_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

                self.pub_deferred.blobExists(blob_id, reponse_proxy)

                response.start()

                if response.response:
                    logging.info("Blob id exists with BlobQuery")
                    os.remove(temp_file_path)
                else:
                    logging.info("Blob id not exists with BlobQuery")
                    os.rename(temp_file_path, final_path)
                    self.blobs[blob_id] = {'file_path': final_path, 'ref_count': 0}
            
        return blob_id

    def download(self, user: IceDrive.UserPrx, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        dataTanferPrx = None
        
        if self.verify_user(user): #Verifica el usuario
            if blob_id in self.blobs:
                dataTanferPrx = self.downloadQuery(blob_id)

                if not user.isAlive():
                    raise IceDrive.Unauthorized(user.getUsername())
            else:
                response = BlobQueryResponse()
                response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

                self.pub_deferred.downloadBlob(blob_id, response_proxy)

                response.start()

                if response.response:
                    logging.info("Blob downloaded with BlobQuery")
                    dataTanferPrx = response.blob
                else:
                    raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")

        return dataTanferPrx

    def downloadQuery(self, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")
        
        file_path = self.blobs[blob_id]['file_path']
        data_transfer = DataTransfer(file_path, 'rb')

        # Registra la instancia de DataTransfer con el adaptador y obtiene su proxy
        proxyDataTransfer = self.adapter.addWithUUID(data_transfer)

        return IceDrive.DataTransferPrx.uncheckedCast(proxyDataTransfer)

    def blobIdExists(self, blob_id: str, current: Ice.Current = None) -> bool:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob(f"Blob not found {blob_id}")

        return blob_id in self.blobs

