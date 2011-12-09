from django.shortcuts import render
from django.contrib.sessions.backends.db import SessionStore
from django.core.mail import EmailMessage
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url

from fusionbox.app import FusionboxApp
from fusionbox.mail import send_markdown_mail
from fusionbox.http import HttpResponseSeeOther

from fusionbox.contact.forms import ContactForm
from fusionbox.contact.models import Recipient

class ContactApp(FusionboxApp):
    """
    In your urls conf:
        from fusionbox.contact.app import contact_app

        urlpatterns = patterns('',
        ...
        url(r'^contact-us/$', include(contact_app.urls)),
        ...

    In your settings:
        INSTALLED_APPS = (
        ...
        fusionbox.contact,
        ...

    Extending example:
        my_site.my_contact.app:

            from .forms import MyContactForm
            from .models import MyRecipient

            class MyContactApp(fusionbox.contact.app.ContactApp):
                contact_form = MyContactForm
                recipient_model_class = MyRecipient

            contact_app = MyContactApp()

    """

    app_name = 'contact'
    namespace = 'contact'
    contact_form_class = ContactForm
    recipient_model_class = Recipient

    index_template = 'contact/index.html'
    success_template = 'contact/success.html'
    email_template = 'contact/mail/contact_form_submission.md'

    def index(self, request, extra_context={}):
        """
        View that displays the contact form and handles contact form submissions
        """
        env = extra_context

        if request.method == 'POST':
            form = self.contact_form_class_class(request, request.POST)
            if form.is_valid():
                submission = form.save()
                try:
                    recipients = settings.CONTACT_FORM_RECIPIENTS
                except AttributeError:
                    recipients = self.recipient_model_class.objects.filter(is_active = True).values_list('email', flat=True)
                env = {}
                env['submission'] = submission
                env['host'] = request.get_host()
                if recipients:
                    send_markdown_mail(
                            self.email_template,
                            env,
                            to = recipients,)
                return HttpResponseSeeOther(self.reverse('contact_success'))
        else:
            form = self.contact_form_class(request)

        env['contact_form'] = form

        return render(request, self.index_template, env)

    def success(self, request, extra_context={}):
        """
        Success page for contact form submissions
        """
        env = extra_context

        env['site_name'] = getattr(settings, 'SITE_NAME', 'Us')

        return render(request, self.success_template, env)


    def get_urls(self):
         return patterns('',
                url(r'^$', self.index, name='index'),
                url(r'^success/$', self.success, name='success'),
            )

contact_app = ContactApp()
