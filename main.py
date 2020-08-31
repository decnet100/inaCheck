# Inadef-Mailchecker
# Author Christian Demmler, BfW

# This will download images taken by trail cam ("Wildkamera") from preconfigured mail accounts into camera folders ([maindir]/cam_[x]).
# Nighttime images should show IR reflectors at constant positions, otherwise the site can be considered distorted (alert!) or the image unclear (fog, rain?)
#
# Initially, it will read the battery level from all images (comparison of black/white pixel content at the battery symbol)
# and analyse their content against known reflector positions ([maindir]/cam[x]/reflector_pos.txt.
# The reflector positions can be marked with a beginning and end date,
# i.e. "100, 200, 10, 2020_01_01_00.00.00, 2020_05_01_10.00.00", pointing out a size 10 circle around xy 100,200, starting in 1.Jan 2020 00:00:00, ending 01.May 2020 10:00:00
# It also checks daylight images (where IR reflectors are not clearly visible) by checking the entire image against known positive images (with reflector).
# In case some analyses do not detect the reflector, it will send out a caution to the recipients contained (one line per mail address) in [maindir]/audience_cam_[x].txt
#
# Program creates and fills a log file at [maindir]/log.txt

import os
from datetime import datetime
from math import sqrt

import numpy as np
import pytz
from suntime import Sun

from inadefChecker import image_prep, inafiles, inamailer
# preconf()
# for set_cfg set in imageset:
#     set_prepare_set(set)
#     if set_receive_set(set).renewSuccess = True:
#         set_analyze(set)
#         set_log(set)
from inadefChecker.inaconf import inaconf


def get_suntimes(date, latitude=47.26, longitude=11.39):
    sun = Sun(latitude, longitude)

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time(date)
    today_ss = sun.get_sunset_time(date)
    return ({'sunrise': today_sr, 'sunset': today_ss})


def get_currentreflectors(reflectors, date):
    current = []
    for reflector in reflectors:
        if len(reflector) == 5:  # if start-end dates are contained
            if (date >= datetime.strptime(reflector[3].strip(), inaconf.datefilefmt) and date <= datetime.strptime(
                    reflector[4].strip(), inaconf.datefilefmt)):
                current.append([reflector[0], reflector[1], reflector[2]])
        else:  # if start-end date is missing
            current.append([reflector[0], reflector[1], reflector[2]])
    return current


# import datetime

def preconfig():
    inaconf.set_datelogfmt(datelogfmt)
    inaconf.set_datefilefmt(datefilefmt)
    inaconf.set_dateexiffmt(dateexiffmt)
    inaconf.set_battcrop([335, 465, 367, 478])
    # locations = inaconf.get_camlocations()
    for i in activecams[0]:
        inafiles.dircreate('cam_%d' % i)
    inafiles.dirlocationchange()

    # if os.path_exists(os.path.join(maindir, 'cam_%d'%camnumber)):
    #    read =


def fetch():
    preconfig()
    newmsg = []
    for i in activecams[0]:
        newmsg = newmsg + inamailer.getinadefmail(i, inaconf.maindir)
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


import pandas as pd


def get_comparisons(imagefile, nclosest=5):
    time_day = inafiles.read_timedate_from_filename(imagefile)
    possible = []
    for compfile in os.listdir(os.path.dirname(imagefile)):
        if os.path.splitext(compfile)[1].lower() == '.jpg' and len(os.path.splitext(compfile)[0]) == 19:
            # if not ('_dil' in compfile or '_ds' in compfile or 'edge' in compfile or 'plot' in compfile):

            val = inafiles.read_timedate_from_filename(compfile)
            possible.append([compfile, val[0], val[1]])
    df = pd.DataFrame(possible, columns=['file', 'time', 'day'])

    res = []
    for comp in df[::-1].iterrows():
        if len(comp) > 1:
            if comp[1]['file'] != os.path.basename(imagefile) and abs(time_day[0].hour - comp[1]['time'].hour) < 2:
                res.append(comp)
            if (len(res) >= nclosest):
                break

    return res


def blobwatch(cam=0, new=[]):
    blobs = []
    camdir = os.path.join(maindir, inafiles.get_camdir(cam))
    start = inafiles.checkstart(cam, inaconf.maindir)

    reflectors = inafiles.read_reflectorpos(i)
    if os.path.exists(camdir):
        for image in os.listdir(camdir):

            valid = False
            goodqual = False
            missing_ref = []
            agreement = True
            if (len(os.path.splitext(image)[0]) == 19) and (os.path.splitext(image)[1].lower() == '.jpg'):
                orig = os.path.join(camdir, image)
                imgdate = datetime.strptime(os.path.splitext(image)[0], datefilefmt)
                local_imgdate = pytz.timezone(localtz).localize(imgdate)

                sr = get_suntimes(imgdate.date())
                # local_sr = pytz.timezone(localtz).localize(sr['sunrise'])
                # local_ss =pytz.timezone(localtz).localize(sr['sunset'])
                # imgdate = imgdate.replace(tzinfo = sr['sunrise'].tzinfo())

                if imgdate > start:
                    current = get_currentreflectors(reflectors, imgdate)
                    print('.............')
                    print('Image date: %s sunrise: %s, sunset: %s' % (local_imgdate.strftime(datelogfmt),
                                                                      sr['sunrise'].strftime(datelogfmt),
                                                                      sr['sunset'].strftime(datelogfmt)))

                    dilimg = os.path.join(camdir, os.path.splitext(image)[0] + '_dil.jpg')
                    if not os.path.exists(dilimg):
                        dilimg = image_prep.dilate(os.path.join(camdir, image))

                    if (local_imgdate > sr['sunrise']) and (local_imgdate < sr['sunset']):
                        inaconf.logprint(
                            'Timecheck: assuming daytime image - skipping blob analysis, doing edge comparison on entire image')
                        col = image_prep.has_color_info(orig, daycrop_win)
                        valid = True
                        agreement = True
                        comparisons = get_comparisons(orig)
                        results = []
                        for comp in comparisons:
                            values = image_prep.daycheck(orig, os.path.join(os.path.dirname(orig), comp[1]['file']))
                            print(comp[1], values)
                            results.append(values)
                        print('fertisch')
                        valid = (np.median(np.array(results)[:, 0]) > 0.45)
                        agreement = valid
                        goodqual = (np.median(np.array(results)[:, 1]) > 0.5)
                    else:
                        inaconf.logprint('Timecheck: assuming nighttime image')
                        if image_prep.is_lowcontrast(dilimg):  # Test of dilated image!

                            goodqual = image_prep.is_highquality(orig, night=True)
                            print('Image %s is low-contrast image. Performing Blob analysis' % (image))
                            missing_dil = image_prep.blobtest(dilimg, current)
                            cannyimg = image_prep.canny(orig)
                            missing_can = image_prep.blobtest(cannyimg, current)
                            if len(missing_dil) == 0 or len(missing_can) == 0:
                                valid = True
                            if min(len(missing_dil), len(missing_can)) != max(len(missing_dil), len(missing_can)):
                                agreement = False
                            missing_ref = missing_dil + missing_can
                            blobs.append(image_prep.blobdet(dilimg))
                            #
                            # for reflector in reflectors:
                            #     reflector_there = False
                            #     for blob in blobs[len(blobs)-1][1]:
                            #         reflector_there = reflector_there or reflector_contains_blob(reflector, blob)
                            #     if not reflector_there:
                            #         logprint('########## Blob Analysis: Reflector missing at cam %d, image %s'% (cam, image))
                            #         missing_ref.append(reflector)
                            #
                            #     else:
                            #         print('Reflector %s found.'%( ','.join(reflector)))

                        else:

                            print('high contrast image - skipping blob analysis')
                    inaconf.logprint('camera %d image %s analysed...' % (cam, image))
                    # decision making
                    if True:  # orig in new:
                        # only concern yourself with new images
                        if valid and agreement:
                            print('CLASSIFICATION: True positive.')
                            # do pretty much nothing. World is in order.
                        if valid and not agreement:
                            plotimg = image_prep.blobdraw(dilimg, cam, missing_ref)
                            inamailer.send_caution(cam, maindir, [orig, plotimg, cannyimg])
                            print('CLASSIFICATION: potentially false positive.')
                            # treat it as spurious. Send Notification
                        if not valid and goodqual:
                            # treat as alarm!
                            print('CLASSIFICATION: True negative.')
                            plotimg = image_prep.blobdraw(dilimg, cam, missing_ref)

                            inamailer.send_alert(cam, maindir, [orig, plotimg, cannyimg])
                            # missing_ref = []
                        if not valid and not goodqual:
                            print('CLASSIFICATION: potentially false negative.')
                            cannyimg = image_prep.canny(orig)
                            inamailer.send_caution(cam, maindir, [orig, plotimg, cannyimg])
                    else:
                        print('Image already registered, no action required.')
                        # treat as spurious. Send Notification
    inaconf.logprint('########## camera %d blobs analysed' % cam)
    # logprint(blobs)
    return blobs


def grow_reflector(center, size):
    return [center[0] - size, center[1] - size, center[0] + size, center[1] + size]


maindir = r'W:\Demmler\Privat\Inadef\CamFun'
config = inaconf(maindir)
activecams = [[1, 5], ['chdem100@gmail.com', 'chdem100@gmail.com ; cdemmler@gmx.de']]
datefilefmt = '%Y_%m_%d_%H.%M.%S'
datelogfmt = '%Y.%m.%d %H.%M.%S'
dateexiffmt = '%Y:%m:%d %H:%M:%S'

localtz = 'Europe/Vienna'
crop = [0, 0, 2560, 1000]
reflector_center = [1190, 460]

# reflectorcrop = [1140,410,1240,510]#
nightcrop_win = grow_reflector(reflector_center, 50)
daycrop_win = grow_reflector(reflector_center, 100)
# reflectorcrop = [100,0,1200,600]
# Mail command:
new = fetch()  # fetches mail, gets an array of all the new files saved to disk
print('%d new images found:' % len(new))
print(new)

blobs_cam = []
reflectors_cam = []
# testdir = r'c:\temp\wildkamera'
for i in activecams[0]:
    reflectors_cam.append([i, inafiles.read_reflectorpos(i)])
    blobs_cam.append(blobwatch(i, new))
