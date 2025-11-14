from django.contrib import admin
from django.urls import path, include
from app_kino import views as kino_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_kino.urls', namespace='app_kino')),

    path("accounts/login/",  auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/signup/", kino_views.signup, name="signup"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="app_kino:home"), name="logout",),
]