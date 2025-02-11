from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import decimal

import boto3
from boto3.dynamodb.conditions import Key


app = Flask(__name__)


@app.route('/')
def index():
    my_dict = {
        'insert_something1': 'views.pyのinsert_something1部分です。',
        'insert_something2': 'views.pyのinsert_something2部分です。',
        'test_titles': ['title1', 'title2', 'title3']
    }
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('UserRecipe')

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

    return render_template('index.html', my_dict=my_dict,response=response)


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
