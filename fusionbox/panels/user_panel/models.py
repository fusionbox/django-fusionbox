import urls
from django.conf.urls import patterns, include
from fusionbox.panels.user_panel.urls import urlpatterns
from django.conf.urls import patterns, url, include
urls.urlpatterns += patterns('',
    ('', include(urlpatterns)),
)
