import numpy as np
from PIL import Image, ImageChops, ImageDraw
from scipy.cluster.vq import kmeans
import matplotlib.pyplot as plt

def pilToNumpy(img):
    return np.array(img)


def NumpyToPil(img):
    # TODO optimize possibly using XYZ package
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

def get_max_dot(row):
    dot = np.diff(row)
    m = max(dot)
    return [i for i, j in enumerate(dot) if j == m][0]

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

def cluster_prediction(cluster, input):
    distances = [abs(input - x) for x in cluster[0]]
    cluster_idx_for_val = distances.index(min(distances))
    return cluster_idx_for_val

def img_and_end_px_to_progress(progress_coordinates, img_input, debug=False):
    im = img_input.convert("L")
    xx = pilToNumpy(im).astype(np.float32)
    target_row = xx[progress_coordinates["left"].y][progress_coordinates["left"].x:progress_coordinates["right"].x]
    draw = ImageDraw.Draw(im)
    draw.line((0, progress_coordinates["left"].y) + (im.size[0], progress_coordinates["left"].y), fill=128)

    endzone_pixel_col = xx[progress_coordinates["right"].x, progress_coordinates["right"].y]
    print("Crosshair col: %s" % endzone_pixel_col)
    # assert abs(max(target_row) - min(target_row)) > 30
    # clusters = kmeans(target_row, 3)
    # distances = [abs(endzone_pixel_col - x) for x in clusters[0]]
    # cluster_idx_for_endzone = distances.index(min(distances))
    # preds = [cluster_prediction(clusters, x) for x in target_row]
    # non_endzone_preds = [x for x in preds if x != cluster_idx_for_endzone]
    # progress_so_far_cluster_idx = non_endzone_preds[-1]
    # val_associated_with_progress = clusters[0][progress_so_far_cluster_idx]
    start_pixel = progress_coordinates["left"].x
    progress_pixel = progress_coordinates["progress"].x
    marked_points = [progress_coordinates["left"].x, progress_coordinates["progress"].x, progress_coordinates["right"].x]
    # finish line
    draw.line((start_pixel, 0) + (start_pixel, im.size[1]), fill=128)
    im.show()

    cropped_pbar = im.crop(
        (progress_coordinates["left"].x, progress_coordinates["left"].y - 20, progress_coordinates["right"].x, progress_coordinates["left"].y + 20))
    cropped_pbar.show()
    tared_points = [x - min(marked_points) for x in marked_points]
    normalized_points = [x / max(tared_points) for x in tared_points]
    progress = normalized_points[1]
    if debug:
        plt.plot(target_row)
        plt.ylabel('Col intensity 0-255')
        plt.title("col values. green is progress, blue is todo")
        plt.plot([0, len(target_row)], [endzone_pixel_col, endzone_pixel_col], color="blue")
        plt.plot([0, len(target_row)], [val_associated_with_progress, val_associated_with_progress], color="green")
        plt.xlabel('pixels left to right.')
        plt.show()

        plt.plot(preds)
        plt.ylabel('cluster index out of 3')
        plt.xlabel('pixels left to right.')
        plt.show()
    return progress