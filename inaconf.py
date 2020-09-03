# INADEF Configurations
# Stores and delivers stuff such as directories, input formats...

import os
from datetime import datetime



class inaconf:
    maindir = ''
    camlocations = []
    lastn  = 1
    activecame = []

    def __init__(self, dir):
        inaconf.maindir = dir


    def preconfig():
        import inafiles, inaimage
        from inamailer import inamailer
        inaconf.activecams = [1, 5]
        datefilefmt = '%Y_%m_%d_%H.%M.%S'
        datelogfmt = '%Y.%m.%d %H.%M.%S'
        dateexiffmt = '%Y:%m:%d %H:%M:%S'
        inaconf.datehumanfmt ='%Y.%m.%d %H:%M'
        inaconf.datehumanshortfmt = '%m.%d %H:%M'
        inaconf.set_datelogfmt(datelogfmt)
        inaconf.set_datefilefmt(datefilefmt)
        inaconf.set_dateexiffmt(dateexiffmt)
        inaconf.set_battcrop([335, 465, 367, 478])
        inaconf.set_lastn(3)
        inaconf.battwarning = 0.3
        inaconf.meteoreportdays = 5
        mailer = inamailer()
        # locations = inaconf.get_camlocations()
        for i in inaconf.activecams:
            inafiles.dircreate('cam_%d' % i)
        inafiles.dirlocationchange()

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
    def set_lastn(n):
        inaconf.lastn = int(n)

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
