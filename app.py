from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_dropzone import Dropzone

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from datetime import datetime
import decimal
import os
import pytz
import tempfile
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from config import config


# Flask設定
app = Flask(__name__)
app.config.from_object(config)
app.secret_key = b'gqJpZCI1InFad3OizQ'
dropzone = Dropzone(app)

# S3クライアントの初期化
s3 = boto3.client('s3')
# S3バケット名
BUCKET_NAME = 'myawsbucketrecipeimg2'
# Region
S3_REGION = 'ap-northeast-1'

# DynamoDB設定
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('UserRecipe')


# アップロードフォルダが存在しない場合は作成
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Flask-LoginManager初期設定
login_manager = LoginManager(app)
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
@login_manager.unauthorized_handler
def unauthorized():
    return redirect('dev/login')
@login_manager.user_loader
def load_user(user_id):
    response = table.get_item(
        Key={
            'userId': user_id,
            'SK': 'PROFILE'
        }
    )
    if 'Item' in response:
        return User(user_id)
    return None


@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    response = table.query(
        KeyConditionExpression=Key('userId').eq(current_user.id) & Key('SK').begins_with('RECIPE#recipe')
    )
    recipes = response['Items']
    for recipe in recipes:
        dt = datetime.strptime(recipe['updated_at'], "%Y-%m-%dT%H:%M:%S.%f")
        recipe['updated_at'] = dt.strftime("%Y-%m-%d %H:%M")
    return render_template('index.html',  recipes=recipes, enumerate=enumerate)


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
            user_id = gsi_response['Items'][0]['userId']
            user = User(user_id)
            login_user(user)
            return redirect( url_for('index') )
        else:
            return render_template(
            'login.html',
        )
    if request.method == 'GET':
        return render_template(
            'login.html',
        )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect( url_for('login') )

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        unique_id = uuid.uuid4()
        num_unique_userid =  unique_id.int % (10**12)
        now_time = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
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
"""
@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'GET':
        return render_template('add_recipe.html')
    if request.method == 'POST':
        # 固定の入力欄の値を取得
        print(f"title:{title}")
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
        recipe_id = add_recipeCounter(current_user.id)
        ingredient_quantity = []
        for ingredient, quantity in zip(ingredients, quantities):
            ingredient_quantity.append({ingredient: quantity})
        table.put_item(
            Item={
                'userId': current_user.id,
                'SK': recipe_id,
                'created_at': now_time,
                'updated_at': now_time,
                'title': title,
                'ingredient': ingredient_quantity,
                'step': instructions,
                'cook_time': cook_time,
                'memo': memo,
                'step_img_path': "recipe_filename",
            }
        )
        return redirect( url_for('index') )
"""
@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'GET':
        return render_template('add_recipe.html')
    if request.method == 'POST':
        # リクエスト値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # list型リクエスト値を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        unique_id = uuid.uuid4()
        num_unique_recipeid =  unique_id.int % (10**12)
        now_time = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        recipe_id = add_recipeCounter(current_user.id)
        ingredient_quantity = []
        for ingredient, quantity in zip(ingredients, quantities):
            ingredient_quantity.append({ingredient: quantity})
        # DynamoDB書込
        table.put_item(
            Item={
                'userId': current_user.id,
                'SK': recipe_id,
                'created_at': now_time,
                'updated_at': now_time,
                'title': title,
                'ingredient': ingredient_quantity,
                'step': instructions,
                'cook_time': cook_time,
                'memo': memo,
                'step_img_path': ["a.img", "a.img"],
            }
        )
       
        return redirect( url_for('index') )

def add_recipeCounter(userId):
    """
    指定された userId に対応するレシピカウンターをインクリメントし、
    新しいレシピ ID を返す
    """
    counter_response = table.update_item(
        Key={
            'userId': userId,
            'SK': 'counter'
        },
        UpdateExpression="SET recipe_counter = if_not_exists(recipe_counter, :start) + :inc",
        ExpressionAttributeValues={':start': 0, ':inc': 1},
        ReturnValues="UPDATED_NEW"
    )
    new_counter = counter_response.get('Attributes', {}).get('recipe_counter', 0)
    # レシピIDを作成
    new_recipe_id = f"RECIPE#recipe{int(new_counter)}"
    return new_recipe_id

@app.route('/recipe_detail/<string:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    response = table.get_item(
        Key={
            'userId': current_user.id,
            'SK': recipe_id,
        }
    )
    recipe = response['Item']
    dt = datetime.strptime(recipe['updated_at'], "%Y-%m-%dT%H:%M:%S.%f")
    recipe['updated_at'] = dt.strftime("%Y-%m-%d %H:%M")
    return render_template(
        'recipe_detail.html', recipe=recipe, enumerate=enumerate,
    )

@app.route('/upgrade_recipe', methods=['GET', 'POST'])
@login_required
def upgrade_recipe():
    if request.method == 'GET':
        # クエリパラメータにより変数を受け取る
        recipe_id = request.args.get('recipe_id')
        response = table.get_item(
            Key={
                'userId': current_user.id,
                'SK': recipe_id,
            }
        )
        recipe = response['Item']
        return render_template(
            'upgrade_recipe.html',recipe=recipe
        )
    if request.method == 'POST':
        recipe_id = request.args.get('recipe_id')
        # 固定の入力欄の値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # 動的な入力欄の値(list型)を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        # DB読み込み

        # DB書込
        now_time = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        ingredient_quantity = []
        for ingredient, quantity in zip(ingredients, quantities):
            ingredient_quantity.append({ingredient: quantity})
        table.put_item(
            Item={
                'userId': current_user.id,
                'SK': recipe_id,
                'created_at': now_time,
                'updated_at': now_time,
                'title': title,
                'ingredient': ingredient_quantity,
                'step': instructions,
                'cook_time': cook_time,
                'memo': memo,
                'step_img_path': ["a.img", "a.img"],
            }
        )
        return redirect( url_for('index') )

@app.route('/delete_recipe')
@login_required
def delete_recipe():
    recipe_id = request.args.get('recipe_id')
    table.delete_item(
        Key={'userId': current_user.id,
             'SK': recipe_id,}
    )
    return redirect( url_for('index') )


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/dragAndDrop", methods=["GET", "POST"])
def dragAndDrop():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        file = request.files.get("file")

        if not title:
            return "Title is required!"
        if not file:
            return "No file uploaded!"

        filename = secure_filename(file.filename)
        s3_filename = f"recipe/{current_user.id}/{filename}"

        # S3 にアップロード
        s3.upload_fileobj(file, BUCKET_NAME, s3_filename)
        file_url = f"https://{BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_filename}"
        print(f'filename : {filename}')
        print(f'file_url : {file_url }')

        # リクエスト値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # list型リクエスト値を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")

        now_time = datetime.now().isoformat()
        recipe_id = add_recipeCounter(current_user.id)
        ingredient_quantity = []
        for ingredient, quantity in zip(ingredients, quantities):
            ingredient_quantity.append({ingredient: quantity})
        # DynamoDB書込
        table.put_item(
            Item={
                'userId': current_user.id,
                'SK': recipe_id,
                'created_at': now_time,
                'updated_at': now_time,
                'title': title,
                'ingredient': ingredient_quantity,
                'step': instructions,
                'cook_time': cook_time,
                'memo': memo,
                'recipe_img_path': s3_filename,
            }
        )
        return f"レシピの追加完了しました！ <a href='{url_for('index')}'>HOMEに戻る</a>"

    return render_template('dragAndDrop.html')
