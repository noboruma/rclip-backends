from botocore.exceptions import ClientError
import boto3
import json
import uuid
import time
import os
import crypt_utils
import http_utils

CLIPBOARD_TABLE = os.environ['CLIPBOARD_TABLE']
LINK_TABLE      = os.environ['LINK_TABLE']
CUSTOMERS_TABLE = os.environ['CUSTOMERS_TABLE']
NAMESPACE_TABLE = os.environ['NAMESPACE_TABLE']
TOKEN_PARAM     = 'TOKEN'
NAMESPACE_PARAM = 'NAMESPACE'
SHORTHASH_PARAM = 'shortHash'
TEXT_PARAM      = 'text'
PAYLOAD_LIMIT_B = 5000

ddb_client = boto3.client('dynamodb')

class InvalidToken(Exception):
    pass
class InvalidNamespace(Exception):
    pass

def trim_escape_token(token):
    return token[0:6]

def prepend_namespace(event, token):
    if NAMESPACE_PARAM in event['queryStringParameters']:
        namespace = event['queryStringParameters'][NAMESPACE_PARAM]
        if not is_namespace_valid(namespace):
            raise InvalidNamespace
        token = namespace + token

def get_token(event):
    token = event['queryStringParameters'][TOKEN_PARAM]
    if not token:
        raise InvalidToken
    else:
        return trim_escape_token(token)

def is_namespace_valid(namespace):
    resp = ddb_client.get_item(TableName=NAMESPACE_TABLE,
            Key= {
                'namespace': { 'S': namespace }
                })
    return resp.get('Item') != None

def push_clipboard(event, context):
    if TEXT_PARAM in event['queryStringParameters']:
        text = event['queryStringParameters'][TEXT_PARAM]
    else:
        text = event['body']
        if len(text) > PAYLOAD_LIMIT_B:
            return http_utils.response_with_cors(http_utils.NOT_IMPLEMENTED)

    try:
        token = get_token(event)
        prepend_namespace(event, token)
    except InvalidNamespace:
        return http_utils.response_with_cors(http_utils.FORBIDDEN)
    except InvalidToken:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)

    ddb_client.put_item(
               TableName=CLIPBOARD_TABLE,
               Item={
                   'token': {'S': token },
                   'text': {'S': text },
               }
           )
    return http_utils.response_with_cors(http_utils.SUCCESS, '{}')

def pull_clipboard(event, context):

    try:
        token = get_token(event)
        prepend_namespace(event, token)
    except InvalidNamespace:
        return http_utils.response_with_cors(http_utils.FORBIDDEN)
    except InvalidToken:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)

    resp = ddb_client.get_item(TableName=CLIPBOARD_TABLE,
                           Key= {
                                'token': { 'S': token }
                           })

    item = resp.get('Item')

    if not item:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)

    text = item.get('text').get('S')

    return http_utils.response_with_cors(http_utils.SUCCESS,
            json.dumps({
            TEXT_PARAM: text
        }))

def generate_valid_unique_token():
    token = ""
    item = not None
    while item != None:
        token = uuid.uuid4()
        token = token.hex[0:6]
        resp = ddb_client.get_item(TableName=LINK_TABLE,
                Key= {
                    'shortHash': { 'S': token }
                    })
        item = resp.get('Item')
    return token

def open_clipboard(event, context):

    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token or token == '':
        token = generate_valid_unique_token()
    else:
        token = trim_escape_token(token)
        ddb_client.delete_item(TableName=LINK_TABLE,
                Key= {
                    'shortHash': {'S': token }
                    })

    shortToken = token[0:6]

    try:
        prepend_namespace(event, token)
    except:
        return http_utils.response_with_cors(http_utils.FORBIDDEN)

    ddb_client.put_item(
            TableName=LINK_TABLE,
            Item={
                'shortHash': {'S': shortToken },
                'token': {'S': token },
                'ttl': {'S': str(int(time.time())) },
                }
            )

    return http_utils.response_with_cors(http_utils.SUCCESS,
            json.dumps({
                TEXT_PARAM: token
            }))

def link_clipboard(event, context):

    short_token = event['queryStringParameters'][SHORTHASH_PARAM]

    if not short_token:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)
    else:
        short_token = trim_escape_token(short_token)

    resp = ddb_client.get_item(TableName=LINK_TABLE,
                           Key= {
                                'shortHash': { 'S': short_token }
                           })

    item = resp.get('Item')

    if not item:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)

    ttl = int(item.get('ttl').get('S'))

    current_time = int(time.time())
    if current_time - ttl > 30:
        return http_utils.response_with_cors(http_utils.UNAUTHORIZED)

    return http_utils.response_with_cors(http_utils.SUCCESS,
            json.dumps({
                TOKEN_PARAM: item.get('token').get('S')
            }))

def login_clipboard(event, context):

    email = event['queryStringParameters']['email']
    crypted_text = crypt_utils.md5_encrypt(event['queryStringParameters']['passwd'])

    resp = ddb_client.get_item(TableName=CUSTOMERS_TABLE,
                           Key= {
                                'email': { 'S': email }
                           })

    item = resp.get('Item')

    if not item:
        return http_utils.response_with_cors(http_utils.NOT_FOUND)

    crypted_passwd = item.get('passwd').get('S')

    if crypted_text == crypted_passwd:
        return http_utils.response_with_cors(http_utils.SUCCESS,
            json.dumps({
                NAMESPACE_PARAM: item.get('namespace').get('S')
            }))
    else:
        return http_utils.response_with_cors(http_utils.FORBIDDEN)
