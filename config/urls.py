"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""



from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.generic import RedirectView
from admin_dashboard.views import admin_redirect_notice

urlpatterns = [
    # Redirect Django admin subscription URLs to custom admin dashboard notice
    path('admin/payments/subscriptionplan/', admin_redirect_notice, name='admin_subscription_redirect'),
    path('admin/payments/subscriptionplan/add/', RedirectView.as_view(url='/admin-dashboard/subscriptions/plans/', permanent=False)),
    path('admin/payments/subscriptionplan/<int:pk>/change/', RedirectView.as_view(url='/admin-dashboard/subscriptions/plans/', permanent=False)),
    path('admin/payments/usersubscription/', RedirectView.as_view(url='/admin-dashboard/subscriptions/users/', permanent=False)),
    path('admin/payments/usersubscription/add/', RedirectView.as_view(url='/admin-dashboard/subscriptions/users/', permanent=False)),
    path('admin/payments/usersubscription/<int:pk>/change/', RedirectView.as_view(url='/admin-dashboard/subscriptions/users/', permanent=False)),
    path('admin/payments/subscriptionpayment/', RedirectView.as_view(url='/admin-dashboard/subscriptions/payments/', permanent=False)),
    path('admin/payments/subscriptionpayment/add/', RedirectView.as_view(url='/admin-dashboard/subscriptions/payments/', permanent=False)),
    path('admin/payments/subscriptionpayment/<int:pk>/change/', RedirectView.as_view(url='/admin-dashboard/subscriptions/payments/', permanent=False)),
    
    # Main admin URL (keep this after the specific redirects)
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    path('', views.home, name='home'),
    path('users/', include('users.urls', namespace='users')),
    path('portfolio/', include('portfolio.urls')),
    path('bookings/', include('bookings.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('community/', include('community.urls')),
    path('help/', include('helpcenter.urls')),
    path('accounts/login/', RedirectView.as_view(url='/users/login/', permanent=True)),
    path('feed/', RedirectView.as_view(url='/portfolio/feed/', permanent=False)),
    path('explore/', __import__('portfolio.views').views.explore, name='explore'),
    path('stories/upload/', RedirectView.as_view(url='/portfolio/stories/upload/', permanent=False)),
    # API endpoints for AJAX like/dislike
    path('api/portfolio/', include('portfolio.api_urls')),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('contact/', views.contact_us, name='contact_us'),
    path('blog/', include('blog.urls')),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
