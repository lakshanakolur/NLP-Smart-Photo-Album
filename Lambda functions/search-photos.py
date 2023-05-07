import json
import boto3
import time
import requests
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    print("Hello from local")
    logger.debug('event')
    logger.debug(event)
    
    #get query from API gateway 'q'
    inputText = event['queryStringParameters']['q']
    print(event)
    #disambiguate the query using amazon lex
    lex = boto3.client('lex-runtime', region_name = 'us-west-2')
    response = lex.post_text(
        botName = 'SearchBot',
        botAlias = 'Search',
        userId = '0123456789',
        sessionAttributes={
        },
        requestAttributes={
        },
        
        inputText = inputText, 
        activeContexts=[
        ]
    )
    slots = response['slots']
    print(slots)
    keywords = []
    for key, value in slots.items():
        if value:
            keywords.append(value)
    print(keywords)
    
    #search elastic search index for the keywords
    host = 'search-photoalbum2-q2e7obqzzx7fmclfqpj57uodvq.us-west-2.es.amazonaws.com'
    region = 'us-west-2'
    service = 'es'
    credentials = boto3.Session().get_credentials()

    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    print(credentials.token)
    
    search = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    headers = { "Content-Type": "application/json" }
    list_of_keywords = []
    for i in keywords:
        list_of_keywords.append(
            {"match": 
                {"labels": i}
            })
    
    query = {"query":
                {"bool": 
                    {"should": 
                        list_of_keywords
                    }
                }
            }
            
    result = search.search(index="photos", doc_type="photo",body=query)
    print('result')
    print(type(result))
    print(result['hits']['hits'])

    photos = []
    for i in result['hits']['hits']:
        objectKey = i['_source']['objectKey']
        bucket = i['_source']['bucket']
        url = "https://" + bucket + ".s3.us-west-2.amazonaws.com/" + objectKey
        photos.append(url)
    
    return {
        'statusCode': 200,
        'headers':{
            'Access-Control-Allow-Origin':'*'
        },
        'body': json.dumps({"results":photos})
    }

