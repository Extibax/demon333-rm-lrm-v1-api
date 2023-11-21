from django.core.mail import EmailMultiAlternatives
from ..settings import EMAIL_HOST_USER


def send_mail(subject: str, body: str, to: str):
    subject, from_email, to = subject, "Local Retail Management <no-reply@cheilbidx.io>", to
    #text_content = 'This is an important message.'
    html_content = body  # '<p>This is an <strong>important</strong> message.</p>'
    msg = EmailMultiAlternatives(subject, '', from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    result = msg.send()
    return result == 1
