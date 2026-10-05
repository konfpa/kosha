from django import forms

from .choices import COLOURS, ICONS
from .models import Category


class CategoryForm(forms.ModelForm):
    # Declared rather than generated so the radios get no blank "---------" choice.
    icon = forms.ChoiceField(
        choices=ICONS, widget=forms.RadioSelect(attrs={"class": "sr-only"})
    )
    colour = forms.ChoiceField(
        choices=COLOURS, widget=forms.RadioSelect(attrs={"class": "sr-only"})
    )

    class Meta:
        model = Category
        fields = ("name", "icon", "colour")

    def clean_name(self):
        name = self.cleaned_data["name"]
        clash = self.instance.user.categories.filter(name__iexact=name).exclude(
            pk=self.instance.pk
        )
        if clash.exists():
            raise forms.ValidationError(f"You already have a category called “{name}”.")
        return name
