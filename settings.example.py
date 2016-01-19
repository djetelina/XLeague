#!/usr/bin/env python
"""
Copyright (c) 2016 iScrE4m@gmail.com

To use the code, you must contact the author directly and ask permission.
"""
"""
STREAKS

number of wins:change multiplier

After a win if number of wins in a row is higher than the first number,
multiply rating by the second number.
"""

streaks = {3: 1.01, 5: 1.02, 10: 1.04}
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

db_path:    relative path from settings.py to db file
"""

db_path = "core/database/main.db"
