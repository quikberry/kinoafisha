from datetime import timedelta
from django.conf import settings
from django.db.models import Count, Avg, Min, Q
from django.shortcuts import render, get_object_or_404, redirect
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

    # --- ДЕТЕКТ И ОБХОД ДЛЯ SQLITE ---
    is_sqlite = settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")

    # ===== ФИЛЬМЫ =====
    if is_sqlite:
        # 1) подбираем id в Python (Unicode-friendly)
        movies_raw = Movie.objects.values("id", "title", "original_title")
        movie_ids = []
        for m in movies_raw:
            # для каждого слова требуем совпадение в title ИЛИ original_title
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
        # PostgreSQL / др. БД — можно обычный icontains
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

    # ===== КИНОТЕАТРЫ =====
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

    # --- ПАГИНАЦИЯ ---
    from django.core.paginator import Paginator
    paginator = Paginator(movies_qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "app_kino/search.html", {
        "q": q,
        "page_obj": page_obj,
        "cinemas": cinemas_qs[:10],
        "total_movies": movies_qs.count(),
        "total_cinemas": cinemas_qs.count(),
    })