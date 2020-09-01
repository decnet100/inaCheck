from zentra.api import *
import os
from datetime import datetime, timedelta, date
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
    readings = read_data(token, device_sn,start_time,end_time)
    data = pd.DataFrame(readings.timeseries[0].values)
    precip_criterium = data['description'] == 'Precipitation'
    precip_data = data[precip_criterium]
    return precip_data
def fullplot(data):
    #grouped = data.groupby(data['dt'].dt.hour, as_index=False)['value'].sum().plot(kind='bar', x='datetime')
    #data.plot(x='datetime', y='value')
    #data.plot(x='datetime',y='rolling')
    #pyplot.show()
    grouped = data.groupby(data['datetime'].dt.date)['value'].apply(lambda x: x.sum())
    grouped.plot(kind='bar', y='value', title='24h sum')
    pyplot.show()
    #grouped2 = data.groupby(data['datetime'].dt.to_period('1h'),group_keys=True)['value'].apply(lambda x: x.sum())
    #grouped2 = data.groupby(data['datetime'].dt.time, group_keys=True)['value'].apply(lambda x: x.sum())

    #grouped2.plot(kind='bar', y='value', title='hourly sum')
    #pyplot.xticks(fontsize=6)
    #pyplot.gca().xaxis.set_major_locator(mdates.DayLocator())
    #pyplot.plot_date(grouped2)
    #pyplot.show()
def getmeteodata(locationnr):
    inaconf(r'W:\Demmler\Privat\Inadef\CamFun')
    token = login()
    meteos = inafiles.getmeteofromlocation(locationnr)
    for meteo in meteos:

        print('Reading Zentra archive...')
        archivefile = os.path.join(inaconf.maindir, 'precip_%s.csv'%(meteo))
        archivedata = inafiles.readDataframe(archivefile,',')
        archivedata.columns=archivedata.columns.str.strip()
        if 'datetime' in archivedata.columns:
            archivedata['datetime']=pd.to_datetime(archivedata['datetime'], utc=True)
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

        fullplot(data)

