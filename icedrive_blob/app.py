"""Blob service application."""
import sys
import Ice
import logging
import IceStorm
import threading

from .discovery import Discovery
from .blob import BlobService
from typing import List

class BlobApp(Ice.Application):
    """Implementation of the Ice.Application for the blob service."""

    def run(self, args: List[str]) -> int:
        """Execute the code for the BlobApp class."""
        topic_manager_proxy = self.communicator().propertyToProxy("IceStorm.TopicManager.Proxy")
        topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_proxy)

        adapter = self.communicator().createObjectAdapter("BlobAdapter")
        adapter.activate()

        # Creamos los servants
        discovery = Discovery()
        discovery_proxy = adapter.addWithUUID(discovery)

        blobService = BlobService(adapter, discovery)
        blobService_proxy = adapter.addWithUUID(blobService)

        # Iniciar el hilo para anunciar mi servicio cada 5 segundos
        announcement_thread = threading.Thread(target=blobService.publish_announcement, 
                                                    args=(topic_manager, blobService_proxy, discovery_proxy))
        announcement_thread.daemon = True  # Esto asegura que el hilo no impida que el programa se cierre
        announcement_thread.start()

        logging.info("Proxy: %s", blobService_proxy)

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        logging.info("Discovery (announcement) finished")
        blobService.running = False
        announcement_thread.join()  # Espera a que el hilo termine
        blobService.publisher.unsubscribe(discovery_proxy)

        return 0

def main():
    """Handle the icedrive-blob program."""
    app = BlobApp()
    return app.main(sys.argv)

