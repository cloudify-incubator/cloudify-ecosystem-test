import click

CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'])

def init():
    pass


def group(name):
    return click.group(name=name, context_settings=CLICK_CONTEXT_SETTINGS)


def command(*args, **kwargs):
    return click.command(*args, **kwargs)

class Options(object):
    def __init__(self):
        """The options api is nicer when you use each option by calling
        `@ecosystem_tests.options.some_option` instead of
        `@ecosystem_tests.some_option`.
        Note that some options are attributes and some are static methods.
        The reason for that is that we want to be explicit regarding how
        a developer sees an option. It it can receive arguments, it's a
        method - if not, it's an attribute.
        """
        pass


options = Options()
