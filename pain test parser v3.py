
## import modules
import json
import tkinter
import tkinter.filedialog

## define functions
def grabjson(jsfile):
    with open(jsfile,'r') as f:
        outputobject=json.load(f)
    f.closed
    return outputobject

def makeobslist(bf):
    ol=[i for i in bf['observations'].keys()]
    ol.sort()
    return ol

def makebehlist(bf):

    bl=[bf['behaviors_conf'][k]['code']
     for k in bf['behaviors_conf'] if bf['behaviors_conf'][k]['type']=='State event']
    bl.sort()
    #bl=[]
    #for k in bf['behaviors_conf']:
    #    bl.append(borisdata['behaviors_conf'][k]['code'])
    return bl

def guiOpenFileName(kwargs={}):
    """Returns the path to the files selected by the GUI.
*Function calls on tkFileDialog and uses those arguments
  ......
  (declare as a dictionairy)
  {"defaultextension":'',"filetypes":'',"initialdir":'',...
  "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
  ......"""
    root=tkinter.Tk()
    outputtext=tkinter.filedialog.askopenfilename(
        **kwargs)
    root.destroy()
    return outputtext

def guiSaveFileName(kwargs={}):
    """Returns the path to the filename and location entered in the GUI.
*Function calls on tkFileDialog and uses those arguments
  ......
  (declare as a dictionairy)
  {"defaultextension":'',"filetypes":'',"initialdir":'',...
  "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
  ......"""
    root=tkinter.Tk()
    outputtext=tkinter.filedialog.asksaveasfilename(
        **kwargs)
    root.destroy()
    return outputtext
                  
## get boris filepath

## script
borisfilepath=guiOpenFileName({'title':'path to boris file','filetypes':[('boris file','.boris')]})
##
borisdata=grabjson(borisfilepath)
obslist=makeobslist(borisdata)
behlist=makebehlist(borisdata)

## create dictionary to hold data
dataholder={}
# build dictionairy of events
for obs in obslist:
    ##
    evtlist={'time':[i[0] for i in borisdata['observations'][obs]['events']],
             'subject':[i[1] for i in borisdata['observations'][obs]['events']],
             'behav':[i[2] for i in borisdata['observations'][obs]['events']]}

    ## still need error checking ofr unpaired state events
    beh_evt_list={}
    for b in behlist:
        beh_evt_list[b]={'all':[evtlist['time'][i] for i in range(len(evtlist['time'])) if evtlist['behav'][i]==b]}
        beh_evt_list[b]['start']=beh_evt_list[b]['all'][0::2]
        beh_evt_list[b]['stop']=beh_evt_list[b]['all'][1::2]
        beh_evt_list[b]['dur']=[beh_evt_list[b]['stop'][i]-beh_evt_list[b]['start'][i]
                                for i in range(len(beh_evt_list[b]['stop']))]
        beh_evt_list[b]['totaldur']=sum(beh_evt_list[b]['dur'])
        beh_evt_list[b]['totalcount']=len(beh_evt_list[b]['start'])
        try:
            beh_evt_list[b]['latency']=min(beh_evt_list[b]['start'])
        except:
            beh_evt_list[b]['latency']='nan'
    ## bins [settings here]
    bin_dur=300
    bin_start=0
    bin_reps=12

    bin_list={}
    for i in range(bin_reps):
        bin_list[i]={'start':i*bin_dur+bin_start,
                     'stop':(i+1)*bin_dur+bin_start,
                     'behav':{}}
        ##
        for b in behlist:
            bin_list[i]['behav'][b]={}
            ##
            bin_list[i]['behav'][b]['start']=[max(beh_evt_list[b]['start'][j],bin_list[i]['start']) for j in range(len(beh_evt_list[b]['start'])) if bin_list[i]['stop']>beh_evt_list[b]['start'][j] and bin_list[i]['start']<beh_evt_list[b]['stop'][j]]
            bin_list[i]['behav'][b]['stop']=[min(beh_evt_list[b]['stop'][j],bin_list[i]['stop']) for j in range(len(beh_evt_list[b]['stop'])) if bin_list[i]['stop']>beh_evt_list[b]['start'][j] and bin_list[i]['start']<beh_evt_list[b]['stop'][j]]
            ##
            bin_list[i]['behav'][b]['count']=len([j for j in beh_evt_list[b]['start'] if bin_list[i]['start']<=j<bin_list[i]['stop']])
            ##
            bin_list[i]['behav'][b]['dur']=[bin_list[i]['behav'][b]['stop'][j]-bin_list[i]['behav'][b]['start'][j] for j in range(len(bin_list[i]['behav'][b]['stop']))]
            ##
            bin_list[i]['behav'][b]['bindur']=sum(bin_list[i]['behav'][b]['dur'])
    dataholder[obs]={'file':borisdata['observations'][obs]['file']['1'],
                     'date':borisdata['observations'][obs]['date'],
                     'events':evtlist,
                     'beh_evt':beh_evt_list,
                     'bins':bin_list
                     }
## output a tab delimited summary
TEXTOUT=''
BASIC_HEADER='{OBS}\t{FILE}'.format(OBS='Observation', FILE='Video Filename')
BEHAV_HEADER_latency='\t'.join(['latency_'+b for b in behlist])
BEHAV_HEADER_count='\t'.join(['count_'+b for b in behlist])
BEHAV_HEADER_dur='\t'.join(['dur_'+b for b in behlist])
BIN_HEADER=''

for b in behlist:
    for i in range(bin_reps):
        BIN_HEADER+='count_'+b+'_'+str(bin_list[i]['start'])+'\t'
    for i in range(bin_reps):
        BIN_HEADER+='dur_'+b+'_'+str(bin_list[i]['start'])+'\t'
HEADER=BASIC_HEADER+'\t'+BEHAV_HEADER_latency+'\t'+BEHAV_HEADER_count+'\t'+BEHAV_HEADER_dur+'\t'+BIN_HEADER+'\n'
TEXTOUT+=HEADER
for obs in obslist:
    BASIC_Line='{OBS}\t{FILE}'.format(OBS=obs, FILE=dataholder[obs]['file'])
    BEHAV_LINE_latency='\t'.join([str(dataholder[obs]['beh_evt'][b]['latency']) for b in behlist])
    BEHAV_LINE_count='\t'.join([str(dataholder[obs]['beh_evt'][b]['totalcount']) for b in behlist])
    BEHAV_LINE_dur='\t'.join([str(dataholder[obs]['beh_evt'][b]['totaldur']) for b in behlist])
    BIN_LINE=''

    for b in behlist:
        for i in range(bin_reps):
            BIN_LINE+=str(dataholder[obs]['bins'][i]['behav'][b]['count'])+'\t'
        for i in range(bin_reps):
            BIN_LINE+=str(dataholder[obs]['bins'][i]['behav'][b]['bindur'])+'\t'
    LINETEXT=BASIC_Line+'\t'+BEHAV_LINE_latency+'\t'+BEHAV_LINE_count+'\t'+BEHAV_LINE_dur+'\t'+BIN_LINE+'\n'    
    TEXTOUT+=LINETEXT
#print(TEXTOUT)
## output to file
outputfilepath=guiSaveFileName({'title':'save output as','filetypes':[('text file','.txt')]})
##
if outputfilepath[-4:].lower()!='.txt':
    outputfilepath+='.txt'
##
with open(outputfilepath,'w') as outfile:
    outfile.write(TEXTOUT)
input('press enter to close')
