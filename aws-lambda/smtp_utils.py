import smtplib, ssl, os, json
import boto3

class Context:
    def __init__(self, smtp_server, port, sender_email, sender_passwd=None):
        self.smtp_server = smtp_server
        self.port = int(port)
        self.sender_email = sender_email
        self.sender_passwd = sender_passwd

def get_secret(key):
    ssm_client = boto3.client('secretsmanager')
    get_secret_value_response = ssm_client.get_secret_value(
            SecretId=key)
    return json.loads(get_secret_value_response['SecretString'])

def get_smtp_context():
    return Context(get_secret('smtp_secrets')['host'],
            get_secret('smtp_secrets')['port'],
            get_secret('smtp_secrets')['sender_email'],
            get_secret('smtp_secrets')['sender_passwd'])

def send_email(context, receiver_email, message):
    with smtplib.SMTP(context.smtp_server, context.port) as server:
        if context.sender_passwd is not None:
            server.login(context.sender_email, context.sender_passwd)
        server.sendmail(context.sender_email, receiver_email, message)

def send_subscribe_email(context, receiver_email, passwd):
    message = f"""\
Subject: Your new remote-clipboard password
To: {receiver_email}
From: {context.sender_email}

Thank you for subscribing!
Your password is {passwd}."""
    send_email(context, context.sender_email, message)
