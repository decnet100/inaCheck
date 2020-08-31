def init_ref_brightness(inDir=maindir):
    # let's read all the files' average brightnesses and compile them into a nice little list.
    readfiles = pd.DataFrame(csving.read(bright_log, None))
    readfiles['hour'] = readfiles['hour'].astype(int)
    readfiles['brightness'] = readfiles['brightness'].astype(float)
    files = readfiles.values
    if len(files) == 0:
        csving.init(bright_log, ['orig', 'hour', 'brightness'])
    for file in os.listdir(inDir):
        if os.path.splitext(file)[1].lower() == '.jpg':
            orig = os.path.join(inDir, file)
            if (len(files) == 0 or not (orig in readfiles['orig'].values)):
                timestr = exifhandler.get_tag_from_file(orig, 'DateTimeOriginal').decode("utf-8")
                filetime = datetime.strptime(timestr, dateexiffmt)
                filehour = int(filetime.hour)
                filebright = image_prep.getavgbrightness(orig)
                readfiles = readfiles.append({'orig': orig, 'hour': filehour, 'brightness': filebright},
                                             ignore_index=True)
                csving.write(bright_log, [orig, filehour, filebright])
            else:
                filehour = readfiles.loc[readfiles['orig'] == orig]['hour'].values[0]

            print(orig, ' added to brightness analysis for hour', filehour)
    for i in range(0, 24):
        ref_brightness.append({'hour': i, 'dark': None, 'darkfile': None, 'med': None, 'medfile': None, 'bright': None,
                               'brightfile': None, 'num': 0})
        csving.init(hourbright_log, ['orig', 'dark', 'darkfile', 'med', 'medfile', 'bright',
                                     'brightfile', 'num'])
        hourfiles = readfiles.loc[readfiles['hour'] == i]
        ranks = np.argsort(hourfiles['brightness'], axis=0)
        med = hourfiles.values[ranks.values[len(hourfiles) // 2]]
        max = hourfiles.values[ranks.values[3 * (len(hourfiles) - 1) // 4]]
        min = hourfiles.values[ranks.values[(len(hourfiles) - 1) // 4]]
        ref_brightness[i]['num'] = 1 + ref_brightness[i]['num']
        # ref_brightness[i]['rec'].append([filebright, orig])
        ref_brightness[i]['med'] = med[2]
        ref_brightness[i]['medfile'] = med[0]
        ref_brightness[i]['dark'] = min[2]
        ref_brightness[i]['darkfile'] = min[0]
        ref_brightness[i]['bright'] = max[2]
        ref_brightness[i]['brightfile'] = max[0]
        csving.write(hourbright_log,
                     [i, ref_brightness[i]['dark'], ref_brightness[i]['darkfile'], ref_brightness[i]['med'],
                      ref_brightness[i]['medfile'], ref_brightness[i]['bright'], ref_brightness[i]['brightfile'],
                      ref_brightness[i]['num']])
        # return ref_brightness


def init_ref_edgeamount(inDir=maindir, crop=[0, 0, 0, 0]):
    # let's read all the files' average brightnesses and compile them into a nice little list.
    files = []
    if os.path.isfile(edge_log):
        readfiles = pd.DataFrame(csving.read(edge_log, None))
        if len(readfiles) > 0:
            readfiles['hour'] = readfiles['hour'].astype(int)
            readfiles['edgeamt'] = readfiles['edgeamt'].astype(float)
            files = readfiles.values
    else:
        csving.init(edge_log, ['orig', 'edgefile', 'hour', 'edgeamt'])
        readfiles = pd.DataFrame(csving.read(edge_log, None))

    for file in os.listdir(inDir):
        if (os.path.splitext(file)[1].lower() == '.jpg' and not os.path.basename(file)[0:2].lower() == 'un'):
            orig = os.path.join(inDir, file)
            if (len(files) == 0 or not (orig in readfiles['orig'].values)):
                timestr = exifhandler.get_tag_from_file(orig, 'DateTimeOriginal').decode("utf-8")
                filetime = datetime.strptime(timestr, dateexiffmt)

                filehour = int(filetime.hour)

                edgeamt, edgefile = image_prep.getedge(orig, crop, os.path.join(inDir, 'edge'))
                readfiles = readfiles.append({'orig': orig, 'edgefile': edgefile, 'hour': filehour, 'edgeamt': edgeamt},
                                             ignore_index=True)
                csving.write(edge_log, [orig, edgefile, filehour, edgeamt])
            else:
                # if not (os.path.isfile(file['edgefile'])
                filehour = readfiles.loc[readfiles['orig'] == orig]['hour'].values[0]
            readfiles.sort_values('edgeamt')
            print(orig, ' added to edge amount analysis for hour', filehour)
    return pd.DataFrame(readfiles)

    # return ref_brightness


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def getclosestref(hour, brightness, reference_set, file):
    hour_set = reference_set[hour]
    print('File brightness:', brightness)
    if brightness < hour_set['dark']:
        print('Very dark image. Using q1 darkest for reference.')
        recomm_file = hour_set['darkfile']
    if brightness > hour_set['bright']:
        print('Very dark image. Using q3 brightest for reference.')
        recomm_file = hour_set['brightfile']
    if (brightness >= hour_set['dark'] and brightness <= hour_set['bright']):
        array = np.asarray([hour_set['dark'], hour_set['med'], hour_set['bright']])
        idx = (np.abs(array - brightness)).argmin()
        files = np.asarray([hour_set['darkfile'], hour_set['medfile'], hour_set['brightfile']])
        recomm_file = files[idx]
    if recomm_file == file:
        print('using another element to avoid A-A comparison.')
        if recomm_file == hour_set['medfile']:
            recomm_file = hour_set['darkfile']
        else:
            recomm_file = hour_set['medfile']
    return hour_set['medfile']
    # return recomm_file


def getclosestedgeref(edgeamt, reference_set, file, number):
    return reference_set.iloc[(reference_set['edgeamt'] - edgeamt).abs().argsort()[:number]]
