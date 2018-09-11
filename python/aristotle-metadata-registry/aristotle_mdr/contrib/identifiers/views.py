from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse

from aristotle_mdr.models import _concept
from aristotle_mdr.utils import url_slugify_concept


def scoped_identifier_redirect(request, ns_prefix, iid, version=None):
    objs = _concept.objects.filter(
        identifiers__namespace__shorthand_prefix=ns_prefix,
        identifiers__identifier=iid
    )

    if version:
        objs.filter(identifiers__version=version)

    if objs.count() == 0:
        raise Http404
    elif objs.count() == 1:
        return redirect(url_slugify_concept(objs.first().item))
    else:
        item = objs.order_by('version').last()  # lets hope there is an order to the versions.
        return redirect(url_slugify_concept(item.item))


def namespace_redirect(request, ns_prefix):
    search_url = reverse('aristotle_mdr:search')
    return redirect(search_url + '?q=ns:' + ns_prefix)
