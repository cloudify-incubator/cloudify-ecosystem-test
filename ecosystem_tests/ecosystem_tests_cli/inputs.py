import os
import glob
import yaml
import  collections
from .exceptions import EcosystemTestCliException

def inputs_to_dict(resources, **kwargs):
    """Returns a dictionary of inputs
    `resources` can be:
    - A list of files. yes!
    - A single file yes!
    - A directory containing multiple input files -no!
    - A key1=value1;key2=value2 pairs string. -yes!
    - A string formatted as JSON/YAML. yes!
    - Wildcard based string (e.g. *-inputs.yaml)   -no!
    """
    # logger = get_logger()

    if not resources:
        return dict()

    parsed_dict = {}

    for resource in resources:
        # logger.debug('Processing inputs source: {0}'.format(resource))
        # if isinstance(resource, (text_type, bytes)):
        try:
            parsed_dict.update(_parse_single_input(resource))
        except EcosystemTestCliException as ex:
            ex_msg = \
                "Invalid input: {0}. It must represent a dictionary. " \
                "Valid values can be one of:\n" \
                "- A path to a YAML file\n" \
                "- A string formatted as JSON/YAML\n" \
                "- A string formatted as key1=value1;key2=value2\n"\
                .format(resource)
            if str(ex):
                ex_msg += "\nRoot cause: {0}".format(ex)
            raise EcosystemTestCliException(ex_msg)

    return parsed_dict



def _parse_single_input(resource, **kwargs):
    try:
        # parse resource as string representation of a dictionary
        return plain_string_to_dict(resource, **kwargs)
    except EcosystemTestCliException:
        # input_files = glob.glob(resource)
        parsed_dict = dict()
        # if os.path.isdir(resource):
        #     for input_file in os.listdir(resource):
        #         parsed_dict.update(
        #             _parse_yaml_path(os.path.join(resource, input_file)))
        # elif input_files:
        #     for input_file in input_files:
        #         parsed_dict.update(_parse_yaml_path(input_file))
        # else:
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
        raise EcosystemTestCliException("'{0}' is not a valid YAML. {1}".format(
            resource, str(e)))

    # Emtpy files return None
    content = content or dict()
    if not isinstance(content, dict):
        raise EcosystemTestCliException('Resource is valid YAML, but does not '
                               'represent a dictionary (content: {0})'
                               .format(content))

    return content


def _parse_key_value_pair(mapped_input, input_string):
    split_mapping = mapped_input.split('=')
    try:
        key = split_mapping[0].strip()
        value = split_mapping[1].strip()
        return key, value
    except IndexError:
        raise EcosystemTestCliException(
            "Invalid input format: {0}, the expected format is: "
            "key1=value1;key2=value2".format(input_string))


def _is_not_plain_string_input(mapped_input):
    """True if the input is a json string, yaml file or a directory"""
    return mapped_input.endswith(('}', '.yaml', '/'))


def plain_string_to_dict(input_string, **kwargs):
    input_string = input_string.strip()
    input_dict = {}
    mapped_inputs = input_string.split(';')
    for mapped_input in mapped_inputs:
        mapped_input = mapped_input.strip()
        if not mapped_input:
            continue

        # # Only in delete-runtime the input can be a string (key) with no value.
        # if kwargs.get('deleting'):
        if _is_not_plain_string_input(mapped_input):
            raise CloudifyCliError('The input {0} is not a plain string '
                                   'key'.format(mapped_input))
        #     key = mapped_input.strip()
        #     value = None
        # else:
        key, value = _parse_key_value_pair(mapped_input, input_string)

        # # If the input is in dot hierarchy format, e.g. 'a.b.c=d'
        # if kwargs.get('dot_hierarchy') and '.' in key:
        #     insert_dotted_key_to_dict(input_dict, key, value)
        # else:
        input_dict[key] = value
    return input_dict

