from aristotle_mdr.tests.migrations import MigrationsTestCase
from aristotle_mdr.utils import migrations as migration_utils
from aristotle_mdr import models
from aristotle_mdr.contrib.slots import models as slots_models

from django.core.exceptions import FieldDoesNotExist
from django.conf import settings
from django.test import TestCase, tag
from django.apps import apps as current_apps


class TestUtils(TestCase):

    def test_forward_slot_move(self):
        oc1 = models.ObjectClass.objects.create(
            name='Test OC',
            definition='Test Definition',
            version='1.11.1'
        )

        oc2 = models.ObjectClass.objects.create(
            name='Test Blank OC',
            definition='Test Definition'
        )

        migration_utils.move_field_to_slot(current_apps, None, 'version')

        self.assertEqual(oc1.slots.count(), 1)
        self.assertEqual(oc2.slots.count(), 0)

        slots = oc1.slots.all()

        self.assertEqual(slots[0].name, 'version')
        self.assertEqual(slots[0].value, '1.11.1')

    def test_backwards_slot_move(self):

        oc1 = models.ObjectClass.objects.create(
            name='Test OC',
            definition='Test Definition',
            version=''
        )

        slot1 = slots_models.Slot.objects.create(
            name='version',
            concept=oc1,
            value='2.222'
        )

        slot2 = slots_models.Slot.objects.create(
            name='otherslot',
            concept=oc1,
            value='othervalue'
        )

        migration_utils.move_slot_to_field(current_apps, None, 'version')

        # Have to get from db again
        oc1 = models.ObjectClass.objects.get(id=oc1.id)
        self.assertEqual(oc1.version, '2.222')


class TestSynonymMigration(MigrationsTestCase, TestCase):

    migrate_from = '0023_auto_20180206_0332'
    migrate_to = '0024_synonym_data_migration'

    def setUpBeforeMigration(self, apps):
        objectclass = apps.get_model('aristotle_mdr', 'ObjectClass')

        self.oc1 = objectclass.objects.create(
            name='Test OC',
            definition='Test Definition',
            synonyms='great'
        )

        self.oc2 = objectclass.objects.create(
            name='Test Blank OC',
            definition='Test Definition'
        )

    def test_migration(self):

        slot = self.apps.get_model('aristotle_mdr_slots', 'Slot')

        self.assertEqual(slot.objects.count(), 1)

        syn_slot = slot.objects.get(name='Synonyms')
        self.assertEqual(syn_slot.concept.name, self.oc1.name)
        self.assertEqual(syn_slot.concept.definition, self.oc1.definition)
        self.assertEqual(syn_slot.value, 'great')

#class TestSynonymMigrationReverse(MigrationsTestCase, TestCase):
#
#    migrate_from = '0024_synonym_data_migration'
#    migrate_to = '0023_auto_20180206_0332'
#
#    def setUpBeforeMigration(self, apps):
#        objectclass = apps.get_model('aristotle_mdr', 'ObjectClass')
#        slot = apps.get_model('aristotle_mdr_slots', 'Slot')
#
#        self.oc = objectclass.objects.create(
#            name='Test OC',
#            definition='Test Definition',
#            synonyms='great'
#        )
#
#        self.slot = slot.objects.create(
#            name='Synonyms',
#            concept=self.oc,
#            value='amazing'
#        )
#
#    def test_migration(self):
#
#        objectclass = self.apps.get_model('aristotle_mdr', 'ObjectClass')
#
#        oc = objectclass.objects.get(pk=self.oc.pk)
#        self.assertEqual(oc.synonyms, 'amazing')

class TestDedMigration(MigrationsTestCase, TestCase):

    migrate_from = '0026_auto_20180411_2323'
    #migrate_to = '0028_replace_old_ded_through'
    migrate_to = '0027_add_ded_through_models'

    def setUpBeforeMigration(self, apps):

        ded = apps.get_model('aristotle_mdr', 'DataElementDerivation')
        de = apps.get_model('aristotle_mdr', 'DataElement')

        self.ded1 = ded.objects.create(
            name='DED1',
            definition='test defn',
        )

        self.de1 = de.objects.create(
            name='DE1',
            definition='test defn',
        )

        self.de2 = de.objects.create(
            name='DE2',
            definition='test defn',
        )

        self.de3 = de.objects.create(
            name='DE3',
            definition='test defn',
        )

        self.ded1.derives.add(self.de1)
        self.ded1.derives.add(self.de2)
        self.ded1.inputs.add(self.de3)

    def test_migration(self):

        ded = self.apps.get_model('aristotle_mdr', 'DataElementDerivation')
        ded_inputs_through = self.apps.get_model('aristotle_mdr', 'DedInputsThrough')
        ded_derives_through = self.apps.get_model('aristotle_mdr', 'DedDerivesThrough')

        ded_obj = ded.objects.get(pk=self.ded1.pk)

        # Test through objects order

        items = ded_inputs_through.objects.filter(data_element_derivation=ded_obj)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.order, 0)
        self.assertEqual(item.data_element.pk, self.de3.pk)

        items = ded_derives_through.objects.filter(data_element_derivation=ded_obj).order_by('order')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].order, 0)
        self.assertEqual(items[1].order, 1)

        de_pks = [item.data_element.pk for item in items]
        orig_de_pks = [self.de1.pk, self.de2.pk]

        self.assertEqual(set(de_pks), set(orig_de_pks))


class TestLowercaseEmailMigration(MigrationsTestCase, TestCase):

    app = 'aristotle_mdr_user_management'
    migrate_from = '0001_initial'
    migrate_to = '0002_lowercase_emails'

    def setUpBeforeMigration(self, apps):
        user = apps.get_model('aristotle_mdr_user_management', 'User')

        user.objects.create(
            email='FIRST@example.com',
        )
        user.objects.create(
            email='Second@example.com',
        )

    def test_migration(self):
        user = self.apps.get_model('aristotle_mdr_user_management', 'User')
        self.assertEqual(user.objects.count(), 2)
        self.assertTrue(user.objects.filter(email='first@example.com').exists())
        self.assertTrue(user.objects.filter(email='second@example.com').exists())
        self.assertFalse(user.objects.filter(email='FIRST@example.com').exists())
        self.assertFalse(user.objects.filter(email='Second@example.com').exists())


class TestRaActiveMigration(MigrationsTestCase, TestCase):

    migrate_from = '0032_add_new_active'
    migrate_to = '0033_ra_levels'

    def setUpBeforeMigration(self, apps):

        ra = apps.get_model('aristotle_mdr', 'RegistrationAuthority')

        self.ra1 = ra.objects.create(
            name='ActiveRA',
            definition='defn',
            active=True
        )
        self.ra2 = ra.objects.create(
            name='InactiveRA',
            definition='defn',
            active=False
        )

    def test_migration(self):

        ra = self.apps.get_model('aristotle_mdr', 'RegistrationAuthority')
        from aristotle_mdr.models import RA_ACTIVE_CHOICES

        activera = ra.objects.get(name='ActiveRA')
        self.assertEqual(activera.new_active, RA_ACTIVE_CHOICES.active)

        inactivera = ra.objects.get(name='InactiveRA')
        self.assertEqual(inactivera.new_active, RA_ACTIVE_CHOICES.inactive)
