import sys
from functools import wraps

from .logging import logger
from .boto3 import get_boto_client


def with_ec2_client(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):

        kwargs['ec2'] = get_client()
        return func(*args, **kwargs)
    return wrapper_func


def get_client():
    return get_boto_client('ec2')


class BadQuotaException(Exception):
    pass


@with_ec2_client
def get_max_eips(ec2=None):
    resp = ec2.describe_account_attributes()
    try:
        for attr in resp['AccountAttributes']:
            if attr['AttributeName'] == 'vpc-max-elastic-ips':
                return int(attr['AttributeValues'][0]['AttributeValue'])
    except (KeyError, IndexError):
        raise BadQuotaException(
            'No max-elastic-ips in E2 account attributes.')


@with_ec2_client
def count_current_eips(ec2=None):
    resp = ec2.describe_addresses()
    try:
        return len(resp['Addresses'])
    except KeyError:
        raise BadQuotaException('Unable to count available EIPs.')


def check_eip_quota(required_ips):
    if required_ips == 0:
        logger.info('Not performing quota check, '
                    'required eips={}'.format(required_ips))
        return
    logger.info('Checking if we have enough EIPs for required {}'.format(
        required_ips))
    max_eips = get_max_eips()
    logger.info('The max EIPs allowed in this region is {}'.format(
        max_eips))
    current_eips = count_current_eips()
    logger.info('The current EIPs in use in this region is {}'.format(
        current_eips))
    if max_eips - current_eips >= required_ips:
        logger.info('There are enough elastic EIPs for this test. '
                    '(But we do not know about other concurrent tests!)')
    else:
        remove_ips = required_ips - (max_eips - current_eips)
        logger.error(
            'There are not enough EIPs in region to run the test. '
            'Max: {}, Current: {}, Requested: {}, '
            'Remove at least: {}'.format(
                max_eips, current_eips, required_ips, remove_ips))
        sys.exit(1)
