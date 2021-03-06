#!/usr/bin/env python
"""
Make ica fix qc pages for all specified files and creates and index html page of summary data.

Usage:
  icafix_qc_index.py [options] <input.feat>...

Arguments:
  <input.feat>  Top directory for the output file structure

Options:
  --html-out FILE          Name [default: qc_icafix.html] (fullpath) to index html file.
  --labelfilename FILE     Name [default: fix4melview_Standard_thr20.txt] of file that contains labels.
  --csvreport FILE         Name of csv output of summary stats.
  -v,--verbose             Verbose logging
  --debug                  Debug logging in Erin's very verbose style
  -n,--dry-run             Dry run
  --help                   Print help

DETAILS
Runs makes an ica qc html page for all specified feat directories.
Writes an index page with some summary data.

Default name for --csvreport is "ica_fix_report_<labelfilename>.csv"

Written by Erin W Dickie, August 25 2015
"""
from docopt import docopt
import os
import subprocess
import glob
import sys
import pandas as pd
import numpy as np

arguments       = docopt(__doc__)
featdirs        = arguments['<input.feat>']
htmlindex       = arguments['--html-out']
icalabels       = arguments['--labelfilename']
csvfilename     = arguments['--csvreport']
VERBOSE         = arguments['--verbose']
DEBUG           = arguments['--debug']
DRYRUN          = arguments['--dry-run']
if DEBUG: print arguments

### Erin's little function for running things in the shell
def docmd(cmdlist):
    "sends a command (inputed as a list) to the shell"
    if DEBUG: print ' '.join(cmdlist)
    if not DRYRUN: subprocess.call(cmdlist)

def write_html_section(featdir, htmlhandle, IClist,SectionClass):
    SectionTitle = "{} Components".format(SectionClass)
    htmlhandle.write('<h2>'+SectionTitle+'</h2>')
    for IC in IClist:
        ## determine absolute and relative paths to the web page ica report data
        pic1 = os.path.join(featdir,'filtered_func_data.ica','report','IC_'+ str(IC) +'_thresh.png')
        pic2 = os.path.join(featdir,'filtered_func_data.ica','report','t'+ str(IC) +'.png')
        icreport = os.path.join(featdir,'filtered_func_data.ica','report','IC_'+ str(IC) +'.html')
        pic1relpath = os.path.relpath(pic1,os.path.dirname(htmlhandle.name))
        pic2relpath = os.path.relpath(pic2,os.path.dirname(htmlhandle.name))
        icreppath = os.path.relpath(icreport,os.path.dirname(htmlhandle.name))
        ## write it to the html
        htmlhandle.write('<p class="{}">\n'.format(SectionClass))
        htmlhandle.write('<a href="{}"><img src="{}"></a>\n'.format(icreppath,pic1relpath))
        htmlhandle.write('<a href="{}"><img src="{}">{}</a><br>\n'.format(icreppath,pic2relpath,icreppath))
        htmlhandle.write('<input type="radio" name="IC{}" value="Signal"'.format(IC))
        if SectionClass == "Signal": htmlhandle.write(' checked="checked"')
        htmlhandle.write('> Signal')
        htmlhandle.write('<input type="radio" name="IC{}" value="Noise"'.format(IC))
        if SectionClass == "Noise": htmlhandle.write(' checked="checked"')
        htmlhandle.write('> Noise')
        htmlhandle.write('</p>\n')

def get_SignalandNoise(inputdir, inputlabelfile, numICs) :
    labelpath = os.path.join(inputdir,inputlabelfile)
    if os.path.isfile(labelpath):
        a=open(labelpath,'rb')
        lines = a.readlines()
        if lines:
            first_line = lines[:1]
            last_line = lines[-1]
        bad_ica = last_line.split(',')
        for i in range(len(bad_ica)):
            bad_ica[i] = bad_ica[i].replace('[','')
            bad_ica[i] = bad_ica[i].replace(']','')
            bad_ica[i] = bad_ica[i].replace(' ','')
            bad_ica[i] = bad_ica[i].replace('\n','')
        bad_ica = map(int,bad_ica)
    else:
        sys.exit("IC labels file {} not found".format(labelpath))

    if  max(bad_ica) > numICs:
        print("We have a problem, more labels in {} than ICs".format(inputlabelfile))
        print("Number of ICs: {}".format(numICs))
        print("Labeled Bad ICs {}".format(bad_ica))

    good_ica = list(set(range(1,numICs+1)) - set(bad_ica))
    return(good_ica,bad_ica)

def write_featdir_html(featdir, htmlpath, signal, noise, htmltitle):

    handlablefile = os.path.join(featdir, "hand_labels_noise.txt")
    handlabelrelpath = os.path.relpath(handlablefile,os.path.dirname(htmlpath))
    htmlpage = open(htmlpath,'w')
    htmlpage.write('<HTML><TITLE>'+htmltitle+'</TITLE>')
    htmlpage.write('<head>\n')
    htmlpage.write('<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>')
    htmlpage.write('<style>\n')
    htmlpage.write('body { background-color:#333333; '
                    'font-family: futura,sans-serif;color:white;\n'
                    'text-align: center;}\n')
    htmlpage.write('p.Signal {background-color:#009999;}\n')
    htmlpage.write('p.Noise {background-color:#ff4000;}\n')
    htmlpage.write('img {width:800; display: block;margin-left: auto;margin-right: auto }\n')
    htmlpage.write('h2 {color:white; }\n')
    htmlpage.write('</style></head>\n')
    htmlpage.write('<BODY>\n')
    htmlpage.write('<form action="{}" method="post" id="main">\n'.format(handlabelrelpath))
    htmlpage.write('<h1>Components for '+ featdir +'</h1>')

    ## Signal for both
    write_html_section(featdir, htmlpage, signal,"Signal")

    ## add a break
    htmlpage.write('<br>\n')

    ## Signal for both
    write_html_section(featdir, htmlpage, noise,"Noise")

    ## finish the file
    htmlpage.write('<br>\n')
    htmlpage.write('<input type="submit" name="submit" value="Show/Update Labels"></br>\n</form>\n')
    htmlpage.write('<br><h3>To write handlabels copy this line into the terminal:</h3>\n')
    htmlpage.write('<br><p>echo "<span id="output"></span>')
    htmlpage.write('" > ' + handlablefile + '</p><br>\n')

    htmlpage.write('<script type="text/javascript">\n')
    htmlpage.write('$("#main").submit(function(e) {\n')
    htmlpage.write('  e.preventDefault();\n')
    htmlpage.write('  var handlabels = "[";\n')

    for IC in range(1, len(signal) + len(noise) + 1):
        htmlpage.write('  if ($("input[name=IC' + str(IC) +']:checked").val() == "Noise") ')
        htmlpage.write('{handlabels += "'+ str(IC) +', ";}\n')

    htmlpage.write('  handlabels = handlabels.substring(0,handlabels.length - 2) + "]";\n')
    htmlpage.write('  $("#output").text(handlabels);\n});\n</script>\n')

    htmlpage.write('</BODY>\n</HTML>\n')
    htmlpage.close() # you can omit in most cases as the destructor will call it


## Start the index html file
htmlindex = open(htmlindex,'w')
htmlindex.write('<HTML><TITLE> ICA FIX qc index </TITLE>\n'
                '<head>\n<style>\n'
                'body { background-color:#333333; '
                'font-family: futura,sans-serif;'
                'color:white;text-align: center;}\n'
                'a {color:#99CCFF;}\n'
                'table { margin: 25px auto; '
                '        border-collapse: collapse;'
                '        text-align: left;'
                '        width: 98%; '
                '        border: 1px solid grey;'
                '        border-bottom: 2px solid #00cccc;} \n'
                'th {background: #00cccc;\n'
                'color: #fff;'
                'text-transform: uppercase;};'
                'td {border-top: thin solid;'
                '    border-bottom: thin solid;}\n'
                '</style></head>\n')

## naming convention for individual html files from labelname
labelbasename = os.path.splitext(icalabels)[0]
htmltitle="{} ICA labels".format(labelbasename)

## check that the csvreport exists
if not csvfilename:
    csvfilename = "ica_fix_report_{}.csv".format(labelbasename)

## load the pandas dataframe
csvreport = pd.DataFrame({ 'featdir' : pd.Categorical(featdirs),
                           'labelfile' : labelbasename,
                           'PercentExcluded' : np.empty([len(featdirs)], dtype=int),
                           'NumSignal' : np.empty([len(featdirs)], dtype=int),
                           'numICs' : np.empty([len(featdirs)], dtype=int)})
#csvreport = loadreportcsv(csvfilename,featdirs)
#csvreport.labelfile = icalabels

## add the title
htmlindex.write('<h1>ICA FIX qc index</h1>')
htmlindex.write('<h2>Labels: {}</h2>'.format(labelbasename))

## add the table header
htmlindex.write('<table>'
                '<tr><th>Path</th>'
                '<th>Percent Excluded</th>'
                '<th>Number Signal ICs</th>'
                '<th>Total ICs</th></tr>')

for featdir in featdirs:
    ## get the number of ICA components from the report length
    ICpngs = glob.glob(os.path.join(featdir,'filtered_func_data.ica','report','IC_*_thresh.png'))
    numICs = len(ICpngs)

    ## use function to get good and bad
    signalICs, noiseICs = get_SignalandNoise(featdir, icalabels, numICs)

    ## write the featdir's html file
    featdirhtml = os.path.join(featdir,"{}_labels_report.html".format(labelbasename))
    write_featdir_html(featdir, featdirhtml, signalICs, noiseICs, "{} ICA labels".format(labelbasename))

    ## print relative link to index
    featdir_relpath = os.path.relpath(featdirhtml,os.path.dirname(htmlindex.name))
    featdir_relname = os.path.dirname(featdir_relpath)

    htmlindex.write('<tr>') ## table new row
    htmlindex.write('<td>') ## first data cell
    htmlindex.write('<a href="{}">{}</a>'.format(featdir_relpath,featdir_relname))
    htmlindex.write('</td>') ## end of cell

    ## print basic stats - % excluded, total IC's number kept, total ICs
    PercentExcluded = round(float(len(noiseICs))/float(numICs)*100)
    NumSignal = len(signalICs)
    htmlindex.write("<td>{}</td><td>{}</td><td>{}</td>".format(PercentExcluded,NumSignal,numICs))
    htmlindex.write('</tr>')

    ## write this info to csvreport
    idx = csvreport[csvreport.featdir == featdir].index[0]
    csvreport[idx,'PercentExcluded'] = PercentExcluded
    csvreport[idx,'NumSignal'] = NumSignal
    csvreport[idx,'numICs'] = numICs


## finish the file
htmlindex.write('</table>\n')
htmlindex.write('</BODY></HTML>\n')
htmlindex.close() # you can omit in most cases as the destructor will call it

## write the results out to a file
csvreport.to_csv(csvfilename, sep=',', index = False)
