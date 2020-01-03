import smtplib

gamil_password = ''
gmail_login = ''
adress_to = 'granaty_ot_nikonovoy@mail.ru'

def smtp_send_email(subj,text):
    SUBJECT = subj
    TO = adress_to
    FROM = "python@mydomain.com"
    BODY = "\r\n".join((
        "From: %s" % FROM,
        "To: %s" % TO,
        "Subject: %s" % SUBJECT,
        "",
        text
    ))
    server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server_ssl.ehlo()
    server_ssl.login(gmail_login, gamil_password)
    print(server_ssl.sendmail(FROM, [TO], BODY))
    server_ssl.quit()