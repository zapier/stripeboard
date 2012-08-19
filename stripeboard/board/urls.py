from django.conf.urls import patterns, include, url

from stripeboard.board import views


urlpatterns = patterns('',
    # should reuse django generics...
    url(r'^login/$', views.do_login, name='login'),
    url(r'^logout/$', views.do_logout, name='logout'),

    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^dashboard/data\.json$', views.json_data, name='json_data'),

    url(r'^dashboard/oauth/start/$', views.oauth_start, name='oauth_start'),
    url(r'^dashboard/oauth/return/$', views.oauth_return, name='oauth_return'), # if they need an account, show them
    url(r'^dashboard/oauth/retrieve/$', views.retrieve_oauth, name='retrieve_oauth'),
)
