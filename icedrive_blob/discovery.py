"""Servant implementations for service discovery."""

import Ice
import random
import logging
import IceDrive

class Discovery(IceDrive.Discovery):
    def __init__(self, serviceId):
        self.serviceId = serviceId  # Identificador único del servicio
        self.authenticationServices = []
        self.registeredServices = {}
        self.directoryServices = []
        self.blobServices = []
    
    def announceAuthentication(self, prx: IceDrive.AuthenticationPrx, current: Ice.Current = None) -> None:
        if prx not in self.authenticationServices:
            self.authenticationServices.append(prx)
            logging.info(f"Received Authentication Service: {prx}")

    def announceDirectoryService(self, prx: IceDrive.DirectoryServicePrx, current: Ice.Current = None) -> None:
        if prx not in self.directoryServices:
            self.directoryServices.append(prx)
            logging.info(f"Received Directory Service: {prx}")

    def announceBlobService(self, prx: IceDrive.BlobServicePrx, current: Ice.Current = None) -> None:
        serviceId = self.registeredServices.get(prx)

        if serviceId != self.serviceId:
            if prx not in self.blobServices:
                self.blobServices.append(prx)
                logging.info(f"Received Blob Service: {prx}")
    
    def get_blobService(self) -> IceDrive.BlobServicePrx:
        if not self.blobServices:
            return None
        return random.choice(self.blobServices)

    def get_authenticationService(self) -> IceDrive.AuthenticationPrx:
        if not self.authenticationServices:
            return None
        return random.choice(self.authenticationServices)

    def get_DirectoryService(self) -> IceDrive.DirectoryServicePrx:
        if not self.directoryServices:
            return None
        return random.choice(self.directoryServices)