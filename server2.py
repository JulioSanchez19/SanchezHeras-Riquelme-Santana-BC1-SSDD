#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
# pylint: disable=W0613
# pylint: disable=C0103
#Se ha deshabilitado la regla C0103 debido a la necesidad de
#correspondencia de los metodos con el slice proporcionado
# pylint: disable=E1101
#Deshabilitado debido a que lo detecta como error pero
#se hizo asi en clase
'''
Servidor de juego y mapas
'''
import sys
import json
import os
import uuid
import random
import time
import glob
import string
import pickle
import IceStorm
import icegauntlettool
import Ice
Ice.loadSlice('icegauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet

ROOMS_DIRECTORY = 'rooms/*'
GAME_PROXY = "gameProxy.json"
SERVIDORES = {}

# pylint: disable=R0903
#Deshabilitado debido a que son clases unicamente
#para representar struct de icegauntlet.ice
class Item(IceGauntlet.Item):
    '''Clase de Items'''
    def __init__(self, id, item_type, posicion_x, posicion_y):
        self.itemId = id
        self.itemType = item_type
        self.positionX = posicion_x
        self.positionY = posicion_y

class Actor(IceGauntlet.Actor):
    '''Clase de actores'''
    def __init__(self, actorId, attributes):
        self.actorId = actorId
        self.attributes = attributes

class DungeonAreaI(IceGauntlet.DungeonArea, IceGauntlet.DungeonAreaSync):
    '''Clase para el dungeon area'''
    def __init__(self, topic_mgr, adapter, dung_area_sync_adapter, broker):
        self._topic_mgr_ = topic_mgr
        self._adapter_ = adapter
        self._broker_ = broker
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        self._channel_name_ = str(uuid.uuid4())
        print("CANAL DE EVENTOS" +self._channel_name_)
        #OBJETO DEL SIGUIENTE DUNGEON AREA
        self._dungeon_area_ = None
        self._dung_area_sync_adapter = dung_area_sync_adapter

        #SE CREA EL CANAL DE EVENTOS
        topic_name = self.getEventChannel()
        qos = {}
        try:
            self._topic_ = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            self._topic_ = topic_mgr.create(topic_name)

        self._publisherPrx_=self._topic_.getPublisher()
        self._publisher_=IceGauntlet.DungeonAreaSyncPrx.uncheckedCast(self._publisherPrx_)

        subscriber = self._dung_area_sync_adapter.addWithUUID(self)
        qos={}
        self._topic_.subscribeAndGetPublisher(qos, subscriber)
        self._dung_area_sync_adapter.activate()

        self._items_=[]
        self._items2_=[]
        self._actors_=[]

        self._tuplas_={}

        if len(self._rooms_) != 0:
            room_aleatoria=self._rooms_[random.randint(0,len(self._rooms_)-1)]
            with open("rooms/"+room_aleatoria,'r') as rooms:
                room_data={}
                room_data=json.load(rooms)
                walls=icegauntlettool.filter_map_objects(json.dumps(room_data))
                self._mapa_=walls
                items=icegauntlettool.get_map_objects(json.dumps(room_data))
                self._items2_=icegauntlettool.get_map_objects(json.dumps(room_data))
                i=0
                for it in items:
                    id=str(i)
                    posicion=it[1]
                    item_type=it[0]
                    self._tuplas_[i]=(item_type, posicion)
                    self._items_.append(Item(id, item_type, posicion[0], posicion[1]))
                    i+=1
        else:
            raise IceGauntlet.RoomNotExists()

    def getEventChannel(self, current=None):
        '''Retorna el canal de eventos'''
        return self._channel_name_

    def getMap(self, current=None):
        '''Retorna el mapa de juego'''
        print("getMap")
        return self._mapa_

    def getActors(self, current=None):
        '''Retorna los actores de un mapa'''
        print("getActors")
        return self._actors_

    def getItems(self, current=None):
        '''Retorna los items de un mapa'''
        print("getItems")
        return self._items_

    def getNextArea(self, current=None):
        '''Retorna el siguiente dungeon_area'''
        print("getnextarea")
        if self._dungeon_area_ is None:
            new_dung_area=self._dung_area_sync_adapter.addWithUUID(DungeonAreaI(self._topic_mgr_, self._adapter_, self._dung_area_sync_adapter, self._broker_))
            self._dungeon_area_=IceGauntlet.DungeonAreaPrx.checkedCast(new_dung_area)
        return self._dungeon_area_
    def fireEvent(self, event, senderId, current=None):
        '''Gestiona los eventos de los mapas'''
        print("ACTORES DE AREA "+self._channel_name_)
        print(self._actors_)
        evento=pickle.loads(event)
        if evento[0]=="spawn_actor":
            self._actors_.append(Actor(evento[1],json.dumps(evento[2])))
            print("ACTORES")
            print(self._actors_)
        elif evento[0]=="kill_object":
            contador_objetos=0
            for it in self._items_:
                if it.itemId==evento[1]:
                    self._items_.pop(contador_objetos)
                contador_objetos+=1
            contador_actores=0
            for act in self._actors_:
                if act.actorId==evento[1]:
                    # next_area=self.getNextArea()
                    # channel=next_area.getEventChannel()
                    # channel.fireEvent(("spawn_actors", act.actorId, act.attributes), None)
                    self._actors_.pop(contador_actores)
                contador_actores+=1
        elif evento[0]=="open_door":
            contador=0
            for it in self._items_:
                if it.itemId==evento[2]:
                    item=self._items_.pop(contador)
                    p_aux=(item.positionX, item.positionY)
                    adjacent_items=icegauntlettool.search_adjacent_door(self._tuplas_, p_aux, None)
                    for adj in adjacent_items:
                        contadorAdj=0
                        for it in self._items_:
                            if it.itemId==str(adj):
                                self._items_.pop(contadorAdj)
                            contadorAdj+=1
                    print("ITEMS DESPUES DE ADJACENT")
                    print(self._items_)
                contador+=1

class JuegoI(IceGauntlet.Dungeon):
    '''Sirviente de juego'''
    def __init__(self, topic_mgr, adapter, dung_area_adapter, broker):
        self._topic_mgr_ = topic_mgr
        self._adapter_ = adapter
        self._broker_ = broker
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        self._dungeon_area__sync_adapter=dung_area_adapter
        self._dungeon_area_=None

    def getEntrance(self, current=None):
        '''Retorna la entrada de un mapa'''
        if self._dungeon_area_ is None:
            if self._rooms_ is not None:
                #new_dung_area=self._adapter_.addWithUUID
                # (DungeonAreaI(self._topic_mgr_, self._adapter_,self._
                # dungeon_area__sync_adapter, self._broker_))
                new_dung_area=self.dung_area_sync_adapter.addWithUUID(DungeonAreaI(self._topic_mgr_, self._adapter_,self._dungeon_area__sync_adapter, self._broker_))
                self._dungeon_area_=IceGauntlet.DungeonAreaPrx.checkedCast(new_dung_area)
            else:
                raise IceGauntlet.RoomNotExists()
        return self._dungeon_area_

class GestionMapasI(IceGauntlet.RoomManager, IceGauntlet.RoomManagerSync):
    '''Sirviente de gestion de mapas'''
    def __init__(self, proxy_auth_server,broker, topic):
        self.proxy_auth_server=proxy_auth_server
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        self._id_=uuid.uuid4()
        self._topic_=topic
        self._adapter_ = broker.createObjectAdapter("Room_Manager_Adapter")
        self._adapter_interno_ = broker.createObjectAdapter("Room_Manager2_Adapter")
        proxy2 = self._adapter_interno_.addWithUUID(self)
        self._remote_reference_=IceGauntlet.RoomManagerPrx.checkedCast(proxy2)
        print("Proxy room manager:")
        print(self._remote_reference_)
        self._adapter_interno_.activate()
        id_ = broker.getProperties().getProperty('Identity')
        self._adapter_.add(self, broker.stringToIdentity(id_))

        self._publisherPrx_=self._topic_.getPublisher()
        self._publisher_=IceGauntlet.RoomManagerSyncPrx.uncheckedCast(self._publisherPrx_)

        subscriber = self._adapter_interno_.addWithUUID(self)
        qos={}
        self._topic_.subscribeAndGetPublisher(qos, subscriber)
        self._adapter_.activate()

        time.sleep(random.randint(0,1))
        self._publisher_.hello(self._remote_reference_, str(self._id_))

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

    def __actualizar_rooms__(self, available_rooms, rooms, manager):
        '''Actualiza los mapas con respecto a otros servidores'''
        for available_room in available_rooms:
            mapa_existente=0
            for room in rooms:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        if room_json["room"]==available_room:
                            mapa_existente=1
                            break
            if mapa_existente==0:
                new_room = manager.getRoom(available_room)
                nombre_aleatorio=self.__elegir_nombre__()
                with open("rooms/"+nombre_aleatorio+".json", 'w') as contents:
                    json.dump(json.loads(new_room), contents, indent=4, sort_keys=True)
    def publish(self, token, room_data, current=None):
        '''Publica una room en la BD'''
        self._rooms_=glob.glob(ROOMS_DIRECTORY)
        room_data_={}
        room_data_=json.loads(room_data)
        owner=self.proxy_auth_server.getOwner(token)
        if owner is not None:
            try:
                if room_data_["room"] is None or room_data_["data"] is None:
                    raise IceGauntlet.WrongRoomFormat()
                else:
                    if self.__comprobar_nombre_distinto__(room_data_, self._rooms_):
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
                            os.remove(room)
                            print(room+" borrado")
                            self._publisher_.removedRoom(room_name)
                            break
                    archivos_comprobados+=1
            if archivos_comprobados==len(glob.glob(ROOMS_DIRECTORY)):
                raise IceGauntlet.RoomNotExists()
        else:
            raise IceGauntlet.Unauthorized()
    def getRoom(self, roomName, current=None):
        '''Metodo para obtener un mapa de otro servidor'''
        rooms=glob.glob(ROOMS_DIRECTORY)
        room_json={}
        data=""
        for room in rooms:
            if os.path.exists(room):
                with open(room,'r') as file_room:
                    room_json=json.load(file_room)
                    if room_json["room"]==roomName:
                        data=room_json
                        break
        return json.dumps(data)
    def hello(self, manager, managerId, current=None):
        '''Evento para la llegada de un nuevo servidor'''
        if managerId!=str(self._id_):
            SERVIDORES[managerId]=manager
            available_rooms = manager.availableRooms()
            rooms=glob.glob(ROOMS_DIRECTORY)
            self.__actualizar_rooms__(available_rooms, rooms, manager)
            time.sleep(random.randint(0,1))
            self._publisher_.announce(self._remote_reference_, str(self._id_))
    def announce(self, manager, managerId, current=None):
        '''Evento para la respuesta a hello'''
        if managerId!=str(self._id_):
            if managerId not in SERVIDORES:
                available_rooms = manager.availableRooms()
                rooms=glob.glob(ROOMS_DIRECTORY)
                self.__actualizar_rooms__(available_rooms, rooms, manager)
            SERVIDORES[managerId]=manager
    def newRoom(self, roomName, managerId, current=None):
        '''Evento para avisar de la llegada de un nuevo mapa'''
        mapa_existente=0
        if managerId!=self._id_:
            rooms=glob.glob(ROOMS_DIRECTORY)
            for room in rooms:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        if room_json["room"]==roomName:
                            mapa_existente=1
                            break
            if mapa_existente==0:
                remote_reference=SERVIDORES[managerId]
                data=""
                data=remote_reference.getRoom(roomName)
                nombre_aleatorio=self.__elegir_nombre__()
                with open("rooms/"+nombre_aleatorio+".json", 'w') as contents:
                    json.dump(json.loads(data), contents, indent=4, sort_keys=True)
    def removedRoom(self, roomName, current=None):
        '''Evento para avisar de la eliminacion de un mapa'''
        rooms=glob.glob(ROOMS_DIRECTORY)
        room_json={}
        for room in rooms:
            if os.path.exists(room):
                with open(room,'r') as file_room:
                    room_json=json.load(file_room)
                    if room_json["room"]==roomName:
                        os.remove(room)
    def availableRooms(self, current=None):
        '''Devuelve los mapas disponibles de un servidor'''
        _available_rooms_ = []
        rooms=glob.glob(ROOMS_DIRECTORY)
        if rooms is not None:
            for room in rooms:
                if os.path.exists(room):
                    with open(room,'r') as file_room:
                        room_json=json.load(file_room)
                        _available_rooms_.append(room_json["room"])
        return _available_rooms_

class Server(Ice.Application):
    '''Servidor que contiene los sirvientes'''
    def get_topic_manager(self):
        '''Obtiene el topic manager'''
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    def run(self, argv):
        broker = self.communicator()
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2
        topic_name = "RoomManagerSyncChannel"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print("no such topic found, creating")
            topic = topic_mgr.create(topic_name)

        adapter = broker.createObjectAdapter("Dungeon_Adapter")
        dung_area_adapter=broker.createObjectAdapter("Dungeon_Area_Adapter")
        adapter.activate()
        dung_area_adapter.activate()
        servant = JuegoI(topic_mgr, adapter, dung_area_adapter, broker)

        auth_server = self.communicator().stringToProxy("default_1")
        proxy_auth_server = IceGauntlet.AuthenticationPrx.checkedCast(auth_server)

        if not proxy_auth_server:
            raise RuntimeError('Invalid proxy')

        GestionMapasI(proxy_auth_server,broker, topic)

        proxy_juego=adapter.add(servant, broker.stringToIdentity("juego"))

        print("Proxy juego:")
        print(proxy_juego, flush=True)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

server = Server()
sys.exit(server.main(sys.argv))
