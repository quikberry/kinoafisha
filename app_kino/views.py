from datetime import timedelta
from django.conf import settings
from django.db.models import Count, Avg, Min, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse
from .models import Movie, Session, Cinema
from .forms import MovieForm

def home(request):
    now = timezone.now()
    today = now.date()
    month_plus = now - timedelta(days=30)

    upcoming_releases = (
        Movie.objects
        .filter(release_date__gte=today)
        .order_by('release_date', 'title')[:3]
    )

    popular_movies = (
        Movie.objects
        .annotate(
            sessions_30d=Count(
                'sessions',
                filter=Q(sessions__start_time__range=(month_plus, now)),
                distinct=True
            ),
            avg_price_30d=Avg(
                'sessions__price',
                filter=Q(sessions__start_time__range=(month_plus, now))
            )
        )
        .filter(sessions_30d__gt=0)
        .order_by('-sessions_30d', 'title')[:3]
    )

    todays_sessions = (
        Session.objects
        .select_related('movie', 'hall', 'hall__cinema')
        .filter(start_time__date=today)
        .exclude(start_time__lt=now)
        .order_by('start_time')[:3]
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
        .order_by("release_date")[:4]
    )

    return render(request, "app_kino/movie/detail.html", {
        "movie": movie,
        "sessions": sessions,
        "by_cinema": list(by_cinema),
        "similar": similar,
    })

def _words(q: str) -> list[str]:
    return [w for w in q.strip().split() if w]

def _casefold_contains(haystack: str, needle: str) -> bool:
    if haystack is None:
        return False
    return needle.casefold() in haystack.casefold()

def search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return redirect("app_kino:movie_list")

    terms = _words(q)
    now = timezone.now()
#обход кириллицы
    is_sqlite = settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")

    if is_sqlite:
        movies_raw = Movie.objects.values("id", "title", "original_title")
        movie_ids = []
        for m in movies_raw:
            ok = all(
                _casefold_contains(m.get("title") or "", w) or
                _casefold_contains(m.get("original_title") or "", w)
                for w in terms
            )
            if ok:
                movie_ids.append(m["id"])

        movies_qs = (
            Movie.objects
            .filter(pk__in=movie_ids)
            .annotate(
                upcoming_sessions=Count(
                    "sessions",
                    filter=Q(sessions__start_time__gte=now),
                    distinct=True
                )
            )
            .order_by("-upcoming_sessions", "title")
        )
    else:
        movie_filter = Q()
        for w in terms:
            movie_filter &= (Q(title__icontains=w) | Q(original_title__icontains=w))
        movies_qs = (
            Movie.objects
            .filter(movie_filter)
            .annotate(
                upcoming_sessions=Count(
                    "sessions",
                    filter=Q(sessions__start_time__gte=now),
                    distinct=True
                )
            )
            .order_by("-upcoming_sessions", "title")
        )

    if is_sqlite:
        cinemas_raw = Cinema.objects.values("id", "name", "address")
        cinema_ids = []
        for c in cinemas_raw:
            ok = all(
                _casefold_contains(c.get("name") or "", w) or
                _casefold_contains(c.get("address") or "", w)
                for w in terms
            )
            if ok:
                cinema_ids.append(c["id"])
        cinemas_qs = Cinema.objects.filter(pk__in=cinema_ids).order_by("name")
    else:
        cinema_filter = Q()
        for w in terms:
            cinema_filter &= (Q(name__icontains=w) | Q(address__icontains=w))
        cinemas_qs = Cinema.objects.filter(cinema_filter).order_by("name")

    from django.core.paginator import Paginator
    paginator = Paginator(movies_qs, 4)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "app_kino/search.html", {
        "q": q,
        "page_obj": page_obj,
        "cinemas": cinemas_qs[:4],
        "total_movies": movies_qs.count(),
        "total_cinemas": cinemas_qs.count(),
    })

def movie_create(request):
    if request.method == "POST":
        form = MovieForm(request.POST)
        if form.is_valid():
            movie = form.save()
            return redirect("app_kino:movie_detail", pk=movie.pk)
    else:
        form = MovieForm()
    return render(request, "app_kino/movie/form.html", {"form": form, "is_create": True})

def movie_update(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == "POST":
        form = MovieForm(request.POST, instance=movie)
        if form.is_valid():
            form.save()
            return redirect("app_kino:movie_detail", pk=movie.pk)
    else:
        form = MovieForm(instance=movie)
    return render(request, "app_kino/movie/form.html", {"form": form, "mode": "edit", "movie": movie, "is_create": False})

def movie_delete(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == "POST":
        movie.delete()
        return redirect("app_kino:movie_list")
    return render(request, "app_kino/movie/confirm_delete.html", {"movie": movie})



