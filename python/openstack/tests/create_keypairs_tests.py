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

from Crypto.PublicKey import RSA

import openstack.create_keypairs as create_keypairs
import openstack.nova_utils as nova_utils
from openstack.tests.os_source_file_test import OSSourceFileTestsCase

__author__ = 'spisarski'

logging.basicConfig(level=logging.DEBUG)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# To run these tests, the CWD must be set to the top level directory of this project
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

keypair_name = 'create_kp_tests'

pub_file_path = 'tmp/create_kp_tests.pub'
priv_file_path = 'tmp/create_kp_tests'


class CreateKeypairsTests(OSSourceFileTestsCase):
    """
    Tests for the OpenStackKeypair class
    """

    def setUp(self):
        self.keypair_creator = None

    def tearDown(self):
        """
        Cleanup of created keypair
        """
        if self.keypair_creator:
            self.keypair_creator.clean()

        try:
            os.remove(pub_file_path)
        except:
            pass

        try:
            os.remove(priv_file_path)
        except:
            pass

    def test_create_keypair_only(self):
        """
        Tests the creation of a generated keypair without saving to file
        :return:
        """
        self.keypair_creator = create_keypairs.OpenStackKeypair(self.os_creds,
                                                                create_keypairs.KeypairSettings(name=keypair_name))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.keypair_creator.nova, self.keypair_creator.keypair)
        self.assertEquals(self.keypair_creator.keypair, keypair)

    def test_create_keypair_save_pub_only(self):
        """
        Tests the creation of a generated keypair and saves the public key only
        :return:
        """
        self.keypair_creator = create_keypairs.OpenStackKeypair(self.os_creds,
                                                                create_keypairs.KeypairSettings(name=keypair_name,
                                                                                        public_filepath=pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.keypair_creator.nova, self.keypair_creator.keypair)
        self.assertEquals(self.keypair_creator.keypair, keypair)

        file_key = open(os.path.expanduser(pub_file_path)).read()
        self.assertEquals(self.keypair_creator.keypair.public_key, file_key)

    def test_create_keypair_save_both(self):
        """
        Tests the creation of a generated keypair and saves both private and public key files[
        :return:
        """
        self.keypair_creator = create_keypairs.OpenStackKeypair(self.os_creds,
                                                                create_keypairs.KeypairSettings(name=keypair_name,
                                                                                    public_filepath=pub_file_path,
                                                                                    private_filepath=priv_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.keypair_creator.nova, self.keypair_creator.keypair)
        self.assertEquals(self.keypair_creator.keypair, keypair)

        file_key = open(os.path.expanduser(pub_file_path)).read()
        self.assertEquals(self.keypair_creator.keypair.public_key, file_key)

        self.assertTrue(os.path.isfile(priv_file_path))

    def test_create_keypair_from_file(self):
        """
        Tests the creation of an existing public keypair from a file
        :return:
        """
        keys = RSA.generate(1024)
        nova_utils.save_keys_to_files(keys=keys, pub_file_path=pub_file_path)
        self.keypair_creator = create_keypairs.OpenStackKeypair(self.os_creds,
                                                                create_keypairs.KeypairSettings(name=keypair_name,
                                                                                        public_filepath=pub_file_path))
        self.keypair_creator.create()

        keypair = nova_utils.keypair_exists(self.keypair_creator.nova, self.keypair_creator.keypair)
        self.assertEquals(self.keypair_creator.keypair, keypair)

        file_key = open(os.path.expanduser(pub_file_path)).read()
        self.assertEquals(self.keypair_creator.keypair.public_key, file_key)
