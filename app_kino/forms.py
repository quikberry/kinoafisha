from django import forms
from .models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ["title", "original_title", "genres",
                  "release_date", "country", "duration",
                  "age_rating", "poster", "description"]
        widgets = {
            "release_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "genres": forms.SelectMultiple(attrs={"size": 8})
        }

