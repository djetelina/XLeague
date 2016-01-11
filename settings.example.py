#!/usr/bin/env python

"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""

import os

"""
IRC SETTINGS

network:    IRC network to connect to
port:       network's port
nickname:   nickname of bot
channel:    first channel to connect to on startup
"""

network = "irc.gamesurge.net"
port = "6667"
nickname = "BotName"
channel = "#LeagueChan"

"""
GAMESURGE AUTHENTICATION

for different networks change command calling auth
"""

auth_name = "BotName"
auth_pw = ""

"""
DATABASE SETTINGS

rel_path:   relative path from settings.py to db file
"""

rel_path = "core/database/main.db"
# Don't touch this:
db_path = os.path.join(os.path.dirname(__file__), rel_path)
# Touching again allowed
