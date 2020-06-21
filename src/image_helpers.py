import numpy as np
from PIL import Image, ImageChops



def pilToNumpy(img):
    return np.array(img)


def NumpyToPil(img):
    return Image.fromarray(img)


def get_diff(filepath_a:str, filepath_b:str):
    prior = Image.open(filepath_a).convert("L")
    prior.load()
    current = Image.open(filepath_b).convert("L")
    current.load()
    diff = ImageChops.difference(current, prior)
    if diff.getbbox is not None:
        return diff
    else:
        return None
