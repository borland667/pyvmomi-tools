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
import os
import shutil
import unittest
import sys
from pyvmomi_tools.extensions.credstore import VICredStore, NoCredentialsFileFound, HostNotFoundException, PasswordEntry
from sys import platform as _platform
try:
    # Python 3.x compatibility workaround
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

__author__ = 'Osvaldo Demo'


class VICredStoreTests(unittest.TestCase):

    def _create_credentialsfile(self, file):
        target = open(file, 'w')
        target.write('<?xml version="1.0" encoding="UTF-8"?>')
        target.write("\n")
        target.write('  <viCredentials>')
        target.write("\n")
        target.write('  <version>1.0</version>')
        target.write("\n")
        target.write('  <passwordEntry>')
        target.write("\n")
        target.write('    <host>mytesthost</host>')
        target.write("\n")
        target.write('    <username>testuser</username>')
        target.write("\n")
        target.write('    <password>NyYwNzMiMDA0LDEnQwY6EwoWFHsINgUwdCV1cg1wDyUtJBssG3cicRE7MQcVKxp1FhsOHBMrdSASNwoJCXM2cjUaOy0JJXsIFXN2EgAsKzUmeiU6EzIvcisrBAEIdg87IQs7JRI3DRwQMRsAMwIGJw8CAXQuDjslJRERKnEmB0M=</password>')
        target.write("\n")
        target.write('  </passwordEntry>')
        target.write("\n")
        target.write('</viCredentials>')
        target.write("\n")
        target.close()

    def setUp(self):
        self.test_path = "mycredentials.xml"
        self._create_credentialsfile(self.test_path)
        self.path = None

        if _platform == "linux" or _platform == "linux2":
            self.path = os.environ['HOME'] + VICredStore.FILE_PATH_UNIX
        elif _platform == "win32":
            self.path = os.environ['APPDATA'] + VICredStore.FILE_PATH_WIN

        if self.path is not None:
            if os.path.exists(self.path):
                shutil.copy(self.path,self.path+'.bak')
                shutil.copy(self.test_path,self.path)
            else:
                if not os.path.exists(os.path.dirname(self.path)):
                    os.makedirs(os.path.dirname(self.path))
                    shutil.copy(self.test_path,self.path)

    def tearDown(self):
        os.remove('mycredentials.xml')
        if self.path is not None:
            if os.path.exists(self.path+'.bak'):
                shutil.copy(self.path+'.bak',self.path)
                os.remove(self.path+'.bak')
            else:
                shutil.rmtree(os.path.dirname(self.path))



    def test_get_userpwd(self):
        os.environ['VI_CREDSTORE'] = self.test_path
        store = VICredStore(os.environ['VI_CREDSTORE'])
        self.assertEqual(store.get_userpwd('mytesthost'),('testuser','testpassword'))

    def test_get_userpwd_2(self):
        store = VICredStore()
        self.assertEqual(store.get_userpwd('mytesthost'),('testuser','testpassword'))

    def test_get_userpwd_3(self):
        os.environ.pop('VI_CREDSTORE',None)
        if self.path is not None:
            if not os.path.exists(os.path.dirname(self.path)):
                os.makedirs(os.path.dirname(self.path))
                self._create_credentialsfile(self.path)

            store = VICredStore()
            self.assertEqual(store.get_userpwd('mytesthost'),('testuser','testpassword'))

    def test_VICredStore_NoCredentialsFileFound(self):
        self.assertRaises(NoCredentialsFileFound,VICredStore,'anyfile.xml')

    def test_get_userpwd_HostNotFoundException(self):
        os.environ['VI_CREDSTORE'] = self.test_path
        store = VICredStore(os.environ['VI_CREDSTORE'])
        self.assertRaises(HostNotFoundException,store.get_userpwd,'notexistanthost')

    def test_get_pwd_entry_list(self):
        os.environ['VI_CREDSTORE'] = self.test_path
        store = VICredStore(os.environ['VI_CREDSTORE'])
        pwdentry = PasswordEntry('mytesthost','testuser','NyYwNzMiMDA0LDEnQwY6EwoWFHsINgUwdCV1cg1wDyUtJBssG3cicRE7MQcVKxp1FhsOHBMrdSASNwoJCXM2cjUaOy0JJXsIFXN2EgAsKzUmeiU6EzIvcisrBAEIdg87IQs7JRI3DRwQMRsAMwIGJw8CAXQuDjslJRERKnEmB0M=')
        pwdlist = store._get_pwd_entry_list()
        self.assertEqual(len(pwdlist),1)
        self.assertEqual(pwdentry,pwdlist[0])

    def test_list_entries(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        os.environ['VI_CREDSTORE'] = self.test_path
        store = VICredStore(os.environ['VI_CREDSTORE'])
        store.list_entries()
        self.assertEqual(sys.stdout.getvalue(),'mytesthost\n')
        sys.stdout = self.held
