#!/usr/bin/env python

###
# Simple example for using the tivolib library
##

import os
import sys
import tivolib
import re

def setup():
    from ConfigParser import ConfigParser
    from optparse import OptionParser
    options = {}
    options['tivo'] = ''
    options['media'] = 0
    options['decrypt'] = False
    options['encode'] = False
    # Read the config file
    config = ConfigParser()
    config.read([os.path.expanduser('~/.tivorc')])
    try:
        options['tivo'] = config.get('Tivo', 'host')
    except:
        pass
    try:
        options['media'] = config.get('Tivo', 'MAC')
    except:
        pass
    try:
        options['decrypt'] = config.getboolean('Tivo', 'decrypt')
    except:
        pass
    try:
        options['encode'] = config.getboolean('Tivo', 'encode')
    except:
        pass
    try:
        options['storage'] = config.get('Tivo', 'storage')
    except:
        pass

    # Read commandline options
    parser = OptionParser('usage: %prog [options] tivo')
    parser.add_option('-d', action='store_true', dest='decrypt',
        help='Decrypt the file automatically')
    parser.add_option('-e', action='store_true', dest='encode',
        help='Re-Encode the video.  Implies decrypt. (currently broken)')
    parser.add_option('-m', '--media',
        help='Media Access Code from TiVo (required).')
    parser.add_option('-s', '--storage',
        help="Location to store downloaded files")
    (optionlist, args) = parser.parse_args()
    if (len(args) == 1):
        options['tivo'] = args[0]
    if options['tivo'] == '':
        parser.error('You must specify a Tivo device to connect to')
    if (not optionlist.media) and (options['media'] == 0):
        parser.error('You must specify a Media Access Code (-m)')
    if optionlist.media:
        options['media'] = optionlist.media
    if optionlist.decrypt:
        options['decrypt'] = optionlist.decrypt
    if optionlist.encode:
        options['encode'] = optionlist.encode
    if optionlist.storage:
        options['storage'] = optionlist.storage
    return options


def progress(current, total):
    """Simple progress indicator"""
    import sys
    percentcomplete = current * 100 / total
    sys.stdout.write("\r  " + "%d%% complete" % percentcomplete)
    sys.stdout.flush()

def printshow(show):
    size = str(int(show['SourceSize']) / 1024 / 1024) + " MB"
    showinfo = size.rjust(10) + "   "
    if show.has_key('InProgress'):
      showinfo += "[In-Progress] "
    if show.has_key('CopyProtected'):
      showinfo += "[CopyProtected] "
    if show.has_key('HighDefinition'):
      if show['HighDefinition'] == "Yes":
        showinfo += "[HD] "
    showinfo += showName(show)
    return showinfo

def showName(show):
    name = show['Title']
    if show.has_key('EpisodeTitle'):
        name += ':'
        if show.has_key('EpisodeNumber') and show['EpisodeNumber'] != "0":
            name += ' [Ep. ' + show['EpisodeNumber'] + "]"
        name += ' ' + show['EpisodeTitle']
    return name

def main():
    options = setup()
    if options.has_key('storage'):
        path = options['storage']
    else:
        path = '.'
    myTivo = tivolib.tivoHandler(options['tivo'], options['media'])
    shownum = 1
    shows = myTivo.listshows()
    for show in shows:
        print str(shownum).ljust(5), 
        print printshow(show).encode('utf-8')
        shownum = shownum + 1

    while 1:
        print
        download = input('Choose show to download (0 to quit): ')
        try:
            download = int(download)
            break
        except:
            print
            print('You must enter a number.')

    if download > 0:
        myShow = shows[download-1]
        name = showName(myShow)
        # Remove unsafe filename characters
        name = re.sub('[*!]', '', name)
        if options['decrypt']:
            filename = name + '.mpeg'
            if options['encode']:
                filename = name + '.ogv'
        else:
            filename = name + '.TiVo'
        print
        print ('Downloading ' + name)
        print
        if myTivo.download(myShow, filename, path=path, decrypt=options['decrypt'], 
                           encode=options['encode'], prog=progress):
            print('\nDownload Complete')
        else:
            print('Download Failed')


if __name__ == '__main__':
    main()
