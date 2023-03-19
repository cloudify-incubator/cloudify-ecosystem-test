import time

from ...ecosystem_tests_cli import ecosystem_tests
from .create_manager.docker import download_and_load_docker_image

from mock import patch


@ecosystem_tests.command(name='wait-test',
                         short_help='Wait Test.')
@patch('ecosystem_tests.ecosystem_tests_cli.commands.create_manager.docker')
def wait_until(docker_mock, *_, **__):

    def fake_docker(*args, **kwargs):
        time.sleep(0.1)
        if kwargs.get('json_format'):
            return {}
        return 'valid result'

    docker_mock.docker = fake_docker
    download_and_load_docker_image(
        'https://github.com/docker-library/'
        'hello-world/archive/refs/heads/master.zip', 'hello-world')
