import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('BlogPosts')

def lambda_handler(event, context):
    http_method = event['httpMethod']

    if http_method == 'GET':
        # Retrieve a specific blog post based on postId
        post_id = event['queryStringParameters']['postId']
        if not post_id:
            return {
                'statusCode': 400,
                'headers': generate_cors_headers(),
                'body': json.dumps('Missing postId parameter in the URL path')
            }

        response = table.get_item(Key={'postId': post_id})
        item = response.get('Item', {})
        return {
            'statusCode': 200,
            'headers': generate_cors_headers(),
            'body': json.dumps(item)
        }
    else:
        return {
            'statusCode': 400,
            'headers': generate_cors_headers(),
            'body': json.dumps('Invalid HTTP method')
        }

def generate_cors_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET'
    }
