from botocore.exceptions import ClientError
import boto3
import json
import uuid
import time

BUCKET='clipboard-bucket2'
HASH_FILE='hashes'
TOKEN_PARAM='TOKEN'
TEXT_PARAM='text'

s3_client = boto3.client('s3')

def push_clipboard(event, context):
    text = event['queryStringParameters'][TEXT_PARAM]
    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token:
        return {
            "statusCode": 404,
        }

    s3_client.put_object(Body=text,
            Bucket=BUCKET, Key=token)

    return {
        "statusCode": 200,
        "body": "{}"
    }

def pull_clipboard(event, context):

    token = event['queryStringParameters'][TOKEN_PARAM]

    if not token:
        return {
            "statusCode": 404,
        }

    obj = s3_client.get_object(Bucket=BUCKET, Key=token)
    text = obj['Body'].read().decode('utf-8')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "text": text
        })
    }

def open_clipboard(event, context):

    try:
        obj = s3_client.get_object(Bucket=BUCKET, Key=HASH_FILE)
        hashes = json.loads(obj['Body'].read().decode('utf-8'))
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
             raise e
        elif error_code == "InvalidLocationConstraint":
            # Not found
            hashes = {}

    token = uuid.uuid4()
    token = token.hex

    new_entry = { "token": token, "ttl": int(time.time()) }
    hashes[token[0:6]] = json.dumps(new_entry)

    s3_client.put_object(Body=json.dumps(hashes),
            Bucket=BUCKET, Key=HASH_FILE)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "text": new_entry["token"]
        })
    }

def link_clipboard(event, context):

    try:
        obj = s3_client.get_object(Bucket=BUCKET, Key=HASH_FILE)
        hashes = json.loads(obj['Body'].read().decode('utf-8'))
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            raise e
        elif error_code == "InvalidLocationConstraint":
            # Not found
            hashes = {}

    short_token = event['queryStringParameters'][TEXT_PARAM]

    if not hashes[short_token]:
        return {
            "statusCode": 404,
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "text": hashes[short_token]
        })
    }
    ttl = int(hashes[short_token]['ttl'])


    current_time = int(time.time())
    if current_time - ttl > 30:
        return {
            "statusCode": 405,
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "text": hashes[short_token]['token']
        })
    }
