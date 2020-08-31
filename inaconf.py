# INADEF Configurations
# Stores and delivers stuff such as directories, input formats...

import os
from datetime import datetime


class inaconf:
    maindir = ''
    camlocations = []

    def __init__(self, dir):
        inaconf.maindir = dir

    def main():
        return self.maindir

    @staticmethod
    def set_datelogfmt(fmt):
        inaconf.datelogfmt = fmt

    @staticmethod
    def set_dateexiffmt(fmt):
        inaconf.dateexiffmt = fmt

    @staticmethod
    def set_datefilefmt(fmt):
        inaconf.datefilefmt = fmt

    @staticmethod
    def set_battcrop(crop):
        inaconf.battcrop = crop

    @staticmethod
    def get_camlocations():
        if len(inaconf.camlocations) < 1:
            filepath = os.path.join(inaconf.maindir, 'cam_locations.txt')
            if os.path.isfile(filepath):
                with open(filepath, 'r') as f:
                    data = f.readlines()
                for line in data:
                    csv = line.split(',')
                    inaconf.camlocations.append([int(csv[0].strip()), int(csv[1].strip()), csv[2].strip()])
        return inaconf.camlocations

    @staticmethod
    def logprint(*text):
        print(*text)
        logfile = os.path.join(inaconf.maindir, 'log.txt')
        with open(logfile, 'a+') as f:
            f.write(datetime.now().strftime(inaconf.datelogfmt) + ' - ')
            print(*text, file=f)
        f.close()
