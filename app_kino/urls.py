from django.urls import path
from . import views

app_name = 'app_kino'


urlpatterns = [
    path('', views.home, name='home'),               # главная
    path('movies/', views.movie_list, name='movie_list'),   # старый список
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('search/', views.search, name='search'),    # поиск
]