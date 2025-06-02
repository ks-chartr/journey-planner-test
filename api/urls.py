"""
This file contains the URL patterns for the API app.
"""

from django.urls import path
from api.views import *

app_name = "api"

urlpatterns = [
    path("", MultiModal.index, name="index"),  # This is the home page of the Directions app, redirects to the version-2
    path("v2/get_multi_modal/", MultiModal.as_view(), name="multi_v2"),  # This is the version-2 of the Directions app
    path("v2/get_stops/", Stops.as_view(), name="stops_v2"),
]
