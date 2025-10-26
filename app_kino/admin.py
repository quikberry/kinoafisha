from django.contrib import admin
from .models import Movie, Genre, Cinema, Hall, Session, Ticket, User


class SessionInlineForMovie(admin.TabularInline):
    model = Session
    fk_name = "movie"
    extra = 0
    raw_id_fields = ("hall",)
    fields = ("hall", "start_time", "price")
    ordering = ("-start_time",)

class SessionInlineForHall(admin.TabularInline):
    model = Session
    fk_name = "hall"
    extra = 0
    raw_id_fields = ("movie",)
    fields = ("movie", "start_time", "price")
    ordering = ("-start_time",)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    inlines = [SessionInlineForMovie]   # ⟵ добавили
    list_display = ("title", "release_date", "country", "age_rating", "duration", "release_year")
    list_display_links = ("title",)     # ⟵ явно
    list_filter = ("age_rating", "country", "release_date", "genres")
    search_fields = ("title", "description", "country")
    date_hierarchy = "release_date"
    filter_horizontal = ("genres",)
    ordering = ("title",)

    @admin.display(description="Год релиза")
    def release_year(self, obj):
        return obj.release_date.year if obj.release_date else "—"


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    inlines = [SessionInlineForHall]    # ⟵ добавили
    list_display = ("cinema", "name", "seats")
    list_display_links = ("name",)      # ⟵ явно
    list_filter = ("cinema",)
    search_fields = ("name", "cinema__name")
    raw_id_fields = ("cinema",)
    ordering = ("cinema", "name")


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ("seat_number", "is_paid")  # оставим как есть


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    inlines = [TicketInline]
    list_display = ("movie", "hall", "start_time", "price", "ticket_count", "occupancy_pct", "poster_preview")
    list_display_links = ("movie", "hall")        # ⟵ явно
    list_filter = ("hall__cinema", "hall", "movie", "start_time")
    search_fields = ("movie__title", "hall__name", "hall__cinema__name")
    date_hierarchy = "start_time"
    raw_id_fields = ("movie", "hall")
    ordering = ("-start_time",)

    @admin.display(description="Кол-во билетов")
    def ticket_count(self, obj):
        return obj.ticket_set.count()

    @admin.display(description="Заполненность")
    def occupancy_pct(self, obj):
        total = obj.hall.seats or 1
        sold = obj.ticket_set.count()
        return f"{round(100 * sold / total, 1)} %"

    @admin.display(description="Постер")
    def poster_preview(self, obj):
        poster = getattr(obj.movie, "poster", "") or ""
        if poster.startswith("http"):
            from django.utils.html import format_html
            return format_html('<img src="{}" style="height:36px;border-radius:4px;">', poster)
        return "—"


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "phone")
    list_display_links = ("name",)
    search_fields = ("name", "address", "phone")
    list_filter = ("name",)
    ordering = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_at")
    list_display_links = ("username",)
    search_fields = ("username", "email")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("session", "seat_number", "user", "is_paid")
    list_display_links = ("session", "seat_number")  # ⟵ явно
    list_filter = ("is_paid", "session__hall__cinema", "session__movie")
    search_fields = ("user__username", "user__email", "session__movie__title")
    raw_id_fields = ("session", "user")