"""Servant implementation for the delayed response mechanism."""

import Ice
import threading
import IceDrive

class BlobQueryResponse(IceDrive.BlobQueryResponse):
    def __init__(self):
        self.lock = threading.Lock()
        self.timer = threading.Timer(5.0, self.timeout)
        self.condition = threading.Condition(self.lock)
        self.response = None
        self.blobs = None

    def start(self) -> None:
        self.timer.start()

        while self.response == None:
            with self.lock:
                self.condition.wait()

    def timeout(self) -> None:
        with self.lock:
            self.response = False
            self.condition.notify()

    def downloadBlob(self, blob: IceDrive.DataTransferPrx, current: Ice.Current = None) -> None:
        with self.lock:
            self.blob = blob
            self.response = True
            self.timer.cancel()
            self.condition.notify()

    def blobExists(self, current: Ice.Current = None) -> None:
        with self.lock:
            self.response = True
            self.timer.cancel()
            self.condition.notify()

    def blobLinked(self, current: Ice.Current = None) -> None:
        with self.lock:
            self.response = True
            self.timer.cancel()
            self.condition.notify()
        
    def blobUnlinked(self, current: Ice.Current = None) -> None:
        with self.lock:
            self.response = True
            self.timer.cancel()
            self.condition.notify()

class BlobQuery(IceDrive.BlobQuery):
    def __init__(self, blobService):
        self.blobService = blobService

    def downloadBlob(self, blob_id: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        dataTransferPrx = self.blobService.downloadQuery(blob_id)

        if dataTransferPrx:
            response.downloadBlob(dataTransferPrx)

    def blobIdExists(self, blob_id: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        if self.blobService.blobIdExists(blob_id):
            response.blobExists()

    def linkBlob(self, blob_id: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        self.blobService.linkBlob(blob_id)
        response.blobLinked()

    def unlinkBlob(self, blob_id: str, response: IceDrive.BlobQueryResponsePrx, current: Ice.Current = None) -> None:
        self.blobService.unlinkBlob(blob_id)
        response.blobUnlinked()
