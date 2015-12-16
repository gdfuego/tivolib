#!/usr/bin/env python

###
# Simple example for using the tivolib library
##

import os
import re
import tivolib

def setup():
    from ConfigParser import ConfigParser
    import argparse

    parser = argparse.ArgumentParser(description='usage: %prog [options] tivo')
    parser.add_argument('--decrypt', '-d', action="store_true", default=False,
                        help="Decrypt the file automatically")
    parser.add_argument('--encode', '-e', action="store_true", default=False,
                        help="Re-Encode the video. (currently broken)"),
    parser.add_argument('--media', '-m', default=False,
                        help='Media Access Code from TiVo (required).'),
    parser.add_argument('-s', '--storage', default=".",
                        help="Location to store downloaded files"),
    parser.add_argument("tivo", nargs='?', default=False,
                        help="Tivo to connect to")
    args = parser.parse_args()

    config = ConfigParser()
    config.read([os.path.expanduser('~/.tivorc')])

    if not args.tivo:
        try:
            args.tivo = config.get('Tivo', 'host')
        except:
            parser.error('You must specify a Tivo device to connect to')
    if not args.media:
        try:
            args.media = config.get('Tivo', 'MAC')
        except:
            parser.error('You must specify a Media Access Code (-m)')
    if not args.decrypt:
        try:
            args.decrypt = config.getboolean('Tivo', 'decrypt')
        except:
            pass
    if not args.encode:
        try:
            args.encode = config.getboolean('Tivo', 'encode')
        except:
            pass
    if args.storage == ".":
        try:
            args.storage = config.get('Tivo', 'storage')
        except:
            pass

    return args


def print_show(show):
    size = str(int(show['SourceSize']) / 1024 / 1024) + " MB"
    showinfo = size.rjust(10) + "   "
    if show.has_key('InProgress'):
        showinfo += "[In-Progress] "
    if show.has_key('CopyProtected'):
        showinfo += "[CopyProtected] "
    if show.has_key('HighDefinition'):
        if show['HighDefinition'] == "Yes":
            showinfo += "[HD] "
    showinfo += show_name(show)
    return showinfo


def show_name(show):
    name = show['Title']
    if show.has_key('EpisodeTitle'):
        name += ':'
        if show.has_key('EpisodeNumber') and show['EpisodeNumber'] != "0":
            name += ' [Ep. ' + show['EpisodeNumber'] + "]"
        name += ' ' + show['EpisodeTitle']
    return name


def main():
    options = setup()
    path = options.storage
    tivo = tivolib.TivoHandler(options.tivo, options.media)
    shownum = 1
    shows = tivo.listshows()
    for show in shows:
        print str(shownum).ljust(5),
        print print_show(show).encode('utf-8')
        shownum = shownum + 1

    while 1:
        print
        download = raw_input('Choose show to download (0 to quit): ')
        try:
            download = int(download)
            break
        except:
            print
            print 'You must enter a number.'

    if download > 0:
        show = shows[download-1]
        name = show_name(show)
        # Remove unsafe filename characters
        name = re.sub('[*!]', '', name)
        if options.decrypt:
            filename = name + '.mpeg'
            if options.encode:
                filename = name + '.ogv'
        else:
            filename = name + '.TiVo'
        print
        print 'Downloading ' + name
        print
        if tivo.download(show, filename, path=path, decrypt=options.decrypt,
                         encode=options.encode):
            print '\nDownload Complete'
        else:
            print 'Download Failed'


if __name__ == '__main__':
    main()
