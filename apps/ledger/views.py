import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .choices import PALETTE
from .forms import CategoryForm
from .models import Category


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
