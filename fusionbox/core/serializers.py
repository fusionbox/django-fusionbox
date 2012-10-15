from django.core.serializers.json import DjangoJSONEncoder


class FusionboxJSONEncoder(DjangoJSONEncoder):
    """
    Tries to call `to_json` on the subject before passing the result to
    `django.core.serializers.json.DjangoJSONEncoder.encode`.
    """
    def encode(self, o):
        try:
            o = o.to_json()
        except AttributeError:
            pass

        try:
            o = [i.to_json() for i in o]
        except (AttributeError, TypeError):
            pass
        return super(FusionboxJSONEncoder, self).encode(o)
