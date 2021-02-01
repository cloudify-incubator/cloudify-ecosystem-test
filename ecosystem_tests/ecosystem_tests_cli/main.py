from .commands import local_blueprint_test, remote_blueprint_test
import ecosystem_tests.ecosystem_tests_cli.ecosystem_tests as ecosystem_tests


@ecosystem_tests.group(name='ecosystem-test')
def _ecosystem_test():
    """Ecosystetm tests Command Line Interface."""
    ecosystem_tests.init()


def _register_commands():
    pass
    _ecosystem_test.add_command(local_blueprint_test.local_blueprint_test)
    _ecosystem_test.add_command(remote_blueprint_test.remote_blueprint_test)


_register_commands()


if __name__ == "__main__":
    _ecosystem_test()
