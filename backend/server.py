import json
from pathlib import Path
import logging
from threading import Thread
import shutil
import os
from flask import Flask, Response, request, send_file, send_from_directory, render_template, abort, redirect, url_for
from flask_cors import CORS
import datetime
import random
import hashlib

############## Basic Operation Function ###############

def HashPass(Password):
	return hashlib.sha256(str(Password).encode()).hexdigest()
def UserAuth(Username,Password,Hash=True):
	with open('Login.json', 'r') as file:
		Login = json.load(file)
	try:
		if Hash:
			Password=HashPass(Password)
		if Login[Username][0]==Password:
			return 'Success'
		else:
			return 'Wrong Password'
	except KeyError:
		return 'User Not Found'
def AddUser(Username,Password):
	with open('UserDatabase.json', 'r') as file:
		UserDatabase = json.load(file)
	UserDatabase.update({Username:HashPass(Password)})
	with open('UserDatabase.json', 'w') as outfile:
		json.dump(UserDatabase, outfile)
	os.makedirs('Users/{}'.format(Username),exist_ok=True)

def CookieCheck():
	Username = request.cookies.get('Username')
	Password = request.cookies.get('Password')
	if UserAuth(Username,Password,False)=='Success':
		return True
	elif UserAuth(Username,Password)=='Wrong Password':
		return False
	elif UserAuth(Username,Password)=='User Not Found':
		return False




logging.basicConfig(filename='access.log', level=logging.INFO)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
# app.secret_key = b'swim4love'
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

##################### Initialize stored variables #####################
with open('Stock.json', 'r') as file:
	stock = json.load(file)
last_stock_id = max(item.id for item in stock)

##################### Request handling #####################
@app.route('/')
def root():
	if request.method=='GET':
		return redirect(url_for('Login'))
	else:
		return abort(404)

@app.route('/Register',methods=['GET', 'POST'])
def Register():
	if request.method == 'POST':
		Username=request.form['Username']
		Password=request.form['Password']
		AddUser(Username,Password)
		return redirect(url_for('Operation_Result',Result='{} User Register Success'.format(Username),Detail='{} Have Been Added To The User Database!'.format(Username),NextPage=url_for('Dashboard').strip('/')))
	if request.method == 'GET':
		return render_template('Register.html')

@app.route('/Login',methods=['GET', 'POST'])
def Login():
	if request.method == 'POST':
		Username=request.form['Username']
		Password=request.form['Password']
		if UserAuth(Username,Password)=='Success':
			expire_date = datetime.datetime.now()+datetime.timedelta(days=7)
			respond = make_response(redirect(url_for('Dashboard')))
			respond.set_cookie('Username',Username, expires=expire_date)
			respond.set_cookie('Password',HashPass(Password), expires=expire_date)
			return respond
		elif UserAuth(Username,Password)=='Wrong Password':
			return redirect(url_for('Operation_Result',Result='Username or Password Incorrect',Detail='Please Check Your Username and Password and Login Again!',NextPage=url_for('Login').strip('/')))

			# return redirect(url_for('Login'))
		elif UserAuth(Username,Password)=='User Not Found':
			return redirect(url_for('Operation_Result',Result='User Not Found',Detail='Please Check Your Username Login Again!',NextPage=url_for('Login').strip('/')))
	elif request.method == 'GET':
		if CookieCheck():
			return redirect(url_for('Dashboard'))
		else:
			return render_template('Login.html')
		return render_template('Login.html')

@app.route('/Dashboard',methods=['GET'])
def Dashboard():
	if CookieCheck():
		if request.method == 'GET':
			return render_template('Dashboard.html')
		else:
			abort(404)


@app.route('/Operation_<Result>_<Detail>_<NextPage>',methods=['GET'])
def Operation_Result(Result,Detail,NextPage):
	NextPage='/{}'.format(NextPage)
	return render_template('Operation_Result.html',Result=Result,Detail=Detail,NextPage=NextPage)

@app.route('/Images/Product/<pid>')
def Product_Image(pid):
	if CookieCheck():
		try:
			ProductImageDir='/Images/Product/{}.jpg'.format(pid)
			return send_file(ProductImageDir)
		except:
			return abort(404)
	else:
		reutrn abort(403)


@app.route('/services/new-stock', methods=['POST','GET'])
def new_stock():
	if CookieCheck():
		if request.method == 'POST':
			# Get post data
			name = request.form.get('name')
			description = request.form.get('description')
			category = request.form.get('category')
			tags = request.form.getlist('tags')
			uid = request.form.get('uid')
			deadline = request.form.get('deadline')
			rent = request.form.get('rent')
			pid = str(datetime.datetime.now()).replace(' ','').replace('.','').replace(':','').replace('-','')+str(random.randint(0,10000)).zfill(5)
			status='available'
			Product_Image = request.files['Product_Image']
			Product_Image_Save_Directory='/Images/Product/'
			Product_Image_Name='{}.jpg'.format(pid)
			if all(map(lambda x: x != None, [name, desc, category, tags, uid, deadline, rent])):
				return resp({'ret': 0, 'msg': 'fuck you, give me correct params'})
			else:
				Product_Image.save(os.path.join(Product_Image_Save_Directory, Product_Image_Name))
				stock.append({
							'name': name,
							'description':description,
							'category': category,
							'tags':[tags],
							'uid':uid,
							'deadline':deadline,
							'rent':rent,
							'pid':pid
							'status':status
							})
				with open('Stock.json', 'w') as outfile:
						json.dump(stock, outfile)
				return redirect(url_for('Operation_Result',Result='Product Added',Detail='Your Product Has Been Added.',NextPage=url_for('Dashboard').strip('/')))
		elif request.method=='GET':
			return render_template(PlaceHolder)
	else:
		return abort(403)





