#
# LSST Data Management System
#
# Copyright 2016 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#

from lsst.afw.image import LOCAL
from lsst.ip.isr import biasCorrection, flatCorrection
from lsst.meas.algorithms.detection import SourceDetectionTask
from .isr import DecamIsrTask, DecamIsrConfig

__all__ = ["DecamCpIsrConfig", "DecamCpIsrTask"]


def _computeEdgeSize(rawExposure, calibExposure):
    """Compute the number of edge trim pixels of the calibration product.

    Some Community Pipeline Calibration products are trimmed on their edges
    and are smaller than the raw data. Use the dimension difference between
    raw exposure and the calibration product to compute the edge trim pixels.

    Parameters
    ----------
    rawExposure : `lsst.afw.image.Exposure`
        The input raw exposure.
    calibExposure : `lsst.afw.image.Exposure`
        Calibration bias or flat exposure, known to be smaller than raw data.

    Returns
    -------
    result : `int`
        An integer as the number of trimmed pixels on each edge.
    """
    nx, ny = rawExposure.getBBox().getDimensions() - calibExposure.getBBox().getDimensions()
    assert nx == ny, "Exposure is trimmed differently in X and Y"
    assert nx % 2 == 0, "Exposure is trimmed unevenly in X"
    assert nx >= 0, "Calibration image is larger than raw data"
    return nx//2


class DecamCpIsrConfig(DecamIsrConfig):

    def setDefaults(self):
        self.biasDataProductName = "cpBias"
        self.flatDataProductName = "cpFlat"


class DecamCpIsrTask(DecamIsrTask):
    """Perform ISR task using Community Pipeline Calibration Products MasterCal.

    The CP MasterCal products have butler dataset types cpBias and cpFlat,
    different from the LSST-generated calibration products (bias/flat).
    """
    ConfigClass = DecamCpIsrConfig

    def biasCorrection(self, exposure, biasExposure):
        """Apply bias correction in place

        DECam bias products have been trimmed and are smaller than
        the raw exposure.  The size of edge trim is computed based
        on the dimensions of the input data.  Only process the inner
        part of the raw exposure, and mask the outer pixels as EDGE.

        Parameters
        ----------
        exposure : `lsst.afw.image.Exposure`
            Exposure to process.
        biasExposure : `lsst.afw.image.Exposure`
            Bias exposure.
        """
        nEdge = _computeEdgeSize(exposure, biasExposure)
        if nEdge > 0:
            rawMaskedImage = exposure.maskedImage[nEdge:-nEdge, nEdge:-nEdge, LOCAL]
        else:
            rawMaskedImage = exposure.getMaskedImage()
        biasCorrection(rawMaskedImage, biasExposure.getMaskedImage())
        # Mask the unprocessed edge pixels as EDGE
        SourceDetectionTask.setEdgeBits(
            exposure.getMaskedImage(),
            rawMaskedImage.getBBox(),
            exposure.getMaskedImage().getMask().getPlaneBitMask("EDGE")
        )

    def flatCorrection(self, exposure, flatExposure):
        """Apply flat correction in place.

        DECam flat products have been trimmed and are smaller than
        the raw exposure.  The size of edge trim is computed based
        on the dimensions of the input data.  Only process the inner
        part of the raw exposure, and mask the outer pixels as EDGE.

        Parameters
        ----------
        exposure : `lsst.afw.image.Exposure`
            Exposure to process.
        flatExposure : `lsst.afw.image.Exposure`
            Flatfield exposure.
        """
        nEdge = _computeEdgeSize(exposure, flatExposure)
        if nEdge > 0:
            rawMaskedImage = exposure.maskedImage[nEdge:-nEdge, nEdge:-nEdge, LOCAL]
        else:
            rawMaskedImage = exposure.getMaskedImage()
        flatCorrection(
            rawMaskedImage,
            flatExposure.getMaskedImage(),
            self.config.flatScalingType,
            self.config.flatUserScale
        )
        # Mask the unprocessed edge pixels as EDGE
        SourceDetectionTask.setEdgeBits(
            exposure.getMaskedImage(),
            rawMaskedImage.getBBox(),
            exposure.getMaskedImage().getMask().getPlaneBitMask("EDGE")
        )
