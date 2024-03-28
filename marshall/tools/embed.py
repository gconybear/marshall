import requests
import json 

from marshall.llms.gpt import GPT 

def embed_text(text: str, model='text-embedding-3-small'):   

    assert model == 'text-embedding-3-small', 'currently, only `text-embedding-3-small` model is supported'

    "basic function that just uses gpt class to get 'text-embedding-3-small' embedding"

    ai = GPT(model_name=None) 

    url = 'https://api.openai.com/v1/embeddings'   
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ai.api_key}',
    } 

    # Data payload
    data = {
        'input': text,
        'model': model
    } 

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data)) 
    if response.status_code != 200:
        return None

    return response.json()['data'][0]['embedding']