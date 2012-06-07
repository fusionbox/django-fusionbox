from django import template

from django.utils.safestring import mark_safe


register = template.Library()


class CanHazNode(template.Node):
    """
    Wraps a section of code in <script type="text/html" id="ID">

    ID is a required argument.

    Example::

        {% canhaz user %}
        <div class="user">
            <p><%= name %></p>
        </div>
        {% endcanhaz %}

    Outputs::

        <script type="text/html" id="user">
        <div class="user">
            <p><%= name %></p>
        </div>
        </script>
    """
    def __init__(self, parser, token):
        tokens = token.split_contents()
        tokens.pop(0)  # pop 'canhaz'
        closer = 'endcanhaz'

        try:
            self.script_id = tokens.pop(0)
        except IndexError:
            raise IndexError('"id" is a required argument to canhaz')

        if tokens:
            raise IndexError('Unknown tokens "{0}" in canhaz block'.format(', '.join(tokens)))

        self.nodelist = parser.parse((closer,))
        parser.delete_first_token()

    def render(self, context):
        content = self.nodelist.render(context)
        return mark_safe(
u"""<script type="text/html" id="{script_id}">{content}</script>""".format(script_id=self.script_id, content=content)
            )

register.tag("canhaz", CanHazNode)


class MustacheNode(template.Node):
    """
    Wraps a section of code in <script type="text/html" id="ID">{{=<% %>=}}

    ID is a required argument.

    Example::

        {% canhaz user %}
        <div class="user">
            <p><%= name %></p>
        </div>
        {% endcanhaz %}

    Outputs::

        <script type="text/html" id="user">{{=<% %>=}}
        <div class="user">
            <p><%= name %></p>
        </div>
        <%={{ }}=%></script>
    """
    def __init__(self, parser, token):
        tokens = token.split_contents()
        tokens.pop(0)  # pop 'mustache'
        closer = 'endmustache'

        try:
            self.script_id = tokens.pop(0)
        except IndexError:
            raise IndexError('"id" is a required argument to mustache')

        try:
            self.tag_opener = tokens.pop(0)
            try:
                self.tag_closer = tokens.pop(0)
            except IndexError:
                # if only tag_opener is given, tag_closer is the
                # reverse of tag_opener.
                self.tag_closer = self.tag_opener[::-1]
                for o, c in (
                    ('[', ']'),
                    ('{', '}'),
                    ('(', ')'),
                    ('<', '>'),
                    ):
                    self.tag_closer = self.tag_closer.replace(o, c)
        except IndexError:
            self.tag_opener = '<%'
            self.tag_closer = '%>'

        if tokens:
            raise IndexError('Unknown tokens "{0}" in mustache block'.format(', '.join(tokens)))

        self.nodelist = parser.parse((closer,))
        parser.delete_first_token()

    def render(self, context):
        content = self.nodelist.render(context)
        return mark_safe(
            u'<script type="text/html" id="{self.script_id}">'
            u'{{{{={self.tag_opener} {self.tag_closer}=}}}}'  # set new delimiters
            u'{content}'
            u'{self.tag_opener}={{{{ }}}}={self.tag_closer}'  # unset new delimiters
            u'</script>'.format(
                self=self,
                content=content,
                )
            )

register.tag("mustache", MustacheNode)
