import json
from pathlib import Path
import logging
from threading import Thread
import shutil
import os
from flask import Flask, Response, request, send_file, send_from_directory, render_template, abort
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit

logging.basicConfig(filename='access.log', level=logging.INFO)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
# app.secret_key = b'swim4love'
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

##################### Initialize stored variables #####################

stock = json.load('')
last_stock_id = max(item.id for item in stock)

##################### Request handling #####################

@app.route('/services/new-stock', methods=['POST'])
def new_stock():
    # Get post data
    name = request.form.get('name')
    desc = request.form.get('desc')
    category = request.form.get('category')
    tags = request.form.get('tags')
    uid = request.form.get('uid')
    deadline = request.form.get('deadline')
    rent = request.form.get('rent')

    if all(map(lambda x: x != None, [name, desc, category, tags, uid, deadline, rent])):
        return resp({'ret': 0, 'msg': 'fuck you, give me correct params'})

    stock.append({'name': name,
                  'desc'
                 })
