from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path(
        'password-reset/',
        views.UserPasswordResetView.as_view(),
        name='password-reset',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.UserPasswordResetConfirmView.as_view(),
        name='password-reset-confirm',
    ),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]
