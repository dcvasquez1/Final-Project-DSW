from flask import Flask, redirect, url_for, session, request, jsonify, flash, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from random import randint

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

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

def scores_to_html():
    try:
        userStyle = ' style="text-align:left;padding-right: 300px;"'
        scoreStyle = ' style="padding-right:30px; padding-left:30px;"'
        rankStyle = ' style="padding-right:10px; padding-left:10px;"'
        tableString = '<table id="scoreTable" cellpadding="5"> <tr> <th' + rankStyle + '></th> <th' + userStyle + '></th> <th><u> Performance </u></th><th' + scoreStyle + '><u> WPM </u></th> <th><u> Accuracy </u></th> </tr>'
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        scoresArray = []
        
        for score in clientData.find():
            scoresArray.append(score['rawPP'])
        scoresArray = sorted(scoresArray, key=float, reverse=True)

        for score in scoresArray:
            for user in clientData.find({"rawPP": score}):
                tableString += " <tr> <td>#" + str(scoresArray.index(score) + 1) + " </td>"
                tableString += " <td style='text-align:left'><b>" + user['username'] + ":</b> </td>"
                tableString += " <td> " + str(round(float(score), 1)) + " </td>"
                tableString += " <td> " + str(round(float(user['score']), 1)) + "</td>"
                tableString += " <td> " + str(round(float(user['percentage']), 1)) + "%</td>"
                tableString += ' </tr> '
        tableString += " </table>"
        table = Markup(tableString)
        return table
    except Exception as e:
        return Markup('<p>' + str(e) + '</p>')

def createLeaderboard():
    try:
        rankStyle = ' style="padding-right:20px; padding-left:20px;"'
        userStyle = ' style="text-align:left;padding-right: 300px;"'
        wpmStyle = ' style="padding-right:12px; padding-left:12px;"'
        rankNumStyle = ' style="padding-right:10px; padding-left:10px;"'
        tableString = '<table id="rankingTable" cellpadding="5"> <tr> <th' + rankNumStyle + '></th> <th' + userStyle + '></th> <th><u> Play Count </u></th> <th><u> Performance </u></th> <th ' + wpmStyle + '><u> WPM </u></th> <th><u> Accuracy </u></th><th' + rankStyle + '><u> S </u></th> <th' + rankStyle + '><u> A </u></th> <th' + rankStyle + '><u> B </u></th> </tr>'
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        rankingData = database["rankingData"]
        rankingArray = []
        scoresArray = []
        
        for score in rankingData.find():
            scoresArray.append(score['pp'])
        scoresArray = sorted(scoresArray, key=float, reverse=True)

        for score in scoresArray:
            for matchingProfile in rankingData.find({'pp': score}):
                tableString += " <tr> <td>#" + str(scoresArray.index(score) + 1) + "</td>"
                tableString += " <td style='text-align:left'><b>" + matchingProfile['username'] + "</b> </td>"
                tableString += " <td>" + matchingProfile['gamesPlayed'] + "</td>"
                tableString += " <td>" + str(round(float(matchingProfile['pp']), 1)) + "</td>"
                tableString += " <td>" + str(round(float(matchingProfile['wpm']), 1)) + "</td>"
                tableString += " <td>" + str(round(float(matchingProfile['acc']), 1)) + "%</td>"
                tableString += " <td>" + matchingProfile['s-rank'] + "</td>"
                tableString += " <td>" + matchingProfile['a-rank'] + "</td>"
                tableString += " <td>" + matchingProfile['b-rank'] + "</td>"
                tableString += " </tr> "
        tableString += " </table>"
        
        table = Markup(tableString)
        return table
    except Exception as e:
        return Markup('<p>' + str(e) + '</p>')

def findAvg():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        avgScore = 0
        for gameEntry in clientData.find({ "username": str(username) }):
            avgScore += float(gameEntry['score'])
        avgScore = round(( avgScore / clientData.count({ "username": str(username) }) ), 1)
        return Markup("<p> " + str(avgScore) + " WPM</p>")
    except Exception as e:
        return Markup("<p> Unable to find user data. </p>")


def findPP():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        scoreSum = 0
        for gameEntry in clientData.find({ "username": str(username) }):
            scoreSum += float(gameEntry['score'])
        scoreSum = round(( scoreSum / clientData.count({ "username": str(username) }) ), 1)
        ppoints = scoreSum
        return Markup('<p"> ' + str(ppoints) + " pp</p>")
    except Exception as e:
        return Markup("<p>  Unable to find user data. </p>")

def findAcc():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
        acc = 0
        for gameEntry in clientData.find({ "username": str(username) }):
            acc += float(gameEntry['percentage'])
        acc = round(( acc / clientData.count({ "username": str(username) }) ), 1)
        return Markup('<p> ' + str(acc) + "%</p>")
    except Exception as e:
        return Markup("<p> Unable to find user data. </p>")

def findHigh():
    try:
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
        database = client["dsw-final-project"]
        clientData = database["clientData"]
        username = session['user_data']['login']
	
        highScore = 0
        for gameEntry in clientData.find({ "username": str(username) }):
            if float(gameEntry['score']) > highScore:
                highScore = round(float(gameEntry['score']), 1)
        return Markup("<p> " + str(highScore) + " WPM</p>")
    except Exception as e:
        return Markup("<p> Unable to find user data. </p>")
	
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

@app.route('/showScore', methods=['POST'])
def submitScore():
    clientTypedString = request.form["typed_text"]
    templateString = request.form["original_text"]
    timeInMilliseconds = request.form["typing_time"]
    timeInSeconds = float(timeInMilliseconds)/1000
    timeInMinutes = timeInSeconds/60

    typedArray = clientTypedString.split()
    templateArray = templateString.split()
    
    correctWords = 0
    for i, templateWord in enumerate(templateArray):
        if i < len(typedArray):
            if templateWord == typedArray[i]:
                correctWords += 1

    percentageCorrect = round(float((correctWords)/(len(templateArray))) * 100, 2)
    userWPM = round((correctWords)/(timeInMinutes), 1)

    rawAcc = float((correctWords)/(len(templateArray)))
    rawWPM = (correctWords)/(timeInMinutes)

    rawPP = (rawAcc**7)*rawWPM
    roundedPP = round(rawPP, 2)

    client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
    database = client["dsw-final-project"]

    clientScores = database["clientData"]
    rankedScores = database["rankingData"]
    rankString = ""
    rankDictKey = ""

    shorteningString = '_rank"><span style="font-size:200%">Rank: </span><span style="color:'
    if percentageCorrect == 100.0:
        rankString = '<p id="S' + shorteningString + '#f3e502; font-size:500%;">S</span></p>'
        rankDictKey = "s-rank"
    elif percentageCorrect >= 93.5:
        rankString = '<p id="A' + shorteningString + '#57e54b; font-size:500%;">A</span></p>'
        rankDictKey = "a-rank"
    elif percentageCorrect >= 81.0:
        rankString = '<p id="B' + shorteningString + '#007ff2; font-size:500%;">B</span></p>'
        rankDictKey = "b-rank"
    elif percentageCorrect >= 70.0:
        rankString = '<p id="C' + shorteningString + '#f667d6; font-size:500%;">C</span></p>'
        rankDictKey = "c-rank"
    elif percentageCorrect >= 60.0:
        rankString = '<p id="D' + shorteningString + '#ff4700; font-size:500%;">D</span></p>'
        rankDictKey = "d-rank"
    else: 
        rankString = '<p id="F' + shorteningString + '#ff0000; font-size:500%;">F</span></p>'
        rankDictKey = "f-rank"
    
    try:
        username = session['user_data']['login']
        scoresList = []
        for score in clientScores.find({'username': username}):
            scoresList.append(score['rawPP'])

        scoresList = sorted(scoresList, key=float, reverse=True)
        total_userPP = 0
        for index, score in enumerate(scoresList):
            total_userPP += float(score) * (0.8**index)
        total_userPP = round(total_userPP, 2)

        user = {}
        if rankedScores.find_one({ "username": username }) == None:
            user = buildRankedProfile()
            user["username"] = username
            user["wpm"] = str(rawWPM)
            user["acc"] = str(rawAcc*100)
            user["pp"] = str(rawPP)
            user["gamesPlayed"] = str(1)
            user[rankDictKey] = str(1)
        else:
            user = rankedScores.find_one({ "username": username })
            user["username"] = username
            user["wpm"] = str( (float(user["wpm"]) * int(user["gamesPlayed"]) + rawWPM) / (int(user['gamesPlayed']) + 1) )
            user["acc"] = str( (float(user["acc"]) * int(user["gamesPlayed"]) + rawAcc*100) / (int(user['gamesPlayed'])+ 1) )
            user["pp"] = str(total_userPP)
            user["gamesPlayed"] = str(int(user["gamesPlayed"]) + 1)
            user[rankDictKey] = str(int(user[rankDictKey]) + 1)
        
        if rankedScores.find_one({ "username": username }) != None:
            rankedScores.find_one_and_replace({ "username": username }, user)
        else:
            rankedScores.insert_one(user)
        
        clientScores.insert_one( { 'username': username, 'score': str(userWPM), 'rawPP': str(rawPP), 'percentage': str(percentageCorrect) } )
        return Markup(rankString + '<p><b>Unweighted PP: </b>' + str(roundedPP) + 'pp</p> <p><b>You Typed:</b> ' + clientTypedString + '</p> <p><b>Original Text:</b> ' + templateString + '</p> <p><b>Percentage Correct:</b> ' + str(percentageCorrect) + '% </p> <p><b>Typing Time:</b> ' + str(timeInSeconds) + ' seconds</p> <p><b>Typing Speed:</b> ' + str(userWPM) + ' WPM</p>')
    except Exception as e:
        return Markup(str(e) + rankString + '<p><b>You Typed:</b> ' + clientTypedString + '</p><p><b>Original Text:</b> ' + templateString + '</p><p><b>Percentage Correct:</b> ' + str(percentageCorrect) + '% </p><p><b>Typing Time:</b> ' + str(timeInSeconds) + ' seconds</p><p><b>Typing Speed:</b> ' + str(userWPM) + ' WPM</p><br><p><b>**LOGIN TO SAVE SCORES**</b></p>')

     
def buildRankedProfile():
    return { "username": "SAMPLE-USERNAME", "pp": "0", "wpm": "0", "acc": "0", "gamesPlayed": "1", "s-rank": "0", "a-rank": "0", "b-rank": "0", "c-rank": "0", "d-rank": "0", "f-rank": "0" }

#redirect to GitHub's OAuth page and confirm the callback URL
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

@app.route('/leaderboard')
def renderLeaderboard():
    return render_template('leaderboard.html', leaderboard_table=createLeaderboard())

@app.route('/clientProfile')
def renderClientProfile():
    try:
        user = "<h1> " + str(session['user_data']['login']) + " </h1>"
        return render_template('clientProfile.html', username=Markup(user), high_score=findHigh(), avg_score=findAvg(), games_played=findNum(), pp=findPP(), acc=findAcc())
    except:
        return render_template('clientProfile.html', username=Markup('<h1> Guest User </h1> <p><b>-- Log in to record scores --</b></p>'), high_score=findHigh(), avg_score=findAvg(), games_played=findNum(), pp=findPP(), acc=findAcc())

@app.route('/gamePage')
def renderGamePage():
    client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds247449.mlab.com:47449/dsw-final-project")
    database = client["dsw-final-project"]
    sampleStrings = database["sampleStrings"]

    sampleStringArray = []
    for s in sampleStrings.find():
        sampleStringArray.append(s)
    givenString = sampleStringArray[randint(0, (len(sampleStringArray)-1))]["quote"]
    return render_template('gamePage.html', provided_quote=givenString)

@app.route('/response')
def textComplete():
    return render_template('gamePage.html')
	
#the tokengetter is automatically called to check who is logged in
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run()
