import logging
import datetime
import time

class LogHelper:
    def __init__(self, logger):
        self.logger = logger

    def log(self, action):
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Action %s", action, extra=self.GetExtraArguments())


    def logd(self, action):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Action %s", action, extra=self.GetExtraArguments())


    def logStart(self):
        self.log("Starting")


    def logFinish(self):
        self.log("Finished")


    def logStop(self):
        self.log("Stopped")


    def logError(self, exception):
        if self.logger.isEnabledFor(logging.ERROR):
            self.logger.error("Error: %s", exception, extra=self.GetExtraArguments())


    def logVideo(self, url):
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Playing video %s", url, extra=self.GetExtraArguments())


    def logChange(self, oldClipboard, newClipboard):
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info("Clipboard changed from \"%s\" to \"%s\"", oldClipboard, newClipboard, extra=self.GetExtraArguments())


    def GetExtraArguments(self):
        arguments = {"time": datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}
        return arguments