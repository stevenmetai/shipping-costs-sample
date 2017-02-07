#!/usr/bin/env python

import urllib
import json
import os

from flask import Flask
from flask import request
from flask import redirect
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/')
def hello_world():
    print("Hi man")
    return "HELLO"

@app.route('/auth')
def auth():
    print("AUTH!!!")
    redirectUri = request.args.get("redirect_uri")
    print redirectUri
    return redirect(redirectUri)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeWebhookResult(req):
    if req.get("result").get("action") != "play-action":
        return {}
    result = req.get("result")
    parameters = result.get("parameters")
    channelnumber = parameters.get("channelNumber")

    #cost = {'Europe':100, 'North America':200, 'South America':300, 'Asia':400, 'Africa':500}

    speech = "The channel " + channelnumber + " starts to play"

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
