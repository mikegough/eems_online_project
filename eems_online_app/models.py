from __future__ import unicode_literals

from django.db import models

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

    def publish(self):
        self.save()

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'EEMS_ONLINE_MODELS'