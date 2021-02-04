from .exceptions import EcosystemTestCliException

def parse_key_value_pair(mapped_input, error_msg):
    split_mapping = mapped_input.split('=',1)
    try:
        key = split_mapping[0].strip()
        value = split_mapping[1].strip()
        return key, value
    except IndexError:
        raise EcosystemTestCliException(
            error_msg)