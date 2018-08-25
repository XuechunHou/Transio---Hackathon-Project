from flask import Flask, request, redirect, url_for
import twilio.twiml
import twilio.rest
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import *
import os
from googletrans import Translator

app = Flask(__name__)
# Host number
host_number = "+18733715591"
bot_number = "+16474909749"
callee_number = None
account_sid = os.environ['TWILIO_ACCOUNT_SID']
account_token = os.environ['TWILIO_AUTHY_TOKEN']
conference_name = "meeting123"
client = twilio.rest.Client(account_sid, account_token)
hostUrl = "https://92974f61.ngrok.io"
record_url = None
current_bot_in_meeting = None

# chosen langs
caller_lang = None
callee_lang = None

# Language Maps
google_langs = {'1': 'en', '2': 'zh-cn'}
alice_gather_langs = {'1': 'en-US', '2': 'cmn-Hans-CN'}
alice_say_langs = {'1': 'en-US', '2': 'zh-CN'}

@app.route('/', methods=['GET', 'POST'])
def index():
    return 'Hello'
@app.route('/sms', methods=['GET', 'POST'])
def sms_reply():
    from_number = request.form['From'] # get message sender phone number Ida's phone number
    to_number = request.form['To'] # get message receiver phone number Twilio number
    body = request.form['Body'] # get message body which should contain geocoded address, destination
    resp = MessagingResponse()
    # Add a text message
    resp.message(from_number + " " + to_number + " " + body)
    return str(resp)

# host number gets called
@app.route('/voice', methods=['GET','POST'])
def answer_call():
    resp = VoiceResponse()
    
    with resp.gather(numDigits=1, action="/select_caller_language",
                     method="POST") as g:
        g.say("Please select your language: 1 for English and 2 for Mandarin", voice="alice")
                     
    return str(resp)

@app.route('/select_caller_language', methods=['GET','POST'])
def select_caller_language():
    global caller_lang
    caller_lang = request.values.get('Digits', None)
    resp = VoiceResponse()
    
    with resp.gather(numDigits=1, action="/select_callee_language",
                     method="POST") as g:
        g.say("Please select your friend's language: 1 for English and 2 for Mandarin", voice="alice")
                     
    return str(resp)

@app.route('/select_callee_language', methods=['GET','POST'])
def select_callee_language():
    global callee_lang
    callee_lang = request.values.get('Digits', None)
    resp = VoiceResponse()
    
    with resp.gather(numDigits=10, action="/connect_callee",
                     method="POST") as g:
        g.say("Please enter 10 digit phone number", voice="alice")
                     
    return str(resp)

# call callee and put caller in meeting 123
@app.route('/connect_callee', methods=['GET','POST'])
def connect_callee():
    global callee_number # callee
    
    callee_number = request.values.get('Digits', None)
    
    # make the call to callee
    client.calls.create(to=callee_number, from_=host_number,
                        url=hostUrl + "/voice/callee_on_connect" )
        
                        conference_room_name = "meeting123"
                        
                        # call robot from host
                        client.calls.create(to=bot_number, from_=host_number, url=hostUrl + '/voice/on_caller_connect_robot')
                        
                        resp = VoiceResponse()
                        # put caller to meeting 123
                        with resp.dial(method="POST") as d:
                            d.conference(name=conference_room_name, muted=False, beep='onEnter',
                                         statusCallbackEvent="join leave", statusCallback="/voice/conference",
                                         statusCallbackMethod="POST")


return str(resp)


# put callee to meeting 1234
@app.route("/voice/callee_on_connect", methods=['GET', 'POST'])
def handle_host_call_customer_service():
    global callee_call_sid
    callee_call_sid = request.values.get('CallSid')
    resp = VoiceResponse()
    conference_room_name = "meeting1234"
    with resp.dial(method="POST") as d:
        d.conference(name=conference_room_name, muted=False, beep='onEnter',
                     statusCallbackEvent="join leave", statusCallback="/voice/conference",
                     statusCallbackMethod="POST")
    
    return str(resp)

@app.route("/voice/on_caller_connect_robot", methods=['GET', 'POST'])
def handle_on_caller_connect_robot():
    global current_bot_in_meeting
    resp = VoiceResponse()
    resp.say("bot joins meeting 123 ", voice="alice")
    current_bot_in_meeting = "meeting123"
    print("before caller connect to robot 123")
    # put bot to meeting 123
    with resp.dial(method="POST") as d:
        d.conference(name="meeting123", muted=False, beep='onEnter',
                     statusCallbackEvent="join leave", statusCallback="/voice/conference",
                     statusCallbackMethod="POST")
    
    print("no sth to play")


return str(resp)

@app.route("/voice/on_callee_connect_robot", methods=['GET', 'POST'])
def handle_on_callee_connect_robot():
    global current_bot_in_meeting
    resp = VoiceResponse()
    resp.say("bot joins meeting 1234 ", voice="alice")
    
    current_bot_in_meeting = "meeting1234"
    print("before callee connect to robot 1234")
    
    # put bot to meeting 1234
    with resp.dial(method="POST") as d:
        d.conference(name="meeting1234", muted=False, beep='onEnter',
                     statusCallbackEvent="join leave", statusCallback="/voice/conference",
                     statusCallbackMethod="POST")
    
    return str(resp)




# handler when call comes into robot number
@app.route("/robot", methods=['GET', 'POST'])
def handle_robot():
    global record_url
    resp = VoiceResponse()
    
    translator = Translator()
    if record_url != None:
        resp.say("reply as follows",loop=1,voice='alice')
        # "meeting1234" record: english
        #meeting123 record: chinese
        if current_bot_in_meeting:
            print("current meeting: " + current_bot_in_meeting + "record:" + record_url)
        if current_bot_in_meeting == "meeting1234":
            
            resp.say(translator.translate(record_url, src=google_langs[callee_lang], dest=google_langs[caller_lang]).text,loop=1, voice='alice', language=alice_say_langs[caller_lang])
        else:
            resp.say(translator.translate(record_url, src=google_langs[caller_lang], dest=google_langs[callee_lang]).text,loop=1, voice='alice', language=alice_say_langs[callee_lang])
        print("has record to play")
        print("record_url = " + record_url)
    
    print("no sth to play")

if current_bot_in_meeting == "meeting1234":
    gather = Gather(input='speech', action='/handle_transcribe', speechTimeout="auto",timeout= 4, language=alice_gather_langs[caller_lang])
    else:
        gather = Gather(input='speech', action='/handle_transcribe', speechTimeout="auto",timeout= 4, language=alice_gather_langs[callee_lang])
gather.say("please reply",voice='alice')
resp.append(gather)
print("bot hangs up the call")
return str(resp)

@app.route("/handle_transcribe", methods=['GET', 'POST'])
def handle_transcribe():
    global current_bot_in_meeting
    global record_url
    resp = VoiceResponse()
    
    record_url = request.values.get('SpeechResult', None)
    print("record: " + record_url)
    resp.hangup()
    return str(resp)


# handler when participant join or leave meeting
@app.route("/voice/conference", methods=['GET', 'POST'])
def handle_conference():
    event = request.values.get("StatusCallbackEvent")
    if event == "participant-join":
        print("someone join the meeting")
    elif event == "participant-leave":
        print("bot leaves the meeting")
        
        if current_bot_in_meeting == "meeting123":
            client.calls.create(to=bot_number, from_=host_number,
                                url=hostUrl + "/voice/on_callee_connect_robot" )
        elif current_bot_in_meeting == "meeting1234":
            client.calls.create(to=bot_number, from_=host_number,
                                url=hostUrl + "/voice/on_caller_connect_robot" )
return ""



@app.route('/completed', methods=['GET','POST'])
def response_call():
    x = request.form['SpeechResult']
    resp = VoiceResponse()
    resp.say(x, voice='alice')
    return str(resp)

if __name__ == "__main__":
    app.run()
