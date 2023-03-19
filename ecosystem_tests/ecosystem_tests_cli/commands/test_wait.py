import time

from ...ecosystem_tests_cli import ecosystem_tests

from tqdm import tqdm

@ecosystem_tests.command(name='wait-test',
                         short_help='Wait Test.')
def wait_until():
    interval = 0.5
    for i in tqdm(range(1), desc='main'):
        time.sleep(interval)
