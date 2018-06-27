from braces.views import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from django.views.generic import CreateView, ListView, DetailView, UpdateView

from aristotle_mdr import models as MDR
from aristotle_mdr import forms as MDRForms
from aristotle_mdr.views.utils import (
    paginated_registration_authority_list,
    RoleChangeView,
    MemberRemoveFromGroupView
)

import logging

logger = logging.getLogger(__name__)
logger.debug("Logging started for " + __name__)


def registrationauthority(request, iid, *args, **kwargs):
    if iid is None:
        return redirect(reverse("aristotle_mdr:all_registration_authorities"))
    item = get_object_or_404(MDR.RegistrationAuthority, pk=iid).item

    return render(request, item.template, {'item': item.item})


def organization(request, iid, *args, **kwargs):
    if iid is None:
        return redirect(reverse("aristotle_mdr:all_organizations"))
    item = get_object_or_404(MDR.Organization, pk=iid).item

    return render(request, item.template, {'item': item.item})


def all_registration_authorities(request):
    ras = MDR.RegistrationAuthority.objects.order_by('name')
    return render(request, "aristotle_mdr/organization/all_registration_authorities.html", {'registrationAuthorities': ras})


def all_organizations(request):
    orgs = MDR.Organization.objects.order_by('name')
    return render(request, "aristotle_mdr/organization/all_organizations.html", {'organization': orgs})


class CreateRegistrationAuthority(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    template_name = "aristotle_mdr/user/registration_authority/add.html"
    fields = ['name', 'definition']
    permission_required = "aristotle_mdr.add_registration_authority"
    raise_exception = True
    redirect_unauthenticated_users = True
    model = MDR.RegistrationAuthority

    def get_success_url(self):
        return reverse('aristotle:registrationauthority_details', kwargs={'iid': self.object.id})


class AddUser(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    # TODO: Replace UpdateView with DetailView, FormView
    # This is required for Django 1.8 only.

    template_name = "aristotle_mdr/user/registration_authority/add_user.html"
    permission_required = "aristotle_mdr.change_registrationauthority_memberships"
    raise_exception = True
    redirect_unauthenticated_users = True
    form_class = MDRForms.actions.AddRegistrationUserForm

    model = MDR.RegistrationAuthority
    pk_url_kwarg = 'iid'
    context_object_name = "item"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})

        # TODO: Not happy about this as its not an updateForm
        kwargs.pop('instance')
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(MDR.RegistrationAuthority, pk=self.kwargs.get('iid'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Insert the single object into the context dict.
        """
        kwargs = super().get_context_data(**kwargs)
        kwargs.update({'item': self.item})
        return kwargs

    def form_valid(self, form):
        user = form.cleaned_data['user']
        for role in form.cleaned_data['roles']:
            self.item.giveRoleToUser(role, user)

        return redirect(reverse('aristotle:registrationauthority_members', args=[self.item.id]))


class ListRegistrationAuthority(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/list_all.html"
    permission_required = "aristotle_mdr.is_registry_administrator"
    raise_exception = True
    redirect_unauthenticated_users = True

    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        ras = MDR.RegistrationAuthority.objects.all()

        text_filter = request.GET.get('filter', "")
        if text_filter:
            ras = ras.filter(Q(name__icontains=text_filter) | Q(definition__icontains=text_filter))
        context = {'filter': text_filter}
        return paginated_registration_authority_list(request, ras, self.template_name, context)


class DetailsRegistrationAuthority(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/details.html"
    permission_required = "aristotle_mdr.view_registrationauthority_details"
    raise_exception = True
    redirect_unauthenticated_users = True

    pk_url_kwarg = 'iid'
    context_object_name = "item"


class MembersRegistrationAuthority(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/members.html"
    permission_required = "aristotle_mdr.view_registrationauthority_details"
    raise_exception = True
    redirect_unauthenticated_users = True

    pk_url_kwarg = 'iid'
    context_object_name = "item"


class EditRegistrationAuthority(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/edit.html"
    permission_required = "aristotle_mdr.change_registrationauthority"
    raise_exception = True
    redirect_unauthenticated_users = True
    object_level_permissions = True

    fields = [
        'name',
        'definition',
        'locked_state',
        'public_state',
        'notprogressed',
        'incomplete',
        'candidate',
        'recorded',
        'qualified',
        'standard',
        'preferred',
        'superseded',
        'retired',
    ]

    pk_url_kwarg = 'iid'
    context_object_name = "item"


class ChangeUserRoles(RoleChangeView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/change_role.html"
    permission_required = "aristotle_mdr.change_registrationauthority_memberships"
    form_class = MDRForms.actions.ChangeRegistrationUserRolesForm
    pk_url_kwarg = 'iid'
    context_object_name = "item"

    def get_success_url(self):
        return redirect(reverse('aristotle:registrationauthority_members', args=[self.get_object().id]))


class RemoveUser(MemberRemoveFromGroupView):
    model = MDR.RegistrationAuthority
    template_name = "aristotle_mdr/user/registration_authority/remove_member.html"
    permission_required = "aristotle_mdr.change_registrationauthority_memberships"
    pk_url_kwarg = 'iid'
    context_object_name = "item"

    def get_success_url(self):
        return redirect(reverse('aristotle:registrationauthority_members', args=[self.get_object().id]))
