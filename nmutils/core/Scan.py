"""  
Implements the Scan class, a container for N-dimensional sample scans
holding arbitrary data at each position. This data can typically be, for
each scan position, one or more 2D detector images, 1D fluorescence
spectra, transmissions, etc.
"""

import numpy as np
import h5py
import copy as cp
import os.path
from .. import NoDataException

import scipy.ndimage.measurements
from scipy.interpolate import griddata
from functools import reduce

__docformat__ = 'restructuredtext'  # This is what we're using! Learn about it.


class Scan(object):

    # An options structure, overridden in subclasses to allow passing 
    # more kwargs to addData(). This is just an illustration and should
    # be overridden. Tip: for multiple choice, give a list or tuple of
    # possibilities in the 'type' field.
    default_opts = {
        'dataSource': {
            'value': 'val1',
            'type': ['val1', 'val2', 'val3'],
            'doc': "some meaningful values, maybe 'waxs' or 'merlin'",
            }
    }

    def __init__(self):
        """ 
        Only initializes counters and containers. Parameters, positions
        and data are added later.
        """

        # A dict of datasets, where each value is an array, the first
        # index of which is the position, so (Npositions x M x N) or
        # (Npositions x M) for example. Each dataset can have different
        # dimensionality.
        self.data = {}

        # An array of scanning positions (Npositions x Ndimensions),
        # common to all datasets. No assumptions on scanning grids
        # are made.
        self.positions = None

        # Optional metadata fields filled in by _readPositions and
        # _readData which can be used later for plotting or labeling.
        self.positionDimLabels = [] # labels for each of the scanning dimensions
        self.dataTitles = {}        # titles for each dataset
        self.dataDimLabels = {}     # labels for each of the data dimensions
        self.dataAxes = {}          # numerical values for the axes of each dataset

    @property
    def nDatasets(self):
        return len(self.data)

    @property
    def nPositions(self):
        return None if self.positions is None else self.positions.shape[0]

    @property
    def nDimensions(self):
        return None if self.positions is None else self.positions.shape[1]

    def _prepareData(self, **kwargs):
        """
        Private method which is passed the kwargs from addData, and
        uses these to set up all parameters for the next dataset to
        be read. Note that parameters are not kept, and are only used
        for data loading. By default attaches all options as
        attributes on self.
        """
        # copy defaults, then update with kwarg options
        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        for k, dct in opts.items():
            exec("self.%s = dct['value']" % k)

    def _readPositions(self):
        """ 
        Placeholder method to be subclassed. Private method which
        interfaces with the actual hdf5 file and returns an array of
        coordinates N-by-(number of scan dimensions).

        The positions are defined as [x, y], where columns x and y are
        motor positions. It is then up to the viewer to display the
        image in a good way. For example, if the motor positions denote
        sample position and under the nanomax coordinate system, the xy
        origin should be top left. Then, the bottom right corner
        corresponds to maximum motor positions, which means minimum in
        the sample frame under the nanomax coordinate system. Phew.
        """
        raise NotImplementedError

    def _readData(self, name):
        """ 
        Placeholder method to be subclassed. Private method which
        interfaces with the actual hdf5 file and returns an N-by-(image
        size) array. 

        The parent Scan class can handle an inconsistent number of 
        positions and data points, so the important thing is to not
        raise unnecessary exceptions, but instead to just return what
        you can.
        """
        raise NotImplementedError

    def _updateOpts(self, opts, **kwargs):
        """
        Helper method which updates the 'value' fields of an options 
        structure (copied from the defaults) with kwargs. Typically 
        called from _prepareData().
        """
        opts = opts.copy()
        for key, val in kwargs.items():
            if key in opts.keys():
                # normal type specified
                if type(opts[key]['type']) is type and not (type(val) == opts[key]['type']):
                    raise Exception('Data type for option %s should be %s, not %s'%(str(key), str(opts[key]['type']), str(type(val))))
                # list or tuple in the type field means multiple choice
                if type(opts[key]['type']) in (list, tuple) and val not in opts[key]['type']:
                    raise Exception("Value '%s' isn't on the menu for option %s (%s)" % (str(val), str(key), str(opts[key]['type'])))
                opts[key]['value'] = val
            else:
                raise Exception('Unknown option %s' % str(key))
        return opts

    def _safe_get_str(self, fp, path):
        """
        Attempts to get string from fp[path], raising an informative
        NoDataException if that fails.
        """
        try:
            a = fp[path][()]
        except KeyError:
            raise NoDataException('Dataset %s not found in %s' % (path, fp.filename))
        if isinstance(a, bytes):
            a = str(a, 'utf-8')
        return a

    def _safe_get_array(self, fp, path):
        """
        Attempts to get array from array(fp[path]), raising an informative
        NoDataException if that fails.
        """
        try:
            a = np.array(fp[path])
        except KeyError:
            raise NoDataException('Dataset %s not found in %s' % (path, fp.filename))
        return a

    def _safe_get_dataset(self, fp, path):
        """
        Attempts to get dataset from fp[path], raising an informative
        NoDataException if that fails.
        """
        try:
            a = fp[path]
        except KeyError:
            raise NoDataException('Dataset %s not found in %s' % (path, fp.filename))
        return a

    def addData(self, name=None, **kwargs):
        """ 
        This method adds positions the first time data is loaded. Then,
        subsequent data additions should check for consistency and
        complain if datasets are not compatible. The name kwarg should 
        hint at what type of data we're reading (for example 'pilatus', 
        'transmission', ...), so data from different sources can be 
        handled by this method.
        """

        if not name:
            name = 'data%u' % self.nDatasets

        self._prepareData(**kwargs)

        # Check if any data exists.
        if not self.nDatasets:
            # initialize data dict and read positions
            self.positions = self._readPositions()
            if not self.positionDimLabels:
                self.positionDimLabels = ['scan direction %d' % i for i in range(1, self.nDimensions+1)]
        else:
            # verify that the data isn't already loaded
            if name in self.data.keys():
                raise ValueError("Dataset '%s' already exists!" % name)
            # verify that positions are are consistent
            if not np.all(self.positions == self._readPositions()):
                raise ValueError(
                    "Positions of new dataset are inconsistent with previously loaded positions!")

        # The actual reading is done by _readData() which knows about the
        # details of the hdf5 file
        data = self._readData(name)

        # Check if _readData has filled in the info fields, otherwise generate something
        if self.dataTitles.get(name) is None:
            self.dataTitles[name] = '%s dataset' % name
        if self.dataDimLabels.get(name) is None:
            self.dataDimLabels[name] = ['data dim %u' % i for i in range(data.ndim-1)]
        if self.dataAxes.get(name) is None:
            self.dataAxes[name] = [np.arange(sh) for sh in data.shape[1:]]
        assert str(self.dataTitles[name]) == self.dataTitles[name]
        assert len(self.dataDimLabels[name]) == data.ndim - 1
        assert len(self.dataAxes[name]) == data.ndim - 1

        # pad the data in case there were missing frames
        if data.shape[0] < self.nPositions:
            missing = self.nPositions - data.shape[0]
            print("there were %d missing images for dataset '%s', filling with average values"%(missing, name))
            pads = ((0, missing),) + ((0, 0),) * (data.ndim - 1)
            data = np.pad(data, pads, mode='mean')

        # remove data in case too much has been returned
        if data.shape[0] > self.nPositions:
            excess = data.shape[0] - self.nPositions
            print("there were %d too many images for dataset '%s', ignoring"%(excess, name))
            data = data[:self.nPositions]

        self.data[name] = data
        
    def removeData(self, name):
        if name in list(self.data.keys()):
            self.data.pop(name, None)
        else:
            raise ValueError("Dataset '%s' doesn't exist!" % name)

    def listData(self):
        return list(self.data.keys())

    def meanData(self, name=None):
        """ Returns the scan-average of the specified data set. """
        if not name:
            if self.nDatasets == 1:
                name = self.listData()[0]
            else:
                raise ValueError(
                    "There is more than one dataset to choose from. Please specify!")
        return np.mean(self.data[name], axis=0)

    def copy(self, data=True):
        """ 
        Returns a copy of the Scan instance. The kwarg data can be set
        to False to ignore data and positions, which is useful for
        creating Scan instances with only a subset of the data. This
        method also copies all attributes and does not need to be
        updated.
        """

        # copy all
        if data:
            return cp.deepcopy(self)

        # otherwise, construct a new objects and copy all the attributes
        # create a new object of the right subclass:
        new = self.__class__()

        # copy all the non-data attributes
        for key in self.__dict__.keys():
            if key not in ['data', 'positions']:
                exec("new.%s = cp.deepcopy(self.%s)" % (key, key))
        for dataset in self.data.keys():
            new.data[dataset] = None

        return new

    def merge(self, scanobj):
        """
        Adds positions and data from another Scan object. The scans must
        have the same datasets.
        """
        assert self.data.keys() == scanobj.data.keys()
        self.positions = np.concatenate((self.positions, scanobj.positions), axis=0)
        for key in self.data.keys():
            self.data[key] = np.concatenate((self.data[key], scanobj.data[key]), axis=0)

    def subset(self, posRange, closest=False):
        """ 
        Returns a Scan instance containing only the scan positions which
        are within a specified range, array([[xmin, ymin, ...], [xmax,
        ymax, ...]]). If the kwarg closest is True, and the specified
        range contains no positions, then the returned instance contains
        only the single closest position.
        """
        new = self.copy(data=False)

        # lists of data and positions to fill in
        new.positions = []
        for dataset in self.data.keys():
            new.data[dataset] = []

        # go through all positions and only include the ones which are
        # within range
        for i in range(self.nPositions):
            ok = True
            for dim in range(self.nDimensions):
                pos = self.positions[i, dim]
                if pos < posRange[0, dim] or pos > posRange[1, dim]:
                    ok = False
                    break
            if ok:
                for dataset in self.data.keys():
                    new.data[dataset].append(self.data[dataset][i])
                new.positions.append(self.positions[i])

        # get the closest positions if requested
        if (len(new.positions) == 0) and closest:
            rangeCenter = np.mean(posRange, axis=0)
            # using sum instead of linalg.norm here, for old numpy at beamline:
            index = np.argmin(
                np.sum((self.positions - rangeCenter)**2, axis=1))
            for dataset in self.data.keys():
                new.data[dataset].append(self.data[dataset][index])
            new.positions.append(self.positions[index])

        # convert lists to arrays
        for dataset in self.data.keys():
            new.data[dataset] = np.array(new.data[dataset])
        new.positions = np.array(new.positions)

        return new

    def interpolatedMap(self, values, oversampling, origin='lr', method='nearest', equal=False):
        """ 
        Provides a regular and interpolated xy map of the scan, with the
        values provided. For example, a ROI integral can be provided which
        results in an interpolated map of that ROI.

        values: a length-N array, with one value per position
        oversampling: the oversampling ratio relative to the average position spacing
        origin: 'lr', 'll', 'ur', 'ul'
        equal: use equal pixel sizes for x and y
        """
        assert self.nDimensions == 2

        xMin, xMax = np.min(self.positions[:,0]), np.max(self.positions[:,0])
        yMin, yMax = np.min(self.positions[:,1]), np.max(self.positions[:,1])

        # here we need special cases for 1d scans (where x or y doesn't vary)
        if np.abs(yMax - yMin) < 1e-12:
            stepsize = (xMax - xMin) / float(self.nPositions) / oversampling
            margin = oversampling * stepsize / 2
            y, x = np.mgrid[yMin-(stepsize*oversampling*5)/2:yMin+(stepsize*oversampling*5)/2:stepsize, xMax+margin:xMin-margin:-stepsize]
        elif np.abs(xMax - xMin) < 1e-12:
            stepsize = (yMax - yMin) / float(self.nPositions) / oversampling
            margin = oversampling * stepsize / 2
            y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMin-(stepsize*oversampling*5)/2:xMin+(stepsize*oversampling*5)/2:stepsize]
        else:
            xstepsize = (xMax-xMin) / np.sqrt(self.nPositions) / oversampling
            ystepsize = (yMax-yMin) / np.sqrt(self.nPositions) / oversampling
            if equal:
                xstepsize = min(xstepsize, ystepsize)
                ystepsize = xstepsize
            xmargin = oversampling * xstepsize / 2
            ymargin = oversampling * ystepsize / 2
            y, x = np.mgrid[yMax+ymargin:yMin-ymargin:-ystepsize, xMax+xmargin:xMin-xmargin:-xstepsize]
        z = griddata(self.positions, values, (x, y), method=method)
        
        # we've been assuming lower-right origin. adjust:
        if origin == 'll':
            x = np.fliplr(x)
            y = np.fliplr(y)
            z = np.fliplr(z)
        elif origin == 'ur':
            x = np.flipud(x)
            y = np.flipud(y)
            z = np.flipud(z)
        elif origin == 'ul':
            x = np.flipud(x)
            y = np.flipud(y)
            z = np.flipud(z)
            x = np.fliplr(x)
            y = np.fliplr(y)
            z = np.fliplr(z)

        return x, y, z
    
    def export(self, filepath, method='reshape', shape=None, oversampling=1, equal=True):
        """ 
        Dumps data into a single HDF5 file in order to allow export into other software
        or reload later.

        filepath: full path and name of the output file
        method: "reshape"  - attempt to cast the data on a regular grid,
                "resample" - resample the data on a regular grid,
                "none" - export the data without forcing it onto any sort of grid
        shape:  tuple defining shape of the scan measurement grid as (lines, points),
                optionally used  with "reshape", inferred by default
        oversampling: the oversampling ratio relative to the typical step size,
                      used with "resample"
        equal:  use equal step sizes in x and y for "resample"
        """
        # this only applies for 1D and 2D scans
        assert self.nDimensions in (1, 2)

        # check input arguments
        assert method in ('reshape', 'resample', 'none')

        # export to hdf5 file
        with h5py.File(filepath, 'w-', libver='earliest') as h5f:
            # create entry
            grp_path = "/entry0"
            grp = h5f.create_group(grp_path)
            # set metdata
            import datetime
            import getpass
            grp.attrs["author"] = getpass.getuser()
            grp.attrs["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            grp.attrs["version"] = u"0.1"
            # create data group
            grp_path = "/entry0/data"
            grp = h5f.create_group(grp_path)
            # save positions
            if method == 'reshape':
                if shape is None:
                    shape, fast_axis_label = self._shapeFromPositions2D(self.positions[:,0],self.positions[:,1])
                    if not np.prod(shape) == self.nPositions:
                        raise Exception('Something went really wrong when trying to reshape the scan grid')
                    print("Fast axis detectected to be: %s" % (fast_axis_label,))
                dset = h5f.create_dataset(name=grp_path+"/positions_x", data=self.positions[:,0], shape=shape, dtype=np.float, compression="lzf")
                dset = h5f.create_dataset(name=grp_path+"/positions_y", data=self.positions[:,1], shape=shape, dtype=np.float, compression="lzf")
            elif method == 'resample':
                x, y = self.interpolatedMap(np.zeros(self.nPositions), oversampling, equal=equal)[:2]
                shape = x.shape
                dset = h5f.create_dataset(name=grp_path+"/positions_x", data=x, dtype=np.float, compression="lzf")
                dset = h5f.create_dataset(name=grp_path+"/positions_y", data=y, dtype=np.float, compression="lzf")
            elif method == 'none':
                dset = h5f.create_dataset(name=grp_path+"/positions_x", data=self.positions[:,0], dtype=np.float, compression="lzf")
                dset = h5f.create_dataset(name=grp_path+"/positions_y", data=self.positions[:,1], dtype=np.float, compression="lzf")
            # create datasets
            for dsetname in self.data.keys():
                # total data shape
                if method in ('reshape', 'resample'):
                    shp = shape + self.data[dsetname].shape[1:]
                else:
                    shp = self.data[dsetname].shape
                # chunking
                dt = self.data[dsetname].dtype
                chunk = self._calcChunkSize(shp, dt.itemsize)
                print("%s, shape: %s, chunk: %s" % (dsetname, shp, chunk,))
                # what data to write?
                if method in ('reshape', 'none'):
                    data = self.data[dsetname]
                elif method == 'resample':
                    data = self.interpolatedMap(self.data[dsetname], oversampling, equal=equal)[-1]
                # write it
                if chunk not in [None,[]]:
                    dset = h5f.create_dataset(name=grp_path+"/"+dsetname, data=data, shape=shp, chunks=chunk, dtype=dt, compression="lzf")
                else:
                    dset = h5f.create_dataset(name=grp_path+"/"+dsetname, data=data, shape=shp, dtype=dt, compression="lzf")
            print("Scan data were exported to %s:%s" % (filepath,grp_path,))

    def _calcChunkSize(self,shape,dsize):
        """ 
        Returns optimal shape of chunks for this type of data. Returns none if chunking is discouraged.
        """
        maxChunkSz = 1 << 22 # 22 ... 4Mib, 20 ... 1MiB, 10 ... 1kiB
        # determine chunk dimensions
        dims = len(shape)
        if dims==0:
            # no chunking
            return None
        elif dims==1:
            # calc chunk size directly
            if dsize*shape[0]<=maxChunkSz:
                # no sense for chunking for this dimension
                return None
            else:
                return (int(maxChunkSz/dsize),) 
        else:
            # try chunking just on the last dimension
            chunk = self._calcChunkSize(shape[-1:], dsize)
            if chunk:
                # chunking here is adviced, just do it
                return (1,)*(dims-1) + chunk 
            else:
                # chunking on the last dim is not adviced (too small), try next
                dsz = shape[-1]*dsize
                chunk = self._calcChunkSize(shape[:-1], dsz)
                if chunk:
                    # use chunking
                    return chunk + (shape[-1],)
                else:
                    # chunking was not adviced
                    from operator import mul
                    if dsize*reduce(mul,shape)>maxChunkSz:
                        # chunk everything
                        return shape
                    else:
                        return None

    def _shapeFromPositions2D(self,x,y):
        """ 
        Returns shape of 2D scan grid calculated from axes positions and the fast axis label.
        The fast axis is the last dimension.
        """
        adx = np.abs(np.diff(x))
        ady = np.abs(np.diff(y))

        if np.median(adx) > np.median(ady):
            fast_axis = x
            fast_axis_adiff = adx
            fast_axis_label = 'x'
        else:
            print("y is the fast axis")
            fast_axis = y
            fast_axis_adiff = ady
            fast_axis_label = 'y'

        fast_axis_total_diff = np.max(fast_axis)-np.min(fast_axis)

        idx_breaks = np.where(fast_axis_adiff>fast_axis_total_diff/2.)
        dim = np.diff(np.insert(idx_breaks,0,-1))
        fast_axis_dim = np.mean(dim,dtype=np.int)
        if np.all(dim!=fast_axis_dim):
            print("Warning: something wrong in fast axis length calculation")
        slow_axis_dim = fast_axis.size // fast_axis_dim
        if slow_axis_dim*fast_axis_dim != fast_axis.size:
            print("Error: auto-detection of scanning grid failed")
        return (slow_axis_dim, fast_axis_dim), fast_axis_label
