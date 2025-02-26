from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from datetime import datetime, timezone, timedelta
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

# S3クライアントの初期化
s3 = boto3.client('s3')
# S3バケット名
S3_BUCKET = 'myawsbucketrecipeimg2'
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
    def __init__(self, user_id, userName):
        self.id = user_id
        self.userName = userName

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
        user_profile = response['Item']
        userName = user_profile.get('userName', 'NoName')
        return User(user_id, userName)
    return None


@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    # updated_at GSIによる降順並び変え
    sort_response = table.query(
        IndexName='userId-updated_at-index',
        KeyConditionExpression=Key('userId').eq(current_user.id) & Key('updated_at').begins_with('RECIPE#'),
        ScanIndexForward=False
    )
    sort_recipes = sort_response['Items']
    for sort_recipe in sort_recipes:
        sort_recipe['updated_at'] = convert_recipeDatetime_to_StrJstDatetime(sort_recipe['updated_at'])

    return render_template('index.html', enumerate=enumerate, sort_recipes=sort_recipes)

def convert_recipeDatetime_to_StrJstDatetime(recipeDatetime):
    datetime_str = recipeDatetime.split("#")[1]
    dt_utc = datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)
    dt_jst = dt_utc.astimezone(timezone(timedelta(hours=9)))
    str_dt_jst = dt_jst.strftime("%Y-%m-%d %H:%M:%S")
    return str_dt_jst

def get_recipes_from_DynamoDB(user_id):
    response = table.query(
        KeyConditionExpression=Key('userId').eq(user_id) & Key('SK').begins_with('RECIPE#recipe')
    )
    recipes = response['Items']
    return recipes


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        input_email = request.form['email']
        input_password = request.form['password']

        gsi_response = table.query(
            IndexName = 'email-index',
            KeyConditionExpression = Key('email').eq(input_email),
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
        now_time = f'PROFILE#{datetime.now().isoformat()}'
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/add_recipe", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        # 画像を取得し、S3にアップロード
        file = request.files.get("file")
        s3_filename = None
        if file:
            filename = secure_filename(file.filename)
            s3_filename = f"recipe/{current_user.id}/{filename}"
            s3.upload_fileobj(file, S3_BUCKET, s3_filename)
        # リクエスト値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # list型リクエスト値を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        recipe_id = add_recipeCounter(current_user.id)
        # DB書込
        add_recipe_to_DynamoDB(title,recipe_id,ingredients,quantities,instructions,cook_time,memo,s3_filename)
        return f"レシピの追加完了しました！ <a href='{url_for('index')}'>HOMEに戻る</a>"

    return render_template('add_recipe.html')

def add_recipe_to_DynamoDB(title,recipe_id,ingredients,quantities,instructions,cook_time,memo,s3_filename):
    now_time = f'RECIPE#{datetime.now().isoformat()}'
    ingredient_quantity = []
    for ingredient, quantity in zip(ingredients, quantities):
        ingredient_quantity.append({ingredient: quantity})
    cook_time = convert_none_empty_to_null(cook_time)
    memo = convert_none_empty_to_null(memo)
    s3_filename = convert_none_empty_to_null(s3_filename)
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
    return None

def convert_none_empty_to_null(data):
    if data is None:
        return {'NULL': True}
    elif not data:
        return {'NULL': True}
    return data

def convert_null_to_empty(data):
    if data is {'NULL': True}:
        return ""
    return data


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
    recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
    recipe['updated_at'] = convert_recipeDatetime_to_StrJstDatetime(recipe['updated_at'])
    recipe_img_path = recipe.get("recipe_img_path")
    # S3署名付きURLを発行
    signed_url = get_presigned_url(recipe_img_path)
    return render_template(
        'recipe_detail.html', recipe=recipe, enumerate=enumerate, signed_url=signed_url,
    )

def get_recipe_from_DynamoDB(user_id, recipe_id):
    db_response = table.get_item(
        Key={
            'userId': user_id,
            'SK': recipe_id,
        }
    )
    recipe = db_response['Item']
    return recipe

def get_presigned_url(recipe_img_path):
    if not recipe_img_path:  # None または 空文字 の場合
        print("画像パスが存在しません。Noneを返します。")
        return None
    try:
        signed_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': recipe_img_path},
        ExpiresIn=3600
    )
        return signed_url
    except Exception as e:
        print(f"署名付きURLの生成に失敗しました: {e}")
        return None  # エラー発生時は None を返す

@app.route('/upgrade_recipe', methods=['GET', 'POST'])
@login_required
def upgrade_recipe():
    if request.method == 'GET':
        recipe_id = request.args.get('recipe_id')
        recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
        recipe_img_path = recipe.get("recipe_img_path")
        # S3署名付きURLを発行
        signed_url = get_presigned_url(recipe_img_path)
        return render_template(
            'upgrade_recipe.html',recipe=recipe, signed_url=signed_url,
        )
    if request.method == 'POST':
        recipe_id = request.args.get('recipe_id')
        recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
        # S3画像ファイルパス
        recipe_img_path = recipe.get("recipe_img_path")
        created_at = recipe['created_at']
        #　リクエスト値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # list型リクエスト値を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        # S3の画像更新
        file = request.files.get("file")
        if file:
            s3.delete_object(Bucket=S3_BUCKET, Key=recipe_img_path)
            filename = secure_filename(file.filename)
            s3_filename = f"recipe/{current_user.id}/{filename}"
            s3.upload_fileobj(file, S3_BUCKET, s3_filename)
            recipe_img_path = s3_filename
        add_recipe_to_DynamoDB(title,recipe_id,ingredients,quantities,instructions,cook_time,memo,recipe_img_path)
        return redirect( url_for('index') )

@app.route('/delete_recipe')
@login_required
def delete_recipe():
    recipe_id = request.args.get('recipe_id')
    recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
    recipe_img_path = recipe.get("recipe_img_path")
    # DynamoDBからレシピ削除
    table.delete_item(
        Key={'userId': current_user.id,
             'SK': recipe_id,}
    )
    # S3から画像削除
    if recipe_img_path not in (None, {'NULL': True}):
        s3.delete_object(Bucket=S3_BUCKET, Key=recipe_img_path)
    return f"レシピの削除完了しました！ <a href='{url_for('index')}'>HOMEに戻る</a>"
