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
import os

import file_utils

from openstack import create_network
from openstack import os_credentials

__author__ = 'spisarski'


def get_credentials(os_env_file, proxy_settings):
    if proxy_settings:
        os.environ['HTTP_PROXY'] = proxy_settings

    if os_env_file:
        config = file_utils.read_os_env_file(os_env_file)
        return os_credentials.OSCreds(config['OS_USERNAME'], config['OS_PASSWORD'], config['OS_AUTH_URL'],
                                      config['OS_TENANT_NAME'], proxy_settings)
    else:
        config = file_utils.read_yaml('openstack/tests/conf/os_env.yaml')
        if config.get('http_proxy'):
            os.environ['HTTP_PROXY'] = config['http_proxy']
        return os_credentials.OSCreds(config['username'], config['password'], config['os_auth_url'],
                                      config['tenant_name'], config.get('http_proxy'))

    # TODO - Add ability to read environment variables here


def get_image_test_settings():
    return OSImageSettings('qcow2', 'http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img',
                           'test-image', '/tmp/create_image_tests', 'cirros')


def get_instance_image_settings():
    return OSImageSettings('qcow2', 'http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2',
                           'centos-inst-test', '/tmp/centos-inst-test', 'centos')


def get_priv_net_config():
    return OSNetworkConfig('test-priv-net', 'test-priv-subnet', '10.55.0.0/24', 'test-priv')


def get_pub_net_config():
    return OSNetworkConfig('test-pub-net', 'test-pub-subnet', '10.55.1.0/24', 'test-pub',
                           external_gateway='external')


class OSImageSettings:
    """
    Represents the settings required for creating an image in OpenStack
    """
    def __init__(self, img_format, url, name, download_file_path, image_user):
        self.format = img_format
        self.url = url
        self.name = name
        self.download_file_path = download_file_path
        self.image_user = image_user


class OSNetworkConfig:
    """
    Represents the settings required for the creation of a network in OpenStack
    """
    def __init__(self, net_name, subnet_name, subnet_cidr, router_name, external_gateway=None):
        self.net_name = net_name
        self.network_settings = create_network.NetworkSettings(name=self.net_name)
        self.subnet_name = subnet_name
        self.subnet_cidr = subnet_cidr
        self.router_name = router_name
        self.router_settings = create_network.RouterSettings(name=self.router_name, external_gateway=external_gateway)
        self.subnet_settings = create_network.SubnetSettings(cidr=subnet_cidr, name=subnet_name)
