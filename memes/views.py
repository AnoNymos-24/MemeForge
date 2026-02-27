import io
import uuid
import logging

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import (
    FileResponse, HttpResponseBadRequest,
    JsonResponse, HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET

from .forms import ImageUploadForm, MemeCreateForm
from .models import Meme
from .utils import generate_meme_from_base64, generate_meme_from_upload

logger = logging.getLogger(__name__)



def _get_session_key(request) -> str:
    """
    Return (and create if needed) a session key for anonymous user tracking.
    """
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key



def index(request):
    """
    Main meme editor page.
    Shows the canvas editor + a preview of the user's last 8 memes.
    Templates mèmes sont chargés côté client (editor.js TEMPLATES array).
    """
    session_key  = _get_session_key(request)
    recent_memes = (
        Meme.objects
        .filter(session_key=session_key)
        .order_by('-created_at')[:8]
    )

    context = {
        'recent_memes': recent_memes,
        'upload_form':  ImageUploadForm(),
    }
    return render(request, 'memes/index.html', context)



@require_POST
def save_meme(request):
    """
    Receive the base64-encoded canvas image + metadata from the JS editor,
    generate the final image with Pillow, and persist to DB.
    """
    session_key = _get_session_key(request)
    form = MemeCreateForm(request.POST)

    if not form.is_valid():
        logger.warning("MemeCreateForm invalid: %s", form.errors)
        messages.error(request, "Données invalides. Veuillez réessayer.")
        return redirect('memes:index')

    cd = form.cleaned_data

    try:
            buffer = generate_meme_from_base64(
            data_url      = cd['meme_data'],
            top_text      = cd.get('top_text', ''),
            bottom_text   = cd.get('bottom_text', ''),
            font_name     = cd.get('font_name') or 'Impact',
            font_size_top = cd.get('font_size_top') or 42,
            font_size_bot = cd.get('font_size_bot') or 42,
            color_top     = cd.get('color_top') or '#ffffff',
            color_bottom  = cd.get('color_bottom') or '#ffffff',
            stroke_color_top = cd.get('stroke_color_top') or '#000000',
            stroke_color_bot = cd.get('stroke_color_bot') or '#000000',
            stroke_width  = cd.get('stroke_width') or 3,
            is_bold       = cd.get('is_bold', True),
            is_italic     = cd.get('is_italic', False),
            is_uppercase  = cd.get('is_uppercase', True),
        )
    except Exception as exc:
        logger.exception("Error generating meme: %s", exc)
        messages.error(request, "Erreur lors de la génération du mème.")
        return redirect('memes:index')

    image_data    = buffer.read()
    filename      = f"meme_{uuid.uuid4().hex[:12]}.png"
    image_content = ContentFile(image_data, name=filename)

    meme = Meme.objects.create(
        session_key      = session_key,
        meme_image       = image_content,
        top_text         = cd.get('top_text', ''),
        bottom_text      = cd.get('bottom_text', ''),
        font_name        = cd.get('font_name') or 'Impact',
        font_size_top    = cd.get('font_size_top') or 42,
        font_size_bot    = cd.get('font_size_bot') or 42,
        color_top        = cd.get('color_top') or '#ffffff',
        color_bottom     = cd.get('color_bottom') or '#ffffff',
        stroke_color_top = cd.get('stroke_color_top') or '#000000',
        stroke_color_bot = cd.get('stroke_color_bot') or '#000000',
        stroke_width     = cd.get('stroke_width') or 3,
        is_bold          = cd.get('is_bold', True),
        is_italic        = cd.get('is_italic', False),
        is_uppercase     = cd.get('is_uppercase', True),
        file_size        = len(image_data),
    )

    messages.success(request, f"✅ Mème #{meme.pk} sauvegardé dans la galerie !")
    logger.info("Meme #%s created for session %s", meme.pk, session_key[:8])
    return redirect('memes:gallery')



def gallery(request):
    """
    Paginated masonry gallery of memes for the current session.
    Supports ?sort=newest|oldest and ?page=N
    """
    session_key = _get_session_key(request)
    sort        = request.GET.get('sort', 'newest')

    qs = Meme.objects.filter(session_key=session_key)
    qs = qs.order_by('created_at') if sort == 'oldest' else qs.order_by('-created_at')

    page_size = getattr(settings, 'GALLERY_PAGE_SIZE', 12)
    paginator = Paginator(qs, page_size)
    memes     = paginator.get_page(request.GET.get('page'))

    context = {
        'memes':       memes,
        'sort':        sort,
        'total_count': qs.count(),
    }
    return render(request, 'memes/gallery.html', context)



@require_POST
def delete_meme(request, pk):
    """
    Delete a meme (only if it belongs to the current session).
    """
    session_key = _get_session_key(request)
    meme = get_object_or_404(Meme, pk=pk)

    if meme.session_key != session_key:
        return HttpResponseForbidden("Vous ne pouvez pas supprimer ce mème.")

    meme.delete()
    messages.success(request, "🗑 Mème supprimé.")
    logger.info("Meme #%s deleted for session %s", pk, session_key[:8])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'deleted', 'id': pk})
    return redirect('memes:gallery')



@require_GET
def download_meme(request, pk):
    """
    Stream the meme image as a downloadable file.
    """
    session_key = _get_session_key(request)
    meme = get_object_or_404(Meme, pk=pk)

    if meme.session_key != session_key:
        return HttpResponseForbidden("Accès refusé.")

    try:
        response = FileResponse(
            meme.meme_image.open('rb'),
            content_type='image/png',
            as_attachment=True,
            filename=f'meme-memeforge-{meme.pk}.png',
        )
        return response
    except FileNotFoundError:
        return HttpResponseBadRequest("Fichier introuvable.")



@require_POST
def upload_image(request):
    """
    AJAX endpoint: upload a raw image and return its temp URL.
    Used optionally when the user wants server-side pre-processing.
    """
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': form.errors.get('image', ['Erreur inconnue'])[0]}, status=400)

    image_file = form.cleaned_data['image']
    session_key = _get_session_key(request)

    try:
        buffer = generate_meme_from_upload(image_file)
        filename      = f"upload_{uuid.uuid4().hex[:12]}.png"
        image_content = ContentFile(buffer.read(), name=filename)

        temp_meme = Meme.objects.create(
            session_key   = session_key,
            original_image = image_content,
            meme_image    = image_content,  
        )
        return JsonResponse({
            'status':   'ok',
            'image_url': temp_meme.original_image.url,
            'meme_id':  temp_meme.pk,
        })
    except Exception as exc:
        logger.exception("Upload error: %s", exc)
        return JsonResponse({'error': "Erreur lors du traitement de l'image."}, status=500)



def meme_detail(request, pk):
    """
    Public detail page for a saved meme (used for social sharing og:image).
    """
    meme = get_object_or_404(Meme, pk=pk)
    context = {
        'meme':      meme,
        'share_url': request.build_absolute_uri(meme.meme_image.url),
    }
    return render(request, 'memes/meme_detail.html', context)



@require_GET
def api_meme_list(request):
    """
    JSON endpoint returning the current session's memes.
    Useful for future SPA/frontend upgrades.
    """
    session_key = _get_session_key(request)
    memes = Meme.objects.filter(session_key=session_key).order_by('-created_at')[:20]
    data = [
        {
            'id':         m.pk,
            'url':        request.build_absolute_uri(m.meme_image.url),
            'top_text':   m.top_text,
            'bottom_text': m.bottom_text,
            'created_at': m.created_at.isoformat(),
        }
        for m in memes
    ]
    return JsonResponse({'memes': data, 'count': len(data)})