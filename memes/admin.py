
from django.contrib import admin
from django.utils.html import format_html
from .models import Meme, MemeTemplate


@admin.register(MemeTemplate)
class MemeTemplateAdmin(admin.ModelAdmin):
    list_display   = ['name', 'preview', 'created_at']
    search_fields  = ['name']
    readonly_fields = ['preview']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px; border-radius:4px;">',
                obj.image.url
            )
        return "—"
    preview.short_description = "Aperçu"


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display   = ['id', 'preview', 'top_text', 'bottom_text', 'session_short', 'created_at', 'file_size_kb']
    list_filter    = ['created_at', 'font_name', 'is_bold', 'is_uppercase']
    search_fields  = ['top_text', 'bottom_text', 'session_key']
    readonly_fields = ['preview_large', 'session_key', 'created_at', 'file_size']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Images', {
            'fields': ('preview_large', 'meme_image', 'original_image'),
        }),
        ('Textes', {
            'fields': ('top_text', 'bottom_text'),
        }),
        ('Typographie', {
            'fields': (
                'font_name', 'font_size_top', 'font_size_bot',
                'color_top', 'color_bottom',
                'stroke_color_top', 'stroke_color_bot', 'stroke_width',
                'is_bold', 'is_italic', 'is_uppercase',
            ),
            'classes': ('collapse',),
        }),
        ('Métadonnées', {
            'fields': ('session_key', 'created_at', 'file_size'),
            'classes': ('collapse',),
        }),
    )

    def preview(self, obj):
        if obj.meme_image:
            return format_html(
                '<img src="{}" style="max-height:50px; border-radius:4px;">',
                obj.meme_image.url
            )
        return "—"
    preview.short_description = "Aperçu"

    def preview_large(self, obj):
        if obj.meme_image:
            return format_html(
                '<img src="{}" style="max-width:400px; border-radius:6px;">',
                obj.meme_image.url
            )
        return "—"
    preview_large.short_description = "Aperçu"

    def session_short(self, obj):
        return f"{obj.session_key[:8]}…"
    session_short.short_description = "Session"

    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} Ko"
        return "—"
    file_size_kb.short_description = "Taille"