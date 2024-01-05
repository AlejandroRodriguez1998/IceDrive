"""Blob service application."""
import sys
import Ice
import uuid
import time
import logging
import IceStorm
import IceDrive
import threading

from .discovery import Discovery
from .delayed_response import BlobQuery
from .blob import BlobService
from typing import List

class BlobApp(Ice.Application):
    def __init__(self):
        self.serviceId = str(uuid.uuid4()) # Identificador único del servicio
        self.publisher_discovery = None
        self.blobService_proxy = None
        self.discovery = None
        self.running = True  # Variable de control para el hilo

    def run(self, args: List[str]) -> int:
        """Execute the code for the BlobApp class."""
        adapter = self.communicator().createObjectAdapter("BlobAdapter")
        adapter.activate()

        self.discovery = Discovery(self.serviceId)
        discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(adapter.addWithUUID(self.discovery))

        blobService = BlobService(adapter, self.discovery)
        self.blobService_proxy = IceDrive.BlobServicePrx.checkedCast(adapter.addWithUUID(blobService))

        logging.info("Proxy: %s\n", self.blobService_proxy)

        blobQuery = BlobQuery(blobService)
        blobQuery_proxy = IceDrive.BlobQueryPrx.checkedCast(adapter.addWithUUID(blobQuery))

        topic_manager = self.communicator().propertyToProxy("IceStorm.TopicManager.Proxy")
        topic_managerPrx = IceStorm.TopicManagerPrx.checkedCast(topic_manager)

        discovery_topic = self.get_announcement_topic("discovery", topic_managerPrx)
        blobQuery_topic = self.get_announcement_topic("blob", topic_managerPrx)

        self.publisher_discovery = IceDrive.DiscoveryPrx.uncheckedCast(discovery_topic.getPublisher().ice_oneway())
        publisher_blobQuery = IceDrive.BlobQueryPrx.uncheckedCast(blobQuery_topic.getPublisher().ice_oneway())

        blobService.pub_deferred = publisher_blobQuery

        discovery_topic.subscribeAndGetPublisher({}, discovery_proxy)
        blobQuery_topic.subscribeAndGetPublisher({}, blobQuery_proxy)

        # Iniciar el hilo para anunciar el servicio cada 5 segundos
        thread = threading.Thread(target=self.publish_announcement)
        thread.daemon = True  # No impide que el programa se cierre
        thread.start()

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        logging.info("Announcements finished")
        self.running = False
        thread.join()  # Espera a que el hilo termine
        discovery_topic.unsubscribe(discovery_proxy)
        blobQuery_topic.unsubscribe(blobQuery_proxy)

        return 0

    def publish_announcement(self) -> None:
        # Para diferenciar que esto es nuestro servicio
        self.discovery.registeredServices[self.blobService_proxy] = self.serviceId

        while self.running:
            try:
                self.publisher_discovery.announceBlobService(self.blobService_proxy)
                time.sleep(5)
            except Exception as e:
                logging.error("Error publishing BlobService announcement: %s", e)
    
    def get_announcement_topic(self, nombre: str, topic_manager: IceStorm.TopicManagerPrx) -> str:
        try:
            topic = topic_manager.retrieve(nombre)
        except IceStorm.NoSuchTopic:
            topic = topic_manager.create(nombre)
        return topic


def main():
    """Handle the icedrive-blob program."""
    app = BlobApp()
    return app.main(sys.argv)

