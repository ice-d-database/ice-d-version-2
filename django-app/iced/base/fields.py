from django.db import models


class UniqueNameField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(UniqueNameField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower().trim().replace(" ", "-")
