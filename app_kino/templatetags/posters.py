from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from urllib.parse import urlparse

register = template.Library()

def _looks_like_url(s: str) -> bool:
    """Разрешаем только http(s) и относительные /media/... (на будущее)."""
    if not s:
        return False
    s = s.strip()

    if s.startswith("http://") or s.startswith("https://"):
        pr = urlparse(s)
        return bool(pr.netloc and pr.path)
    if s.startswith("/media/") or (hasattr(settings, "MEDIA_URL") and s.startswith(settings.MEDIA_URL or "")):
        return True
    return False

@register.filter
def poster_url(url) -> str:
    """
    Возвращает корректный URL постера.
    Если в БД мусор/пусто — возвращает статическую заглушку.
    """
    s = (str(url).strip()) if url is not None else ""
    if _looks_like_url(s):
        return s
    return staticfiles_storage.url("img/no-poster.png")