from django.db import models
from django.utils.functional import lazy
from django.core.urlresolvers import reverse


def lookup_needs_distinct(opts, lookup_path):
    """
    Returns True if 'distinct()' should be used to query the given lookup path.
    """
    field_name = lookup_path.split('__', 1)[0]
    field = opts.get_field_by_name(field_name)[0]
    if ((hasattr(field, 'rel') and
         isinstance(field.rel, models.ManyToManyRel)) or
        (isinstance(field, models.related.RelatedObject) and
         not field.field.unique)):
         return True
    return False


reverse_lazy = lambda name=None, *args : lazy(reverse, str)(name, args=args)
