from django.contrib import admin
from django.utils.html import format_html
from .models import Movie, Genre, Cinema, Hall, Session, Ticket

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ("movie", "start_time", "price")
    show_change_link = True

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "country", "age_rating", "poster_preview")
    search_fields = ("title", "original_title")
    list_filter = ("country", "age_rating", "release_date")
    readonly_fields = ("poster_preview",)
    filter_horizontal = ("genres",)
    date_hierarchy = "release_date"

    def poster_preview(self, obj):
        url = (obj.poster or "").strip() or "/static/img/no-poster.png"
        return format_html('<img src="{}" width="60" style="border-radius:6px" />', url)
    poster_preview.short_description = "Постер"

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)

@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone")
    search_fields = ("name", "address")
    inlines = [SessionInline]

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ("name", "cinema", "seats")
    list_filter = ("cinema",)
    search_fields = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("movie", "cinema", "hall", "start_time", "price")
    list_filter = ("cinema", "hall", "movie", "start_time")
    date_hierarchy = "start_time"
    search_fields = ("movie__title", "hall__name", "cinema__name")
    raw_id_fields = ('movie', 'hall', 'cinema')
    inlines = []




