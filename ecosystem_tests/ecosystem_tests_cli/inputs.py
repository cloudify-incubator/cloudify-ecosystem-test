import os
import yaml

from .logger import logger
from .utilities import parse_key_value_pair
from .exceptions import EcosystemTestCliException

ERR_MSG = "Invalid input format: {0}, the expected format is: " \
          "key1=value1;key2=value2"


def inputs_to_dict(resources):
    """Returns a dictionary of inputs
    `resources` can be:
    - A list of files.
    - A single file
    - A key1=value1;key2=value2 pairs string.
    """

    if not resources:
        return dict()

    parsed_dict = {}

    for resource in resources:
        logger.debug('Processing inputs source: {0}'.format(resource))
        try:
            parsed_dict.update(_parse_single_input(resource))
        except EcosystemTestCliException as ex:
            ex_msg = \
                "Invalid input: {0}. It must represent a dictionary. " \
                "Valid values can be one of:\n" \
                "- A path to a YAML file\n" \
                "- A string formatted as JSON/YAML\n" \
                "- A string formatted as key1=value1;key2=value2\n".format(
                    resource)
            if str(ex):
                ex_msg += "\nRoot cause: {0}".format(ex)
            raise EcosystemTestCliException(ex_msg)

    return parsed_dict


def _parse_single_input(resource):
    try:
        # parse resource as string representation of a dictionary
        return plain_string_to_dict(resource)
    except EcosystemTestCliException:
        parsed_dict = dict()
        parsed_dict.update(_parse_yaml_path(resource))
    return parsed_dict


def _parse_yaml_path(resource):
    try:
        # if resource is a path - parse as a yaml file
        if os.path.isfile(resource):
            with open(resource) as f:
                content = yaml.safe_load(f.read())
        else:
            # parse resource content as yaml
            content = yaml.safe_load(resource)
    except yaml.error.YAMLError as e:
        raise EcosystemTestCliException(
            "'{0}' is not a valid YAML. {1}".format(
                resource, str(e)))

    # Emtpy files return None
    content = content or dict()
    if not isinstance(content, dict):
        raise EcosystemTestCliException('Resource is valid YAML, but does not '
                                        'represent a dictionary (content: {0})'
                                        .format(content))

    return content


def _is_not_plain_string_input(mapped_input):
    """True if the input is a json string, yaml file or a directory"""
    return mapped_input.endswith(('}', '.yaml', '/'))


def plain_string_to_dict(input_string):
    input_string = input_string.strip()
    input_dict = {}
    mapped_inputs = input_string.split(';')
    for mapped_input in mapped_inputs:
        mapped_input = mapped_input.strip()
        if not mapped_input:
            continue

        if _is_not_plain_string_input(mapped_input):
            raise EcosystemTestCliException(
                'The input {0} is not a plain string '
                'key'.format(mapped_input))
        key, value = parse_key_value_pair(mapped_input,
                                          ERR_MSG.format(input_string))

        input_dict[key] = value
    return input_dict
