#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W1203

import sys
import os
import atexit
import logging
import argparse
import hashlib
import getpass

import Ice
Ice.loadSlice('icegauntlet.ice')
import IceGauntlet

class clienteAutenticacion(Ice.Application):
    def run(self, argv):
        
        if len(argv)!=4:
            print("usage: auth_client.py <-g/-p> <user> <proxy> ")

        proxy = self.communicator().stringToProxy(argv[3])
        auth = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not auth:
            raise RuntimeError('Invalid proxy')

        self.user=argv[2]

        if argv[1]=="-g":
            self.conseguirToken(self.user, auth)
        elif argv[1]=="-c":
            self.cambiarPassword(self.user, auth)
        else:
            print("Opciones -g -c")
        
        return 0

    def calcularHash(self,password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def conseguirToken(self,user, auth):#python3 auth_client.py -t proxy usuario
        token=""
        password=getpass.getpass(prompt="Enter password:")
        passwordHash=self.calcularHash(password)
        try:
            token=auth.getNewToken(user, passwordHash)
        except IceGauntlet.Unauthorized:
            print("Usuario y/o contraseña no valida")
            os._exit(-1)
        with open("token.txt", 'w') as tokenTxt:#se escribe el nuevo token en el archivo token.txt para futuras operaciones
            tokenTxt.write(token)
    
    def cambiarPassword(self, user,auth):
        currentPassword=getpass.getpass(prompt="Enter current password:")
        if(currentPassword == ""):
            newPasswordHash=self.calcularHash(getpass.getpass(prompt="Enter new password:"))
            try:
                auth.changePassword(user,None, newPasswordHash)
            except IceGauntlet.Unauthorized:
                print("Usuario y/o contraseña no valida")
                os._exit(-1)
            
        else:
            currentPasswordHash=self.calcularHash(currentPassword)
            newPasswordHash=self.calcularHash(getpass.getpass(prompt="Enter new password:"))
            try:
                auth.changePassword(user,currentPasswordHash, newPasswordHash)
            except IceGauntlet.Unauthorized:
                print("Usuario y/o contraseña no valida")
                os._exit(-1)
            
sys.exit(clienteAutenticacion().main(sys.argv))