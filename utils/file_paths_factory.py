# -*- coding: utf-8 -*-

# Paste Images As WebP add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.


import itertools
import random
import re
import time
import unicodedata
from functools import wraps
from time import gmtime, strftime
from typing import AnyStr, List

from aqt.editor import Editor
from aqt.qt import *

from ..config import config


def compatible_filename(f):
    max_len = 50

    def replace_forbidden_chars(s: str) -> str:
        return re.sub(r'[<>:"/|?*\\]+', '_', s, flags=re.MULTILINE | re.IGNORECASE)

    @wraps(f)
    def wrapper(*args, **kwargs) -> str:
        s = unicodedata.normalize('NFC', f(*args, **kwargs))
        s = replace_forbidden_chars(s)
        s = s.lower()
        return s[:max_len] if s else FilePathFactory.default_prefix

    return wrapper


class FilePathFactory:
    ext = '.webp'
    default_prefix = 'paste'

    def __init__(self, target_dir_path: str = None, editor: Editor = None):
        self.target_dir_path = target_dir_path
        self.editor = editor

        self.prefixes = {
            self.default_prefix: lambda: self.default_prefix,
            'sort-field': self.sort_field,
            'current-field': self.current_field,
        }
        self.suffixes = {
            'time-number': lambda: str(int(time.time() * 1000)),
            'time-human': lambda: strftime("%d-%b-%Y_%H-%M-%S", gmtime()),
        }

        self.patterns = [f'{prefix}_{suffix}{self.ext}' for prefix in self.prefixes for suffix in self.suffixes]

    @property
    def patterns_populated(self) -> List[str]:
        return [self.make_filename(pattern) for pattern in self.patterns]

    def make_filename(self, pattern: str) -> str:
        for k, v in itertools.chain(self.prefixes.items(), self.suffixes.items()):
            pattern = pattern.replace(k, v())

        return pattern

    def make_unique_filepath(self) -> AnyStr:
        try:
            pattern = self.patterns[config.get('filename_pattern_num', 0)]
        except IndexError:
            pattern = self.patterns[0]

        out_filename = self.make_filename(pattern)
        out_filename = self.ensure_unique(out_filename)
        return os.path.join(self.target_dir_path, out_filename)

    def ensure_unique(self, file_path: str) -> str:
        out = file_path
        cut = file_path[:-len(self.ext)]
        while os.path.isfile(out):
            out = cut + '_' + str(random.randint(100, 999)) + self.ext
        return out

    @compatible_filename
    def sort_field(self):
        try:
            sort_field = self.editor.note.note_type()['sortf']
            return self.editor.note.values()[sort_field]
        except AttributeError:
            return 'sort-field'

    @compatible_filename
    def current_field(self):
        try:
            return self.editor.note.values()[self.editor.currentField]
        except (AttributeError, TypeError):
            return 'current-field'
