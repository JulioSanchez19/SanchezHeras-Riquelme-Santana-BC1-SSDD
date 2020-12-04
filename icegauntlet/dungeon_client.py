#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W1203

import sys
import atexit
import logging
import argparse

import Ice
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet

import game
import game.common
import game.screens
import game.pyxeltools
import game.orchestration

class RemoteDungeonMap():
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
    

class clientGame(Ice.Application):
    def run(self,argv):
        self.proxy = self.communicator().stringToProxy(argv[1])
        self.dung = IceGauntlet.DungeonPrx.checkedCast(self.proxy)
        if not self.dung:
            raise RuntimeError('Invalid proxy')
        dungeon=RemoteDungeonMap(self.dung)
        while dungeon.finished==False:
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
    sys.exit(clientGame().main(sys.argv))