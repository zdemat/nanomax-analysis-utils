from silx.gui.icons import getQIcon
from silx.gui import qt
import numpy as np

from .Base import CustomPlotWindow, PairedWidgetBase
from .MapWidget import MapWidget

class ImageWidget(CustomPlotWindow):
    """
    A re-implementation of Plot2D, with customized tools.
    """

    def __init__(self, parent=None):

        super(ImageWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=True, save=True, print_=False,
                                     control=False, roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comImageWidget')

        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        self.getMaskToolsDockWidget().setWindowTitle('diffraction ROI')
        self.getMaskAction().setToolTip('Select a diffraction region of interest')
        self.getMaskAction().setIcon(getQIcon('image-select-box'))

        # set default colormap
        self.setDefaultColormap({'name':'temperature', 'autoscale':True, 'normalization':'log'})

class XrdWidget(PairedWidgetBase):
    # This widget defines a MapWidget and and ImageWidget and describes
    # how they are related by data operations.
    def __init__(self, parent=None):

        super(XrdWidget, self).__init__()
        self.map = MapWidget(self)
        self.image = ImageWidget(self)
        self.setLayout(qt.QHBoxLayout())
        splitter = qt.QSplitter()
        splitter.addWidget(self.image)
        splitter.addWidget(self.map)
        self.layout().addWidget(splitter)

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)

        # connect the selection tools
        self.map.indexSelectionChanged.connect(self.selectByIndex)
        self.map.clickSelectionChanged.connect(self.selectByPosition)
        self.map.selectionCleared.connect(self.clearSelection)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.image.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateMap)
        self.map.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateImage)

        # keep track of map selections by ROI or by index
        self.selectionMode = 'roi' # 'roi' or 'ind'

    def setScan(self, scan):
        self.scan = scan
        if not scan:
            self.map.removeImage('data')
            self.image.removeImage('data')
            return
        # avoid old position grids:
        if self.map.positionsAction.isChecked():
            self.togglePositions()
        self.map.indexBox.setMaximum(scan.nPositions - 1)
        self.resetMap()
        self.resetImage()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetImage(self):
        self.updateImage()
        self.image.resetZoom()

    def updateMap(self):
        if self.scan is None:
            return
        try:
            self.window().statusOutput('Building 2D data map...')
            # workaround to avoid the infinite loop which occurs when both
            # mask widgets are open at the same time
            self.map.getMaskToolsDockWidget().setVisible(False)
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # get and check the mask array
            mask = self.image.getMaskToolsDockWidget().widget().getSelectionMask()
            # if the mask is cleared, reset without wasting time
            if (mask is None) or (not np.sum(mask)):
                print('building 2D data map by averaging all pixels')
                average = np.mean(self.scan.data['2d'], axis=(1,2))
            else:
                ii, jj = np.where(mask)
                print('building 2D data map by averaging %d pixels'%len(ii))
                average = np.mean(self.scan.data['2d'][:, ii, jj], axis=1)
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method='nearest')
            self.map.addImage(z, legend='data', 
                scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                origin=[x.min(), y.min()], resetzoom=False)
            self.map.setGraphXLimits(*xlims)
            self.map.setGraphYLimits(*ylims)
            aspect = (x.max() - x.min()) / (y.max() - y.min())
            if aspect > 50 or aspect < 1./50:
                self.map.setKeepDataAspectRatio(False)
            else:
                self.map.setKeepDataAspectRatio(True)
            self.window().statusOutput('')
            self.map.setGraphXLabel(self.scan.positionDimLabels[0])
            self.map.setGraphYLabel(self.scan.positionDimLabels[1])
        except:
            self.window().statusOutput('Failed to build 2D data map. See terminal output.')
            raise

    def updateImage(self):
        if self.scan is None:
            return
        try:
            self.window().statusOutput('Building 2D image...')
            # workaround to avoid the infinite loop which occurs when both
            # mask widgets are open at the same time
            self.image.getMaskToolsDockWidget().setVisible(False)
            if self.scan.data['2d'].shape[1:] == (1, 1):
                return
            # get and check the mask array
            if self.selectionMode == 'ind':
                index = self.map.indexBox.value()
                data = self.scan.data['2d'][index]
            elif self.selectionMode == 'roi':
                self.indexMarkerOn(False)
                mask = self.map.getMaskToolsDockWidget().widget().getSelectionMask()
                if (mask is None) or (not np.sum(mask)):
                    # the mask is empty, don't waste time with positions
                    print('building 2D image from all positions')
                    data = np.mean(self.scan.data['2d'], axis=0)
                else:
                    # recreate the interpolated grid from above, to find masked
                    # positions on the oversampled grid
                    dummy = np.zeros(self.scan.nPositions)
                    x, y, z = self.scan.interpolatedMap(dummy, self.map.interpolBox.value(), origin='ul')
                    maskedPoints = np.vstack((x[np.where(mask)], y[np.where(mask)])).T
                    pointSpacing2 = (x[0,1] - x[0,0])**2 + (y[0,0] - y[1,0])**2
                    # go through actual positions and find the masked ones
                    maskedPositions = []
                    for i in range(self.scan.nPositions):
                        # the minimum distance of the current position to a selected grid point:
                        dist2 = np.sum((maskedPoints - self.scan.positions[i])**2, axis=1).min()
                        if dist2 < pointSpacing2:
                            maskedPositions.append(i)
                    print('building 2D image from %d positions'%len(maskedPositions))
                    # get the average and replace the image with legend 'data'
                    data = np.mean(self.scan.data['2d'][maskedPositions], axis=0)
            self.image.addImage(data, legend='data', resetzoom=False)
            self.image.setGraphTitle(self.scan.dataTitles['2d'])
            self.image.setGraphXLabel(self.scan.dataDimLabels['2d'][1])
            self.image.setGraphYLabel(self.scan.dataDimLabels['2d'][0])
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build 2D image. See terminal output.')
            raise
