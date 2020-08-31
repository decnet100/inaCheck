# INADEF Configurations
# Stores and delivers stuff such as directories, input formats...

import os
from datetime import datetime


class mailerconf:
    maindir = ''
    camlocations = []

    def __init__(self, dir):
        mailerconf.maindir = dir

    def main():
        return self.maindir

    @staticmethod
    def set_datelogfmt(fmt):
        mailerconf.datelogfmt = fmt

    @staticmethod
    def set_dateexiffmt(fmt):
        mailerconf.dateexiffmt = fmt

    @staticmethod
    def set_datefilefmt(fmt):
        mailerconf.datefilefmt = fmt

    @staticmethod
    def set_battcrop(crop):
        mailerconf.battcrop = crop

    @staticmethod
    def get_camlocations():
        if len(mailerconf.camlocations) < 1:
            filepath = os.path.join(mailerconf.maindir, 'camlocations.txt')
            with open(filepath, 'r') as f:
                data = f.readlines()
            for line in data:
                csv = line.split(',')
                mailerconf.camlocations.append([int(csv[0].strip()), csv[1].strip()])
        return mailerconf.camlocations

    @staticmethod
    def logprint(*text):
        print(*text)
        logfile = os.path.join(mailerconf.maindir, 'log.txt')
        with open(logfile, 'a+') as f:
            f.write(datetime.now().strftime(mailerconf.datelogfmt) + ' - ')
            print(*text, file=f)
        f.close()
