
# レシピアプリ

このアプリは、ユーザーが自分のレシピを登録、編集できるシンプルなレシピ管理ツールです。
https://a6w2pqm0il.execute-api.ap-northeast-1.amazonaws.com/dev

## 主な機能
- **レシピ登録**: レシピ名、写真、食材、調理工程を入力して保存。
- **レシピ編集**: 自分の登録したレシピを追加、閲覧、更新、削除可能。
- **ユーザー認証**: メールとパスワードを用いてユーザー認証。
- **レシピ自動生成**: レシピ名を入力することで、Google Geminiがレシピを自動生成。

## 使用技術
| カテゴリー       | 使用技術                       |
|------------------|--------------------------------|
| フロントエンド   | HTML, CSS, JavaScript, bootstrap5 |
| バックエンド     | flask (python), zappa, boto3, GeminiAPI,|
| インフラ         | AWS (lambda, APIGateway, S3, DynamoDB, SSM Paramater Store)   |

## ディレクトリ構成
<pre>
zappa_RecipeApp
├──app.py
├──templates
│ ├──login.html
│ ├──signup.html
│ ├──index.html
│ ├──add_recipe.html
│ ├──recipe_detail.html
│ ├──upgrade_recipe.html
│ ├──gemini_generate_recipe.html
│ └──gemini_add_recipe.html
│──static
│ └──addInputField.js
├──config.py
├──venv
├──requirements.txt
└──zappa_settings.json
</pre>


## AWSインフラ構成

![Image](https://github.com/user-attachments/assets/9f3aad72-0872-4130-bb53-cc86c46bf2a4)


## DynamoDB の構成

このプロジェクトでは、シングルテーブルデザイン を採用した AWS DynamoDB を使用してデータを管理しています。以下にDynamoDBのテーブル構成を説明します。

### 1. テーブル構成

| テーブル名  | パーティションキー (PK) | ソートキー (SK) | データの種類 | 説明 |
|------------|------------------|--------------------|-------------|------|
| `UserRecipe` | `user#<user_id>` | `PROFILE`          | ユーザープロフィール | ユーザー情報（名前、メール、パスワード）を格納 |
| `UserRecipe` | `user#<user_id>` | `RECIPE#<recipe_id>` | レシピ情報 | ユーザーが投稿したレシピ情報（料理名、手順、分量、画像パス等）を格納 |
| `UserRecipe` | `user#<user_id>` | `Counter`          | レシピカウント | ユーザーの投稿レシピ数を記録 (<recipe_id>のオートインクリメント用途) |



### 2. グローバルセカンダリインデックス (GSI)
PK,SK以外で検索を可能にするために、以下のGSIを設定しています。

| GSI名           | パーティションキー (GSI PK) | ソートキー (GSI SK) | 用途 |
|---------------|-------------------|-----------------|------|
| email-index | `email` (string)  | -             | メールアドレスでユーザー認証 |
| userId-updated_at-index | `userId` (string)  | `updated_at` (string)  | レシピ更新順に並び変え |


### 3. データの例
#### UserRecipe テーブルのサンプルデータ
```json
SK=PROFILE
{
  "userId": "USER#user244959578138",
  "SK": "PROFILE",
  "userName": "John",
  "email": "john@example.com",
  "pass": "expass",
  "created_at": "PROFILE#2025-02-28T03:43:22.118225",
  "updated_at": "PROFILE#2025-02-28T03:43:22.118225",
}
```
```json
SK=RECIPE#<recipe_id>
{
  "userId": "USER#user244959578138",
  "SK": "RECIPE#recipe11",
  "recipe_img_path": "recipe/USER#user244959578138/hamburgersteak.png",
  "title": "ハンバーグ（2人分）",
  "ingredient": '[{"name":"ミートミンチ", "quantity":"170g"},{"name":"玉ねぎ ","quantity":"1／2個"}]',
  "step": '[ "冷凍のソミートを自然解凍" , "玉ねぎをみじん切りし、油をひいたフライパンで炒める" ]',
  "cook_time":"20分",
  "memo": "玉ねぎを飴色になるまで炒める",
  "created_at": "RECIPE#2025-02-28T03:43:22.118225",
  "updated_at": "RECIPE#2025-02-28T03:43:22.118225",
}
```
```json
SK=Counter
{
  "userId": "USER#user244959578138",
  "SK": "counter",
  "recipe_counter": 13,
}
```

## AWS SystemsManager Parameter Store
### パラメータストアの構成
- /zappa_RecipeApp/dev/AppSecret_key
- /zappa_RecipeApp/dev/Gemini_api_key

### lambda パラメータストアアクセス用ポリシー
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"ssm:GetParameter",
				"ssm:GetParameters",
				"ssm:GetParametersByPath"
			],
			"Resource": "arn:aws:ssm:{YOUR_REGION}:{YOUR_ACCOUNT_ID}:parameter/zappa_RecipeApp/dev/*"
		},
		{
			"Effect": "Allow",
			"Action": "kms:Decrypt",
			"Resource": "arn:aws:kms:{YOUR_REGION}:{YOUR_ACCOUNT_ID}:key/{YOUR_KMS_KEY_ID}"
		}
	]
}
```
## S3の構成
 ### 許可する拡張子
{'png', 'jpg', 'jpeg', 'gif'}
<pre>
/
├──Noimage.png
├──recipe
│  └──userId
│  		├──hamburgersteak.png.png
│  		└──pasta.jpeg
│ └──userId
│     ├──
│  	...
</pre>

## Gemini API
### レシピ生成関数
```
def get_gemini_recipe(dish_name):
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
 
model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content(prompt)
```
## 画面イメージ
### ログイン画面
![Image](https://github.com/user-attachments/assets/0cf1b171-978e-4d7a-8295-3241d3328c5c)

### アカウント作成画面
![Image](https://github.com/user-attachments/assets/aa6ca4b3-a45e-48b4-8932-784e2275ffde)

### ホーム画面 
![Image](https://github.com/user-attachments/assets/b1325a3f-c143-4906-812e-3eb211c145cf)

### レシピ追加画面
![Image](https://github.com/user-attachments/assets/f9761535-ff55-4382-a4fd-cb120e4dbafc)

### レシピ詳細画面
![Image](https://github.com/user-attachments/assets/c36af4bf-a0ec-4807-bd97-b7fc0cb6e738)

### レシピ編集画面
![Image](https://github.com/user-attachments/assets/7974d58a-c0c8-4c19-841f-902373ed315e)

### レシピ自動生成画面
![Image](https://github.com/user-attachments/assets/328d6210-ee19-4197-a538-bdead36320c6)

### 自動生成レシピの登録画面
![Image](https://github.com/user-attachments/assets/66815747-4061-4270-807b-e1ee59021505)


## 今後の予定
- メール送信(SES,EventBridge) : ユーザーが設定した時間にプッシュ通知(献立などに)
- S3FullAccess →  「必要最小限の権限」IAMロールに変更(インラインポリシー作成)
- カテゴリー（例：和食、洋食、デザートなど）を追加 +ナビゲーションバーにカテゴリーを追加し、カテゴリーで検索
- レシピ個人的評価(Rating: 1.0 ~ 5.0, 0.1毎) : おいしさ、作りやすさ、食材の集めやすさなど
---


