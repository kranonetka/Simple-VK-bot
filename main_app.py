from flask import Flask, request, abort
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bs4 import BeautifulSoup
import requests
import random
from multiprocessing import Process
import json


app = Flask(__name__)


confirmation_token = "confirmation_token"
token = "token"
secret = "secret"
group_id = 666
bot_session = vk_api.VkApi(token=token)
bot_api = bot_session.get_api()


def get_weather(city="tomsk"):
	page = requests.get(r"https://yandex.ru/pogoda/" + city.lower())
	soup = BeautifulSoup(page.text, "lxml")
	weather = dict()
	weather["city"] = soup.find("h1", {"class": "title title_level_1 header-title__title"}).text
	wrap = soup.find("div", {"class": "fact__temp-wrap"})
	wrap = wrap.contents[0]
	weather["time"] = wrap.contents[0].text
	weather["temp"] = wrap.contents[1].contents[0].text
	weather["feel"] = wrap.contents[3].contents[0].text
	weather["feel temp"] = wrap.contents[3].contents[1].contents[1].contents[0].contents[0].text
	return weather


def get_random_button_color():
	return random.choice(tuple(VkKeyboardColor))


def event_handler(event):
	if event["type"] == "message_new":
		keyboard = VkKeyboard(one_time = False)
		keyboard.add_button(label="Убери", color=get_random_button_color())
		keyboard.add_line()
		keyboard.add_button(label="Погода", color=get_random_button_color())
		if "Убери" in event["object"]["text"]:
			msg = "Да пожалуйста"
			keyboard = VkKeyboard(one_time = False)
			keyboard.keyboard["buttons"] = []
		elif "Погода" in event["object"]["text"]:
			weather = get_weather()
			msg = ""
			msg += weather["city"] + "\n"
			msg += weather["time"] + "\n"
			msg += weather["temp"] + "\n"
			msg += weather["feel"] + "\n"
			msg += "Ощущается как " + weather["feel temp"]
		bot_api.messages.send(
			random_id	=	random.getrandbits(32),
			peer_id		=	event["object"]["peer_id"],
			message		=	msg,
			keyboard	=	keyboard.get_keyboard(),
			reply_to	=	event["object"]["id"]
			)


@app.route("/vk_bot", methods=["POST"])
def vk_callback():
    try:
        event = json.loads(request.data)
    except:
        abort(500)
		
    print({key:val for key, val in event.items() if key != "secret"})
	
    if "type" not in event and "group_id" not in event:
        abort(404)
		
    if event["type"] == "confirmation" and event["group_id"] == group_id:
        return confirmation_token
		
    if event["secret"] != secret:
        abort(401)
		
    proc = Process(target=event_handler, args=(event,))
    proc.daemon = True
    proc.start()
	
    return "ok"
