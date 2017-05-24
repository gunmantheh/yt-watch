import _thread
import configparser
import datetime
import re
import subprocess
import time
import win32clipboard

def log(action):
    print(("[{0}] " + action + " thread {1}").format(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), _thread.get_ident()))

def logStart():
    log("Starting")

def logFinish():
    log("Finished")

def logStop():
    log("Stopped")

def logError(exception):
    print(("[{0}] Error in thread {1} - {2}").format(
        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), _thread.get_ident(), exception))

def logVideo(url):
    print(("[{0}] Playing video in thread {1} - {2}").format(
        datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), _thread.get_ident(), url))

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
    win32clipboard.OpenClipboard()
    lastURL = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    while(True):
        try:
            time.sleep(1)
            win32clipboard.OpenClipboard()
            clipboard = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            if (lastURL != clipboard):
                print("it changed {0}".format(clipboard))
                match = re.search("(http)(s?)(:\/\/)(www\.)?(youtube\.com\/watch\?v\=)(.*)", clipboard)
                if (match and match.group(6)):
                    videoId = match.group(6)
                    if videoId is not None:
                        if config["youtube"]["player"] == "mpv":
                            _thread.start_new_thread(runPlayer, (([config["mpv"]["bin"], "https://www.youtube.com/watch?v=" + videoId, config["mpv"]["quality"]]),))
                        else:
                            if config["youtube"]["player"] == "livestreamer":
                                _thread.start_new_thread(runPlayer, (([config["livestreamer"]["bin"],
                                                "https://www.youtube.com/watch?v=" + videoId,
                                                config["livestreamer"]["quality"],
                                                "-p " + config["livestreamer"]["player"]]),))

            lastURL = clipboard
        except KeyboardInterrupt:
            print("Exiting")
            exit(0)

if __name__ == "__main__":
    main()