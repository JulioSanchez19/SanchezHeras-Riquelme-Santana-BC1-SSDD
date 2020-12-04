#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W1203

import sys
import atexit
import logging
import argparse
import os
import json

import Ice
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet


class RoomsToolClient(Ice.Application):
    def run(self, argv):
        
        if len(argv)!=4:
            print("usage: roomsToolClient.py <-p/-r> <proxy> <token> <roomName/roomData>")

        proxy = self.communicator().stringToProxy(argv[2])
        self.roomMan = IceGauntlet.RoomManagerPrx.checkedCast(proxy)

        if not self.roomMan:
            raise RuntimeError('Invalid proxy')

        self.token=""
        with open("token.json",'r') as tokenFile:
            self.token=json.load(tokenFile)["token"]

        if argv[1]=="-p":#publish
            self.uploadMap(argv)
        elif argv[1]=="-r":#remove
            self.deleteMap(argv)
        else:
            print("Opciones: -p -r")
            
        
    def uploadMap(self,argv):
        try:
            print(self.token)
            self.roomMan.publish(self.token, argv[3])
        except IceGauntlet.RoomAlreadyExists:
            print("La room que desea guardar ya existe")
            os._exit(-1)
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
            os._exit(-1)
        except IceGauntlet.WrongRoomFormat:
            print("Formato de la room incorrecto")
            os._exit(-1)
        
    def deleteMap(self,argv):
        try:
            self.roomMan.remove(self.token, argv[3])
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
            os._exit(-1)
        except IceGauntlet.RoomNotExists:
            print("La room no existe")
            os._exit(-1)

sys.exit(RoomsToolClient().main(sys.argv))