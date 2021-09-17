"""
Thie async cache utility was copied in its entirety from an open source
repositiory contributed to the community by Rajat Singh.

Since it is not under semantic version control, it is not an installable
dependancy of this project, and so it has been reproduced as a core
utility of this project.

The License for the project is reproduced as it appeared on 2021-09-17.

Copyright (c) 2020 Rajat Singh

pypi: https://pypi.org/project/async-cache/
github: https://github.com/iamsinghrajat/async-cache

"""
from .async_lru import AsyncLRU as async_lru
from .async_ttl import AsyncTTL as async_ttl
