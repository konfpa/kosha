from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/new/", views.tag_create, name="tag_create"),
    path("tags/<int:pk>/edit/", views.tag_edit, name="tag_edit"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),
]
