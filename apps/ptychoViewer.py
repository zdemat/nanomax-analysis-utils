#/usr/bin/env python

"""
This application loads ptypy reconstruction files and displays them nicely.
"""

from nmutils.gui.ptychoViewer import PtychoViewer
from silx.gui import qt
import sys

if __name__ == '__main__':
    # you always need a qt app
    app = qt.QApplication(sys.argv)
    app.setStyle('Fusion')

    # Parse input
    import argparse
    parser = argparse.ArgumentParser(
        description='This application visualizes the output of a ptypy run, by loading a ptyr file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', type=str, nargs='?',
                        help='a ptypy reconstruction file', default=None)
    args = parser.parse_args()

    # instantiate and show the main object
    viewer = PtychoViewer(args.file)
    viewer.show()
    # run the app
    app.exec_()
