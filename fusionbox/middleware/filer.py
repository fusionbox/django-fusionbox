from __future__ import absolute_import

import mimetypes

from django.http import HttpResponse
from django.db.models import Q

from filer.models import File


def get_file_for_parts(parts):
    """
    ['foo', 'bar', 'baz.png'] -> the filer file object at 'foo/bar/baz.png'
    """
    assert parts, "at least one path part (the filename) is required"

    # A naive implementation would do one join per part. This is
    # untenable with path is thousands of components long. Instead, do
    # up to MAX_JOINS joins, and recheck afterwards that the path is
    # correct. This allows us to efficiently support paths of any depth.
    MAX_JOINS = 5

    path_without_filename = parts[:-1]
    filename = parts[-1]

    lookup_path = 'folder'
    # folder filter conditions
    # {'folder__name': 'baz',
    #  'folder__parent__name': 'bar',
    #  'folder__parent__parent__name': 'foo'}
    filter_kwargs = {}
    for part in list(reversed(path_without_filename))[:MAX_JOINS]:
        filter_kwargs['%s__name' % lookup_path] = part
        lookup_path += '__parent'

    # use name, or if name is blank use original_filename
    filename_q = (
        Q(Q(name=None) | Q(name=''), original_filename=filename) |
        Q(name=filename)
    )

    if len(path_without_filename) <= MAX_JOINS:
        # If we are able to do all the joins we need to, just make sure
        # the top folder is the root.
        filter_kwargs['%s__isnull' % lookup_path] = True
        return File.objects.get(filename_q, **filter_kwargs)
    else:
        # We weren't able to check all path components in SQL. This
        # means we get all files whose path shares a suffix with
        # `parts`. Fetch each of these files, checking their full paths.
        possibilities = File.objects.filter(filename_q, **filter_kwargs).select_related('folder')
        for f in possibilities:
            if [i.name for i in f.logical_path] == path_without_filename:
                return f
        raise File.DoesNotExist


class FilerPublicHtmlMiddleware(object):
    """
    Serves files out of a django-filer 'public_html' folder. Allows
    users to upload their own robots.txt, sitemap.xml, etc. files.

        http://website.com/foo.xml         -> public_html/foo.xml
        http://website.com/foo/bar/foo.xml -> public_html/foo/bar/foo.xml
        http://website.com/foo/bar/        -> public_html/foo/bar/index.html

    If using ``APPEND_SLASH``, this middleware should come before
    CommonMiddleware so it can check if the file exists before the path gets
    mangled.

    """

    # Careful here, possible XSS if non-superusers can upload HTML, SVG,
    # XML, etc. A check for the file's owner being a superuser would
    # be appropriate to allow other mimetypes, but it would be rather
    # mysterious for other users who wouldn't be able to get it to work,
    # with no warning.
    allowed_mimetypes = set([
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/gif',
    ])

    base_folder = ['public_html']

    def process_request(self, request):
        path = request.get_full_path()
        if path.endswith('/'):
            path += 'index.html'

        parts = self.base_folder + path.split('/')[1:]

        try:
            file = get_file_for_parts(parts)
        except File.DoesNotExist:
            pass
        else:
            mimetype, encoding = mimetypes.guess_type(parts[-1])
            if mimetype not in self.allowed_mimetypes:
                mimetype = 'application/octet-stream'
            # Maybe consider X-SendFile?
            return HttpResponse(file.file.read(), content_type=mimetype)
