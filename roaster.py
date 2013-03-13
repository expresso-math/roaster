"""
roaster.py -- utilities for worker bean.py to use.
http://github.com/expresso-math/
Daniel Guilak <daniel.guilak@gmail.com> and Josef D. Lange <josefdlange@gmail.com>
"""
import cv2, cv

import Image
import cStringIO

def saveImage(imageValue):
    # Opens buffer that takes imageValue as input
    buff = cStringIO.StringIO(imageValue)
    # Seeks to the beginning of the buffer
    buff.seek(0)
    # Opens a file to save the test image
    f = open('testImg.png', 'wb')
    f.write(buff.getvalue())
    f.close()
    # Successfully loads image into OpenCV format.
    im = cv.LoadImageM('testImg.png')
    
