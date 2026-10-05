import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .choices import PALETTE
from .forms import CategoryForm, TagForm
from .models import Category, Tag


@login_required
def category_list(request):
    return render(
        request,
        "ledger/category_list.html",
        {"categories": request.user.categories.all()},
    )


@login_required
def category_create(request):
    initial = {"icon": "bookmark", "colour": random.choice(list(PALETTE))}  # noqa: S311
    return _category_form(request, Category(user=request.user), initial)


@login_required
def category_edit(request, pk):
    return _category_form(request, get_object_or_404(request.user.categories, pk=pk))


@login_required
@require_POST
def category_delete(request, pk):
    get_object_or_404(request.user.categories, pk=pk).delete()
    return redirect("category_list")


def _category_form(request, category, initial=None):
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category, initial=initial)
    return render(request, "ledger/category_form.html", {"form": form})


@login_required
def tag_list(request):
    return render(request, "ledger/tag_list.html", {"tags": request.user.tags.all()})


@login_required
def tag_create(request):
    return _tag_form(request, Tag(user=request.user))


@login_required
def tag_edit(request, pk):
    return _tag_form(request, get_object_or_404(request.user.tags, pk=pk))


@login_required
@require_POST
def tag_delete(request, pk):
    get_object_or_404(request.user.tags, pk=pk).delete()
    return redirect("tag_list")


def _tag_form(request, tag):
    if request.method == "POST":
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect("tag_list")
    else:
        form = TagForm(instance=tag)
    return render(request, "ledger/tag_form.html", {"form": form})
