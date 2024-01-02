"""Module for servants implementations."""
import os
import Ice
import hashlib
import logging
import IceDrive
import tempfile

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
        self.blob_query_publisher = None
        self.discovery = discovery
        self.adapter = adapter
        self.blobs = {}  # Dicionario donde almacenar blobId y rutas de archivo
        
    def verify_user(self, user: IceDrive.UserPrx) -> bool:
        auth_service_proxy = self.discovery.get_authenticationService()
        result = False

        try:
           result = auth_service_proxy.verifyUser(user)
        except IceDrive.UserNotExist:
            logging.warning("User does not exist")
        except (Ice.ConnectionRefusedException, ConnectionError):
            logging.warning("Connection refused")
            self.discovery.authenticationServices.remove(auth_service_proxy)
        except Exception as e:
            logging.warning("Error: %s", e)

        return result

    def calculate_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()
    
    def link(self, blob_id: str, current: Ice.Current = None) -> None:    
        if blob_id in self.blobs:
            self.blobs[blob_id]['ref_count'] += 1
        else:
            response = BlobQueryResponse()
            response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

            self.blob_query_publisher.linkBlob(blob_id, response_proxy)

            response.start()

            if response.response:
                logging.info("Blob linked with BlobQuery")

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:     
        if blob_id in self.blobs:
            self.blobs[blob_id]['ref_count'] -= 1

            if self.blobs[blob_id]['ref_count'] == 0:
                os.remove(self.blobs[blob_id]['file_path'])
                del self.blobs[blob_id]
        else:
            response = BlobQueryResponse()
            response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

            self.blob_query_publisher.unlinkBlob(blob_id, response_proxy)

            response.start()

            if response.response:
                logging.info("Blob unlinked with BlobQuery")

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

            if blob_id not in self.blobs:
                response = BlobQueryResponse()
                reponse_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

                self.blob_query_publisher.blobExists(blob_id, reponse_proxy)

                response.start()

                if response.response:
                    logging.info("Blob id exists with BlobQuery")
                    os.remove(temp_file_path)
                else:
                    os.rename(temp_file_path, final_path)
                    self.blobs[blob_id] = {'file_path': final_path, 'ref_count': 0}
            else:
                os.remove(temp_file_path)  # Elimina el archivo temporal si el blob ya existe
            
        return blob_id

    def download(self, user: IceDrive.UserPrx, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        dataTanferPrx = None
        
        if self.verify_user(user) or user is None: #Verifica el usuario
            if blob_id in self.blobs:
            
                file_path = self.blobs[blob_id]['file_path']
                data_transfer = DataTransfer(file_path, 'rb')

                # Registra la instancia de DataTransfer con el adaptador y obtiene su proxy
                dataTanferPrx = IceDrive.DataTransferPrx.uncheckedCast(self.adapter.addWithUUID(data_transfer))

            else:
                response = BlobQueryResponse()
                response_proxy = IceDrive.BlobQueryResponsePrx.uncheckedCast(self.adapter.addWithUUID(response))

                self.blob_query_publisher.downloadBlob(blob_id, response_proxy)

                response.start()

                if response.response:
                    logging.info("Blob downloaded with BlobQuery")
                    dataTanferPrx = response.blob

        return dataTanferPrx

    def downloadQuery(self, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob("Blob not found")

        file_path = self.blobs[blob_id]['file_path']
        data_transfer = DataTransfer(file_path, 'rb')

        # Registra la instancia de DataTransfer con el adaptador y obtiene su proxy
        proxyDataTransfer = self.adapter.addWithUUID(data_transfer)

        return IceDrive.DataTransferPrx.uncheckedCast(proxyDataTransfer)

    def blobIdExists(self, blob_id: str, current: Ice.Current = None) -> bool:
        return blob_id in self.blobs

