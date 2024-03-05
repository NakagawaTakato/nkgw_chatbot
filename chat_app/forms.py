# forms.py

from django import forms
from django.conf import settings

class LanguageForm(forms.Form):
    language = forms.ChoiceField(choices=settings.LANGUAGES, required=True)
