from django.conf import settings
from django.urls import reverse
from django.test import TestCase, override_settings, tag
from django.utils import timezone
from django.db.models.fields import CharField, TextField

import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
import aristotle_mdr.contrib.identifiers.models as ident_models
from aristotle_mdr.utils import url_slugify_concept
from aristotle_mdr.forms.creation_wizards import (
    WorkgroupVerificationMixin,
    CheckIfModifiedMixin
)
from aristotle_mdr.tests import utils
import datetime

from aristotle_mdr.utils import setup_aristotle_test_environment

from aristotle_mdr.templatetags.aristotle_tags import get_dataelements_from_m2m


setup_aristotle_test_environment()


def setUpModule():
    from django.core.management import call_command
    call_command('load_aristotle_help', verbosity=0, interactive=False)


class AnonymousUserViewingThePages(TestCase):
    def test_homepage(self):
        response = self.client.get(reverse('aristotle:smart_root'))
        self.assertRedirects(response, reverse('aristotle:home'))

    def test_notifications_for_anon_users(self):
        response = self.client.get(reverse('aristotle:home'))
        self.assertEqual(response.status_code,200)
        # Make sure notifications library isn't loaded for anon users as they'll never have notifications.
        self.assertNotContains(response, "notifications/notify.js")
        # At some stage this might need a better test to check the 500 page doesn't show... after notifications is fixed.

    def test_sitemaps(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code,200)
        response = self.client.get("/sitemaps/sitemap_0.xml")
        self.assertEqual(response.status_code,200)

    def test_visible_item(self):
        wg = models.Workgroup.objects.create(name="Setup WG")
        ra = models.RegistrationAuthority.objects.create(name="Test RA")
        item = models.ObjectClass.objects.create(name="Test OC",workgroup=wg)
        s = models.Status.objects.create(
                concept=item,
                registrationAuthority=ra,
                registrationDate=timezone.now(),
                state=ra.locked_state
                )
        response = self.client.get(url_slugify_concept(item))
        # Anonymous users requesting a hidden page will be redirected to login
        self.assertEqual(response.status_code,302)
        s.state = ra.public_state
        s.save()
        response = self.client.get(url_slugify_concept(item))
        self.assertEqual(response.status_code,200)


class LoggedInViewHTMLPages(utils.LoggedInViewPages, TestCase):
    def test_homepage(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:smart_root'))
        self.assertRedirects(response, reverse('aristotle:userHome'))


class LoggedInViewConceptPages(utils.LoggedInViewPages, utils.FormsetTestUtils):
    defaults = {}
    def setUp(self):
        super().setUp()

        self.item1 = self.itemType.objects.create(
            name="Test Item 1 (visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg1,
            **self.defaults
        )
        self.item2 = self.itemType.objects.create(
            name="Test Item 2 (NOT visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg2,
            **self.defaults
        )
        self.item3 = self.itemType.objects.create(
            name="Test Item 3 (visible to tested viewers)",
            definition="my definition",
            workgroup=self.wg1,
            **self.defaults
        )

    # ---- utils ----

    def make_review_request(self, item, user):

        self.assertFalse(perms.user_can_view(user,item))
        self.item1.save()
        self.item1 = self.itemType.objects.get(pk=item.pk)

        review = models.ReviewRequest.objects.create(
            requester=self.su,registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(item)

        self.assertTrue(perms.user_can_view(user,item))
        self.assertTrue(perms.user_can_change_status(user,item))

    # ---- tests ----

    def test_su_can_view(self):
        self.login_superuser()
        response = self.client.get(self.get_page(self.item1))
        self.assertEqual(response.status_code,200)
        response = self.client.get(self.get_page(self.item2))
        self.assertEqual(response.status_code,200)

    def test_editor_can_view(self):
        self.login_editor()
        response = self.client.get(self.get_page(self.item1))
        self.assertEqual(response.status_code,200)
        response = self.client.get(self.get_page(self.item2))
        self.assertEqual(response.status_code,403)

    def test_viewer_can_view(self):
        self.login_viewer()
        response = self.client.get(self.get_page(self.item1))
        self.assertEqual(response.status_code,200)
        response = self.client.get(self.get_page(self.item2))
        self.assertEqual(response.status_code,403)

    def test_stubs_redirect_correctly(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:item',args=[self.item1.id]))
        self.assertRedirects(response,url_slugify_concept(self.item1))
        response = self.client.get(reverse('aristotle:item',args=[self.item1.id])+"/not-a-model/fake-name")
        self.assertRedirects(response,url_slugify_concept(self.item1))
        response = self.client.get(reverse('aristotle:item',args=[self.item1.id])+"/this-isnt-even-a-proper-stub")
        self.assertRedirects(response,url_slugify_concept(self.item1))

    def test_uuids_redirect_correctly(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:item_uuid',args=[self.item1.id]))
        self.assertRedirects(response,url_slugify_concept(self.item1))

    def test_anon_cannot_view_edit_page(self):
        self.logout()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,302)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,302)
    def test_viewer_cannot_view_edit_page(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
    def test_submitter_can_view_edit_page(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        form = response.context['form']
        self.assertTrue('change_comments' in form.fields)

        response = self.client.get(reverse('aristotle:edit_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_regular_can_view_own_items_edit_page(self):
        self.login_regular_user()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
        self.regular_item = self.itemType.objects.create(name="regular item",definition="my definition", submitter=self.regular,**self.defaults)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.regular_item.id]))
        self.assertEqual(response.status_code,200)

    def test_regular_can_save_via_edit_page(self):
        self.login_regular_user()
        self.regular_item = self.itemType.objects.create(name="regular item",definition="my definition", submitter=self.regular,**self.defaults)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.regular_item.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name
        response = self.client.post(reverse('aristotle:edit_item',args=[self.regular_item.id]), updated_item)
        self.regular_item = self.itemType.objects.get(pk=self.regular_item.pk)
        self.assertRedirects(response,url_slugify_concept(self.regular_item))
        self.assertEqual(self.regular_item.name,updated_name)

    def test_submitter_can_save_via_edit_page(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.name,updated_name)

    def test_submitter_can_save_item_with_no_workgroup_via_edit_page(self):
        self.login_editor()
        self.item1 = self.itemType.objects.create(name="Test Item 1 (visible to tested viewers)",submitter=self.editor,definition="my definition",**self.defaults)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.name,updated_name)
        self.assertEqual(self.item1.workgroup,None)

    def test_submitter_can_save_via_edit_page_with_change_comment(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name
        change_comment = "I changed this because I can"
        updated_item['change_comments'] = change_comment
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)

        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.name,updated_name)

        response = self.client.get(reverse('aristotle:item_history',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response, change_comment)

    def test_submitter_can_save_via_edit_page_with_slots(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.slots.count(),0)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name

        formset_data = [
            {
                'concept': self.item1.pk,
                'name': 'extra',
                'type': 'string',
                'value': 'test slot value',
                'order': 0,
                'permission': 0,
            },
            {
                'concept': self.item1.pk,
                'name': 'more_extra',
                'type': 'string',
                'value': 'an even better test slot value',
                'order': 1,
                'permission': 0,
            }
        ]
        slot_formset_data = self.get_formset_postdata(formset_data, 'slots')

        updated_item.update(slot_formset_data)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)

        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.slots.count(),2)

        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertContains(response, 'test slot value')
        self.assertContains(response, 'an even better test slot value')

        slots = self.item1.slots.all()
        self.assertEqual(slots[0].name, 'extra')
        self.assertEqual(slots[0].order, 0)
        self.assertEqual(slots[1].name, 'more_extra')
        self.assertEqual(slots[1].order, 1)

    def test_submitter_can_save_via_edit_page_with_identifiers(self):

        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.slots.count(),0)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name

        namespace = ident_models.Namespace.objects.create(
            naming_authority=self.ra,
            shorthand_prefix='pre'
        )

        formset_data = [
            {
                'concept': self.item1.pk,
                'namespace': namespace.pk,
                'identifier': 'YE',
                'version': 1,
                'order': 0
            },
            {
                'concept': self.item1.pk,
                'namespace': namespace.pk,
                'identifier': 'RE',
                'version': 1,
                'order': 1
            }
        ]
        ident_formset_data = self.get_formset_postdata(formset_data, 'identifiers')

        updated_item.update(ident_formset_data)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)

        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.identifiers.count(),2)

        response = self.client.get(reverse('aristotle:item',args=[self.item1.id]), follow=True)
        self.assertContains(response, 'pre</a>/YE/1')
        self.assertContains(response, 'pre</a>/RE/1')

        idents = self.item1.identifiers.all()
        self.assertEqual(idents[0].identifier, 'YE')
        self.assertEqual(idents[0].order, 0)
        self.assertEqual(idents[1].identifier, 'RE')
        self.assertEqual(idents[1].order, 1)

    def test_submitter_cannot_save_via_edit_page_if_other_saves_made(self):
        from datetime import timedelta
        self.login_editor()
        modified = self.item1.modified
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        # fake that we fetched the page seconds before modification
        updated_item = utils.model_to_dict_with_change_time(response.context['item'],fetch_time=modified-timedelta(seconds=5))
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name
        change_comment = "I changed this because I can"
        updated_item['change_comments'] = change_comment
        time_before_response = timezone.now()
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)

        self.assertEqual(response.status_code,200)
        form = response.context['form']
        self.assertTrue(form.errors['last_fetched'][0] == CheckIfModifiedMixin.modified_since_form_fetched_error)

        # When sending a response with a bad last_fetch, the new one should come back right
        self.assertTrue(time_before_response < form.fields['last_fetched'].initial)

        # With the new last_fetched we can submit ok!
        updated_item['last_fetched'] = form.fields['last_fetched'].initial
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,302)


        updated_item.pop('last_fetched')
        time_before_response = timezone.now()
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)

        self.assertEqual(response.status_code,200)
        form = response.context['form']
        self.assertTrue(form.errors['last_fetched'][0] == CheckIfModifiedMixin.modified_since_field_missing)
        # When sending a response with no last_fetch, the new one should come back right
        self.assertTrue(time_before_response < form.fields['last_fetched'].initial)

        # With the new last_fetched we can submit ok!
        updated_item['last_fetched'] = form.fields['last_fetched'].initial
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,302)

    # Test if workgroup-moving settings work

    @override_settings(ARISTOTLE_SETTINGS=dict(settings.ARISTOTLE_SETTINGS, WORKGROUP_CHANGES=[]))
    def test_submitter_cannot_change_workgroup_via_edit_page(self):
        # based on the idea that 'submitter' is not set in ARISTOTLE_SETTINGS.WORKGROUP
        self.wg_other = models.Workgroup.objects.create(name="Test WG to move to")
        self.wg_other.submitters.add(self.editor)

        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])

        updated_item['workgroup'] = str(self.wg_other.pk)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        form = response.context['form']

        self.assertTrue('workgroup' in form.errors.keys())
        self.assertTrue(len(form.errors['workgroup'])==1)

        # Submitter is logged in, tries to move item - fails because
        self.assertFalse(perms.user_can_remove_from_workgroup(self.editor,self.item1.workgroup))
        self.assertTrue(form.errors['workgroup'][0] == WorkgroupVerificationMixin.cant_move_any_permission_error)

        updated_item['workgroup'] = str(self.wg2.pk)
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        form = response.context['form']

        self.assertTrue('workgroup' in form.errors.keys())
        self.assertTrue(len(form.errors['workgroup'])==1)

        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])

    @override_settings(ARISTOTLE_SETTINGS=dict(settings.ARISTOTLE_SETTINGS, WORKGROUP_CHANGES=['submitter']))
    def test_submitter_can_change_workgroup_via_edit_page(self):
        # based on the idea that 'submitter' is set in ARISTOTLE_SETTINGS.WORKGROUP
        self.wg_other = models.Workgroup.objects.create(name="Test WG to move to")

        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_item['workgroup'] = str(self.wg_other.pk)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        form = response.context['form']

        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])

        self.wg_other.submitters.add(self.editor)

        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)

        self.assertEqual(response.status_code,302)
        updated_item['workgroup'] = str(self.wg2.pk)
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])


    @override_settings(ARISTOTLE_SETTINGS=dict(settings.ARISTOTLE_SETTINGS, WORKGROUP_CHANGES=['admin']))
    def test_admin_can_change_workgroup_via_edit_page(self):
        # based on the idea that 'admin' is set in ARISTOTLE_SETTINGS.WORKGROUP
        self.wg_other = models.Workgroup.objects.create(name="Test WG to move to")

        self.login_superuser()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict_with_change_time(self.item1)
        updated_item['workgroup'] = str(self.wg_other.pk)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,302)

        updated_item = utils.model_to_dict_with_change_time(self.item1)
        updated_item['workgroup'] = str(self.wg2.pk)
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,302)


    @override_settings(ARISTOTLE_SETTINGS=dict(settings.ARISTOTLE_SETTINGS, WORKGROUP_CHANGES=['manager']))
    def test_manager_of_two_workgroups_can_change_workgroup_via_edit_page(self):
        # based on the idea that 'manager' is set in ARISTOTLE_SETTINGS.WORKGROUP
        self.wg_other = models.Workgroup.objects.create(name="Test WG to move to")
        self.wg_other.submitters.add(self.editor)

        self.login_editor()
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_item['workgroup'] = str(self.wg_other.pk)
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        form = response.context['form']
        # Submitter can't move because they aren't a manager of any workgroups.
        self.assertTrue(form.errors['workgroup'][0] == WorkgroupVerificationMixin.cant_move_any_permission_error)

        self.wg_other.managers.add(self.editor)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        form = response.context['form']
        # Submitter can't move because they aren't a manager of the workgroup the item is in.
        self.assertTrue(form.errors['workgroup'][0] == WorkgroupVerificationMixin.cant_move_from_permission_error)


        self.login_manager()

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,403)

        self.wg1.submitters.add(self.manager) # Need to give manager edit permission to allow them to actually edit things
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)
        form = response.context['form']

        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])

        self.wg_other.managers.add(self.manager)

        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)
        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])

        self.wg_other.submitters.add(self.manager) # Need to give manager edit permission to allow them to actually edit things
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,302)

        updated_item['workgroup'] = str(self.wg2.pk)
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.assertEqual(response.status_code,200)

        self.assertTrue('Select a valid choice.' in form.errors['workgroup'][0])

    def test_anon_cannot_view_clone_page(self):
        self.logout()
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,302)
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,302)

    def test_viewer_can_view_clone_page(self):
        self.login_viewer()
        # Viewer can clone an item they can see
        self.assertTrue(perms.user_can_view(self.viewer, self.item1))
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        # Viewer can't clone an item they can't see
        self.assertFalse(perms.user_can_view(self.viewer, self.item2))
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_submitter_can_view_clone_page(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_submitter_can_save_via_clone_page(self):
        self.login_editor()
        import time
        time.sleep(2) # delays so there is a definite time difference between the first item and the clone on very fast test machines
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict(response.context['item'])
        updated_name = updated_item['name'] + " cloned!"
        updated_item['name'] = updated_name
        response = self.client.post(reverse('aristotle:clone_item',args=[self.item1.id]), updated_item)
        most_recent = self.itemType.objects.order_by('-created').first()
        self.assertTrue(perms.user_can_view(self.editor, most_recent))

        self.assertRedirects(response,url_slugify_concept(most_recent))
        self.assertEqual(most_recent.name,updated_name)

        # Make sure the right item was save and our original hasn't been altered.
        self.item1 = self.itemType.objects.get(id=self.item1.id) # Stupid cache
        self.assertTrue('cloned' not in self.item1.name)

    def test_submitter_can_save_via_clone_page_with_no_workgroup(self):
        self.login_editor()
        import time
        time.sleep(2) # delays so there is a definite time difference between the first item and the clone on very fast test machines
        response = self.client.get(reverse('aristotle:clone_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict(response.context['item'])
        updated_name = updated_item['name'] + " cloned with no WG!"
        updated_item['name'] = updated_name
        updated_item['workgroup'] = '' # no workgroup this time
        response = self.client.post(reverse('aristotle:clone_item',args=[self.item1.id]), updated_item)

        self.assertTrue(response.status_code == 302) # make sure its saved ok
        most_recent = self.itemType.objects.order_by('-created').first()

        self.assertTrue('cloned with no WG' in most_recent.name)
        self.assertTrue(most_recent.workgroup == None)
        self.assertTrue(perms.user_can_view(self.editor, most_recent))

        self.assertRedirects(response,url_slugify_concept(most_recent))
        self.assertEqual(most_recent.name,updated_name)

        # Make sure the right item was save and our original hasn't been altered.
        self.item1 = self.itemType.objects.get(id=self.item1.id) # Stupid cache
        self.assertTrue('cloned with no WG' not in self.item1.name)

    def test_viewer_cannot_view_supersede_page(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:supersede',args=[self.item1.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:supersede',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_editor_can_view_supersede_page(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:supersede',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:supersede',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:supersede',args=[self.item3.id]))
        self.assertEqual(response.status_code,200)

    def test_editor_can_remove_supersede_relation(self):
        self.login_editor()
        self.item2 = self.itemType.objects.create(name="supersede this",workgroup=self.wg1, **self.defaults)
        self.item1.superseded_by = self.item2
        self.item1.save()

        self.assertTrue(self.item1 in self.item2.supersedes.all().select_subclasses())
        response = self.client.post(
            reverse('aristotle:supersede',args=[self.item1.id]),{'newerItem':""})
        self.assertEqual(response.status_code,302)
        self.item1 = self.itemType.objects.get(id=self.item1.id) # Stupid cache
        self.assertTrue(self.item1.superseded_by == None)
        self.assertTrue(self.item2.supersedes.count() == 0)

    def test_viewer_cannot_view_deprecate_page(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item1.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_editor_can_view_deprecate_page(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item3.id]))
        self.assertEqual(response.status_code,200)

    def test_editor_can_deprecate_item(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:deprecate',args=[self.item3.id]))
        self.assertEqual(response.status_code,200)

        response = self.client.post(
            reverse('aristotle:deprecate',args=[self.item3.id]),{'olderItems':[self.item1.id]})
        self.assertEqual(response.status_code,302)

        self.item1 = self.itemType.objects.get(id=self.item1.id) # Stupid cache
        self.assertTrue(self.item1.superseded_by == self.item3.concept)

    def test_help_page_exists(self):
        self.logout()
        response = self.client.get(
            reverse('aristotle_help:concept_help',args=[self.itemType._meta.app_label,self.itemType._meta.model_name])
        )
        self.assertEqual(response.status_code,200)

    def test_viewer_can_view_registration_history(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:registrationHistory',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:registrationHistory',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_anon_cannot_view_registration_history(self):
        self.logout()
        response = self.client.get(reverse('aristotle:registrationHistory',args=[self.item1.id]))
        self.assertEqual(response.status_code,302)
        response = self.client.get(reverse('aristotle:registrationHistory',args=[self.item2.id]))
        self.assertEqual(response.status_code,302)

    def test_viewer_can_view_item_history(self):
        # Workgroup members can see the edit history of items
        self.login_viewer()
        response = self.client.get(reverse('aristotle:item_history',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:item_history',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

        # # Viewers shouldn't even have the link to history on items they arent in the workgroup for
        # This check makes no sense - a user can't see the page to begin with.
        # Keeping for posterity
        # response = self.client.get(self.item2.get_absolute_url())
        # self.assertNotContains(response, reverse('aristotle:item_history',args=[self.item2.id]))

        # Viewers will even have the link to history on items they are in the workgroup for
        response = self.client.get(self.item1.get_absolute_url())
        self.assertContains(response, reverse('aristotle:item_history',args=[self.item1.id]))

    def test_editor_can_view_item_history__and__compare(self):
        self.login_editor()

        #from reversion import revisions as reversion
        import reversion

        with reversion.revisions.create_revision():
            self.item1.name = "change 1"
            reversion.set_comment("change 1")
            self.item1.save()

        review = models.ReviewRequest.objects.create(
            requester=self.su,registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)
        with reversion.revisions.create_revision():
            self.item1.name = "change 2"
            reversion.set_comment("change 2")
            self.ra.register(
                item=self.item1,
                state=models.STATES.incomplete,
                user=self.registrar
            )
            self.item1.save()

        from reversion.models import Version
        revisions = Version.objects.get_for_object(self.item1)

        response = self.client.get(reverse('aristotle:item_history',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        response = self.client.get(
            reverse('aristotle:item_history',args=[self.item1.id]),
            {'version_id1' : revisions.first().pk,
            'version_id2' : revisions.last().pk
            }
        )

        self.assertEqual(response.status_code,200)
        self.assertContains(response, "change 2")
        self.assertContains(response, 'statuses')

        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache
        self.assertTrue(self.item1.name == "change 2")
        for s in self.item1.statuses.all():
            self.assertContains(
                response,
                '%s is %s'%(self.item1.name,s.get_state_display())
            )

    def test_editor_can_revert_item_and_status_goes_back_too(self):
        self.login_editor()

        # REVISION 0
        import reversion
        #from reversion import revisions as reversion
        with reversion.revisions.create_revision():
            self.item1.save()
        original_name = self.item1.name

        # REVISION 1
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name
        change_comment = "I changed this because I can"
        updated_item['change_comments'] = change_comment

        # REVISION 2
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertEqual(self.item1.name,updated_name)

        review = models.ReviewRequest.objects.create(
            requester=self.su,registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)
        self.ra.register(
            item=self.item1,
            state=models.STATES.incomplete,
            user=self.registrar
        )
        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache

        self.assertTrue(self.item1.statuses.all().count() == 1)
        self.assertTrue(self.item1.statuses.first().state == models.STATES.incomplete)

        # REVISION 3
        response = self.client.get(reverse('aristotle:edit_item',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name_again = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name_again
        change_comment = "I changed this again because I can"
        updated_item['change_comments'] = change_comment

        # REVISION 4
        response = self.client.post(reverse('aristotle:edit_item',args=[self.item1.id]), updated_item)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertEqual(self.item1.name,updated_name_again)

        # REVISION 5
        self.ra.register(self.item1,models.STATES.candidate,self.registrar)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache
        self.assertTrue(self.item1.statuses.count() == 2)
        self.assertTrue(self.item1.statuses.last().state == models.STATES.candidate)

        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(self.item1._meta.model)
        versions = list(
            reversion.models.Version.objects.filter(
                object_id=self.item1.id,
                content_type_id=ct.id
            ).order_by('revision__date_created')
        )
        versions[2].revision.revert(delete=True) # The version that has the first status changes

        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache

        self.assertTrue(self.item1.statuses.count() == 1)
        self.assertTrue(self.item1.statuses.first().state == models.STATES.incomplete)
        self.assertEqual(self.item1.name,updated_name)

        # Go back to the initial revision
        versions[0].revision.revert(delete=True)
        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache
        self.assertTrue(self.item1.statuses.count() == 0)
        self.assertEqual(self.item1.name,original_name)


        versions[4].revision.revert(delete=True) # Back to the latest version
        self.item1 = self.itemType.objects.get(pk=self.item1.pk) #decache

        self.assertTrue(self.item1.statuses.count() == 2)
        self.assertTrue(self.item1.statuses.order_by('state')[0].state == models.STATES.incomplete)
        self.assertTrue(self.item1.statuses.order_by('state')[1].state == models.STATES.candidate)
        self.assertEqual(self.item1.name,updated_name_again)


    def test_anon_cannot_view_item_history(self):
        self.logout()
        response = self.client.get(reverse('aristotle:item_history',args=[self.item1.id]))
        self.assertEqual(response.status_code,302)
        response = self.client.get(reverse('aristotle:item_history',args=[self.item2.id]))
        self.assertEqual(response.status_code,302)


        # Register to check if link is on page... it shouldn't be
        models.Status.objects.create(
            concept=self.item1,
            registrationAuthority=self.ra,
            registrationDate = datetime.date(2009,4,28),
            state =  models.STATES.standard
            )

        # Anon users shouldn't even have the link to history *any* items
        response = self.client.get(self.item1.get_absolute_url())
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response, reverse('aristotle:item_history',args=[self.item1.id]))

    def test_viewer_can_favourite(self):
        self.login_viewer()
        self.assertTrue(perms.user_can_view(self.viewer,self.item1))

        response = self.client.post(reverse('friendly_login'), {'username': 'vicky@example.com', 'password': 'viewer'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.viewer.profile.favourites.count(),0)

        response = self.client.get(
            reverse('aristotle:toggleFavourite', args=[self.item1.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            url_slugify_concept(self.item1)
        )
        self.assertEqual(self.viewer.profile.favourites.count(),1)
        self.assertEqual(self.viewer.profile.favourites.first().item,self.item1)
        self.assertContains(response, "added to favourites")

        response = self.client.get(
            reverse('aristotle:toggleFavourite', args=[self.item1.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            url_slugify_concept(self.item1)
        )
        self.assertEqual(self.viewer.profile.favourites.count(),0)
        self.assertContains(response, "removed from favourites")

        response = self.client.get(reverse('aristotle:toggleFavourite', args=[self.item2.id]))
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.viewer.profile.favourites.count(),0)

    def test_anon_cannot_favourite(self):
        self.logout()

        response = self.client.get(reverse('aristotle:toggleFavourite', args=[self.item1.id]))
        self.assertRedirects(response,reverse('friendly_login')+"?next="+reverse('aristotle:toggleFavourite', args=[self.item1.id]))

    @tag('changestatus')
    def test_registrar_can_change_status(self):
        self.login_registrar()

        self.make_review_request(self.item1, self.registrar)

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.statuses.count(),0)
        response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': self.ra.public_state,
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': 0, # no
                'submit_skip': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )
        self.assertRedirects(response,url_slugify_concept(self.item1))

        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertEqual(self.item1.statuses.count(),1)
        self.assertTrue(self.item1.is_registered)
        self.assertTrue(self.item1.is_public())

    @tag('inactive_ra', 'changestatus')
    def test_registrar_cant_change_status_with_inactive_ra(self):

        self.login_registrar()
        self.make_review_request(self.item1, self.registrar)

        # Deactivate RA
        self.ra.active = 1
        self.ra.save()

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)
        self.assertFalse(self.ra in response.context['form'].fields['registrationAuthorities'].queryset)

        response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': self.ra.public_state,
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': 0, # no
                'submit_skip': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('registrationAuthorities' in response.context['form'].errors)


    @tag('changestatus')
    def test_registrar_can_change_status_with_cascade(self):
        if not hasattr(self,"run_cascade_tests"):
            return
        self.login_registrar()

        self.make_review_request(self.item1, self.registrar)

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.statuses.count(),0)
        for sub_item in self.item1.registry_cascade_items:
            if sub_item is not None:
                self.assertEqual(sub_item.statuses.count(),0)
            else:
                pass

        response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': self.ra.public_state,
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': 1, # yes
                'submit_skip': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )
        self.assertRedirects(response,url_slugify_concept(self.item1))

        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertEqual(self.item1.statuses.count(),1)
        self.assertTrue(self.item1.is_registered)
        self.assertTrue(self.item1.is_public())
        for sub_item in self.item1.registry_cascade_items:
            if sub_item is not None:
                if not sub_item.is_registered: # pragma: no cover
                    # This is debug code, and should never happen
                    print(sub_item)
                self.assertTrue(sub_item.is_registered)

    @tag('changestatus')
    def test_registrar_cannot_use_faulty_statuses(self):
        self.login_registrar()

        self.assertFalse(perms.user_can_view(self.registrar,self.item1))
        self.item1.save()
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)

        review = models.ReviewRequest.objects.create(
            requester=self.su,registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        self.assertTrue(perms.user_can_view(self.registrar,self.item1))
        self.assertTrue(perms.user_can_change_status(self.registrar,self.item1))

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.statuses.count(),0)
        response = self.client.post(
            reverse('aristotle:changeStatus', args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': "Not a number", # obviously wrong
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': 0, # no
                'submit_skip': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )
        self.assertFormError(response, 'form', 'state', 'Select a valid choice. Not a number is not one of the available choices.')

        response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': "343434", # also wrong
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': 0, # no
                'submit_skip': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )
        self.assertFormError(response, 'form', 'state', 'Select a valid choice. 343434 is not one of the available choices.')

    def registrar_can_change_status_with_review(self, cascade, check_bad_perms=False):
        if not hasattr(self,"run_cascade_tests") and cascade:
            return
        self.login_registrar()

        self.assertFalse(perms.user_can_view(self.registrar,self.item1))
        self.item1.save()
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)

        review = models.ReviewRequest.objects.create(
            requester=self.su,registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        self.assertTrue(perms.user_can_view(self.registrar,self.item1))
        self.assertTrue(perms.user_can_change_status(self.registrar,self.item1))

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.statuses.count(),0)
        for sub_item in self.item1.registry_cascade_items:
            if sub_item is not None:
                self.assertEqual(sub_item.statuses.count(),0)
            else:
                pass

        if cascade:
            cascade_post = 1
            if not check_bad_perms:
                # add all cascade items to review
                for item in self.item1.registry_cascade_items:
                    review.concepts.add(item)
        else:
            cascade_post = 0

        response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'change_status-registrationAuthorities': [str(self.ra.id)],
                'change_status-state': self.ra.public_state,
                'change_status-changeDetails': "testing",
                'change_status-cascadeRegistration': cascade_post,
                'submit_next': 'value',
                'change_status_view-current_step': 'change_status',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['wizard']['steps'].step1, 2) # check we are now on second setep
        selected_for_change = [self.item1.id]

        if cascade:
            selected_for_change.append(self.item1.registry_cascade_items[0].id)

        selected_for_change_strings = [str(a) for a in selected_for_change]

        review_response = self.client.post(
            reverse('aristotle:changeStatus',args=[self.item1.id]),
            {
                'review_changes-selected_list': selected_for_change_strings,
                'change_status_view-current_step': 'review_changes',
            }
        )
        self.assertRedirects(review_response,url_slugify_concept(self.item1))

        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertEqual(self.item1.statuses.count(),1)
        self.assertTrue(self.item1.is_registered)
        self.assertTrue(self.item1.is_public())
        if cascade:
            for sub_item in self.item1.registry_cascade_items:
                if sub_item is not None:
                    if sub_item.id in selected_for_change:
                        if not check_bad_perms:
                            self.assertTrue(sub_item.is_registered)
                        else:
                            self.assertFalse(sub_item.is_registered)
                    else:
                        self.assertFalse(sub_item.is_registered)

    @tag('changestatus')
    def test_registrar_can_change_status_with_review_cascade(self):
        self.registrar_can_change_status_with_review(cascade=True)

    @tag('changestatus')
    def test_registrar_cant_update_cascaded_items_without_perm(self):
        self.registrar_can_change_status_with_review(cascade=True, check_bad_perms=True)

    @tag('changestatus')
    def test_registrar_can_change_status_with_review_no_cascade(self):
        self.registrar_can_change_status_with_review(cascade=False)

    @tag('changestatus')
    def test_viewer_cannot_change_status(self):
        self.login_viewer()

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertEqual(response.status_code,403)

    @tag('changestatus')
    def test_anon_cannot_change_status(self):
        self.logout()

        response = self.client.get(reverse('aristotle:changeStatus',args=[self.item1.id]))
        self.assertRedirects(response,reverse('friendly_login')+"?next="+reverse('aristotle:changeStatus', args=[self.item1.id]))

    @tag('changestatus')
    def test_cascade_action(self):
        self.logout()
        check_url = reverse('aristotle:check_cascaded_states', args=[self.item1.pk])

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,403)

        self.login_editor()

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,404)

    def test_weak_editing_in_advanced_editor_dynamic(self, updating_field=None, default_fields={}):

        if hasattr(self.item1, 'serialize_weak_entities'):
            self.login_editor()
            value_url = 'aristotle:edit_item'

            response = self.client.get(reverse(value_url,args=[self.item1.id]))
            self.assertEqual(response.status_code, 200)

            weak_formsets = response.context['weak_formsets']

            weak = self.item1.serialize_weak_entities

            for entity in weak:

                value_type = entity[1]
                pre = entity[0]

                # find associated formset
                current_formset = None
                for formset in weak_formsets:
                    if formset['formset'].prefix == pre:
                        current_formset = formset['formset']

                # check that a formset with the correct prefix was rendered
                self.assertIsNotNone(current_formset)

                data = utils.model_to_dict_with_change_time(self.item1)

                num_vals = getattr(self.item1,value_type).all().count()
                ordering_field = getattr(self.item1,value_type).model.ordering_field

                # check to make sure the classes with weak entities added them on setUp below
                self.assertGreater(num_vals, 0)

                skipped_fields = ['id', 'ORDER', 'start_date', 'end_date', 'DELETE']
                for i,v in enumerate(getattr(self.item1,value_type).all()):
                    data.update({"%s-%d-id"%(pre,i): v.pk, "%s-%d-ORDER"%(pre,i) : getattr(v, ordering_field)})
                    for field in current_formset[0].fields:
                        if hasattr(v, field) and field not in skipped_fields:
                            value = getattr(v, field)
                            if value is not None:

                                if (updating_field is None):
                                    # see if this is the field to update
                                    model_field = current_formset[0]._meta.model._meta.get_field(field)

                                    if isinstance(model_field, CharField) or isinstance(model_field, TextField):
                                        updating_field = field

                                if field == updating_field:
                                    data.update({"%s-%d-%s"%(pre,i,field) : value + ' -updated'})
                                else:
                                    added_value = value
                                    if field in default_fields:
                                        data.update({"%s-%d-%s"%(pre,i,field) : default_fields[field]})
                                        added_value = default_fields[field]
                                    else:
                                        data.update({"%s-%d-%s"%(pre,i,field) : value})
                                    if (i == num_vals - 1):
                                        # add a copy
                                        data.update({"%s-%d-%s"%(pre,i+1,field) : added_value})

                self.assertIsNotNone(updating_field)
                # no string was found to update
                # if this happends the test needs to be passed an updating_field or changed to support more than text updates

                i=0
                data.update({"%s-%d-DELETE"%(pre,i): 'checked', "%s-%d-%s"%(pre,i,updating_field) : getattr(v, updating_field)+" - deleted"}) # delete the last one.

                # add order and updating_value to newly added data
                i=num_vals
                data.update({"%s-%d-ORDER"%(pre,i) : i, "%s-%d-%s"%(pre,i,updating_field) : "new value -updated"})

                # add management form
                data.update({
                    "%s-TOTAL_FORMS"%pre:num_vals+1, "%s-INITIAL_FORMS"%pre: num_vals, "%s-MAX_NUM_FORMS"%pre:1000,
                    })

                response = self.client.post(reverse(value_url,args=[self.item1.id]), data)

                self.item1 = self.itemType.objects.get(pk=self.item1.pk)

                self.assertTrue(num_vals == getattr(self.item1,value_type).all().count())

                new_value_seen = False
                for v in getattr(self.item1,value_type).all():
                    value = getattr(v, updating_field)
                    self.assertTrue('updated' in value) # This will fail if the item isn't updated
                    self.assertFalse('deleted' in value) # make sure deleted value not present
                    if value == 'new value -updated':
                        new_value_seen = True
                self.assertTrue(new_value_seen)


class ObjectClassViewPage(LoggedInViewConceptPages, TestCase):
    url_name='objectClass'
    itemType=models.ObjectClass
class PropertyViewPage(LoggedInViewConceptPages, TestCase):
    url_name='property'
    itemType=models.Property
class UnitOfMeasureViewPage(LoggedInViewConceptPages, TestCase):
    url_name='unitOfMeasure'
    itemType=models.UnitOfMeasure
class ValueDomainViewPage(LoggedInViewConceptPages, TestCase):
    url_name='valueDomain'
    itemType=models.ValueDomain
    def setUp(self):
        super().setUp()

        for i in range(4):
            models.PermissibleValue.objects.create(
                value=i,meaning="test permissible meaning %d"%i,order=i,valueDomain=self.item1
                )
        for i in range(4):
            models.SupplementaryValue.objects.create(
                value=i,meaning="test supplementary meaning %d"%i,order=i,valueDomain=self.item1
                )

        # Data used to test value domain conceptual domain link
        cd = models.ConceptualDomain.objects.create(
            description='test description'
        )

        cd2 = models.ConceptualDomain.objects.create(
            description='unrelated conceptual domain'
        )
        models.ValueMeaning.objects.create(
            name="test name",
            definition="test definition",
            conceptual_domain=cd2,
            order=0,
        )

        self.vms = []
        for i in range(2):
            vm = models.ValueMeaning.objects.create(
                name="test name",
                definition="test definition",
                conceptual_domain=cd,
                order=i,
            )
            self.vms.append(vm)

        self.item3.conceptual_domain = cd
        self.item3.save()

    def test_weak_editing_in_advanced_editor_dynamic(self):
        super().test_weak_editing_in_advanced_editor_dynamic(updating_field='value')

    def test_anon_cannot_use_value_page(self):
        self.logout()
        response = self.client.get(reverse('aristotle:permsissible_values_edit',args=[self.item1.id]))
        self.assertRedirects(response,reverse('friendly_login')+"?next="+reverse('aristotle:permsissible_values_edit',args=[self.item1.id]))
        response = self.client.get(reverse('aristotle:supplementary_values_edit',args=[self.item1.id]))
        self.assertRedirects(response,reverse('friendly_login')+"?next="+reverse('aristotle:supplementary_values_edit',args=[self.item1.id]))

    def loggedin_user_can_use_value_page(self,value_url,current_item,http_code):
        response = self.client.get(reverse(value_url,args=[current_item.id]))
        self.assertEqual(response.status_code,http_code)

    def submitter_user_can_use_value_edit_page(self,value_type):
        value_url = {
            'permissible': 'aristotle:permsissible_values_edit',
            'supplementary': 'aristotle:supplementary_values_edit'
        }.get(value_type)

        self.login_editor()
        self.loggedin_user_can_use_value_page(value_url,self.item1,200)
        self.loggedin_user_can_use_value_page(value_url,self.item2,403)
        self.loggedin_user_can_use_value_page(value_url,self.item3,200)

        data = {}
        num_vals = getattr(self.item1,value_type+"Values").count()
        i=0
        for i,v in enumerate(getattr(self.item1,value_type+"Values").all()):
            data.update({"form-%d-id"%i: v.pk, "form-%d-ORDER"%i : v.order, "form-%d-value"%i : v.value, "form-%d-meaning"%i : v.meaning+" -updated"})
        data.update({"form-%d-DELETE"%i: 'checked', "form-%d-meaning"%i : v.meaning+" - deleted"}) # delete the last one.
        # now add a new one
        i=i+1
        data.update({"form-%d-ORDER"%i : i, "form-%d-value"%i : 100, "form-%d-meaning"%i : "new value -updated"})

        data.update({
            "form-TOTAL_FORMS":num_vals+1, "form-INITIAL_FORMS": num_vals, "form-MAX_NUM_FORMS":1000,

            })
        self.client.post(reverse(value_url,args=[self.item1.id]),data)
        self.item1 = models.ValueDomain.objects.get(pk=self.item1.pk)

        self.assertTrue(num_vals == getattr(self.item1,value_type+"Values").count())
        new_value_seen = False
        for v in getattr(self.item1,value_type+"Values").all():
            self.assertTrue('updated' in v.meaning) # This will fail if the deleted item isn't deleted
            if v.value == '100':
                new_value_seen = True
        self.assertTrue(new_value_seen)


        # Item is now locked, submitter is no longer able to edit
        models.Status.objects.create(
                concept=self.item1,
                registrationAuthority=self.ra,
                registrationDate=timezone.now(),
                state=self.ra.locked_state
                )

        self.item1 = models.ValueDomain.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.is_locked())
        self.assertFalse(perms.user_can_edit(self.editor,self.item1))
        self.loggedin_user_can_use_value_page(value_url,self.item1,403)

    def test_submitter_can_use_permissible_value_edit_page(self):
        self.submitter_user_can_use_value_edit_page('permissible')

    def test_submitter_can_use_supplementary_value_edit_page(self):
        self.submitter_user_can_use_value_edit_page('supplementary')

    def test_submitter_user_doesnt_save_all_blank_permissible_value_edit_page(self):
        self.submitter_user_doesnt_save_all_blank('permissible')

    def test_submitter_user_doesnt_save_all_blank_supplementary_value_edit_page(self):
        self.submitter_user_doesnt_save_all_blank('supplementary')

    def submitter_user_doesnt_save_all_blank(self,value_type):
        value_url = {
            'permissible': 'aristotle:permsissible_values_edit',
            'supplementary': 'aristotle:supplementary_values_edit'
        }.get(value_type)

        self.login_editor()
        self.loggedin_user_can_use_value_page(value_url,self.item1,200)

        data = {}
        num_vals = getattr(self.item1,value_type+"Values").count()

        i=0
        for i,v in enumerate(getattr(self.item1,value_type+"Values").all()):
            data.update({"form-%d-id"%i: v.pk, "form-%d-ORDER"%i : v.order, "form-%d-value"%i : v.value, "form-%d-meaning"%i : v.meaning+" -updated"})

        # now add two new values that are all blank
        i=i+1
        data.update({"form-%d-ORDER"%i : i, "form-%d-value"%i : '', "form-%d-meaning"%i : ""})
        i=i+1
        data.update({"form-%d-ORDER"%i : i, "form-%d-value"%i : '', "form-%d-meaning"%i : ""})

        data.update({
            "form-TOTAL_FORMS":num_vals+1, "form-INITIAL_FORMS": num_vals, "form-MAX_NUM_FORMS":1000,

            })
        self.client.post(reverse(value_url,args=[self.item1.id]),data)
        self.item1 = models.ValueDomain.objects.get(pk=self.item1.pk)

        self.assertTrue(num_vals == getattr(self.item1,value_type+"Values").count())

    def test_su_can_download_csv(self):
        self.login_superuser()
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item2.id]))
        self.assertEqual(response.status_code,200)

    def test_editor_can_download_csv(self):
        self.login_editor()
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_viewer_can_download_csv(self):
        self.login_viewer()
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item1.id]))
        self.assertEqual(response.status_code,200)
        response = self.client.get(reverse('aristotle:download',args=['csv-vd',self.item2.id]))
        self.assertEqual(response.status_code,403)

    def test_values_shown_on_page(self):
        self.login_viewer()

        response = self.client.get(self.get_page(self.item1))
        self.assertEqual(response.status_code,200)
        for pv in self.item1.permissiblevalue_set.all():
            self.assertContains(response,pv.meaning,1)
        for sv in self.item1.supplementaryvalue_set.all():
            self.assertContains(response,sv.meaning,1)

    def test_conceptual_domain_selection(self):
        self.login_editor()
        url = 'aristotle:permsissible_values_edit'
        self.loggedin_user_can_use_value_page(url,self.item3,200)

        response = self.client.get(reverse(url,args=[self.item3.id]))
        self.assertEqual(response.status_code, 200)

        # check queryset correctly filled from conceptual domain for item 2
        formset = response.context['formset']
        for form in formset:
            self.assertFalse('meaning' in form.fields)
            self.assertTrue('value_meaning' in form.fields)
            queryset = form.fields['value_meaning'].queryset
            for item in queryset:
                self.assertTrue(item in self.vms)

        # Check empty queryset for item 1 (no cd linked)
        response = self.client.get(reverse(url,args=[self.item1.id]))
        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']
        for form in formset:
            self.assertFalse('value_meaning' in form.fields)
            self.assertTrue('meaning' in form.fields)

class ConceptualDomainViewPage(LoggedInViewConceptPages, TestCase):
    url_name='conceptualDomain'
    itemType=models.ConceptualDomain

    def setUp(self):
        super().setUp()

        for i in range(4):
            models.ValueMeaning.objects.create(
                name="test name",
                definition="test definition",
                conceptual_domain=self.item1,
                order=i,
            )

    @tag('edit_formsets')
    def test_edit_formset_error_display(self):

        self.login_editor()

        edit_url = 'aristotle:edit_item'
        response = self.client.get(reverse(edit_url,args=[self.item1.id]))
        self.assertEqual(response.status_code, 200)

        data = utils.model_to_dict_with_change_time(self.item1)

        # submit an item with a blank name
        valuemeaning_formset_data = [
            {'name': '', 'definition': 'test defn', 'start_date': '1999-01-01', 'end_date': '2090-01-01', 'ORDER': 0},
            {'name': 'Test2', 'definition': 'test defn', 'start_date': '1999-01-01', 'end_date': '2090-01-01', 'ORDER': 1}
        ]
        data.update(self.get_formset_postdata(valuemeaning_formset_data, 'value_meaning', 0))
        response = self.client.post(reverse(edit_url,args=[self.item1.id]), data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['weak_formsets'][0]['formset'].errors[0], {'name': ['This field is required.']})
        self.assertContains(response, 'This field is required.')


class DataElementConceptViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataElementConcept'
    itemType=models.DataElementConcept
    run_cascade_tests = True

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.oc = models.ObjectClass.objects.create(
            name="sub item OC",
            workgroup=self.item1.workgroup,
        )
        self.prop = models.Property.objects.create(
            name="sub item prop",
            workgroup=self.item1.workgroup
        )
        self.item1.objectClass = self.oc
        self.item1.property = self.prop
        self.item1.save()
        self.assertTrue(self.oc.can_view(self.editor))
        self.assertTrue(self.prop.can_view(self.editor))

    def test_foreign_key_popups(self):
        self.logout()

        check_url = reverse('aristotle:generic_foreign_key_editor', args=[self.item1.pk, 'objectclassarino'])
        response = self.client.get(check_url)
        self.assertEqual(response.status_code,404)

        check_url = reverse('aristotle:generic_foreign_key_editor', args=[self.item1.pk, 'objectclass'])
        response = self.client.get(check_url)
        self.assertEqual(response.status_code,302)  # user must login too see

        response = self.client.post(check_url,{'objectClass':''})
        self.assertEqual(response.status_code,302)
        self.item1 = self.item1.__class__.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.objectClass is not None)

        self.login_editor()
        response = self.client.get(check_url)
        self.assertEqual(response.status_code,200)

        response = self.client.post(check_url,{'objectClass':''})
        self.assertEqual(response.status_code,302)
        self.item1 = self.item1.__class__.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.objectClass is None)

        response = self.client.post(check_url,{'objectClass':self.prop.pk})
        self.assertEqual(response.status_code,200)
        self.item1 = self.item1.__class__.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.objectClass is None)

        another_oc = models.ObjectClass.objects.create(
            name="editor can't see this",
            definition="my definition",
        )
        response = self.client.post(check_url,{'objectClass':another_oc.pk})
        self.assertEqual(response.status_code,200)
        self.item1 = self.item1.__class__.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.objectClass is None)


        response = self.client.post(check_url,{'objectClass':self.oc.pk})
        self.assertEqual(response.status_code,302)
        self.item1 = self.item1.__class__.objects.get(pk=self.item1.pk)
        self.assertTrue(self.item1.objectClass == self.oc)

    def test_regular_cannot_save_a_property_they_cant_see_via_edit_page(self):
        self.login_regular_user()
        self.regular_item = self.itemType.objects.create(name="regular item",definition="my definition", submitter=self.regular,**self.defaults)
        response = self.client.get(reverse('aristotle:edit_item',args=[self.regular_item.id]))
        self.assertEqual(response.status_code,200)

        updated_item = utils.model_to_dict_with_change_time(response.context['item'])
        updated_name = updated_item['name'] + " updated!"
        updated_item['name'] = updated_name

        different_prop = models.Property.objects.create(
            name="sub item prop 2",
            workgroup=self.item1.workgroup
        )
        updated_item['property'] = different_prop.pk

        self.assertFalse(self.prop.can_view(self.regular))
        self.assertFalse(different_prop.can_view(self.regular))

        response = self.client.post(reverse('aristotle:edit_item',args=[self.regular_item.id]), updated_item)
        self.regular_item = self.itemType.objects.get(pk=self.regular_item.pk)

        self.assertEqual(response.status_code,200)
        self.assertTrue('not one of the available choices' in response.context['form'].errors['property'][0])
        self.assertFalse(self.regular_item.name == updated_name)
        self.assertFalse(self.regular_item.property == self.prop)

    def test_cascade_action(self):
        self.logout()
        check_url = reverse('aristotle:check_cascaded_states', args=[self.item1.pk])

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,403)

        self.login_editor()

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,200)
        self.assertContains(response, self.item1.objectClass.name)
        self.assertContains(response, self.item1.property.name)

        ra = models.RegistrationAuthority.objects.create(name="new RA")
        item = self.item1.property
        s = models.Status.objects.create(
                concept=item,
                registrationAuthority=ra,
                registrationDate=timezone.now(),
                state=ra.locked_state
                )
        s = models.Status.objects.create(
                concept=item,
                registrationAuthority=self.ra,
                registrationDate=timezone.now(),
                state=ra.locked_state
                )
        s = models.Status.objects.create(
                concept=self.item1,
                registrationAuthority=self.ra,
                registrationDate=timezone.now(),
                state=ra.public_state
                )

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,200)
        self.assertContains(response, self.item1.objectClass.name)
        self.assertContains(response, self.item1.property.name)
        self.assertContains(response, 'fa-times') # The property has a different status


class DataElementViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataElement'
    itemType=models.DataElement


    def test_cascade_action(self):
        self.logout()
        check_url = reverse('aristotle:check_cascaded_states', args=[self.item1.pk])
        self.dec1 = models.DataElementConcept.objects.create(name='DEC1 - visible',definition="my definition",workgroup=self.wg1)
        self.item1.dataElementConcept = self.dec1
        self.item1.save()

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,403)

        self.login_editor()

        response = self.client.get(check_url)
        self.assertEqual(response.status_code,200)

class DataElementDerivationViewPage(LoggedInViewConceptPages, TestCase):
    url_name='dataelementderivation'
    itemType=models.DataElementDerivation

    def derivation_m2m_concepts_save(self, url, attr):
        self.de1 = models.DataElement.objects.create(name='DE1 - visible',definition="my definition",workgroup=self.wg1)
        self.de2 = models.DataElement.objects.create(name='DE2 - not visible',definition="my definition",workgroup=self.wg2)
        self.oc1 = models.ObjectClass.objects.create(name='OC - visible but wrong',definition="my definition",workgroup=self.wg1)

        self.login_editor()

        management_form = {
            'form-INITIAL_FORMS': 0,
            'form-TOTAL_FORMS': 1,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000
        }

        self.assertFalse(self.de2.can_view(self.editor))

        response = self.client.get(
            reverse(url, args=[self.item1.pk])
        )
        self.assertEqual(response.status_code,200)

        postdata = management_form.copy()
        postdata['form-0-item_to_add'] = self.de2.pk
        postdata['form-0-ORDER'] = 0
        #postdata['form-TOTAL_FORMS'] = 2

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata
        )
        self.item1 = self.itemType.objects.get(pk=self.item1.pk)
        self.assertTrue(self.de2 not in getattr(self.item1, attr).all())
        self.assertEqual(response.status_code,200)
        self.assertContains(response, 'Select a valid choice')

        postdata = management_form.copy()
        postdata['form-0-item_to_add'] = self.de1.pk
        postdata['form-0-ORDER'] = 0
        postdata['form-1-item_to_add'] = self.de2.pk
        postdata['form-1-ORDER'] = 1
        postdata['form-TOTAL_FORMS'] = 2

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata,
            follow=True
        )
        self.assertTrue(self.de2 not in getattr(self.item1, attr).all())
        self.assertContains(response, 'Select a valid choice')
        self.assertEqual(response.status_code,200)

        # user can see OC1, but its the wrong type so expect failure

        postdata = management_form.copy()
        postdata['form-0-item_to_add'] = self.de1.pk
        postdata['form-0-ORDER'] = 0
        postdata['form-1-item_to_add'] = self.oc1.pk
        postdata['form-1-ORDER'] = 1
        postdata['form-TOTAL_FORMS'] = 2

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata,
            follow=True
        )
        self.assertTrue(self.de2 not in getattr(self.item1, attr).all())
        self.assertContains(response, 'Select a valid choice')
        self.assertEqual(response.status_code,200)

        postdata = management_form.copy()
        postdata['form-0-item_to_add'] = self.de1.pk
        postdata['form-0-ORDER'] = 0

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata
        )
        self.assertTrue(self.de1 in getattr(self.item1, attr).all())
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response, self.item1.get_absolute_url())

    def test_derivation_derives_concepts_save(self):
        self.derivation_m2m_concepts_save(
            url="aristotle_mdr:dataelementderivation_change_derives",
            attr='derives',
        )

    def test_derivation_inputs_concepts_save(self):
        self.derivation_m2m_concepts_save(
            url="aristotle_mdr:dataelementderivation_change_inputs",
            attr='inputs',
        )

    def derivation_m2m_formset(self, url, attr, prefix='form', item_add_field='item_to_add', add_itemdata=False, extra_postdata=None):

        self.de1 = models.DataElement.objects.create(name='DE1 - visible',definition="my definition",workgroup=self.wg1)
        self.de2 = models.DataElement.objects.create(name='DE2 - visible',definition="my definition",workgroup=self.wg1)
        self.de3 = models.DataElement.objects.create(name='DE3 - visible',definition="my definition",workgroup=self.wg1)

        self.login_editor()

        management_form = {
            '{}-INITIAL_FORMS'.format(prefix): 0,
            '{}-TOTAL_FORMS'.format(prefix): 1,
            '{}-MIN_NUM_FORMS'.format(prefix): 0,
            '{}-MAX_NUM_FORMS'.format(prefix): 1000
        }

        if extra_postdata:
            management_form.update(extra_postdata)

        # Post 3 items
        postdata = management_form.copy()

        if add_itemdata:
            postdata.update(utils.model_to_dict_with_change_time(self.item1))

        postdata['{}-0-{}'.format(prefix, item_add_field)] = self.de3.pk
        postdata['{}-0-ORDER'.format(prefix)] = 0
        postdata['{}-1-{}'.format(prefix, item_add_field)] = self.de1.pk
        postdata['{}-1-ORDER'.format(prefix)] = 1
        postdata['{}-2-{}'.format(prefix, item_add_field)] = self.de2.pk
        postdata['{}-2-ORDER'.format(prefix)] = 2
        postdata['{}-TOTAL_FORMS'.format(prefix)] = 3

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata
        )

        self.assertRedirects(response, self.item1.get_absolute_url())

        items = getattr(self.item1, attr).all()
        self.assertTrue(self.de1 in items)
        self.assertTrue(self.de2 in items)
        self.assertTrue(self.de3 in items)

        # Load page to check loading of existing data and preserved order

        response = self.client.get(reverse(url, args=[self.item1.pk]))
        self.assertEqual(response.status_code, 200)

        if not add_itemdata:
            # If m2m specific form
            formset_initial = response.context['formset'].initial

            self.assertEqual(len(formset_initial), 3)
            for data in formset_initial:
                self.assertTrue(data['ORDER'] in [0,1,2])
                if data['ORDER'] == 0:
                    self.assertEqual(data['{}'.format(item_add_field)], self.de3)
                elif data['ORDER'] == 1:
                    self.assertEqual(data['{}'.format(item_add_field)], self.de1)
                elif data['ORDER'] == 2:
                    self.assertEqual(data['{}'.format(item_add_field)], self.de2)

        if attr == 'derives':
            through_model = models.DedDerivesThrough
        else:
            through_model = models.DedInputsThrough

        # Check order with through table
        self.assertEqual(through_model.objects.count(), 3)
        self.assertEqual(through_model.objects.get(order=0).data_element, self.de3)
        self.assertEqual(through_model.objects.get(order=1).data_element, self.de1)
        self.assertEqual(through_model.objects.get(order=2).data_element, self.de2)


        # Change order and delete
        postdata = management_form.copy()

        if add_itemdata:
            postdata.update(utils.model_to_dict_with_change_time(self.item1))

        postdata['{}-0-{}'.format(prefix, item_add_field)] = self.de3.pk
        postdata['{}-0-id'.format(prefix)] = through_model.objects.get(data_element=self.de3).pk
        postdata['{}-0-ORDER'.format(prefix)] = 0
        postdata['{}-0-DELETE'.format(prefix)] = 'checked'
        postdata['{}-1-{}'.format(prefix, item_add_field)] = self.de2.pk
        postdata['{}-1-id'.format(prefix)] = through_model.objects.get(data_element=self.de2).pk
        postdata['{}-1-ORDER'.format(prefix)] = 1
        postdata['{}-2-{}'.format(prefix, item_add_field)] = self.de1.pk
        postdata['{}-2-id'.format(prefix)] = through_model.objects.get(data_element=self.de1).pk
        postdata['{}-2-ORDER'.format(prefix)] = 2
        postdata['{}-TOTAL_FORMS'.format(prefix)] = 3
        postdata['{}-INITIAL_FORMS'.format(prefix)] = 3

        response = self.client.post(
            reverse(url, args=[self.item1.pk]),
            postdata
        )
        print(response.status_code)

        self.assertRedirects(response, self.item1.get_absolute_url())

        items = getattr(self.item1, attr).all()
        self.assertTrue(items.count(), 2)
        self.assertTrue(self.de1 in items)
        self.assertTrue(self.de2 in items)
        self.assertFalse(self.de3 in items)

        # Load page to check order

        response = self.client.get(reverse(url, args=[self.item1.pk]))
        self.assertEqual(response.status_code, 200)

        formset_initial = response.context['formset'].initial

        if not add_itemdata:
            # If m2m specific form
            self.assertEqual(len(formset_initial), 2)
            for data in formset_initial:
                self.assertTrue(data['ORDER'] in [1,2])
                if data['ORDER'] == 1:
                    self.assertEqual(data['{}'.format(item_add_field)], self.de2)
                elif data['ORDER'] == 2:
                    self.assertEqual(data['{}'.format(item_add_field)], self.de1)

        # Check order with through table
        self.assertEqual(through_model.objects.count(), 2)
        self.assertEqual(through_model.objects.get(order=1).data_element, self.de2)
        self.assertEqual(through_model.objects.get(order=2).data_element, self.de1)

    @tag('edit_formsets')
    def test_derivation_inputs_formset(self):
        self.derivation_m2m_formset(
            url="aristotle_mdr:dataelementderivation_change_inputs",
            attr='inputs',
        )

    @tag('edit_formsets')
    def test_derivation_derives_formset(self):
        self.derivation_m2m_formset(
            url="aristotle_mdr:dataelementderivation_change_derives",
            attr='derives',
        )

    @tag('edit_formsets')
    def test_derivation_inputs_formset_editor(self):

        self.derivation_m2m_formset(
            url="aristotle_mdr:edit_item",
            attr="inputs",
            prefix="inputs",
            item_add_field="data_element",
            add_itemdata=True,
        )

    @tag('edit_formsets')
    def test_derivation_derives_formset_editor(self):

        self.derivation_m2m_formset(
            url="aristotle_mdr:edit_item",
            attr="derives",
            prefix="derives",
            item_add_field="data_element",
            add_itemdata=True,
        )

    def test_derivation_item_page(self):

        de1 = models.DataElement.objects.create(name='DE1 Name',definition="my definition",workgroup=self.wg1)
        de2 = models.DataElement.objects.create(name='DE2 Name',definition="my definition",workgroup=self.wg1)
        de3 = models.DataElement.objects.create(name='DE3 Name',definition="my definition",workgroup=self.wg1)
        ded = models.DataElementDerivation.objects.create(name='DED Name', definition='my definition', workgroup=self.wg1)

        ded_derives_1 = models.DedDerivesThrough.objects.create(data_element_derivation=ded, data_element=de1, order=0)
        ded_derives_2 = models.DedDerivesThrough.objects.create(data_element_derivation=ded, data_element=de2, order=1)
        ded_derives_3 = models.DedDerivesThrough.objects.create(data_element_derivation=ded, data_element=de3, order=2)

        ded_inputs_1 = models.DedInputsThrough.objects.create(data_element_derivation=ded, data_element=de3, order=0)
        ded_inputs_1 = models.DedInputsThrough.objects.create(data_element_derivation=ded, data_element=de2, order=1)
        ded_inputs_1 = models.DedInputsThrough.objects.create(data_element_derivation=ded, data_element=de1, order=2)

        self.login_editor()
        response = self.client.get(reverse("aristotle:item", args=[ded.pk]), follow=True)

        self.assertEqual(response.status_code, 200)

        # Check the template tag that was used returned the correct data

        item = response.context['item']

        des = get_dataelements_from_m2m(item, "inputs")
        self.assertEqual(des[0].pk, de3.pk)
        self.assertEqual(des[1].pk, de2.pk)
        self.assertEqual(des[2].pk, de1.pk)

        des = get_dataelements_from_m2m(item, "derives")
        self.assertEqual(des[0].pk, de1.pk)
        self.assertEqual(des[1].pk, de2.pk)
        self.assertEqual(des[2].pk, de3.pk)


class LoggedInViewUnmanagedPages(utils.LoggedInViewPages):
    defaults = {}
    def setUp(self):
        super().setUp()
        self.item1 = self.itemType.objects.create(name="OC1",**self.defaults)

    def get_page(self,item):
        url_name = "".join(item._meta.verbose_name.title().split())
        url_name = url_name[0].lower() + url_name[1:]
        return reverse('aristotle:%s'%url_name,args=[item.id])

    def test_help_page_exists(self):
        self.logout()
        #response = self.client.get(self.get_help_page())
        #self.assertEqual(response.status_code,200)

    def test_item_page_exists(self):
        self.logout()
        response = self.client.get(self.get_page(self.item1))
        self.assertEqual(response.status_code,200)

class MeasureViewPage(LoggedInViewUnmanagedPages, TestCase):
    url_name='measure'
    itemType=models.Measure

    def setUp(self):
        super().setUp()

        self.item2 = models.UnitOfMeasure.objects.create(name="OC1",workgroup=self.wg1,measure=self.item1,**self.defaults)

class RegistrationAuthorityViewPage(LoggedInViewUnmanagedPages, TestCase):
    url_name='registrationAuthority'
    itemType=models.RegistrationAuthority

    def setUp(self):
        super().setUp()

        self.item2 = models.DataElement.objects.create(name="OC1",workgroup=self.wg1,**self.defaults)

        models.Status.objects.create(
            concept=self.item2,
            registrationAuthority=self.item1,
            registrationDate=timezone.now(),
            state=models.STATES.standard
        )

    def get_page(self,item):
        return item.get_absolute_url()

    def test_view_all_ras(self):
        self.logout()
        response = self.client.get(reverse('aristotle:all_registration_authorities'))
        self.assertEqual(response.status_code,200)

class OrganizationViewPage(LoggedInViewUnmanagedPages, TestCase):
    url_name='organization'
    itemType=models.Organization

    def setUp(self):
        super().setUp()

    def get_page(self,item):
        return item.get_absolute_url()

    def test_view_all_orgs(self):
        self.logout()
        response = self.client.get(reverse('aristotle:all_organizations'))
        self.assertEqual(response.status_code,200)
