import logging

logging.basicConfig()
logger = logging.getLogger('ecosystem-cli')
logger.setLevel(logging.DEBUG)

botocore_hooks = logging.getLogger('botocore.hooks')
botocore_hooks.setLevel(logging.ERROR)

botocore_loaders = logging.getLogger('botocore.loaders')
botocore_loaders.setLevel(logging.ERROR)

botocore_credentials = logging.getLogger('botocore.credentials')
botocore_credentials.setLevel(logging.ERROR)

botocore_utils = logging.getLogger('botocore.utils')
botocore_utils.setLevel(logging.ERROR)

botocore_httpsession = logging.getLogger('botocore.httpsession')
botocore_httpsession.setLevel(logging.ERROR)

botocore_parsers = logging.getLogger('botocore.parsers')
botocore_parsers.setLevel(logging.ERROR)

botocore_auth = logging.getLogger('botocore.auth')
botocore_auth.setLevel(logging.ERROR)

botocore_endpoint = logging.getLogger('botocore.endpoint')
botocore_endpoint.setLevel(logging.ERROR)

botocore_endpoint = logging.getLogger('botocore.endpoint')
botocore_endpoint.setLevel(logging.ERROR)

botocore_retryhandler = logging.getLogger('botocore.retryhandler')
botocore_retryhandler.setLevel(logging.ERROR)

botocore_client = logging.getLogger('botocore.client')
botocore_client.setLevel(logging.ERROR)

boto3_resources_model = logging.getLogger('boto3.resources.model')
boto3_resources_model.setLevel(logging.ERROR)

boto3_resources_factory = logging.getLogger('boto3.resources.factory')
boto3_resources_factory.setLevel(logging.ERROR)

s3transfer_utils = logging.getLogger('s3transfer.utils')
s3transfer_utils.setLevel(logging.ERROR)

s3transfer_tasks = logging.getLogger('s3transfer.tasks')
s3transfer_tasks.setLevel(logging.ERROR)

s3transfer_futures = logging.getLogger('s3transfer.futures')
s3transfer_futures.setLevel(logging.ERROR)

botocore_regions = logging.getLogger('botocore.regions')
botocore_regions.setLevel(logging.ERROR)

urllib3_connectionpool = logging.getLogger('urllib3.connectionpool')
urllib3_connectionpool.setLevel(logging.ERROR)

boto3_resources_action = logging.getLogger('boto3.resources.action')
boto3_resources_action.setLevel(logging.ERROR)

boto3_resources_collection = logging.getLogger('boto3.resources.collection')
boto3_resources_collection.setLevel(logging.ERROR)
