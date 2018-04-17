#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from datetime import datetime
from typing import Sequence, Mapping


def timestamp() -> str:
    ''' Функция возвращает текущее время
    '''
    return datetime.now().strftime('%H:%M:%S')


class CompletionsFile:

    def __init__(self, filename):
        self._filename = filename


    def read(self) -> Sequence:
        completions = []

        # создание файла, если его до этого его не существовало
        if not os.path.isfile(self._filename):
            with open(self._filename, 'w') as file:
                pass

        with open(self._filename, 'r') as file:
            for line in file:
                completions.append(line.rstrip('\n'))

            return completions


    def write(self, completions: Sequence):
        with open(self._filename, 'w+') as file:
            for line in completions:
                file.write('{}\n'.format(line.strip()))
