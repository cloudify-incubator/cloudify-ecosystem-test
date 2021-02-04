INPUTS_PARAMS_USAGE = (
    '(Can be provided as path to YAML file, or as '
    '\'key1=value1;key2=value2\'). This argument can be used multiple times.'
)

INPUTS = "Test inputs {0}".format(INPUTS_PARAMS_USAGE)

TEST_TIMEOUT = 'Test timeout (seconds).'

TEST_ID = 'Test id, the name of the test deployment.'

NESTED_TEST = 'Nested tests, will run by pytest, should be specified in the ' \
              'pytest notation like: path/to/module.py::TestClass::test_method'

VALIDATE_ONLY = 'Perform blueprint validation only on the given blueprints.'

LICENSE = 'Licence for the manager, should be either path to licence file ' \
          'or base64 encoded licence string.'

SECRETS = 'A secret to update on the manager, should be provided as' \
          ' secret_key:secret_value. This argument can be used multiple times.'

FILE_SECRETS = 'A secret to update on the manager, should be provided as' \
               ' secret_key:file_path. This argument can be used' \
               ' multiple times.'

ENCODED_SECRETS ='Base 64 encoded secret to update on the manager, ' \
                 'should be provided as ' \
                 'secret_key:secret_value_base_64_encoded. This argument can' \
                 ' be used multiple times.'

CONTAINER_NAME = 'Manager docker container name. ' \
                 'Default: MANAGER_CONTAINER environment variable or ' \
                '"cfy_manager" if there is no such environment variable.'