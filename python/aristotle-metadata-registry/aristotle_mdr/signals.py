from django.db.models.signals import m2m_changed, post_save, pre_delete
# from reversion.signals import post_revision_commit
import haystack.signals as signals  # .RealtimeSignalProcessor as RealtimeSignalProcessor
from aristotle_mdr.utils import fetch_metadata_apps
# Don't import aristotle_mdr.models directly, only pull in whats required,
#  otherwise Haystack gets into a circular dependancy.

# class AristotleSignalProcessor(signals.BaseSignalProcessor):
# Replace below with this when doing a dataload (shuts off Haystack)
#    pass


# @receiver(pre_save)
def pre_save_clean(sender, instance, *args, **kwargs):
    instance.full_clean()


class AristotleSignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        from aristotle_mdr.models import _concept, ReviewRequest, concept_visibility_updated
        post_save.connect(self.handle_concept_save)
        # post_revision_commit.connect(self.handle_concept_revision)
        pre_delete.connect(self.handle_concept_delete, sender=_concept)
        post_save.connect(self.update_visibility_review_request, sender=ReviewRequest)
        m2m_changed.connect(self.update_visibility_review_request, sender=ReviewRequest.concepts.through)
        concept_visibility_updated.connect(self.handle_concept_recache)
        super().setup()

    def teardown(self):  # pragma: no cover
        from aristotle_mdr.models import _concept
        post_save.disconnect(self.handle_concept_save, sender=_concept)
        # post_revision_commit.disconnect(self.handle_concept_revision)
        pre_delete.disconnect(self.handle_concept_delete, sender=_concept)
        super().teardown()

    def handle_concept_recache(self, concept, **kwargs):
        instance = concept.item
        self.handle_save(instance.__class__, instance)

    def handle_concept_save(self, sender, instance, **kwargs):
        from aristotle_mdr.models import _concept, aristotleComponent
        if isinstance(instance, _concept) and type(instance) is not _concept:
            if instance._meta.app_label in fetch_metadata_apps():
                obj = instance.item
                self.handle_save(obj.__class__, obj, **kwargs)
            else:
                return

        # Components should have parents, but lets be kind.
        if issubclass(sender, aristotleComponent) and hasattr(instance, "parentItem"):
            obj = instance.parentItem.item
            self.handle_save(obj.__class__, obj, **kwargs)

    def handle_concept_delete(self, sender, instance, **kwargs):
        # Delete index *before* the object, as we need to query it to check the actual subclass.
        obj = instance.item
        self.handle_delete(obj.__class__, obj, **kwargs)

    def update_visibility_review_request(self, sender, instance, **kwargs):
        from aristotle_mdr.models import ReviewRequest
        assert(sender in [ReviewRequest, ReviewRequest.concepts.through])
        for concept in instance.concepts.all():
            obj = concept.item
            self.handle_save(obj.__class__, obj, **kwargs)
