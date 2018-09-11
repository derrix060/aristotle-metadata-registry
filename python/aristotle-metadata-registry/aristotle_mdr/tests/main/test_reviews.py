from django.urls import reverse
from django.test import TestCase, tag
import aristotle_mdr.models as models
import aristotle_mdr.tests.utils as utils
from aristotle_mdr.utils import url_slugify_concept

import datetime
from aristotle_mdr.utils import setup_aristotle_test_environment


setup_aristotle_test_environment()


class ReviewRequestActionsPage(utils.LoggedInViewPages, TestCase):
    def setUp(self):
        super().setUp()

        # There would be too many tests to test every item type against every other
        # But they all have identical logic, so one test should suffice
        self.item1 = models.ObjectClass.objects.create(name="Test Item 1 (visible to tested viewers)",definition="my definition",workgroup=self.wg1)
        self.item2 = models.ObjectClass.objects.create(name="Test Item 2 (NOT visible to tested viewers)",definition="my definition",workgroup=self.wg2)
        self.item3 = models.ObjectClass.objects.create(name="Test Item 3 (only visible to the editor)",definition="my definition",workgroup=None,submitter=self.editor)

        self.item4 = models.ValueDomain.objects.create(name='Test Value Domain', definition='my definition', workgroup=self.wg1)
        self.item5 = models.DataElement.objects.create(name='Test data element', definition='my definition', workgroup=self.wg1, valueDomain=self.item4)

    def check_item_status(self, item, review, updated):

        self.assertEqual(item.is_public(), updated)
        self.assertEqual(item.current_statuses().count() == 1, updated)

        if updated:
            state = item.current_statuses().first()

            self.assertTrue(state.registrationAuthority == review.registration_authority)
            self.assertTrue(state.state == review.state)
            self.assertTrue(state.registrationDate == review.registration_date)
        else:
            self.assertTrue(item.current_statuses().count() == 0)

    def post_public_rr(self, item):
        response = self.client.post(
            reverse('aristotle:request_review',args=[item.id]),
            {
                'registrationAuthorities': [str(self.ra.id)],
                'state': self.ra.public_state,
                'cascadeRegistration': 0,
                'changeDetails': "Please review this",
                'registrationDate':datetime.date(2010,1,1)
            }
        )
        return response

    def test_viewer_cannot_request_review_for_private_item(self):
        self.login_viewer()

        response = self.client.get(reverse('aristotle:request_review',args=[self.item3.id]))
        self.assertEqual(response.status_code,403)

        response = self.client.get(reverse('aristotle:request_review',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

        response = self.client.get(reverse('aristotle:request_review',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

    def test_viewer_can_request_review(self):
        self.login_editor()

        response = self.client.get(reverse('aristotle:request_review',args=[self.item3.id]))
        self.assertEqual(response.status_code,200)

        response = self.client.get(reverse('aristotle:request_review',args=[self.item2.id]))
        self.assertEqual(response.status_code,403)

        response = self.client.get(reverse('aristotle:request_review',args=[self.item1.id]))
        self.assertEqual(response.status_code,200)

        self.assertEqual(self.item1.review_requests.count(),0)
        response = self.post_public_rr(self.item1)

        self.assertRedirects(response,url_slugify_concept(self.item1))
        self.assertEqual(self.item1.review_requests.count(),1)

    def test_registrar_has_valid_items_in_review(self):

        item1 = models.ObjectClass.objects.create(name="Test Item 1",definition="my definition",workgroup=self.wg1)
        item2 = models.ObjectClass.objects.create(name="Test Item 2",definition="my definition",workgroup=self.wg2)
        item3 = models.ObjectClass.objects.create(name="Test Item 3",definition="my definition",workgroup=self.wg1)
        item4 = models.ObjectClass.objects.create(name="Test Item 4",definition="my definition",workgroup=self.wg2)

        self.login_registrar()

        response = self.client.get(reverse('aristotle:userReadyForReview',))
        self.assertEqual(response.status_code,200)

        self.assertEqual(len(response.context['page']),0)

        review = models.ReviewRequest.objects.create(
            requester=self.su,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(item1)
        review.concepts.add(item4)

        response = self.client.get(reverse('aristotle:userReadyForReview',))
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context['page']),1)

        review = models.ReviewRequest.objects.create(
            requester=self.su,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(item1)

        response = self.client.get(reverse('aristotle:userReadyForReview',))
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context['page']),2)

        other_ra = models.RegistrationAuthority.objects.create(name="A different ra")
        review = models.ReviewRequest.objects.create(
            requester=self.su,
            registration_authority=other_ra,
            state=other_ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(item2)

        response = self.client.get(reverse('aristotle:userReadyForReview',))
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context['page']),2)

        other_ra.giveRoleToUser('registrar',self.registrar)
        response = self.client.get(reverse('aristotle:userReadyForReview',))
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.context['page']),3)

    def test_superuser_can_see_review(self):
        self.login_superuser()
        other_ra = models.RegistrationAuthority.objects.create(name="A different ra")

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=other_ra,
            state=other_ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

    def test_registrar_can_see_review(self):
        self.login_registrar()
        other_ra = models.RegistrationAuthority.objects.create(name="A different ra")

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=other_ra,
            state=other_ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,404)

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,404)

    def test_anon_cannot_see_review(self):
        self.logout()

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,302)
        # is redirected to login

    def test_editor_can_see_review(self):
        self.login_editor()

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )
        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        response = self.client.get(reverse('aristotle:userReviewDetails',args=[review.pk]))
        self.assertEqual(response.status_code,200)

    def registrar_can_accept_review(self, review_changes=False):
        self.login_registrar()
        other_ra = models.RegistrationAuthority.objects.create(name="A different ra")

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=other_ra,
            state=other_ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )
        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code,403)

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )
        review.concepts.add(self.item1)
        review.concepts.add(self.item2)

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code,403)

        response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
            {
                'review_accept-response': "I can't accept this, its cancelled",
                'review_accept_view-current_step': 'review_accept',
                'submit_skip': 'value',
            })

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertEqual(response.status_code,403)
        self.assertEqual(review.status, models.REVIEW_STATES.cancelled)
        self.assertTrue(bool(review.response) == False)

        review.status = models.REVIEW_STATES.submitted
        review.save()

        self.assertTrue(self.item1.current_statuses().count() == 0)

        self.item1 = models.ObjectClass.objects.get(pk=self.item1.pk) # decache
        self.assertFalse(self.item1.is_public())

        if review_changes:
            button = "submit_next"
        else:
            button = "submit_skip"

        response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
            {
                'review_accept-response': "I can accept this!",
                'review_accept_view-current_step': 'review_accept',
                button: 'value',
            })

        if review_changes:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['wizard']['steps'].step1, 2) # check we are now on second setep
            selected_for_change = [self.item1.id]
            selected_for_change_strings = [str(a) for a in selected_for_change]

            review_response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
                {
                    'review_changes-selected_list': selected_for_change_strings,
                    'review_accept_view-current_step': 'review_changes'
                })

            self.assertRedirects(review_response,reverse('aristotle:userReadyForReview'))

        else:
            self.assertRedirects(response,reverse('aristotle:userReadyForReview'))

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertEqual(review.response, "I can accept this!")
        self.assertEqual(review.status,models.REVIEW_STATES.accepted)
        self.assertEqual(review.reviewer, self.registrar)

        self.item1 = models.ObjectClass.objects.get(pk=self.item1.pk) # decache
        self.item2 = models.ObjectClass.objects.get(pk=self.item2.pk) # decache

        if review_changes:
            updated_items = [self.item1.pk]
        else:
            updated_items = [self.item1.pk, self.item2.pk]

        for item in [self.item1, self.item2]:
            if item.id in updated_items:
                updated = True
            else:
                updated = False

            self.check_item_status(item, review, updated)

    @tag('changestatus')
    def test_registrar_can_accept_review_direct(self):
        self.registrar_can_accept_review(review_changes=False)

    @tag('changestatus')
    def test_registrar_can_accept_review_alter_changes(self):
        self.registrar_can_accept_review(review_changes=True)

    def test_registrar_can_reject_review(self):
        self.login_registrar()
        other_ra = models.RegistrationAuthority.objects.create(name="A different ra")

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=other_ra,
            state=other_ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertEqual(response.status_code,403)

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertEqual(response.status_code,403)

        response = self.client.post(reverse('aristotle:userReviewReject',args=[review.pk]),
            {
                'response':"I can't reject this, its cancelled"
            })

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertEqual(response.status_code,403)
        self.assertEqual(review.status, models.REVIEW_STATES.cancelled)
        self.assertTrue(bool(review.response) == False)

        review.status = models.REVIEW_STATES.submitted
        review.save()

        response = self.client.post(reverse('aristotle:userReviewReject',args=[review.pk]),
            {
                'response':"I can reject this!",
            })
        #self.assertEqual(response.status_code,200)
        self.assertRedirects(response,reverse('aristotle:userReadyForReview',))

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertEqual(review.response, "I can reject this!")
        self.assertEqual(review.status,models.REVIEW_STATES.rejected)
        self.assertEqual(review.reviewer, self.registrar)

        self.item1 = models.ObjectClass.objects.get(pk=self.item1.pk) # decache
        self.assertFalse(self.item1.is_public())

    # Function used by the 2 tests below
    def registrar_can_accept_cascade_review(self, review_changes=True):
        self.login_registrar()

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1),
            cascade_registration=1,
        )

        review.concepts.add(self.item5)

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        if review_changes:
            button = 'submit_next'
        else:
            button = 'submit_skip'

        response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
            {
                'review_accept-response': "I can accept this!",
                'review_accept_view-current_step': 'review_accept',
                button: 'value',
            })

        if review_changes:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['wizard']['steps'].step1, 2) # check we are now on second setep
            selected_for_change = [self.item4.id, self.item5.id]
            selected_for_change_strings = [str(a) for a in selected_for_change]

            review_response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
                {
                    'review_changes-selected_list': selected_for_change_strings,
                    'review_accept_view-current_step': 'review_changes'
                })

            self.assertRedirects(review_response,reverse('aristotle:userReadyForReview'))

        else:
            self.assertEqual(response.status_code, 302)

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertEqual(review.response, "I can accept this!")
        self.assertEqual(review.status,models.REVIEW_STATES.accepted)
        self.assertEqual(review.reviewer, self.registrar)

        self.item4 = models.ValueDomain.objects.get(pk=self.item4.pk) # decache
        self.item5 = models.DataElement.objects.get(pk=self.item5.pk) # decache

        for item in [self.item4, self.item5]:
            self.check_item_status(item, review, True)

    @tag('changestatus')
    def test_registrar_can_accept_cascade_review_direct(self):
        self.registrar_can_accept_review(review_changes=False)

    @tag('changestatus')
    def test_registrar_can_accept_cascade_review_revstep(self):
        self.registrar_can_accept_review(review_changes=True)

    def test_user_can_cancel_review(self):
        self.login_editor()

        review = models.ReviewRequest.objects.create(
            requester=self.viewer,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewCancel',args=[review.pk]))
        self.assertEqual(response.status_code,403)

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewCancel',args=[review.pk]))
        self.assertEqual(response.status_code,200)

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        response = self.client.get(reverse('aristotle:userReviewCancel',args=[review.pk]))
        self.assertRedirects(response,reverse('aristotle:userReviewDetails',args=[review.pk]))

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        self.assertFalse(review.status == models.REVIEW_STATES.cancelled)
        response = self.client.post(reverse('aristotle:userReviewCancel',args=[review.pk]),{})
        self.assertRedirects(response,reverse('aristotle:userMyReviewRequests',))

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache
        self.assertTrue(review.status == models.REVIEW_STATES.cancelled)

    def test_registrar_cant_load_rejected_or_accepted_review(self):
        self.login_registrar()
        models.RegistrationAuthority.objects.create(name="A different ra")

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            status=models.REVIEW_STATES.accepted,
            state=models.STATES.standard,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertRedirects(response,reverse('aristotle_mdr:userReviewDetails', args=[review.pk]))

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertRedirects(response,reverse('aristotle_mdr:userReviewDetails', args=[review.pk]))

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            status=models.REVIEW_STATES.rejected,
            state=models.STATES.standard,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertRedirects(response,reverse('aristotle_mdr:userReviewDetails', args=[review.pk]))

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertRedirects(response,reverse('aristotle_mdr:userReviewDetails', args=[review.pk]))

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            status=models.REVIEW_STATES.cancelled,
            state=models.STATES.standard,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        response = self.client.get(reverse('aristotle:userReviewReject',args=[review.pk]))
        self.assertEqual(response.status_code,403)
        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code,403)

    def test_who_can_see_review(self):
        from aristotle_mdr.perms import user_can_view_review

        review = models.ReviewRequest.objects.create(
            requester=self.editor,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        review.concepts.add(self.item1)

        self.assertTrue(user_can_view_review(self.editor,review))
        self.assertTrue(user_can_view_review(self.registrar,review))
        self.assertTrue(user_can_view_review(self.su,review))
        self.assertFalse(user_can_view_review(self.viewer,review))

        review.status = models.REVIEW_STATES.cancelled
        review.save()

        review = models.ReviewRequest.objects.get(pk=review.pk) #decache

        self.assertTrue(user_can_view_review(self.editor,review))
        self.assertFalse(user_can_view_review(self.registrar,review))
        self.assertTrue(user_can_view_review(self.su,review))
        self.assertFalse(user_can_view_review(self.viewer,review))

    def test_notifications(self):
        viewer_num_notifications = self.viewer.notifications.count()
        registrar_num_notifications = self.registrar.notifications.count()
        editor_num_notifications = self.editor.notifications.count()

        review = models.ReviewRequest.objects.create(
            requester=self.viewer,
            registration_authority=self.ra,
            state=self.ra.public_state,
            registration_date=datetime.date(2010,1,1)
        )

        # Review requested, does a registrar get the notification?
        self.assertTrue(self.viewer.notifications.count() == viewer_num_notifications)
        self.assertTrue(self.registrar.notifications.count() == registrar_num_notifications + 1)
        self.assertTrue(self.editor.notifications.count() == editor_num_notifications)

        self.assertTrue(self.registrar.notifications.first().target == review)

        review.status = models.REVIEW_STATES.accepted
        review.save()

        # Review updated, does the requester get the notification?
        self.assertTrue(self.viewer.notifications.count() == viewer_num_notifications + 1)
        self.assertTrue(self.registrar.notifications.count() == registrar_num_notifications + 1)
        self.assertTrue(self.editor.notifications.count() == editor_num_notifications)

        self.assertTrue(self.viewer.notifications.first().target == review)

    @tag('inactive_ra')
    def test_cannot_create_rr_against_incative_ra(self):
        self.login_editor()
        self.ra.active = 1
        self.ra.save()

        self.assertEqual(self.item1.review_requests.count(),0)

        response = self.post_public_rr(self.item1)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('registrationAuthorities' in response.context['form'].errors)
        self.assertEqual(self.item1.review_requests.count(),0)

    @tag('inactive_ra')
    def test_cannot_accept_rr_with_inactive_ra(self):
        self.login_editor()

        # Create review request
        response = self.post_public_rr(self.item3)
        self.assertEqual(self.item3.review_requests.count(),1)
        review = self.item3.review_requests.all()[0]

        # Make ra inactive
        self.ra.active = 1
        self.ra.save()

        response = self.client.get(reverse('aristotle:userReviewAccept',args=[review.pk]))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('aristotle:userReviewAccept',args=[review.pk]),
            {
                'review_accept-response': "I can accept this!",
                'review_accept_view-current_step': 'review_accept',
                'submit_skip': 'value',
            })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.item3.review_requests.count(),1)

    @tag('inactive_ra')
    def test_reviews_hidden_from_lists_when_ra_inactive(self):
        self.login_viewer()

        # Create review request
        response = self.post_public_rr(self.item1)
        self.assertEqual(self.item1.review_requests.count(),1)

        # Make ra inactive
        self.ra.active = 1
        self.ra.save()

        # My review requests
        response = self.client.get(reverse('aristotle_mdr:userMyReviewRequests'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['reviews']), 0)

        # Registrar Review list
        self.login_registrar()
        response  = self.client.get(reverse('aristotle_mdr:userReadyForReview'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['reviews']), 0)
