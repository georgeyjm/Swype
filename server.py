import json
from pathlib import Path
import logging
import os
from flask import Flask, Response, request, send_file, send_from_directory, render_template, abort, redirect, url_for, jsonify
from flask_cors import CORS
import random
import hashlib
import time
import requests


############## Basic Operation Function ###############

def box(action):
    global BOX_URL
    requests.get('{}/{}'.format(BOX_URL, action))

def hash(string):
    return hashlib.sha256(str(string).encode()).hexdigest()

def gen_pid():
    ts = time.time()
    return str(ts).replace('.', '')

def save_database(data, db_name):
    json.dump(data, (DB_ROOT / db_name).open('w', encoding='utf-8'), indent=4)

def read_database(db_name):
    global DB_ROOT
    data = json.load((DB_ROOT / db_name).open(encoding='utf-8'))
    return data

def calc_rating(pid):
    # Compute the harmonic mean of the number of likes and dislikes
    a = max(1, stock[pid]['likes'])
    b = max(1, stock[pid]['dislikes'])
    r = 2 * a * b / (a + b)
    m = min(a, b)
    # Map the value to the range [0, 5]
    stock[pid]['rating'] = 5 * (r - m) / m

def filter_stock(**kwargs):
    filtered = [item for item in stock]
    # Specific categories
    restriction = kwargs.get('category')
    if restriction:
        restriction = [restriction] if isinstance(restriction, str) else restriction
        filtered = list(filter(lambda i: i['category'] in restriction))
    # Specific rating ranges
    # restriction = kwargs.get('rating_ub')
    # if restriction:
    #     restriction = [restriction] if isinstance(restriction, str) else restriction
    #     for item in stock:
    #         if item['category'] in restriction:
    #             filtered.append(item)


################### FLASK SETUP ###################
# logging.basicConfig(filename='access.log', level=logging.INFO)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='static')

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)
stock = {}
##################### Initialize stored variables #####################

BOX_URL = 'http://10.20.193.206:8000'
DB_ROOT = Path('.')
USERS_DB = 'users.json'
STOCK_DB = 'stock.json'
UPLOAD_DIR = 'uploads'

users = read_database(USERS_DB)
stock = read_database(STOCK_DB)


##################### Request handling #####################

@app.route('/register', methods=['POST'])
def user_register():
    request.form = json.loads(request.get_data().decode('utf-8'))
    username = request.form.get('username')
    password = request.form.get('password')

    users[username] = {'username':username, 'hpwd': hash(password), 'favs': []}
    save_database(users, USERS_DB)
    return jsonify({'ret': 0, 'msg': 'Success'})


@app.route('/login', methods=['POST'])
def user_login():
    request.form = json.loads(request.get_data().decode('utf-8'))
    username = request.form.get('username')
    password = request.form.get('password')
    hpwd = hash(password)

    if username not in users.keys() or users[username]['hpwd'] != hpwd:
        return jsonify({'ret': 1, 'msg': 'Login authentication failed'})
    return jsonify({'ret': 0, 'msg': 'Success'})


@app.route('/user/info/<username>', methods=['GET', 'POST'])
def get_user_info(username):
    if username not in users.keys():
        return jsonify({'ret': 3, 'msg': 'Cannot find user'})
    return jsonify({'ret': 0, 'msg': 'Success', 'data': users[username]})


@app.route('/item/image/<pid>', methods=['GET', 'POST'])
def get_item_image(pid):
    if pid not in stock.keys():
        return jsonify({'ret': 2, 'msg': 'Cannot find stock item'})
    return send_file('{}/{}.jpg'.format(UPLOAD_DIR, pid))


@app.route('/item/new', methods=['POST'])
def new_item():
    request.form = json.loads(request.get_data().decode('utf-8'))
    # Get attributes
    pid = gen_pid()
    name = request.form.get('name')
    description = request.form.get('description')
    category = request.form.get('category')
    rent = float(request.form.get('rent'))
    username = request.form.get('username')
    img = request.files.get('img')
    status = 'available'
    borrower = ''
    likes = 0
    dislikes = 0
    rating = 1 # maybe change this?

    # Save item
    img.save('{}/{}.jpg'.format(UPLOAD_DIR, pid))
    stock[pid] = {
        'pid': pid,
        'name': name,
        'description': description,
        'category': category,
        'rent': rent,
        'username': username,
        'status': status,
        'borrower': borrower,
        'likes': likes,
        'dislikes': dislikes,
        'rating': rating
    }
    save_database(stock, STOCK_DB)
    box('close')
    return jsonify({'ret': 0, 'msg': 'Success', 'data': stock[pid]})


@app.route('/item/action', methods=['POST'])
def item_action():
    request.form = json.loads(request.get_data().decode('utf-8'))
    pid = request.form.get('pid')
    action = request.form.get('action')
    username = request.form.get('username')

    # Validate item and user
    if pid not in stock.keys():
        return jsonify({'ret': 2, 'msg': 'Cannot find stock item'})
    if username not in users.keys():
        return jsonify({'ret': 3, 'msg': 'Cannot find user'})

    # Process action
    if action == 'like':
        stock[pid]['likes'] += 1
        calc_rating(pid)
    elif action == 'dislike':
        stock[pid]['dislikes'] += 1
        calc_rating(pid)
    elif action == 'fav':
        if stock[pid]['status'] != 'available':
            return jsonify({'ret': 5, 'msg': 'Stock item unavailable'})
        stock[pid].update(status='borrowed', borrower=username)
        users[username]['favs'].append(pid)
        save_database(users, USERS_DB)
    elif action == 'take':
        if stock[pid]['borrower'] != username:
            return jsonify({'ret': 6, 'msg': 'No permission to perform action on this item'})
        box('open')
        users[username]['favs'].remove(pid)
        save_database(users, USERS_DB)
    elif action == 'ret':
        if stock[pid]['borrower'] != username:
            return jsonify({'ret': 6, 'msg': 'No permission to perform action on this item'})
        box('close')
        stock[pid].update(status='available', borrower='')
    else:
        return jsonify({'ret': 4, 'msg': 'Invalid action'})

    save_database(stock, STOCK_DB)
    return jsonify({'ret': 0, 'msg': 'Success'})


@app.route('/item/info/<pid>', methods=['GET', 'POST'])
def get_item_info(pid):
    if pid not in stock.keys():
        return jsonify({'ret': 2, 'msg': 'Cannot find stock item'})
    return jsonify({'ret': 0, 'msg': 'Success', 'data': stock[pid]})


# @app.route('/Search/<keys>/<terms>')
# def product_search(keys, terms):
#     try:
#         result = {}
#         for product in stock:
#             if stock[product][keys] == terms:
#                 result.update({product: stock[product]})
#         return jsonify(result)
#     except:
#         abort(404)


@app.route('/feed', methods=['GET', 'POST'])
def feed():
    pid = random.choice(list(stock.keys()))
    while stock[pid]['status'] == 'borrowed':
        pid = random.choice(list(stock.keys()))
    return get_item_info(pid)

@app.route('/feed/<category>', methods=['GET', 'POST'])
def feed_categ(category):
    chosen = filter_stock(category=category)
    max_ = sum(i['rating'] for i in chosen.values())
    pick = random.uniform(0, max_)
    current = 0
    for pid, value in chosen.items():
        current += value['rating']
        if current > pick:
            return pid
    while chosen[pid]['status'] == 'borrowed':
        pid = random.choice(list(chosen.keys()))
    return get_item_info(pid)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000', threaded=True)
