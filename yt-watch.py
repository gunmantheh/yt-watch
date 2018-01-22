"""
Created by Pavel Polák
"""

import configparser
import logging
import re
import subprocess
import win32clipboard
from threading import Thread
from loggingHelp import LogHelper
import datetime, time

LIVESTREAMER = "livestreamer"
YOUTUBE = "youtube"
MPV = "mpv"
TWITCH = "twitch"
MAIN = "main"
MESSAGES = "messages"
LOGTOFILE = "logtofile"

config = configparser.ConfigParser()
config.read('config.ini')
if config[YOUTUBE] is None:
    print("Youtube has invalid configuration")
    exit(2)
if config[MPV] is None and config[LIVESTREAMER] is None:
    print("At least one player has to be setup")
    exit(3)

formatter = logging.Formatter('%(time)s - %(name)s - %(levelname)s - thread: %(thread)d - %(message)s')

levelOfDebugging = logging.ERROR

if config[MAIN] and config[MAIN][MESSAGES]:
    switch = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    levelOfDebugging = switch.get(config[MAIN][MESSAGES], logging.ERROR)

logger = logging.getLogger('yt-watch')
logger.setLevel(levelOfDebugging)

ch = logging.StreamHandler()
ch.setLevel(levelOfDebugging)
ch.setFormatter(formatter)
logger.addHandler(ch)

if config[MAIN] and config[MAIN][LOGTOFILE] and config[MAIN][LOGTOFILE].lower() == "yes":
    fh = logging.FileHandler(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H-%M-%S') + ".log")
    fh.setLevel(levelOfDebugging)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

lh = LogHelper(logger)

class Player:
    def __init__(self, player, clipboard, website, url, regEx):
        self.player = player
        self.clipboard = clipboard
        self.website = website
        self.url = url
        self.regEx = regEx

    def Play(self):
        if not self.player:
            return False
        match = re.search(self.regEx, self.clipboard)
        if match and match.group(6):
            videoId = match.group(6)
            if videoId is not None:
                lh.logd("{0} matched".format(self.website))
                if self.player == MPV:
                    lh.logd("starting {0} via {1}".format(self.website, self.player))
                    Thread(target=self.runPlayer, args=(([config[MPV]["bin"],
                                                     self.url + videoId,
                                                     config[MPV]["quality"]]),)).start()
                    return True
                else:
                    if self.player == LIVESTREAMER:
                        lh.logd("starting {0} via {1}".format(self.website, self.player))
                        Thread(target=self.runPlayer, args=(([config[LIVESTREAMER]["bin"],
                                                         self.url + videoId,
                                                         config[LIVESTREAMER]["quality"],
                                                         "-p " + config[LIVESTREAMER]["player"]]),)).start()
                        return True
        lh.logd("{0} didn't match".format(self.website))
        return False

    def runPlayer(self, arguments):
        try:
            lh.logStart()
            lh.logVideo(arguments[1])
            lh.logd(arguments)
            subprocess.run(arguments, shell=True, stderr=subprocess.PIPE)
            lh.logFinish()
        except Exception as e:
            lh.logError(e)

class youtube(Player):
    def __init__(self, player, clipboard):
        self.website = YOUTUBE
        self.url = "https://www.youtube.com/watch?v="
        self.regEx = "(http)(s?)(:\/\/)(www\.)?(youtube\.com\/watch\?v\=)(.*)"
        Player.__init__(self, player, clipboard, self.website, self.url, self.regEx)

class twitch(Player):
    def __init__(self, player, clipboard):
        self.website = TWITCH
        self.url = "https://www.twitch.tv/"
        self.regEx = "(http)(s?)(:\/\/)(www\.)?(twitch\.tv\/)(.*)"
        Player.__init__(self, player, clipboard, self.website, self.url, self.regEx)

def matchYoutube(clipboard):
    lh.logd("matching {0}".format(YOUTUBE))
    player = config[YOUTUBE]["player"]
    return youtube(player, clipboard).Play()

def matchTwitch(clipboard):
    lh.logd("matching {0}".format(TWITCH))
    player = config[TWITCH]["player"]
    return twitch(player, clipboard).Play()


def matchClipboard(clipboard):
    if not matchYoutube(clipboard):
        if not matchTwitch(clipboard):
            lh.logd("nothing matched")
            return False  # Nothing matches
    return True  # Something matched


def main():
    clipboard, lastClipboard = "", ""
    clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)

    while True:
        try:
            time.sleep(1)
            clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)
            if lastClipboard != clipboard:
                lh.logChange(lastClipboard, clipboard)
                matchClipboard(clipboard)
            lastClipboard = clipboard
        except KeyboardInterrupt:
            print("Exiting")
            exit(0)


def GetClipboard(clipboard, lastURL):
    win32clipboard.OpenClipboard()
    try:
        clipboard = win32clipboard.GetClipboardData()
    except TypeError:
        clipboard = "invalidData"
        lastURL = clipboard
    win32clipboard.CloseClipboard()
    return clipboard, lastURL


if __name__ == "__main__":
    main()
