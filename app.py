from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    get_flashed_messages,
)
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from markupsafe import Markup
from typing import Optional
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta

import botocore.exceptions
import json
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key

from config import config

import google.generativeai as genai


# AWS Systems Managerクライアントの初期化
SSM_REGION = "ap-northeast-1"
ssm = boto3.client("ssm", region_name=SSM_REGION)


def get_systems_manager_param(param_name: str, with_decryption: bool = True) -> Optional[str]:
    """
    AWS Systems Manager Parameter Store からパラメータを取得する。
    :param param_name: 取得するパラメータの名前
    :param with_decryption: 暗号化されたパラメータを復号するか（デフォルトは True）
    :return: パラメータの値（取得できなかった場合は None）
    """
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=with_decryption)
        return response["Parameter"]["Value"]
    
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ParameterNotFound":
            print(f"パラメータ '{param_name}' が見つかりません。")
        elif error_code == "AccessDeniedException":
            print(f"アクセス権限がありません: {param_name}")
        else:
            print(f"エラー発生: {error_code} - {e}")
    
    except Exception as e:
        print(f"予期しないエラー: {e}")

    return None  # 取得できなかった場合は None を返す


# Flask設定
app = Flask(__name__)
app.config.from_object(config)

# Parameter Store から取得
#app.secret_key = get_systems_manager_param("/zappa_RecipeApp/dev/AppSecret_key")
#GEMINI_API_KEY = get_systems_manager_param("/zappa_RecipeApp/dev/Gemini_api_key")

# Parameter Storeから値を取得して環境変数として設定
os.environ["SECRET_KEY"] = get_systems_manager_param("/zappa_RecipeApp/dev/AppSecret_key")
os.environ["GEMINI_API_KEY"] = get_systems_manager_param("/zappa_RecipeApp/dev/Gemini_api_key")

# Flask設定に環境変数を適用
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
S3_BUCKET = get_systems_manager_param("/zappa_RecipeApp/dev/s3_bucket")

# DynamoDB設定
DynamoDB_REGION = "ap-northeast-1"
DynamoDB_TABLE = "UserRecipe"
dynamodb = boto3.resource("dynamodb", region_name=DynamoDB_REGION)
table = dynamodb.Table(DynamoDB_TABLE)

# S3クライアントの初期化
S3_REGION = "ap-northeast-1"
s3 = boto3.client("s3")

# アップロードフォルダが存在しない場合は作成
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Flask-LoginManager初期設定
login_manager = LoginManager(app)


class User(UserMixin):
    def __init__(self, user_id, userName):
        self.id = user_id
        self.userName = userName


@login_manager.unauthorized_handler
def unauthorized():
    return redirect("dev/login")


@login_manager.user_loader
def load_user(user_id):
    response = table.get_item(Key={"userId": user_id, "SK": "PROFILE"})
    if "Item" in response:
        user_profile = response["Item"]
        userName = user_profile.get("userName", "NoName")
        return User(user_id, userName)
    return None


@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    # updated_at GSIによる降順並び変え
    sort_response = table.query(
        IndexName="userId-updated_at-index",
        KeyConditionExpression=Key("userId").eq(current_user.id)
        & Key("updated_at").begins_with("RECIPE#"),
        ScanIndexForward=False,
    )
    sort_recipes = sort_response["Items"]
    for sort_recipe in sort_recipes:
        sort_recipe["updated_at"] = convert_recipeDatetime_to_StrJstDatetime(
            sort_recipe["updated_at"]
        )
        # S3署名付きURLを発行
        sort_recipe["recipe_img_path"] = get_presigned_url(
            sort_recipe["recipe_img_path"]
        )
    noImage_pre_url = get_presigned_url("NoImage.png")
    print(f"noImage_pre_url : {noImage_pre_url}")
    return render_template(
        "index.html",
        enumerate=enumerate,
        sort_recipes=sort_recipes,
        noImage_pre_url=noImage_pre_url,
    )


def convert_recipeDatetime_to_StrJstDatetime(recipeDatetime):
    datetime_str = recipeDatetime.split("#")[1]
    dt_utc = datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)
    dt_jst = dt_utc.astimezone(timezone(timedelta(hours=9)))
    str_dt_jst = dt_jst.strftime("%Y-%m-%d %H:%M:%S")
    return str_dt_jst


def get_recipes_from_DynamoDB(user_id):
    response = table.query(
        KeyConditionExpression=Key("userId").eq(user_id)
        & Key("SK").begins_with("RECIPE#recipe")
    )
    recipes = response["Items"]
    return recipes


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        input_email = request.form["email"]
        input_password = request.form["password"]

        gsi_response = table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(input_email),
        )
        # ログイン認証
        if input_password == gsi_response["Items"][0]["password"]:
            username = gsi_response["Items"][0]["userName"]
            user_id = gsi_response["Items"][0]["userId"]
            user = User(user_id, username)
            login_user(user)
            return redirect(url_for("index"))
        else:
            return render_template(
                "login.html",
            )
    if request.method == "GET":
        return render_template(
            "login.html",
        )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        unique_id = uuid.uuid4()
        num_unique_userid = unique_id.int % (10**12)
        userId = "USER#user" + str(num_unique_userid)
        now_time = f"PROFILE#{datetime.now().isoformat()}"

        # メールアドレスの重複チェック
        gsi_response = table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(email),
        )
        if gsi_response["Count"] > 0:
            flash("このメールアドレスは既に登録されています。", "error")

        # パスワードの長さチェック（8文字以上）
        if len(password) < 8:
            flash("パスワードは8文字以上で入力してください。", "error")

        print("ERRORMSG")
        print([msg[0] for msg in get_flashed_messages(with_categories=True)])
        if "error" in [msg[0] for msg in get_flashed_messages(with_categories=True)]:
            return render_template("signup.html")

        table.put_item(
            Item={
                "userId": userId,
                "SK": "PROFILE",
                "userName": username,
                "password": password,
                "email": email,
                "created_at": now_time,
                "updated_at": now_time,
            }
        )
        return redirect(url_for("login"))
    if request.method == "GET":
        return render_template("signup.html")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def format_success_message(action: str):
    return Markup(f"""
    <div class="container mt-5">
        <div class="alert alert-success" role="alert">
            <h4 class="alert-heading">成功！</h4>
            <p>レシピの{action}が完了しました。</p>
            <hr>
            <p class="mb-0">
                <a href="{url_for('index')}" class="btn btn-primary">HOMEに戻る</a>
            </p>
        </div>
    </div>
    """)


@app.route("/add_recipe", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        try:
            # 画像アップロード
            file = request.files.get("file")
            s3_filename = upload_image_to_s3(file)
            # レシピデータ取得
            recipe_data = extract_recipe_data()
            # データ保存
            save_recipe_to_db(recipe_data, s3_filename)
            return format_success_message("追加")
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return render_template("add_recipe.html")
    return render_template("add_recipe.html")


def add_recipe_to_DynamoDB(
    title,
    recipe_id,
    ingredients,
    quantities,
    instructions,
    cook_time,
    memo,
    s3_filename,
):
    now_time = f"RECIPE#{datetime.now().isoformat()}"

    ingredient_quantity = [
        {"name": ingredient, "quantity": quantity}
        for ingredient, quantity in zip(ingredients, quantities)
    ]
    print(f"ingredient_quantity : {ingredient_quantity}")
    """
    ingredient_quantity = []
    for ingredient, quantity in zip(ingredients, quantities):
        ingredient_quantity.append({ingredient: quantity})
    """
    cook_time = convert_none_empty_to_null(cook_time)
    memo = convert_none_empty_to_null(memo)
    s3_filename = convert_none_empty_to_null(s3_filename)
    table.put_item(
        Item={
            "userId": current_user.id,
            "SK": recipe_id,
            "created_at": now_time,
            "updated_at": now_time,
            "title": title,
            "ingredient": ingredient_quantity,
            "step": instructions,
            "cook_time": cook_time,
            "memo": memo,
            "recipe_img_path": s3_filename,
        }
    )
    return None


def convert_none_empty_to_null(data):
    if data is None:
        return {"NULL": True}
    elif not data:
        return {"NULL": True}
    return data


def convert_null_to_empty(data):
    if data is {"NULL": True}:
        return ""
    return data


def add_recipeCounter(userId):
    """
    指定された userId に対応するレシピカウンターをインクリメントし、
    新しいレシピ ID を返す
    """
    counter_response = table.update_item(
        Key={"userId": userId, "SK": "counter"},
        UpdateExpression="SET recipe_counter = if_not_exists(recipe_counter, :start) + :inc",
        ExpressionAttributeValues={":start": 0, ":inc": 1},
        ReturnValues="UPDATED_NEW",
    )
    new_counter = counter_response.get("Attributes", {}).get("recipe_counter", 0)
    # レシピIDを作成
    new_recipe_id = f"RECIPE#recipe{int(new_counter)}"
    return new_recipe_id


@app.route("/recipe_detail/<string:recipe_id>")
@login_required
def recipe_detail(recipe_id):
    recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
    recipe["updated_at"] = convert_recipeDatetime_to_StrJstDatetime(
        recipe["updated_at"]
    )
    recipe_img_path = recipe.get("recipe_img_path")
    # S3署名付きURLを発行
    signed_url = get_presigned_url(recipe_img_path)
    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        enumerate=enumerate,
        signed_url=signed_url,
    )


def get_recipe_from_DynamoDB(user_id, recipe_id):
    db_response = table.get_item(
        Key={
            "userId": user_id,
            "SK": recipe_id,
        }
    )
    recipe = db_response["Item"]
    return recipe


def get_presigned_url(recipe_img_path):
    if recipe_img_path in (
        "",
        None,
        {"NULL": True},
    ):  # 空文字,None,DynamoDBのNULL値 いずれかの場合
        print("画像パスが存在しません。Noneを返します。")
        return None
    try:
        signed_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": recipe_img_path},
            ExpiresIn=3600,
        )
        return signed_url
    except Exception as e:
        print(f"{recipe_img_path}は署名付きURLの生成に失敗しました: {e}")
        return None


@app.route("/upgrade_recipe", methods=["GET", "POST"])
@login_required
def upgrade_recipe():
    if request.method == "GET":
        recipe_id = request.args.get("recipe_id")
        recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
        recipe_img_path = recipe.get("recipe_img_path")
        # S3署名付きURLを発行
        signed_url = get_presigned_url(recipe_img_path)
        return render_template(
            "upgrade_recipe.html",
            recipe=recipe,
            signed_url=signed_url,
        )
    if request.method == "POST":
        recipe_id = request.args.get("recipe_id")
        recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
        recipe_img_path = recipe.get("recipe_img_path")
        created_at = recipe["created_at"]
        # 　リクエスト値を取得
        title = request.form.get("title")
        cook_time = request.form.get("cook_time")
        memo = request.form.get("memo")
        # list型リクエスト値を取得
        ingredients = request.form.getlist("dynamic_ingredient")
        quantities = request.form.getlist("dynamic_quantity")
        instructions = request.form.getlist("dynamic_instruction")
        # S3の画像更新
        file = request.files.get("file")
        print(f"file : {file}")
        if file:
            print("file exit")
            if recipe_img_path != {"NULL": True}:
                s3.delete_object(Bucket=S3_BUCKET, Key=recipe_img_path)
            filename = secure_filename(file.filename)
            s3_filename = f"recipe/{current_user.id}/{filename}"
            print(f"s_filaname : {s3_filename}")
            s3.upload_fileobj(file, S3_BUCKET, s3_filename)
            recipe_img_path = s3_filename
        else:
            print("file not exit")
        add_recipe_to_DynamoDB(
            title,
            recipe_id,
            ingredients,
            quantities,
            instructions,
            cook_time,
            memo,
            recipe_img_path,
        )
        return redirect(url_for("index"))


@app.route("/delete_recipe")
@login_required
def delete_recipe():
    recipe_id = request.args.get("recipe_id")
    recipe = get_recipe_from_DynamoDB(current_user.id, recipe_id)
    recipe_img_path = recipe.get("recipe_img_path")
    # DynamoDBからレシピ削除
    table.delete_item(
        Key={
            "userId": current_user.id,
            "SK": recipe_id,
        }
    )
    # S3から画像削除
    if recipe_img_path not in (None, {"NULL": True}):
        s3.delete_object(Bucket=S3_BUCKET, Key=recipe_img_path)
    return format_success_message("削除")


def get_gemini_recipe(dish_name):
    """Gemini API からレシピ情報を JSON 形式で取得"""
    prompt = f"""
        {dish_name} のレシピを JSON 形式で日本語で出力してください。
        必ず以下のフォーマットに従ってください。
        出力には、前後にコードブロック (```json) を付けずに、直接 JSON 形式で出力してください。
        ```
        {{
        "材料": [
            {{"name": "玉ねぎ", "quantity": "大1個"}},
            {{"name": "にんじん", "quantity": "1本"}},
            {{"name": "トマト缶（カットトマト）", "quantity": "400g"}}
        ],
        "手順": [
            "玉ねぎをみじん切りにする。",
            "鍋に油をひき、玉ねぎを炒める。",
            "カレー粉を加えて香りを出す。"
        ],
        "調理時間": "40分",
        "調理ポイント": [
            "スパイスは焦がさないように弱火で炒める。",
            "トマトを加えると酸味が増して美味しくなる。"
        ],
        "何人前": "4人前"
        }}
        ```
        """

    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)

        if response and response.text:
            return json.loads(response.text)  # JSON -> dict に変換
        else:
            return {"error": "レシピの取得に失敗しました"}
    except json.JSONDecodeError:
        return {"error": "JSON の解析に失敗しました"}
    except Exception as e:
        return {"error": str(e)}


@app.route("/gemini_generate_recipe", methods=["GET", "POST"])
@login_required
def gemini_generate_recipe():
    if request.method == "POST":
        dish_name = request.form.get("title")
        # APIキーを設定
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        gemini_recipe = get_gemini_recipe(dish_name)
        print(gemini_recipe)
        # return render_template('gemini_add_recipe.html', dish_name=dish_name, gemini_recipe=gemini_recipe)
        session["dish_name"] = dish_name
        session["gemini_recipe"] = gemini_recipe
        return redirect(url_for("gemini_add_recipe"))
    return render_template("gemini_generate_recipe.html")


def upload_image_to_s3(file):
    """画像をS3にアップロードする"""
    if file:
        filename = secure_filename(file.filename)
        s3_filename = f"recipe/{current_user.id}/{filename}"
        try:
            s3.upload_fileobj(file, S3_BUCKET, s3_filename)
            return s3_filename
        except Exception as e:
            flash("画像のアップロードに失敗しました。")
            return None
    return None


def extract_recipe_data():
    """フォームからレシピデータを取得し、バリデーションを行う"""
    title = request.form.get("title")
    cook_time = request.form.get("cook_time")
    memo = request.form.get("memo")
    ingredients = request.form.getlist("dynamic_ingredient")
    quantities = request.form.getlist("dynamic_quantity")
    instructions = request.form.getlist("dynamic_instruction")
    return {
        "title": title,
        "cook_time": cook_time,
        "memo": memo,
        "ingredients": ingredients,
        "quantities": quantities,
        "instructions": instructions,
    }


def save_recipe_to_db(recipe_data, s3_filename):
    """レシピデータをDynamoDBに保存する"""
    recipe_id = add_recipeCounter(current_user.id)
    add_recipe_to_DynamoDB(
        recipe_data["title"],
        recipe_id,
        recipe_data["ingredients"],
        recipe_data["quantities"],
        recipe_data["instructions"],
        recipe_data["cook_time"],
        recipe_data["memo"],
        s3_filename,
    )


@app.route("/gemini_add_recipe", methods=["GET", "POST"])
@login_required
def gemini_add_recipe():
    if request.method == "POST":
        try:
            # 画像アップロード
            file = request.files.get("file")
            s3_filename = upload_image_to_s3(file)
            # レシピデータ取得
            recipe_data = extract_recipe_data()
            # データ保存
            save_recipe_to_db(recipe_data, s3_filename)
            return format_success_message("追加")
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return redirect(url_for("gemini_add_recipe"))

    # セッションからデータを取得
    dish_name = session.pop("dish_name", None)
    gemini_recipe = session.pop("gemini_recipe", None)
    return render_template(
        "gemini_add_recipe.html", dish_name=dish_name, gemini_recipe=gemini_recipe
    )
