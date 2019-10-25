from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path


class contrast_stepscan(Scan):
    """
    Stepscan format for the Contrast acquisition software.
    """

    default_opts = {
        'scanNr': {
            'value': 0,
            'type': int,
            'doc': "scan number",
            },
        'path': {
            'value': None,
            'type': str,
            'doc': "folder containing the main data file",
            },
        'dataSource': {
            'value': 'merlin',
            'type': ['merlin', 'xspress3', 'pilatus', 'pilatus1m', 'counter1', 'counter2', 'counter3', 'waxs'],
            'doc': "type of data",
            },
        'xMotor': {
            'value': 'sx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'sy',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'xrfChannel': {
            'value': 3,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
            },
        'xrdCropping': {
            'value': [],
            'type': list,
            'doc': 'detector area to load, [i0, i1, j0, j1]',
            },
        'xrdBinning': {
            'value': 1,
            'type': int,
            'doc': 'bin xrd pixels n-by-n (after cropping)',
            },
        'normalize_by_I0': {
            'value': False,
            'type': bool,
            'doc': 'whether to normalize against I0 (counter1)',
            },
        'nominalPositions': {
            'value': False,
            'type': bool,
            'doc': 'use nominal instead of recorded positions',
            },
        'waxsPath': {
            'value': '../../process/radial_integration/<sampledir>',
            'type': str,
            'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
        },
        'burstSum': {
            'value': False,
            'type': bool,
            'doc': 'whether or not to sum burst acquisitions (otherwise you get the first frame)',
        },
        'nMaxPositions': {
            'value': 0,
            'type': int,
            'doc': 'maximum number of positions to read (0 means all)',
        },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pilatus':2, 'xspress3':1, 'merlin':2, 'pilatus1m':2, 'counter1':0, 'counter2':0, 'counter3':0, 'waxs':1}
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        path = opts['path']['value']
        if path.endswith('h5'):
            path = os.path.dirname(path)
        scanNr = int(opts['scanNr']['value'])
        self.dataSource = opts['dataSource']['value']
        self.fileName = os.path.join(path, '%06u.h5'%scanNr)
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = opts['xrdCropping']['value']
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.normalize_by_I0 = (opts['normalize_by_I0']['value'])
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.waxsPath = opts['waxsPath']['value']
        self.burstSum = opts['burstSum']['value']
        self.nMaxPositions = opts['nMaxPositions']['value']

        # Sanity check
        try:
            with h5py.File(self.fileName, 'r') as fp:
                pass
        except OSError:
            raise NoDataException('Could not find or open the file %s' % self.fileName)

    def _readPositions(self):
        """ 
        Override position reading.
        """

        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            x = np.array(hf.get('entry/measurement/%s' % self.xMotor))
            y = np.array(hf.get('entry/measurement/%s' % self.yMotor))
        if self.nMaxPositions:
            x = x[:self.nMaxPositions]
            y = y[:self.nMaxPositions]
        # allow 1d scans
        try:
            len(y)
        except TypeError:
            y = np.zeros(x.shape)
        try:
            len(x)
        except TypeError:
            x = np.zeros(y.shape)

        # save motor labels
        self.positionDimLabels = [self.xMotor, self.yMotor]

        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if self.normalize_by_I0:
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = self._safe_get_array(hf, 'entry/ni/measurement/counter1')
                I0_data = I0_data.astype(float) * 1e-5
                print(I0_data)

        if self.dataSource in ('merlin', 'pilatus', 'pilatus1m'):
            print("loading diffraction data...")
            path = os.path.split(os.path.abspath(self.fileName))[0]

            data = []
            ic = None; jc = None # center of mass
            missing = 0
            hdf_pattern = 'entry/measurement/%s/%%06u' % self.dataSource

            with h5py.File(self.fileName, 'r') as hf:
                print('loading diffraction data: ' + self.fileName)
                for im in range(self.positions.shape[0]):
                    if self.nMaxPositions and im == self.nMaxPositions:
                        break
                    dataset = self._safe_get_dataset(hf, hdf_pattern%im)
                    if dataset.shape[0] == self.positions.shape[0]:
                        # this is hybrid triggering data!
                        subframe = im
                    else:
                        subframe = 0
                    # for the first frame, determine center of mass
                    if ic is None or jc is None == 0:
                        import scipy.ndimage.measurements
                        img = np.array(dataset[0])
                        try:
                            ic, jc = list(map(int, scipy.ndimage.measurements.center_of_mass(img)))
                        except ValueError:
                            ic = img.shape[0] // 2
                            jc = img.shape[1] // 2
                        print("Estimated center of mass to (%d, %d)"%(ic, jc))
                    if self.xrdCropping:
                        i0, i1, j0, j1 = self.xrdCropping
                        if 'merlin' in hdf_pattern:
                            # Merlin images indexed from the bottom left...
                            i1_ = i1
                            i1 = 515 - i0
                            i0 = 515 - i1_
                        if self.burstSum:
                            data_ = np.sum(np.array(dataset[:, i0:i1, j0:j1]), axis=0)
                        else:
                            data_ = np.array(dataset[subframe, i0:i1, j0:j1])
                    else:
                        if self.burstSum:
                            data_ = np.sum(np.array(dataset), axis=0)
                        else:
                            data_ = np.array(dataset[subframe])
                    if self.xrdBinning > 1:
                        data_ = fastBinPixels(data_, self.xrdBinning)
                    if 'merlin' in hdf_pattern:
                        data_ = np.flipud(data_) # Merlin images indexed from the bottom left...
                    data.append(data_)

            print("loaded %d images"%len(data))
            if missing:
                print("there were %d missing images" % missing)
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None, None]

        elif self.dataSource == 'xspress3':
            print("loading fluorescence data...")
            print("selecting xspress3 channel %d"%self.xrfChannel)
            data = []
            with h5py.File(self.fileName, 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = self._safe_get_dataset(hf, 'entry/measurement/xspress3/%06d' % im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, self.xrfChannel, :4096])
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None]
            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data.shape[-1]) * .01]

        elif self.dataSource in ('counter1', 'counter2', 'counter3'):
            entry = 'entry/measurement/ni/%s' % self.dataSource
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = self._safe_get_array(hf, entry)
                I0_data = I0_data.astype(float)
                data = I0_data.flatten()

        elif self.dataSource == 'waxs':
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            fn = os.path.basename(self.fileName)
            waxsfn = fn.replace('.h5', '_waxs.h5')
            waxs_file = os.path.join(path, waxsfn)
            print('loading waxs data from %s' % waxs_file)
            with h5py.File(waxs_file, 'r') as fp:
                q = self._safe_get_array(fp, 'q')
                I = self._safe_get_array(fp, 'I')
            data = I
            self.dataAxes[name] = [q,]
            self.dataDimLabels[name] = ['q (1/nm)']

        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')
        
        return data

