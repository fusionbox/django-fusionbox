from django.conf.urls import patterns, url, include

_PREFIX = '__debug__'

urlpatterns = patterns('fusionbox.panels.user_panel.views',
    url(r'^%s/users/$' % _PREFIX, 'content',
        name='debug-userpanel'),
    url(r'^%s/users/login/$' % _PREFIX, 'login',
        name='debug-userpanel-login'),
    url(r'^%s/users/login/(?P<pk>-?\d+)$' % _PREFIX, 'login',
        name='debug-userpanel-login'),
)
