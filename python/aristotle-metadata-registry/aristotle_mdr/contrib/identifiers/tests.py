from django.urls import reverse
from django.test import TestCase

from aristotle_mdr.contrib.identifiers import models as ID
from aristotle_mdr import models as MDR
from aristotle_mdr.tests import utils
from aristotle_mdr.utils import url_slugify_concept, setup_aristotle_test_environment

setup_aristotle_test_environment()


class TestIdentifiers(utils.LoggedInViewPages, TestCase):

    def setUp(self):
        self.jl = MDR.Organization.objects.create(
            name="Justice League of America",
            definition="Fighting for Truth Justice and Liberty"
        )
        self.sra = MDR.Organization.objects.create(
            name="Super-human Registration Authority",
            definition="Protecting humans from unregistered mutant activity"
        )
        self.ns_jla = ID.Namespace.objects.create(
            naming_authority=self.jl,
            shorthand_prefix='jla',
        )
        self.ns_sra = ID.Namespace.objects.create(
            naming_authority=self.sra,
            shorthand_prefix='sra',
        )
        self.meta = MDR.ObjectClass.objects.create(
            name="Metahuman",
            definition=(
                "A human-like being with extranormal powers and abilities,"
                "be they technological, alien, mutant, or magical in nature."
            ),
            references="https://en.wikipedia.org/wiki/Metahuman"
        )
        self.meta_jl_id = ID.ScopedIdentifier.objects.create(
            concept=self.meta.concept, identifier="metahumans", namespace=self.ns_jla
        )
        self.meta_sra_id = ID.ScopedIdentifier.objects.create(
            concept=self.meta.concept, identifier="mutants", namespace=self.ns_sra
        )
        self.meta_jl_id_2 = ID.ScopedIdentifier.objects.create(
            concept=self.meta.concept, identifier="metahuman", namespace=self.ns_jla, version="1"
        )
        super().setUp()

    def test_identifier_displays(self):
        self.assertEqual(
            str(self.meta_jl_id),
            "{0}:{1}:{2}".format(self.jl.name, self.meta_jl_id.identifier, self.meta_jl_id.version)
        )

    def test_identifier_redirects(self):

        response = self.client.get(
            reverse(
                'aristotle_identifiers:scoped_identifier_redirect',
                args=[
                    self.meta_jl_id.namespace.shorthand_prefix,
                    self.meta_jl_id.identifier
                ]
            )
        )
        self.assertRedirects(response, url_slugify_concept(self.meta), fetch_redirect_response=False)

        response = self.client.get(
            reverse(
                'aristotle_identifiers:scoped_identifier_redirect',
                args=[
                    self.meta_sra_id.namespace.shorthand_prefix,
                    self.meta_sra_id.identifier
                ]
            )
        )
        self.assertRedirects(response, url_slugify_concept(self.meta), fetch_redirect_response=False)

    def test_fake_id_redirect(self):
        response = self.client.get(
            reverse(
                'aristotle_identifiers:scoped_identifier_redirect',
                args=[
                    self.meta_sra_id.namespace.shorthand_prefix,
                    "obviously_fake_id"
                ]
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_redirect_with_version(self):
        response = self.client.get(
            reverse(
                'aristotle_identifiers:scoped_identifier_redirect_version',
                args=[
                    self.meta_jl_id_2.namespace.shorthand_prefix,
                    self.meta_jl_id_2.identifier,
                    self.meta_jl_id_2.version
                ]
            )
        )
        self.assertRedirects(response, url_slugify_concept(self.meta), fetch_redirect_response=False)

    def test_redirect_namespace(self):
        response = self.client.get(
            reverse(
                'aristotle_identifiers:namespace_redirect',
                args=[
                    self.ns_jla.shorthand_prefix,
                ]
            )
        )
        self.assertRedirects(response, '/search?q=ns:jla')
