# Copyright (c) 2016 Cable Television Laboratories, Inc. ("CableLabs")
#                    and others.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os

import file_utils
from Crypto.PublicKey import RSA

import openstack.nova_utils as nova_utils
from openstack.tests.os_source_file_test import OSSourceFileTestsCase

__author__ = 'spisarski'

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('nova_utils_tests')

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# To run these tests, the CWD must be set to the top level directory of this project
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

priv_key_file_path = 'tmp/nova_utils_tests'
pub_key_file_path = priv_key_file_path + '.pub'

test_conf = file_utils.read_yaml('openstack/tests/conf/os_env.yaml')

if test_conf.get('ext_net'):
    ext_net_name = test_conf['ext_net']
else:
    ext_net_name = 'external'


class NovaUtilsKeypairTests(OSSourceFileTestsCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        self.nova = nova_utils.nova_client(self.os_creds)
        self.keys = RSA.generate(1024)
        self.public_key = self.keys.publickey().exportKey('OpenSSH')
        self.keypair_name = 'testKP'
        self.keypair = None
        self.floating_ip = None

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        if self.keypair:
            try:
                nova_utils.delete_keypair(self.nova, self.keypair)
            except:
                pass

        try:
            os.remove(priv_key_file_path)
        except:
            pass

        try:
            os.remove(pub_key_file_path)
        except:
            pass

        if self.floating_ip:
            nova_utils.delete_floating_ip(self.nova, self.floating_ip)

    def test_create_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name, self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEquals(self.keypair, result)
        keypairs = nova_utils.get_keypairs(self.nova)
        for kp in keypairs:
            if kp.id == self.keypair.id:
                return
        self.fail('Keypair not found')

    def test_create_delete_keypair(self):
        """
        Tests the creation of an OpenStack keypair that does not exist.
        """
        self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_name, self.public_key)
        result = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertEquals(self.keypair, result)
        nova_utils.delete_keypair(self.nova, self.keypair)
        result2 = nova_utils.keypair_exists(self.nova, self.keypair)
        self.assertIsNone(result2)

    def test_create_key_from_file(self):
        """
        Tests that the generated RSA keys are properly saved to files
        :return:
        """
        nova_utils.save_keys_to_files(self.keys, pub_key_file_path, priv_key_file_path)
        self.keypair = nova_utils.upload_keypair_file(self.nova, self.keypair_name, pub_key_file_path)
        pub_key = open(os.path.expanduser(pub_key_file_path)).read()
        self.assertEquals(self.keypair.public_key, pub_key)

    def test_floating_ips(self):
        """
        Tests the creation of a floating IP
        :return:
        """
        ips = nova_utils.get_floating_ips(self.nova)
        self.assertIsNotNone(ips)

        self.floating_ip = nova_utils.create_floating_ip(self.nova, ext_net_name)
        returned = nova_utils.get_floating_ip(self.nova, self.floating_ip)
        self.assertEquals(self.floating_ip, returned)
