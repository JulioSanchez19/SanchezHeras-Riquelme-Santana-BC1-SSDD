#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import json
import Ice
import os 
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet

ROOMS_FILE='tutorial.json'

class JuegoI(IceGauntlet.Dungeon):
    def __init__(self):
        self._rooms_={}
        if os.path.exists(ROOMS_FILE):
            with open(ROOMS_FILE,'r') as rooms:
                self._rooms_=json.load(rooms)

    def getRoom(self, current=None):
        if self._rooms_:
            print(self._rooms_['data'])
            return self._rooms_['data']
        else:
            raise IceGauntlet.RoomNotExists()

class GestionMapasI(IceGauntlet.Dungeon):

    def publish(self,token, roomData, current=None):

    def remove(self,token, roomName, current=None):

class Server(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        servant = JuegoI()
        #servant2 = GestionMapasI()

        adapter = broker.createObjectAdapter("ServerAdapter")
        proxy=adapter.add(servant, broker.stringToIdentity("juego"))
        #proxy2=adapter.add(servant2,broker.stringToIdentity("gestionMapas"))
        #proxy=adapter.addWithUUID(servant)


        print(proxy, flush=True)
        #print(proxy2, flush=True)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))