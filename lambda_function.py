import json
import boto3
import requests
import time
from heapq import *
from boto3.dynamodb.conditions import Key

def getHelpfulness(h1, h2):
    if h2 == 0:
        return 0.3
    return h1 * 1.0 / h2

def getSimilarity(str1, str2):
    '''
    str1: user query
    str2: review
    '''
    set1 = set()
    set2 = set()
    for word in str1.lower().split(' '):
        set1.add(word)
    for word in str2.split(' '):
        set2.add(word)
    return len(set1 & set2) * 1.0 / len(set1)

def arrary2obj(arr, user_profile):
    # ProductId, Name, URL, Img, Tags, ProfileName, Score, Summary, Review
    res = {}
    res["productId"] = arr[0]
    res["name"] = arr[1]
    res["url"] = arr[2]
    res["img"] = arr[3]
    res["tags"] = arr[4]
    res["profileName"] = arr[5]
    res["score"] = arr[6]
    res["summary"] = arr[7]
    res["review"] = arr[8]
    res["userAge"] = user_profile["userAge"]
    res["userGender"] = user_profile["userGender"]
    res["searchWord"] = user_profile["foodType"]
    
    return res
    
    
def item2obj(item):
    res = {}
    res["productId"] = item["productId"]
    res["name"] =  item["name"]
    res["url"] = item["url"]
    res["img"] = item["img"]
    res["tags"] = item["tags"]
    res["profileName"] = item["profileName"]
    res["score"] = item["score"]
    res["summary"] = item["summary"]
    res["review"] = item["review"]
    res["userAge"] = item["userAge"]
    res["userGender"] = item["userGender"]
    res["searchWord"] = item["searchWord"]
    
    return res
    
def lambda_handler(event, context):
    # read dynamodb
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('Snack_log')
    db_response = table.scan(
        FilterExpression=Key('timestamp').gt(0)
    )
    items_list = db_response['Items']
    selected_item_list = []
    for item in items_list:
        if getSimilarity(event['foodType'], item['searchWord']) > 0 and item['action'] == 'like' and item['userGender'].lower() == event['userGender'].lower() and int(event['userAge']) - 2 <= int(item['userAge']) and int(event['userAge']) + 2 >= int(item['userAge']):
            selected_item_list.append(item)
    try:
        selected_item_list = sorted(selected_item_list, key=lambda item: int(
            item['timestamp']), reverse=True)
    except:
        pass
    res = []
    count = 0
    for item in selected_item_list:
        res.append(item2obj(item))
        count += 1
        if count == 5:
            break
    
    # read s3 file
    t1 = time.time()
    s3 = boto3.client('s3')
    response = s3.get_object(
        Bucket='finalprojspark',
        Key='result.csv'
    )
    file_body = str(response['Body'].read())
    search_word = event['foodType']
    # search_word = 'dark chocolate'
    # print(event)
    reviews = file_body[2:-1].split('\\n')
    score = []
    heap = []
    heap_count = 0
    K = 10
    for review in reviews[:-1]: 
        elems = review.split('\\t') # ProductId, Name, URL, Img, Tags, ProfileName, Score, Summary, Review
        name = elems[1].lower()
        tags = elems[4].lower()
        s = float(elems[6])
        summary = elems[7].lower()
        text = elems[8]
        s *= getSimilarity(search_word, name+' '+tags+' '+summary+' '+text)**2
        score.append(s)
        if heap_count < K:
            heappush(heap, (s, review))
            heap_count += 1
        else:
            heappushpop(heap, (s, review))
    for item in heap:
        # print(item)
        elems = item[1].split('\\t')
        obj_temp = arrary2obj(elems, event)
        res.append(obj_temp)
    # print(res)
    
    # return
    return res
    
    
    # print(time.time()-t1)