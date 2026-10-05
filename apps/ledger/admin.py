from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "colour", "user")
    list_filter = ("colour",)
    list_select_related = ("user",)
    search_fields = ("name", "user__email")
    autocomplete_fields = ("user",)
