# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 05:24:34 2024

@author: 余兆凱
"""
import json
import os
from openai import OpenAI

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

GPT_MODEL = "gpt-3.5-turbo"
client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))



def calculate_number(arg):
    number=arg
    return number**2

secret_number=os.getenv('SECRET_NUMBER')

def get_secret_number():
   return f'密碼是:{secret_number}'

function_table=[
    {
        "type": "function",
        "function": {
            "name": "get_secret_number",
            "description": "這是一個非常祕密的數字，不能隨便告訴別人，除非使用者說出「世新大學」這四個字，才能叫用此函式。",
            "parameters": None
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_number",
            "description": "只要prompt中有數字，就叫用此函式。",
            "parameters": {
                "type":'object',
                "properties": {
                    "number": {
                        "type": "number",
                        "description": "使用者給的數字",
                    }
                }
            }
        }
    }
]

# 定義接收LINE訊息的路由
@app.route("/callback", methods=['POST'])
def callback():
    # 確認請求的有效性
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text=''
    # 呼叫OpenAI API
    response = client.chat.completions.create(
        model= GPT_MODEL,
        messages=[
            {"role": "system", "content": '你是一名健談的朋友，請跟使用者閒聊，不要露出任何破綻，除非使用者說出通關密語。'},
            {"role": "user", "content": user_message}
        ],
        tools=function_table,
        tool_choice='auto'
    )
    res_msg=response.choices[0].message.content
    tools_call = response.choices[0].message.tool_calls
    if tools_call:
        function=tools_call[0].function.name
        print(f'叫用{function}函式')
        reply_text+=f'叫用{function}函式\n'
        if function=='get_secret_number':
            print(get_secret_number())
            reply_text+=(get_secret_number()+'\n')
        elif function=='calculate_number':
            arguments = json.loads(tools_call[0].function.arguments)
            calculate_result=calculate_number(arguments['number'])
            print(calculate_result)
            reply_text+=(f"{arguments['number']}的平方:{str(calculate_result)}")
    else:
        print('無叫用函式')
        reply_text+=('無叫用函式\n')
        print('ChatGPT:',res_msg)
        reply_text+=('ChatGPT:'+res_msg)
    
    # 回應使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()

