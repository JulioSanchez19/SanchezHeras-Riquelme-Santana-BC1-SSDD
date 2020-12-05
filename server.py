#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
# pylint: disable=W0613
'''
Servidor de juego y mapas
'''
import sys
import json
import os
import random
import glob
import string
import Ice
Ice.loadSlice('icegauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet

ROOMS_DIRECTORY='rooms/*'
GAME_PROXY="gameProxy.json"

class JuegoI(IceGauntlet.Dungeon):
    '''Sirviente de juego'''
    def __init__(self):
        self._rooms_=glob.glob(ROOMS_DIRECTORY)

    def getRoom(self, current=None):
        '''Devuelve una room de la BD'''
        room=""
        if self._rooms_:
            room=self._rooms_[random.randint(0, len(self._rooms_)-1)]
        else:
            raise IceGauntlet.RoomNotExists()
        return room

class GestionMapasI(IceGauntlet.RoomManager):
    '''Sirviente de gestion de mapas'''
    def __init__(self, proxy_auth_server):
        self.proxy_auth_server=proxy_auth_server
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
    
    def __comprobar_nombre_distinto__(self,token,room_data, rooms):
        '''Comprueba que el nombre de la room no este ya en la BD'''
        distinto=True
        room_json={}
        for room in rooms:
            if os.path.exists(room):
                with open(room,'r') as file_room:
                    room_json=json.load(file_room)
                    if room_json["room"]==room_data["room"]:
                        distinto=False
        return distinto

    def __elegir_nombre__(self):
        '''Elige un nombre aleatorio para la nueva room'''
        nombre_archivo=""
        while 1:
            nombre_archivo=random.choice(string.ascii_letters)+random.choice(string.ascii_letters)
            if nombre_archivo not in self._rooms_:
                break
        return nombre_archivo

    def publish(self, token, room_data, current=None):
        '''Publica una room en la BD'''
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        room_data_={}
        if self.proxy_auth_server.isValid(token):
            if os.path.exists(room_data):
                with open(room_data,'r') as rooms:
                    try:
                        room_data_=json.load(rooms)
                    except:
                        raise IceGauntlet.WrongRoomFormat()
            print(room_data_)
            if room_data_["room"] is None or room_data_["data"] is None:
                raise IceGauntlet.WrongRoomFormat()
            else:
                if self.__comprobar_nombre_distinto__(token,room_data_, self._rooms_)==True:
                    room_data_["token"]=token
                    with open("rooms/"+self.__elegir_nombre__()+".json", 'w') as contents:
                        json.dump(room_data_, contents, indent=4, sort_keys=True)
                else:
                    raise IceGauntlet.RoomAlreadyExists()
        else:
            raise IceGauntlet.Unauthorized()

    def remove(self,token, room_name, current=None):
        '''Borra una room de la BD'''
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        archivos_comprobados=0
        if self.proxy_auth_server.isValid(token):
            for room in self._rooms_:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        print(room_json["room"])
                        if room_json["room"]==room_name:
                            if room_json["token"]==token:
                                print(room+" borrado")
                                os.remove(room)
                                break
                            else:
                                raise IceGauntlet.Unauthorized()
                    archivos_comprobados+=1
            if archivos_comprobados==len(glob.glob(ROOMS_DIRECTORY)):
                raise IceGauntlet.RoomNotExists()
        else:
            raise IceGauntlet.Unauthorized()

class Server(Ice.Application):
    '''Servidor que contiene los sirvientes'''
    def run(self, argv):
        broker = self.communicator()
        servant = JuegoI()

        auth_server = self.communicator().stringToProxy(argv[1])
        proxy_auth_server = IceGauntlet.AuthenticationPrx.checkedCast(auth_server)

        if not proxy_auth_server:
            raise RuntimeError('Invalid proxy')

        servant2 = GestionMapasI(proxy_auth_server)

        adapter = broker.createObjectAdapter("ServerAdapter")
        proxy_juego=adapter.add(servant, broker.stringToIdentity("juego"))
        proxy_gestion_mapas=adapter.add(servant2,broker.stringToIdentity("gestionMapas"))

        print(proxy_gestion_mapas, flush=True)

        game_proxy={}
        game_proxy["proxy"]=str(proxy_juego)
        with open(GAME_PROXY,'w') as file_proxy:
            json.dump(game_proxy,file_proxy)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

server = Server()
sys.exit(server.main(sys.argv))
