import base.views as views
from base.models import Calculation
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic.base import RedirectView
from rest_framework import routers, serializers, viewsets


class CalculationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Calculation
        fields = ["name", "calculation_service_endpoint", "variable_json"]


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "is_staff"]


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CalculationsViewSet(viewsets.ModelViewSet):
    queryset = Calculation.objects.all()
    serializer_class = CalculationSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"users", UserViewSet)

router.register(r"calculations", CalculationsViewSet)

# Favicon redirection
favicon_view = RedirectView.as_view(url="/static/favicon.ico", permanent=True)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # Admin/Auth Routes
    path("favicon.ico", favicon_view),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("logout", LogoutView.as_view()),
    # API Routes
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include(router.urls)),
    path("api/", include("api.urls")),
    # Template driven routes
    path("", views.home),
    path("<application_name>/", views.landing),
    path("<application_name>/cores/", views.cores),
    path("<application_name>/core/<core_name>/", views.core),
    path("<application_name>/coresample/<coresample_name>", views.coresample),
    path("<application_name>/publications", views.publications),
    path("<application_name>/publication/<int:pub_id>/", views.publication),
    path("<application_name>/nsf/", views.nsf),
    path("<application_name>/nsf/<int:project_id>", views.nsf_samples),
    path("<application_name>/cal_data_set/", views.cal_data_set),
    path("<application_name>/cal_data_set/<int:cd_id>", views.cal_data_set_samples),
    path("<application_name>/sites/", views.sites),
    path("<application_name>/sites/<continent>/", views.sites),
    path("<application_name>/site/<site_name>/", views.site),
    path("<application_name>/sample/<sample_name>/", views.sample),
    path("<application_name>/pubyears", views.pubYears),
    path("<application_name>/pubyear/<int:year>/", views.pubYear),
    path("<application_name>/sitemap/<str:site>/<str:lat>/<str:lon>/<int:zoom>", views.sitemap),
]

urlpatterns += staticfiles_urlpatterns()
