# zappa_RecipeApp

# レシピアプリ

このアプリは、ユーザーが自分のレシピを登録、編集できるシンプルなレシピ管理ツールです。

## 主な機能
- **レシピ登録**: レシピ名、写真、食材、調理工程を入力して保存。
- **他ユーザーのレシピ編集**: 自分の登録したレシピを追加、閲覧、更新、削除可能。
- **レシピの自動生成**: レシピ名を入力することで、Google Geminiがレシピを自動生成。

## 使用技術
| カテゴリー       | 使用技術                       |
|------------------|--------------------------------|
| フロントエンド   | HTML, CSS, JavaScript          |
| バックエンド     | flask, zappa, boto3, GeminiAPI,|
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
│ └──addInoutField.js
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
| `UserRecipe` | `user#<user_id>` | `RECIPE#<recipe_id>` | レシピ情報 | ユーザーが投稿したレシピ情報（料理名、手順、分量、画像パス） |
| `UserRecipe` | `user#<user_id>` | `Counter`          | レシピカウント | ユーザーの投稿レシピ数を記録 |



### 2. グローバルセカンダリインデックス (GSI)
一部の検索を高速化するために、以下のGSIを設定しています。

| GSI名           | パーティションキー (GSI PK) | ソートキー (GSI SK) | 用途 |
|---------------|-------------------|-----------------|------|
| UserEmailIndex | `email` (string)  | -               | メールアドレスでユーザーを検索 |
| UserEmailIndex | `email` (string)  | -               | メールアドレスでユーザーを検索 |

### 3. アクセス方法
- `boto3` を使用してPython（Flask API）からデータを操作。
- API Gateway + Lambda を経由してクライアントからデータ取得。
- DynamoDB SDK を利用して直接データを取得可能。

### 4. データの例
#### Users テーブルのサンプルデータ
```json
{
  "user_id": "12345",
  "name": "John Doe",
  "email": "john@example.com"
}


## スクリーンショット
- トップ画面  
![トップ画面](path/to/image)

- レシピ詳細画面  
![レシピ詳細](path/to/image)

## 今後の予定
- レシピのお気に入り機能追加。
- コメント機能の実装。

---

