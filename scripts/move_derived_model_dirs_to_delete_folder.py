# Moves the model directories that don't have an associated entry in the database and are more than a day old to 
# a folder to be deleted. These model directories are created from model runs where the user didn't get the link.
# If the user didn't push the get link button, they have no intention of sharing the results of the model run.
# These models can therefore be deleted. 
# TODO: consider putting on a cron job that runs every night at midnight

from datetime import datetime, timedelta
from os import path
import sys
import os
import sqlite3
import shutil

# Don't move these folders...
folder_exemptions = ["zip", "Archive"]

# The folder containing the models: 
#root_model_dir = "/home/mike/webapps/eems/eems_online_project/eems_online_app/static/eems/models"
root_model_dir = r"F:\Projects2\EEMS_Online\tasks\web_applications\eems_online_django\eems_online_project\eems_online_app\static\eems\models"

# The folder to move models to for deletion:
#models_to_delete_dir = "/home/mike/webapps/eems/eems_online_project/eems_online_app/static/eems/delete"
models_to_delete_dir = r"F:\Projects2\EEMS_Online\tasks\web_applications\eems_online_django\eems_online_project\eems_online_app\static\eems\delete"

# Get a list of all the model directories in the models folder: 
model_dirs = os.listdir(root_model_dir)

# Get a list of all the model ids in the database: 
conn = sqlite3.connect("../db.sqlite3")
conn.row_factory = lambda cursor, row: row[0]
c = conn.cursor()
query = "select ID from EEMS_ONLINE_MODELS"
c.execute(query)
all_rows = c.fetchall()

# Determine what the date was 24 hours ago: 
one_day_ago = datetime.now() - timedelta(days=1)

print("\nModel folders created before " + str(one_day_ago) + " that are not in the database will be moved to the delete folder for deletion.")

print("\nMoving...\n")

count_total = 0
count_to_delete = 0 

models_in_database = len(all_rows)

for model_dir in model_dirs:
    count_total += 1
    full_path = root_model_dir + os.sep + model_dir
    model_dir_creation = datetime.fromtimestamp(path.getctime(full_path))
    # if the model directory is not in the database (it's a derived model, not an uploaded model), and its creation date is earlier than the date 24 hours ago...move the directory.
    if model_dir not in all_rows and model_dir_creation < one_day_ago:
        if model_dir not in folder_exemptions: 
            print(model_dir + ": " + str(model_dir_creation))
            #shutil.move(full_path, models_to_delete_dir)
            count_to_delete += 1

print("\nTotal number of models in the database (includes failed uploads where status = 0): " + str(models_in_database))
print("\nTotal number of model directories: " + str(count_total))
print("Total number of model directories moved for deletion (derived models, >1 day old, 'Get Link' button not pushed): " + str(count_to_delete))
print("Total number of model directories to keep: " + str(count_total - count_to_delete))
conn.close()
