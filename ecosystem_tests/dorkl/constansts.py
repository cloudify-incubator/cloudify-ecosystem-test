import os

MANAGER_CONTAINER_NAME = os.environ.get('MANAGER_CONTAINER', 'cfy_manager')
TIMEOUT = 1800
VPN_CONFIG_PATH = '/tmp/vpn.conf'
