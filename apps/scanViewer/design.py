# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1084, 664)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../nmutils/resources/N.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setMargin(10)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.diffPlot = Plot2D(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.diffPlot.sizePolicy().hasHeightForWidth())
        self.diffPlot.setSizePolicy(sizePolicy)
        self.diffPlot.setObjectName(_fromUtf8("diffPlot"))
        self.horizontalLayout.addWidget(self.diffPlot)
        self.mapPlot = Plot2D(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapPlot.sizePolicy().hasHeightForWidth())
        self.mapPlot.setSizePolicy(sizePolicy)
        self.mapPlot.setObjectName(_fromUtf8("mapPlot"))
        self.horizontalLayout.addWidget(self.mapPlot)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.browseButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseButton.sizePolicy().hasHeightForWidth())
        self.browseButton.setSizePolicy(sizePolicy)
        self.browseButton.setMaximumSize(QtCore.QSize(1000000, 16777215))
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.gridLayout.addWidget(self.browseButton, 1, 2, 1, 1)
        self.scanClassBox = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scanClassBox.sizePolicy().hasHeightForWidth())
        self.scanClassBox.setSizePolicy(sizePolicy)
        self.scanClassBox.setMinimumSize(QtCore.QSize(100, 0))
        self.scanClassBox.setBaseSize(QtCore.QSize(200, 0))
        self.scanClassBox.setMaxVisibleItems(100)
        self.scanClassBox.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.scanClassBox.setObjectName(_fromUtf8("scanClassBox"))
        self.gridLayout.addWidget(self.scanClassBox, 0, 1, 1, 1)
        self.logoLabel = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMinimumSize(QtCore.QSize(260, 0))
        self.logoLabel.setText(_fromUtf8(""))
        self.logoLabel.setPixmap(QtGui.QPixmap(_fromUtf8("../../nmutils/resources/nanomax.png")))
        self.logoLabel.setObjectName(_fromUtf8("logoLabel"))
        self.gridLayout.addWidget(self.logoLabel, 0, 0, 3, 1)
        self.scanOptionsBox = QtGui.QLineEdit(self.centralwidget)
        self.scanOptionsBox.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scanOptionsBox.sizePolicy().hasHeightForWidth())
        self.scanOptionsBox.setSizePolicy(sizePolicy)
        self.scanOptionsBox.setMinimumSize(QtCore.QSize(250, 0))
        self.scanOptionsBox.setMaximumSize(QtCore.QSize(350, 16777215))
        self.scanOptionsBox.setObjectName(_fromUtf8("scanOptionsBox"))
        self.gridLayout.addWidget(self.scanOptionsBox, 0, 2, 1, 2)
        self.loadButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loadButton.sizePolicy().hasHeightForWidth())
        self.loadButton.setSizePolicy(sizePolicy)
        self.loadButton.setMaximumSize(QtCore.QSize(10000, 16777215))
        self.loadButton.setObjectName(_fromUtf8("loadButton"))
        self.gridLayout.addWidget(self.loadButton, 1, 3, 1, 1)
        self.filenameBox = QtGui.QLineEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filenameBox.sizePolicy().hasHeightForWidth())
        self.filenameBox.setSizePolicy(sizePolicy)
        self.filenameBox.setMinimumSize(QtCore.QSize(100, 0))
        self.filenameBox.setBaseSize(QtCore.QSize(200, 0))
        self.filenameBox.setPlaceholderText(_fromUtf8(""))
        self.filenameBox.setObjectName(_fromUtf8("filenameBox"))
        self.gridLayout.addWidget(self.filenameBox, 1, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1084, 27))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "NanoMAX Scan Viewer", None))
        self.browseButton.setText(_translate("MainWindow", "Browse...", None))
        self.scanOptionsBox.setText(_translate("MainWindow", "<class options>", None))
        self.loadButton.setText(_translate("MainWindow", "Load", None))
        self.filenameBox.setText(_translate("MainWindow", "<input file>", None))

from silx.gui.plot.PlotWindow import Plot2D
