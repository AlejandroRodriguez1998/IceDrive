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
        """Mark a blob_id file as linked in some directory."""

    def unlink(self, blob_id: str, current: Ice.Current = None) -> None:
        """Mark a blob_id as unlinked (removed) from some directory."""

    def upload(
        self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None
    ) -> str:
        """Register a DataTransfer object to upload a file to the service."""

    def download(self, blob_id: str, current: Ice.Current = None) -> IceDrive.DataTransferPrx:
        """Return a DataTransfer objet to enable the client to download the given blob_id."""
