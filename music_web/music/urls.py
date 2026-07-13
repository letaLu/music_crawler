from django.urls import path
from . import views

urlpatterns = [
    path('', views.song_list, name='home'),
    path('songs/', views.song_list, name='song_list'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('artists/', views.artist_list, name='artist_list'),
    path('artist/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path('search/', views.search_results, name='search_results'),
]