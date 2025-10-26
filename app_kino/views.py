from datetime import timedelta
from django.db.models import Count, Avg, Min
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Movie, Session, Cinema

def home(request):
    now = timezone.now()
    today = now.date()
    week_later = now + timedelta(days=7)

    upcoming_releases = (
        Movie.objects
        .filter(release_date__gte=today)
        .order_by('release_date', 'title')[:10]
    )

    popular_movies = (
        Movie.objects
        .filter(sessions__start_time__range=(now, week_later))
        .annotate(
            sold=Count('sessions__tickets', distinct=True),
            avg_price=Avg('sessions__price'),
        )
        .order_by('-sold', 'title')[:10]
    )

    todays_sessions = (
        Session.objects
        .select_related('movie', 'hall', 'hall__cinema')
        .filter(start_time__date=today)
        .exclude(start_time__lt=now)
        .order_by('start_time')[:10]
    )

    return render(request, 'app_kino/home.html', {
        'upcoming_releases': upcoming_releases,
        'popular_movies': popular_movies,
        'todays_sessions': todays_sessions,
    })

def movie_list(request):
    movies = Movie.objects.all().order_by('title')
    return render(request, 'app_kino/movie/list.html', {'movies': movies})

def movie_detail(request, pk: int):
    movie = get_object_or_404(
        Movie.objects.prefetch_related("genres"),
        pk=pk
    )

    now = timezone.now()
    week_later = now + timezone.timedelta(days=7)

    sessions = (
        Session.objects
        .select_related("hall", "cinema")
        .filter(movie=movie, start_time__range=(now, week_later))
        .order_by("cinema__name", "start_time")
    )

    by_cinema = (
        sessions.values("cinema__id", "cinema__name")
        .annotate(total=Count("id"), min_price=Min("price"))
        .order_by("cinema__name")
    )

    similar = (
        Movie.objects
        .filter(genres__in=movie.genres.all())
        .exclude(pk=movie.pk)
        .distinct()
        .order_by("release_date")[:8]
    )

    return render(request, "app_kino/movie/detail.html", {
        "movie": movie,
        "sessions": sessions,
        "by_cinema": list(by_cinema),
        "similar": similar,
    })

def search(request):
    q = request.GET.get('q', '').strip()
    movies = cinemas = []
    if q:
        movies = (Movie.objects
                  .filter(title__icontains=q)
                  .union(Movie.objects.filter(original_title__icontains=q))
                  .distinct()
                  .order_by('title'))
        cinemas = (Cinema.objects
                   .filter(name__icontains=q)
                   .order_by('name'))
    return render(request, 'app_kino/search.html', {'q': q, 'movies': movies, 'cinemas': cinemas})