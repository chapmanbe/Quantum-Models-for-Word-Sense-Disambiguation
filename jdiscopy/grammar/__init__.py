# -*- coding: utf-8 -*-
# pylint: disable=unused-import

"""
Groups together the grammar modules:
:mod:`pregroup`, :mod:`cfg` and :mod:`ccg`
"""

from . import pregroup, cfg, ccg
from . pregroup import Word, draw, eager_parse, brute_force
from .cfg import CFG
from .ccg import cat2ty, tree2diagram
