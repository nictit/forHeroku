#for future make ship as an class with objects of ships
import requests
import bs4
import telebot
from requests import get
from bs4 import BeautifulSoup
import os
from flask import Flask, request
import logging

#required initializing parameters
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
token = '5048232576:AAHKQXWuVI-KIFQOEsDEizTGo9A1Ahjk4cw'

# read ships.csv file and make tuples with norway and canadian ships
# each of them contain 3 parameters: country, c/s, mmsi
def fileReader():
    nor_ships = [['NOR', 'JWAO', 257012200],
                 ['NOR', 'LABN', 259041000],
                 ['NOR', 'JWCD', 259047000],
                 ['NOR', 'LBDA', 259014000],
                 ['NOR', 'LABS', 259043000],
                 ['NOR', 'LBDV', 259018000],
                 ['NOR', 'LBDB', 259015000],
                 ['NOR', 'LAQL', 259317000],
                 ['NOR', 'LASE', 257736000],
                 ['NOR', 'JWBR', 259050000],
                 ['NOR', 'LBHH', 257079200],
                 ['NOR', 'LBDW', 259019000]]
    cdn_ships = [['CDN', 'CGAX', 316296000],
                 ['CDN', 'CGAS', 316011116],
                 ['CDN', 'CGAV', 316113000],
                 ['CDN', 'CGAN', 316143000],
                 ['CDN', 'CGAE', 316148000],
                 ['CDN', 'CGAP', 316138000],
                 ['CDN', 'CGJC', 316294000],
                 ['CDN', 'CGJI', 316267000],
                 ['CDN', 'CGBT', 316014510],
                 ['CDN', 'CGJG', 316259000],
                 ['CDN', 'CGJJ', 316295000],
                 ['CDN', 'CGAZ', 316192000],
                 ['CDN', 'CGAR', 316160000],
                 ['CDN', 'CGBV', 316200000],
                 ['CDN', 'CGAY', 316191000],
                 ['CDN', 'CGAL', 316158000]]

    return nor_ships, cdn_ships

#input - mmsi code from tuples nor_ship and cdn_ship
#output - html code of the ship page with info about its c/s,
#position etc
def getPageSource(mmsi):
    url = 'https://www.vesselfinder.com/vessels?name=' + str(mmsi)
    response = get(url, headers=HEADERS, timeout=None)
    soup = BeautifulSoup(response.content, features='lxml')
    address = soup.find('a', attrs={'class':'ship-link'})
    url = 'https://www.vesselfinder.com' + address['href']
    response = get(url, headers=HEADERS, timeout=None)
    return BeautifulSoup(response.content, features='lxml')

# get c/s, position, time from source in minutes
def getInfo(page_source):
    ship_location = page_source.find('p', attrs={'class':'text2'}).text
    first_coordinate = ship_location[ship_location.find('coordinates') + len('coordinates') + 1:ship_location.find('/', ship_location.find('coordinates'))-1]
    second_coordinate = ship_location[ship_location.find('/',ship_location.find('coordinates')) + 1:ship_location.find(')', ship_location.find('coordinates'))]
    ship_callsign_and_time = page_source.find('table', attrs={'class': 'aparams'}).text
    callsign = ship_callsign_and_time[ship_callsign_and_time.find('Callsign') + len('Callsign'):ship_callsign_and_time.find('Callsign') + len('Callsign') + 4]
    if not (callsign.isalpha() and callsign.isupper() and len(callsign)==4):
        callsign = 'error'
    time = ship_callsign_and_time[ship_callsign_and_time.find('Position received') + len('Position received') + 1:ship_callsign_and_time.find('ago') + 3]
    time = timeconventer(time)
    first_coordinate,  second_coordinate = decToDegree(first_coordinate,second_coordinate)
    ship_info = [callsign, first_coordinate, second_coordinate, time]
    return ship_info

def timeconventer(time: str):
    if 'min' in time:
        time = str([int(s) for s in time.split() if s.isdigit()][0])
        return (time)
    elif 'hour' in time:
        time = str([int(s) for s in time.split() if s.isdigit()][0])
        return (str(int(time) * 60))
    elif 'day' in time:
        time = str([int(s) for s in time.split() if s.isdigit()][0])
        return (str(int(time) * 1440))

# conversion of coordinates
def decToDegree(first_coordinate_dec,second_coordinate_dec):
    minutes1, sec1 = divmod(float(first_coordinate_dec[:-2]) * 3600, 60)
    deg1, minutes1 = divmod(minutes1, 60)
    minutes2, sec2 = divmod(float(second_coordinate_dec[:-2]) * 3600, 60)
    deg2, minutes2 = divmod(minutes2, 60)
    first_coordinate_degree = str(round(deg1)) + u"\u00b0" + str(round(minutes1)) + "'" + str(round(sec1)) + '"' + first_coordinate_dec[-2:]
    second_coordinate_degree = str(round(deg2)) + u"\u00b0" + str(round(minutes2)) + "'" + str(round(sec2)) + '"' + second_coordinate_dec[-2:]
    return first_coordinate_degree, second_coordinate_degree

def output(ship):
    ship[3] = int(ship[3])
    if ship[3] >= 1440:
        ship[3] = round(ship[3] / 1440)
        out = ship[0] + ': ' + ship[1] + ' ' + ship[2] + ' (' + str(ship[3]) + ' days ago)'
    elif ship[3] > 60:
        ship[3] = round(ship[3] / 60)
        out = ship[0] + ': ' + ship[1] + ' ' + ship[2] + ' (' + str(ship[3]) + ' hr ago)'
    else:
        out = ship[0] + ': ' + ship[1] + ' ' + ship[2] + ' (' + str(ship[3]) + ' min ago)'
    return out


def main():
    nor_ships_info = []
    cdn_ships_info = []
    nor_ships, cdn_ships = fileReader()

# add time filter: if last ship posotion recieved > 15 hr *60 = 900 min ago then delete it
    for ship in nor_ships:
        nor_ships_info.append(getInfo(getPageSource(ship[2])))
        print('1')
    nor_ships_info = sorted(nor_ships_info, key= lambda x: int(x[3]))

    for ship in cdn_ships:
        cdn_ships_info.append(getInfo(getPageSource(ship[2])))
        print('2')
    cdn_ships_info = sorted(cdn_ships_info, key= lambda x: int(x[3]))

    nor = ''
    cdn = ''
    for ship in nor_ships_info[:4]:
        nor += output(ship)
        nor += '\n'
    for ship in cdn_ships_info[:4]:
        cdn += output(ship)
        cdn += '\n'
    all = nor + '\n' + cdn
    return all

bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, 'уже ищу...')
    bot.send_message(message.chat.id, main())


if "HEROKU" in list(os.environ.keys()):
    logger = telebot.logger
    telebot.logger.setLevel(logging.INFO)

    server = Flask(__name__)
    @server.route("/bot", methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200
    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url="https://marinefinder.herokuapp.com/bot")
        return "?", 200
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 80))
else:
    bot.remove_webhook()
    bot.polling(none_stop=True)
