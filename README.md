Python scripts for creating virtual environments on OpenStack with Ansible playbooks for provisioning.

Environment Setup
  * Python 2.7 (recommend leveraging a Virtual Python runtime)
    * OpenStack clients 2.0.0
      * neutron
      * glance
      * keystone
      * nova
    * shutil
    * time
    * Crypto
    * ansible (1.9.4)

To run unit tests.
  * cd python
  * python unit_test_suite.py

To deploy virtual environments
  * cd <repo dir> python
    (CWD must be here now as there are some post-deployment Ansible scripts located in python/provisioning/ansible
     called by create_instance.py
  * export PYTHONPATH=$PYTHONPATH:$(pwd)
  * python deploy_venv.py <path to deployment configuration YAML file>
    * i.e. python deploy_venv.py <path to repo>/ansible/yardstick/deploy-yardstick.yaml
      (deployment of a virtual environment where the VM has Yardstick installed)

Also see the [CableLabs project wiki page](https://community.cablelabs.com/wiki/display/SNAPS/OpenStack+Instantiation%2C+Provisioning%2C+and+Testing)
for more information on these scripts.

(More to come...)