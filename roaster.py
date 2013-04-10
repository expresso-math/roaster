"""
roaster.py -- utilities for worker bean.py to use.
http://github.com/expresso-math/
Daniel Guilak <daniel.guilak@gmail.com> and Josef D. Lange <josef.d.lange@gmail.com>
"""
import cv2, cv
import numpy as np
from PIL import Image
from cStringIO import StringIO

import redis
import rq

r = redis.StrictRedis(host='ec2-54-244-145-206.us-west-2.compute.amazonaws.com', port=6379, db=1)

def identify_symbols(expression_id):
    
    # Unpacks the data sent to us.
    new_symbols = []

    # Get the image from the DB.
    string_value = r.get('expression_image:' + expression_id)

    # Opens buffer that takes imageValue as input
    image_buffer = StringIO(string_value)

    # Seeks to the beginning of the buffer
    image_buffer.seek(0)

    # Uses numpy to create some kind of data array with a predetermind byte encoding type
    img_array = np.asarray(bytearray(image_buffer.read()), dtype=np.uint8)

    # Gets a CV2 image from the data array.
    image = cv2.imdecode(img_array, 0)  # The second argument, zero, is a loading argument.
                                        # We _could_ put in "cv2.CV_LOAD_IMAGE_COLOR" to load color, by why bother?
    ## Do something with the image, then write back some symbols to the database, I presume...

    # Find contours (and hierarchy? I don't know what that is...)
    contours,hierarchy = cv2.findContours(image,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        symbol_identifier = r.incr('symbol_identifier_ids')
        box = [x,y,w,h]
        possible_characters = { 'a' : 0.1 }

        box_key = 'symbol_box:' + str(symbol_identifier)
        candidates_key = 'symbol_candidates:' + str(symbol_identifier)
        
        [r.rpush(box_key, value) for value in box]
        [r.zadd(candidates_key, possible_characters[key], key) for key in possible_characters.keys()]

        new_symbols.append(symbol_identifier)

    [r.rpush(expression_identifier, new_symbol) for new_symbol in new_symbols]

    return 1