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
from .blob import BlobService
from typing import List

class BlobApp(Ice.Application):
    def __init__(self):
        self.serviceId = str(uuid.uuid4()) # Identificador único del servicio
        self.blobService_proxy = None
        self.announcementTopic = None
        self.topic_name = "discovery" # Nombre para suscribirme y publicar
        self.topic_manager = None
        self.discovery = None
        self.publisher = None
        self.running = True  # Variable de control para el hilo
        self.thread = None

    def run(self, args: List[str]) -> int:
        """Execute the code for the BlobApp class."""
        adapter = self.communicator().createObjectAdapter("BlobAdapter")
        adapter.activate()

        # Creamos los servants y sus proxys
        self.discovery = Discovery(self.serviceId)
        discovery_proxy = IceDrive.DiscoveryPrx.checkedCast(adapter.addWithUUID(self.discovery))

        blobService = BlobService(adapter, self.discovery)
        self.blobService_proxy = IceDrive.BlobServicePrx.checkedCast(adapter.addWithUUID(blobService))

        # Creamos el topic manager
        topic_manager_proxy = self.communicator().propertyToProxy("IceStorm.TopicManager.Proxy")
        self.topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_proxy)

        # Creamos el topic para publicar el servicio
        try:
            self.announcementTopic = self.topic_manager.retrieve(self.topic_name)
        except IceStorm.NoSuchTopic:
            self.announcementTopic = self.topic_manager.create(self.topic_name)

        # Creamos el publisher y nos suscribimos al topic
        self.publisher = IceDrive.DiscoveryPrx.uncheckedCast(self.announcementTopic.getPublisher())
        self.announcementTopic.subscribeAndGetPublisher({}, discovery_proxy)

        # Iniciar el hilo para anunciar el servicio cada 5 segundos
        self.thread = threading.Thread(target=self.publish_announcement)
        self.thread.daemon = True  # Esto asegura que el hilo no impida que el programa se cierre
        self.thread.start()

        logging.info("Proxy: %s", self.blobService_proxy)

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        logging.info("Announcements finished")
        self.running = False
        self.thread.join()  # Espera a que el hilo termine

        logging.info("Unsubcribe from Discovery")
        self.announcementTopic.unsubscribe(discovery_proxy)

        return 0

    # Implementación de la función de publicación
    def publish_announcement(self):
        while self.running:
            try:
                self.discovery.registeredServices[self.blobService_proxy] = self.serviceId
                self.publisher.announceBlobService(self.blobService_proxy)
                time.sleep(5)
            except Exception as e:
                logging.error("Error publishing BlobService announcement: %s", e)


def main():
    """Handle the icedrive-blob program."""
    app = BlobApp()
    return app.main(sys.argv)

