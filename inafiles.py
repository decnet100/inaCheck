import os
from datetime import datetime

from inadefChecker.inaconf import inaconf


def badcharremove(value):
    deletechars = '\/:*?"<>| '
    for c in deletechars:
        value = value.replace(c, '_')
    return value;


def getloc(locations, number):
    val = ''
    locnr = ''
    for loc in locations:
        if loc[0] == number:
            val = '_' + badcharremove(loc[2].strip())
            locnr = str(loc[1])
            break
    return val, locnr


def getlocationdata(locations, number):
    locdata = None
    for loc in locations:
        if loc[0] == number:
            locdata = loc
            break
    return locdata


def dircreate(dirName, maindir=inaconf.maindir):
    if not os.path.exists(os.path.join(maindir, dirName)):
        os.mkdir(os.path.join(maindir, dirName))
        inaconf.logprint("Directory ", dirName, " Created ")
    else:
        inaconf.logprint("Directory ", dirName, " already exists")


def get_camdir(camnr):
    maindir = inaconf.maindir
    loc = getlocationdata(inaconf.get_camlocations(), camnr)
    for thing in os.listdir(maindir):
        if os.path.isdir(os.path.join(maindir, thing)) and thing[0:7] == 'cam_%d_%d' % (loc[1], camnr):
            return os.path.join(maindir, thing)


def dirlocationchange():
    maindir = inaconf.maindir
    locations = inaconf.get_camlocations()
    for thing in os.listdir(maindir):
        if os.path.isdir(os.path.join(maindir, thing)) and thing[0:4] == 'cam_':
            camnr = int(os.path.basename(thing)[6])
            camloc, locnr = getloc(locations, camnr)
            newname = 'cam_%s_%d%s' % (locnr, camnr, camloc)
            if newname != thing:
                try:
                    os.rename(os.path.join(maindir, thing), os.path.join(maindir, newname))
                    print('renamed directory %s to %s' % (os.path.join(maindir, thing), newname))
                except:
                    print('can''t rename right now. Will try later.')


def checkstart(camnumber=0, maindir=inaconf.maindir):
    startfile = os.path.join(maindir, get_camdir(camnumber), 'startdate.txt')
    if os.path.isfile(startfile):
        with open(startfile) as f:
            datestr = f.readline()
        f.close()
        if len(datestr) > 9:
            date = datetime.strptime(datestr, '%Y_%m_%d')
        else:
            date = datetime.now()
        return date


def read_timedate_from_filename(file):
    filedate = datetime.strptime(os.path.splitext(os.path.basename(file))[0], inaconf.datefilefmt)
    time = filedate.time()
    date = filedate.date()

    return time, date


def read_reflectorpos(cam=0):
    defaultreflectors = [[1, 113, 297, 20], [5, 242, 448, 20]]
    maindir = inaconf.maindir
    reffile = os.path.join(maindir, get_camdir(cam), 'reflector_pos.txt')
    ref = []
    if os.path.isfile(reffile):
        with open(reffile) as f:
            lines = f.readlines()
        f.close()

        for line in lines:
            if len(line) > 0:
                ref.append(line.split(sep=','))
    else:
        with open(reffile, 'w+') as f:
            for default in defaultreflectors:
                if default[0] == cam:
                    f.write('%d, %d, %d' % (default[1], default[2], default[3]))
                    ref.append(default[1:3])
        f.close()
    return ref
