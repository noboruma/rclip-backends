import boto3
import json

def get_secret(key):
    ssm_client = boto3.client('secretsmanager')
    get_secret_value_response = ssm_client.get_secret_value(SecretId=key)
    return json.loads(get_secret_value_response['SecretString'])
