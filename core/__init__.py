# Copyright 2025 Elasticsearch B.V.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import yaml

try:
    # use the LibYAML C library bindings if available
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


if sys.version_info >= (3, 12):
    from itertools import batched
else:
    from itertools import islice

    def batched(iterable, chunk_size):
        iterator = iter(iterable)
        while chunk := list(islice(iterator, chunk_size)):
            yield chunk


def get(*, logger=None, default=sys.exit):
    global state

    if state:
        return state

    if logger:
        logger.debug("awaiting state...")

    with open("/dev/stdin") as f:
        state = yaml.load(f, Loader=Loader)

    if state:
        if logger:
            logger.debug("got state")
    elif default is sys.exit:
        if logger:
            logger.debug("no state, exiting")
        sys.exit(1)
    else:
        if logger:
            logger.debug("using default state")
        state = default

    def _put():
        if logger:
            logger.debug("relaying state...")

        with open("/dev/stdout", "w") as f:
            yaml.dump(state, f, Dumper=Dumper)

    import atexit

    atexit.register(_put)
    return state


def get_es(*, logger=None):
    from elasticsearch import Elasticsearch

    env = get(logger=logger)["environment"]
    args = {
        "hosts": env["es_url"],
        "basic_auth": (env["username"], env["password"]),
    }
    return Elasticsearch(**args)


def get_kb(*, logger=None):
    from .kibana import Kibana

    env = get(logger=logger)["environment"]
    args = {
        "url": env["kb_url"],
        "basic_auth": (env["username"], env["password"]),
    }
    return Kibana(**args)


state = None
