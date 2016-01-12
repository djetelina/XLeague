#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

import os
import pkgutil


def abs_db_path(rel_db_path):
    settings_package = pkgutil.get_loader("settings")
    settings_path = settings_package.filename
    absolute_db_path = os.path.join(
        os.path.dirname(settings_path), rel_db_path)
    return absolute_db_path
