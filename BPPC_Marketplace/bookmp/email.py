import sendgrid
from sendgrid.helpers.mail import *
from sendgrid import SendGridAPIClient
from BPPC_Marketplace import keyconfig


def send_confirmation_mail(email_address, confirmation_link):
    sg = SendGridAPIClient(keyconfig.SENDGRID_APIKEY)
    from_email = Email("market@bits-dvm.org")
    to_email = To(str(email_address))
    subject = "BPPC Marketplace Email Verification Required"
    content = Content(
        "text/plain", "Thanks for registering on BPPC Marketplace. Click the following link to confirm your email - " + str(confirmation_link))
    mail = Mail(from_email, to_email, subject, content)
    response = sg.send(mail)
    return response
