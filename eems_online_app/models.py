from __future__ import unicode_literals

from django.db import models

from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from django.conf import settings
import os
import shutil
base_dir = settings.BASE_DIR
static_dir = settings.STATIC_URL
models_dir = base_dir + "/eems_online_app" + static_dir + "eems/models/"

# Create your models here.
class EemsOnlineModels(models.Model):
    id = models.TextField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.TextField(db_column='NAME', blank=True, null=True)  # Field name made lowercase.
    extent = models.TextField(db_column='EXTENT', blank=True, null=True)  # Field name made lowercase.
    extent_gcs = models.TextField(db_column='EXTENT_GCS', blank=True, null=True) # Field name made lowercase.
    owner = models.TextField(db_column='OWNER', blank=True, null=True)  # Field name made lowercase.
    short_description = models.TextField(db_column='SHORT_DESCRIPTION', blank=True, null=True)  # Field name made lowercase.
    long_description = models.TextField(db_column='LONG_DESCRIPTION', blank=True, null=True)  # Field name made lowercase.
    author = models.TextField(db_column='AUTHOR', blank=True, null=True)  # Field name made lowercase.
    creation_date = models.TextField(db_column='CREATION_DATE', blank=True, null=True)  # Field name made lowercase.
    epsg = models.TextField(db_column='EPSG', blank=True, null=True)  # Field name made lowercase.
    project = models.TextField(db_column='PROJECT', blank=True, null=True)  # Field name made lowercase.
    user = models.TextField(db_column='USER', blank=True, null=True)  # Field name made lowercase.
    status = models.TextField(db_column='STATUS', blank=True, null=True)  # Field name made lowercase.
    upload_datetime = models.TextField(db_column='UPLOAD_DATETIME', blank=True, null=True)  # Field name made lowercase.

    def publish(self):
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'EEMS_ONLINE_MODELS'
        verbose_name_plural = "My EEMS Models"
        default_permissions = ('add', 'change', 'delete', 'view')
        # This line was the trick to allowing users to view/modify the EEMS MODEL table
        permissions = (
            ("read_eems", "Can Read EEMS"),
        )

# Delete the eems model directory when the corresponding record is deleted.
@receiver(pre_delete, sender=EemsOnlineModels)
def mymodel_delete(sender, instance, **kwargs):
    # Make sure there aren't any slashes in the id
    model_dir = models_dir + instance.id.replace("/", "").replace("\\", "")
    if os.path.isdir(model_dir) and instance.id != "":
        print model_dir
        shutil.rmtree(model_dir)

