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

import neutron_utils_tests
import openstack.create_network as create_network
import openstack_tests
from openstack.tests.os_source_file_test import OSSourceFileTestsCase

__author__ = 'spisarski'

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)

net_config = openstack_tests.get_pub_net_config()


class CreateNetworkSuccessTests(OSSourceFileTestsCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        self.net_creator = create_network.OpenStackNetwork(self.os_creds, net_config.network_settings,
                                                           net_config.subnet_settings,
                                                           net_config.router_settings)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        self.net_creator.clean()

        if self.net_creator.subnet:
            # Validate subnet has been deleted
            neutron_utils_tests.validate_subnet(self.net_creator.neutron, self.net_creator.subnet_settings.name,
                                                self.net_creator.subnet_settings.cidr, False)

        if self.net_creator.network:
            # Validate network has been deleted
            neutron_utils_tests.validate_network(self.net_creator.neutron, self.net_creator.network_settings.name,
                                                 False)

    def test_create_network(self):
        """
        Tests the creation of an OpenStack network.
        """
        # Create Image
        self.net_creator.create()

        # Validate network was created
        neutron_utils_tests.validate_network(self.net_creator.neutron, self.net_creator.network_settings.name, True)

        # Validate subnets
        neutron_utils_tests.validate_subnet(self.net_creator.neutron, self.net_creator.subnet_settings.name,
                                            self.net_creator.subnet_settings.cidr, True)

        # Validate routers
        neutron_utils_tests.validate_router(self.net_creator.neutron, self.net_creator.router_settings.name, True)

        # Validate interface routers
        neutron_utils_tests.validate_interface_router(self.net_creator.interface_router, self.net_creator.router,
                                                      self.net_creator.subnet)

        # TODO - Expand tests especially negative ones.
