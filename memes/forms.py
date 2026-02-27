from django import forms
from .models import Meme

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
MAX_UPLOAD_SIZE     = 10 * 1024 * 1024  


class ImageUploadForm(forms.Form):

    image = forms.ImageField(
        label="Image",
        error_messages={
            'required':  "Veuillez sélectionner une image.",
            'invalid':   "Le fichier sélectionné n'est pas une image valide.",
        }
    )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                raise forms.ValidationError(
                    f"Format non supporté : {image.content_type}. "
                    f"Utilisez JPG, PNG, GIF ou WEBP."
                )
            if image.size > MAX_UPLOAD_SIZE:
                size_mb = image.size / (1024 * 1024)
                raise forms.ValidationError(
                    f"Fichier trop volumineux ({size_mb:.1f} Mo). Maximum : 10 Mo."
                )
        return image


class MemeCreateForm(forms.Form):

    meme_data    = forms.CharField(widget=forms.HiddenInput())   
    top_text     = forms.CharField(max_length=200, required=False)
    bottom_text  = forms.CharField(max_length=200, required=False)
    font_name    = forms.CharField(max_length=60,  required=False, initial='Impact')
    font_size_top = forms.IntegerField(min_value=8, max_value=200, required=False, initial=42)
    font_size_bot = forms.IntegerField(min_value=8, max_value=200, required=False, initial=42)
    color_top    = forms.CharField(max_length=7,   required=False, initial='#ffffff')
    color_bottom = forms.CharField(max_length=7,   required=False, initial='#ffffff')
    stroke_color_top = forms.CharField(max_length=7,   required=False, initial='#000000')
    stroke_color_bot = forms.CharField(max_length=7,   required=False, initial='#000000')
    stroke_width = forms.IntegerField(min_value=0, max_value=20,   required=False, initial=3)
    is_bold      = forms.BooleanField(required=False, initial=True)
    is_italic    = forms.BooleanField(required=False)
    is_uppercase = forms.BooleanField(required=False, initial=True)

    def clean_meme_data(self):
        data = self.cleaned_data.get('meme_data', '')
        if not data.startswith('data:image/'):
            raise forms.ValidationError("Données d'image invalides.")

        approx_bytes = len(data) * 3 / 4
        if approx_bytes > 20 * 1024 * 1024:
            raise forms.ValidationError("L'image est trop volumineuse.")
        return data

    def clean_color_top(self):
        return self._clean_hex_color('color_top', '#ffffff')

    def clean_color_bottom(self):
        return self._clean_hex_color('color_bottom', '#ffffff')

    def clean_stroke_color_top(self):
        return self._clean_hex_color('stroke_color_top', '#000000')

    def clean_stroke_color_bot(self):
        return self._clean_hex_color('stroke_color_bot', '#000000')

    def _clean_hex_color(self, field: str, default: str) -> str:
        import re
        value = self.cleaned_data.get(field, default) or default
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            return default
        return value.lower()