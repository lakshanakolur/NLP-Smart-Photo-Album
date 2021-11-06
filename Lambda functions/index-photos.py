import json
import logging
import boto3
import time
import requests
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_photo_labels(bucket, photokey):
    rekClient = boto3.client('rekognition')
    response = rekClient.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photokey}}, MaxLabels=10, MinConfidence=90)
    #logger.debug(response)
    #logger.debug(response['Labels'])
    labels = [label['Name'] for label in response['Labels']]
    #logger.debug(labels)
    return labels
    
def upload_to_es(index, type_doc, new_doc):
    host = 'search-photoalbum2-q2e7obqzzx7fmclfqpj57uodvq.us-west-2.es.amazonaws.com' 
    region = 'us-west-2'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    search = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    search.index(index=index, doc_type=type_doc, body=new_doc )

def lambda_handler(event, context):
    # TODO implement
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        photokey = record['s3']['object']['key']
        print(bucket, photokey)
        labels = []
        labels = get_photo_labels(bucket, photokey)
        new_doc = {
            "objectKey": photokey,
            "bucket": bucket,
            "createdTimestamp": time.strftime("%Y%m%d-%H%M%S"),
            "labels": labels
        }
        
        print(new_doc)
        
        upload_to_es('photos','photo',json.dumps(new_doc))
    
    logger.debug('You got it!')
