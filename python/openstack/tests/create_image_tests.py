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

import openstack.create_image as create_image
import openstack_tests
from openstack import os_credentials
from openstack.tests.os_source_file_test import OSSourceFileTestsCase

__author__ = 'spisarski'

# Initialize Logging
logging.basicConfig(level=logging.DEBUG)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# To run these tests, the CWD must be set to the top level directory of this project
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

os_image_settings = openstack_tests.get_image_test_settings()


class CreateImageSuccessTests(OSSourceFileTestsCase):
    """
    Test for the CreateImage class defined in create_image.py
    """

    def setUp(self):
        """
        Instantiates the CreateImage object that is responsible for downloading and creating an OS image file
        within OpenStack
        """
        self.os_image = create_image.OpenStackImage(self.os_creds, os_image_settings.image_user,
                                                    os_image_settings.format, os_image_settings.url,
                                                    os_image_settings.name, os_image_settings.download_file_path)

    def tearDown(self):
        """
        Cleans the image and downloaded image file
        """
        self.os_image.clean()

    def testCreateImageClean(self):
        """
        Tests the creation of an OpenStack image when the download directory does not exist.
        """
        # Create Image
        created_image = self.os_image.create()
        glance = self.os_image.glance
        images = glance.images.list()

        # Validate
        for image in images:
            if image.name == self.os_image.image_name:
                self.assertEquals(created_image.id, image.id)
                self.assertEquals('active', image.status)
                return
        self.fail("Created image not found")

    def testCreateSameImage(self):
        """
        Tests the creation of an OpenStack image when the image already exists.
        """
        # Create Image
        image1 = self.os_image.create()
        # Should be retrieving the instance data
        os_image_2 = create_image.OpenStackImage(self.os_creds, os_image_settings.image_user, os_image_settings.format,
                                                 os_image_settings.url, os_image_settings.name,
                                                 os_image_settings.download_file_path)
        image2 = os_image_2.create()
        self.assertEquals(image1['id'], image2['id'])

    def testCreateImageWithExistingDownloadDirectory(self):
        """
        Tests the creation of an OpenStack image when the image file directory exists but not the image file.
        """
        # Create download directory
        os.makedirs(os_image_settings.download_file_path)

        # Create Image
        created_image = self.os_image.create()
        glance = self.os_image.glance
        images = glance.images.list()

        # Validate
        for image in images:
            if image.name == self.os_image.image_name:
                self.assertEquals('active', image.status)
                self.assertEquals(created_image.id, image.id)
                return
        self.fail("Created image not found")

    def testCreateImageWithExistingImageFile(self):
        """
        Tests the creation of an OpenStack image when the image file exists.
        """
        # Create download directory
        os.makedirs(os_image_settings.download_file_path)

        # Download image file
        file_utils.download(os_image_settings.url, os_image_settings.download_file_path)

        # Create Image
        created_image = self.os_image.create()
        glance = self.os_image.glance
        images = glance.images.list()

        # Validate
        for image in images:
            if image.name == self.os_image.image_name:
                self.assertEquals('active', image.status)
                self.assertEquals(created_image.id, image.id)
                return
        self.fail("Created image not found")


class CreateImageNegativeTests(OSSourceFileTestsCase):
    """
    Negative test cases for the CreateImage class
    """

    def setUp(self):
        self.createImage = None

    def tearDown(self):
        if self.createImage is not None:
            self.createImage.clean()

    def testInvalidDirectory(self):
        """
        Expect an exception when the download destination path cannot be created
        """
        self.createImage = create_image.OpenStackImage(self.os_creds, os_image_settings.image_user,
                                                       os_image_settings.format, os_image_settings.url,
                                                       os_image_settings.name, '/foo')
        with self.assertRaises(Exception):
            self.createImage.create()

    def testNoneImageName(self):
        """
        Expect an exception when the image name is None
        """
        self.createImage = create_image.OpenStackImage(self.os_creds, os_image_settings.image_user,
                                                       os_image_settings.format, os_image_settings.url, None,
                                                       os_image_settings.download_file_path)
        with self.assertRaises(Exception):
            self.createImage.create()

    def testBadImageUrl(self):
        """
        Expect an exception when the image download url is bad
        """
        self.createImage = create_image.OpenStackImage(self.os_creds, os_image_settings.image_user,
                                                       os_image_settings.format, 'http://bad.url.com/bad.iso',
                                                       os_image_settings.name, os_image_settings.download_file_path)
        with self.assertRaises(Exception):
            self.createImage.create()

    def testNoneTenantName(self):
        """
        Expect an exception when the tenant name is None
        """
        with self.assertRaises(Exception):
            self.createImage = create_image.OpenStackImage(os_credentials.OSCreds(self.os_creds.username,
                                                                                  self.os_creds.password,
                                                                                  self.os_creds.auth_url,
                                                                                  None),
                                                           os_image_settings.image_user,
                                                           os_image_settings.format, os_image_settings.url,
                                                           os_image_settings.name, os_image_settings.download_file_path)

    def testNoneAuthUrl(self):
        """
        Expect an exception when the tenant name is None
        """
        with self.assertRaises(Exception):
            self.createImage = create_image.OpenStackImage(os_credentials.OSCreds(self.os_creds.username,
                                                                                  self.os_creds.password, None,
                                                                                  self.os_creds.tenant_name),
                                                           os_image_settings.image_user,
                                                           os_image_settings.format, os_image_settings.url,
                                                           os_image_settings.name, os_image_settings.download_file_path)

    def testNonePassword(self):
        """
        Expect an exception when the tenant name is None
        """
        with self.assertRaises(Exception):
            self.createImage = create_image.OpenStackImage(os_credentials.OSCreds(self.os_creds.username, None,
                                                                                  self.os_creds.os_auth_url,
                                                                                  self.os_creds.tenant_name),
                                                           os_image_settings.image_user,
                                                           os_image_settings.format, os_image_settings.url,
                                                           os_image_settings.name, os_image_settings.download_file_path)

    def testNoneUser(self):
        """
        Expect an exception when the tenant name is None
        """
        with self.assertRaises(Exception):
            self.createImage = create_image.OpenStackImage(os_credentials.OSCreds(None, self.os_creds.password,
                                                                                  self.os_creds.os_auth_url,
                                                                                  self.os_creds.tenant_name),
                                                           os_image_settings.image_user,
                                                           os_image_settings.format, os_image_settings.url,
                                                           os_image_settings.name, os_image_settings.download_file_path)
