from django.conf.urls import url
from aristotle_mdr.contrib.identifiers.views import scoped_identifier_redirect, namespace_redirect


urlpatterns = [
    url(r'^identifier/(?P<ns_prefix>.+)/(?P<iid>.+)/(?P<version>.+)?$', scoped_identifier_redirect, name='scoped_identifier_redirect_version'),
    url(r'^identifier/(?P<ns_prefix>.+)/(?P<iid>.+)?$', scoped_identifier_redirect, name='scoped_identifier_redirect'),
    url(r'^identifier/(?P<ns_prefix>.+)?$', namespace_redirect, name='namespace_redirect'),
]
