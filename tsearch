#!/usr/bin/env python


import os
import re
import tivolib

def setup():
    from ConfigParser import ConfigParser
    import argparse

    parser = argparse.ArgumentParser(description='usage: %prog [options] tivo')
    parser.add_argument('--decrypt', '-d', action="store_true",
                        help="Decrypt the file automatically")
    parser.add_argument('--encode', '-e', action="store_true",
                        help="Re-Encode the video. (currently broken)"),
    parser.add_argument('--media', '-m', default=False,
                        help='Media Access Code from TiVo (required).'),
    parser.add_argument('--storage', '-s', default=False,
                        help="Location to store downloaded files"),
    parser.add_argument('--tivo', '-t', nargs='?', default=False,
                        help="Tivo to connect to")
    parser.add_argument('--download', action="store_true",
                        help="Download Matches")
    parser.add_argument('pattern',
                        help="Pattern to search for")
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
    if not args.storage:
        try:
            args.storage = config.get('Tivo', 'storage')
        except:
            args.storage = "."

    return args


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
    shows = tivo.listshows()
    for show in shows:
        name = show_name(show)
        if re.search(options.pattern, name):
            print name
            if options.download:
                if options.decrypt:
                    filename = name + '.mpeg'
                if options.encode:
                    filename = name + '.ogv'
                else:
                    filename = name + '.TiVo'
                print 'Downloading ' + name
                print
                if tivo.download(show, filename, path=path, decrypt=options.decrypt,
                                 encode=options.encode):
                    print '\nDownload Complete'
                else:
                    print 'Download Failed'


if __name__ == '__main__':
    main()
