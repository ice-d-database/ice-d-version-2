from api import views
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path("calculations/", views.CalculationsList.as_view()),
    path("calculations/<int:pk>/", views.CalculationDetail.as_view()),
    path("calculations/name/<str:name>", views.GetCalculationByName.as_view()),
    path("calculations/run/<str:name>", views.RunCalculationByName.as_view()),
    path("leaflet_map/<str:application_name>", views.GetLeafletMapData.as_view()),
    path("kml/samples/<str:sample_ids>", views.GetSampleKMLs().as_view()),
    path("kml/coresamples/<str:sample_ids>", views.GetCoresampleKMLs().as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
