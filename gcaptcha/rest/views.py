from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json

#system libraries
import os
import random
import time

#selenium libraries
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

#recaptcha libraries
import speech_recognition as sr
import urllib
import pydub

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView


def delay():
    print("[INFO] delay")
    time.sleep(random.randint(3, 5))

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')


class Test(APIView):
    def get(self, request, *args, **kwargs):
        # create chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)

        delay()
        driver.get(
            "https://www.google.com/search?q=hello&oq=hello&aqs=chrome..69i57j69i59j69i60.821j0j1&sourceid=chrome&ie=UTF-8"
        )
        # go to website
        driver.get("https://www.gstatic.com/cloud-site-ux/vision/vision.min.html")
        delay()

        shadow_section = driver.execute_script('''return document.querySelector("vs-app").shadowRoot''')
        element = shadow_section.find_element_by_tag_name('input')
        driver.execute_script("document.getElementById('input').removeAttribute('hidden')")

        randNum = random.randint(1, 100)
        randImg = '{}.png'.format(randNum)
        element.send_keys(
            os.path.join(
                os.getcwd(),
                'gcaptcha',
                'rest',
                'images',
                randImg
            )
        )

        delay()

        # switch to recaptcha frame
        frames = driver.find_elements_by_tag_name("iframe")
        driver.switch_to.frame(frames[0])
        delay()

        # click on checkbox to activate recaptcha
        driver.find_element_by_class_name("recaptcha-checkbox-border").click()

        # switch to recaptcha audio control frame
        driver.switch_to.default_content()

        frames = driver.find_elements_by_tag_name("iframe")
        driver.switch_to.frame(frames[len(frames) - 1])
        delay()

        # click on audio challenge
        driver.find_element_by_id("recaptcha-audio-button").click()

        # switch to recaptcha audio challenge frame
        driver.switch_to.default_content()
        frames = driver.find_elements_by_tag_name("iframe")
        driver.switch_to.frame(frames[-1])
        delay()

        flag = True
        while flag:
            try:
                # click on the play button
                button_div = driver.find_element_by_class_name('rc-audiochallenge-play-button')
                button = button_div.find_element_by_class_name('rc-button-default')
                button.click()
                delay()
                # get the mp3 audio file
                src = driver.find_element_by_id("audio-source").get_attribute("src")
                print("[INFO] Audio src: %s" % src)
                # download the mp3 audio file from the source
                urllib.request.urlretrieve(src, os.getcwd() + "\\sample.mp3")
                sound = pydub.AudioSegment.from_mp3(os.getcwd() + "\\sample.mp3")
                sound.export(os.getcwd() + "\\sample.wav", format="wav")
                sample_audio = sr.AudioFile(os.getcwd() + "\\sample.wav")
                r = sr.Recognizer()

                with sample_audio as source:
                    audio = r.record(source)

                # translate audio to text with google voice recognition
                key = r.recognize_google(audio)
                print("[INFO] Recaptcha Passcode: %s" % key)
                time.sleep(1)
                # key in results and submit
                driver.find_element_by_id("audio-response").send_keys(key.lower())
                time.sleep(2)
                driver.find_element_by_id("audio-response").send_keys(Keys.ENTER)
                delay()
            except Exception as e:
                # pass
                print('[Exception]', e)
                driver.save_screenshot(os.path.join(
                    os.getcwd(),
                    'gcaptcha',
                    'rest',
                    'screenshots',
                    'error.png'
                ))
                flag = False
                driver.switch_to.default_content()
                delay()
        # HERE IS success image
        token = "Google mark as spam. Please try again later."
        for request in driver.requests:
            if 'https://cxl-services.appspot.com/proxy' in request.url:
                key = 'token='
                queryString = request.querystring
                index = queryString.index(key)
                token = queryString[index + len(key): len(queryString)]
                print(token)

        driver.close()
        return Response({
            "token": token
        })
