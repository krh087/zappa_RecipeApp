# zappa_RecipeApp

# レシピアプリ

このアプリは、ユーザーが自分のレシピを登録、編集、検索、共有できるシンプルなレシピ管理ツールです。

## 主な機能
- **レシピ登録**: レシピ名、写真、使う食材、調理工程を入力して保存。
- **レシピ検索**: 食材名やキーワードで簡単に検索。
- **他ユーザーのレシピ閲覧**: 他のユーザーが登録したレシピを参照可能。
- **プロフィール編集**: ユーザー情報の更新機能。

## 使用技術
| カテゴリー       | 使用技術                       |
|------------------|--------------------------------|
| フロントエンド   | HTML, CSS, JavaScript          |
| バックエンド     | Ruby on Rails                  |
| データベース     | MySQL                          |
| インフラ         | AWS (EC2, RDS, S3, Route53)   |

## ディレクトリ構成
<pre>
├── app
│ ├── models
│ ├── views
│ └── controllers
├── config
├── db
└── public
</pre>


## セットアップ手順
1. リポジトリをクローンします。

git clone https://github.com/username/recipe-app.git

text
2. 必要なGemをインストールします。

bundle install

text
3. データベースをセットアップします。

rails db:create db:migrate db:seed

text
4. サーバーを起動します。

rails server

text

## スクリーンショット
- トップ画面  
![トップ画面](path/to/image)

- レシピ詳細画面  
![レシピ詳細](path/to/image)

## 今後の予定
- レシピのお気に入り機能追加。
- コメント機能の実装。

---

