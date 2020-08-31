# # This is a sample Python script.
#
# # Press Umschalt+F10 to execute it or replace it with your code.
# # Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# imageset = []
# class set_cfg:
#     name = 'InadefX'
#     setDir = 'directory//to//reference-files'
#     downloadDir = 'directory//to//download'
#     renewSuccess = False
#     def renewal(self):
#         self.renewSuccess=True
#     def storeParams(self):
#         #do stuff to store to cfg file to setDir
#     def loadParams(self):
#         #do stuff that results in cfg file getting read from setDir
#     def prepare(self):
#         #create config files if non-existant;  read config variables
#     def receive(self):
#         #check if we got new mail; if successful: renewal
#
# preconf()
# for set_cfg set in imageset:
#     set_prepare_set(set)
#     if set_receive_set(set).renewSuccess = True:
#         set_analyze(set)
#         set_log(set)
maindir = r'W:\Demmler\Privat\Inadef\CamFun'
# maindir = r'c:\temp\wildkamera'
import os
from datetime import datetime
from math import sqrt

import pytz
from imap_tools import MailBox

from inadefChecker import image_prep, inamailer

activecams = [[1, 5], ['chdem100@gmail.com', 'chdem100@gmail.com ; cdemmler@gmx.de']]
datefilefmt = '%Y_%m_%d_%H.%M.%S'
datelogfmt = '%Y.%m.%d %H.%M.%S'
dateexiffmt = '%Y:%m:%d %H:%M:%S'
defaultreflectors = [[1, 113, 297, 20], [5, 242, 448, 20]]
localtz = 'Europe/Vienna'
from suntime import Sun


def get_suntimes(date, latitude=47.26, longitude=11.39):
    sun = Sun(latitude, longitude)

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time(date)
    today_ss = sun.get_sunset_time(date)
    return ({'sunrise': today_sr, 'sunset': today_ss})


def read_reflectorpos(cam=0):
    reffile = os.path.join(maindir, 'cam_%d' % cam, 'reflector_pos.txt')
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


# import datetime
def dircreate(dirName='dir'):
    if not os.path.exists(os.path.join(maindir, dirName)):
        os.mkdir(os.path.join(maindir, dirName))
        logprint("Directory ", dirName, " Created ")
    else:
        logprint("Directory ", dirName, " already exists")


def preconfig():
    for i in activecams[0]:
        dircreate('cam_%d' % i)


def checkstart(camnumber=0):
    startfile = os.path.join(maindir, 'cam_%d' % camnumber, 'startdate.txt')
    if os.path.isfile(startfile):
        with open(startfile) as f:
            datestr = f.readline()
        f.close()
        if len(datestr) > 9:
            date = datetime.strptime(datestr, '%Y_%m_%d')
        else:
            date = datetime.now()
        return date

    # if os.path_exists(os.path.join(maindir, 'cam_%d'%camnumber)):
    #    read =


def getinadefmail(number=1):
    newmessage = []
    with MailBox('bimap.a1.net').login('inadef%d@bfw6020.at' % number, '!Fedani%d' % number, 'INBOX') as mailbox:
        for message in mailbox.fetch():
            print(message.date)
            for att in message.attachments:  # list: [Attachment objects]
                filePath = os.path.join(maindir, 'cam_%d' % (number), message.date.strftime(datefilefmt) + '.JPG')
                if not os.path.isfile(filePath):
                    logprint('Cam %d: saving mail attachment %s' % (number, filePath))
                    fp = open(filePath, 'wb')
                    fp.write(att.payload)
                    fp.close()
                    newmessage.append(filePath)
    return newmessage


def fetch():
    preconfig()
    newmsg = []
    for i in activecams[0]:
        newmsg.append(getinadefmail(i))
    return newmsg


def blob_contains(ref, check):
    d = sqrt((check[0] - int(ref[0])) ** 2 + (check[1] - int(ref[1])) ** 2)
    if int(ref[2]) >= (d + check[2]):

        return True
    else:
        return False


def blobset_difference(ref_set, check_set):
    diff = 0.0
    if ref_set.ndim == 1:
        ref_set = [ref_set]
    if check_set.ndim == 1:
        check_set = [check_set]
    total_area = 0.0
    for ref in ref_set:
        # size check? if really small, skip it?
        total_area = total_area + (ref[2] / blobtolerance) ** 2
        found = False
        for check in check_set:
            found = blob_contains(ref, check)
            if found:
                break
        diff = diff + ((not found) * (ref[2] / blobtolerance) ** 2)
    if total_area > 0.0:
        return diff, total_area
    else:
        return None, None


def blob_is_different(ref_set, check_set, threshold=0.5):
    # print('reference: ', ref_set)
    # print('check: ', check_set)
    diff, area = blobset_difference(ref_set, check_set)

    if not (area is None):
        amount = (diff / area)
        logprint('Reference and check blob sets differ by %f percent' % ((100 * diff / area)))
        if amount > threshold:
            return True, amount
        else:
            return False, amount
    else:
        print('Difference uncheckable.')
        return None, 0.0


def reflector_contains_blob(reflector, blob):
    # print blob.ndim
    if blob.ndim == 1:
        d = sqrt((blob[0] - int(reflector[0])) ** 2 + (blob[1] - int(reflector[1])) ** 2)
        if int(reflector[2]) >= (d + blob[2]):
            return True
        else:
            return False
    else:
        for blob_check in blob:
            d = sqrt((blob_check[0] - int(reflector[0])) ** 2 + (blob_check[1] - int(reflector[1])) ** 2)
            if int(reflector[2]) >= (d + blob_check[2]):
                return True
                break
            else:
                return False


def logprint(*text):
    print(*text)
    logfile = os.path.join(maindir, 'log.txt')
    with open(logfile, 'a+') as f:
        f.write(datetime.now().strftime(datelogfmt) + ' - ')
        print(*text, file=f)
    f.close()


def blobwatch(cam=0, new=[]):
    blobs = []
    camdir = os.path.join(maindir, 'cam_%d' % cam)
    start = checkstart(cam)

    reflectors = read_reflectorpos(i)
    if os.path.exists(camdir):
        for image in os.listdir(camdir):
            valid = False
            goodqual = False
            missing_ref = []
            structure_similar = True
            if (not ('_dil' in image) and not ('_plot' in image) and os.path.splitext(image)[1].lower() == '.jpg'):
                orig = os.path.join(camdir, image)
                imgdate = datetime.strptime(os.path.splitext(image)[0], datefilefmt)
                local_imgdate = pytz.timezone(localtz).localize(imgdate)

                sr = get_suntimes(imgdate.date())
                # local_sr = pytz.timezone(localtz).localize(sr['sunrise'])
                # local_ss =pytz.timezone(localtz).localize(sr['sunset'])
                # imgdate = imgdate.replace(tzinfo = sr['sunrise'].tzinfo())

                if imgdate > start:
                    print('.............')
                    print('Image date: %s sunrise: %s, sunset: %s' % (local_imgdate.strftime(datelogfmt),
                                                                      sr['sunrise'].strftime(datelogfmt),
                                                                      sr['sunset'].strftime(datelogfmt)))

                    dilimg = os.path.join(camdir, os.path.splitext(image)[0] + '_dil.jpg')
                    if not os.path.exists(dilimg):
                        dilimg = image_prep.dilate(os.path.join(camdir, image))

                    if (local_imgdate > sr['sunrise']) and (local_imgdate < sr['sunset']):
                        logprint('Timecheck: assuming daytime image - skipping blob analysis')
                        col = image_prep.has_color_info(orig, daycrop_win)
                        if not (col):
                            print('This seems to be a B/W image due to low-light conditions.')
                        else:
                            goodqual = True
                    else:
                        logprint('Timecheck: assuming nighttime image')
                        if image_prep.is_lowcontrast(dilimg):
                            goodqual = True
                            print('Image %s is low-contrast image. Performing Blob analysis' % (image))
                            blobs.append(image_prep.blobdet(dilimg))

                            for reflector in reflectors:
                                reflector_there = False
                                for blob in blobs[len(blobs) - 1][1]:
                                    reflector_there = reflector_there or reflector_contains_blob(reflector, blob)
                                if not reflector_there:
                                    logprint('########## Blob Analysis: Reflector missing at cam %d, image %s' % (
                                    cam, image))
                                    missing_ref.append(reflector)

                                else:
                                    print('Reflector %s found.' % (','.join(reflector)))

                        else:

                            print('high contrast image - skipping blob analysis')
                    logprint('camera %d image %s analysed...' % (cam, image))
                valid = (len(missing_ref) == 0 and (structure_similar == True))
                # decision making
                if orig in new:
                    # only concern yourself with new images
                    if valid and goodqual:
                        pass
                        # do pretty much nothing. World is in order.
                    if valid and not goodqual:
                        pass
                        # treat it as spurious. Send Notification
                    if not valid and goodqual:
                        # treat as alarm!

                        plotimg = image_prep.blobdraw(dilimg, cam, missing_ref)

                        inamailer.send_alert(cam, maindir, [orig, plotimg])
                        missing_ref = []
                    if not valid and not goodqual:
                        pass
                else:
                    print('Image already registered, no action required.')
                    # treat as spurious. Send Notification
    logprint('########## camera %d blobs analysed' % cam)
    # logprint(blobs)
    return blobs


def grow_reflector(center, size):
    return [center[0] - size, center[1] - size, center[0] + size, center[1] + size]


def lightamount(cam=0):
    lightamt = []
    camdir = os.path.join(maindir, 'cam_%d' % cam)
    start = checkstart(cam)
    reflectors = read_reflectorpos(i)
    if os.path.exists(camdir):
        for image in os.listdir(camdir):
            if (os.path.splitext(image)[0][-4:] != '_dil' and os.path.splitext(image)[1].lower() == '.jpg'):
                imagefile = os.path.join(camdir, image)


ref_brightness = []

crop = [0, 0, 2560, 1000]
reflector_center = [1190, 460]

# reflectorcrop = [1140,410,1240,510]#
nightcrop_win = grow_reflector(reflector_center, 50)
daycrop_win = grow_reflector(reflector_center, 100)
# reflectorcrop = [100,0,1200,600]
# Mail command:
new = fetch()
print('%d new images found' % len(new))

blobs_cam = []
reflectors_cam = []
# testdir = r'c:\temp\wildkamera'
for i in activecams[0]:
    reflectors_cam.append([i, read_reflectorpos(i)])
    blobs_cam.append(blobwatch(i, new))
    lightamount(i)
    # blobtolerance = 0.2
    # day_log = os.path.join(testdir, 'day.log')
    # night_log = os.path.join(testdir, 'night.log')
    # bright_log = os.path.join(testdir, 'file_brightness.log')
    # hourbright_log = os.path.join(testdir, 'hour_brightness.log')
    # csving.init(day_log, ['orig', 'time', 'delta', 'sim', 'blob_delta'])
    # csving.init(night_log,['orig', 'time', 'delta', 'reflector_there'])
    #
    # #csving.init(hourbright_log,['hour', 'dark', 'darkfile', 'med', 'medfile', 'bright', 'brightfile'])
    # # reference = r'c:\temp\wildkamera\SYER1817.jpg'
    # # night_reference = r'c:\temp\wildkamera\SYER1876.jpg'
    # day_max_sigma= 30
    # day_min_sigma = 5
    # #print(image_prep.has_color_info(reference))
    # #print(image_prep.has_color_info(night_reference))
    # #
    # # nightcrop =image_prep.cropsave(night_reference,nightcrop_win)
    # # #refpolys = image_prep.polygonization(image_prep.dilation(referencecrop))
    # # #refblobs = image_prep.blobdet(referencecrop, min_sigma = 5, max_sigma = 10, threshold=0.025)
    # #
    # #
    # #
    # #
    # #
    # # nightblobs = image_prep.blobdet(image_prep.dilate(nightcrop))
    # # print('night blobs: ', nightblobs)
    # # for blob in nightblobs[1]:
    # #     blob[2] = blob[2] * (1+ blobtolerance)
    # # #nightblobs[1][0][2] = nightblobs[1][0][2] * (1 + blobtolerance)
    # # logprint('Adjusting night blob size to +%f percent for tolerance: '%(blobtolerance*100), nightblobs)
    # edges = []
    # similarities = []
    # #init_ref_brightness()
    # edge_log = os.path.join(testdir, 'edges.log')
    # #csving.init(edge_log,['orig', 'hour', 'edgeamt'])
    # init_ref_edgeamount(maindir,daycrop_win)
    #
    # missing_log =os.path.join(testdir, 'missing.log')
    # csving.init(missing_log,['orig', 'ref', 'delta', 'edge_comp', 'edge_ref'])
    #
    # testdir = os.path.join(maindir, 'testfiles')
    # for file in os.listdir(testdir):
    #     if os.path.splitext(file)[1].lower() == '.jpg':
    #         #edge = image_prep.canny(os.path.join(testdir, file))
    #         orig = os.path.join(testdir, file)
    #         timestr = exifhandler.get_tag_from_file(orig, 'DateTimeOriginal').decode("utf-8")
    #         filetime = datetime.strptime(timestr, dateexiffmt)
    #         edgeamt, edgefile = image_prep.getedge(os.path.join(testdir,file), daycrop_win,os.path.join(maindir,'edge'))
    #         edges = pd.DataFrame(csving.read(edge_log))
    #         edges['hour'] = edges['hour'].astype(int)
    #         edges['edgeamt'] = edges['edgeamt'].astype(float)
    #         compnum = 10
    #         ref_set = getclosestedgeref(edgeamt*1.2,edges,edgefile, compnum)
    #         valid = 0
    #         deltas = []
    #         crop1 = image_prep.cropsave(orig, daycrop_win)
    #         for ref in ref_set.values:
    #             if orig != ref[0]:
    #
    #                 crop2 = image_prep.cropsave(ref[0], daycrop_win)
    #                 print(crop1, '_', crop2)
    #                 #print(orig, '_', ref[0], ': %f'%cvcomp.comp(crop1, crop2))
    #                 delta = image_prep.img_difference(orig, ref[0],crop=daycrop_win, edgepath=os.path.join(maindir,'edge'), outpath=os.path.join(maindir,'comp'))
    #                 #print (delta)
    #         #         print(delta / (edge_ref - edge_comp))
    #         #         print((delta * 10) / (edge_ref + edge_comp))
    #         #         deltas.append((delta*10) / (edge_ref + edge_comp))
    #         #         if (delta*10) / (edge_ref + edge_comp) < 1:
    #         #             valid = valid+1
    #         # print('%d out of %d valid...'%(valid, compnum))
    #         # print('median delta: %f'% median(deltas))
    #         # if median(deltas) <1 or min(deltas)<0.5:
    #         #
    #         #     print(orig, r': ++++++++++   Bild scheint das gewohnte Motiv zu zeigen')
    #         # else:
    #         #     print(orig, r': ---------------- Bild tanzt aus der Reihe.')
    #
    #                                 # if image_prep.has_color_info(orig, nightcrop_win):
    #                                 #     #reference = getclosestref(filetime.hour,image_prep.getavgbrightness(orig),ref_brightness, orig)
    #                                 #     daycrop = image_prep.cropsave(reference, daycrop_win)
    #                                 #     #refblobs = image_prep.blobdet(daycrop, min_sigma=day_min_sigma, max_sigma=day_max_sigma)
    #                                 #     #print('day blobs: ', refblobs)
    #                                 #     #for blob in refblobs[1]:
    #                                 #     #    blob[2] = blob[2] * (1 + blobtolerance)
    #                                 #     #logprint('Adjusting day blob size to +%f percent for tolerance: ' % (blobtolerance * 100), refblobs)
    #                                 #     cropped = image_prep.cropsave(orig, daycrop_win)
    #                                 #     #matched = image_prep.matchhist(cropped, daycrop)
    #                                 #     matched = cropped
    #                                 #     #edge = image_prep.edge(matched)
    #                                 #     #poly = image_prep.polygonization(image_prep.dilation(croppy))
    #                                 #     delta, edge_comp, edge_ref = image_prep.img_difference(matched, daycrop)
    #                                 #     edge_max = max(edge_ref, edge_comp)
    #                                 #     edge_min = min(edge_ref, edge_comp)
    #                                 #     print(orig, reference, delta, edge_max, edge_min)
    #                                 #     print(delta*10 / (edge_min+edge_max))
    #                                 #     if (edge_comp) > 0 and (edge_ref > 0.66 * edge_comp):
    #                                 #         if (delta / (edge_min+edge_max))>0.1:
    #                                 #             print('potentially big change detected!')
    #                                 #             csving.write(missing_log,[matched, daycrop, delta, edge_comp, edge_ref])
    #                                 #         if edge_comp < 0.66 * edge_ref:
    #                                 #             print('untextured comparison image')
    #                                 #     else:
    #                                 #         print('untextured reference image')
    #                                 #
    #                                 #     #sim =  image_prep.checksim(referencecrop, croppy, crop = [0,0,0,0], match_hist = True)
    #                                 #     #checkblobs = image_prep.blobdet(matched,min_sigma = day_min_sigma, max_sigma = day_max_sigma)
    #                                 #     #logprint(orig, 'DAY blobs:',checkblobs)
    #                                 #     #blob_different, blob_delta =  blob_is_different(refblobs[1], checkblobs[1])
    #                                 #     #if blob_different:
    #                                 #     #   logprint(orig, 'DAY: couldn''t find blobs in  %s'%orig)
    #                                 #     #print('%s: %f similarity to day-reference' % (orig, sim))
    #                                 #     #logprint(orig, 'RMS: %f' % delta)
    #                                 #     #sim =  image_prep.img_similarity(matched, daycrop)
    #                                 #     #logprint(orig, 'SSIM:',)
    #                                 #
    #                                 #     csving.write(day_log, [orig, filetime.strftime(datelogfmt), delta, edge_max, edge_min])
    #                                 # else:
    #                                 #     cropped = image_prep.cropsave(orig, nightcrop_win)
    #                                 #     dilated = image_prep.dilate(cropped)
    #                                 #     #sim = image_prep.checksim(nightcrop, croppy, crop=[0, 0, 0, 0])
    #                                 #     night_blobs = image_prep.blobdet(dilated)[1]
    #                                 #     logprint(orig, 'NIGHT: %s blobs:'%(orig),night_blobs)
    #                                 #     reflector_there = False
    #                                 #     #for ref_blob in nightblobs[1]:
    #                                 #     #    reflector_there = (reflector_there or reflector_contains_blob(ref_blob, night_blobs))
    #                                 #     #if reflector_there:
    #                                 #     #    logprint(orig, 'NIGHT Reflector found, everything seems fine.')
    #                                 #     #else:
    #                                 #    #     logprint(orig, 'NIGHT Couldn''t find reflector in %s'%(orig))
    #                                 #     #print('%s: %f similarity to night-reference' % (orig, sim))
    #                                 #     #delta = image_prep.img_difference(dilated, nightcrop)
    #                                 #     #logprint(orig, 'RMS: %f' % delta)
    #                                 #     #logprint(orig, 'SSIM:', image_prep.img_similarity(dilated, nightcrop, True))
    #                                 #     #csving.write(night_log, [orig, filetime.strftime(datelogfmt), delta, reflector_there])
    #                                 # #if sim < 0.5:
    #                                 # #    print('Detector seems to be missing!')
    #                                 # #similarities.append([orig, sim])
    #                                 # #edges.append(edge)
    #
    #     print('all done')
    #
    #
    #
    #
    #
