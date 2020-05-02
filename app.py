from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mail import Mail,Message
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import os
from urllib.request import urlopen 
import urllib
import shutil
from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_uploads import UploadSet, configure_uploads, IMAGES
import timeit
import datetime
from flask_mail import Mail, Message
import os
from wtforms.fields.html5 import EmailField
import urllib.request
import time
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
from urllib.request import urlopen

app=Flask(__name__)


app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='my_music'
app.config['MYSQL_CURSORCLASS']='DictCursor'

app.config.from_pyfile('config.cfg')
mail=Mail(app)

s=URLSafeTimedSerializer('secret123')

mysql=MySQL(app)


@app.route('/')
def index():
	return render_template('index.html')
@app.route('/Artists')
def artists():
	return render_template("artists.html")
@app.route('/Albums')
def albums():
	return render_template("album.html")


class RegisterForm(Form):
	name=StringField('Name',[validators.Length(min=1,max=50)])
	username=StringField('Username',[validators.Length(min=4,max=25)])
	email=StringField('Email',[validators.Length(min=6,max=50)])
	password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='Password do not match')])
	confirm=PasswordField('confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
	form =RegisterForm(request.form)
	if request.method=='POST' and form.validate():
		name=form.name.data
		email=form.email.data
		username=form.username.data
		password=sha256_crypt.encrypt(str(form.password.data))
		
		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM users WHERE username= %s",[username])
		result2=cur.execute("SELECT * FROM users WHERE email=%s",[email])
		if result>0:
			error='User name already exists,please try another user name'
			return render_template('register.html',form=form,error=error)
		if result2>0:
			error='Email already exists,please try another Email'
			return render_template('register.html',form=form,error=error)
		else:
			cur=mysql.connection.cursor()
			cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
			mysql.connection.commit()
			cur.close()
			flash('Successfully verified','success')



			
		return redirect(url_for('index'))

	return render_template('register.html',form=form)



#login
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='POST':
		username=request.form['username']

		password_candidate=request.form['password']

		cur=mysql.connection.cursor()

		result=cur.execute("SELECT * FROM users WHERE username= %s",[username])

		if result>0:
			data=cur.fetchone()
			password=data['password']	

			if sha256_crypt.verify(password_candidate,password):
				session['logged_in']=True
				session['username']=username
				session['id']=data['id']

				flash('login successful','success')
				return redirect(url_for('dashboard'))
			else:
				error='wrong password'
			return render_template('login.html',error=error)
			cur.close()
		else:
			error='Username not found'
			return render_template('login.html',error=error)

	return render_template('login.html')

#to prevent using of app without login
def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('unauthorised,please login','danger')
			return redirect(url_for('login'))
	return wrap

#logout
@app.route('/logout')
def logout():
	session.clear()
	flash('you are now logout','success')
	return redirect(url_for('login'))

#search
@app.route('/new',methods=['POST'])
def new():
	string=""
	co=request.form['give']
	song=co
	song_name=co+'.mp3'
	cur=mysql.connection.cursor()
	result=cur.execute("SELECT * FROM songs_list WHERE song_name=%s",[song_name])
	albu69=cur.fetchall()
	if result>0:
		return render_template('search.html',albu=albu69)
	else:
		try:
			page = requests.get("https://www.youtube.com/results?search_query="+song)
			soup = BeautifulSoup(page.text,'html.parser')
			
			# source = urllib.request.urlopen(page).read()
			# body = BeautifulSoup(source,'html.parser').body
			# heading=body.find('img',class_="style-scope yt-img-shadow")
			
			# print("hhhhhhhh")

			# print(heading)
			# print(heading.get('src'))
			# print("hhhhhhh")
			#imgs=imgh.get('img')

			for div in soup.find_all('div', { "class" : "yt-lockup-video" }):
				if div.get("data-context-item-id") != None:
					video_id = div.get("data-context-item-id")
					break
			os.system('youtube-dl --extract-audio --audio-format mp3 -o "vijaycse.mp3" https://www.youtube.com/watch?v='+video_id)
			os.system("move *.mp3 ./static/music/")
			# shutil.copyfile("static/music/vijaycse17031.mp3","static/music/akhil1.mp3")
			os.rename("static/music/vijaycse.mp3","static/music/"+song_name)

			string="/static/music/"+song_name
			cur=mysql.connection.cursor()
			cur.execute("INSERT INTO songs_list(path,album,song_name) VALUES (%s,%s,%s)",(string,"NA",song_name))
			mysql.connection.commit()
			result=cur.execute("SELECT * FROM songs_list WHERE song_name=%s",[song_name])
			albu99=cur.fetchall()
			return render_template('search.html',albu=albu99)
		except NameError:
			flash('Song Not Found','success')
			return render_template('dashboard.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
	cur=mysql.connection.cursor()

	result=cur.execute("SELECT * from songs_list ")

	songs=cur.fetchall()

	if result>0:
		return render_template('dashboard.html',songs=songs)
	else:
		msg="NO PLAYLIST FOUND "

	return render_template('dashboard.html',msg=msg)
	cur.close()




@app.route('/connect')
def connect():
	return render_template('connect.html')




# _____________________________Youtube_____________________________

def findLink(songName):
    query = songName
    query = query.replace(' ', '+')
    app.logger.info('query ' + query)
    # search for the best similar matching video
    url = 'https://www.youtube.com/results?search_query=' + query
    source_code = requests.get(url,timeout=15)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "html.parser")

    # fetches the url of the video
    songs = soup.findAll('div', {'class': 'yt-lockup-video'})
    song = songs[0].contents[0].contents[0].contents[0]
    link = song['href']
    app.logger.info('Link ' + link)
    url = 'https://www.youtube.com'+link
    source = urllib.request.urlopen(url).read()
    body = BeautifulSoup(source,'html.parser').body
   # print(body)
    heading=body.find('div',class_="html5-video-container")
    # print(heading)
    # viii=heading.text
    #print(heading.text)
    source_code = requests.get(url, timeout=15)
    plain_text = source_code.text
    soup2 = BeautifulSoup(plain_text,'html.parser')
    scriptTag = soup2.find("meta", {"property": "og:video:url"})
    print(scriptTag['content'])
    # print(plain_text)
    return scriptTag['content']
@app.route('/youtube')
def insex():
    return render_template('youtube.html')

@app.route('/handle_data', methods=['POST'])
def handle_data():
    projectpath = request.form['projectFilepath']
    songname=projectpath
    app.logger.info(songname)
    songLink = findLink(songname)
    return render_template('youtube.html' , songLink = songLink)


# @app.route('/open')
# def open():






# -----------------------------------------Close youtube--------------------------------------



if __name__=='__main__':
	app.secret_key='secret123'
	app.run(debug=True)
