from silx.gui.plot import PlotWindow
from silx.gui.plot.Profile import ProfileToolBar
from silx.gui import qt
import scipy.ndimage.measurements
import numpy as np

from XrdWidget import MapWidget

class ImageWidget(PlotWindow):
    """
    A re-implementation of Plot2D, with customized tools.
    """

    def __init__(self, parent=None):
        # List of information to display at the bottom of the plot
        posInfo = [
            ('X', lambda x, y: x),
            ('Y', lambda x, y: y),
            ('Data', self._getActiveImageValue)]

        super(ImageWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=False, save=False, print_=False,
                                     control=False, position=posInfo,
                                     roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comImageWidget')

        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setGraphTitle('Mask excluded areas for COM analysis')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

    def _getActiveImageValue(self, x, y):
        """Get value of active image at position (x, y)

        :param float x: X position in plot coordinates
        :param float y: Y position in plot coordinates
        :return: The value at that point or '-'
        """
        image = self.getActiveImage()
        if image is not None:
            data, params = image[0], image[4]
            ox, oy = params['origin']
            sx, sy = params['scale']
            if (y - oy) >= 0 and (x - ox) >= 0:
                # Test positive before cast otherwisr issue with int(-0.5) = 0
                row = int((y - oy) / sy)
                col = int((x - ox) / sx)
                if (row < data.shape[0] and col < data.shape[1]):
                    return data[row, col]
        return '-'

class ComWidget(qt.QWidget):
    def __init__(self, parent=None):

        super(ComWidget, self).__init__(parent=parent)
        self.map = MapWidget(self)
        self.image = ImageWidget(self)
        self.setLayout(qt.QHBoxLayout())
        self.layout().addWidget(self.image)
        self.layout().addWidget(self.map)

        # disable the roi tool
        self.map.getMaskAction().setEnabled(False)

        self.direction = 0
        import ipdb; ipdb.set_trace()

        self.diffCmap = {'name':'temperature', 'autoscale':True, 'normalization':'log'}

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.image.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateMap)

    def setScan(self, scan):
        self.scan = scan
        if not scan:
            self.map.removeImage('data')
            self.image.removeImage('data')
            return
        if scan.data['2d'].shape[1:] == (1, 1):
            return
        # avoid old position grids:
        if self.map.positionsAction.isChecked():
            self.togglePositions()
        self.resetMap()
        self.resetImage()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetImage(self):
        self.image.addImage(self.scan.meanData(name='2d'), 
            colormap=self.diffCmap, legend='data')
        self.image.setKeepDataAspectRatio(True)
        self.image.setYAxisInverted(True)
        self.image.resetZoom()

    def updateMap(self):
        if self.scan is None:
            return
        try:
            print 'building COM map'
            self.window().statusOutput('Building COM map...')
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # calculate COM
            com = []
            mask = self.image.getMaskToolsDockWidget().widget().getSelectionMask()
            if (mask is None) or (not np.sum(mask)):
                mask = np.zeros(self.scan.data['2d'][0].shape, dtype=int)
            for im in self.scan.data['2d']:
                com_ = scipy.ndimage.measurements.center_of_mass(im * (1 - mask))
                if np.any(np.isnan(com_)):
                    com_ = (0, 0)
                com.append(com_)
            com = np.array(com)
            # choose which COM to show
            if self.direction == 0:
                com = com[:, 1] - np.mean(com[:, 1])
            elif self.direction == 1:
                com = com[:, 0] - np.mean(com[:, 0])
            elif self.direction == 2:
                com = np.sum((com - np.mean(com, axis=0))**2, axis=1)
            else:
                return
            # interpolate and show
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(com, sampling, origin='ul', method='nearest')
            try:
                self.map.addImage(z, legend='data', 
                    scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                    origin=[x.min(), y.min()])
                self.map.setGraphXLimits(*xlims)
                self.map.setGraphYLimits(*ylims)
            except:
                print "Invalid center of mass"
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build COM map. See terminal output.')
            raise


    def togglePositions(self):
        xlims = self.map.getGraphXLimits()
        ylims = self.map.getGraphYLimits()
        if self.map.positionsAction.isChecked():
            self.map.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                legend='scan positions', symbol='+', color='red', linestyle=' ')
        else:
            self.map.addCurve([], [], legend='scan positions')
        self.map.setGraphXLimits(*xlims)
        self.map.setGraphYLimits(*ylims)

#class ComWidget(qt.QWidget):
#    def setScan(self, scan):
#        pass
