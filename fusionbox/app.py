from django.core.urlresolvers import reverse
from django.shortcuts import redirect

class FusionboxApp(object):
    """
    Base Class for implementing Fusionbox Apps

    """
    app_name = None
    namespace = None

    def __init__(self, name=None):
        self.app_name = name or self.app_name

    def get_context_data(self, request, **kwargs):
        context = {
            'current_app': self.app_name,
        }
        context.update(kwargs)
        return context

    def get_urls(self, prefix=None):
        raise NotImplementedError()

    def redirect(self, to, *args, **kwargs):
        """
        Uses namespaced reverse
        """
        uri = self.reverse(to, args=args, kwargs=kwargs)
        return redirect(uri)

    def reverse(self, to, args=None, kwargs=None):
        """
        Wrapper for django.core.urlresolvers.reverse

        Calls reverse() based on namespace settings for current app
        """
        to = '%s:%s' % (self.namespace, to)
        return reverse(to, args=args, kwargs=kwargs, current_app=self.app_name)

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace
