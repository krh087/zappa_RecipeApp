
# レシピアプリ

このアプリは、ユーザーが自分のレシピを登録、編集できるシンプルなレシピ管理ツールです。

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
| インフラ         | AWS (lambda, APIGateway, S3, DynamoDB, SSM)   |

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

画像貼り付け(draw.io)


## DynamoDB の構成

このプロジェクトでは、シングルテーブルデザイン を採用した AWS DynamoDB を使用してデータを管理しています。以下にDynamoDBのテーブル構成を説明します。

### 1. テーブル構成

| テーブル名  | パーティションキー (PK) | ソートキー (SK) | データの種類 | 説明 |
|------------|------------------|--------------------|-------------|------|
| `UserRecipe` | `user#<user_id>` | `PROFILE`          | ユーザープロフィール | ユーザー情報（名前、メール、パスワード）を格納 |
| `UserRecipe` | `user#<user_id>` | `RECIPE#<recipe_id>` | レシピ情報 | ユーザーが投稿したレシピ情報（料理名、手順、分量、画像パス等）を格納 |
| `UserRecipe` | `user#<user_id>` | `Counter`          | レシピカウント | ユーザーの投稿レシピ数を記録 (<recipe_id>のオートインクリメント用途) |



### 2. グローバルセカンダリインデックス (GSI)
一部の検索を高速化するために、以下のGSIを設定しています。

| GSI名           | パーティションキー (GSI PK) | ソートキー (GSI SK) | 用途 |
|---------------|-------------------|-----------------|------|
| UserEmailIndex | `email` (string)  | -               | メールアドレスでユーザーを検索 |
| UserEmailIndex | `email` (string)  | -               | メールアドレスでユーザーを検索 |


### 3. データの例
#### Users テーブルのサンプルデータ
```json
{
  "user_id": "12345",
  "name": "John Doe",
  "email": "john@example.com"
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


## スクリーンショット
- トップ画面  
![トップ画面](path/to/image)

- レシピ詳細画面  
![レシピ詳細](path/to/image)

## 今後の予定
- メール送信(SES,EventBridge) : ユーザーが設定した時間にプッシュ通知(献立などに)
- S3FullAccess →  「必要最小限の権限」IAMロールに変更(インラインポリシー作成)
- カテゴリー（例：和食、洋食、デザートなど）を追加 +ナビゲーションバーにカテゴリーを追加し、カテゴリーで検索
- レシピ個人的評価(Rating: 1.0 ~ 5.0, 0.1毎) : おいしさ、作りやすさ、食材の集めやすさなど
---


