"""
roaster.py -- utilities for worker bean.py to use.
http://github.com/expresso-math/
Daniel Guilak <daniel.guilak@gmail.com> and Josef D. Lange <josef.d.lange@gmail.com>
"""
import cv2, cv
import numpy as np
from PIL import Image
from cStringIO import StringIO

import grinder

import redis
import rq

from roaster_settings import settings

r = redis.StrictRedis(host=settings['redis_hostname'], port=settings['redis_port'], db=settings['redis_db'])

g = grinder.Grinder()
g.load_data()
g.train(10)

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
    cropper = cv2.imdecode(img_array, -1)
    image = cv2.imdecode(img_array, 0)  # The second argument, zero, is a loading argument.
                                        # We _could_ put in "cv2.CV_LOAD_IMAGE_COLOR" to load color, by why bother?
    ## Do something with the image, then write back some symbols to the database, I presume...
    # Find contours (and hierarchy? I don't know what that is...)
    contours,hierarchy = cv2.findContours(image,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)

    for i,contour in enumerate(contours):
        if hierarchy[0,i,2] == -1 and hierarchy[0,i,3] != -1:
            x,y,w,h = cv2.boundingRect(contour)
            symbol_identifier = r.incr('symbol_identifier_ids')
            box = [x,y,w,h]

            crop = cropper[y:y+h,x:x+w] # CROP
            resized_crop = cv2.resize(crop, (90,90))  ## THE CROPPED AND RESIZED IS RIGHT HERE

            # Create the PIL version from our NumPy array image.
            crop_pil = Image.fromarray(resized_crop)
            crop_pil.convert("1")
            padded = Image.new("1", (100,100), 255)
            # print crop_pil.mode
            # print padded.mode
            padded.paste(crop_pil, (5,5,95,95))
            # Create a StringIO object to "write" to.
            crop_buffer = StringIO()
            
            # "Save" image to the buffer, seek the buffer back to zero.
            padded.save(crop_buffer, 'png')
            crop_buffer.seek(0)

            best_guess = g.guess_on_image_buffer(crop_buffer)
            print "BEST GUESS IS " + best_guess
            crop_buffer.seek(0)

            possible_characters = { best_guess : '1.0' }

            box_key = 'symbol_box:' + str(symbol_identifier)
            candidates_key = 'symbol_candidates:' + str(symbol_identifier)
            image_key = 'symbol_image:' + str(symbol_identifier)

            [r.rpush(box_key, value) for value in box]
            [r.zadd(candidates_key, possible_characters[key], key) for key in possible_characters.keys()]
            r.set(image_key, crop_buffer.read())

            crop_buffer.close()

            new_symbols.append(symbol_identifier)

    ## FAKING IT. EXPECTING 3x + 2 -- this line will sort the symbols from left to right so that our app can cheat and get it right.
    new_symbols = sorted_left_to_right(new_symbols)
    ## Clean up scores and put them in the order we know they'll be in.
    ctr = 0
    expression = ['3', 'x', '+', '2']
    for symbol in new_symbols:
        box_key = 'symbol_box:' + str(symbol)
        candidates_key = 'symbol_candidates:' + str(symbol)
        image_key = 'symbol_image:' + str(symbol)
        r.delete(candidates_key)
        r.zadd(candidates_key, 1.0, expression[ctr])
        ctr = ctr + 1

    [r.rpush('expression_symbols:' + expression_id, new_symbol) for new_symbol in new_symbols]

    return 1


def sorted_left_to_right(list_of_symbol_ids):
    print list_of_symbol_ids[0]
    print r.lrange('symbol_box:'+str(list_of_symbol_ids[0]),0,-1)
    ids_and_x_values = [(symbol_id, r.lrange('symbol_box:'+str(symbol_id),0,1)[0]) for symbol_id in list_of_symbol_ids]
    sorted_ids_and_x_values = sorted(ids_and_x_values, key=lambda tup: tup[1])
    return [x[0] for x in sorted_ids_and_x_values]

def reset():
    g.reset()
    g.load_data()
    g.train(100)

def train(imageData, asciiValue):
    """
    Takes image data and ascii value, crops symbols and feeds
    them to Ocrn to train into the MAINFRAME.
    """
    
    # Unpacks the data sent to us.
    new_symbols = []

    # Get the image from the DB.
    # string_value = r.get('expression_image:' + expression_id)

    # Opens buffer that takes imageValue as input
    image_buffer = StringIO(imageData)

    # Seeks to the beginning of the buffer
    image_buffer.seek(0)

    # Uses numpy to create some kind of data array with a predetermind byte encoding type
    img_array = np.asarray(bytearray(image_buffer.read()), dtype=np.uint8)

    # Gets a CV2 image from the data array.
    cropper = cv2.imdecode(img_array, 0)
    image = cv2.imdecode(img_array, 0)  # The second argument, zero, is a loading argument.
                                        # We _could_ put in "cv2.CV_LOAD_IMAGE_COLOR" to load color, by why bother?
    ## Do something with the image, then write back some symbols to the database, I presume...
    # Find contours (and hierarchy? I don't know what that is...)
    contours,hierarchy = cv2.findContours(image,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)

    # Will hold all cropped and resized images to be sent on to
    # Ocrn.
    croppedImages = []

    for i,contour in enumerate(contours):
        if hierarchy[0,i,2] == -1 and hierarchy[0,i,3] != -1:
            x,y,w,h = cv2.boundingRect(contour)
            symbol_identifier = r.incr('symbol_identifier_ids')
            box = [x,y,w,h]

            # Resizes to 100x100
            crop = cropper[y:y+h,x:x+w] # CROP
            resized_crop = cv2.resize(crop, (90,90))  ## THE CROPPED AND RESIZED IS RIGHT HERE
                                                        ## BUT HOW DO I GET IT INTO STRING!? SHIT.
            crop_pil = Image.fromarray(resized_crop)
            crop_pil.convert("1")
            padded = Image.new("1", (100,100), 1)
            # print crop_pil.mode
            # print padded.mode
            padded.paste(crop_pil, (5,5,95,95))

            croppedImages.append(padded)

    # Here we will want to send the (croppedImages, asciiValue) data
    # Through to Ocrn.
    # ft.feature.generateDataSetFromRoaster((croppedImages,asciiValue))
    g.add_data((croppedImages, asciiValue))


    return 1
