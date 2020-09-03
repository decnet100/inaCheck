from zentra.api import *
import os
from datetime import datetime, timedelta, date, timezone
import pandas as pd
from inadefChecker import inafiles
from inadefChecker.inaconf import inaconf
import matplotlib.dates as mdates
from matplotlib import pyplot



def login():

    logindata = inafiles.getZentraLogin()
    token = ZentraToken(username=logindata['username'][0], password=logindata['password'][0])
    return token

def read_data(token, device_sn, start_time, end_time):
    start = datetime.fromtimestamp(start_time)
    end = datetime.fromtimestamp(end_time)
    print('Requesting data from Zentra Cloud for %s, from %s - %s'%(device_sn, start, end))
    print('This might take a loooooong while... Zentra Cloud is not exactly a rocketship.')
    readings = ZentraReadings(sn=device_sn, token=token, start_time=start_time, end_time=end_time)
    return readings
# Report the readings from the first ZentraTimeseriesRecord

def read_precip(token, device_sn, start_time, end_time):
    # readings = read_data(token, device_sn,start_time,end_time)
    # data = pd.DataFrame(readings.timeseries[0].values)
    # precip_criterium = data['description'] == 'Precipitation'
    # precip_data = data[precip_criterium]
    # return precip_data
    return read_criterium(token, device_sn, start_time, end_time, 'Precipitation')
def read_batt(token, device_sn, start_time, end_time):
    return read_criterium(token, device_sn, start_time, end_time, 'Battery Percent')
def read_criterium(token, device_sn, start_time, end_time, criterium):
    readings = read_data(token, device_sn, start_time, end_time)
    data = pd.DataFrame(readings.timeseries[0].values)
    filter_criterium = data['description'] == criterium
    data = data[filter_criterium]
    return data

def saveplot(data, devicesn, filename):
    #grouped = data.groupby(data['dt'].dt.hour, as_index=False)['value'].sum().plot(kind='bar', x='datetime')
    #data.plot(x='datetime', y='value')
    #data.plot(x='datetime',y='rolling')
    #pyplot.show()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    lastmonth = (data['datetime'] > start) & (data['datetime'] <= end)
    data = data.loc[lastmonth]
    grouped = data.groupby(data['datetime'].dt.date)['value'].apply(lambda x: x.sum())
    grouped.plot(kind='bar', y='value', title='%s 24h sum'%(devicesn))
    pyplot.savefig(filename)
    return filename
    #grouped2 = data.groupby(data['datetime'].dt.to_period('1h'),group_keys=True)['value'].apply(lambda x: x.sum())
    #grouped2 = data.groupby(data['datetime'].dt.time, group_keys=True)['value'].apply(lambda x: x.sum())

    #grouped2.plot(kind='bar', y='value', title='hourly sum')
    #pyplot.xticks(fontsize=6)
    #pyplot.gca().xaxis.set_major_locator(mdates.DayLocator())
    #pyplot.plot_date(grouped2)
    #pyplot.show()

def getmeteoforcam(camnr):
    nr = int(camnr)
    locdata = inafiles.getlocationdata(inaconf.get_camlocations(), nr)
    locnr = int(locdata[1])
    summary = pd.DataFrame(getsummary(locnr))
    print(summary)
    return summary

def getsummary(locationnr):
    nr = int(locationnr)
    enddate = datetime.now(timezone.utc)
    startdate = enddate - timedelta(days=inaconf.meteoreportdays)

    meteos = inafiles.getmeteofromlocation(nr)
    summary = []
    for device in meteos:
        data, file = readarchive(device)
        data['datetime']= pd.to_datetime(data['datetime'])
        relevant = data.loc[(data['datetime'] > startdate) & (data['datetime'] <= enddate)]
        total = relevant['value'].sum()
        maxval = relevant['value'].max()
        batt = gettodaysbattlevel(device)
        summary.append({'location': nr, 'device': device, 'start':startdate, 'end': enddate, 'total': total, 'max': maxval,'batt': batt})

    return summary

def gettodaysbattlevel(device_sn):
    token = login()
    end = int(datetime.now(timezone.utc).timestamp())
    start = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
    battdate = read_batt(token, device_sn, start_time=start,end_time=end)
    return battdate['value'].mean()



def readarchive(device_sn):
    maindir = inaconf.maindir
    archivefile = os.path.join(maindir, 'precip_%s.csv' % (device_sn))
    archivedata = inafiles.readDataframe(archivefile, ',')
    archivedata.columns = archivedata.columns.str.strip()
    if 'datetime' in archivedata.columns:
        archivedata['datetime'] = pd.to_datetime(archivedata['datetime'], utc=True)
    return archivedata, archivefile
def getmeteodata(locationnr):
    token = login()
    meteos = inafiles.getmeteofromlocation(locationnr)
    attachments = []
    for meteo in meteos:

        print('Reading Zentra archive...')
        archivedata, archivefile = readarchive(meteo)
        if 'datetime' in archivedata.columns:
            #archivedata['datetime']=pd.to_datetime(archivedata['datetime'], utc=True)
            first = archivedata['datetime'].max()
        else:
            first = datetime(year=2020, month=8,  day=27)
        last = datetime.now()


        data = read_precip(token=token, device_sn=meteo, start_time=int(first.timestamp()), end_time=int(last.timestamp()))

        all = pd.concat([data, archivedata],ignore_index=True)
        all['datetime']=pd.to_datetime(all['datetime'], utc=True)
        all.set_index('datetime')
        all['rolling']=all['value'].rolling(min_periods=1, window=48).sum()
        all=all.drop_duplicates(subset=['mrid', 'description']).reset_index(drop=True)
        all = all[['datetime','mrid','rssi','port','units','description','value','error']]
        all.to_csv(archivefile)
        data = all
        #data['date'] = data['datetime']
        file = os.path.join(inaconf.maindir, 'plot_%s.png'%(meteo))
        plot = saveplot(data, devicesn=meteo, filename = file)
        attachments.append({'device': meteo, 'plotfile': plot})
    return attachments

