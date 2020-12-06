#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Cliente del juego'''
import sys

import Ice
Ice.loadSlice('icegauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet

import game
import game.common
import game.screens
import game.pyxeltools
import game.orchestration

EXIT_OK=0

class RemoteDungeonMap():
    '''Servidor pide mapas remotos'''
    def __init__(self, prox):
        self.proxy=prox
    @property
    def next_room(self):
        try:
            return self.proxy.getRoom()
        except IceGauntlet.RoomNotExists:
            print("No hay mapas")
    @property
    def finished(self):
        return False

class ClientGame(Ice.Application):
    '''Clase que ejecuta el cliente de juego'''
    def run(self,argv):
        proxy = self.communicator().stringToProxy(argv[1])
        dung = IceGauntlet.DungeonPrx.checkedCast(proxy)
        if not dung:
            raise RuntimeError('Invalid proxy')
        dungeon=RemoteDungeonMap(dung)
        while not dungeon.finished:
            game.pyxeltools.initialize()
            gauntlet = game.Game(game.common.HEROES[0], dungeon)
            gauntlet.add_state(game.screens.TileScreen, game.common.INITIAL_SCREEN)
            gauntlet.add_state(game.screens.StatsScreen, game.common.STATUS_SCREEN)
            gauntlet.add_state(game.screens.GameScreen, game.common.GAME_SCREEN)
            gauntlet.add_state(game.screens.GameOverScreen, game.common.GAME_OVER_SCREEN)
            gauntlet.add_state(game.screens.GoodEndScreen, game.common.GOOD_END_SCREEN)
            gauntlet.start()
        return EXIT_OK

if __name__ == '__main__':
    sys.exit(ClientGame().main(sys.argv))
