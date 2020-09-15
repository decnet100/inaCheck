import PySimpleGUI as sg
import inafiles
from inaconf import inaconf
import pandas as pd
sg.theme('LightBlue')   # Add a touch of color
# All the stuff inside your window.
class inagui:

    @staticmethod
    def initialize():
        inaconf(r'W:\Demmler\Frei\Inadef\CamFun')
        inaconf.preconfig()
        locations = inafiles.readlocations()
        inagui.locations = locations['name'].tolist()
        inagui.tlcs = inafiles.combinetlclocations()
        inagui.cameras = []
    def filltlcs(location):
        values = inagui.tlcs.loc[inagui.tlcs['name']==location]['direction'].tolist()
        window['camselect'].update(values = values)
        window.refresh
    def gettlcnum():
        return 1
    def gettlc():
        return 2
inagui.initialize()

layout = [
    [sg.T('Please select location:')],
          [sg.Combo(values=inagui.locations,key='locselect',enable_events=True)],
            [sg.Text('Please select date of refresh:')],

            [sg.In(key='refreshdate'),sg.CalendarButton(target='refreshdate', button_text='Date')],
            [sg.T('Please select the Camera views from that location that were refreshed:')],
            [sg.Listbox(values=inagui.cameras,size=(30,3),key='camselect',select_mode='multiple')],
            [sg.Text('Please select (or describe in your own words!) the location where images can be found:')],
            [sg.In(key='savelocation'), sg.FolderBrowse(target='savelocation',button_text='Browse for directory')],
            [sg.Button('Enter Data'), sg.Button('Cancel')] ]

# Create the Window


window = sg.Window('Timelapse-Camera Updater', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event=='locselect':
        inagui.filltlcs(values['locselect'])
    if event=='Enter Data':
        if values['locselect']!='' and values['refreshdate']!='' and values['camselect']!='' and values['savelocation']!='':
            vals=[]
            for cam in values['camselect']:
                vals.append({'direction': cam, 'name': values['locselect'], 'refreshdate': values['refreshdate'], 'savelocation': values['savelocation']})
            guiframe = pd.DataFrame(vals)
            guidata = inagui.tlcs.merge(guiframe, left_on=['name', 'direction'], right_on=['name', 'direction'])
            inafiles.savetlc(guidata)
            sg.Popup('Data has been entered, probably successfully.')
        else:
            sg.Popup('Please fill in all required data.')
    if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
        break

window.close()