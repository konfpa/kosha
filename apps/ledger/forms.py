from django import forms

from .choices import COLOURS, ICONS
from .models import Category, Tag


class NoteField(forms.CharField):
    # Browsers submit line breaks as CRLF; normalise before validation so each
    # counts as the one character the user sees.
    def to_python(self, value):
        return super().to_python(value).replace("\r\n", "\n")


class CategoryForm(forms.ModelForm):
    # Declared rather than generated so the radios get no blank "---------" choice.
    icon = forms.ChoiceField(
        choices=ICONS, widget=forms.RadioSelect(attrs={"class": "sr-only"})
    )
    colour = forms.ChoiceField(
        choices=COLOURS, widget=forms.RadioSelect(attrs={"class": "sr-only"})
    )
    note = NoteField(required=False, max_length=1000)

    class Meta:
        model = Category
        fields = ("name", "description", "icon", "colour", "note")

    def clean_name(self):
        name = self.cleaned_data["name"]
        clash = self.instance.user.categories.filter(name__iexact=name).exclude(
            pk=self.instance.pk
        )
        if clash.exists():
            raise forms.ValidationError(f"You already have a category called “{name}”.")
        return name


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ("name",)

    def clean_name(self):
        name = self.cleaned_data["name"]
        clash = self.instance.user.tags.filter(name__iexact=name).exclude(
            pk=self.instance.pk
        )
        if clash.exists():
            raise forms.ValidationError(f"You already have a tag called “{name}”.")
        return name
