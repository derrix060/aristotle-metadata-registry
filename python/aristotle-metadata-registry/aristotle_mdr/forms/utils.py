from aristotle_mdr import models as MDR


class FormRequestMixin(object):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class RegistrationAuthorityMixin(object):
    def set_registration_authority_field(self, field_name, qs=None):
        if qs is None:
            qs = MDR.RegistrationAuthority.objects.filter(active=MDR.RA_ACTIVE_CHOICES.active)

        ras = [(ra.id, ra.name) for ra in qs]
        self.fields[field_name].queryset = qs
        self.fields[field_name].choices = ras
