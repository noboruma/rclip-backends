from botocore.exceptions import ClientError
import boto3
import json
import uuid
import time
import os

CLIPBOARD_TABLE = os.environ['CLIPBOARD_TABLE']
LINK_TABLE = os.environ['LINK_TABLE']
TOKEN_PARAM='TOKEN'
SHORTHASH_PARAM='shortHash'
TEXT_PARAM='text'

s3_client = boto3.client('dynamodb')

def push_clipboard(event, context):
    text = event['queryStringParameters'][TEXT_PARAM]
    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token:
        return {
            "statusCode": 404,
        }

    resp = s3_client.put_item(
               TableName=CLIPBOARD_TABLE,
               Item={
                   'token': {'S': token },
                   'text': {'S': text },
               }
           )

    return {
        "statusCode": 200,
        "headers": {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET'
        },
        "body": "{}"
    }

def pull_clipboard(event, context):

    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token:
        return {
            "statusCode": 404,
        }

    resp = s3_client.get_item(TableName=CLIPBOARD_TABLE,
                           Key= {
                                'token': { 'S': token }
                           })

    item = resp.get('Item')

    if not item:
        return {
            "statusCode": 404,
        }

    text = item.get('text').get('S')

    return {
        "statusCode": 200,
        "headers": {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        },
        "body": json.dumps({
            TEXT_PARAM: text
        })
    }

def generate_valid_unique_token():
    token = ""
    item = not None
    while item != None:
        token = uuid.uuid4()
        token = token.hex
        resp = s3_client.get_item(TableName=LINK_TABLE,
                Key= {
                    'shortHash': { 'S': token[0:6] }
                    })
        item = resp.get('Item')
    return token

def open_clipboard(event, context):

    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token or token == '':
        token = generate_valid_unique_token()
    else:
        s3_client.delete_item(TableName=LINK_TABLE,
                Key= {
                    'shortHash': {'S': token[0:6] }
                    })

    s3_client.put_item(
            TableName=LINK_TABLE,
            Item={
                'shortHash': {'S': token[0:6] },
                'token': {'S': token },
                'ttl': {'S': str(int(time.time())) },
                }
            )

    return {
        "statusCode": 200,
        "headers": {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        },
        "body": json.dumps({
            TEXT_PARAM: token
        })
    }

def link_clipboard(event, context):

    short_token = event['queryStringParameters'][SHORTHASH_PARAM]

    resp = s3_client.get_item(TableName=LINK_TABLE,
                           Key= {
                                'shortHash': { 'S': short_token }
                           })

    item = resp.get('Item')

    if not item:
        return {
            "statusCode": 404,
        }

    ttl = int(item.get('ttl').get('S'))

    current_time = int(time.time())
    if current_time - ttl > 30:
        return {
            "statusCode": 405,
        }

    return {
        "statusCode": 200,
        "headers": {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        },
        "body": json.dumps({
            TOKEN_PARAM: item.get('token').get('S')
        })
    }
