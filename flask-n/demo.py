'''
Description: 
email: 359066432@qq.com
Author: lhj
software: vscode
Date: 2021-10-27 09:50:18
platform: windows 10
LastEditors: lhj
LastEditTime: 2021-10-27 17:51:16
'''
from flask import Flask

app = Flask(__name__)

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'User {username}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return f'Post {post_id}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return f'Subpath {subpath}'