import os.path

from django.db import models
from django import forms

from south.modelsinspector import add_introspection_rules


class ExtensionRestrictedFileField(models.FileField):
    """
    A FileField that checks filename extensions.

        file = ExtensionRestrictedFileField(extensions=[
            '.txt',
            '.pdf',
            '.png',
        ])
    """

    def __init__(self, *args, **kwargs):
        self.extensions = kwargs.pop('extensions')
        super(ExtensionRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ExtensionRestrictedFileField, self).clean(*args, **kwargs)
        extension = os.path.splitext(data.name)[1]
        extension = extension.lower()
        if extension not in self.extensions:
            raise forms.ValidationError("%s files are not allowed" % extension)
        return data

add_introspection_rules([
    (
        [ExtensionRestrictedFileField],
        [],
        {
            'extensions': ['extensions', {}],
        },
    )
], [r'^fusionbox\.db\.fields\.ExtensionRestrictedFileField$'])
