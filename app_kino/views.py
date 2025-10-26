from django.shortcuts import render, get_object_or_404
from .models import Movie, Session

def movie_list(request):
    """Список фильмов (аналог списка постов в книге, гл.1)."""
    movies = Movie.objects.all().order_by('title')
    return render(request, 'app_kino/movie/list.html', {'movies': movies})

def movie_detail(request, pk: int):
    """Детальная страница фильма (аналог detail)."""
    movie = get_object_or_404(Movie, pk=pk)
    # ближайшие сеансы для карточки фильма
    sessions = Session.objects.filter(movie=movie).order_by('start_time')[:10]
    ctx = {'movie': movie, 'sessions': sessions}
    return render(request, 'app_kino/movie/detail.html', ctx)