import datetime

from django.utils import unittest, timezone
from django.forms import ValidationError
from mock import patch

from fusionbox.forms.fields import CCExpirationDateField, CCNumberField


class TestCCExpirationDateField(unittest.TestCase):

    def setUp(self):
        self.field = CCExpirationDateField()

    def test_not_a_date(self):
        with self.assertRaises(ValidationError):
            self.field.clean('asdfasdf')

        with self.assertRaises(ValidationError):
            self.field.clean('12')

    def test_looks_like_a_date_but_isnt(self):
        with self.assertRaises(ValidationError):
            self.field.clean('50 / 2012')

    def test_expired_date(self):
        with patch.object(timezone, 'now') as mocked_timezone:
            mocked_timezone.return_value = datetime.datetime(day=1, month=5, year=2005)

            with self.assertRaises(ValidationError):
                self.field.clean('04 / 05')

            self.field.clean('05 / 05')

            with self.assertRaises(ValidationError):
                self.field.clean('10 / 04')

    def test_month_year(self):
        with patch.object(timezone, 'now') as mocked_timezone:
            mocked_timezone.return_value = datetime.datetime(day=1, month=5, year=2005)

            value = self.field.clean('03 / 2006')
            self.assertEqual(value.month, 3)
            self.assertEqual(value.year, 2006)


class TestCCNumberField(unittest.TestCase):

    def setUp(self):
        self.field = CCNumberField()

    def test_creditcard_number(self):
        self.assertEqual(self.field.clean('4242 4242 4242 4242'), 4242424242424242)

    def test_last_four(self):
        self.assertEqual(self.field.clean('42424242').last_four, 4242)
