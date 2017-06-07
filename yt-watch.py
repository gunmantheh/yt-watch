from threading import Thread
import configparser
import datetime
import re
import subprocess
import time
import win32clipboard
import logging

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
if (config[MPV] is None and config[LIVESTREAMER] is None):
    print("At least one player has to be setup")
    exit(3)

formatter = logging.Formatter('%(time)s - %(name)s - %(levelname)s - thread: %(thread)d - %(message)s')

levelOfDebugging = logging.DEBUG

if config[MAIN] and config[MAIN][MESSAGES]:
    switch = {
        "debug" : logging.DEBUG,
        "info" : logging.INFO,
        "warning" : logging.WARNING,
        "error" : logging.ERROR,
        "critical" : logging.CRITICAL
    }
    levelOfDebugging = switch.get(config[MAIN][MESSAGES], logging.INFO)

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

class Player():
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
        if (match and match.group(6)):
            videoId = match.group(6)
            if videoId is not None:
                logd("{0} matched".format(self.website))
                if self.player == MPV:
                    logd("starting {0} via {1}".format(self.website, self.player))
                    Thread(target=runPlayer, args=(([config[MPV]["bin"],
                                                     self.url + videoId,
                                                     config[MPV]["quality"]]),)).start()
                    return True
                else:
                    if self.player == LIVESTREAMER:
                        logd("starting {0} via {1}".format(self.website, self.player))
                        Thread(target=runPlayer, args=(([config[LIVESTREAMER]["bin"],
                                                         self.url + videoId,
                                                         config[LIVESTREAMER]["quality"],
                                                         "-p " + config[LIVESTREAMER]["player"]]),)).start()
                        return True
        logd("{0} didn't match".format(self.website))
        return False


def log(action):
    if logger.isEnabledFor(logging.INFO):
        logger.info("Action %s", action, extra=GetExtraArguments())

def logd(action):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Action %s", action, extra=GetExtraArguments())

def logStart():
    log("Starting")

def logFinish():
    log("Finished")

def logStop():
    log("Stopped")

def logError(exception):
    if logger.isEnabledFor(logging.ERROR):
        logger.error("Error: %s", exception, extra=GetExtraArguments())

def logVideo(url):
    if logger.isEnabledFor(logging.INFO):
        logger.info("Playing video %s", url, extra=GetExtraArguments())

def logChange(oldClipboard, newClipboard):
    if logger.isEnabledFor(logging.INFO):
        logger.info("Clipboard changed from \"%s\" to \"%s\"", oldClipboard, newClipboard, extra=GetExtraArguments())

def GetExtraArguments():
    arguments = {"time": datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}
    return arguments

def runPlayer(arguments):
    try:
        logStart()
        logVideo(arguments[1])
        logd(arguments)
        process = subprocess.run(arguments, shell=True, stderr=subprocess.PIPE)
        logFinish()
    except Exception as e:
        logError(e)

def matchYoutube(clipboard):
    website = YOUTUBE
    url = "https://www.youtube.com/watch?v="
    logd("matching {0}".format(website))
    player = config[YOUTUBE]["player"]
    regEx = "(http)(s?)(:\/\/)(www\.)?(youtube\.com\/watch\?v\=)(.*)"
    return Player(player, clipboard, website, url, regEx).Play()

def matchTwitch(clipboard):
    website = TWITCH
    url = "https://www.twitch.tv/"
    logd("matching {0}".format(website))
    player = config[TWITCH]["player"]
    regEx = "(http)(s?)(:\/\/)(www\.)?(twitch\.tv\/)(.*)"
    return Player(player, clipboard, website, url, regEx).Play()


def matchClipboard(clipboard):
    if not matchYoutube(clipboard):
        if not matchTwitch(clipboard):
            logd("nothing matched")
            return False # Nothing matches
    return True # Something matched


def main():

    clipboard, lastClipboard = "", ""
    clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)

    while(True):
        try:
            time.sleep(1)
            clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)
            if (lastClipboard != clipboard):
                logChange(lastClipboard,clipboard)
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