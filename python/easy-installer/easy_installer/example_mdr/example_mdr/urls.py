from django.conf.urls import include, url

# Below are the 'recommended' locations for the paths to aristotle extensions.
# At this point the 'glossary' extension *requires* being in the root at `/glossary/`.
urlpatterns = (
    url(r'^', include('aristotle_mdr.urls')),
    url(r'^browse/', include('aristotle_mdr.contrib.browse.urls')),
    url(r'^help/', include('aristotle_mdr.contrib.help.urls', app_name="aristotle_help", namespace="aristotle_help")),
    url(r'^', include('aristotle_mdr.contrib.identifiers.urls', app_name="aristotle_mdr_identifiers", namespace="aristotle_identifiers")),
    #url(r'^', include('aristotle_mdr.contrib.links.urls', app_name="aristotle_mdr_links", namespace="aristotle_mdr_links")
#!aristotle_dse!    url(r'^dse/', include('aristotle_dse.urls',app_name="aristotle_dse",namespace="aristotle_dse")),
#!aristotle_glossary!    url(r'^glossary/', include('aristotle_glossary.urls',app_name="aristotle_glossary",namespace="glossary")),
#!aristotle_mdr_api!    url(r'^api/', include('aristotle_mdr_api.urls',app_name="aristotle_mdr_api",namespace="aristotle_mdr_api")),
#!aristotle_graphql!    url(r'^api/graphql/', include('aristotle_mdr_graphql.urls', namespace="aristotle_graphql")),
#!mallard!    url(r'^mallard/', include('mallard_qr.urls',app_name="mallard_qr",namespace="mallard_qr")),
#!comet!    url(r'^comet/', include('comet.urls', namespace='comet')),
    )
