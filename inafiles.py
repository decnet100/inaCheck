import os
from datetime import datetime, timedelta
from pandas import read_csv
import pandas as pd
import inaimage, inamailer
from inaconf import inaconf


def badcharremove(value):
    deletechars = '\/:*?"<>| '
    for c in deletechars:
        value = value.replace(c, '_')
    return value;

def getclearloc(locations, camnumber): #delivers location data in clear text as it appears in location file
    val = ''
    locnr = ''
    for loc in locations:
        if loc[0] == camnumber:
            val = loc[2].strip()
            locnr = str(loc[1])
            break
    return val, locnr

def getlocname(locations, locnr):
    #locations = readlocations()
    i = int(locnr)
    val = ''
    for loc in locations:
        if loc[0] == i:
            val = loc[1].strip()
            break
    return val

def getlocname(locnr):
    locations = readlocations()
    i = int(locnr)
    val = ''
    for loc in locations.iterrows():
        if loc[1]['location'] == i:
            val = loc[1]['name'].strip()
            break
    return val


def getlocationfrommeteo(devicesn):
    meteo = readmeteo()
    if len(meteo)> 0:
        locnr = int(meteo['devicesn'==devicesn]['location'])
    else:
        locnr = 0
    return locnr

def getloc(locations, camnumber): #reformats location data to OS-Path compatible string
    val, locnr = getclearloc(locations,camnumber)
    val = '_' + badcharremove(val.strip())
    return val, locnr


def getlocationdata(locations, camnumber):
    locdata = None
    for loc in locations:
        if loc[0] == camnumber:
            locdata = loc
            break
    return locdata

def readlocations():
    locationfile = os.path.join(inaconf.maindir, 'locations.txt')

    locations = readDataframe(locationfile)
    return locations

def is_caminputfile(file):
    return (len(os.path.splitext(os.path.basename(file))[0]) == 19 and os.path.splitext(os.path.basename(file))[1].lower() == '.jpg')

def get_comparisons(imagefile, nclosest=5):
    time_day = inafiles.time_date_from_file(imagefile)
    possible = []
    path =os.path.dirname(imagefile)
    for compfile in os.listdir(path):
        if os.path.splitext(compfile)[1].lower() == '.jpg' and len(os.path.splitext(compfile)[0]) == 19:
            # if not ('_dil' in compfile or '_ds' in compfile or 'edge' in compfile or 'plot' in compfile):
            compfullfile = os.path.join(path, compfile)
            val = inafiles.time_date_from_file(compfile)
            possible.append([compfullfile, val[0], val[1]])
    df = pd.DataFrame(possible, columns=['file', 'time', 'day'])

    res = []
    for comp in df[::-1].iterrows():
        if len(comp) > 1:
            if os.path.basename(comp[1]['file']) != os.path.basename(imagefile) and abs(time_day[0].hour - comp[1]['time'].hour) < 2:
                res.append(comp)
            if (len(res) >= nclosest):
                break

    return res

def daycompare(file):
    comparisons = get_comparisons(file)
    for comp in comparisons:
        values = inaimage.daycheck(file, comp[1]['file'])
        print(comp[1], values)
        results.append(values)


def getcurrentfiles(camnr):
    all = []
    path = get_camdir(int(camnr))
    if os.path.isdir(path):
        for file in os.listdir(path):
            if is_caminputfile(file):
                filedate = datetime_from_file(file)
                if filedate <= datetime.now():
                    all.append({'date': filedate,'file': os.path.join(path,file)})
    all.sort(key=lambda item:item['date'], reverse=True)
    n = inaconf.lastn
    return all[0:n]

def getactivecams():
    activecams= readlinelistfile(os.path.join(inaconf.maindir, 'activecams.txt'))
    return activecams

def gapcheck(lastfiles):
    prevdate = datetime.now()
    now = prevdate
    prevfile = ''
    latestfile = ''
    latestdate = datetime.min
    gaps = []

    for file in lastfiles:
        if prevdate < now:
            if (max(file['date'],prevdate) - min(file['date'],prevdate)) > timedelta(hours=25):
                newgap = {**file, 'prevdate': prevdate, 'prevfile': prevfile}
                gaps.append(newgap)
        prevdate = file['date']
        prevfile = file['file']
        if latestdate < prevdate:
            latestfile, latestdate = prevfile, prevdate
    if (now - latestdate) > timedelta(hours=25):
        newgap = {'date': now, 'file': '', 'prevdate': latestdate, 'prevfile': latestfile}
        gaps.append(newgap)

    return gaps


def getZentraLogin():
    maindir = inaconf.maindir
    loginfile = os.path.join(maindir, 'zentra.txt')
    #login = read_csv(loginfile, delimiter=';')
    login = readDataframe(loginfile)
    return login

def readlinelistfile(file, delimiter=';'):
    list = []
    if os.path.isfile(file):
        with open(file,'r') as f:
            lines = f.readlines()
    for line in lines:
        line = line.rstrip('\n')
        list.append(line.split(delimiter))
    return list

def readDataframe(file, delimiter=';'):
    data = pd.DataFrame()
    if os.path.isfile(file):
        data = read_csv(file, delimiter)
    return data

def getmeteofromlocation(number):
    meteo = []
    data = readmeteo()
    if not data is None:
        for station in data.iterrows():
            if int(station[1]['location'])==number:
                meteo.append(station[1]['device_sn'])
    return meteo

def readmeteo():
    meteofile = os.path.join(inaconf.maindir, 'meteo_locations.txt')
    data = None
    if os.path.isfile(meteofile):
        data = readDataframe(meteofile)
    return data

def getlocationfrommeteo(devicesn):
    data = readmeteo()
    loc = []
    if not data is None:
        for station in data.iterrows():
            if station[1]['device_sn'].strip()==devicesn.strip():
                loc.append(int(station[1]['location']))
    return loc






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


def time_date_from_file(file):
    filedate = datetime_from_file(file)
    time = filedate.time()
    date = filedate.date()

    return time, date

def datetime_from_file(file):
    filedate = datetime.strptime(os.path.splitext(os.path.basename(file))[0], inaconf.datefilefmt)
    time = filedate.time()
    date = filedate.date()

    return filedate

def get_cam_receipients(camnr, default=''):
    maindir = inaconf.maindir
    filepath = os.path.join(maindir, 'audience_cam_%d.txt' % (camnr))
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            rec = f.readlines()
        actual_rec = []
        for receipient in rec:
            if len(receipient) != 0 and '@' in receipient and '.' in receipient:
                actual_rec.append(receipient.rstrip('\n'))
        if len(actual_rec) > 0:
            return actual_rec
        else:
            return default
    else:  # file not found
        with open(filepath, 'w+') as f:
            f.write(default + '\n')
        return default

def getmaildata():
    maindir = inaconf.maindir
    filepath = os.path.join(maindir, 'maildata.txt')
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            rec = f.readline()
    else:
        raise AssertionError
    vals = rec.split(',')
    return {'host': vals[0].strip(), 'mail': vals[1].strip(), 'pwd': vals[2].strip(), 'outhost': vals[3].strip()}

def getcammaildata(camnr):
    i = int(camnr)
    data = getmaildata()
    return{'host': data['host'], 'mail': data['mail']%i, 'pwd': data['mail']%i, 'outhost': data['outhost']}

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
