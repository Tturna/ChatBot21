# ChatBot21

import time
import speech_recognition as sr
import pywhatkit
import pyttsx3
import requests, json
import math
import inspect
import random
import urllib.request
import pafy
import vlc # Requires VLC to be installed on the machine. Probably VLC 64-bit, not tested on anything else
from datetime import date, timedelta
from youtubesearchpython import VideosSearch
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException
from bs4 import BeautifulSoup
from googlesearch import search as google

WEATHER_REQUEST_URL = "https://api.openweathermap.org/data/2.5/weather?"
tts_langID_fin = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\MSTTS_V110_fiFI_Heidi" #finnish TTS
tts_langID_en_US = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0" #english_US TTS

# Get API codes from external JSON
data = None
with open("apicodes.json", "r") as file:
    data = json.load(file)

def TryGetKey(keyName):
    try: return data[keyName]
    except: return ""

API_CODE_WEATHER = TryGetKey("weatherapi")
API_CODE_NEWS = TryGetKey("newsapi")
API_CODE_TWITTER = TryGetKey("twitterapi")
API_CODE_GOOGLECLOUD = TryGetKey("googlecloudapi")


# Filter Result codes
FILRES_NONE = 0
FILRES_WAKEWORD = 1
FILRES_GOOGLE = 2
FILRES_WIKIPEDIA = 3
FILRES_YOUTUBE = 4
FILRES_TIME = 5
FILRES_CALC = 6
FILRES_NEWS = 7
FILRES_WEATHER = 8
FILRES_COINFLIP = 9
FILRES_M8B = 10

FILRES_STOPVIDEO = 100
FILRES_MUTEVIDEO = 101
FILRES_VOLUMEUP = 102
FILRES_VOLUMEDOWN = 103
FILRES_FULLSCREEN = 104

# List of all words that are considered as "wakewords".
# The system will not run any commands before it hears a wakeword
wakeWords = ["Dude", "dude"]

# List of all command function names with their respective filter codes as indexes in the dictionary
# NOTE: DO NOT SET ANYTHING TO INDEXES 0 OR 1
commands = {
    2: "GoogleSearch",
    3: "WikipediaSearch",
    4: "YoutubeSearch",
    5: "GetTime",
    6: "Calculate",
    7: "GetNews",
    8: "GetWeather",
    9: "CoinFlip",
    10: "Magic8Ball",

    100: "Stop",
    101: "MuteVideo",
    102: "VideoVolumeUp",
    103: "VideoVolumeDown",
    104: "VideoToggleFullscreen"
}

# List of all command keywords that the system will listen to and all of their respective filter codes
keywords = {
    "Google": FILRES_GOOGLE,
    "Wikipedia": FILRES_WIKIPEDIA,
    "Who is": FILRES_WIKIPEDIA,
    "What is": FILRES_WIKIPEDIA,
    "YouTube": FILRES_YOUTUBE,
    "Play": FILRES_YOUTUBE,
    "Time": FILRES_TIME,
    "Calculate": FILRES_CALC,
    "News": FILRES_NEWS,
    "Weather": FILRES_WEATHER,
    "Coin flip": FILRES_COINFLIP,
    "Magic 8 ball": FILRES_M8B,
    "Magic 8-ball": FILRES_M8B,

    "Stop": FILRES_STOPVIDEO,
    "Mute": FILRES_MUTEVIDEO,
    "Volume up": FILRES_VOLUMEUP,
    "Volume down": FILRES_VOLUMEDOWN,
    "Full screen": FILRES_FULLSCREEN
}

errorCode = ""
isWoke = False
isPlayingVideo = False
vlcPlayer = None
ttsSpeed = 175

# ///////////////////// DEBUG MODE
debug_mode = True
# ///////////////////// DEBUG MODE
    
# Initialize the TTS engine
def Speak(text):
    global ttsSpeed

    if text == None: return
    ttsEngine = pyttsx3.init()
    ttsEngine.setProperty("rate", ttsSpeed)
    ttsEngine.setProperty("voice", tts_langID_en_US)
    ttsEngine.setProperty("volume", 0.5)
    ttsEngine.say(text)
    print("...................................................... @ " + str(ttsSpeed) + " ..... " + text)
    ttsEngine.runAndWait()
    return True

def FilterCommands(text):
    # This function will check if the argument text has any commands in it
    # Returns a filter result code depending on what was heard

    # Check if heard speech contained the wakeword
    for w in wakeWords:
        if w in text:
            # Wakeword detected
            return FILRES_WAKEWORD, []

    # Check if a command was heard
    text = str.lower(text)
    for k in keywords:
        og = k
        k = str.lower(k)
        if (k in text):

            # NOTE: This system needs improvement
            # Currently you can only search stuff on Google and Wikipedia by saying
            # "Google x" or "Wikipedia x"
            # You should be able to also search by saying
            # "Search x on Google" or "Find x from Wikipedia"

            args = []

            # Find the initial command word's starting position
            cspos = text.find(k)
            fullcmd = text[cspos:]
            cmd = fullcmd[:len(k)]

            try:
                argsAtEnd = True
                while True: # This "while" is here just so we can break from it later

                    # Check if arguments should be taken from BEFORE the command
                    if (cspos > 5 and len(text) > cspos + len(cspos) + 5):
                        argsAtEnd = False

                        # Filter out useless words...
                        preCmd = text[:cspos]

                        fuckyQuestionWords = ["what", "how"]
                        # If the precommand contains a fucky question word, skip this
                        for f in fuckyQuestionWords:
                            if f in preCmd:
                                argsAtEnd = True
                                break

                        # ... from the start of the pre-command
                        fuckyWords = ["search", "find", "check", "look up"]
                        for f in fuckyWords:
                            if f in preCmd:
                                preCmd = preCmd[:preCmd.find(f)] + preCmd[len(f):]

                        # ... from the end of the pre-command
                        fuckyWordsPartTwo = [" on ", " from ", " in "]
                        for f in fuckyWordsPartTwo:
                            if f in preCmd:
                                if len(preCmd) <= preCmd.find(f) + len(f):
                                    preCmd = preCmd[:preCmd.find(f)]

                        args = str(preCmd).split()
                    break

                if (argsAtEnd):
                    # Get all the words after the initial command and set them as arguments, if possible
                    argset = fullcmd[len(k) + 1:]
                    args = argset.split()
            except: pass

            print("Command: " + cmd + ", Args: " + str(args))

            return keywords[og], args

    # No command detected
    return FILRES_NONE, []

# Commands ------------------------------------------------------------------------
def GoogleSearch(query="###"):

    # Check if this function was called with no parameters
    # If so, roast the fuck our of the user
    roasts = ["I can't Google nothing", "Provide something to Google", "No", "Fuck you"]
    print("Google query: " + str(query))
    if (query == "###" or query == [] or query == "" or query == None):
        return random.choice(roasts)

    maxContentCharacters = 400

    # Attempt to get Google results
    attempts = 3
    contents = " nothing. Google got fucked."
    resultURLs = google(query, num_results=attempts)
    for n in range(attempts):
        try:
            html = urllib.request.urlopen(resultURLs[n]).read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            contents = " ".join(soup.get_text().split())[:maxContentCharacters]
            break
        except:
            continue
    print("Found: " + contents)

    # Check if result was on Wikipedia and use the proper command for it instead
    if ("wikipedia" in contents.lower()):
        return WikipediaSearch(query)

    return "I found this on Google, " + contents

def WikipediaSearch(query="###"):

    # Check if this function was called with no parameters
    # If so, roast the fuck our of the user
    roasts = ["Yes, Wikipedia is a thing.", "Give me a topic, dipshit"]
    if (query == "###" or query == [] or query == "" or query == None):
        return random.choice(roasts)

    maxContentCharacters = 400
    print("Wikipedia query: " + str(query))
    contents = str(pywhatkit.info(query, return_value=True))[:maxContentCharacters]

    return "I Found this on Wikipedia, " + contents

def YoutubeSearch(query):
    global vlcPlayer
    global isPlayingVideo

    Speak("Looking for " + query + " on YouTube.")

    # Get best relevant YouTube video URL
    resultDict = VideosSearch(query, limit = 1).result()
    print("YTSearch got: " + resultDict["result"][0]["link"])
    pafynew = pafy.new(resultDict["result"][0]["link"])
    print("Pafy got: " + str(pafynew))
    bestresult = pafynew.getbest()
    url = bestresult.url

    # Tell VLC to play the video
    Instance = vlc.Instance()
    vlcPlayer = Instance.media_player_new()
    Media = Instance.media_new(url)
    Media.get_mrl()
    vlcPlayer.set_media(Media)
    vlcPlayer.audio_set_volume(40)
    vlcPlayer.set_fullscreen(True)
    vlcPlayer.play()
    isPlayingVideo = True

    return "Playing " + resultDict["result"][0]["title"]

def GetTime():
    cTime = time.localtime()
    return "The time is " + str(cTime.tm_hour) + ":" + ("0" + str(cTime.tm_min))[-2:]

def Calculate(equation):
    return "Calculating doesn't exist yet."

def GetNews(requestParam="recent"):
    global ttsSpeed

    # Maybe get some news from Twitter? Pretty sure they have an API
    # NewsApiClient for actual sources
    newsapi = NewsApiClient(api_key=API_CODE_NEWS)
    sources = "google-news,bbc-news,cnn"
    print("RePa: " + requestParam)

    # Parse the request parameter(s)
    # Get news accordingly
    startDate = str(date.today() - timedelta(days=7))
    if ("week" in requestParam):
        startDate = str(date.today() - timedelta(days=7))

    news = ""

    try:
        all_articles = newsapi.get_everything(
        sources=sources,
        from_param=startDate,
        to=str(date.today()),
        language='en',
        sort_by='publishedAt',
        page=1)

        for article in all_articles["articles"]:
            news += article["source"]["name"] + ". \n" + article["title"] + ". \n" + article["description"] + " \n ----------------- \n"
    except NewsAPIException:
        return "Something went wrong when looking for news. Check your API key."
    except:
        return "Something went wrong when looking for news."

    # Slow down the TTS so you can actually comprehend the news
    ttsSpeed = 135

    return "No news found." if len(news) < 10 else news

def GetWeather(query):
    roasts = ["Please specify a city", "A city needs to be specified to get weather"]
    if (query == "###" or query == [] or query == "" or query == None):
        return random.choice(roasts)

    # Filter out bullshit word(s)
    fuckery = ["in ", "at ", "like "]
    for f in fuckery:
        if f in query:
            query = query[:query.find(f)] + query[query.find(f) + len(f):]

    CITY = str(query)
    API_KEY = API_CODE_WEATHER
    URL = WEATHER_REQUEST_URL + "q=" + CITY + "&appid=" + API_KEY + "&units=metric"
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        main = data['main']
        wind = data['wind']
        clouds = data['clouds']
        feelslike = main['feels_like']
        temperature = main['temp']
        humidity = main['humidity']
        clouds_all = clouds['all']
        wind_speed = wind['speed']
        report = data['weather']
        rounded_temp = round(temperature)
        rounded_feels = round(feelslike)
        return "Weather in " + CITY + ": " + str(report[0]['description']) + ", " + str(rounded_temp) + " degrees, at a humidity of, " + str(humidity) + " %, the temperature feels like " + str(rounded_feels) + " degrees. It is " + str(clouds_all) + "%" + "  cloudy and the wind speed is " + str(wind_speed) + " meters per second"
    else:
        return "Error. API key is not set." if (API_KEY == "") else CITY + " is not a valid city."
        
def CoinFlip():
    flip = random.randint(0,1)
    if (flip == 0):
        return "Heads"
    else:
        return "Tails"

def Magic8Ball(question):
    if question == "":
        return "You need to ask a question"
    else:
        responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predict you", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
        return random.choice(responses)
 
def Stop():
    # This function will stop whatever is currently going on

    if (isPlayingVideo):
        vlcPlayer.stop()

def MuteVideo():
    print("Toggled video mute.")
    vlcPlayer.audio_toggle_mute()

def VideoVolumeUp(amount=10):
    amount = amount if int(amount.isdigit()) else 10
    print("Increased video volume by " + str(amount))
    vlcPlayer.audio_set_volume(vlcPlayer.audio_get_volume() + amount)

def VideoVolumeDown(amount=-20):
    amount = amount if int(amount.isdigit()) else -20
    print("Decreased video volume by " + str(amount))
    vlcPlayer.audio_set_volume(vlcPlayer.audio_get_volume() + amount)

def VideoToggleFullscreen():
    vlcPlayer.toggle_fullscreen()

# Commands ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def ExecuteCommand(filterResult, argList):
    global isWoke
    global errorCode

    errorCode = ""
    tts = "Something went wrong. This shouldn't have happened."

    # Listen for wakeword
    if (filterResult == 1):
        isWoke = True
        tts = "Hello"

    # Return error if the system is not WOKE and a command was heard
    # Ignore wokeness if debug mode is enabled
    elif (isWoke == False and debug_mode == False):
        errorCode = "Not woke"
        return False

    # Return error when no command was heard
    elif (filterResult == 0):
        errorCode = "No such command"
        tts = "I don't know what that means."
    
    # Execute heard command
    if errorCode == "" and filterResult != 1:
        # paramNames is a list of parameter names in the function
        paramNames, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(eval(commands[filterResult]))

        # Get arguments from heard speech if there are any
        args = '"'

        for n in range(len(argList)):
            args += str(argList[n])
            if len(argList) > n + 1:
                args += " "
        args += '"'

        # Check if the function wants parameters. If not, clear arguments variable
        if (len(paramNames) == 0):
            args = ""

        # Call the command function
        #tts = eval(commands[filterResult] + "(" + args + ")")
        try:
            tts = eval(commands[filterResult] + "(" + args + ")")
        except:
            tts = "Something went wrong with the command."
    
    # Text-To-Speech
    Speak(tts)

    return errorCode == ""

# this is called from the background thread
def ProcessAudio(recognizer, audio):
    global ttsSpeed

    ttsSpeed = 175

    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        text = recognizer.recognize_google(audio)
        filterResult, args = FilterCommands(text)
        print(text)
        #print(text + " [ Detected command: " + str(filterResult) + " ]")

        succeeded = ExecuteCommand(filterResult, args)

        if (not succeeded):
            print("Error: " + errorCode)

    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


r = sr.Recognizer()
m = sr.Microphone()

r.energy_threshold = 150 # energy level threshold for sounds. Values below this threshold are considered silence (default: 300)
r.pause_threshold = 0.5 # minimum length of silence (in seconds) that will register as the end of a phrase (default: ~0.7)
phrase_time = 7.5 # maximum time in seconds the recognizer will listen to a phrase before cutting off (default: None)

with m as source:
    r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening

print("Listening for speech...")

# start listening in the background
stop_listening = r.listen_in_background(source=m, callback=ProcessAudio, phrase_time_limit=phrase_time)
# `stop_listening` is now a function that, when called, stops background listening

# Right here we can do other shit. The system will keep listening even if we freeze the thread by looping and stuff

# calling this function requests that the background listener stop listening
#stop_listening(wait_for_stop=False)

#print("Stopped listening")

while True:
    time.sleep(0.1)
    #print(ttsEngine.isBusy())
