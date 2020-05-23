import numpy as np
import pydicom
from skimage.transform import resize
from skimage.restoration import unwrap_phase

# This is a script containing different methods that are auxiliary in
# Image Analysis and might be used by multiple algorithms.

# Joao Sousa wrote these simple methods (11/05/2020) to demonstrate
# what this file should look like. Feel free to write and include
# more complex methods that involve for example thresholding, filtering, etc.


def unwrap_phase_image(pixel_array):
    # Wrapping of the phase image according to
    # https://scikit-image.org/docs/dev/auto_examples/filters/plot_phase_unwrap.html
    wrapped_phase = np.angle(np.exp(2j * pixel_array))
    return unwrap_phase(wrapped_phase)


def convert_to_pi_range(pixel_array):
    """Set the image values to the interval [-pi, pi]."""
    if (np.amax(pixel_array) > 3.2) and (np.amin(pixel_array) < -3.2):
        # The value 3.2 was chosen instead of np.pi in order
        # to give some margin.
        pi_array = np.pi * np.ones(np.shape(pixel_array))
        min_array = np.amin(pixel_array) * np.ones(np.shape(pixel_array))
        max_array = np.amax(pixel_array) * np.ones(np.shape(pixel_array))
        radians_array = (2.0 * pi_array * (pixel_array - min_array) /
                         (max_array - min_array)) - pi_array
    else:
        # It means it's already on the interval [-pi, pi]
        radians_array = pixel_array
    return radians_array


def invert(pixel_array):
    return np.invert(pixel_array)


def square(pixel_array):
    return np.square(pixel_array)


def resize_array(pixel_array, pixel_spacing, reconst_pixel=None):
    """Resizes the given pixel_array, using reconstPixel as the reference
        of the resizing operation. This method assumes that the dimension
        axes=0 of pixel_array is the number of slices for np.shape > 2."""
    # This is so that data shares the same resolution and size

    if reconstPixel is not None:
        fraction = reconstPixel / pixelSpacing
    else:
        fraction = 1

    if len(np.shape(pixel_array)) == 2:
        pixel_array = resize(
            pixel_array, (pixel_array.shape[0] // fraction,
                          pixel_array.shape[1] // fraction),
            anti_aliasing=True)
    elif len(np.shape(pixel_array)) == 3:
        pixel_array = resize(pixel_array, (pixel_array.shape[0],
                                           pixel_array.shape[1] // fraction,
                                           pixel_array.shape[2] // fraction),
                             anti_aliasing=True)
    elif len(np.shape(pixel_array)) == 4:
        pixel_array = resize(pixel_array, (pixel_array.shape[0],
                                           pixel_array.shape[1],
                                           pixel_array.shape[2] // fraction,
                                           pixel_array.shape[3] // fraction),
                             anti_aliasing=True)
    elif len(np.shape(pixel_array)) == 5:
        pixel_array = resize(pixel_array, (pixel_array.shape[0],
                                           pixel_array.shape[1],
                                           pixel_array.shape[2],
                                           pixel_array.shape[3] // fraction,
                                           pixel_array.shape[4] // fraction),
                             anti_aliasing=True)
    elif len(np.shape(pixel_array)) == 6:
        pixel_array = resize(pixel_array, (pixel_array.shape[0],
                                           pixel_array.shape[1],
                                           pixel_array.shape[2],
                                           pixel_array.shape[3],
                                           pixel_array.shape[4] // fraction,
                                           pixel_array.shape[5] // fraction),
                             anti_aliasing=True)

    return pixel_array