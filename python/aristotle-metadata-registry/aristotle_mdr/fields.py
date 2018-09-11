"""
Concept model relations
-----------------------

These are direct reimplementations of Django model relations,
at the moment they onyl exist to make permissions-based filtering easier for
the GraphQL codebase. However, in future these may add additional functionality
such as automatically applying certain permissions to ensure users only
retrieve the right objects.

When building models that link to any subclass of ``_concept``, use these in place
of the Django builtins.

.. note:: The model these are place on does *not* need to be a subclass of concept.
 They are for linking *to* a concept subclass.

"""

from django import forms
from django.db.models import (
    ForeignKey, ManyToOneRel,
    ManyToManyField, ManyToManyRel,
    OneToOneField, OneToOneRel
)
from django.db.models.fields import (
    TextField, EmailField
)

from django.forms import EmailField as EmailFormField

from constrainedfilefield.fields import ConstrainedImageField
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
import io
import os


class ConceptOneToOneRel(OneToOneRel):
    pass


class ConceptOneToOneField(OneToOneField):
    """
    Reimplementation of ``OneToOneField`` for linking
    a model to a Concept
    """
    rel_class = ConceptOneToOneRel


class ConceptManyToOneRel(ManyToOneRel):
    pass


class ConceptForeignKey(ForeignKey):
    """
    Reimplementation of ``ForeignKey`` for linking
    a model to a Concept
    """
    rel_class = ConceptManyToOneRel


class ConceptManyToManyRel(ManyToManyRel):
    pass


class ConceptManyToManyField(ManyToManyField):
    """
    Reimplementation of ``ManyToManyField`` for linking
    a model to a Concept
    """
    rel_class = ConceptManyToManyRel


class ShortTextField(TextField):

    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {'widget': forms.TextInput}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class ConvertedConstrainedImageField(ConstrainedImageField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result_size = kwargs.pop('size', (256, 256))

    def clean(self, value, *args, **kwargs):

        # data is an ImageFieldFile object
        data = super().clean(value, *args, **kwargs)

        filename = os.path.splitext(data.name)[0]
        filename = filename + '.png'
        pythonfile = data.file.file

        bytesio = io.BytesIO()

        im = Image.open(pythonfile)
        im = im.rotate(180)
        im.thumbnail(self.result_size, Image.ANTIALIAS)
        im = im.rotate(180)

        im.save(bytesio, 'png')

        imagefile = InMemoryUploadedFile(
            file=bytesio,
            field_name=data.file.field_name,
            name=filename,
            content_type='image/png',
            size=bytesio.getbuffer().nbytes,
            charset=None
        )

        return imagefile


class LowerEmailFormField(EmailFormField):

    def clean(self, value):
        if value is not None:
            value = value.lower()
        return super().clean(value)


class LowerEmailField(EmailField):
    """
    Reimplementation of email field, where email is always stored lowercase
    """

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        if value is not None:
            return value.lower()
        else:
            return value

    def formfield(self, *args, **kwargs):
        defaults = {
            'form_class': LowerEmailFormField
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
