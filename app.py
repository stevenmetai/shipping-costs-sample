#!/usr/bin/env python

import pycurl
import urllib
import json
import os
import StringIO

import flask
import httplib2
from apiclient import discovery
from flask import send_from_directory
from oauth2client import client
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub




# Flask app should start in global layout
app = flask.Flask(__name__, static_folder='')
app.secret_key = 'super secret key'

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-79baf02c-29d0-11e5-b8da-0619f8945a4f'
pnconfig.publish_key = 'pub-c-a3e23e4f-a8de-4725-9410-73836d348af4'

pubnub = PubNub(pnconfig)
state = None
code = None

@app.route('/index')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        print "ACCESS_TOKEN : " +credentials.access_token
        ##user_info_service = discovery.build(
        ##    serviceName='email', version='v1',
        ##    http=http_auth)
        #user_info = user_info_service.userinfo().get().execute()
        #if user_info and user_info.get('id'):
        email = credentials.id_token['email']
        print "Email : " + email
        return flask.redirect("https://www.google.com?result_code=SUCCESS", code=302)


@app.route('/channel')
def channel():
    channelNum = flask.request.args.get('num')
    userId = flask.request.args.get('userId')
    print("channel : "+channelNum + "  userId : " + userId)
    playVideo(userId, channelNum)
    return "OK " + channelNum


def playVideo(userId, channelnumber):
    message = json.dumps({'action': 'startPlayChannel', 'channel_no': channelnumber})
    pubnub.publish().channel(userId).message(message).sync()


@app.route('/', methods=['GET', 'POST'])
def zero():
    req = flask.request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))
    return "HELLO"


@app.route('/login', methods=['GET', 'POST'])
def login():
    global state
    state = flask.request.args.get('state')
    global code
    code = flask.request.args.get('code')
    return send_from_directory(directory=app.static_folder, filename='amazonoauth.html')


@app.route('/handle_login', methods=['GET', 'POST'])
def handle_login():
    access_token = flask.request.args.get('access_token')
    b = StringIO.StringIO()

    # verify that the access token belongs to us
    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://api.amazon.com/auth/o2/tokeninfo?access_token=" + urllib.quote_plus(access_token))
    c.setopt(pycurl.SSL_VERIFYPEER, 1)
    c.setopt(pycurl.WRITEFUNCTION, b.write)

    c.perform()
    d = json.loads(b.getvalue())

    if d['aud'] != 'amzn1.application-oa2-client.5e9c7fb1640b44759e12682c130c5db0':
        # the access token does not belong to us
        raise BaseException("Invalid Token")

    # exchange the access token for user profile
    b = StringIO.StringIO()

    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://api.amazon.com/user/profile")
    c.setopt(pycurl.HTTPHEADER, ["Authorization: bearer " + access_token])
    c.setopt(pycurl.SSL_VERIFYPEER, 1)
    c.setopt(pycurl.WRITEFUNCTION, b.write)

    c.perform()
    d = json.loads(b.getvalue())

    print "%s %s %s" % (d['name'], d['email'], d['user_id'])
    return send_from_directory(directory=app.static_folder, filename='handle_login.html')


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
        playVideo(channelnumber)
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


@app.route('/privacy')
def privacy():
    return "Privacy Page"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    #context = ('server.key', 'server.crt')
    print "Starting app on port %d" % port

    app.run(debug=True, port=port, host='0.0.0.0')
