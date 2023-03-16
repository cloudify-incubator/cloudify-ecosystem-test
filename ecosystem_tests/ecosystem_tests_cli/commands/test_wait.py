import time

from ..logger import logger
from ...ecosystem_tests_cli import ecosystem_tests

from ecosystem_cicd_tools.new_cicd import bundles


@ecosystem_tests.command(name='wait-test',
                         short_help='Wait Test.')
def wait_until(duration=5):
    interval = 1
    start_time = time.time()
    end_time = start_time + duration
    while True:
        if time.time() > end_time:
            break
        logger.info('Waiting....')
        time.sleep(interval)
