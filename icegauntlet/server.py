#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import json
import os 
import random
import glob
import string
import Ice
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet

ROOMS_DIRECTORY='rooms/*'

class JuegoI(IceGauntlet.Dungeon):
    def __init__(self):
        self._rooms_=glob.glob(ROOMS_DIRECTORY)

    def getRoom(self, current=None):
        if self._rooms_:
            return self._rooms_[random.randint(0, len(self._rooms_)-1)]
        else:
            raise IceGauntlet.RoomNotExists()

class GestionMapasI(IceGauntlet.RoomManager):#Ice.Application

    def __init__(self, proxyAuthServer):
        self.proxyAuthServer=proxyAuthServer

    def comprobarNombreDistinto(self,token,roomData, rooms):
        distinto=True
        roomJson={}
        for room in rooms:#recorre la lista de los archivos que estan en rooms 
            if os.path.exists(room):
                with open(room,'r') as fileRoom:
                    roomJson=json.load(fileRoom)
                    if roomJson["room"]==roomData["room"]:
                        distinto=False
        return distinto

    def elegirNombre(self):#crea un nombre aleatorio para guardar los nuevos mapas en rooms
        nombreArchivo=""
        while 1:
            nombreArchivo=random.choice(string.ascii_letters)+random.choice(string.ascii_letters)
            if nombreArchivo not in self._rooms_:
                break
        return nombreArchivo
            

    def publish(self, token, roomData, current=None):
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        roomData_={}
        if self.proxyAuthServer.isValid(token):#roomData es el nombre del archivo .json que se quiere meter a la "BD" rooms
            if os.path.exists(roomData):#no se concatena con rooms/ porque se supone que esta en el directorio de fuera
                with open(roomData,'r') as rooms:
                    try:
                        roomData_=json.load(rooms)
                    except:
                        raise IceGauntlet.WrongRoomFormat()   
            if roomData_["room"]==None or roomData_["data"]==None:#se comprueba que estan las keys room y data
                raise IceGauntlet.WrongRoomFormat()
            else:
                if self.comprobarNombreDistinto(token,roomData_, self._rooms_)==True:
                    roomData_["token"]=token#añadir el token al contenido del json nuevo
                    with open("rooms/"+self.elegirNombre()+".json", 'w') as contents:#se escribe el nuevo archivo en la "BD" rooms
                        json.dump(roomData_, contents, indent=4, sort_keys=True) 
                else:
                    raise IceGauntlet.RoomAlreadyExists()
        else:
            raise IceGauntlet.Unauthorized()
 
    def remove(self,token, roomName, current=None):
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        archivosComprobados=0
        if self.proxyAuthServer.isValid(token):#se comprueba si el token es valido  
            for room in self._rooms_:#recorre todas las rooms de la "BD" rooms
                if os.path.exists(room):
                    with open(room,'r') as fileRoom:
                        roomJson=json.load(fileRoom)
                        print(roomJson["room"])
                        if roomJson["room"]==roomName:
                            if roomJson["token"]==token:
                                print(room+" borrado")
                                os.remove(room)
                                break 
                            else:
                                raise IceGauntlet.Unauthorized()
                    archivosComprobados+=1
            if archivosComprobados==len(glob.glob(ROOMS_DIRECTORY)):
                raise IceGauntlet.RoomNotExists()
        else:
            raise IceGauntlet.Unauthorized()

class Server(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        servant = JuegoI()

        authServer = self.communicator().stringToProxy(argv[1])
        proxyAuthServer = IceGauntlet.AuthenticationPrx.checkedCast(authServer)

        if not proxyAuthServer:
            raise RuntimeError('Invalid proxy')

        servant2 = GestionMapasI(proxyAuthServer)

        adapter = broker.createObjectAdapter("ServerAdapter")
        proxyJuego=adapter.add(servant, broker.stringToIdentity("juego"))
        proxyGestionMapas=adapter.add(servant2,broker.stringToIdentity("gestionMapas"))

        print(proxyJuego, flush=True)
        print(proxyGestionMapas, flush=True)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))