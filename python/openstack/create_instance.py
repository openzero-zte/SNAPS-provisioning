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
import time

from novaclient.exceptions import NotFound
from provisioning import ansible_utils

import nova_utils
from openstack import neutron_utils

__author__ = 'spisarski'

logger = logging.getLogger('create_instance')

VM_BOOT_TIMEOUT = 1500
VM_DELETE_TIMEOUT = 600
SSH_TIMEOUT = 120
POLL_INTERVAL = 3
STATUS_ACTIVE = 'ACTIVE'
STATUS_DELETED = 'DELETED'


class OpenStackVmInstance:
    """
    Class responsible for creating a VM instance in OpenStack
    """

    def __init__(self, os_creds, name, flavor, image_creator, ports, remote_user, keypair_creator=None,
                 floating_ip_conf=None, userdata=None):
        """
        Constructor
        :param os_creds: The connection credentials to the OpenStack API
        :param name: The name of the OpenStack instance to be deployed
        :param flavor: The size of the VM to be deployed (i.e. 'm1.small')
        :param image_creator: The object responsible for creating the OpenStack image on which to deploy the VM
        :param ports: List of ports (NICs) to deploy to the VM
        :param remote_user: The sudo user
        :param keypair_creator: The object responsible for creating the keypair for this instance (Optional)
        :param floating_ip_conf: The configuration for the addition of a floating IP to an instance (Optional)
        :param userdata: The post installation script as a string or a file object (Optional)
        :raises Exception
        """
        self.os_creds = os_creds
        self.name = name
        self.image_creator = image_creator
        self.ports = ports
        self.remote_user = remote_user
        self.keypair_creator = keypair_creator
        self.floating_ip_conf = floating_ip_conf

        # TODO - need to potentially support multiple floating IPs
        self.floating_ip = None
        self.userdata = userdata
        self.vm = None
        self.nova = nova_utils.nova_client(os_creds)

        # Validate that the flavor is supported
        self.flavor = self.nova.flavors.find(name=flavor)
        if not self.flavor:
            raise Exception

    def create(self):
        """
        Creates a VM instance
        :return: The VM reference object
        """
        servers = self.nova.servers.list()
        for server in servers:
            if server.name == self.name:
                self.vm = server
                logger.info('Found existing machine with name - ' + self.name)
                fips = self.nova.floating_ips.list()
                for fip in fips:
                    if fip.instance_id == server.id:
                        self.floating_ip = fip
                return self.vm

        if not self.vm:
            nics = []
            for port in self.ports:
                kv = dict()
                kv['port-id'] = port['port']['id']
                nics.append(kv)

            logger.info('Creating VM with name - ' + self.name)
            keypair_name = None
            if self.keypair_creator:
                keypair_name = self.keypair_creator.keypair_settings.name

            self.vm = self.nova.servers.create(
                name=self.name,
                flavor=self.flavor,
                image=self.image_creator.image,
                nics=nics,
                key_name=keypair_name,
                userdata=self.userdata)

            logger.info('Created instance with name - ' + self.name)

            if self.floating_ip_conf:
                for port in self.ports:
                    if port['port']['name'] == self.floating_ip_conf['port_name']:
                        self.floating_ip = nova_utils.create_floating_ip(self.nova, self.floating_ip_conf['ext_net'])
                        logger.info('Created floating IP ' + self.floating_ip.ip)
                        self._add_floating_ip(port['port']['fixed_ips'][0]['ip_address'])

        return self.vm

    def clean(self):
        """
        Destroys the VM instance
        """
        if self.vm:
            try:
                self.nova.servers.delete(self.vm)
            except Exception as e:
                logger.error('Error deleting VM - ' + str(e))

            # Block until instance cannot be found or returns the status of DELETED
            if self.vm_deleted(block=True, timeout=VM_DELETE_TIMEOUT):
                logger.info('VM has been properly deleted')
            else:
                logger.error('VM not deleted within the timeout period of ' + str(VM_DELETE_TIMEOUT) + ' seconds')

        if self.floating_ip:
            try:
                nova_utils.delete_floating_ip(self.nova, self.floating_ip)
            except Exception as e:
                logger.error('Error deleting Floating IP - ' + e.message)

        neutron = neutron_utils.neutron_client(self.os_creds)
        for port in self.ports:
            neutron_utils.delete_port(neutron, port)

    def _add_floating_ip(self, port_ip, timeout=30, poll_interval=POLL_INTERVAL):
        """
        Returns True when active else False
        TODO - Make timeout and poll_interval configurable...
        """
        count = timeout / poll_interval
        while count > 0:
            logger.debug('Attempting to add floating IP to instance')
            try:
                self.vm.add_floating_ip(self.floating_ip, port_ip)
                logger.info('Added floating IP to port IP - ' + port_ip)
                return
            except Exception as e:
                logger.warn('Error adding floating IP to instance - ' + e.message)
                time.sleep(poll_interval)
                pass
        logger.error('Timeout attempting to add the floating IP to instance.')

    def config_rpm_nics(self):
        """
        Responsible for configuring NICs on RPM systems where the instance has more than one configured port
        :return: None
        """
        if len(self.ports) > 1 and self.vm_active(block=True) and self.vm_ssh_active(block=True):
            for port in self.ports:
                port_index = self.ports.index(port)
                if port_index > 0:
                    nic_name = 'eth' + repr(port_index)
                    self._config_rpm_nic(nic_name, port)
                    logger.info('Configured NIC - ' + nic_name)

    def _config_rpm_nic(self, nic_name, port):
        """
        Although ports/NICs can contain multiple IPs, this code currently only supports the first.

        Your CWD at this point must be the <repo dir>/python directory.
        TODO - fix this restriction.

        :param nic_name: Name of the interface
        :param port: The port information containing the expected IP values.
        """
        ip = port['port']['fixed_ips'][0]['ip_address']

        variables = {
            'floating_ip': self.floating_ip.ip,
            'nic_name': nic_name,
            'nic_ip': ip
        }

        ansible_utils.apply_playbook('provisioning/ansible/centos-network-setup/playbooks/configure_host.yml',
                                     [self.floating_ip.ip], self.remote_user,
                                     self.keypair_creator.keypair_settings.private_filepath, variables,
                                     self.os_creds.proxy)

    def vm_deleted(self, block=False, timeout=VM_DELETE_TIMEOUT, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM status returns the value of expected_status_code or instance retrieval throws
        a NotFound exception.
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        try:
            return self._vm_status_check(STATUS_DELETED, block, timeout, poll_interval)
        except NotFound as e:
            logger.info("Instance not found when querying status for " + STATUS_DELETED + ' with message ' + e.message)
            return True

    def vm_active(self, block=False, timeout=VM_BOOT_TIMEOUT, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM status returns the value of expected_status_code
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        return self._vm_status_check(STATUS_ACTIVE, block, timeout, poll_interval)

    def _vm_status_check(self, expected_status_code, block, timeout, poll_interval):
        """
        Returns true when the VM status returns the value of expected_status_code
        :param expected_status_code: instance status evaluated with this string value
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval in seconds
        :return: T/F
        """
        # sleep and wait for VM status change
        if block:
            start = time.time()
        else:
            start = time.time() - timeout

        while timeout > time.time() - start:
            status = self._status(expected_status_code)
            if status:
                logger.info('VM is active')
                return True

            logger.debug('Retry querying VM status in ' + str(poll_interval) + ' seconds')
            time.sleep(poll_interval)
            logger.debug('VM status query timeout in ' + str(timeout - (time.time() - start)))

        logger.error('Timeout checking for VM status for ' + expected_status_code)
        return False

    def _status(self, expected_status_code):
        """
        Returns True when active else False
        :param expected_status_code: instance status evaluated with this string value
        :return: T/F
        """
        instance = self.nova.servers.get(self.vm.id)
        if not instance:
            logger.warn('Cannot find instance with id - ' + self.vm.id)
            return False

        if instance.status == 'ERROR':
            raise Exception('Instance had an error during deployment')
        logger.debug('Instance status is - ' + instance.status)
        return instance.status == expected_status_code

    def vm_ssh_active(self, block=False, timeout=SSH_TIMEOUT, poll_interval=POLL_INTERVAL):
        """
        Returns true when the VM can be accessed via SSH
        :param block: When true, thread will block until active or timeout value in seconds has been exceeded (False)
        :param timeout: The timeout value
        :param poll_interval: The polling interval
        :return: T/F
        """
        # sleep and wait for VM status change
        logger.info('Checking if VM is active')

        if self.vm_active(block=True):
            if block:
                start = time.time()
            else:
                start = time.time() - timeout

            while timeout > time.time() - start:
                status = self._ssh_active()
                if status:
                    logger.info('SSH is active for VM instance')
                    return True

                logger.debug('Retry SSH connection in ' + str(poll_interval) + ' seconds')
                time.sleep(poll_interval)
                logger.debug('SSH connection timeout in ' + str(timeout - (time.time() - start)))

        logger.error('Timeout attempting to connect with VM via SSH')
        return False

    def _ssh_active(self):
        """
        Returns True when can create a SSH session else False
        :return: T/F
        """

        ssh = ansible_utils.ssh_client(self.floating_ip.ip, self.remote_user,
                                       self.keypair_creator.keypair_settings.private_filepath, self.os_creds.proxy)
        if ssh:
            return True
        return False
