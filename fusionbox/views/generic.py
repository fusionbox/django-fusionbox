"""
Generic Views
"""
import json
from django.core.exceptions import PermissionDenied, ValidationError, Http404
from django.views.generic import ListView, View
from fusionbox.http import JSONResponse


class RESTMixin(object):

    def respond(self, context, status=200, encoder=None, **kwargs):
        return JSONResponse(context, encoder=encoder, status=status, **kwargs)

    @property
    def payload(self):
        try:
            return json.loads(self.request.raw_post_data)
        except ValueError:
            return {}


class RESTView(View, RESTMixin):
    """
    A `starter view` for a REST API

    Example usage:

        class BlogAPI(RESTView):

            def get(self, request, *args, **kwargs):
                blog = get_object_or_404(Blog, pk=kwargs.get("pk"))
                return self.respond(blog.to_dict(), encoder=MyJSONEncoder)

    """

    def dispatch(self, *args, **kwargs):
        try:
            return super(RESTView, self).dispatch(*args, **kwargs)
        except ValidationError as e:
            return self.respond(e.message, status=400)
        except Http404:
            return self.respond(None, status=404)
        except PermissionDenied:
            return self.respond(None, status=403)


class FilteredListView(ListView):
    """
    Example usage:

        `views.py`
            class BlogListView(FilteredListView):
                sorts = {
                        "date": lambda x: x.order_by("-publish_at"),
                        "alpha" : lambda x: x.order_by("title"),
                        "popular": lambda x: x.annotate(
                            comment_count=models.Count("comments"))\
                                    .order_by("-comment_count")
                        }
                filters = {
                        "category": (Category, "category__slug")
                        }
                template_name ='blog/index.html'
                context_object_name = 'entry_list'
                model = Entry

    """
    sorts = {}
    filters = {}

    def get_context_data(self, **kwargs):
        context = super(FilteredListView, self)\
                .get_context_data(**kwargs)
        for key, val in self.filters.iteritems():
            plural_name = val[0]._meta.verbose_name_plural
            context[plural_name] = val[0].objects.all()
            context[key] = self.request.GET.get(key, "all")
        return context

    def get_queryset(self):
        paginated_items = self.model.objects.all()
        sorting_type = self.request.GET.get("sort", self.sorts.keys()[0])
        for key, val in self.filters.iteritems():
            _filter_val = self.request.GET.get(key, "all")
            if _filter_val != "all":
                paginated_items = paginated_items\
                        .filter(**{val[1]: _filter_val})
        return self.sorts[sorting_type](paginated_items)
