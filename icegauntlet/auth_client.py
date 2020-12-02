#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W1203

import sys
import atexit
import logging
import argparse
import hashlib

import Ice
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet

class clienteAutenticacion(Ice.Application):
    def run(self, argv):
        proxy = self.communicator().stringToProxy(argv[2])
        auth = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not auth:
            raise RuntimeError('Invalid proxy')
        print(argv[1])
        if argv[1]=="1":
            self.conseguirToken(argv, auth)
        elif argv[1]=="2":
            self.cambiarPassword(argv, auth)
        else:
            print("Que quieres hacer")
        

        return 0

    def calcularHash(self,password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def conseguirToken(self,argv, auth):
        passwordHash=self.calcularHash(argv[4])
        print(passwordHash)
        token=auth.getNewToken(argv[3], passwordHash)
        print(token)
    
    def cambiarPassword(self, argv,auth):
        passwordHash=self.calcularHash(argv[4])
        newPasswordHash=self.calcularHash(argv[5])
        auth.changePassword(argv[3],passwordHash, newPasswordHash)

sys.exit(clienteAutenticacion().main(sys.argv))