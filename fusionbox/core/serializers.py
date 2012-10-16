from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet


class FusionboxJSONEncoder(DjangoJSONEncoder):
    """
    Tries to call `to_json` on the subject before passing the result to
    `django.core.serializers.json.DjangoJSONEncoder.encode`.
    """
    def default(self, o):
        try:
            return o.to_json()
        except AttributeError:
            pass

        if isinstance(o, QuerySet):
            return list(o)

        return super(FusionboxJSONEncoder, self).default(o)
