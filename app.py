from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import decimal
import uuid

import boto3
from boto3.dynamodb.conditions import Key



app = Flask(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserRecipe')


@app.route('/')
def index():
    my_dict = {
        'insert_something1': 'views.pyのinsert_something1部分です。',
        'insert_something2': 'views.pyのinsert_something2部分です。',
        'test_titles': ['title1', 'title2', 'title3']
    }

    # Scan(DynamoDB Item 全件取得)
    #response = table.scan()

    # getItem(DynamoDB Item PK(+SK)検索で１件のみ取得)
    """
    response = table.get_item(
        Key={
            'userId': 'USER#user1',
            'SK': 'PROFILE'
        }
    )
    response = response['Item']
    """

    # query(DynamoDB Item PK(+SK)検索で複数件取得)
    response = table.query(
        KeyConditionExpression=Key('userId').eq('USER#user1')
    )
    response = response['Items']

    return render_template('index.html', response=response)


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        input_email = request.form['email']
        input_password = request.form['password']

        gsi_response = table.query(
            IndexName = 'email-index',
            KeyConditionExpression = Key('email').eq(input_email)
        )
        # ログイン認証
        if input_password == gsi_response['Items'][0]['password']:
            username = gsi_response['Items'][0]['userName']
            return render_template(
                'index.html', username=username
            )
        else:
            return render_template(
            'login.html',
        )
    if request.method == 'GET':
        return render_template(
            'login.html',
        )


@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('UserRecipe')

        unique_id = uuid.uuid4()
        num_unique_id =  unique_id.int % (10**12)
        now_time = datetime.now().isoformat()
        
        table.put_item(
            Item={
                'userId': 'USER#user' + str(num_unique_id),
                'SK': 'PROFILE',
                'userName': username,
                'password': password,
                'email': email,
                'created_at': now_time,
                'updated_at': now_time,
            }
        )
        return render_template('login.html')
    if request.method == 'GET':
        return render_template(
            'signup.html'
        )





# アトミックカウンター関数
def get_next_sequence(name='atomic_counter', table_name='sequence_table'):
    # DynamoDBリソースの初期化
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    """
    指定されたキーに対して連番を取得する関数
    Args:
        name (str): シーケンス名（例: 'atomic_counter'）
        table_name(str): シーケンスを含むテーブル名 (例: 'sequence_table')
    Returns:
        int: 次のシーケンス番号
    """
    response = table.update_item(
        Key={"name": name},
        UpdateExpression="ADD #value :increment",
        ExpressionAttributeNames={"#value": "value"},
        ExpressionAttributeValues={":increment": decimal.Decimal(1)},
        ReturnValues="UPDATED_NEW"
    )
    return int(response['Attributes']['value'])
@app.route('/add_atomicCounter')
def add_atomicCounter():
    # アトミックカウンター
    next_sequence = get_next_sequence()
    return None
