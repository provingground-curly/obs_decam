"""
DECam-specific overrides for ProcessCcdTask/Community Pipeline products
"""
import os.path

from lsst.utils import getPackageDir

obsConfigDir = os.path.join(getPackageDir('obs_decam'), 'config')

config.isr.load(os.path.join(obsConfigDir, 'isr.py'))

config.charImage.repair.cosmicray.nCrPixelMax = 100000

for refObjLoader in (config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader,
                     config.charImage.refObjLoader,
                     ):
    refObjLoader.ref_dataset_name = "ps1_pv3_3pi_20170110"
    # Note the u-band results may not be useful without a color term
    refObjLoader.filterMap['u'] = 'g'
    refObjLoader.filterMap['Y'] = 'y'

config.calibrate.photoCal.photoCatName = "ps1_pv3_3pi_20170110"
