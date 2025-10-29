from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile, name='profile_by_id'),
    path('logout/', views.user_logout, name='logout'),

    # Email activation
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset_form.html',
        email_template_name='users/password_reset_email.html',
        success_url=reverse_lazy('users:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    # Photographer search
    path('search/', views.photographer_search, name='photographer_search'),
    # Messaging/Chat
    path('inbox/', views.inbox, name='inbox'),
    path('send_message/', views.send_message, name='send_message'),
]
