#!/usr/bin/env python

__version__ = "0.9"
__author__ = "Gregory Boyce <gregory.boyce@gmail.com>"
__copyright__ = "(c) Coypright 2010 by Gregory Boyce <gregory.boyce@gmail.com>"
__license__ = "GPL"


class TivoHandler:
    """Class for handling TiVo connections"""
    def __init__(self, mytivo, media):
        """Setup connection to the TiVo.
        Accepts mytivo variable containing the IP address or hostname of a Tivo
        device and media variable containing your Media Access Key"""
        import ssl
        self.username = "tivo"
        self.tivo = mytivo
        self.media = media
        self.connect()

    def tivo_request(self, url, stream=False):
        import requests
        requests.packages.urllib3.disable_warnings()
        from requests.auth import HTTPDigestAuth
        request = requests.get(
            url, auth=HTTPDigestAuth(self.username, self.media),
            verify=False, stream=stream)
        return request

    def connect(self):
        """Establish the initial connection"""
        test_url = "https://" + self.tivo + "/nowplaying/index.html"
        self.tivo_request(test_url)

    def listshows(self):
        """Obtain a list of shows"""
        url = "https://" + self.tivo
        url += "/TiVoConnect?Container=%2FNowPlaying&"
        url += "Command=QueryContainer&Recurse=Yes"
        request = self.tivo_request(url)
        shows = show_parser(request.text)
        shows.sort(key=lambda show: show['Title'])
        return shows


    def download(self, show, filename, path=".", decrypt=False,
                 encode=False):
        """Trigger a download for the specified TV show.
        Takes a show object as an argument."""
        import sys
        from clint.textui import progress
        myshow = show
        fullpath = path + "/" + filename
        fd = open(fullpath, 'wb')
        if encode:
            fd = tivoencode(fd)
            if not fd:
                return False
        if decrypt or encode:
            fd = tivodecrypt(fd, self.media)
            if not fd:
                return False
        r = self.tivo_request(myshow['Url'], stream=True)
        chunk_size = 1024 * 1024 # 1KB at a time
        total_length = int(r.headers['TiVo-Estimated-Length'])
        expected_size = (total_length / chunk_size) + 1
        for i in progress.bar(range(expected_size)):
            for chunk in r.raw.read(chunk_size):
                fd.write(chunk)
                fd.flush()
        return True


def show_parser(data):
    """Take a Tivo Manifest and return a list show arrays"""
    import xml.dom.minidom
    from re import sub
    shows = []
    dom = xml.dom.minidom.parseString(data)
    for show in dom.getElementsByTagName('Item'):
        myshow = {}
        details = show.getElementsByTagName('Details')[0]
        for node in details.childNodes:
            if node.localName:
                myshow[node.localName] = node.childNodes[0].data
        url = show.getElementsByTagName('Links')[0].getElementsByTagName('Url')
        myshow['Url'] = sub(":80", "", url[0].childNodes[0].data)
        shows.append(myshow)
    return shows


def tivodecrypt(outfile, media):
    """Decode a TiVo file and output an MPEG file.
    Takes the input/output files and media access code (MAC) as arguments."""
    import subprocess
    try:
        tivodecode = subprocess.Popen(
            ['tivodecode', '-m', media, "-"],
            stdin=subprocess.PIPE, stderr=open("/dev/null", 'w'),
            stdout=outfile)
    except OSError:
        print "tivodecode not found."
        return False
    return tivodecode.stdin


def tivoencode(outfile):
    """Uses fmpeg to re-encode the movie optimized for an iPad.
    Uses a recommended two step encoding process"""
    import subprocess
    try:
        encoder = subprocess.Popen(
            ['ffmpeg2theora', '-o', '-', '-'],
            stdin=subprocess.PIPE, stderr=open("/dev/null", 'w'),
            stdout=outfile)
    except OSError:
        print "ffmpeg2theora not found"
        return False
    return encoder.stdin
