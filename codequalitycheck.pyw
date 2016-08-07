#!/usr/bin/env python3
# Copyright (c) 2008-10 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import platform
import sys
import copy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import helpform
import newimagedlg
import treeofplc
import qrc_resources
import logixfile


__version__ = "1.0.1"

class ServerModel(treeofplc.TreeOfPLCModel):

    def __init__(self, parent=None):
        super(ServerModel, self).__init__(parent)

    def data(self, index, role):
        if role == Qt.DecorationRole:
            node = self.nodeFromIndex(index)
            if node is None:
                return None
            if isinstance(node, treeofplc.BranchNode):
                if index.column() != 0:
                    return None
                filename = node.toString().replace(" ", "_")
                parent = node.parent.toString()
                if parent and parent != "USA":
                    return None
                if parent == "USA":
                    filename = "USA_" + filename
                filename = os.path.join(os.path.dirname(__file__),
                                        "flags", filename + ".png")
                pixmap = QPixmap(filename)
                if pixmap.isNull():
                    return None
                return pixmap
        return treeofplc.TreeOfPLCModel.data(self, index, role)

class TreeOfPLCWidget(QTreeView):

    def __init__(self, filename, nesting, separator, parent=None):
        super(TreeOfPLCWidget, self).__init__(parent)
        self.setSelectionBehavior(QTreeView.SelectItems)
        self.setUniformRowHeights(True)
        model = ServerModel(self)
        self.setModel(model)
        try:
            model.load(filename, nesting, separator)
        except IOError as e:
            QMessageBox.warning(self, "Server Info - Error", e)
        self.connect(self, SIGNAL("activated(QModelIndex)"),
                     self.activated)
        self.connect(self, SIGNAL("expanded(QModelIndex)"),
                     self.expanded)
        self.expanded()

    def currentFields(self):
        return self.model().asRecord(self.currentIndex())


    def activated(self, index):
        self.emit(SIGNAL("activated"), self.model().asRecord(index))


    def expanded(self):
        for column in range(self.model().columnCount(
                            QModelIndex())):
            self.resizeColumnToContents(column)

class MainWindow(QMainWindow):

    def __init__(self, filename, nesting, separator, parent=None):
        super(MainWindow, self).__init__(parent)

        self.image = QImage()
        self.dirty = False
        self.filename = None
        self.mirroredvertically = False
        self.mirroredhorizontally = False

        treeDockWidget = QDockWidget("Explore", self)
        treeDockWidget.setObjectName("TreeDockWidget")
        treeDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|
                                     Qt.RightDockWidgetArea)

        headers = ["Country/State (US)/City/Provider", "Server", "IP"]
        if nesting != 3:
            if nesting == 1:
                headers = ["Country/State (US)", "City", "Provider",
                           "Server"]
            elif nesting == 2:
                headers = ["Country/State (US)/City", "Provider",
                           "Server"]
            elif nesting == 4:
                headers = ["Country/State (US)/City/Provider/Server"]
            headers.append("IP")

        self.treeWidget = TreeOfPLCWidget(filename, nesting, separator)
        self.treeWidget.model().headers = headers
        #self.setCentralWidget(self.treeWidget)

        QShortcut(QKeySequence("Escape"), self, self.close)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

        self.connect(self.treeWidget, SIGNAL("activated"),
                     self.activated)


        #self.listWidget = QListWidget()
        treeDockWidget.setWidget(self.treeWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, treeDockWidget)

        logDockWidget = QDockWidget("Log", self)
        logDockWidget.setObjectName("LogDockWidget")
        logDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|
                                      Qt.RightDockWidgetArea|
                                      Qt.BottomDockWidgetArea)

#        self.listWidget = QListWidget()
        self.browserWidget = QTextBrowser()
        logDockWidget.setWidget(self.browserWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, logDockWidget)

        self.imageLabel = QLabel()
        self.imageLabel.setMinimumSize(200, 200)
        self.imageLabel.setAlignment(Qt.AlignRight)
        self.imageLabel.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setCentralWidget(self.imageLabel)

        self.printer = None

        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Ready", 5000)

        fileNewAction = self.createAction("&New...", self.fileNew,
                QKeySequence.New, "filenew", "Create an image file")
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "fileopen",
                "Open an existing image file")
        fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "filesave", "Save the image")
        fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, icon="filesaveas",
                tip="Save the image using a new name")
        filePrintAction = self.createAction("&Print", self.filePrint,
                QKeySequence.Print, "fileprint", "Print the image")
        fileQuitAction = self.createAction("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")

        editSearchAction = self.createAction("&Search",
                self.editSearch, "Ctrl+F", "editsearch",
                "search L5K")

        editInvertAction = self.createAction("&Invert",
                self.editInvert, "Ctrl+I", "editinvert",
                "Invert the image's colors", True, "toggled(bool)")
        editSwapRedAndBlueAction = self.createAction("Sw&ap Red and Blue",
                self.editSwapRedAndBlue, "Ctrl+A", "editswap",
                "Swap the image's red and blue color components", True,
                "toggled(bool)")
        editZoomAction = self.createAction("&Zoom...", self.editZoom,
                "Alt+Z", "editzoom", "Zoom the image")
        mirrorGroup = QActionGroup(self)
        editUnMirrorAction = self.createAction("&Unmirror",
                self.editUnMirror, "Ctrl+U", "editunmirror",
                "Unmirror the image", True, "toggled(bool)")
        mirrorGroup.addAction(editUnMirrorAction)
        editMirrorHorizontalAction = self.createAction(
                "Mirror &Horizontally", self.editMirrorHorizontal,
                "Ctrl+H", "editmirrorhoriz",
                "Horizontally mirror the image", True, "toggled(bool)")
        mirrorGroup.addAction(editMirrorHorizontalAction)
        editMirrorVerticalAction = self.createAction(
                "Mirror &Vertically", self.editMirrorVertical,
                "Ctrl+V", "editmirrorvert",
                "Vertically mirror the image", True, "toggled(bool)")
        mirrorGroup.addAction(editMirrorVerticalAction)
        editUnMirrorAction.setChecked(True)

        toolGroup = QActionGroup(self)
        toolHardware = self.createAction("&Hardware",
        self.toolSafety, "Alt+H", "toolhardware",
        "Hardware Check", True, "toggled(bool)")
        toolGroup.addAction(toolHardware)
        toolSafety = self.createAction("&Safety",
                self.toolSafety, "Alt+S", "toolsafety",
                "Safety Configuration Check", True, "toggled(bool)")
        toolGroup.addAction(toolSafety)
        toolHardware.setChecked(True)

        helpAboutAction = self.createAction("&About Image Changer",
                self.helpAbout)
        helpHelpAction = self.createAction("&Help", self.helpHelp,
                QKeySequence.HelpContents)

        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (fileNewAction, fileOpenAction,
                fileSaveAction, fileSaveAsAction, None, filePrintAction,
                fileQuitAction)
        self.connect(self.fileMenu, SIGNAL("aboutToShow()"),
                     self.updateFileMenu)
        editMenu = self.menuBar().addMenu("&Edit")

        #search
        # self.addActions(editMenu, (editSearchAction,
        #         editSwapRedAndBlueAction, editZoomAction))

        # mirrorMenu = editMenu.addMenu(QIcon(":/editzoom.png"),
        #                               "&Search L5K")

        self.addActions(editMenu, (editSearchAction, editInvertAction, editSwapRedAndBlueAction, editZoomAction))

        mirrorMenu = editMenu.addMenu(QIcon(":/editmirror.png"),
                                      "&Mirror")
        self.addActions(mirrorMenu, (editUnMirrorAction,
                editMirrorHorizontalAction, editMirrorVerticalAction))
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        self.addActions(fileToolbar, (fileNewAction, fileOpenAction,
                                      fileSaveAsAction))

        editToolbar = self.addToolBar("Edit")
        editToolbar.setObjectName("EditToolBar")
        self.addActions(editToolbar, (editInvertAction,
                editSwapRedAndBlueAction, editUnMirrorAction,
                editMirrorVerticalAction, editMirrorHorizontalAction))

        selectToolbar = self.addToolBar("Tool")
        selectToolbar.setObjectName("SelectToolBar")
        self.addActions(selectToolbar, (toolHardware,
                                        toolSafety))

        self.zoomSpinBox = QSpinBox()
        self.zoomSpinBox.setRange(1, 400)
        self.zoomSpinBox.setSuffix(" %")
        self.zoomSpinBox.setValue(100)
        self.zoomSpinBox.setToolTip("Zoom the image")
        self.zoomSpinBox.setStatusTip(self.zoomSpinBox.toolTip())
        self.zoomSpinBox.setFocusPolicy(Qt.NoFocus)
        self.connect(self.zoomSpinBox,
                     SIGNAL("valueChanged(int)"), self.showImage)
        editToolbar.addWidget(self.zoomSpinBox)

        self.addActions(self.imageLabel, (editSearchAction, editInvertAction,
                editSwapRedAndBlueAction, editUnMirrorAction,
                editMirrorVerticalAction, editMirrorHorizontalAction))

        self.resetableActions = ((editInvertAction, False),
                                 (editSwapRedAndBlueAction, False),
                                 (editUnMirrorAction, True))

        settings = QSettings()
        self.recentFiles = settings.value("RecentFiles") or []
        self.restoreGeometry(settings.value("MainWindow/Geometry",
                QByteArray()))
        self.restoreState(settings.value("MainWindow/State",
                QByteArray()))
        
        self.setWindowTitle("QC")
        self.updateFileMenu()
        QTimer.singleShot(0, self.loadInitialFile)

    def picked(self):
        return self.treeWidget.currentFields()


    def activated(self, fields):
        self.statusBar().showMessage("*".join(fields), 60000)


    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def closeEvent(self, event):
        #if self.okToContinue():
            settings = QSettings()
            settings.setValue("LastFile", self.filename)
            settings.setValue("RecentFiles", self.recentFiles or [])
            settings.setValue("MainWindow/Geometry", self.saveGeometry())
            settings.setValue("MainWindow/State", self.saveState())
        #else:
        #    event.ignore()


    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self,
                    "Image Changer - Unsaved Changes",
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.fileSave()
        return True


    def loadInitialFile(self):
        settings = QSettings()
        fname = settings.value("LastFile")
        if fname and QFile.exists(fname):
            self.loadFile(fname)

    def updateLog(self, message, color):
        self.statusBar().showMessage(message, 5000)
        #self.browserWidget.addItem(message)
        self.browserWidget.append("<font color={}>{}</font>".format(color), format(message))

    def updateStatus(self, message):
        self.statusBar().showMessage(message, 5000)
        #self.browserWidget.addItem(message)
        self.browserWidget.append("<font color=blue>{}</font>".format(message))
        # if self.filename:
        #     self.setWindowTitle("Image Changer - {}[*]".format(
        #                         os.path.basename(self.filename)))
        # elif not self.image.isNull():
        #     self.setWindowTitle("Image Changer - Unnamed[*]")
        # else:
        #     self.setWindowTitle("Image Changer[*]")
        # self.setWindowModified(self.dirty)


    def updateFileMenu(self):
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = self.filename
        recentFiles = []
        for fname in self.recentFiles:
            if fname != current and QFile.exists(fname):
                recentFiles.append(fname)
        if recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QAction(QIcon(":/icon.png"),
                        "&{} {}".format(i + 1, QFileInfo(
                        fname).fileName()), self)
                action.setData(fname)
                self.connect(action, SIGNAL("triggered()"),
                             self.loadFile)
                self.fileMenu.addAction(action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])


    def fileNew(self):
        if not self.okToContinue():
            return
        dialog = newimagedlg.NewImageDlg(self)
#        dialog = ui_newimagedlg.Ui_NewImageDlg()
        if dialog.exec_():
            self.addRecentFile(self.filename)
            self.image = QImage()
            for action, check in self.resetableActions:
                action.setChecked(check)
            self.image = dialog.image()
            self.filename = None
            self.dirty = True
            self.showImage()
            self.sizeLabel.setText("{} x {}".format(self.image.width(),
                                                      self.image.height()))
            self.updateStatus("Created new image")


    def fileOpen(self):
        lgxCtrl = logixfile.LogixFile()
        # if not self.okToContinue():
        #     return
        # dir = (os.path.dirname(self.filename)
        #         if self.filename is not None else ".")
        # formats = "*.L5K"
        # fname = QFileDialog.getOpenFileName(self, "QC - Choose L5K", dir, "L5K files ({})".format(formats))
        # if fname:
        #     self.loadFile(fname)

        if lgxCtrl.ControllerName:
            self.updateStatus(lgxCtrl.ControllerName)
            self.updateStatus(lgxCtrl.L5KVersion)

            for index in lgxCtrl.LgxProgram:
                self.updateStatus("{}, Start={}, End={}".format(index.Name, index.Start, index.End ))

            for ptask in lgxCtrl.LgxTask:
                self.updateStatus("BEGIN TASK")
                self.updateStatus(ptask.Name)
                for pprog in ptask.Program:
                    self.updateStatus(pprog)
                self.updateStatus("END TASK")
                self.updateStatus("")

        elif os.path.basename(lgxCtrl.FilePath) == "":
            self.updateStatus("No file selected")


    def loadFile(self, fname=None):
        if fname is None:
            action = self.sender()
            if isinstance(action, QAction):
                fname = action.data()
                if not self.okToContinue():
                    return
            else:
                return
        if fname:
            self.filename = None
            image = QImage(fname)
            if image.isNull():
                message = "Failed to read {}".format(fname)
            else:
                self.addRecentFile(fname)
                self.image = QImage()
                for action, check in self.resetableActions:
                    action.setChecked(check)
                self.image = image
                self.filename = fname
                self.showImage()
                self.dirty = False
                self.sizeLabel.setText("{} x {}".format(
                                       image.width(), image.height()))
                message = "Loaded {}".format(os.path.basename(fname))
            self.updateStatus(message)


    def addRecentFile(self, fname):
        if fname is None:
            return
        if fname not in self.recentFiles:
            self.recentFiles = [fname] + self.recentFiles[:8]


    def fileSave(self):
        if self.image.isNull():
            return True
        if self.filename is None:
            return self.fileSaveAs()
        else:
            if self.image.save(self.filename, None):
                self.updateStatus("Saved as {}".format(self.filename))
                self.dirty = False
                return True
            else:
                self.updateStatus("Failed to save {}".format(
                                  self.filename))
                return False


    def fileSaveAs(self):
        if self.image.isNull():
            return True
        fname = self.filename if self.filename is not None else "."
        formats = (["*.{}".format(format.data().decode("ascii").lower())
                for format in QImageWriter.supportedImageFormats()])
        fname = QFileDialog.getSaveFileName(self,
                "Image Changer - Save Image", fname,
                "Image files ({})".format(" ".join(formats)))
        if fname:
            if "." not in fname:
                fname += ".png"
            self.addRecentFile(fname)
            self.filename = fname
            return self.fileSave()
        return False


    def filePrint(self):
        if self.image.isNull():
            return
        if self.printer is None:
            self.printer = QPrinter(QPrinter.HighResolution)
            self.printer.setPageSize(QPrinter.Letter)
        form = QPrintDialog(self.printer, self)
        if form.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.image.size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(),
                                size.height())
            painter.drawImage(0, 0, self.image)


    def editSearch(self):
        self.updateStatus("Search the RSLogix L5K File")
        l5kfilename = "AD010B02_s.L5K"

        exception = None
        fh = None

        try:
            for line in open(l5kfilename, "rU", encoding="utf-8"):
                if not line:
                    continue
                #self.addRecord(line.split(separator), False)
                #self.updateLog(line, "Red")
                self.updateStatus(line)

        except IOError as e:
            exception = e
        finally:
            if fh is not None:
                fh.close()
            # for i in range(self.columns):
            #     self.headers.append("Column #{}".format(i))
            if exception is not None:
                raise exception



    def editInvert(self, on):
        if self.image.isNull():
            return
        self.image.invertPixels()
        self.showImage()
        self.dirty = True
        self.updateStatus("Inverted" if on else "Uninverted")


    def editSwapRedAndBlue(self, on):
        if self.image.isNull():
            return
        self.image = self.image.rgbSwapped()
        self.showImage()
        self.dirty = True
        self.updateStatus(("Swapped Red and Blue"
                           if on else "Unswapped Red and Blue"))


    def editUnMirror(self, on):
        if self.image.isNull():
            return
        if self.mirroredhorizontally:
            self.editMirrorHorizontal(False)
        if self.mirroredvertically:
            self.editMirrorVertical(False)


    def editMirrorHorizontal(self, on):
        if self.image.isNull():
            return
        self.image = self.image.mirrored(True, False)
        self.showImage()
        self.mirroredhorizontally = not self.mirroredhorizontally
        self.dirty = True
        self.updateStatus(("Mirrored Horizontally"
                           if on else "Unmirrored Horizontally"))


    def editMirrorVertical(self, on):
        if self.image.isNull():
            return
        self.image = self.image.mirrored(False, True)
        self.showImage()
        self.mirroredvertically = not self.mirroredvertically
        self.dirty = True
        self.updateStatus(("Mirrored Vertically"
                           if on else "Unmirrored Vertically"))


    def editZoom(self):
        if self.image.isNull():
            return
        percent, ok = QInputDialog.getInteger(self,
                "Image Changer - Zoom", "Percent:",
                self.zoomSpinBox.value(), 1, 400)
        if ok:
            self.zoomSpinBox.setValue(percent)

    def toolSafety(self, on):
        self.dirty = True

    def toolHardware(self, on):
        self.dirty = True


    def showImage(self, percent=None):
        if self.image.isNull():
            return
        if percent is None:
            percent = self.zoomSpinBox.value()
        factor = percent / 100.0
        width = self.image.width() * factor
        height = self.image.height() * factor
        image = self.image.scaled(width, height, Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(QPixmap.fromImage(image))


    def helpAbout(self):
        QMessageBox.about(self, "About Image Changer",
                """<b>Image Changer</b> v {0}
                <p>Copyright &copy; 2008-10 Qtrac Ltd. 
                All rights reserved.
                <p>This application can be used to perform
                simple image manipulations.
                <p>Python {1} - Qt {2} - PyQt {3} on {4}""".format(
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR,
                platform.system()))


    def helpHelp(self):
        form = helpform.HelpForm("index.html", self)
        form.show()


def main():
    app = QApplication(sys.argv)
    nesting = 3
    if len(sys.argv) > 1:
        try:
            nesting = int(sys.argv[1])
        except:
            pass
        if nesting not in (1, 2, 3, 4):
            nesting = 3


    app.setOrganizationName("Qtrac Ltd.")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("CheckTool")
    app.setWindowIcon(QIcon(":/gmlogo.png"))

    form = MainWindow(os.path.join(os.path.dirname(__file__), "servers.txt"),nesting, "*")

    form.show()
    app.exec_()


main()