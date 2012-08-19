from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.shortcuts import render

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', lambda r: render(r, 'home.html', {'request': r}), name='home'),
    url(r'^', include('stripeboard.board.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
