PLUGINS_RELEASE_MESSAGE_START = """
Version {version}, assets:\n"""

PLUGINS_RELEASE_MESSAGE_ASSET = "{asset_link}"

BLUEPRINTS_RELEASE_MESSAGE_TEMPLATE = """
Example blueprints for use with Cloudify version {cloudify_version}.
This is package number {package} to be released for this version of Cloudify.
Always try to use the latest package for your version of Cloudify.
"""


BLUEPRINT_LABEL_TEMPLATE = """
blueprint_labels:
  obj-type: 
    values: 
      - {plugin_name}
"""

DEPLOYMENT_LABEL_TEMPLATE = """
labels:
  obj-type: 
    values: 
      - {plugin_name}
"""

RESOURCE_TAGS_TEMPLATE = """
resource_tags:
  tenant: { get_sys: [ tenant, name ] }
  deployment_id: { get_sys: [ deployment, id ] }
  owner: { get_sys: [ deployment, owner ] }
"""

LABELLED_PLUGINS = ['aws',
                    'gcp',
                    'azure',
                    'terraform',
                    'helm',
                    'ansible',
                    'kubernetes',
                    'openstack',
                    'vcloud',
                    'vsphere',
                    'starlnigx',
                    'docker']

V2_YAML = 'v2_plugin.yaml'
