import sys
import sqlite3
conn = sqlite3.connect("../db.sqlite3")
c = conn.cursor()

query = "SELECT ID, NAME, PROJECT, OWNER, STATUS from EEMS_ONLINE_MODELS"

print "ID, NAME, OWNER"
for row in c.execute(query):
	print ",".join(map(str,row))

conn.close()

