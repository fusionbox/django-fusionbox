---
subject: "Contact Form Submission"
---
Contact Form Submission

{% for field in submission %}
**{{field.name}}:** {{field.value|linebreaks}}

{% endfor %}
