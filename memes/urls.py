from django.urls import path
from . import views

app_name = 'memes'

urlpatterns = [

    path('',                     views.index,        name='index'),
    path('gallery/',             views.gallery,      name='gallery'),
    path('meme/<int:pk>/',       views.meme_detail,  name='detail'),

    path('save/',                views.save_meme,    name='save'),
    path('delete/<int:pk>/',     views.delete_meme,  name='delete'),
    path('download/<int:pk>/',   views.download_meme, name='download'),

    path('upload/',              views.upload_image, name='upload'),

    path('api/memes/',           views.api_meme_list, name='api_memes'),
]
