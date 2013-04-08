import StringIO
import copy
import csv
import urllib

from django import forms
from django.core.exceptions import ValidationError
from django.forms.util import ErrorList, ErrorDict
from django.utils.functional import cached_property
from django.db import models
from django.db.models import Q
from django.utils.datastructures import SortedDict

from fusionbox.forms.fields import UncaptchaField


class IterDict(SortedDict):
    """
    Extension of djangos built in sorted dictionary class which iterates
    through the values rather than keys.
    """
    def __iter__(self):
        for key in super(IterDict, self).__iter__():
            yield self[key]


class CSSClassMixin(object):
    error_css_class = 'error'
    required_css_class = 'required'


class NonBraindamagedErrorMixin(object):
    """
    Form mixin for easier field based error messages.
    """
    def field_error(self, name, error):
        self._errors = self._errors or ErrorDict()
        self._errors.setdefault(name, ErrorList())
        self._errors[name].append(error)


class FieldsetMixin(NonBraindamagedErrorMixin):
    """
    Form mixin for grouping sets of fields together for both errors and
    rendering.  Declaration of fieldsets follows that of ModelAdmin.

    FIELDSETS class variable should be a list of fieldsets like for ModelAdmin.
    For example::
    >>> class MyForm(FieldsetMixin):
    ...     FIELDSETS = [
    ...        ('fieldset1', {
    ...            'fields': ['field11', 'field12'],
    ...        }),
    ...        ('fieldset2', {
    ...            'fields': ['field21', 'field22'],
    ...        }),
    ...     ]
    """
    FIELDSETS = tuple()

    def get_fieldsets(self):
        return self.FIELDSETS

    def fieldset_error(self, name, error):
        fieldset = self.fieldsets[name]
        fieldset.errors = getattr(fieldset, 'errors', ErrorList())
        fieldset.errors.append(error)
        self.field_error(name, error)

    @cached_property
    def fieldsets(self):
        fieldsets = IterDict()
        for fieldset_name, fieldset in self.get_fieldsets():
            fieldsets[fieldset_name] = IterDict({
                'name': fieldset_name,
                'fields': IterDict([(field, self[field]) for field in fieldset.get('fields', [])]),
                'css_classes': ' '.join(fieldset.get('css_classes', [])),
                'template_name': fieldset.get('template_name'),
            }.items())
        return fieldsets


class BaseForm(FieldsetMixin, CSSClassMixin, forms.Form):
    """
    A 'Better' base Form class.
    """
    pass


class BaseModelForm(FieldsetMixin, CSSClassMixin, forms.ModelForm):
    """
    A 'Better' base ModelForm class.
    """
    pass


class BaseChangeListForm(BaseForm):
    """
    Base class for all ``ChangeListForms``.
    """
    def __init__(self, *args, **kwargs):
        """
        Takes an option named argument ``queryset`` as the base queryset used in
        the ``get_queryset`` method.
        """
        try:
            self.base_queryset = kwargs.pop('queryset', None)
            if self.base_queryset is None:
                self.base_queryset = self.model.objects.all()
        except AttributeError:
            raise AttributeError('`ChangeListForm`s must be instantiated with a\
                                 queryset, or have a `model` attribute set on\
                                 them')
        super(BaseChangeListForm, self).__init__(*args, **kwargs)

    def get_queryset(self):
        """
        If the form was initialized with a queryset, this method returns that
        queryset.  Otherwise it returns ``Model.objects.all()`` for whatever
        model was defined for the form.
        """
        return self.base_queryset

    def full_clean(self, *args, **kwargs):
        super(BaseChangeListForm, self).full_clean()
        if self.is_valid():
            self.queryset = self.get_queryset()




class SearchForm(BaseChangeListForm):
    """
    Base form class for implementing searching on a model.

    # Example Usage
    ::

        class UserSearchForm(SearchForm):
            SEARCH_FIELDS = ('username', 'email', 'profile__role')
            model = User

    ::

        >>> form = UserSearchForm(request.GET, queryset=User.objects.filter(is_active=True))
        >>> form.is_valid()  # Sets form.queryset if form is valid.
        True
        >>> form.queryset
        [<User: admin>, <User: test@test.com>, <User: test2@test.com>]

    ``SEARCH_FIELDS`` should be an iterable of valid django queryset field lookups.
    Lookups can span foreign key relationships.

    By default, searches will be case insensitive.  Set ``CASE_SENSITIVE`` to
    ``True`` to make searches case sensitive.
    """
    SEARCH_FIELDS = tuple()
    CASE_SENSITIVE = False
    q = forms.CharField(label="Search", required=False)

    def get_queryset(self):
        """
        Constructs an '__contains' or '__icontains' filter across all of the
        fields listed in ``SEARCH_FIELDS``.
        """
        qs = super(SearchForm, self).get_queryset()

        # Do Searching
        q = self.cleaned_data.get('q', None).strip()
        if q:
            args = []
            for field in self.SEARCH_FIELDS:
                if self.CASE_SENSITIVE:
                    kwarg = {field + '__contains': q}
                else:
                    kwarg = {field + '__icontains': q}
                args.append(Q(**kwarg))
            if len(args) > 1:
                qs = qs.filter(reduce(lambda x, y: x | y, args))
            elif len(args) == 1:
                qs = qs.filter(args[0])

        return qs


class ThingSet(object):
    ThingClass = None

    def __init__(self, form, headers):
        if self.ThingClass is None:
            raise AttributeError('ThingSet must have a ThingClass attribute')
        self.form = form
        self.headers = SortedDict()
        for header in headers:
            self.headers[header.name] = header

    def __iter__(self):
        for header in self.headers.values():
            yield self.ThingClass(self.form, header)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.ThingClass(self.form, self.headers.values()[key])
        else:
            return self.ThingClass(self.form, self.headers[key])


class Header(object):
    def __init__(self, name, label=None, column_name=False, is_sortable=True):
        self.name = name
        self.label = label or pretty_name(name)
        self.column_name = column_name or name
        self.is_sortable = is_sortable


def construct_querystring(data, **kwargs):
    params = copy.copy(data)
    params.update(kwargs)
    return urllib.urlencode(params)


class BoundHeader(object):
    """
    Template object for outputting headers for SortForms
    """
    def __init__(self, form, header):
        self.name = header.name
        self.label = header.label
        self.column_name = header.column_name
        self.is_sortable = header.is_sortable
        self.form = form
        self.sorts = getattr(form, 'cleaned_data', {}).get('sorts', [])
        self.header = header
        self.param = "{0}-sorts".format(form.prefix or '').strip('-')

    @property
    def index(self):
        return self.form.HEADERS.index(self.header)

    @property
    def sort_index(self):
        return self.index + 1

    @property
    def is_ascending(self):
        return self.is_active and self.sort_index in self.sorts

    @property
    def is_descending(self):
        return self.is_active and self.sort_index not in self.sorts

    @property
    def css_classes(self):
        classes = []
        if self.is_active:
            classes.append('active')
            if self.sort_index in self.sorts:
                classes.append('ascending')
            else:
                classes.append('descending')
        return ' '.join(classes)

    def get_sorts_with_header(self):
        if not self.sorts:
            return [self.sort_index]
        elif abs(self.sorts[0]) == self.sort_index:
            return [-1 * self.sorts[0]] + self.sorts[1:]
        else:
            return [self.sort_index] + filter(lambda x: x != self.sort_index, self.sorts)

    @property
    def priority(self):
        if self.is_active:
            return map(abs, self.sorts).index(self.sort_index) + 1

    @property
    def is_active(self):
        return self.sort_index in map(abs, self.sorts)

    @property
    def querystring(self):
        return construct_querystring(self.form.data, **{self.param: '.'.join(map(str, self.get_sorts_with_header()))})

    @property
    def singular_queryset(self):
        return construct_querystring(self.form.data, **{self.param: str(self.sort_index)})

    @property
    def remove_queryset(self):
        return construct_querystring(self.form.data, **{self.param: '.'.join(map(str, self.get_sorts_with_header()[1:]))})


class HeaderSet(ThingSet):
    ThingClass = BoundHeader


class SortForm(BaseChangeListForm):
    """
    Base class for implementing sorting on a model.

    # Example Usage
    ::

        class UserSortForm(SortForm):
            HEADERS = (
                SortForm.Header('username'),
                SortForm.Header('email'),
                SortForm.Header('is_active'),
            )
            model = User

    The sort field for this form defaults to a HiddenInput widget which should
    be output within your form to preserve sorting accross any form
    submissions.
    """
    Header = Header  # Easy access when defining SortForms
    error_messages = {
        'unknown_header': 'Invalid sort parameter',
        'unsortable_header': 'Invalid sort parameter',
    }
    HEADERS = tuple()
    sorts = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SortForm, self).__init__(*args, **kwargs)
        if not len(set(h.name for h in self.HEADERS)) == len(self.HEADERS):
            raise AttributeError('Duplicate `name` in HEADERS')
        self.headers = HeaderSet(self, self.HEADERS)

    def clean_sorts(self):
        cleaned_data = self.cleaned_data
        sorts = filter(bool, cleaned_data.get('sorts', '').split('.'))
        if not sorts:
            return []
        # Ensure that the sort parameter does not contain non-numeric sort indexes
        if not all([sort.strip('-').isdigit() for sort in sorts]):
            raise ValidationError(self.error_messages['unknown_header'])
        sorts = [int(sort) for sort in sorts]
        # Ensure that all of our sort parameters are in range of our header values
        if any([abs(sort) > len(self.HEADERS) for sort in sorts]):
            raise ValidationError(self.error_messages['unknown_header'])
        # Ensure not un-sortable fields are being sorted by
        if not all(self.HEADERS[abs(i) - 1].is_sortable for i in sorts):
            raise ValidationError(self.error_messages['unsortable_header'])

        return sorts

    def get_queryset(self):
        """
        Returns an ordered queryset, sorted based on the values submitted in
        the sort parameter.
        """
        qs = super(SortForm, self).get_queryset()

        # Do Sorting
        sorts = self.cleaned_data.get('sorts', [])
        order_by = []
        for sort in sorts:
            param = self.headers[abs(sort) - 1].column_name
            if sort < 0:
                param = '-' + param
            order_by.append(param)

        if order_by:
            qs = qs.order_by(*order_by)

        return qs


# How do we depricate this?
class FilterForm(BaseChangeListForm):
    """
    Base class for implementing filtering on a model.

    # Example Usage

    ::

        class UserFilterForm(FilterForm):
            FILTERS = {
                'active': 'is_active',
                'date_joined': 'date_joined__gte',
                'published': None, # Custom filtering
                }
            model = User

            PUBLISHED_CHOICES = (
                    ('', 'All'),
                    ('before', 'Before Today'),
                    ('after', 'After Today'),
                    )

            active = forms.BooleanField(required=False)
            date_joined = forms.DateTimeField(required=False)
            published = forms.ChoiceField(choices=PUBLISHED_CHOICES, widget=forms.HiddenInput())

            def pre_filter(self, queryset):
                published = self.cleaned_data.get('published')
                if published == '':
                    return queryset
                elif published == 'before':
                    return queryset.filter(published_at__lte=datetime.datetime.now())
                elif published == 'after':
                    return queryset.filter(published_at__gte=datetime.datetime.now())

    ``FILTERS`` defines a mapping of form fields to queryset filters.

    When displaying in the template, this form also provides you with url querystrings for all of your filters.

    ``form.filters`` is a dictionary of all of the filters defined on your form.

    In the example above, you could do the following in the template for display links for the published filter

    ::

        {% for choice in form.filters.published %}
            {% if choice.active %}
                {{ choice.display }} (<a href='?{{ choice.remove }}'>remove</a>)
            {% else %}
                <a href='?{{ choice.querystring }}'>{{ choice.display }}</a>
            {% endif %}
        {% endfor %}
    """
    FILTERS = {}

    @property
    def filters(self):
        """
        Generates a dictionary of filters with proper queryset links to
        maintian multiple filters.
        """
        filters = IterDict()
        for key in self.FILTERS:
            filter = IterDict()
            filter_param = ((self.prefix or '') + '-' + key).strip('-')

            for value, display in self.fields[key].choices:
                choice = {}
                choice['value'] = value
                choice['display'] = display

                # These are raw values so they must come from data, and be
                # coerced to strings
                choice['active'] = str(value) == self.data.get(filter_param, '')

                params = copy.copy(self.data)
                # Filter by this current choice
                params[filter_param] = value
                choice['querystring'] = urllib.urlencode(params)
                # remove this filter
                params[filter_param] = ''
                choice['remove'] = urllib.urlencode(params)

                filter[value] = choice
            filters[key] = filter
        return filters

    def pre_filter(self, qs):
        """
        Hook for doing pre-filter modification to the queryset

        Runs prior to any form filtering and is run regardless form validation.
        """
        return qs

    def post_filter(self, qs):
        """
        Hook for doing post-filter modification to the queryset.  This is also
        the place where any custom filtering should take place.

        Runs only if the form validates.
        """
        return qs

    def get_queryset(self):
        """
        Performs the following steps:
            - Returns the queryset if the form is invalid.
            - Otherwise, filters the queryset based on the filters defined on the
              form.
            - Returns the filtered queryset.
        """
        qs = super(FilterForm, self).get_queryset()

        qs = self.pre_filter(qs)

        #  Ensure that the form is valid
        if not self.is_valid():
            return qs

        # Do filtering
        for field, column_name in self.FILTERS.items():
            if column_name and self.cleaned_data.get(field, ''):
                qs = qs.filter(**{column_name: self.cleaned_data[field]})

        qs = self.post_filter(qs)

        return qs


def csv_getattr(obj, attr_name):
    """
    Helper function for CsvForm class that gets an attribute from a model with
    a custom exception.
    """
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        raise AttributeError('CsvForm: No \'{0}\' attribute found on \'{1}\' object'.format(
            attr_name,
            obj._meta.object_name,
            ))


def csv_getvalue(obj, path):
    """
    Helper function for CsvForm class that retrieves a value from an object
    described by a django-style query path.  The value can be a model field,
    property method, foreign key field, or instance method on the model.

    Example:
    ::
        >>> # full_name is a property method
        >>> csv_getvalue(instance, 'project__employee__full_name')
        u'David Sanders'
    """
    path = path.split('__', 1)
    attr_name = path[0]

    if obj is None:
        # Record object is empty, return None
        return None
    if len(path) == 1:
        # Return the last leaf of the path after evaluation
        attr = csv_getattr(obj, attr_name)

        if isinstance(attr, models.Model):
            # Attribute is a model instance.  Return unicode.
            return unicode(attr)
        elif hasattr(attr, '__call__'):
            # Attribute is a callable method.  Return its value when called.
            return attr()
        else:
            # Otherwise, assume attr is a simple value
            return attr
    elif len(path) == 2:
        # More of path is remaining to be traversed
        attr = csv_getattr(obj, attr_name)

        if attr is None:
            return None
        elif isinstance(attr, models.Model):
            # If attribute is a model instance, traverse into it
            return csv_getvalue(attr, path[1])
        else:
            raise AttributeError('CsvForm: Attribute \'{0}\' on object \'{1}\' is not a related model'.format(
                attr_name,
                obj._meta.object_name,
                ))


class CsvForm(BaseChangeListForm):
    """
    Base class for implementing csv generation on a model.

    Example:

    # Given this class...
    ::

        class UserFilterForm(FilterForm):
            model = User

            CSV_COLUMNS = (
                    {'column': 'id', 'title': 'Id'},
                    {'column': 'username', 'title': 'Username'},
                    {'column': 'email__domain_name', 'title': 'Email Domain'},
                    )

            FILTERS = {
                'active': 'is_active',
                'date_joined': 'date_joined__gte',
                'published': None, # Custom filtering
                }

            PUBLISHED_CHOICES = (
                    ('', 'All'),
                    ('before', 'Before Today'),
                    ('after', 'After Today'),
                    )

            active = forms.BooleanField(required=False)
            date_joined = forms.DateTimeField(required=False)
            published = forms.ChoiceField(choices=PUBLISHED_CHOICES, widget=forms.HiddenInput())

            def pre_filter(self, queryset):
                published = self.cleaned_data.get('published')
                if published == '':
                    return queryset
                elif published == 'before':
                    return queryset.filter(published_at__lte=datetime.datetime.now())
                elif published == 'after':
                    return queryset.filter(published_at__gte=datetime.datetime.now())

    ::

        >>> # This code in a repl will produce a string buffer with csv output for
        >>> # the form's queryset
        >>> form = UserFilterForm(request.GET, queryset=User.objects.all())
        >>> form.csv_content()
        <StringIO.StringO object at 0x102fd2f48>
        >>>


    ``CSV_COLUMNS`` defines a list of properties to fetch from each obj in the
    queryset which will be output in the csv content.  The ``column`` key defines
    the lookup path for the property.  This can lookup a field, property
    method, or method on the model which may span relationships.  The ``title``
    key defines the column header to use for that property in the csv content.

    The :func:`csv_content` method returns a string buffer with csv content for the
    form's queryset.
    """
    def csv_content(self):
        """
        Returns the objects in the form's current queryset as csv content.
        """
        if not hasattr(self, 'CSV_COLUMNS'):
            raise NotImplementedError('Child classes of CsvForm must implement the CSV_COLUMNS constant')

        # Get column fields and headers
        csv_columns = [i['column'] for i in self.CSV_COLUMNS]
        csv_headers = [i['title'].encode('utf-8') for i in self.CSV_COLUMNS]

        # Build data for csv writer
        csv_data = []
        for obj in self.get_queryset():
            csv_data.append([unicode(csv_getvalue(obj, column)).encode('utf-8') for column in csv_columns])

        # Create buffer with csv content
        content = StringIO.StringIO()
        writer = csv.writer(content)
        writer.writerow(csv_headers)
        writer.writerows(csv_data)
        content.seek(0)

        return content


class UncaptchaBase(object):
    """
    Base class for Uncaptcha forms to centralize the uncaptcha validation.
    """
    def clean_uncaptcha(self):
        value = self.cleaned_data['uncaptcha']
        if value is not None and not value == self.data.get('csrfmiddlewaretoken'):
            raise forms.ValidationError("Incorrect uncaptcha value")
        return value


class UncaptchaForm(UncaptchaBase, forms.Form):
    """
    Extension of ``django.forms.Form`` which adds an UncaptchaField to the
    form.
    """
    uncaptcha = UncaptchaField(required=False)
