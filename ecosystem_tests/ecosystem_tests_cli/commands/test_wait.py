import time
from tqdm import tqdm

from ...ecosystem_tests_cli import ecosystem_tests


@ecosystem_tests.command(name='wait-test', short_help='Wait Test.')
def wait_until():
    interval = 0.5
    for i in tqdm(range(1), desc='main'):
        time.sleep(interval)
