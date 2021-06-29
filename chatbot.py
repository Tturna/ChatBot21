# ChatBot21

import time
import speech_recognition as sr
import pywhatkit
import pyttsx3
import requests, json
import math
import inspect
from googlesearch import search as google

WEATHER_REQUEST_URL = "https://api.openweathermap.org/data/2.5/weather?"
tts_langID_fin = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\MSTTS_V110_fiFI_Heidi" #finnish TTS
tts_langID_en_US = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0" #english_US TTS

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

# List of all words that are considered as "wakewords".
# The system will not run any commands before it hears a wakeword
wakeWords = ["Dude", "dude"]

# List of all command function names with their respective filter codes as indexes in the dictionary
commands = {
    2: "GoogleSearch",
    3: "WikipediaSearch",
    4: "YoutubeSearch",
    5: "GetTime",
    6: "Calculate",
    7: "GetNews",
    8: "GetWeather"
}

# List of all command keywords that the system will listen to and all of their respective filter codes
# NOTE: Use the upper case versions here. The system will check both these words and their lower case versions.
keywords = {
    "Google": FILRES_GOOGLE,
    "Wikipedia": FILRES_WIKIPEDIA,
    "YouTube": FILRES_YOUTUBE,
    "Time": FILRES_TIME,
    "Calculate": FILRES_CALC,
    "News": FILRES_NEWS,
    "Weather": FILRES_WEATHER
}

errorCode = ""
isWoke = False
debug_mode = True
    
# Initialize the TTS engine
def Speak(text):
    ttsEngine = pyttsx3.init()
    ttsEngine.setProperty("rate", 175)
    ttsEngine.setProperty("voice", tts_langID_en_US)
    ttsEngine.setProperty("volume", 0.5)
    ttsEngine.say(text)
    ttsEngine.runAndWait()
    return True

def FilterCommands(text):
    # This function will check if the argument text has any commands in it
    # Returns a filter result code depending on what was heard

    # Check if heard speech contained the wakeword
    for w in wakeWords:
        if w in text:
            # Wakeword detected
            return FILRES_WAKEWORD

    # Check if a command was heard
    for k in keywords:
        if (k in text or str.lower(k) in text):
            return keywords[k]

    # No command detected
    return FILRES_NONE

# Commands ------------------------------------------------------------------------
def GoogleSearch(query):
    return "Google searching doesn't exist yet."

def WikipediaSearch(query):
    return "Wikipedia searching doesn't exist yet."

def YoutubeSearch(query):
    return "YouTube searching doesn't exist yet."

def GetTime():
    cTime = time.localtime()
    return "The time is " + str(cTime.tm_hour) + ":" + str(cTime.tm_min) 

def Calculate(equation):
    return "Calculating doesn't exist yet."

def GetNews():
    return "Getting news doesn't exist yet."

def GetWeather():
    CITY = "" #used later as a keyword thingymajigy you know chief
    API_KEY = ""
    URL = WEATHER_REQUEST_URL + "q=" + CITY + "&appid=" + API_KEY
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        main = data['main']
        temperature = main['temp']
        humidity = main['humidity']
        #pressure = main['pressure'] idk does anyone actually need to know this? leaving here in case yes
        report = data['weather']
        temperature -= 273
        rounded_temp = round(temperature)
        return "Weather in " + CITY + ": " + str(report[0]['description']) + ", " + str(rounded_temp) + " degrees at a humidity of" + str(humidity) + " %"
    else:
        return "Error. API key is not set." if (API_KEY == "") else "City not found."

# Commands ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def ExecuteCommand(filterResult):
    global isWoke
    global errorCode

    errorCode = ""
    tts = "Something went wrong. This shouldn't have happened."

    # Listen for wakeword
    if (filterResult == 1):
        isWoke = True
        tts = "Hello"

    # Return error if the system is not WOKE and a command was heard
    elif (isWoke == False):
        errorCode = "Not woke"
        return False

    # Return error when no command was heard
    elif (filterResult == 0):
        errorCode = "No such command"
        tts = "I don't know what that means."
    
    # Execute heard command
    if errorCode == "" and filterResult != 1:
        # Get arguments from heard speech if there are any
        # NOTE: The current system just fills in bullshit strings so the function call doesn't fuck over
        args = ""
        paramNames, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(eval(commands[filterResult]))

        if len(paramNames) > 0:
            args += "'"
            for n in range(len(paramNames)):
                args += (paramNames[n])
                if len(paramNames) > n + 1:
                    args += "', '"
            args += "'"

        # Call the command function
        tts = eval(commands[filterResult] + "(" + args + ")")
    
    # Text-To-Speech
    Speak(tts)

    return errorCode == ""

# this is called from the background thread
def ProcessAudio(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        text = recognizer.recognize_google(audio)
        filterResult = FilterCommands(text)
        print(text)
        #print(text + " [ Detected command: " + str(filterResult) + " ]")

        succeeded = ExecuteCommand(filterResult)

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
