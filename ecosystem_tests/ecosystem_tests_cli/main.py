from .logger import logger
from ..ecosystem_tests_cli import ecosystem_tests
from .commands import (local_blueprint_test,
                       prepare_test_manager)


@ecosystem_tests.group(name='ecosystem-test')
def _ecosystem_test():
    """Ecosystetm tests Command Line Interface."""
    ecosystem_tests.init()


def _register_commands():
    _ecosystem_test.add_command(local_blueprint_test.local_blueprint_test)
    _ecosystem_test.add_command(prepare_test_manager.prepare_test_manager)


_register_commands()

if __name__ == "__main__":
    _ecosystem_test()
