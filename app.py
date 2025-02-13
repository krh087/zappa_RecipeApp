from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import decimal
import uuid

import boto3
from boto3.dynamodb.conditions import Key


app = Flask(__name__)
app.config.from_object('config')

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

        unique_id = uuid.uuid4()
        num_unique_userid =  unique_id.int % (10**12)
        now_time = datetime.now().isoformat()
        table.put_item(
            Item={
                'userId': 'USER#user' + str(num_unique_userid),
                'SK': 'PROFILE',
                'userName': username,
                'password': password,
                'email': email,
                'created_at': now_time,
                'updated_at': now_time,
            }
        )
        return render_template(
            'login.html'
        )
    if request.method == 'GET':
        return render_template(
            'signup.html'
        )

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'GET':
        return render_template('add_recipe.html')
    if request.method == 'POST':
        # 固定の入力欄の値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # 動的な入力欄の値(list型)を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        # DB書込
        unique_id = uuid.uuid4()
        num_unique_recipeid =  unique_id.int % (10**12)
        now_time = datetime.now().isoformat()
        recipe_id = add_recipe('USER#user484824819085')
        ingredient_quantity = []
        for ingredient, quantity in zip(ingredients, quantities):
            ingredient_quantity.append({ingredient: quantity})
        table.put_item(
            Item={
                'userId': 'USER#user484824819085',
                'SK': recipe_id,
                'created_at': now_time,
                'updated_at': now_time,
                'title': title,
                'ingredient': ingredient_quantity,
                'cook_time': cook_time,
                'memo': memo,
                'step_img_path': ["a.img", "a.img"],
            }
        )
       
        return render_template(
            'login.html'
        )

def add_recipe(userId):
    # ユーザーのカウンターをインクリメント
    counter_response = table.update_item(
        Key={
            'userId': userId,
            'SK': 'counter'
            },
        UpdateExpression="SET recipe_counter = if_not_exists(recipe_counter, :start) + :inc",
        ExpressionAttributeValues={':start': 0, ':inc': 1},
        ReturnValues="UPDATED_NEW"
    )
    new_recipe_id = f"RECIPE#recipe{int(counter_response['Attributes']['recipe_counter'])}"
    return new_recipe_id
