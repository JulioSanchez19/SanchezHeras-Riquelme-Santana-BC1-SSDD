#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
# pylint: disable=W0613
'''
Servidor de juego y mapas
'''
import sys
import json
import os
import IceStorm
import uuid
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
SERVIDORES={}

class DungeonAreaI(IceGauntlet.DungeonArea):
    def __init__(self, topic_mgr):
        topic_name = self.getEventChannel()
        qos = {}#valores de calidad de servicio/ no lo vamos a utilizar
        try:
            topic = topic_mgr.retrieve(topic_name)#coger el proxy del topic
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
        adapter = ic.createObjectAdapter("SaludarAdapter")
        subscriber = adapter.addWithUUID(servant)
        topic.subscribeAndGetPublisher(qos, subscriber)

    def getEventChannel():
        return "DungeonAreaSync"


class JuegoI(IceGauntlet.Dungeon):
    '''Sirviente de juego'''
    def __init__(self, topic_mgr):
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        self._topic_mgr_=topic_mgr

    # def getRoom(self, current=None):
    #     '''Devuelve una room de la BD'''
    #     self._rooms_=glob.glob(ROOMS_DIRECTORY)
    #     room=""
    #     if self._rooms_:
    #         room=self._rooms_[random.randint(0, len(self._rooms_)-1)]
    #     else:
    #         raise IceGauntlet.RoomNotExists()
    #     return room

    def getEntrance(self, current=None):
        dungArea=DungeonAreaI(self._topic_mgr_)
        newDungArea=current.adapter().addWithUUID(dungArea)
        return IceGauntlet.DungeonAreaPrx.checkedCast(newDungArea)
# class RoomManagerSyncI(IceGauntlet.RoomManagerSync):
#     def __init__(self, id, publisher, remote_reference):
#         self._publisher_=publisher
#         self._id_=id
#         self._remote_reference_=remote_reference
#     def hello(self, manager, managerId, current=None):
#         if(managerId!=str(self._id_)):
#             self.announce(self._remote_reference_, self._id_)
#             SERVIDORES[managerId]=manager
#             print(SERVIDORES)
#     def announce(self, manager, managerId, current=None):
#         if(managerId!=str(self._id_)):
#             SERVIDORES[managerId]=manager
#     def newRoom(self, roomName, managerId, current=None):
#         mapaExistente=False
#         if(managerId!=self._id_):
#             rooms=glob.glob(ROOMS_DIRECTORY)
#             for room in rooms:
#                 if os.path.exists(room):
#                     with open(room,'r') as file_room:
#                         room_json=json.load(file_room)
#                         if room_json["room"]==roomName:
#                             mapaExistente=True
#             if(mapaExistente==False):
#                 remote_reference=SERVIDORES[managerId]
#                 remote_reference.getRoom(roomName)
#         else:   
#             print("Soy yo "+str(managerId))
#     def removedRoom(self, roomName, current=None):
#         rooms=glob.glob(ROOMS_DIRECTORY)
#         for room in rooms:
#             if os.path.exists(room):
#                 with open(room,'r') as file_room:
#                     room_json=json.load(file_room)
#                     if room_json["room"]==roomName:
#                         os.remove(room)

class GestionMapasI(IceGauntlet.RoomManager, IceGauntlet.RoomManagerSync):
    '''Sirviente de gestion de mapas'''
    def __init__(self, proxy_auth_server,broker, topic):
        self.proxy_auth_server=proxy_auth_server
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        self._id_=uuid.uuid4()
        print("MI ID "+str(self._id_))
        self._topic_=topic
        adapter = broker.createObjectAdapter('RoomManagerAdapter')
        proxy=adapter.addWithUUID(self)
        self._remote_reference_=IceGauntlet.RoomManagerPrx.checkedCast(proxy)
        #print("MI REFERENCIA REMOTA "+str(self._remote_reference_))
        print("MI REFERENCIA REMOTA "+str(self._remote_reference_))
        adapter.activate()
        
        self._publisherPrx_=self._topic_.getPublisher()
        self._publisher_=IceGauntlet.RoomManagerSyncPrx.uncheckedCast(self._publisherPrx_)
        
        #roomManagerSync = RoomManagerSyncI(self._id_, self._publisher_, remoteReference)
        
        self._adapter_ = broker.createObjectAdapter("RoomManagerSyncAdapter")
        subscriber = self._adapter_.addWithUUID(self)
        qos={}
        self._topic_.subscribeAndGetPublisher(qos, subscriber)
        self._adapter_.activate()

        self._publisher_.hello(self._remote_reference_, str(self._id_))
        #self._topic_.unsubscribe()

        
    def __comprobar_nombre_distinto__(self,room_data, rooms):
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
        owner=self.proxy_auth_server.getOwner(token)
        if owner is not None:
            if os.path.exists("/home/julio/Escritorio/TrabajoDist/"+room_data):
                with open("/home/julio/Escritorio/TrabajoDist/"+room_data,'r') as rooms:
                    try:
                        room_data_=json.load(rooms)
                    except:
                        raise IceGauntlet.WrongRoomFormat()
                try:
                    if room_data_["room"] is None or room_data_["data"] is None:
                        raise IceGauntlet.WrongRoomFormat()
                    else:
                        if self.__comprobar_nombre_distinto__(room_data_, self._rooms_)==True:
                            room_data_["owner"]=owner
                            nombre_aleatorio=self.__elegir_nombre__()
                            with open("rooms/"+nombre_aleatorio+".json", 'w') as contents:
                                json.dump(room_data_, contents, indent=4, sort_keys=True)
                            if os.path.exists("rooms/"+nombre_aleatorio+".json"):
                                with open("rooms/"+nombre_aleatorio+".json",'r') as file_room:
                                    room_json=json.load(file_room)
                                    nombre_room=room_json["room"]
                                    self._publisher_.newRoom(nombre_room,str(self._id_))
                        else:
                            raise IceGauntlet.RoomAlreadyExists()
                except IceGauntlet.RoomAlreadyExists:
                    raise IceGauntlet.RoomAlreadyExists()
                except:
                    raise IceGauntlet.WrongRoomFormat()
        else:
            raise IceGauntlet.Unauthorized()

    def remove(self,token, room_name, current=None):
        '''Borra una room de la BD'''
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        archivos_comprobados=0
        owner=self.proxy_auth_server.getOwner(token)
        if owner is not None:
            for room in self._rooms_:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        if room_json["room"]==room_name:
                            #if room_json["token"]==token:
                            os.remove(room)
                            print(room+" borrado")
                            self._publisher_.removedRoom(room_name)
                            print("ha mandado removedroom")
                            break
                            # else:
                            #     raise IceGauntlet.Unauthorized()
                    archivos_comprobados+=1
            if archivos_comprobados==len(glob.glob(ROOMS_DIRECTORY)):
                raise IceGauntlet.RoomNotExists()
        else:
            raise IceGauntlet.Unauthorized()
    def getRoom(self, roomName, current=None):
        print("llega getRoom"+roomName)
        rooms=glob.glob(ROOMS_DIRECTORY)
        room_json={}
        data=""
        for room in rooms:
            if os.path.exists(room):
                print("existe path")
                with open(room,'r') as file_room:
                    room_json=json.load(file_room)
                    if room_json["room"]==roomName:
                        print("igual")
                        data=room_json
                        print(type(data))
                        break
        return json.dumps(data)#str(data)
    def hello(self, manager, managerId, current=None):
        if(managerId!=str(self._id_)):
            self._publisher_.announce(self._remote_reference_, str(self._id_))
            print("Hello")
            SERVIDORES[managerId]=manager
            print(SERVIDORES)
    def announce(self, manager, managerId, current=None):
        if(managerId!=str(self._id_)):
            print("announce")
            SERVIDORES[managerId]=manager#self.announce(self._remote_reference_, self._id_)
            print(SERVIDORES)
    def newRoom(self, roomName, managerId, current=None):
        mapaExistente=False
        #room_json={}
        if(managerId!=self._id_):
            rooms=glob.glob(ROOMS_DIRECTORY)
            for room in rooms:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        if room_json["room"]==roomName:
                            mapaExistente=True
                            break
            if(mapaExistente==False):
                remote_reference=SERVIDORES[managerId]
                data=""
                data=remote_reference.getRoom(roomName)
                nombre_aleatorio=self.__elegir_nombre__()
                with open("rooms/"+nombre_aleatorio+".json", 'w') as contents:
                    json.dump(json.loads(data), contents, indent=4, sort_keys=True)
        else:   
            print("Soy yo "+str(managerId))
    def removedRoom(self, roomName, current=None):
        print("entra remove")
        print(roomName)
        rooms=glob.glob(ROOMS_DIRECTORY)
        room_json={}
        for room in rooms:
            print("antes existe")
            if os.path.exists(room):
                with open(room,'r') as file_room:
                    print("archivo abierto")
                    room_json=json.load(file_room)
                    if room_json["room"]==roomName:
                        print("borra")
                        os.remove(room)

class Server(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    '''Servidor que contiene los sirvientes'''
    def run(self, argv):
        broker = self.communicator()
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2
        topic_name = "RoomManagerSyncChannel"
        try:
            topic = topic_mgr.retrieve(topic_name)
            print("hay topic")
        except IceStorm.NoSuchTopic:
            print("no such topic found, creating")
            topic = topic_mgr.create(topic_name)

        # publisherPrx = topic.getPublisher()
        # publisher = IceGauntlet.RoomManagerSyncPrx.uncheckedCast(publisherPrx)

        servant = JuegoI(topic)

        auth_server = self.communicator().stringToProxy(argv[1])
        proxy_auth_server = IceGauntlet.AuthenticationPrx.checkedCast(auth_server)

        if not proxy_auth_server:
            raise RuntimeError('Invalid proxy')

        servant2 = GestionMapasI(proxy_auth_server,broker, topic)

        # adapter = broker.createObjectAdapter("ServerAdapter")
        # #proxy_juego=adapter.add(servant, broker.stringToIdentity("juego"))
        # proxy_gestion_mapas=adapter.add(servant2,broker.stringToIdentity("gestionMapas"))

        # print(proxy_gestion_mapas, flush=True)

        # game_proxy={}
        # game_proxy["proxy"]=str(proxy_juego)
        # with open(GAME_PROXY,'w') as file_proxy:
        #     json.dump(game_proxy,file_proxy)

        # #servant=RoomManagerSyncChannel(top)
        # for i in range(5):
        #     top.hello("Hola chavales %s"%i)

        # servant=SaludoI(top)
        # adapter = broker.createObjectAdapter("PrinterAdapter")
        # subscriber = adapter.addWithUUID(servant)
        # topic.subscribeAndGetPublisher(qos, subscriber)



        #adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        #topic.unsubscribe(subscriber)

        return 0

server = Server()
sys.exit(server.main(sys.argv))
