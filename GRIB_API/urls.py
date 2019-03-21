from django.conf.urls import url, include
from rest_framework import routers
from app_1.views import GetParametrosView, GetGribView, GetSectionsView, ListFilesView, GetGribDataView
from app_2.views import ListFilesListView, ListParametrosListView, ListDetailListView, ListSectionsListView

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # API
    url(r'^getParametros/(?P<param>.+)/$', GetParametrosView, name='getParametros'),
    url(r'^getGrib/(?P<param>.+)/(?P<pk>\d+)/$', GetGribView, name='getGrib'),
    url(r'^getSections/(?P<param>.+)/(?P<pk>\d+)/$', GetSectionsView, name='getSections'),
    url(r'^getGribData/(?P<param>.+)/(?P<pk>\d+)/(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)/$', GetGribDataView, name='getGribData'),
    url(r'^listFiles/$', ListFilesView, name='listFiles'),

    # Aplicacao
    url(r'^index/$', ListFilesListView.as_view(), name='indexList'),
    url(r'^parametros/(?P<param>.+)/$', ListParametrosListView.as_view(), name='parametrosList'),
    url(r'^detail/(?P<param>.+)/(?P<pk>\d+)/$', ListDetailListView.as_view(), name='detailList'),
    url(r'^sections/(?P<param>.+)/(?P<pk>\d+)/$', ListSectionsListView.as_view(), name='sectionsList'),

]