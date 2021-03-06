import os

import numpy
try:
    from PIL import Image
    available = True
except ImportError as e:
    available = False
    _import_error = e
import six

from chainer.dataset import dataset_mixin


def _read_image_as_array(path, dtype):
    f = Image.open(path)
    try:
        image = numpy.asarray(f, dtype=dtype)
    finally:
        # Only pillow >= 3.0 has 'close' method
        if hasattr(f, 'close'):
            f.close()
    return image


class MultiLabeledImageDataset(dataset_mixin.DatasetMixin):

    """Dataset of image and label pairs built from a list of paths and labels.

    This dataset reads an external image file like :class:`ImageDataset`. The
    difference from :class:`ImageDataset` is that this dataset also returns a
    label integer. The paths and labels are given as either a list of pairs or
    a text file contains paths/labels pairs in distinct lines. In the latter
    case, each path and corresponding label are separated by white spaces. This
    format is same as one used in Caffe.

    .. note::
       **This dataset requires the Pillow package being installed.** In order
       to use this dataset, install Pillow (e.g. by using the command ``pip
       install Pillow``). Be careful to prepare appropriate libraries for image
       formats you want to use (e.g. libpng for PNG images, and libjpeg for JPG
       images).

    .. warning::
       **You are responsible for preprocessing the images before feeding them
       to a model.** For example, if your dataset contains both RGB and
       grayscale images, make sure that you convert them to the same format.
       Otherwise you will get errors because the input dimensions are different
       for RGB and grayscale images.

    Args:
        pairs (str or list of tuples): If it is a string, it is a path to a
            text file that contains paths to images in distinct lines. If it is
            a list of pairs, the ``i``-th element represents a pair of the path
            to the ``i``-th image and the corresponding label. In both cases,
            each path is a relative one from the root path given by another
            argument.
        root (str): Root directory to retrieve images from.
        dtype: Data type of resulting image arrays.
        label_dtype: Data type of the labels.

    """

    def __init__(self, pairs, root='.', dtype=numpy.float32,
                 label_dtype=numpy.int32):
        _check_pillow_availability()
        if isinstance(pairs, six.string_types):
            pairs_path = pairs
            with open(pairs_path) as pairs_file:
                pairs = []
                for i, line in enumerate(pairs_file):
                    pair = line.strip().split()
                    if len(pair) <= 1:
                        raise ValueError(
                            'invalid format at line {} in file {}'.format(
                                i, pairs_path))
                    pairs.append((pair[0],
                        [int(pair[index]) for index in range(1, len(pair))]))
        self._pairs = pairs
        self._root = root
        self._dtype = dtype
        self._label_dtype = label_dtype

    def __len__(self):
        return len(self._pairs)

    def get_example(self, i):
        path, multi_labels = self._pairs[i]
        full_path = os.path.join(self._root, path)
        image = _read_image_as_array(full_path, self._dtype)

        if image.ndim == 2:
            # image is greyscale
            image = image[:, :, numpy.newaxis]
        multi_labels = numpy.array(multi_labels, dtype=self._label_dtype)
        return image.transpose(2, 0, 1), multi_labels


def _check_pillow_availability():
    if not available:
        raise ImportError('PIL cannot be loaded. Install Pillow!\n'
                          'The actual import error is as follows:\n' +
                          str(_import_error))
