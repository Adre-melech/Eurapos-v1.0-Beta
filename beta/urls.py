"""
URL configuration for beta project.

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
from django.contrib.sitemaps.views import sitemap
from beta.sitemaps import StaticViewSitemap
from django.views.generic import TemplateView

sitemaps = {"static": StaticViewSitemap}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('dahaka-dark/', admin.site.urls),
    path('dark-panel/', include('adminpanel.urls', namespace='adminpanel')),
    path('', include('home.urls', namespace='home')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('seeker/', include('seeker.urls', namespace='seeker')),
    path('recruiter/', include('recruiter.urls', namespace='recruiter')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('events/', include('events.urls', namespace='events')),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)