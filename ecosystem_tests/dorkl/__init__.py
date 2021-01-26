import logging

logging.basicConfig()
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)


class EcosystemTestException(Exception):
    pass


class EcosystemTimeout(Exception):
    pass
