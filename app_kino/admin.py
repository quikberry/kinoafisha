from django.contrib import admin
from .models import Movie, Genre, Cinema, Hall, Session, Ticket, User

admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Cinema)
admin.site.register(Hall)
admin.site.register(Session)
admin.site.register(Ticket)
admin.site.register(User)