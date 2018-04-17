#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s -> %(message)s', '[%Y.%m.%d - %H:%M:%S]')

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

try:
    fh = logging.FileHandler('logger.log', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
except Exception:
    pass
