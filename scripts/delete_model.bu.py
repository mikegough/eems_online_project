# Deletes the specified model from the database and removes the model directory

import sys
import sqlite3
import shutil
conn = sqlite3.connect("../db.sqlite3")

model_id_to_delete= sys.argv[1]

c = conn.cursor()

query = "DELETE from EEMS_ONLINE_MODELS where ID = %s" % model_id_to_delete
print query

c.execute(query)

#all_rows = c.fetchall()
#print all_rows 

conn.commit()
conn.close()

print "Model with ID %s has been deleted" % model_id_to_delete 

model_dir = "../eems_online_app/static/eems/models/%s" % model_id_to_delete

shutil.rmtree(model_dir)

print "Model directory with ID %s has been deleted" % model_id_to_delete 


