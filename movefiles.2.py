#!/usr/bin/python
'''
Created on Jan 25, 2015

@author: bogdan.bala
'''

import os
import sys
from stat import *
import re
import shutil
import logging

import datetime


downloaded = "/volume1/downloaded"
series = "/volume1/video/tvshow"
movies = "/volume1/video/movie"
music = "/volume1/music"
log = "/volume1/misc/movefiles.log"

# downloaded = "/home/bbala/test/downloaded"
# series = "/home/bbala/test/video/series"
# movies = "/home/bbala/test/video/movie"
# music = "/home/bbala/test/music"
# log = "/home/bbala/test/movefile2.log"

implementor = "link"

logging.basicConfig(level=logging.INFO, filename=log)


class ProcessingItem:
    def __init__(self):
        self.seriesName = None
        self.seasons = []
        self.downloadPath = None
        self.pathtype = None
        self.existingSerie = False
        self.type = None
        self.existingSeasons = []
        self.src = None
    def __str__(self):
        return self.seriesName+" "+str(self.seasons)+" "+self.src+" existing seasons:"+str(self.existingSeasons)


class Downloads:
    def __init__(self, folder, series, movies, music, implementor):
        self.downloaded = folder
        self.seriesFolder = series
        self.moviesFolder = movies
        self.musicFolder = music
        self.implementor = implementor
        self.processingItem = None

    '''
    listezi download folder
    '''

    def list(self):
        for pathname in os.listdir(self.downloaded):
            pathtype = self.testit(os.path.join(self.downloaded, pathname), pathname)
            self.processingItem = ProcessingItem()
            self.processingItem.pathtype = pathtype
            self.processingItem.downloadPath = pathname
            self.processingItem.src = os.path.join(self.downloaded, pathname)
            self.processItem()
            self.checkDestination()

            logging.info("processing item: "+str(self.processingItem))

            self.moveit()


    '''
    Mutam copiem sau linkam
    '''

    #def moveit(self, item, src, filename):
    def moveit(self):
        if self.processingItem.type == "serie":
            for season in self.processingItem.seasons:

                # skipping existing seasons
                if season in self.processingItem.existingSeasons:
                    logging.warn("season exists already: "+self.processingItem.seriesName+": "+season)
                    continue

                dest = os.path.join(self.seriesFolder, self.processingItem.seriesName, season)
                src = self.processingItem.src
                if len(self.processingItem.seasons) > 1:
                    # we have to go in the season folder
                    for s in os.listdir(self.processingItem.src):
                        if s.find(season) > 0:
                            src = os.path.join(self.processingItem.src, s)
                            break
                self.process(src, dest, self.processingItem.pathtype, self.processingItem.seriesName)

        if self.processingItem.type == "music":
            if not self.processingItem.existingSerie:
                dst = os.path.join(self.musicFolder, self.processingItem.seriesName)
                self.process(self.processingItem.src, dst, self.processingItem.pathtype, self.processingItem.seriesName)
            else:
                logging.warn("music exists already: "+self.processingItem.seriesName)


        if self.processingItem.type == "movie":
            if not self.processingItem.existingSerie:
                dst = os.path.join(self.moviesFolder, self.processingItem.seriesName)
                self.process(self.processingItem.src, dst, self.processingItem.pathtype, self.processingItem.seriesName)
            else:
                logging.warn("movie exists already: "+self.processingItem.seriesName)


    '''
    if this is not a series then
    check if the file is a movie or a song
    '''
    def isMusic(self):
        musicExtensions = (".mp3", ".flac", ".wav", ".pls")
        videoExtensions = (".avi", ".mkv", ".mp4", ".iso")
        videoCount = 0
        musicCount = 0
        if self.processingItem.pathtype == "dir":
            for files in os.listdir(self.processingItem.src):
                if files.endswith(videoExtensions):
                    videoCount += 1
                if files.endswith(musicExtensions):
                    musicCount += 1
        if (videoCount > musicCount):
            # print "is video", musicCount, videoCount
            return False
        else:
            # print "is music", musicCount, videoCount
            return True

    '''
    Mutam linkam copiem...
    '''
    def process(self, src, dst, type, filename):
        logging(self.implementor +" "+src+" "+dst)
        # print src, dst, type
        if type == "file":
            if implementor == "copy":
                self.copy(src, dst)
            if implementor == "move":
                self.move(src, dst)
            if implementor == "link":
                self.link(src, os.path.join(dst, filename))

        if type == "dir":
            if implementor == "copy":
                self.copyDir(src, dst)
            if implementor == "move":
                self.moveDir(src, dst)
            if implementor == "link":
                self.linkDir(src, dst)

    def move(self, src, dst):
        try:
            shutil.move(src, dst)
        except Exception as e:
            logging.warn("Moving " + src + " to: " + dst + " failed with error: " + e.message)

    def copy(self, src, dst):
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            logging.warn("Copying " + src + " to: " + dst + " failed with error: " + e.message)

    def link(self, src, dst):
        try:
            os.link(src, dst)
        except Exception as e:
            logging.warn("Linking \n" + src + " to: \n" + dst + "\nfailed with error: ".join([str(x) for x in e.args]))

    def moveDir(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)

        for file in os.listdir(src):
            if self.testit(os.path.join(src, file), file) == "dir":
                self.moveDir(os.path.join(src, file), os.path.join(dst, file))
            else:
                logging.info("trying to move file: " + file + " to: " + dst)
                self.move(os.path.join(src, file), dst)
        shutil.rmtree(src)

    def copyDir(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)

        for file in os.listdir(src):
            if self.testit(os.path.join(src, file), file) == "dir":
                self.copyDir(os.path.join(src, file), os.path.join(dst, file))
            else:
                logging.info("trying to copy file:" + file + " to: " + dst)
                self.copy(os.path.join(src, file), dst)

    def linkDir(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)

        for file in os.listdir(src):
            if self.testit(os.path.join(src, file), file) == "dir":
                self.linkDir(os.path.join(src, file), os.path.join(dst, file))
            else:
                logging.info("trying to link file:" + file + " to: " + dst)
                self.link(os.path.join(src, file), os.path.join(dst, file))

    '''
    Verific daca mai ai deja seria sau filmul respectiv
    result = item
    '''
    def checkDestination(self):
        if self.processingItem:
            if self.processingItem.type == "serie":
                for pathname in os.listdir(self.seriesFolder):
                    i = 0
                    if pathname == self.processingItem.seriesName:
                        self.processingItem.existingSerie = True
                        i += 1
                        break
                if self.processingItem.existingSerie:
                    # check if we have the season too
                    for pathname in os.listdir(os.path.join(self.seriesFolder, self.processingItem.seriesName)):
                        if pathname in self.processingItem.seasons:
                            self.processingItem.existingSeasons.append(pathname)

            if self.processingItem.type == "music":
                for pathname in os.listdir(self.musicFolder):
                    i = 0
                    if pathname == self.processingItem.seriesName:
                        self.processingItem.existingSerie = True
                        i += 1
                        break

            if self.processingItem.type == "movie":
                for pathname in os.listdir(self.moviesFolder):
                    i = 0
                    if pathname == self.processingItem.seriesName:
                        self.processingItem.existingSerie = True
                        i += 1
                        break

    '''
    Vezi daca e serie sau film
    '''
    def processItem(self):
        lastpart = self.processingItem.downloadPath
        episodnr = None

        self.processingItem.seriesName = lastpart
        # Big.Bang.Theory.S01-S04.DVDRip.&.BDRip.XviD.RoSu...
        # Big.Bang.Theory.S01.DVDRip.&.BDRip.XviD.RoSu...
        serie = re.search("[sS]\d+", lastpart)
        if serie:
            self.processingItem.type = "serie"
            # sa vedem daca avem mai multe sezoane in acelasi file:
            colectiv = re.findall("[sS]\d+", lastpart)
            # Big.Bang.Theory.S01E04.DVDRip.&.BDRip.XviD.RoSu...
            episod = re.search("[eE]\d+", lastpart)
            if episod:
                episodnr = episod.group()

            if colectiv:
                for x in colectiv:
                    self.processingItem.seasons.append(x[1:])

                if len(self.processingItem.seasons) > 1:
                    self.fillInTheMissingSeasons()

                serienume = re.split(colectiv[0], lastpart)[0][:-1]
                self.processingItem.seriesName = serienume.replace(" ", ".").lower()
                if episodnr:
                    self.processingItem.episodeNumber = episodnr[1:]
        else:
            if self.isMusic():
                self.processingItem.type = "music"
            else:
                self.processingItem.type = "movie"

    def fillInTheMissingSeasons(self):
        start = int(self.processingItem.seasons[0])
        end = int(self.processingItem.seasons[1])
        for x in range(start+1, end):
            self.processingItem.seasons.append(str(x).zfill(2))



    '''
    Vezi daca e folder file sau link
    '''
    def testit(self, pathname, lastpart):
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):
            return "dir"
        elif S_ISREG(mode):
            return "file"
        elif S_ISLINK(mode):
            return "link"
        else:
            # Unknown file type, print a message
            logging.info('Skipping ' + pathname)
            return "UNKNOWN"



        # guessed = guess_file_info(pathname)
        #print guessed  # MAIN
if len(sys.argv) <= 1:
    # print "You must provide a folder to watch, ",folder," selected"
    pass
else:
    downloaded = sys.argv[1]

if len(sys.argv) <= 2:
    # print "You must provide a folder for series, ",series," selected"
    pass
else:
    series = sys.argv[2]

if len(sys.argv) <= 3:
    # print "You must provide a folder for movies, ",movies," selected"
    pass
else:
    movies = sys.argv[3]

if len(sys.argv) <= 4:
    # print "You must provide a music folder, ",music," selected."
    pass
else:
    music = sys.argv[4]

if len(sys.argv) <= 5:
    # print "You must provide an implementor function (link, copy, move), ",implementor," selected"
    pass
else:
    implementor = sys.argv[5]

logging.info(datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
logging.info("Default: " + downloaded + " " + series + " " + movies + " " + implementor)

try:
    downloads = Downloads(downloaded, series, movies, music, implementor)
    downloads.list()
except Exception as e:
    logging.info(e)

logging.info("DONE!")
