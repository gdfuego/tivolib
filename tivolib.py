#!/usr/bin/env python

__version__ = "0.8"
__author__ = "Gregory Boyce <gboyce@badbelly.com>"
__copyright = "(c) Coypright 2010 by Gregory Boyce <gboyce@badbelly.com>"
__license__ = "GPL"


class tivoHandler():
    """Class for handling TiVo connections"""

    def __init__(self, mytivo, media):
        """Setup connection to the TiVo.
        Accepts mytivo variable containing the IP address or hostname of a Tivo
        device and media variable containing your Media Access Key"""
        self.username = "tivo"
        self.tivo = mytivo
        self.media = media
        self.connect()

    def connect(self):
        """Establish the initial connection"""
        import urllib2
        import cookielib
        self.cj = cookielib.CookieJar()
        self.ck = cookielib.Cookie(version=0, name='sid', value='0000000000000000', 
                                   port=None, port_specified=False, domain=self.tivo, 
                                   domain_specified=False, domain_initial_dot=False, 
                                   path='/', path_specified=True, secure=False, 
                                   expires=None, discard=True, comment=None, 
                                   comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.cj.set_cookie(self.ck)
        self.urlhandler = urllib2
        self.authhandler = self.urlhandler.HTTPDigestAuthHandler()
        self.authhandler.add_password("TiVo DVR", self.tivo, \
            self.username, self.media)
        self.opener = self.urlhandler.build_opener(self.authhandler, \
            self.urlhandler.HTTPCookieProcessor(self.cj))
        self.urlhandler.install_opener(self.opener)
        try:
            self.pagehandle = self.urlhandler.urlopen("https://" + self.tivo + \
              "/nowplaying/index.html")
        except IOError as e:
            if hasattr(e, 'code'):
                if e.code != 401:
                    print('We got another error')
                    print(e.code)
            else:
                print("Error 401")
                print(e.headers)
                print(e.headers['www-authenticate'])

    def listshows(self):
        """Obtain a list of shows"""
        self.pagehandle = self.urlhandler.urlopen("https://" + self.tivo + \
            "/TiVoConnect?Container=%2FNowPlaying&Command=QueryContainer&Recurse=Yes")
        self.list = self.pagehandle.readlines()[0]
        self.shows = showParser(self.list)
        self.shows.sort(key=lambda show: show['Title'])
        return self.shows

    def progress(current, total):
        """Stub Progress indicator"""
        return

    def download(self, show, filename, path=".", decrypt=False, encode=False, prog=progress):
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
        self.pagehandle = self.urlhandler.urlopen(self.myshow['Url'])
        headers = self.pagehandle.info().headers
        for header in headers:
              if header.split(" ")[0] == "TiVo-Estimated-Length:":
                  self.filesize = int(header.split(" ")[1])
        self.bs = 512 * 1024 # .5MB at a time
        self.numblocks = self.filesize // self.bs
        for count in range(1, self.numblocks):
            prog(count, self.numblocks)
            self.block = self.pagehandle.read(self.bs)
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
    Takes the input file, output file and media access code (MAC) as arguments."""
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
