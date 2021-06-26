langID_fin_home1 = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\MSTTS_V110_fiFI_Heidi" #finnish TTS
#langID_eng_home1 = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0" #english_US TTS
#langID_fin_sskky1 = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\MSTTS_V110_fiFI_Heidi" #finnish TTSimport speech_recognition as sr

import time
import speech_recognition as sr
import pywhatkit

# this is called from the background thread
def ProcessAudio(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        print(recognizer.recognize_google(audio))
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


r = sr.Recognizer()
m = sr.Microphone()

r.energy_threshold = 200 # energy level threshold for sounds. Values below this threshold are considered silence
r.pause_threshold = 0.5 # minimum length of silence (in seconds) that will register as the end of a phrase
phrase_time = 3 # maximum time in seconds the recognizer will listen to a phrase before cutting off

with m as source:
    r.adjust_for_ambient_noise(source)  # we only need to calibrate once, before we start listening

print("Listening for speech...")

# start listening in the background (note that we don't have to do this inside a `with` statement)
stop_listening = r.listen_in_background(source=m, callback=ProcessAudio, phrase_time_limit=phrase_time)
# `stop_listening` is now a function that, when called, stops background listening

# Right here we can do other shit. The system will keep listening even if we freeze the thread by looping and stuff

# calling this function requests that the background listener stop listening
#stop_listening(wait_for_stop=False)

#print("Stopped listening")

# do some more unrelated things
while True: time.sleep(0.1)  # we're not listening anymore, even though the background thread might still be running for a second or two while cleaning up and stopping
