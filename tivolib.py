#!/usr/bin/env python

__version__ = "0.8"
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
        r = requests.get(
            url, auth=HTTPDigestAuth(self.username, self.media),
            verify=False, stream=stream)
        return r

    def connect(self):
        """Establish the initial connection"""
        r = self.tivo_request("https://" + self.tivo + "/nowplaying/index.htl")

    def listshows(self):
        """Obtain a list of shows"""
        url = "https://" + self.tivo + \
            "/TiVoConnect?Container=%2FNowPlaying&Command=QueryContainer&Recurse=Yes"
        self.request = self.tivo_request(url)
        self.shows = show_parser(self.request.text)
        self.shows.sort(key=lambda show: show['Title'])
        return self.shows


    def download(self, show, filename, path=".", decrypt=False,
                 encode=False):
        """Trigger a download for the specified TV show.
        Takes a show object as an argument."""
        import sys
        from clint.textui import progress
        self.myshow = show
        self.fullpath = path + "/" + filename
        self.fd = open(self.fullpath, 'wb')
        if encode:
            self.fd = tivoencode(self.fd)
            if not self.fd:
                return False
        if decrypt or encode:
            self.fd = tivodecrypt(self.fd, self.media)
            if not self.fd:
                return False
        self.r = self.tivo_request(self.myshow['Url'], stream=True)
        self.chunk_size = 1024 * 1024 # 1MB at a time
        self.total_length = int(self.r.headers['TiVo-Estimated-Length'])
        self.expected_size = (self.total_length / self.chunk_size) + 1
        for self.chunk in progress.bar(
                self.r.iter_content(chunk_size=self.chunk_size), 
                expected_size = self.expected_size):
            if self.chunk:
                self.fd.write(self.chunk)
                self.fd.flush()
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
