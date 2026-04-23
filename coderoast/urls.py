from django.urls import path

from . import views

app_name = "coderoast"

urlpatterns = [
    path("", views.index, name="index"),
    path("assets/", views.assets, name="assets"),
    path("roast/", views.roast, name="roast"),
]
