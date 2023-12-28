"""Servant implementations for service discovery."""

import Ice
import uuid
import random
import logging
import IceDrive

class Discovery(IceDrive.Discovery):
    def __init__(self):
        self.serviceId = str(uuid.uuid4()) # Identificador único del servicio
        self.authenticationServices = []
        self.registeredServices = {}
        self.directoryServices = []
        self.blobServices = []
    
    def announceAuthentication(self, prx: IceDrive.AuthenticationPrx, current: Ice.Current = None) -> None:
        if prx not in self.blobServices:
            self.authenticationServices.append(prx)
            logging.info(f"Received Authentication Service Announcement: {prx}")

    def announceDirectoryService(self, prx: IceDrive.DirectoryServicePrx, current: Ice.Current = None) -> None:
        if prx not in self.directoryServices:
            self.directoryServices.append(prx)
            logging.info(f"Received Directory Service Announcement: {prx}")

    def announceBlobService(self, prx: IceDrive.BlobServicePrx, current: Ice.Current = None) -> None:
        serviceId = self.registeredServices.get(prx)

        if serviceId != self.serviceId:
            if prx not in self.blobServices:
                self.blobServices.append(prx)
                logging.info(f"Received Blob Service Announcement: {prx}")
    
    def get_blobService(self):
        if not self.blobServices:
            return None
        return random.choice(self.blobServices)

    def get_authenticationService(self):
        if not self.authenticationServices:
            return None
        return random.choice(self.authenticationServices)

    def get_DirectoryService(self):
        if not self.directoryServices:
            return None
        return random.choice(self.directoryServices)