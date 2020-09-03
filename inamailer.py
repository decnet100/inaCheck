# Inadef Mailer module
# Prepares notification mails
# Currently sends one mail each for all the problems encountered
# TO DO: Send a summary instead.

import os

from envelopes import Envelope
from imap_tools import MailBox

from inadefChecker import inaimage, inafiles
from inadefChecker.inaconf import inaconf
from datetime import datetime
import pandas as pd
class inamailer:

    def __init__(self):
        inamailer.cautions = [None] * 10
        inamailer.alerts = [None] * 10
        inamailer.batts = [None] * 10
        inamailer.gaps = [None] * 10
        inamailer.meteodata = [None] * 10
        inamailer.locplots = [None] * 10
        # for i in range(10):
        #     inamailer.cautions[i] = []
        #     inamailer.alerts[i] = []
        #     inamailer.batts[i] = []
        #     inamailer.gaps[i] = []
    @staticmethod




    def getinadefmail(number=1, maindir=inaconf.maindir):
        newmessage = []
        #battlevels = []
        filePath = ''
        params = inafiles.getmaildata()
        with MailBox(params['host']).login(params['mail'] % number, params['pwd'] % number, 'INBOX') as mailbox:
            for message in mailbox.fetch():
                if len(message.attachments) > 0:
                    print(message.date)
                for att in message.attachments:  # list: [Attachment objects]

                    filePath = os.path.join(maindir, inafiles.get_camdir(number),
                                            message.date.strftime(inaconf.datefilefmt) + '.JPG')
                    if not os.path.isfile(filePath):
                        inaconf.logprint('Cam %d: saving mail attachment %s' % (number, filePath))
                        fp = open(filePath, 'wb')
                        fp.write(att.payload)
                        fp.close()
                        newmessage.append(filePath)

        return newmessage
    def battcheck(filelist):
        battlevels = []
        for file in filelist:
            filePath = file['file']
            battlevels.append([inaimage.battcheck(filePath), inafiles.datetime_from_file(filePath)])
        return battlevels

    @staticmethod

    def get_inadefinfo(nr):
        number = int(nr)
        maindir = inaconf.maindir
        params = inafiles.getmaildata()
        locname = inafiles.getclearloc(inaconf.get_camlocations(),number)
        return {'login': params['mail'] % (number), 'pwd': params['pwd'] % (number), 'name': 'Inadef Cam %d-%s' % (number, locname[0]),
                'rec': inafiles.get_cam_receipients(number), 'host': params['host'], 'outhost': params['outhost']}

    @staticmethod

    def send_inadefmail(camnr, text=u'Something is happening!!', rec_name='Inadef observer', subject='Inadef notification',
                        attachments=[''], maindir=inaconf.maindir):
        data = inamailer.get_inadefinfo(camnr)
        envelope = Envelope(
            from_addr=(data['login'], data['name']),
            to_addr=(data['rec']),
            subject=subject,
            text_body=text
        )
        for attachment in attachments:
            if attachment != '':
                if os.path.isfile(attachment):
                    envelope.add_attachment(attachment)
                else:
                    print('Attachment %s not found. Skipping that file. ' % (attachment))

        # Send the envelope using an ad-hoc connection...


        envelope.send(data['outhost'], login=data['login'], password=data['pwd'], tls=True)

    @staticmethod

    def send_alert(camnr, maindir=inaconf.maindir, attachments=[]):
        print('sending alert to receipients: ', inafiles.get_cam_receipients(camnr))
        # send_inadefmail(camnr,
        #                 text='Camera %d alert: Reflector missing! Please see attached photo for verification.' % (camnr),
        #                 rec_name='Inadef observer', subject='Inadef %d alert - reflector missing' % (camnr),
        #                 attachments=attachments, maindir=maindir)
        # print('alerts: ', alerts)

        inamailer.alerts.append([camnr, attachments])

    @staticmethod
    def send_caution(camnr, maindir=inaconf.maindir, attachments=[]):

        inamailer.cautions.append([camnr, attachments])
        print('caution: ', inamailer.cautions[len(inamailer.cautions)-1])


        # send_inadefmail(camnr,
        #                 text='Camera %d notification: Image detection unclear! Please see attached photo for verification.' % (
        #                     camnr),
        #                 rec_name='Inadef observer', subject='Inadef %d caution - image unclear' % (camnr),
        #                 attachments=attachments, maindir=maindir)

    @staticmethod
    def fetch():

        newmsg = []
        activecams = inafiles.getactivecams()
        for nrstr in activecams:
            i = int(nrstr[0])
            newmsg = newmsg + inamailer.getinadefmail(int(i), inaconf.maindir)
        return newmsg

    @staticmethod
    def send_battalert_caution(camnr, levels, attachments=[], maindir=inaconf.maindir):

        inamailer.batts.append([camnr, levels])
        print('battery alerts:')
        print(inamailer.batts)
        #inamailer.send_inadefmail(camnr, text='Camera %d notification: Battery level low (%d)! Please replace batteries!' % (
        #camnr, levels[len(levels) - 1]),
        #                rec_name='Inadef observer', subject='Inadef %d caution - image unclear' % (camnr),
        #                attachments=attachments, maindir=maindir)
    @staticmethod
    def getmailpayload(number):
        alerts, cautions, batts, gaps = inamailer.alerts[i], inamailer.cautions[i], inamailer.batts[i], inamailer.gaps[i]
    def send_mails(camnr):
        i = int(camnr)
        alerts, cautions, batts, gaps, meteodata = inamailer.alerts[i], inamailer.cautions[i], inamailer.batts[i], inamailer.gaps[i], inamailer.meteodata[i]
        locations = inaconf.get_camlocations()
        locname = inafiles.getclearloc(locations,i)[0]
        locnr = int(inafiles.getclearloc(locations,i)[1])

        attachments = []
        for loc in inamailer.locplots[locnr]:
            attachments.append(loc['plotfile'])
        reportname = 'Inadef report (%s), %s'%(locname, datetime.now().strftime(inaconf.datehumanfmt))
        subjectmode = 'Notification: '
        alerttext =''
        gaptext=''
        if len(gaps)>0:
            subjectmode = 'Alert! '
            gaptext = 'Alert: Camera not delivering images at expected frequency (1 image/24h)'
        for gap in gaps:
            gaptext = gaptext + '\nUnexpected gap: img %s - %s'% (gap['prevdate'].strftime(inaconf.datehumanfmt), gap['date'].strftime(inaconf.datehumanfmt))
        for alert in alerts:
            date, time = inafiles.read_timedate_from_filename(alert[1])
            attachments = attachments+alerts[2]
            camstr = inafiles.getclearloc(locations, i)
            text = 'Alert: Cam %d (%s) - on %s reflector presumably missing!'%(i, camstr[0], camdate.strftime(inaconf.datelogfmt))
            alerttext = alerttext + '\n' + text
            subjectmode = 'Alert! '
        cautiontext=''
        for caution in cautions:
            date = inafiles.datetime_from_file(caution[2][0])
            attachments = attachments+caution[2]
            camstr = inafiles.getclearloc(locations, i)
            text = 'caution: Cam %d (%s) - on %s reflector not clearly detected.'%(i, camstr[0], date.strftime(inaconf.datehumanfmt))
            cautiontext = cautiontext + '\n' + text
        meteotext =''
        if len (meteodata)>0:
            avg = meteodata['total'].mean()
            first = meteodata['start'].min().strftime(inaconf.datehumanfmt)
            last = meteodata['end'].max().strftime(inaconf.datehumanfmt)

            devices = ';'.join(meteodata['device'])
            meteotext = 'Meteorological data (%s): total precipitation - %.1f mm from %s - %s'%(devices, avg, first, last)
            for device  in meteodata.iterrows():
                meteotext = meteotext+'\nBattery level last 24h (%s): %.f percent'%(device[1]['device'], device[1]['batt'])


        batttext = ''
        if batts[len(batts)-1][0] <= inaconf.battwarning:
            camstr = inafiles.getclearloc(locations, i)
            batttext = 'Battery notification: Level of cam %d (%s) low - last reading below %.f percent'%(i, camstr[0], 100*inaconf.battwarning)
            subjectmode = 'Alert! '
        for j in range(len(batts)):
            batttext = '\n'.join([batttext, 'Trailcam Battery Level (%s): %.f percent'%(batts[j][1].strftime(inaconf.datehumanfmt), batts[j][0]*100)])

        mailtext = '\n'.join([gaptext, meteotext, alerttext,cautiontext, batttext])
        inamailer.send_inadefmail(camnr=camnr, text=mailtext, rec_name='Inadef mail checker', subject=subjectmode + reportname,
                        attachments=attachments, maindir=inaconf.maindir)
