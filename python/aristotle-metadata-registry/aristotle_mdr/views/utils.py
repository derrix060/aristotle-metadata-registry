from braces.views import LoginRequiredMixin, PermissionRequiredMixin

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from django.views.generic.detail import BaseDetailView
from django.views.generic import (
    DetailView, FormView, ListView
)

from aristotle_mdr import models as MDR

paginate_sort_opts = {
    "mod_asc": ["modified"],
    "mod_desc": ["-modified"],
    "cre_asc": ["created"],
    "cre_desc": ["-created"],
    "name_asc": [Lower("name").asc()],
    "name_desc": [Lower("name").desc()],
}


@login_required
def paginated_list(request, items, template, extra_context={}):
    if hasattr(items, 'select_subclasses'):
        items = items.select_subclasses()
    sort_by=request.GET.get('sort', "mod_desc")
    if sort_by not in paginate_sort_opts.keys():
        sort_by="mod_desc"

    paginator = Paginator(
        items.order_by(*paginate_sort_opts.get(sort_by)),
        request.GET.get('pp', 20)  # per page
    )

    page = request.GET.get('page')
    try:
        paged_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paged_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        paged_items = paginator.page(paginator.num_pages)
    context = {
        'object_list': items,
        'sort': sort_by,
        'page': paged_items,
        }
    context.update(extra_context)
    return render(request, template, context)


@login_required
def paginated_reversion_list(request, items, template, extra_context={}):

    paginator = Paginator(
        items,
        request.GET.get('pp', 20)  # per page
    )

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    context = {
        'page': items,
        }
    context.update(extra_context)
    return render(request, template, context)


paginate_workgroup_sort_opts = {
    "users": ("user_count", lambda qs: qs.annotate(user_count=Count('viewers'))),
    "items": ("item_count", lambda qs: qs.annotate(item_count=Count('items'))),
    "name": "name",
}


@login_required
def paginated_workgroup_list(request, workgroups, template, extra_context={}):
    sort_by=request.GET.get('sort', "name_desc")
    try:
        sorter, direction = sort_by.split('_')
        if sorter not in paginate_workgroup_sort_opts.keys():
            sorter="name"
            sort_by = "name_desc"
        direction = {'asc': '', 'desc': '-'}.get(direction, '')
    except:
        sorter, direction = 'name', ''

    opts = paginate_workgroup_sort_opts.get(sorter)
    qs = workgroups

    try:
        sort_field, extra = opts
        qs = extra(qs)
    except:
        sort_field = opts

    qs = qs.order_by(direction + sort_field)
    paginator = Paginator(
        qs,
        request.GET.get('pp', 20)  # per page
    )

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    context = {
        'sort': sort_by,
        'page': items,
        }
    context.update(extra_context)
    return render(request, template, context)


paginate_registration_authority_sort_opts = {
    "name": "name",
    "users": ("user_count", lambda qs: qs.annotate(user_count=Count('registrars') + Count('managers'))),
}


@login_required
def paginated_registration_authority_list(request, ras, template, extra_context={}):
    sort_by=request.GET.get('sort', "name_desc")
    try:
        sorter, direction = sort_by.split('_')
        if sorter not in paginate_registration_authority_sort_opts.keys():
            sorter="name"
            sort_by = "name_desc"
        direction = {'asc': '', 'desc': '-'}.get(direction, '')
    except:
        sorter, direction = 'name', ''

    opts = paginate_registration_authority_sort_opts.get(sorter)
    qs = ras

    try:
        sort_field, extra = opts
        qs = extra(qs)
    except:
        sort_field = opts

    qs = qs.order_by(direction + sort_field)
    qs = qs.annotate(user_count=Count('registrars') + Count('managers'))
    paginator = Paginator(
        qs,
        request.GET.get('pp', 20)  # per page
    )

    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)
    context = {
        'sort': sort_by,
        'page': items,
        }

    context.update(extra_context)
    return render(request, template, context)


def workgroup_item_statuses(workgroup):
    from aristotle_mdr.models import STATES

    raw_counts = workgroup.items.filter(
        Q(statuses__until_date__gte=timezone.now()) |
        Q(statuses__until_date__isnull=True)
    ).values_list('statuses__state').annotate(num=Count('id'))

    counts = []
    for state, count in raw_counts:
        if state is None:
            state = _("Not registered")
        else:
            state = STATES[state]
        counts.append((state, count))
    return counts


def generate_visibility_matrix(user):
    matrix={}

    from aristotle_mdr.models import STATES

    for ra in user.profile.registrarAuthorities:
        ra_matrix = {'name': ra.name, 'states': {}}
        for s, name in STATES:
            if s >= ra.public_state:
                ra_matrix['states'][s] = "public"
            elif s >= ra.locked_state:
                ra_matrix['states'][s] = "locked"
            else:
                ra_matrix['states'][s] = "hidden"
        matrix[ra.id] = ra_matrix
    return matrix


class SortedListView(ListView):
    """
    Can be used to replace current paginated fucntion views,
    while retaining the template

    allowed_sorts can be a dict mapping names to sorts or just a list of sorts
    """

    allowed_sorts = []
    default_sort = ''

    def dispatch(self, request, *args, **kwargs):
        self.text_filter = request.GET.get('filter', "")
        self.sort = request.GET.get('sort', "")
        return super().dispatch(request, *args, **kwargs)

    def sort_queryset(self, queryset):
        # To be used in get_queryset
        sort = ''
        asc = True
        if self.sort:
            if '_' in self.sort:
                parts = self.sort.split('_')
                sort = parts[0]
                if parts[1] == 'desc':
                    asc = False
            else:
                sort = self.sort

            if sort in self.allowed_sorts:

                if type(self.allowed_sorts) == dict:
                    sort = self.allowed_sorts[sort]

                if not asc:
                    sort = '-' + sort

                return queryset.order_by(sort)

        if not self.default_sort:
            return queryset
        else:
            return queryset.order_by(self.default_sort)

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'filter': self.text_filter,
            'page': context['page_obj'],
            'sort': self.sort
        })
        return context


class GenericListWorkgroup(LoginRequiredMixin, SortedListView):

    model = MDR.Workgroup
    redirect_unauthenticated_users = True
    paginate_by = 20

    allowed_sorts = {
        'items': 'items__count',
        'name': 'name',
        'users': 'viewers__count'
    }

    default_sort = 'name'

    def get_initial_queryset(self):
        raise NotImplementedError

    def get_queryset(self):
        workgroups = self.get_initial_queryset().annotate(Count('items')).annotate(Count('viewers'))
        workgroups = workgroups.prefetch_related('viewers', 'managers', 'submitters', 'stewards')

        if self.text_filter:
            workgroups = workgroups.filter(Q(name__icontains=self.text_filter) | Q(definition__icontains=self.text_filter))

        workgroups = self.sort_queryset(workgroups)
        return workgroups


class GroupMemberMixin(object):
    user_pk_kwarg = "user_pk"

    @cached_property
    def user_to_change(self):
        user = get_object_or_404(get_user_model(), pk=self.kwargs.get(self.user_pk_kwarg))
        if user not in self.get_object().members.all():
            raise Http404
        return user

    def get_context_data(self, **kwargs):
        """
        Insert the single object into the context dict.
        """
        kwargs = super().get_context_data(**kwargs)
        kwargs.update({'user_to_change': self.user_to_change})
        return kwargs


class RoleChangeView(GroupMemberMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseDetailView, FormView):
    raise_exception = True
    redirect_unauthenticated_users = True
    object_level_permissions = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        initial = {'roles': []}
        initial['roles'] = self.get_object().list_roles_for_user(self.user_to_change)

        kwargs.update({'initial': initial})
        return kwargs

    def form_valid(self, form):
        for role in self.model.roles:
            if role in form.cleaned_data['roles']:
                self.get_object().giveRoleToUser(role, self.user_to_change)
            else:
                self.get_object().removeRoleFromUser(role, self.user_to_change)

        return self.get_success_url()


class MemberRemoveFromGroupView(GroupMemberMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    raise_exception = True
    redirect_unauthenticated_users = True
    object_level_permissions = True

    http_method_names = ['get', 'post']

    def post(self, request, *args, **kwargs):
        for role in self.get_object().list_roles_for_user(self.user_to_change):
            self.get_object().removeRoleFromUser(role, self.user_to_change)
        return self.get_success_url()


class AlertFieldsMixin:
    """Provide a list of fields where help text should be rendered as an alert"""

    alert_fields = []

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({'alert_fields': self.alert_fields})
        return context
