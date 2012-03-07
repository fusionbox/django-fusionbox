"""
Helpful decorators for the DRY philosophy.
"""
import json
from django.http import HttpResponse


def json_response(cls=None):
    """
    Decorator that accepts an obj and encodes it
    into json based on specified decoder.

    Usage:

        @json_response
        def myview(request, *args, **kwargs):
            blog = get_object_or_404(Blog.published, pk=request.GET.get("id"))
            return {
                "title": blog.title
                "author: blog.author,
                "content": blog.content,
            }

    """

    def outer(view):
        def inner(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            if not getattr(response, "__iter__", False):
                raise TypeError(response + " is not iterable")
            json_content = json.dumps(response, cls=cls)
            return HttpResponse(json_content, content_type="application/json")
        return inner
    return outer


def jsonp(cls=None, content_type="text/javascript"):
    """
    Decorator that accepts an indexable obj (hint: `(str, dict)`) and returns a
    json-p string. The response can allow for any obj that has an __iter__
    method.

    Note: not all objs that return an iterable obj (ex: strings) from
    `iter()` will work.

    Usage:

        @jsonp
        def myview(request, *args, **kwargs):
            callback = request.GET.get("callback")
            content = {
                "id": request.GET.get("id")
                "name": request.GET.get("name", "spam")
            }
            return callback, content

    """

    def outer(view):
        def inner(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            try:
                callback = response[0]
                content = response[1]
            except IndexError:
                raise TypeError("The user defined view did not return an\
                        indexable obj with at least two values.")
            if not getattr(content, "__iter__", False):
                raise TypeError(response + " is not iterable")
            json_content = json.dumps(content, cls=cls)
            jsonp_response = "{callback}({json});".format(callback=callback,
                    json=json_content)
            return HttpResponse(jsonp_response, content_type=content_type)
        return inner
    return outer
