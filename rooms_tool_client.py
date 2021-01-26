#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W0201

'''
Cliente para la gestion de los mapas
'''

import sys
import json
import os
import Ice
Ice.loadSlice('icegauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet

class RoomsToolClient(Ice.Application):
    '''Clase para la gestion de los mapas'''
    def run(self, argv):
        if len(argv)!=5:
            print("usage: roomsToolClient.py <-p/-r> <proxy> <token> <roomName/roomData>")

        room_manager = self.communicator().stringToProxy(argv[2])
        proxy_room_manager = IceGauntlet.RoomManagerPrx.checkedCast(room_manager)

        if not proxy_room_manager:
            raise RuntimeError('Invalid proxy')

        return_code=0

        if argv[1]=="-p":
            return_code=self.upload_map(proxy_room_manager,argv)
        elif argv[1]=="-r":
            return_code=self.delete_map(proxy_room_manager,argv)
        else:
            print("Opciones: -p -r")

        return return_code

    def upload_map(self,proxy_room_manager,argv):
        '''Sube un mapa'''
        token=argv[3]
        room_data_={}
        if os.path.exists(argv[4]):
                with open(argv[4],'r') as rooms:
                    room_data_=json.load(rooms)
        try:
            proxy_room_manager.publish(token, json.dumps(room_data_))
            return 0
        except IceGauntlet.RoomAlreadyExists:
            print("La room que desea guardar ya existe")
            return -1
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
            return -1
        except IceGauntlet.WrongRoomFormat:
            print("Formato de la room incorrecto")
            return -1

    def delete_map(self,proxy_room_manager,argv):
        '''Borra un mapa'''
        token=argv[3]
        try:
            proxy_room_manager.remove(token, argv[4])
            print("Room eliminada con exito")
            return 0
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
            return -1
        except IceGauntlet.RoomNotExists:
            print("La room no existe")
            return -1

sys.exit(RoomsToolClient().main(sys.argv))
