from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    my_dict = {
        'insert_something1': 'views.pyのinsert_something1部分です。',
        'insert_something2': 'views.pyのinsert_something2部分です。',
        'test_titles': ['title1', 'title2', 'title3']
    }
    return render_template('index.html', my_dict=my_dict)
