#!/usr/bin/env python

import pandas.io.sql as sql
from wordpress_xmlrpc import Client, WordPressPage
from wordpress_xmlrpc.methods import posts
import csv, os, sqlite3, time

script_dir = os.path.dirname(__file__)
rel_path = "database/main.db"
database = sqlite3.connect(os.path.join(script_dir, rel_path), timeout=1)
login = (os.path.join(os.path.dirname(__file__), "wordpress/wp.txt"))


def updateleader():
    read = sql.read_sql("SELECT Name, ELO, Played, W, L FROM players WHERE Played > 0 ORDER BY ELO DESC", database)
    csvpath = (os.path.join(os.path.dirname(__file__), "wordpress/temp.csv"))
    read.to_csv(csvpath)
    # get wordpress login information
    with open(login) as f:
        wplogin = f.read().split(',')
    # open csv and save it to string
    with open(csvpath, 'rb') as f:
        csvfile = csv.reader(f)
        table = ""
        for row in csvfile:
            table += "%s\n" % (str(row))
    # get rid of unwanted characters
    table = table.translate(None, '\'[]')
    timestamp = time.strftime("%d.%m.%Y at %H:%M:%SCET", time.localtime(time.time()))
    # define content of new page, syntax for wordpress title, our string in the middle and Timestamp at the end
    content = "[table]" + str(table) + "[/table] \n Last update: %s" % (timestamp)
    # Login to wordpress
    wp = Client("http://xleague.djetelina.cz/xmlrpc.php", "%s" % (wplogin[0]), "%s" % (wplogin[1]))
    # Define what are we editing
    page = WordPressPage()
    page.id = 139
    page.content = content
    page.title = "LeaderBoard"
    # Edit desired page
    wp.call(posts.EditPost(page.id, page))


if __name__ == '__main__':
    updateleader()
