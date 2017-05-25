import _thread
import configparser
import datetime
import re
import subprocess
import time
import win32clipboard
import logging

formatter = logging.Formatter('%(time)s - %(name)s - %(levelname)s - thread: %(thread)d - %(message)s')

logger = logging.getLogger('yt-watch')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# fh = logging.FileHandler(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H-%M-%S') + ".log")
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)

def log(action):
    logger.info("Action %s", action, extra=GetExtraArguments())

def logStart():
    log("Starting")

def logFinish():
    log("Finished")

def logStop():
    log("Stopped")

def logError(exception):
    logger.error("Error: %s", exception, extra=GetExtraArguments())

def logVideo(url):
    logger.info("Playing video %s", url, extra=GetExtraArguments())

def logChange(oldClipboard, newClipboard):
    logger.info("Clipboard changed from \"%s\" to \"%s\"", oldClipboard, newClipboard, extra=GetExtraArguments())

def GetExtraArguments():
    arguments = {"time": datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}
    return arguments


def runPlayer(arguments):
    try:
        logStart()
        logVideo(arguments[1])
        subprocess.run(arguments, shell=True)
        logFinish()
    except Exception as e:
        logError(e)


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config["youtube"] is None:
        print("Youtube has invalid configuration")
        exit(2)
    if (config["mpv"] is None and config["livestreamer"] is None):
        print("At least one player has to be setup")
        exit(3)
    clipboard, lastClipboard = "", ""
    clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)

    while(True):
        try:
            time.sleep(1)
            clipboard, lastClipboard = GetClipboard(clipboard, lastClipboard)
            if (lastClipboard != clipboard):
                logChange(lastClipboard,clipboard)
                match = re.search("(http)(s?)(:\/\/)(www\.)?(youtube\.com\/watch\?v\=)(.*)", clipboard)
                if (match and match.group(6)):
                    videoId = match.group(6)
                    if videoId is not None:
                        if config["youtube"]["player"] == "mpv":
                            _thread.start_new_thread(runPlayer,
                             (([config["mpv"]["bin"],
                                "https://www.youtube.com/watch?v=" + videoId,
                                config["mpv"]["quality"]]),))
                        else:
                            if config["youtube"]["player"] == "livestreamer":
                                _thread.start_new_thread(runPlayer,
                                (([config["livestreamer"]["bin"],
                                "https://www.youtube.com/watch?v=" + videoId,
                                config["livestreamer"]["quality"],
                                "-p " + config["livestreamer"]["player"]]),))

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