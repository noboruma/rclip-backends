SUCCESS = 200
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
INTERNAL_ERROR = 500
NOT_IMPLEMENTED = 501

def response_with_cors(code, body=''):
    return {
        "statusCode": code,
        "body": body,
        "headers": {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST',
            'Access-Control-Allow-Credentials': 'true',
        },
    }

