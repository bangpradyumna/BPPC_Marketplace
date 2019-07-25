import sendgrid
from sendgrid.helpers.mail import *
from BPPC_Marketplace import keyconfig

def send_confirmation_mail(email_address, confirmation_link):
    sg = sendgrid.SendGridAPIClient(apikey=keyconfig.SENDGRID_APIKEY)
    from_email = Email("dushyantvsmessi@gmail.com")
    to_email = Email(str(email_address))
    subject = "Confirmation of your email account"
    content = Content("text/plain", "Please click on this link - " + str(confirmation_link))
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return response


