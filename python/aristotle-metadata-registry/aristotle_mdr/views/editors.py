from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.views.generic import (
    CreateView, DetailView, UpdateView
)

import reversion

from braces.views import PermissionRequiredMixin

from aristotle_mdr.utils import (
    concept_to_clone_dict, construct_change_message_extra_formsets,
    construct_change_message, url_slugify_concept, is_active_module
)
from aristotle_mdr import forms as MDRForms
from aristotle_mdr import models as MDR

from aristotle_mdr.contrib.identifiers.models import ScopedIdentifier
from aristotle_mdr.contrib.slots.models import Slot
from aristotle_mdr.contrib.slots.utils import get_allowed_slots

import logging

from aristotle_mdr.contrib.generic.forms import (
    one_to_many_formset_excludes, one_to_many_formset_filters,
    ordered_formset_factory, ordered_formset_save,
)
from aristotle_mdr.contrib.generic.views import ExtraFormsetMixin


import re

logger = logging.getLogger(__name__)
logger.debug("Logging started for " + __name__)


class ConceptEditFormView(PermissionRequiredMixin):
    raise_exception = True
    redirect_unauthenticated_users = True
    object_level_permissions = True
    model = MDR._concept
    pk_url_kwarg = 'iid'

    def dispatch(self, request, *args, **kwargs):
        self.item = super().get_object().item
        self.model = self.item.__class__
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({'model': self.model._meta.model_name,
                        'app_label': self.model._meta.app_label,
                        'item': self.item})
        return context


class EditItemView(ExtraFormsetMixin, ConceptEditFormView, UpdateView):
    template_name = "aristotle_mdr/actions/advanced_editor.html"
    permission_required = "aristotle_mdr.user_can_edit"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slots_active = is_active_module('aristotle_mdr.contrib.slots')
        self.identifiers_active = is_active_module('aristotle_mdr.contrib.identifiers')

    def get_form_class(self):
        return MDRForms.wizards.subclassed_edit_modelform(self.model)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'instance': self.item,
        })
        return kwargs

    def get_extra_formsets(self, item=None, postdata=None):

        extra_formsets = super().get_extra_formsets(item, postdata)

        if self.slots_active:
            slot_formset = self.get_slots_formset()(
                queryset=Slot.objects.filter(concept=self.item.id),
                instance=self.item.concept,
                data=postdata
            )

            extra_formsets.append({
                'formset': slot_formset,
                'title': 'Slots',
                'type': 'slot',
                'saveargs': None
            })

        if self.identifiers_active:
            id_formset = self.get_identifier_formset()(
                queryset=ScopedIdentifier.objects.filter(concept=self.item.id),
                instance=self.item.concept,
                data=postdata
            )

            extra_formsets.append({
                'formset': id_formset,
                'title': 'Identifiers',
                'type': 'identifiers',
                'saveargs': None
            })

        return extra_formsets

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        extra_formsets = self.get_extra_formsets(self.item, request.POST)

        self.object = self.item

        if form.is_valid():
            item = form.save(commit=False)
            change_comments = form.data.get('change_comments', None)
            form_invalid = False
        else:
            form_invalid = True

        formsets_invalid = self.validate_formsets(extra_formsets)
        invalid = form_invalid or formsets_invalid

        if invalid:
            return self.form_invalid(form, formsets=extra_formsets)
        else:
            with transaction.atomic(), reversion.revisions.create_revision():

                # Save formsets
                self.save_formsets(extra_formsets)

                # save the change comments
                if not change_comments:
                    change_comments = construct_change_message_extra_formsets(request, form, extra_formsets)

                reversion.revisions.set_user(request.user)
                reversion.revisions.set_comment(change_comments)

                # Save item
                form.save_m2m()
                item.save()

            return HttpResponseRedirect(url_slugify_concept(self.item))

    def get_slots_formset(self):
        from aristotle_mdr.contrib.slots.forms import slot_inlineformset_factory
        return slot_inlineformset_factory()

    def get_identifier_formset(self):
        from aristotle_mdr.contrib.identifiers.forms import identifier_inlineformset_factory
        return identifier_inlineformset_factory()

    def form_invalid(self, form, formsets=None):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """

        return self.render_to_response(self.get_context_data(form=form, formsets=formsets))

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)

        if 'formsets' in kwargs:
            extra_formsets = kwargs['formsets']
        else:
            extra_formsets = self.get_extra_formsets(self.item)

        fscontext = self.get_formset_context(extra_formsets)
        context.update(fscontext)

        context['show_slots_tab'] = self.slots_active
        context['show_id_tab'] = self.identifiers_active

        return context


class CloneItemView(ConceptEditFormView, DetailView, CreateView):
    template_name = "aristotle_mdr/create/clone_item.html"
    permission_required = "aristotle_mdr.user_can_view"

    def get_form_class(self):
        return MDRForms.wizards.subclassed_clone_modelform(self.model)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'initial': concept_to_clone_dict(self.item)
        })
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            with transaction.atomic(), reversion.revisions.create_revision():
                new_clone = form.save(commit=False)
                new_clone.submitter = self.request.user
                new_clone.save()
                reversion.revisions.set_user(self.request.user)
                reversion.revisions.set_comment("Cloned from %s (id: %s)" % (self.item.name, str(self.item.pk)))
                return HttpResponseRedirect(url_slugify_concept(new_clone))
        else:
            return self.form_invalid(form)
