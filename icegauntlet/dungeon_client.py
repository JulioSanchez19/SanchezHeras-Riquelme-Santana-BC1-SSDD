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

class RemoteDungeonMap(Ice.Application):
    def run(self, argv):
        print(argv[1])
        proxy = self.communicator().stringToProxy(argv[1])
        self.dung = IceGauntlet.DungeonPrx.checkedCast(proxy)
        if not self.dung:
            raise RuntimeError('Invalid proxy')
        return self.next_room()
    def next_room(self):
        return self.dung.getRoom()


def main(argv):
    game.pyxeltools.initialize()
    dungeon=RemoteDungeonMap().main(argv)
    gauntlet = game.Game(game.common.HEROES[0], dungeon)
    gauntlet.add_state(game.screens.TileScreen, game.common.INITIAL_SCREEN)
    gauntlet.add_state(game.screens.StatsScreen, game.common.STATUS_SCREEN)
    gauntlet.add_state(game.screens.GameScreen, game.common.GAME_SCREEN)
    gauntlet.add_state(game.screens.GameOverScreen, game.common.GAME_OVER_SCREEN)
    gauntlet.add_state(game.screens.GoodEndScreen, game.common.GOOD_END_SCREEN)
    gauntlet.start()

    return EXIT_OK


if __name__ == '__main__':
    sys.exit(main(sys.argv))