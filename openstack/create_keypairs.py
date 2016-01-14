import logging
import nova_utils
import os
from Crypto.PublicKey import RSA

logger = logging.getLogger('OpenStackKeypair')


class OpenStackKeypair:
    """
    Class responsible for creating a network in OpenStack

    All tasks have been designed after the vPing scenario in the OPNFV functest repository. We will want to make
    this class more flexible, expand it beyond the private network. Additionally, many of the private methods here
    should probably make their way into a file named something like neutron_utils.py.
    """

    def __init__(self, os_creds, keypair_settings):
        """
        Constructor - all parameters are required
        :param os_creds: The credentials to connect with OpenStack
        :param keypair_settings: The settings used to create a keypair
        """
        self.os_creds = os_creds
        self.keypair_settings = keypair_settings
        self.nova = nova_utils.nova_client(os_creds)

        # Attributes instantiated on create()
        self.keypair = None

    def create(self):
        """
        Responsible for creating not only the network but then a private subnet, router, and an interface to the router.
        """
        logger.info('Creating keypair %s...' % self.keypair_settings.name)

        keypair_insts = nova_utils.get_keypairs(self.nova)
        found = False
        for keypair_inst in keypair_insts:
            if keypair_inst.name == self.keypair_settings.name:
                self.keypair = keypair_inst
                found = True

        if not found:
            if self.keypair_settings.public_filepath:
                if os.path.isfile(self.keypair_settings.public_filepath):
                    self.keypair = nova_utils.upload_keypair_file(self.nova, self.keypair_settings.name,
                                                                  self.keypair_settings.public_filepath)
                else:
                    # TODO - Make this value configurable
                    keys = RSA.generate(1024)
                    self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_settings.name,
                                                             keys.publickey().exportKey('OpenSSH'))
                    nova_utils.save_keys_to_files(keys, self.keypair_settings.public_filepath,
                                                  self.keypair_settings.private_filepath)
            else:
                # TODO - Make this value configurable
                keys = RSA.generate(1024)
                self.keypair = nova_utils.upload_keypair(self.nova, self.keypair_settings.name,
                                                         keys.publickey().exportKey('OpenSSH'))

    def clean(self):
        """
        Removes and deletes the keypair.
        """
        if self.keypair:
            nova_utils.delete_keypair(self.nova, self.keypair)


class KeypairSettings:
    """
    Class representing a network configuration
    """

    def __init__(self, config=None, name=None, public_filepath=None, private_filepath=None):
        """
        Constructor - all parameters are optional
        :param config: Should be a dict object containing the configuration settings using the attribute names below
                       as each member's the key and overrides any of the other parameters.
        :param name: The keypair name.
        :param public_filepath: The path to/from the filesystem where the public key file is or will be stored
        :param private_filepath: The path where the generated private key file will be stored
        :return:
        """

        if config:
            self.name = config.get('name')
            self.public_filepath = config.get('public_filepath')
            self.private_filepath = config.get('private_filepath')
        else:
            self.name = name
            self.public_filepath = public_filepath
            self.private_filepath = private_filepath