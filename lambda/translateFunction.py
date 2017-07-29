import urllib
import json
import boto3
from boto3 import resource
from boto3.dynamodb.conditions import Key, Attr

region_name = 'ap-south-1'
dynamo = boto3.client('dynamodb', region_name=region_name)

table_name = 'test'                                 #DB TABLE 
table = resource('dynamodb').Table(table_name)

api_key = 'AIzaSyBifplJ7fgurI1FZI4uODk-0eKb8fgJ4xc'     #API KEY FOR GOOGLE TRANSLATE

def lambda_handler(event, context):
    if 'challenge' in event:
        return event['challenge']
    # text = event['text']
    text = event['event']['text']
    team_id = event['team_id']
    # user_id = event['user_id']
    user_id = event['event']['user']
    # user_name = event['user_name']
    user_name = "|Translations|"
    #src_lang = event['source_lang']    # Derive from DB
    tgt_lang = 'de'         #Derive from DB
    
    arr = text.split(' ')
    print(arr)
    if arr[0] == 'config':
        save_to_db(team_id, user_id, arr[1])
        return 'Language Preference ' + arr[1] + ' configured for ' + user_name
    
    url = 'https://translation.googleapis.com/language/translate/v2'
    
    langList = {}
    langList = getLangList(team_id, user_id)
    retStr = '|' + user_name + '| ' + '\n'
    for tgt_lang in langList:
        headers = {'q':text, 'target':tgt_lang, 'key':api_key}
        encoded_url = url + '?' + urllib.parse.urlencode(headers)
        # r = requests.get(encoded_url)
        response = urllib.request.urlopen(encoded_url)
        data = json.load(response) 
        print(data)
        # return '{\'text\' : data[\'data\'][\'translations\'][\'translatedText\']}'
        retStr = retStr + '[' + tgt_lang + '] ' + data['data']['translations'][0]['translatedText'] + '\n'
        
    url = 'https://hooks.slack.com/services/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'
    post_fields = {'text' : retStr}
    params = json.dumps(post_fields ).encode('utf-8')
    req = urllib.request.Request(url, data=params,
                             headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    print(response.read())
    return {'text' : retStr, 'username' : 'Transalations'}

def save_to_db(team, user, lang):
    # subtract owed_amount from user
    dynamo.put_item(
        TableName=table_name,
        Item={
            'userid' : {
                'S' : user
            },
            'langPref' :{
                'S': lang
            },
            'teamid' : {
                'S' : team
            }
        }
    )
    
def get_from_db(team_id, user_id):
    # subtract owed_amount from user
    filtering_exp = Key('teamid').eq(team_id)&Attr('userid').ne(user_id)
    # resp = dynamo.scan(
    #     TableName=table_name,
    #     FilterExpression=filtering_exp
    # )
    resp = table.scan(FilterExpression=filtering_exp)
    
    items = resp['Items']
    print("RESPONSE\n")
    print(resp)
    return items

def getLangList(team_id, user_id):
    items = get_from_db(team_id, user_id)
    langList = []
    for item in items:
        print("Fetched language ", item['langPref'])
        langList.append(item['langPref'])
    
    return langList