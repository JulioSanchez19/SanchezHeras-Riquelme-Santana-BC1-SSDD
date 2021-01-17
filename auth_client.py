#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Cliente de autenticacion
'''

import sys
import hashlib
import getpass

import Ice
Ice.loadSlice('icegauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet

class ClienteAutenticacion(Ice.Application):
    '''Clase del cliente de autenticacion'''
    def run(self, argv):

        if len(argv)!=4:
            print("usage: auth_client.py <-g/-p> <user> <proxy> ")

        proxy = self.communicator().stringToProxy(argv[3])
        auth = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not auth:
            raise RuntimeError('Invalid proxy')

        user=argv[2]
        return_code=0

        print(auth.getOwner('g8tujeuHVr6C3GTMPNDVXjDY137L6EgePsEK5W7Q'))

        if argv[1]=="-g":
            return_code=self.conseguir_token(user, auth)
        elif argv[1]=="-c":
            return_code=self.cambiar_password(user, auth)
        else:
            print("Opciones -g -c")

        return return_code

    def calcular_hash(self,password):
        '''Calcula el hash del password'''
        return hashlib.sha256(password.encode()).hexdigest()

    def conseguir_token(self,user, auth):
        '''Consigue un nuevo token'''
        token=""
        password=getpass.getpass(prompt="Enter password:")
        password_hash=self.calcular_hash(password)
        try:
            token=auth.getNewToken(user, password_hash)
            print("token: "+token)
            return 0
        except IceGauntlet.Unauthorized:
            print("Usuario y/o contraseña no valida")
            return -1

    def cambiar_password(self, user,auth):
        '''Cambia contrasenia de usuario'''
        current_password=getpass.getpass(prompt="Enter current password:")
        if(current_password == ""):
            new_password_hash=self.calcular_hash(getpass.getpass(prompt="Enter new password:"))
            try:
                auth.changePassword(user,None, new_password_hash)
                return 0
            except IceGauntlet.Unauthorized:
                print("Usuario y/o contraseña no valida")
                return -1
        else:
            current_password_hash=self.calcular_hash(current_password)
            new_password_hash=self.calcular_hash(getpass.getpass(prompt="Enter new password:"))
            try:
                auth.changePassword(user,current_password_hash, new_password_hash)
                return 0
            except IceGauntlet.Unauthorized:
                print("Usuario y/o contraseña no valida")
                return -1

sys.exit(ClienteAutenticacion().main(sys.argv))
