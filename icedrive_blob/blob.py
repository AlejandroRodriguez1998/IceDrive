"""Module for servants implementations."""
import os
import Ice
import hashlib
import IceDrive
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
            raise IceDrive.FailedToReadData(str(e))

    def close(self, current: Ice.Current = None) -> None:
        self.file.close()

class BlobService(IceDrive.BlobService):
    def __init__(self, adapter):
        self.adapter = adapter
        self.storage_path = tempfile.mkdtemp()
        os.environ["STORAGE_PATH"] = self.storage_path
        self.blobs = {}  # Dicionario donde almacenar blobId y rutas de archivo

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

    def upload(self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None) -> str:
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

    def download(self, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        if blob_id not in self.blobs:
            raise IceDrive.UnknownBlob("Blob not found")

        file_path = self.blobs[blob_id]['file_path']
        data_transfer = DataTransfer(file_path, 'rb')

        # Registra la instancia de DataTransfer con el adaptador y obtiene su proxy
        proxyDataTransfer = self.adapter.addWithUUID(data_transfer)

        return IceDrive.DataTransferPrx.uncheckedCast(proxyDataTransfer)
