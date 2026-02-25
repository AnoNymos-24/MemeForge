"""
Models — memes app
"""
from django.db import models


class MemeTemplate(models.Model):
    """
    Pre-loaded popular meme templates (managed via Django admin).
    """
    name       = models.CharField(max_length=100, verbose_name="Nom")
    image      = models.ImageField(upload_to='templates/', verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name         = "Template de mème"
        verbose_name_plural  = "Templates de mèmes"
        ordering             = ['name']

    def __str__(self):
        return self.name


class Meme(models.Model):
    """
    A generated meme linked to an anonymous session.
    Stores both the original uploaded image and the final rendered meme.
    """
    # Images
    original_image = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        verbose_name="Image originale",
        blank=True, null=True,
    )
    meme_image = models.ImageField(
        upload_to='memes/%Y/%m/%d/',
        verbose_name="Mème généré",
    )

    # Text overlays
    top_text    = models.CharField(max_length=200, blank=True, verbose_name="Texte du haut")
    bottom_text = models.CharField(max_length=200, blank=True, verbose_name="Texte du bas")

    # Typography settings (stored for potential re-editing)
    font_name      = models.CharField(max_length=60,  default='Impact',   verbose_name="Police")
    font_size_top  = models.PositiveSmallIntegerField(default=42,          verbose_name="Taille texte haut")
    font_size_bot  = models.PositiveSmallIntegerField(default=42,          verbose_name="Taille texte bas")
    color_top      = models.CharField(max_length=7,   default='#ffffff',   verbose_name="Couleur texte haut")
    color_bottom   = models.CharField(max_length=7,   default='#ffffff',   verbose_name="Couleur texte bas")
    stroke_color_top = models.CharField(max_length=7,   default='#000000',   verbose_name="Couleur contour haut")
    stroke_color_bot = models.CharField(max_length=7,   default='#000000',   verbose_name="Couleur contour bas")
    stroke_width   = models.PositiveSmallIntegerField(default=3,            verbose_name="Épaisseur contour")
    is_bold        = models.BooleanField(default=True,                      verbose_name="Gras")
    is_italic      = models.BooleanField(default=False,                     verbose_name="Italique")
    is_uppercase   = models.BooleanField(default=True,                      verbose_name="Majuscules")

    # Session (anonymous user tracking)
    session_key = models.CharField(max_length=40, db_index=True, verbose_name="Clé de session")

    # Metadata
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    file_size   = models.PositiveIntegerField(default=0, verbose_name="Taille fichier (octets)")

    class Meta:
        verbose_name         = "Mème"
        verbose_name_plural  = "Mèmes"
        ordering             = ['-created_at']

    def __str__(self):
        texts = ' / '.join(filter(None, [self.top_text, self.bottom_text]))
        return f"Mème #{self.pk} — {texts or 'sans texte'}"

    def delete(self, *args, **kwargs):
        """Also remove image files from disk on deletion."""
        if self.meme_image:
            storage, name = self.meme_image.storage, self.meme_image.name
            super().delete(*args, **kwargs)
            storage.delete(name)
        else:
            super().delete(*args, **kwargs)
        if self.original_image:
            try:
                self.original_image.storage.delete(self.original_image.name)
            except Exception:
                pass