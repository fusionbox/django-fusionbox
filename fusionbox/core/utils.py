from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

import phonenumbers

def format_phonenumber(number, region):
    """
    Format a phonenumber for dialing from the specified region.
    Regions can be: "US", "JP", "FR", ...
    """
    region = region.upper()
    n = phonenumbers.parse(number, region)

    if phonenumbers.region_code_for_number(n) == region:
        formatting = phonenumbers.PhoneNumberFormat.NATIONAL
    else:
        formatting = phonenumbers.PhoneNumberFormat.INTERNATIONAL
    return phonenumbers.format_number(n, formatting)

def format_us_phonenumber(number):
    """
    Format a phonenumber for dialing from the US
    """
    return format_phonenumber(number, "US")


try:
    from django.utils.html import format_html
except ImportError:
    # Django < 1.5 doesn't have this

    def format_html(format_string, *args, **kwargs):  # NOQA
        """
        Similar to str.format, but passes all arguments through
        conditional_escape, and calls 'mark_safe' on the result. This function
        should be used instead of str.format or % interpolation to build up
        small HTML fragments.
        """
        args_safe = map(conditional_escape, args)
        kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in kwargs.iteritems()])
        return mark_safe(format_string.format(*args_safe, **kwargs_safe))
