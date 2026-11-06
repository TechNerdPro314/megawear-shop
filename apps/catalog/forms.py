from django import forms


class CatalogSearchForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.CharField(required=False)