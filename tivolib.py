#!/usr/bin/env python

__version__ = "0.8"
__author__ = "Gregory Boyce <gboyce@badbelly.com>"
__copyright__ = "(c) Coypright 2010 by Gregory Boyce <gboyce@badbelly.com>"
__license__ = "GPL"


class tivoHandler():
    """Class for handling TiVo connections"""
    def __init__(self, mytivo, media):
        """Setup connection to the TiVo.
        Accepts mytivo variable containing the IP address or hostname of a Tivo
        device and media variable containing your Media Access Key"""
        import ssl
        self.username = "tivo"
        self.tivo = mytivo
        self.media = media
        self.context = ssl._create_unverified_context()
        self.connect()

    def tivo_request(self, url, stream=False):
        import requests
        requests.packages.urllib3.disable_warnings()
        from requests.auth import HTTPDigestAuth
        r = requests.get(url, auth=HTTPDigestAuth(self.username, self.media), verify=False, stream=stream)
        return r

    def connect(self):
        """Establish the initial connection"""
        r = self.tivo_request("https://" + self.tivo + "/nowplaying/index.htl")

    def listshows(self):
        """Obtain a list of shows"""
        url = "https://" + self.tivo + \
            "/TiVoConnect?Container=%2FNowPlaying&Command=QueryContainer&Recurse=Yes"
        self.r = self.tivo_request(url)
        self.shows = showParser(self.r.text)
        self.shows.sort(key=lambda show: show['Title'])
        return self.shows

    def progress(current, total):
        """Stub Progress indicator"""
        return

    def download(self, show, filename, path=".", decrypt=False, 
            encode=False, prog=progress):
        """Trigger a download for the specified TV show.
        Takes a show object as an argument."""
        import sys
        self.myshow = show
        self.fullpath = path + "/" + filename
        self.fd = open(self.fullpath, 'wb')
        if encode:
            self.fd = tivoencode(self.fd)
            if self.fd == False:
              return False
        if decrypt or encode:
            self.fd = tivodecrypt(self.fd, self.media)
            if self.fd == False:
              return False
        self.r = self.tivo_request(self.myshow['Url'], stream=True)
        self.filesize = int(self.r.headers['TiVo-Estimated-Length'])
        self.bs = 512 * 1024 # .5MB at a time
        self.numblocks = self.filesize // self.bs
        for count in range(1, self.numblocks):
            prog(count, self.numblocks)
            self.block = self.r.raw.read(self.bs)
            self.fd.write(self.block)
        prog(self.numblocks, self.numblocks)
        self.block = self.pagehandle.read(self.filesize % self.bs)
        self.fd.write(self.block)
        self.fd.close()
        return True


def showParser(data):
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
        Url = show.getElementsByTagName('Links')[0].getElementsByTagName('Url')
        myshow['Url'] =  sub(":80", "", Url[0].childNodes[0].data)
        shows.append(myshow)
    return shows


def tivodecrypt(outfile, media):
    """Decode a TiVo file and output an MPEG file.
    Takes the input/output files and media access code (MAC) as arguments."""
    import subprocess
    try:
      tivodecode = subprocess.Popen(['tivodecode', '-m', media, "-"],
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
     encoder = subprocess.Popen(['ffmpeg2theora', '-o', '-', '-'],
       stdin=subprocess.PIPE, stderr=open("/dev/null", 'w'),
       stdout=outfile)
   except OSError:
     print "ffmpeg2theora not found"
     return False
   return encoder.stdin
