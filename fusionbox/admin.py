from django.contrib import admin
from django.contrib.admin.util import unquote
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import update_wrapper

from django.conf.urls.defaults import patterns, url

class OrderableAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(OrderableAdmin, self).get_urls()
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        app_label = self.model._meta.app_label
        model_name = self.model._meta.module_name
        my_urls = patterns('',
                #url(r'^(.+)/swap/(?P<object_id>.+)/(?P<other_id>.+)/$', 
                url(r'^(.+)/swap/(.+)/$', 
                    wrap(self.swap), 
                    name='{app_label}_{model_name}_reorder'.format(
                        app_label = self.model._meta.app_label,
                        model_name = self.model._meta.module_name)
                ),
            )
        return my_urls + urls

    def swap(self, request, object_id, other_id):
        obj = get_object_or_404(self.model, pk=unquote(object_id))
        obj.swap(other_id)
        return HttpResponseRedirect('../../../')

    def move_links(self, obj):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.module_name
        reorder_url_name = 'admin:{app_label}_{model_name}_reorder'.format(
            app_label = self.model._meta.app_label,
            model_name = self.model._meta.module_name)
        return u'<a href="{move_up}">\u25b2</a><a href="{move_down}">\u25bc</a>'.format(
                move_up = reverse('admin:portfolio_video_reorder', args=[obj.pk, obj.order-1]),
                move_down = reverse('admin:portfolio_video_reorder', args=[obj.pk, obj.order+1]),
            )
    move_links.allow_tags = True
    move_links.short_description = 'Order'
