import json
import boto3

def lambda_handler(event, context):
    # Extract username and password from the query parameters
    
    print(event)
    username = event['queryStringParameters']['username']
    password = event['queryStringParameters']['password']

    # Check credentials against DynamoDB table
    is_authenticated = check_credentials(username, password)

    # Return a response indicating authentication status
    response = {
        'isAuthenticated': is_authenticated
    }

    return {
        'statusCode': 200,
        'headers': generate_cors_headers(),
        'body': json.dumps(response)
    }

def check_credentials(username, password):
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('login')  # Replace 'login' with your actual table name

    # Scan DynamoDB table for the provided username and password
    response = table.scan(
        FilterExpression='username = :u and password = :p',
        ExpressionAttributeValues={
            ':u': username,
            ':p': password
        }
    )

    # Check if a matching record was found
    return len(response['Items']) > 0
    
    
def generate_cors_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }
