# import testtools
import re
# import .utils

IP_ADDRESS_REGEX = "(?:[0-9]{1,3}\.){3}[0-9]{1,3}"


class PasswordFilter(object):
    """ Lifted from here: https://stackoverflow.com/a/42021966/5580340.
    """
    def __init__(self, strings_to_filter, stream):
        if not isinstance(strings_to_filter, list):
            raise
        self.stream = stream
        strings_to_filter.append(IP_ADDRESS_REGEX)
        self.strings_to_filter = strings_to_filter

    def __getattr__(self, attr_name):
        return getattr(self.stream, attr_name)

    def write(self, data):
        for my_string in self.strings_to_filter:
            data = re.sub(
                r'\b{0}\b'.format(my_string), '*' * len(my_string), data)
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.stream.flush()


# class TestLocal(testtools.TestCase):

#     def create_inputs():
#         raise NotImplementedError(
#             'Class create_inputs implemented by subclass.')

#     def _test_manager(self, _cfy_local, post_install=None):

#         try:
#             cfy_local.execute(
#                 'install',
#                 task_retries=45,
#                 task_retry_interval=10)
#             if post_install:
#                 post_install()
#         finally:
#             utils.initialize_cfy_profile()
#             _cfy_local.execute(
#                 'uninstall',
#                 parameters={'ignore_failure': True},
#                 allow_custom_parameters=True,
#                 task_retries=100,
#                 task_retry_interval=15)
