#!/usr/bin/env python

import urllib
import json
import os

import flask
import httplib2
from apiclient import discovery
from oauth2client import client

# Flask app should start in global layout
app = flask.Flask(__name__)
app.secret_key = 'super secret key'

@app.route('/index')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        ##user_info_service = discovery.build(
        ##    serviceName='email', version='v1',
        ##    http=http_auth)
        #user_info = user_info_service.userinfo().get().execute()
        #if user_info and user_info.get('id'):
        email = credentials.id_token['email']
        return email

@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets(
        'client_secret_1070580814571-0rr6m54mdtes4fe3lp1t99bvlqgllvg6.apps.googleusercontent.com.json',
        scope='email',
        redirect_uri=flask.url_for('oauth2callback', _external=True, _scheme='https'))
    if 'code' not in flask.request.args:
      auth_uri = flow.step1_get_authorize_url()
      return flask.redirect(auth_uri)
    else:
      auth_code = flask.request.args.get('code')
      print "CODE = " + auth_code
      credentials = flow.step2_exchange(auth_code)
      flask.session['credentials'] = credentials.to_json()
      return flask.redirect(flask.url_for('index'))

@app.route('/webhook', methods=['POST'])
def webhook():
    req = flask.request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = flask.make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeWebhookResult(req):
    if req.get("result").get("action") == "play-action":
        result = req.get("result")
        parameters = result.get("parameters")
        channelnumber = parameters.get("channelNumber")
        speech = "The channel " + channelnumber + " starts to play"
    elif req.get("result").get("action") == "volume-action":
        result = req.get("result")
        parameters = result.get("parameters")
        volumetype = parameters.get("volume-type")
        speech = "OK, "+ volumetype + " the volume"
    else:
        return {}
    #cost = {'Europe':100, 'North America':200, 'South America':300, 'Asia':400, 'Africa':500}


    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        #"data": {},
        # "contextOut": [],
        "source": "apiai-videotraytester"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=True, port=port, host='0.0.0.0')
