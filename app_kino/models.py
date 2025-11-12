from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class User(models.Model):
    username = models.CharField("Логин", max_length=100, unique=True)
    email = models.EmailField("E-mail", max_length=150, unique=True)
    password_hash = models.TextField("Хэш пароля")
    created_at = models.DateTimeField("Дата регистрации", default=timezone.now)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Genre(models.Model):
    name = models.CharField("Название жанра", max_length=100, unique=True)

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.name


class Movie(models.Model):
    original_title = models.CharField("Оригинальное название", max_length=200, blank=True)
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    release_date = models.DateField("Дата выхода", null=True, blank=True)
    duration = models.PositiveIntegerField("Длительность")
    country = models.CharField("Страна", max_length=100, blank=True)
    age_rating = models.CharField("Возрастной рейтинг", max_length=10, blank=True)
    poster = models.TextField("Постер (URL)", blank=True)
    genres = models.ManyToManyField(Genre, verbose_name="Жанры", related_name="movies")

    class Meta:
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"

    def __str__(self):
        return self.title


class Cinema(models.Model):
    name = models.CharField("Название", max_length=200)
    address = models.CharField("Адрес", max_length=300, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Кинотеатр"
        verbose_name_plural = "Кинотеатры"

    def __str__(self):
        return self.name


class Hall(models.Model):
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, verbose_name="Кинотеатр",null=True, blank=True)
    name = models.CharField("Название зала", max_length=100)
    seats = models.PositiveIntegerField("Количество мест")

    class Meta:
        verbose_name = "Зал"
        verbose_name_plural = "Залы"

    def __str__(self):
        return f"{self.cinema} — {self.name}"

class Favorite(models.Model):  # NEW
    user = models.ForeignKey("User", on_delete=models.CASCADE, verbose_name="Пользователь")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="Фильм")
    created_at = models.DateTimeField("Добавлено", default=timezone.now)

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ("user", "movie")

    def __str__(self):
        return f"{self.user} → {self.movie}"


class Session(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Фильм"
    )
    hall = models.ForeignKey(
        Hall, on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Зал"
    )
    cinema = models.ForeignKey(
        Cinema,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Кинотеатр",
        null=True, blank=True,
    )
    start_time = models.DateTimeField("Время начала")
    price = models.DecimalField("Цена", max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = "Сеанс"
        verbose_name_plural = "Сеансы"
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.movie} ({self.start_time:%d.%m %H:%M})"

    def clean(self):
        super().clean()
        if self.hall_id and self.cinema_id:
            if self.hall and self.hall.cinema_id != self.cinema_id:
                raise ValidationError({"hall": "Выбранный зал не принадлежит указанному кинотеатру."})

    def save(self, *args, **kwargs):
        if self.hall_id and not self.cinema_id:
            self.cinema_id = self.hall.cinema_id
        super().save(*args, **kwargs)


class Ticket(models.Model):
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Сеанс"
    )
    seat_number = models.PositiveIntegerField("Место")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Покупатель")
    is_paid = models.BooleanField("Оплачен", default=False)

    class Meta:
        verbose_name = "Билет"
        verbose_name_plural = "Билеты"
        unique_together = ("session", "seat_number")

    def __str__(self):
        return f"Билет {self.session} — место {self.seat_number}"
