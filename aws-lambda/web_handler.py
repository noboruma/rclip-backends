from botocore.exceptions import ClientError
import boto3
import json
import uuid
import time
import os
import stripe
import crypt_utils
import smtp_utils
import secrets_utils
import http_utils

NAMESPACE_TABLE = os.environ['NAMESPACE_TABLE']
CUSTOMERS_TABLE = os.environ['CUSTOMERS_TABLE']

ddb_client = boto3.client('dynamodb')

def generate_valid_unique_namespace():
    namespace = ""
    item = not None
    while item != None:
        namespace = uuid.uuid4()
        namespace = namespace.hex
        resp = ddb_client.get_item(TableName=NAMESPACE_TABLE,
                Key= {
                    'namespace': { 'S': namespace }
                    })
        item = resp.get('Item')
    return namespace

def checkout_session(event, context):
    stripe.api_key = secrets_utils.get_secret('stripe_secrets')['api_key']
    id = event['queryStringParameters']['sessionId']
    checkout_session = stripe.checkout.Session.retrieve(id)
    return json.dumps(checkout_session)

def customer_portal(event, context):
    stripe.api_key = secrets_utils.get_secret('stripe_secrets')['api_key']
    # For demonstration purposes, we're using the Checkout session to retrieve the customer ID.
    # Typically this is stored alongside the authenticated user in your database.
    checkout_session_id = event['body']['sessionId']
    checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)

    # This is the URL to which the customer will be redirected after they are
    # done managing their billing with the portal.
    return_url = os.getenv("DOMAIN")

    session = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=return_url)
    return json.dumps({'url': session.url})

def webhook_payment_received(event, context):
    stripe.api_key =  secrets_utils.get_secret('stripe_secrets')['api_key']
    webhook_secret = secrets_utils.get_secret('stripe_secrets')['webhook_payment']

    try:
        pay_event = stripe.Webhook.construct_event(
            payload=event['body'],
            sig_header=event['headers']['Stripe-Signature'],
            secret=webhook_secret)
        data = pay_event['data']
        event_type = pay_event['type']
        data_object = data['object']
    except Exception:
        return http_utils.response_with_cors(http_utils.FORBIDDEN)

    try:
        if event_type == 'checkout.session.completed':
            passwd = uuid.uuid4().hex[0:6]
            crypted_passwd = crypt_utils.md5_encrypt(passwd)
            # TODO: Make sure the namespace is adeed atomically
            namespace = generate_valid_unique_namespace()
            ddb_client.put_item(
                    TableName = CUSTOMERS_TABLE,
                    Item = {
                        'email': {'S': data_object['customer_details']['email'] },
                        'first_payment_timestamp': {'S': str(int(time.time())) },
                        'last_payment_timestamp': {'S': str(int(time.time())) },
                        'namespace': {'S': namespace },
                        'passwd': {'S': crypted_passwd },
                    }
            )
            ddb_client.put_item(
                    TableName=NAMESPACE_TABLE,
                    Item={
                        'namespace': {'S': namespace },
                        }
                    )
            smtp_utils.send_subscribe_email(smtp_utils.get_smtp_context(),
                                            data_object['customer_details']['email'],
                                            str(passwd))
        elif event_type == 'invoice.paid':
            ddb_client.update_item(TableName=CUSTOMERS_TABLE,
                Key = {
                    'email': { 'S': data_object['customer_email'] },
                },
                UpdateExpression = "set last_payment_timestamp=:t",
                ExpressionAttributeValues = {
                    ':t': {'S': str(int(time.time())) },
                },
                ReturnValues = "UPDATED_NEW"
            )
        elif event_type == 'invoice.payment_failed':
            ddb_client.delete_item(TableName=CUSTOMERS_TABLE,
                      Key = {
                          'email': {'S': data_object['customer_email'] },
                      }
            )
    except Exception as e:
        return http_utils.response_with_cors(http_utils.INTERNAL_ERROR, str(e))

    return http_utils.response_with_cors(http_utils.SUCCESS)

def checkout_namespace(event, context):
    stripe.api_key =  secrets_utils.get_secret('stripe_secrets')['api_key']
    session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': secrets_utils.get_secret('stripe_secrets')['product_id'],
                'quantity': 1,
                }],
            mode='subscription',
            success_url='https://www.remote-clipboard.net/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://www.remote-clipboard.net/cancel.html',
        )

    return http_utils.response_with_cors(http_utils.SUCCESS, json.dumps(session))
