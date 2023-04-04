# -*- python -*-
#
#       spatial_image: spatial nd images
#
#       Copyright 2006 INRIA - CIRAD - INRA
#
#       File author(s): Jerome Chopard <jerome.chopard@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
"""
This module create the main |SpatialImage| object
"""

__license__ = "Cecill-C"
__revision__ = " $Id: $ "

import numpy as np
from scipy import ndimage

# -- deprecation messages --
# import warnings, exceptions
# msg = "SpatialImage.resolution is deprecated, use SpatialImage.voxelsize"
# rezexc = exceptions.PendingDeprecationWarning(msg)


class SpatialImage(np.ndarray):
    """
    Associate meta data to np.ndarray
    """

    def __new__(
        cls, input_array, voxelsize=None, vdim=None, info=None, dtype=None, **kwargs
    ):
        """Instantiate a new |SpatialImage|

        if voxelsize is None, vdim will be used to infer space size and affect
        a voxelsize of 1 in each direction of space

        .. warning :: `resolution` keyword is deprecated. Use `voxelsize` instead.

        :Parameters:
         - `cls` - internal python
         - `input_array` (array) - data to put in the image
         - `voxelsize` (tuple of float) - spatial extension in each direction
                                           of space
         - `vdim` (int) - size of data if vector data are used
         - `info` (dict of str|any) - metainfo
        """
        # if the input_array is 2D we can reshape it to 3D.
        # ~ if input_array.ndim == 2: # Jonathan
        # ~ input_array = input_array.reshape( input_array.shape+(1,) ) # Jonathan

        # initialize datas. For some obscure reason, we want the data
        # to be F-Contiguous in the NUMPY sense. I mean, if this is not
        # respected, we will have problems when communicating with
        # C-Code... yeah, that makes so much sense (fortran-contiguous
        # to be c-readable...).
        dtype = dtype if dtype is not None else input_array.dtype
        if input_array.flags.f_contiguous:
            obj = np.asarray(input_array, dtype=dtype).view(cls)
        else:
            obj = np.asarray(input_array, dtype=dtype, order="F").view(cls)

        voxelsize = kwargs.get("resolution", voxelsize)  # to manage transition

        if voxelsize is None:
            # ~ voxelsize = (1.,) * 3
            voxelsize = (1.0,) * input_array.ndim  # Jonathan
        else:
            # ~ if len(voxelsize) != 3 :
            if (input_array.ndim != 4) and (
                len(voxelsize) != input_array.ndim
            ):  # Jonathan _ Compatibility with "champs_*.inr.gz" generated by Baloo & SuperBaloo
                raise ValueError("data dimension and voxelsize mismatch")

        obj.voxelsize = tuple(voxelsize)
        obj.vdim = vdim if vdim else 1

        # set metadata
        if info is None:
            obj.info = {}
        else:
            obj.info = dict(info)

        # return
        return obj

    def _get_resolution(self):
        # warnings.warn(rezexc)
        return self.voxelsize

    def _set_resolution(self, val):
        # warnings.warn(rezexc)
        self.voxelsize = val

    resolution = property(_get_resolution, _set_resolution)

    @property
    def real_shape(self):
        # ~ return np.multiply(self.shape[:3], self.voxelsize)
        return np.multiply(self.shape, self.voxelsize)  # Jonathan

    def invert_z_axis(self):
        """
        invert allong 'Z' axis
        """
        self = self[:, :, ::-1]

    def __array_finalize__(self, obj):
        if obj is None:
            return

        # assert resolution
        res = getattr(obj, "voxelsize", None)
        if res is None:  # assert vdim == 1
            res = (1.0,) * len(obj.shape)

        self.voxelsize = tuple(res)

        # metadata
        self.info = dict(getattr(obj, "info", {}))

    def clone(self, data):
        """Clone the current image metadata
        on the given data.
        .. warning:: vdim is defined according to self.voxelsize and data.shape
        :Parameters:
         - `data` - (array)

        :Returns Type: |SpatialImage|
        """
        if len(data.shape) == len(self.voxelsize):
            vdim = 1
        elif len(data.shape) - len(self.voxelsize) == 1:
            vdim = data.shape[-1]
        else:
            raise UserWarning("unable to handle such data dimension")

        return SpatialImage(data, self.voxelsize, vdim, self.info)

    @classmethod
    def valid_array(cls, array_like):
        return (
            isinstance(array_like, (np.ndarray, cls)) and array_like.flags.f_contiguous
        )


def empty_image_like(spatial_image):
    array = np.zeros(spatial_image.shape, dtype=spatial_image.dtype)
    return SpatialImage(array, spatial_image.voxelsize, vdim=1)


def null_vector_field_like(spatial_image):
    array = np.zeros(list(spatial_image.shape) + [3], dtype=np.float32)
    return SpatialImage(array, spatial_image.voxelsize, vdim=3)


def random_vector_field_like(spatial_image, smooth=0, max_=1):
    # ~ if spatial_image.vdim == 1:
    # ~ shape = spatial_image.shape+(3,)
    # ~ else:
    # ~ shape = spatial_image.shape
    shape = spatial_image.shape  # Jonathan
    array = np.random.uniform(-max_, max_, shape)
    if smooth:
        array = ndimage.gaussian_filter(array, smooth)
    return SpatialImage(array, spatial_image.voxelsize, dtype=np.float32)


def checkerboard(nx=9, ny=8, nz=5, size=10, vs=(1.0, 1.0, 1.0), dtype=np.uint8):
    """Creates a 3D checkerboard image with `nx` squares in width,
    `ny` squares in height and `nz` squares in depth. The length of the edge in real units
    of each square is `size`."""

    sxv, syv, szv = np.array([size] * 3) / np.array(vs)
    array = np.zeros((sxv * nx, syv * ny, szv * nz), dtype=dtype, order="F")
    typeinfo = np.iinfo(dtype)

    # -- wooo surely not the most beautiful implementation out here --
    for k in range(nz):
        kval = typeinfo.max if (k % 2 == 0) else typeinfo.min
        jval = kval
        for j in range(ny):
            ival = jval
            for i in range(nx):
                array[
                    i * sxv : i * sxv + sxv,
                    j * syv : j * syv + syv,
                    k * szv : k * szv + szv,
                ] = ival
                ival = typeinfo.max if (ival == typeinfo.min) else typeinfo.min
            jval = typeinfo.max if (jval == typeinfo.min) else typeinfo.min
        kval = typeinfo.max if (kval == typeinfo.min) else typeinfo.min

    return SpatialImage(array, vs, dtype=dtype)


def is2D(image):
    """
    Test if the `image` (array) is in 2D or 3D.
    Return True if 2D, False if not.
    """
    if len(image.shape) == 2 or image.shape[2] == 1:
        return True
    else:
        return False