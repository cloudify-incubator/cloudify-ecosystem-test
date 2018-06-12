import re

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
