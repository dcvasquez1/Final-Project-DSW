from flask import Flask, redirect, url_for, session, request, jsonify, flash
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os

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


#redirect to HitHub'[s OAuth page and confirm the callback URL
@app.route('/login')
def login():   
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
    return render_template('scoreboard.html')

@app.route('/clientProfile')
def renderClientProfile():
    return render_template('clientProfile.html')

@app.route('/clientProfile')
def renderGamePage():
    return render_template('gamePage.html')
	
#the tokengetter is automatically called to check who is logged in
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()