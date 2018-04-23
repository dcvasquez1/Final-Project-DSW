from flask import Flask, redirect, url_for, session, request, jsonify, flash, Markup
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import time
import json
import pymongo
from pymongo import MongoClient

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #use SECRET_KEY to sign session cookies
oauth = OAuth(app)

#Set up Github as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #webapp's pseudo username for github OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'], #webapp's pseudo password for github OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#context processors run before template are rendered and add variable(s) to the template
#context processors must return a dictionary
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

def scores_to_html():
    try:
        tableString = '<table id="scoreTable" cellpadding="5"> <tr> <th> Username </th> <th> High Score </th> </tr>'
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        
        for i in clientData.find():
            tableString += " <tr> <td>" + i['username'] + ": </td>"
            tableString += " <td>" + i['score'] + "</td>"
            tableString += ' </tr> '
        tableString += " </table>"
        table = Markup(tableString)
        return table
    except Exception as e:
        return Markup('<p>' + str(e) + '</p>')

@app.route('/postedScore', methods=['POST'])
def postScore():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        score = request.form['score']
        clientData.insert_one({'username': username, 'score': score})
        return render_template('scoreboard.html', scoreboard_table=scores_to_html())
    except Exception as e:
        return render_template('scoreboard.html', scoreboard_table=Markup('<p>' + str(e) + '</p>'))

def findAvg():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        avgScore = 0
        for gameEntry in clientData.find({ "username": str(username) })
            avgScore += gameEntry['score']
        avgScore = (avgScore)/(clientData.count({ "username": str(username) }))
        return Markup("<p> " + str(avgScore) + " </p>")
    except:
        return Markup("<p> Unable to find user data </p>")
	
def findHigh():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
	
        highScore = 0
        for gameEntry in clientData.find({ "username": str(username) })
            if gameEntry['score'] > highScore:
                highScore = gameEntry['score']
        return Markup("<p> " + str(highScore) + " </p>")
    except:
        return Markup("<p> Unable to find user data </p>")
	
def findNum():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        
        numPlayed = clientData.count({ "username": str(username) })
        return Markup("<p> " + str(numPlayed) + " </p>")
    except:
        return Markup("<p> Unable to find user data </p>")

#redirect to HitHub'[s OAuth page and confirm the callback URL
@app.route('/login')
def login():
    client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
    database = client["dsw-final-project"]
    clientData = database["clientData"]

    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')#the route should match the callback URL registered with the OAuth provider
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            #save user data and set log in message
            session['github_token'] = (resp['access_token'], '')
            session['user_data'] = github.get('user').data
            message = "Your were successfully logged in as " + session['user_data']['login']
        except:
            #clear the session and give error message
            session.clear()
            message = 'Unable to login. Please try again.'
            
    return render_template('message.html', message=message)


@app.route('/scoreboard')
def renderScoreboard():
    return render_template('scoreboard.html', scoreboard_table=scores_to_html())

@app.route('/clientProfile')
def renderClientProfile():
    try:
        user = "<h1> " + str(session['user_data']['login']) + " </h1>"
        return render_template('clientProfile.html', username=user, high_score=findHigh(), avg_score=findAvg(), games_played=findNum())
    except:
        return render_template('clientProfile.html', username='<h1> Guest User </h1>')

@app.route('/gamePage')
def renderGamePage():
    return render_template('gamePage.html')

@app.route('/response')
def textComplete():
    return render_template('gamePage.html')
	
#the tokengetter is automatically called to check who is logged in
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
