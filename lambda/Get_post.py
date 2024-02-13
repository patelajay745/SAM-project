import json
import boto3
import uuid
import base64
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('BlogPosts')
s3 = boto3.client('s3')
s3_name = 'myblog-serverless'

def lambda_handler(event, context):
    
    print(event)
    http_method = event['httpMethod']
    
    request_origin = event['headers'].get('origin', '')
    allowed_origin = 'http://serverless.ajayproject.com'
    
    print(f"request_origin: {request_origin}")
    
    if request_origin == allowed_origin:

        if http_method == 'GET':
            # Retrieve all blog posts
            
            response = table.scan()
            items = response.get('Items', [])
            
            # Sort the items by createdAt in descending order
            sorted_items = sorted(items, key=lambda x: x['createdAt'], reverse=True)
    
            return {
                'statusCode': 200,
                'headers': generate_cors_headers(),
                'body': json.dumps(sorted_items)
            }
            
        elif http_method == 'POST':
            # Create a new blog post with date and time
            data = json.loads(event['body'])
            post_id = str(uuid.uuid4())
            current_datetime = datetime.now().isoformat()
            
            fileExtension = data['extension']
            
            timestamp = str(int(datetime.now().timestamp())) + fileExtension
            
            decode_content = base64.b64decode(data['image'])
            
            s3_upload = s3.put_object(Bucket=s3_name, Key=timestamp, Body=decode_content)
            
            image_url = f"https://{s3_name}.s3.amazonaws.com/{timestamp}"  # Update with your S3 bucket URL
            
            table.put_item(
                Item={
                    'postId': post_id,
                    'title': data['title'],
                    'content': data['content'],
                    'createdAt': current_datetime,
                    'updatedAt': current_datetime,
                    'imageUrl': image_url
                }
            )
            return {
                'statusCode': 201,
                'headers': generate_cors_headers(),
                'body': json.dumps(f'{post_id} post created successfully!')
            }
            
        elif http_method == 'PUT':
            # Update an existing blog post with date and time
            data = json.loads(event['body'])
            post_id = event['queryStringParameters']['postId']
            if not post_id:
                return {
                    'statusCode': 400,
                    'headers': generate_cors_headers(),
                    'body': json.dumps('Missing postId parameter')
                }
            
            current_datetime = datetime.now().isoformat()
            
            # Check if there's a new image in the request
            if 'newImage' in data:
                # Upload the new image to S3
                file_extension = data['extension']
                timestamp = str(int(datetime.now().timestamp())) + file_extension
                decode_content = base64.b64decode(data['newImage'])
                
                # Delete the associated image from S3
                post = table.get_item(Key={'postId': post_id}).get('Item', {})
                if 'imageUrl' in post:
                    key = post['imageUrl'].split('/')[-1]
                    print(key)
                    s3.delete_object(Bucket=s3_name, Key=key)
                
                s3_upload = s3.put_object(Bucket=s3_name, Key=timestamp, Body=decode_content)
                image_url = f"https://{s3_name}.s3.amazonaws.com/{timestamp}"
                
                # Update the post with the new image URL
                table.update_item(
                    Key={'postId': post_id},
                    UpdateExpression='SET title = :title, content = :content, imageUrl = :imageUrl, updatedAt = :updatedAt',
                    ExpressionAttributeValues={
                        ':title': data['title'],
                        ':content': data['content'],
                        ':imageUrl': image_url,
                        ':updatedAt': current_datetime
                    }
                )
            else:
                # Update the post without changing the image
                table.update_item(
                    Key={'postId': post_id},
                    UpdateExpression='SET title = :title, content = :content, updatedAt = :updatedAt',
                    ExpressionAttributeValues={
                        ':title': data['title'],
                        ':content': data['content'],
                        ':updatedAt': current_datetime
                    }
                )
            
            return {
                'statusCode': 200,
                'headers': generate_cors_headers(),
                'body': json.dumps(f'{post_id} post updated successfully!')
            }
        
        elif http_method == 'DELETE':
            post_id = event['queryStringParameters']['postId']
            if not post_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps('Missing postId parameter in the URL path')
                }
            
            # Delete the associated image from S3
            post = table.get_item(Key={'postId': post_id}).get('Item', {})
            if 'imageUrl' in post:
                key = post['imageUrl'].split('/')[-1]
                print(key)
                s3.delete_object(Bucket=s3_name, Key=key)
            
            table.delete_item(
                Key={'postId': post_id}
            )
            return {
                'statusCode': 200,
                'headers': generate_cors_headers(),
                'body': json.dumps(f'{post_id} post deleted successfully!')
            }
        else:
            return {
                'statusCode': 400,
                'headers': generate_cors_headers(),
                'body': json.dumps('Invalid HTTP method')
            }
    else:
        return {
                'statusCode': 400,
                'headers': generate_cors_headers(),
                'body': json.dumps('you are not authorized')
            }

def generate_cors_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': 'http://serverless.ajayproject.com',
        # 'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,PUT,DELETE'
    }
