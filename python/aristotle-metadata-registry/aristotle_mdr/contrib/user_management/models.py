from aristotle_mdr.fields import LowerEmailField
from improved_user.model_mixins import AbstractUser

from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    email = LowerEmailField(_('email address'), max_length=254, unique=True)
