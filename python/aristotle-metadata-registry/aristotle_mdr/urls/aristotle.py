from django.conf.urls import url
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy

from haystack.views import search_view_factory

import aristotle_mdr.views as views
import aristotle_mdr.forms as forms
import aristotle_mdr.models as models
from aristotle_mdr.contrib.generic.views import (
    GenericAlterOneToManyView,
    GenericAlterManyToManyView,
    GenericAlterManyToManyOrderView,
    generic_foreign_key_factory_view
)

from django.utils.translation import ugettext_lazy as _


urlpatterns=[
    url(r'^$', views.SmartRoot.as_view(
        unauthenticated_pattern='aristotle_mdr:home',
        authenticated_pattern='aristotle_mdr:userHome'
    ), name='smart_root'),
    url(r'^home/?$', TemplateView.as_view(template_name='aristotle_mdr/static/home.html'), name="home"),
    url(r'^manifest.json$', TemplateView.as_view(template_name='meta/manifest.json', content_type='application/json')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='meta/robots.txt', content_type='text/plain')),
    url(r'^sitemap.xml$', views.sitemaps.main, name='sitemap_xml'),
    url(r'^sitemaps/sitemap_(?P<page>[0-9]+).xml$', views.sitemaps.page_range, name='sitemap_range_xml'),

    # all the below take on the same form:
    # url(r'^itemType/(?P<iid>\d+)?/?
    # Allowing for a blank ItemId (iid) allows aristotle to redirect to /about/itemtype instead of 404ing

    url(r'^valuedomain/(?P<iid>\d+)?/edit/values/permissible/?$',
        GenericAlterOneToManyView.as_view(
            model_base=models.ValueDomain,
            model_to_add=models.PermissibleValue,
            model_base_field='permissiblevalue_set',
            model_to_add_field='valueDomain',
            ordering_field='order',
            form_add_another_text=_('Add a code'),
            form_title=_('Change Permissible Values'),
        ), name='permsissible_values_edit'),
    url(r'^valuedomain/(?P<iid>\d+)?/edit/values/supplementary/?$',
        GenericAlterOneToManyView.as_view(
            model_base=models.ValueDomain,
            model_to_add=models.SupplementaryValue,
            model_base_field='supplementaryvalue_set',
            model_to_add_field='valueDomain',
            ordering_field='order',
            form_add_another_text=_('Add a code'),
            form_title=_('Change Supplementary Values')
        ), name='supplementary_values_edit'),
    url(r'^conceptualdomain/(?P<iid>\d+)?/edit/values/?$',
        GenericAlterOneToManyView.as_view(
            model_base=models.ConceptualDomain,
            model_to_add=models.ValueMeaning,
            model_base_field='valuemeaning_set',
            model_to_add_field='conceptual_domain',
            ordering_field='order',
            form_add_another_text=_('Add a value meaning'),
            form_title=_('Change Value Meanings')
        ), name='value_meanings_edit'),
    url(r'^item/(?P<iid>\d+)/dataelementderivation/change_inputs/?$',
        GenericAlterManyToManyOrderView.as_view(
            model_base=models.DataElementDerivation,
            model_to_add=models.DataElement,
            model_base_field='inputs'
        ), name='dataelementderivation_change_inputs'),
    url(r'^item/(?P<iid>\d+)/dataelementderivation/change_derives/?$',
        GenericAlterManyToManyOrderView.as_view(
            model_base=models.DataElementDerivation,
            model_to_add=models.DataElement,
            model_base_field='derives'
        ), name='dataelementderivation_change_derives'),

    url(r'^item/(?P<iid>\d+)?/alter_relationship/(?P<fk_field>[A-Za-z\-_]+)/?$',
        generic_foreign_key_factory_view,
        name='generic_foreign_key_editor'),


    url(r'^workgroup/(?P<iid>\d+)(?:-(?P<name_slug>[A-Za-z0-9\-_]+))?/?$', views.workgroups.WorkgroupView.as_view(), name='workgroup'),
    url(r'^workgroup/(?P<iid>\d+)/members/?$', views.workgroups.MembersView.as_view(), name='workgroupMembers'),
    url(r'^workgroup/(?P<iid>\d+)/items/?$', views.workgroups.ItemsView.as_view(), name='workgroupItems'),
    url(r'^workgroup/(?P<iid>\d+)/leave/?$', views.workgroups.LeaveView.as_view(), name='workgroup_leave'),
    url(r'^workgroup/(?P<iid>\d+)/add_member$', views.workgroups.AddMembersView.as_view(), name='addWorkgroupMembers'),
    url(r'^workgroup/(?P<iid>\d+)/change_roles/(?P<user_pk>\d+)/?$', views.workgroups.ChangeUserRoles.as_view(), name='workgroup_member_change_role'),
    url(r'^workgroup/(?P<iid>\d+)/remove/(?P<user_pk>\d+)/?$', views.workgroups.RemoveUser.as_view(), name='workgroup_member_remove'),
    url(r'^workgroup/(?P<iid>\d+)/archive/?$', views.workgroups.ArchiveView.as_view(), name='archive_workgroup'),
    url(r'^workgroup/(?P<iid>\d+)/edit$', views.workgroups.EditWorkgroup.as_view(), name='workgroup_edit'),
    url(r'^workgroups/create/?$', views.workgroups.CreateWorkgroup.as_view(), name='workgroup_create'),
    url(r'^workgroups/all/?$', views.workgroups.ListWorkgroup.as_view(), name='workgroup_list'),


    url(r'^discussions/?$', views.discussions.All.as_view(), name='discussions'),
    url(r'^discussions/new/?$', views.discussions.New.as_view(), name='discussionsNew'),
    url(r'^discussions/workgroup/(?P<wgid>\d+)/?$', views.discussions.Workgroup.as_view(), name='discussionsWorkgroup'),
    url(r'^discussions/post/(?P<pid>\d+)/?$', views.discussions.Post.as_view(), name='discussionsPost'),
    url(r'^discussions/post/(?P<pid>\d+)/newcomment/?$', views.discussions.NewComment.as_view(), name='discussionsPostNewComment'),
    url(r'^discussions/delete/comment/(?P<cid>\d+)/?$', views.discussions.DeleteComment.as_view(), name='discussionsDeleteComment'),
    url(r'^discussions/delete/post/(?P<pid>\d+)/?$', views.discussions.DeletePost.as_view(), name='discussionsDeletePost'),
    url(r'^discussions/edit/comment/(?P<cid>\d+)/?$', views.discussions.EditComment.as_view(), name='discussionsEditComment'),
    url(r'^discussions/edit/post/(?P<pid>\d+)/?$', views.discussions.EditPost.as_view(), name='discussionsEditPost'),
    url(r'^discussions/post/(?P<pid>\d+)/toggle/?$', views.discussions.TogglePost.as_view(), name='discussionsPostToggle'),

    # url(r'^item/(?P<iid>\d+)/?$', views.items.concept, name='item'),
    url(r'^item/(?P<iid>\d+)/edit/?$', views.editors.EditItemView.as_view(), name='edit_item'),
    url(r'^item/(?P<iid>\d+)/clone/?$', views.editors.CloneItemView.as_view(), name='clone_item'),
    url(r'^item/(?P<iid>\d+)/history/?$', views.ConceptHistoryCompareView.as_view(), name='item_history'),
    url(r'^item/(?P<iid>\d+)/registrationHistory/?$', views.registrationHistory, name='registrationHistory'),
    url(r'^item/(?P<iid>\d+)/child_states/?$', views.actions.CheckCascadedStates.as_view(), name='check_cascaded_states'),

    url(r'^item/(?P<iid>\d+)(?:\/(?P<model_slug>\w+)\/(?P<name_slug>.+))?/?$', views.concept, name='item'),
    url(r'^item/(?P<iid>\d+)(?:\/.*)?$', views.concept, name='item'),  # Catch every other 'item' URL and throw it for a redirect
    url(r'^item/(?P<uuid>[\w-]+)/?(.*)?$', views.concept_by_uuid, name='item_uuid'),

    url(r'^unmanaged/measure/(?P<iid>\d+)(?:\/(?P<model_slug>\w+)\/(?P<name_slug>.+))?/?$', views.measure, name='measure'),

    # url(r'^create/?$', views.item, name='item'),
    url(r'^create/?$', views.create_list, name='create_list'),
    url(r'^create/wizard/aristotle_mdr/dataelementconcept$', views.wizards.DataElementConceptWizard.as_view(), name='createDataElementConcept'),
    url(r'^create/wizard/aristotle_mdr/dataelement$', views.wizards.DataElementWizard.as_view(), name='createDataElement'),
    url(r'^create/(?P<app_label>.+)/(?P<model_name>.+)/?$', views.wizards.create_item, name='createItem'),
    url(r'^create/(?P<model_name>.+)/?$', views.wizards.create_item, name='createItem'),

    url(r'^download/bulk/(?P<download_type>[a-zA-Z0-9\-\.]+)/?$', views.downloads.bulk_download, name='bulk_download'),
    url(r'^download/(?P<download_type>[a-zA-Z0-9\-\.]+)/(?P<iid>\d+)/?$', views.downloads.download, name='download'),

    url(r'^action/supersede/(?P<iid>\d+)$', views.supersede, name='supersede'),
    url(r'^action/deprecate/(?P<iid>\d+)$', views.deprecate, name='deprecate'),
    url(r'^action/bulkaction/?$', views.bulk_actions.BulkAction.as_view(), name='bulk_action'),
    url(r'^action/bulkaction/state/?$', views.bulk_actions.ChangeStatusBulkActionView.as_view(), name='change_state_bulk_action'),
    url(r'^action/compare/?$', views.comparator.compare_concepts, name='compare_concepts'),

    url(r'^action/changestatus/(?P<iid>\d+)$', views.ChangeStatusView.as_view(), name='changeStatus'),
    # url(r'^remove/WorkgroupUser/(?P<iid>\d+)/(?P<userid>\d+)$', views.removeWorkgroupUser, name='removeWorkgroupUser'),

    url(r'^account/?$', RedirectView.as_view(url=reverse_lazy("aristotle:userHome"), permanent=True)),
    url(r'^account/home/?$', views.user_pages.home, name='userHome'),
    url(r'^account/sandbox/?$', views.user_pages.CreatedItemsListView.as_view(), name='userSandbox'),
    url(r'^account/sandbox/delete/?$', views.actions.DeleteSandboxView.as_view(), name="sandbox_delete"),
    url(r'^account/roles/?$', views.user_pages.roles, name='userRoles'),
    url(r'^account/admin/?$', views.user_pages.admin_tools, name='userAdminTools'),
    url(r'^account/admin/statistics/?$', views.user_pages.admin_stats, name='userAdminStats'),
    url(r'^account/edit/?$', views.user_pages.EditView.as_view(), name='userEdit'),
    url(r'^account/profile/?$', views.user_pages.ProfileView.as_view(), name='userProfile'),
    url(r'^account/recent/?$', views.user_pages.recent, name='userRecentItems'),
    url(r'^account/favourites/?$', views.user_pages.favourites, name='userFavourites'),
    url(r'^account/reviews/?$', views.user_pages.my_review_list, name='userMyReviewRequests'),
    url(r'^account/reviews/cancel/(?P<review_id>\d+)/?$', views.actions.ReviewCancelView.as_view(), name='userReviewCancel'),
    url(r'^account/workgroups/?$', views.user_pages.MyWorkgroupList.as_view(), name='userWorkgroups'),
    url(r'^account/workgroups/archives/?$', views.user_pages.WorkgroupArchiveList.as_view(), name='user_workgroups_archives'),
    url(r'^account/notifications(?:/folder/(?P<folder>all))?/?$', views.user_pages.inbox, name='userInbox'),
    url(r'^account/notifications/api/mark-all-as-read/', views.notify.MarkAllReadApiView.as_view(), name='api_mark_all_read'),

    url(r'^account/django/(.*)?$', views.user_pages.django_admin_wrapper, name='django_admin'),


    url(r'^action/review/(?P<iid>\d+)?$', views.actions.SubmitForReviewView.as_view(), name='request_review'),
    url(r'^account/registrartools/?$', views.user_pages.RegistrarTools.as_view(), name='userRegistrarTools'),
    url(r'^account/registrartools/review/?$', views.user_pages.review_list, name='userReadyForReview'),
    url(r'^account/registrartools/review/details/(?P<review_id>\d+)/?$', views.user_pages.ReviewDetailsView.as_view(), name='userReviewDetails'),
    url(r'^account/registrartools/review/accept/(?P<review_id>\d+)/?$', views.actions.ReviewAcceptView.as_view(), name='userReviewAccept'),
    url(r'^account/registrartools/review/reject/(?P<review_id>\d+)/?$', views.actions.ReviewRejectView.as_view(), name='userReviewReject'),


    url(r'^registrationauthority/create/?$', views.registrationauthority.CreateRegistrationAuthority.as_view(), name='registrationauthority_create'),
    url(r'^registrationauthority/all/?$', views.registrationauthority.ListRegistrationAuthority.as_view(), name='registrationauthority_list'),

    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/details/$', views.registrationauthority.DetailsRegistrationAuthority.as_view(), name='registrationauthority_details'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/members/$', views.registrationauthority.MembersRegistrationAuthority.as_view(), name='registrationauthority_members'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/edit', views.registrationauthority.EditRegistrationAuthority.as_view(), name='registrationauthority_edit'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/add_user/?$', views.registrationauthority.AddUser.as_view(), name='registrationauthority_add_user'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/change_roles/(?P<user_pk>.+)?/?$', views.registrationauthority.ChangeUserRoles.as_view(), name='registrationauthority_change_user_roles'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/remove/(?P<user_pk>\d+)/?$', views.registrationauthority.RemoveUser.as_view(), name='registrationauthority_member_remove'),
    url(r'^organization/registrationauthority/(?P<iid>\d+)(?:\/(?P<name_slug>.+))?/?$', views.registrationauthority.registrationauthority, name='registrationAuthority'),

    url(r'^organization/(?P<iid>\d+)?(?:\/(?P<name_slug>.+))?/?$', views.registrationauthority.organization, name='organization'),
    url(r'^organizations/?$', views.registrationauthority.all_organizations, name='all_organizations'),
    url(r'^registrationauthorities/?$', views.registrationauthority.all_registration_authorities, name='all_registration_authorities'),

    url(r'^account/toggleFavourite/(?P<iid>\d+)/?$', views.toggleFavourite, name='toggleFavourite'),

    url(r'^extensions/?$', views.extensions, name='extensions'),

    url(r'^notifyredirect/(?P<content_type>\d+)/(?P<object_id>\d+)/', views.notification_redirect, name="notify_redirect"),

    url(r'^about/aristotle/?$', TemplateView.as_view(template_name='aristotle_mdr/static/aristotle_mdr.html'), name="aboutMain"),
    url(r'^about/(?P<template>.+)/?$', views.DynamicTemplateView.as_view(), name="about"),

    url(r'^accessibility/?$', TemplateView.as_view(template_name='aristotle_mdr/static/accessibility.html'), name="accessibility"),

    url(r'user/(?P<uid>\d+)/profilePicture.svg', views.user_pages.profile_picture, name="dynamic_profile_picture"),

    url(
        r'^search/?$',
        search_view_factory(
            view_class=views.PermissionSearchView,
            template='search/search.html',
            searchqueryset=None,
            form_class=forms.search.PermissionSearchForm
            ),
        name='search'
    ),
]
