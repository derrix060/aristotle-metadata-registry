from dal.autocomplete import ModelSelect2Multiple, ModelSelect2
from django.urls import reverse_lazy


class ConceptAutocompleteBase(object):

    class Media:
        """Automatically include static files for the admin."""

        css = {
            'all': (
                'autocomplete_light/vendor/select2/dist/css/select2.css',
                'autocomplete_light/select2.css',
                'aristotle_mdr/aristotle.autocomplete.css',
            )
        }
        js = (
            'autocomplete_light/jquery.init.js',
            'autocomplete_light/autocomplete.init.js',
            'autocomplete_light/vendor/select2/dist/js/select2.full.js',
            'autocomplete_light/select2.js',
        )

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        if self.model:
            url = reverse_lazy(
                'aristotle-autocomplete:concept',
                args=[self.model._meta.app_label, self.model._meta.model_name]
            )
        else:
            url = 'aristotle-autocomplete:concept'
        kwargs.update(
            url=url,
            attrs={'data-html': 'true'}
        )
        super().__init__(*args, **kwargs)


class ConceptAutocompleteSelectMultiple(ConceptAutocompleteBase, ModelSelect2Multiple):
    pass


class ConceptAutocompleteSelect(ConceptAutocompleteBase, ModelSelect2):
    pass


class UserAutocompleteMixin(object):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            url=reverse_lazy(self.url),
            attrs={'data-html': 'true'}
        )
        super().__init__(*args, **kwargs)

    def render_options(self, *args, **kwargs):
        """This prevents users from showing in a static HTML list"""
        return ""


class UserAutocompleteSelect(UserAutocompleteMixin, ModelSelect2):
    url = 'aristotle-autocomplete:user'


class UserAutocompleteSelectMultiple(UserAutocompleteMixin, ModelSelect2Multiple):
    url = 'aristotle-autocomplete:user'


class WorkgroupAutocompleteMixin(object):
    def __init__(self, *args, **kwargs):
        kwargs.update(
            url=reverse_lazy(self.url),
            attrs={'data-html': 'true'}
        )
        super().__init__(*args, **kwargs)


class WorkgroupAutocompleteSelect(WorkgroupAutocompleteMixin, ModelSelect2):
    url = 'aristotle-autocomplete:workgroup'
