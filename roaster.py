"""
roaster.py -- utilities for worker bean.py to use.
http://github.com/expresso-math/
Daniel Guilak <daniel.guilak@gmail.com> and Josef D. Lange <josefdlange@gmail.com>
"""
import cv2, cv
from PIL import Image
from cStringIO import StringIO

def identify_symbols(image_tuple):
    # Unpacks the data sent to us.
    expression_identifier = image_tuple(0)
    string_value = image_tuple(1)

    # Opens buffer that takes imageValue as input
    image_buffer = StringIO(string_value)

    # Seeks to the beginning of the buffer
    image_buffer.seek(0)

    # Uses numpy to create some kind of data array with a predetermind byte encoding type
    img_array = np.asarray(bytearray(image_buffer.read()), dtype=np.uint8)

    # Gets a CV2 image from the data array.
    image = cv2.imdecode(img_array, 0)  # The second argument, zero, is a loading argument.
                                        # We _could_ put in "cv2.CV_LOAD_IMAGE_COLOR" to load color, by why bother?
    ## Do something with the image, then write back some symbols to the database, I presume...?

    return image.type