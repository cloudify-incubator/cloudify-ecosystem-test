# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
    Decorators
    ~~~~~~~~~~~~~~~~~
    cloudify-ecosystem-test decorators


    click decorators are located in the class Options in ecosystem_tests.py
"""

import time

from .logger import logger
from constants import YELLOW, RESET


def timer_decorator(fn):
    def wrapper(**kwargs):
        start = time.time()
        logger.info(YELLOW +
                    "Test starts at {}".format(time.ctime(start)) +
                    RESET)

        result = fn(**kwargs)

        end = time.time()
        logger.info(YELLOW +
                    "Test finished at {}".format(time.ctime(end)) +
                    RESET)
        logger.info(YELLOW +
                    "Test ran for {} seconds".format(end - start) +
                    RESET)
        return result
    return wrapper

