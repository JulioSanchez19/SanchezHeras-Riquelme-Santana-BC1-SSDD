#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Cliente para la gestion de los mapas
'''

import sys
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

        if argv[1]=="-p":
            self.upload_map(proxy_room_manager,argv)
        elif argv[1]=="-r":
            self.delete_map(proxy_room_manager,argv)
        else:
            print("Opciones: -p -r")

    def upload_map(self,proxy_room_manager,argv):
        '''Sube un mapa'''
        token=argv[3]
        try:
            proxy_room_manager.publish(token, argv[4])
        except IceGauntlet.RoomAlreadyExists:
            print("La room que desea guardar ya existe")
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
        except IceGauntlet.WrongRoomFormat:
            print("Formato de la room incorrecto")

    def delete_map(self,proxy_room_manager,argv):
        '''Borra un mapa'''
        token=argv[3]
        try:
            proxy_room_manager.remove(token, argv[4])
        except IceGauntlet.Unauthorized:
            print("Acceso no autorizado")
        except IceGauntlet.RoomNotExists:
            print("La room no existe")

sys.exit(RoomsToolClient().main(sys.argv))
