# Inadef Mailer module
# Prepares notification mails
# Currently sends one mail each for all the problems encountered
# TO DO: Send a summary instead.

import os

from envelopes import Envelope
from imap_tools import MailBox

from inadefChecker import inaimage, inafiles
from inadefChecker.inaconf import inaconf

caution = []
missing = []
batt = []


def get_cam_receipients(camnr, maindir=inaconf.maindir, default=''):
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


def getinadefmail(number=1, maindir=inaconf.maindir):
    newmessage = []
    battlevels = []
    filePath = ''
    params = getmaildata(maindir)
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
                battlevels.append(inaimage.battcheck(filePath))
            if len(battlevels) > 0:
                print('Cam %d  Batt level percent:' % (number), round(100 * battlevels[len(battlevels) - 1]))
        if battlevels[len(battlevels) - 1] < 0.2:
            inamailer.send_battalert_caution(number, battlevels, inaconf.maindir, filePath)
    return newmessage


def getmaildata(maindir=inaconf.maindir):
    filepath = os.path.join(maindir, 'maildata.txt')
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            rec = f.readline()
    else:
        raise AssertionError
    vals = rec.split(',')
    return {'host': vals[0].strip(), 'mail': vals[1].strip(), 'pwd': vals[2].strip()}


def get_inadefinfo(number, maindir=inaconf.maindir):
    params = getmaildata(maindir)
    return {'login': params['mail'] % (number), 'pwd': params['pwd'] % (number), 'name': 'Inadef Camera %d' % (number),
            'rec': get_cam_receipients(number, maindir)}


def send_inadefmail(camnr, text=u'Something is happening!!', rec_name='Inadef observer', subject='Inadef notification',
                    attachments=[''], maindir=inaconf.maindir):
    data = get_inadefinfo(camnr, maindir)
    envelope = Envelope(
        from_addr=(data['login'], data['name']),
        to_addr=(data['rec']),
        subject=subject,
        text_body=text
    )
    for attachment in attachments:
        if os.path.isfile(attachment):
            envelope.add_attachment(attachment)
        else:
            print('Attachment %s not found. Skipping that file. ' % (attachment))

    # Send the envelope using an ad-hoc connection...


    envelope.send(data['host'], login=data['login'], password=data['pwd'], tls=True)

def send_alert(camnr, maindir=inaconf.maindir, attachments=[]):
    print('sending alert to receipients: ', get_cam_receipients(camnr, maindir))
    send_inadefmail(camnr,
                    text='Camera %d alert: Reflector missing! Please see attached photo for verification.' % (camnr),
                    rec_name='Inadef observer', subject='Inadef %d alert - reflector missing' % (camnr),
                    attachments=attachments, maindir=maindir)
    print('alerts: ', missing)
    missing.append([camnr, attachments])


def send_caution(camnr, maindir=inaconf.maindir, attachments=[]):
    caution.append([camnr, attachments])
    print('cautions: ', caution)

    send_inadefmail(camnr,
                    text='Camera %d notification: Image detection unclear! Please see attached photo for verification.' % (
                        camnr),
                    rec_name='Inadef observer', subject='Inadef %d caution - image unclear' % (camnr),
                    attachments=attachments, maindir=maindir)


def send_battalert_caution(camnr, levels, attachments=[], maindir=inaconf.maindir):
    batt.append([camnr, levels])
    print('battery alerts:')
    print(batt)
    send_inadefmail(camnr, text='Camera %d notification: Battery level low (%d)! Please replace batteries!' % (
    camnr, levels[len(levels) - 1]),
                    rec_name='Inadef observer', subject='Inadef %d caution - image unclear' % (camnr),
                    attachments=attachments, maindir=maindir)
