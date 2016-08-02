#!/usr/bin/env python3

##############################################################################
# This class module will store an entire L5K file, breaking down the file
# into arrays of Programs, Datatypes, and Modules.  It will also store the
# entire raw data file and counts of all of the data listed above.
##############################################################################

import os
import platform
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ControllerType(object):
    Name=None
    FilePath=None
    RSfile=None
    tmpfile=None
    NumPrograms=None
    NumDataTypes=None
    NumModules=None
    NumAOIs=None
    NumENCODED=None
    L5KVersion=None
    TagStart=None
    TagEnd=None
    RawSize=None
    NumTags=None
    Tags = []             #0=tag name, 1=tag alias, 2=datatype, 3=producer

class LogixFile(QWidget):

    def __init__(self, parent=None):
        super(LogixFile, self).__init__()

        self.Ctrl = ControllerType()

    ##############################################################################
    # This routine is called when an LogixFileClass class is being created.  It
    # will set the default values for the class, then call OpenFile.  Once OpenFile
    # is complete it will assign Controller information to the Crtl structure.
    ##############################################################################
    def main(self):

        self.Ctrl.NumPrograms = 0
        self.Ctrl.NumDataTypes = 0
        self.Ctrl.NumModules = 0
        self.Ctrl.NumAOIs = 0
        self.Ctrl.NumENCODED = 0
        self.Ctrl.NumTags = 0
        self.ControllerName = ""
        self.L5KVersion = ""

        self.MaxRawFile = 500000
        self.MaxPrograms = 100
        self.MaxDataTypes = 100
        self.MaxModules = 100
        self.MaxAOIs = 10
        self.MaxENCODED = 10
        self.MaxCtrlTags = 200

        self.openFile()

        self.Ctrl.Name = self.ControllerName
        self.Ctrl.RawSize = self.RawSize
        self.Ctrl.FilePath = self.FilePath
        #self.Ctrl.tmpfile = self.tmpfile
        self.Ctrl.RSfile = self.RSfile
        self.Ctrl.L5KVersion = self.L5KVersion
        #print(self.RSfile)

    ##############################################################################
    # This routine is called from the Main routine.  It will open the L5K file,
    # create a new txt file based off of the L5K file with the tabs stripped out,
    # and call ProcessData to process each line of the L5K file.
    ##############################################################################
    def openFile(self):
        directory = os.path.realpath(__file__)
        formats = "*.L5K"
        #choosefile = QFileDialog()
        # Get file path
        self.FilePath = QFileDialog.getOpenFileName(self, "QC - Choose L5K", directory, "L5K files ({})".format(formats))
        if self.FilePath:
            #print(self.FilePath)
            # Extract Filename from Filepath
            self.RSfile = os.path.basename(self.FilePath)
            #print(os.path.basename(filepath))

        exception = None
        fh = None

        self.RawSize = 0

        try:
            for inputData in open(self.RSfile, "rU", encoding="utf-8"):
                if not inputData:
                    continue

                # strip all unwanted leading and trailing chars
                tempstr = inputData.strip(' \t\n\r')

                self.parseData(tempstr, self.RawSize)
                #self.updateStatus(inputData)

                self.RawSize += 1

        except IOError as e:
            exception = e
        finally:
            if fh is not None:
                fh.close()
            if exception is not None:
                raise exception


        # Create Tree
        #self.loadFile(fname)

    ##############################################################################
    # This routine is called from the OpenFile routine.  It will parse through the
    # L5K file one line at a time, determine where DataTypes, Routines, Programs,
    # and Modules start and end.  It will also store the names of the each of
    # those devices and any relevant information that goes with them.
    ##############################################################################
    def parseData(self, inputData, Position):

        if inputData.find("CONTROLLER ") == 0:
            tmpInputData = inputData.split()
            self.ControllerName = self.getName("CONTROLLER", tmpInputData)

        if inputData.find("Version ") == 0:
            if inputData.find("v") >= 0:
                self.L5KVersion = inputData[inputData.find("v")+1:len(inputData)]

        if inputData.find("PROGRAM ") == 0:
            tmpInputData = inputData.split()
            self.ControllerName = self.getName("PROGRAM", tmpInputData)



    ##############################################################################
    # This function is called from the ParseData routine.  It will process the
    # data passed into it and return the Program, Routine, or DataType name.
    ##############################################################################

    def getName(self, target, source):
        for i, w in enumerate(source):
            if w == target:
                return source[i+1]