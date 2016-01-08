import unittest
import openstack.create_network as create_network
import neutron_utils_tests
import logging
import openstack_tests

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)

os_creds = openstack_tests.get_credentials()

net_name = 'test-priv-net'
network_settings = create_network.NetworkSettings(name=net_name)
subnet_name = 'test-priv-subnet'
subnet_cidr = '10.0.1.0/24'
router_name = 'test-router'
router_settings = create_network.RouterSettings(name=router_name)


class CreateNetworkSuccessTests(unittest.TestCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        self.net_creator = create_network.OpenStackNetwork(os_creds, network_settings,
                                                           create_network.SubnetSettings(cidr=subnet_cidr,
                                                                                         name=subnet_name),
                                                           router_settings)

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
