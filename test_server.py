import smtplib
import email.utils
from email.mime.text import MIMEText

# Create the message
msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', 'recipient@example.com'))
msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
msg['Subject'] = 'Simple test message'

print('logging in')
server = smtplib.SMTP('127.0.0.1', 1111)
server.set_debuglevel(True)  # show communication with the server
print('done')
try:
    print('sendin')
    server.sendmail('author@example.com', ['recipient@example.com'], msg.as_string())
    print('done')
finally:
    server.quit()