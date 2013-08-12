import string

from django.test import TestCase

from filer.models import File, Folder

from fusionbox.middleware.filer import get_file_for_parts


class FilerMiddlewareTest(TestCase):
    def test_simple(self):
        f = File.objects.create(name='foo.jpg')

        self.assertEqual(f, get_file_for_parts(['foo.jpg']))

    def test_folder(self):
        folder = Folder.objects.create(name='public_html')
        f = File.objects.create(
            folder=folder,
            name='foo.jpg',
        )
        self.assertEqual(f, get_file_for_parts(['public_html', 'foo.jpg']))

    def test_not_found_simple(self):
        with self.assertRaises(File.DoesNotExist):
            get_file_for_parts(['asdfasdfasdf'])

    def test_not_found_deep(self):
        """
        A path with a common suffix shouldn't count.
        """
        folder = Folder.objects.create(name='public_html')
        File.objects.create(
            folder=folder,
            name='foo.jpg',
        )
        with self.assertRaises(File.DoesNotExist):
            get_file_for_parts(['foo.jpg'])

    def test_original_filename(self):
        f = File.objects.create(
            original_filename='foo.jpg',
        )
        self.assertEqual(f, get_file_for_parts(['foo.jpg']))

    def test_deep(self):
        folder = None
        for i in range(10):
            folder = Folder.objects.create(
                name='a',
                parent=folder
            )

        f = File.objects.create(
            folder=folder,
            name='foo.txt',
        )

        self.assertEqual(f, get_file_for_parts((['a'] * 10) + ['foo.txt']))

        with self.assertRaises(File.DoesNotExist):
            # see test_not_found_deep
            get_file_for_parts((['a'] * 9) + ['foo.txt'])

    def test_deep_different_names(self):
        path = string.ascii_lowercase
        folder = None
        for i in path:
            folder = Folder.objects.create(
                name=i,
                parent=folder
            )

        f = File.objects.create(
            folder=folder,
            name='foo.txt',
        )

        self.assertEqual(f, get_file_for_parts(list(path) + ['foo.txt']))

    def test_no_dos(self):
        # if this terminates, we're fine!
        with self.assertRaises(File.DoesNotExist):
            get_file_for_parts(['a'] * 5000)
