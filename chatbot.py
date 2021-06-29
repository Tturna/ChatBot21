langID_fin_home1 = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\MSTTS_V110_fiFI_Heidi" #finnish TTS
langID_eng_home1 = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0" #english_US TTS

import time
import speech_recognition as sr
import pywhatkit
import pyttsx3
import requests, json
import math
from googlesearch import search as google

WEATHER_REQUEST_URL = "https://api.openweathermap.org/data/2.5/weather?"

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

wakeWords = ["wakeword"]

errorCode = ""
ttsEngine = pyttsx3.init()

def FilterCommands(text):
    # This function will check if the argument text has any commands in it

    for w in wakeWords:
        if w in text:
            # Wakeword detected
            return FILRES_WAKEWORD

    if "Google" in text or "google" in text:
        # Google search command detected
        return FILRES_GOOGLE

    if "Wikipedia" in text or "wikipedia" in text or "wiki" in text:
        # Wikipedia search command detected
        return FILRES_WIKIPEDIA

    if "Weather" in text or "weather" in text:
        # Get weather of specified city
        return FILRES_WEATHER

    if "Time" in text or "time" in text:
        # Time check command detected
        return FILRES_TIME

    if "Calculate" in text or "calculate" in text:
        # Calculation command detected
        return FILRES_CALC
    
    if "News" in text or "news" in text:
        # News check command detected
        return FILRES_NEWS

    # No command detected
    return FILRES_NONE

# Commands ------------------------------------------------------------------------
def GetTime():
    cTime = time.localtime()
    return "The time is " + str(cTime.tm_hour) + ":" + str(cTime.tm_min) 

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
        return CITY + " weather: " + str(report[0]['description']) + ", " + str(rounded_temp) + " degrees at a humidity of" + str(humidity) + " %"
    else:
        return "City not found"

def ExecuteCommand(filterResult):
    tts = "fuck, it didn't work"
    if (filterResult == FILRES_NONE):
        return False
    elif (filterResult == FILRES_GOOGLE):
        #tts = GoogleSearch(query)
        pass
    elif (filterResult == FILRES_WIKIPEDIA):
        #tts = WikipediaSearch(query)
        pass
    elif (filterResult == FILRES_TIME):
        tts = GetTime()
        pass
    elif (filterResult == FILRES_CALC):
        #tts = Calculate(equation)
        pass
    elif (filterResult == FILRES_NEWS):
        #tts = GetNews()
        pass
    elif (filterResult == FILRES_WEATHER):
        tts = GetWeather()
        pass
    else:
        return False
    
    # Text-To-Speech
    ttsEngine.say(tts)
    ttsEngine.runAndWait()

    return True

# this is called from the background thread
def ProcessAudio(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        text = recognizer.recognize_google(audio)
        filterResult = FilterCommands(text)
        print(text + " [ Detected command: " + str(filterResult) + " ]")

        succeeded = ExecuteCommand(filterResult)

        if (not succeeded):
            print(errorCode)

    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


r = sr.Recognizer()
m = sr.Microphone()

r.energy_threshold = 30 # energy level threshold for sounds. Values below this threshold are considered silence
r.pause_threshold = 0.5 # minimum length of silence (in seconds) that will register as the end of a phrase
phrase_time = 7.5 # maximum time in seconds the recognizer will listen to a phrase before cutting off

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

while True: time.sleep(0.1)
