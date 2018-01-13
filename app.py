import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import requests
import geocoder
from werkzeug import secure_filename
import os, base64
import time
import operator

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'csisfun'

'''Connect mysql database to app'''
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'admin'
app.config['MYSQL_DATABASE_DB'] = 'coordinates'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	try:
		user.is_authenticated = request.form['password'] == pwd
		return use
	except:
		pass

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('index.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		cursor.execute("INSERT INTO Users (email, firstname, lastname, password) VALUES ('{0}', '{1}', '{2}', '{3}')".format(email, firstname, lastname, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('index.html', name=email, message='Account Created!')
	else:
		print ("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def get_user_name(email):
	cursor = conn.cursor()
	cursor.execute("SELECT firstname FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

@app.route('/maps')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	name = get_user_name(flask_login.current_user.id)
	coordinates = leafify(flask_login.current_user.id)
	return render_template('maps.html', name=name, message="Here's your profile", user=uid, coordinates=coordinates)

@app.route('/addLocation')
@flask_login.login_required
def add_location():
	email = flask_login.current_user.id
	name = get_user_name(email)
	return render_template("addtomap.html", name=name,email=email)

@app.route('/add_a_location', methods=['POST'])
@flask_login.login_required
def add_a_location():
	locationname = request.form.get('locationname')
	address = request.form.get('house_num')
	street = request.form.get('street')
	city = request.form.get('city')
	zipcode = request.form.get('zipcode')
	user = flask_login.current_user.id
	cursor = conn.cursor()
	cursor.execute("INSERT INTO locations (user, locationname, city, street, house_num, zipcode) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}')".format(user, locationname,city,street,address,zipcode))
	conn.commit()
	return redirect(url_for('protected'))

'''Gather location data from the database for the specific user and return the coordinates.
	What I use here is geocoder library for python found here: http://geocoder.readthedocs.io/api.html#install
'''
def leafify(email):
	email = email
	cursor = conn.cursor()
	cursor.execute("SELECT locationname, city, street, house_num, zipcode FROM locations WHERE user = '{0}'".format(email))
	location = cursor.fetchall()
	coordinates_array = []
	for i in location:
		#im not sure if its necessary to initialize but it does not hurt to do so just to be safe.
		string = ''
		string = str([i[3]]) + ',' + str(i[2]) + ',' + str(i[1])
		g = geocoder.google(string)
		coordinates_array.append(g.latlng)
	return coordinates_array
	
'''This is the home page. When the application is called via command line, this function is called'''
@app.route("/")
def hello():
	return render_template('index.html')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)