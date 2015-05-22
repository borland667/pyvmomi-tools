# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Minimal functionality to read and use passwords from vSphere Credential Store XML file
'''

from __future__ import print_function

__author__ = 'Osvaldo Demo'

import base64
import xml.etree.ElementTree as Et
from sys import platform as _platform
import os
import os.path


class PasswordEntry(object):
    """
    Abstraction object that translates from obfuscated password to usable password text
    """

    def __init__(self, host=None, username=None, password=None):
        self.__host = host
        self.__username = username
        self.__password = password

    def __str__(self):
        return '{ Host: ' + self.__host + ' User: ' + self.__username + ' Pwd: ' + self.__password + ' }'

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__host) + hash(self.__username) + hash(self.__password)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        else:
            return False

    @staticmethod
    def _compute_hash(text):
        """
        Generates a hash based on the following formula:

        hash = s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]

        :param text: String
        :return: Computed hash value
        :rtype: int
        """

        boundary = 0x7FFFFFFF
        negative = 0x80000000
        hash_value = 0
        for my_char in text:
            hash_value = hash_value * 31 + ord(my_char)

            if hash_value & negative:
                hash_value |= ~boundary
            else:
                hash_value &= boundary

        return hash_value

    def _deobfuscate(self):
        """
        Convert the obfuscated string to the actual password in clear text

        Functionality taken from the perl module VICredStore.pm since the goal was to emulate its behaviour.

        """

        hashmod = 256
        password = base64.b64decode(self.__password).decode('UTF-8')
        hash_value = self._compute_hash(self.__host + self.__username) % hashmod
        crypt = chr(hash_value & 0xFF) * len(password)
        password_final = []
        for n in range(0, len(password)):
            password_final.append(ord(password[n]) ^ ord(crypt[n]))
        decrypted_pwd = ''
        for ci in password_final:
            if ci == 0:
                break
            decrypted_pwd += chr(ci)

        return decrypted_pwd

    def get_pwd(self):
        return self._deobfuscate()

    def get_user(self):
        return self.__username

    def get_host(self):
        return self.__host


class HostNotFoundException(Exception):
    """
    Exception raised when the host/server was not found in the credentials file.
    """
    pass


class NoCredentialsFileFound(Exception):
    """
    Exception raised when the credentials xml file was not found.
    """
    pass


class VICredStore(object):
    """
    Helper class that mimicks VICredStore perl module.

    Functionality implemented to decode the existing credentials file only.
    """

    __hostdata = {}
    FILE_PATH_UNIX = '/.vmware/credstore/vicredentials.xml'
    FILE_PATH_WIN = '/VMware/credstore/vicredentials.xml'

    def __init__(self, path=None):
        if path is None:
            try:
                if os.environ['VI_CREDSTORE'] is not None:
                    self.__path = os.environ['VI_CREDSTORE']
            except KeyError:

                if _platform == "linux" or _platform == "linux2":
                    self.__path = os.environ['HOME'] + self.FILE_PATH_UNIX
                elif _platform == "win32":
                    self.__path = os.environ['APPDATA'] + self.FILE_PATH_WIN
                else:
                    raise Exception('Unsupported platform! (' + _platform + ')')
        else:
            self.__path = path

        if os.path.exists(self.__path):
            self.__tree = Et.parse(self.__path)
            self.__root = self.__tree.getroot()
            self.__hostdata = self.__populate_data()
        else:
            self.__root = None
            self.__tree = None
            raise NoCredentialsFileFound('Credential filename [' + self.__path + '] doesn\'t exist!')


    def get_userpwd(self, hostname):

        try:
            entry = self.__hostdata[hostname]
        except KeyError:
            raise HostNotFoundException("Host " + hostname + " does not exist in the credential store!")

        return entry.get_user(), entry.get_pwd()

    def _get_pwd_entry_list(self):

        tmp_list = []
        for entry in self.__root:
            if entry.tag == "passwordEntry":
                tmp_list.append(entry)

        pwdentries = []
        for entry in tmp_list:
            host = None
            user = None
            pwd = None
            for child in entry:
                if child.tag == "host":
                    host = child.text
                if child.tag == "username":
                    user = child.text
                if child.tag == "password":
                    pwd = child.text

            if host is not None and user is not None and pwd is not None:
                pwdentries.append(PasswordEntry(host, user, pwd))

        return pwdentries

    def list_entries(self):
        for entry in sorted(self.__hostdata.keys()):
            print(entry)

    def __populate_data(self):
        pwd_list = self._get_pwd_entry_list()
        new_hostdata = {}
        for entry in pwd_list:
            new_hostdata[entry.get_host()] = entry

        return new_hostdata
