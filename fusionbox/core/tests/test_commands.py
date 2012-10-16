import warnings
from django.test import TestCase
from django.test.utils import override_settings


class RedirectFallbackMiddlewareTests(TestCase):

    @override_settings(MIDDLEWARE_CLASSES=tuple())
    def test_raise_warning(self):
        from fusionbox.core.management.commands.validate_redirects import (
            Command as ValidateRedirectsCommand
        )
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            ValidateRedirectsCommand().handle()
            assert len(w) == 1
            assert issubclass(w[-1].category, RuntimeWarning)

    @override_settings(MIDDLEWARE_CLASSES=('fusionbox.middleware.RedirectFallbackMiddleware',))
    def test_dont_raise_warning(self):
        from fusionbox.core.management.commands.validate_redirects import (
            Command as ValidateRedirectsCommand
        )
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            ValidateRedirectsCommand().handle()
            assert len(w) == 0
