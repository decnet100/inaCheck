# INADEF Image Preparation/Manipulation/Analysis module
# WARNING: Currently stores stuff that is obsolete or not required at all


import os
from math import sqrt

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
# import skimage
from skimage import io, img_as_ubyte
from skimage.exposure import match_histograms
from skimage.feature import blob_doh
from skimage.metrics import mean_squared_error
from skimage.metrics import structural_similarity as ssim

from inadefChecker.inaconf import inaconf

matplotlib.rcParams['font.size'] = 8


def imgcrop(img, crop=[0, 0, 0, 0]):
    if crop != [0, 0, 0, 0]:  # expect format x1 y1 x2 y2

        return img[crop[1]: crop[3], crop[0]: crop[2]]
    else:
        return img


from skimage.color import rgb2hsv


def matchhist(file, reference):
    img_ref = img_as_float(io.imread(reference))
    img_comp = img_as_float(io.imread(file))
    outfile = os.path.splitext(file)[0] + '_hist.jpg'
    matched = match_histograms(img_comp, img_ref, multichannel=True)
    io.imsave(outfile, img_as_ubyte(matched))
    return outfile


def checksim(reference, edge, crop, match_hist=False):
    img_ref = imgcrop(img_as_float(io.imread(reference)), crop)
    img_comp = imgcrop(img_as_float(io.imread(edge)), crop)
    if match_hist:
        matched = match_histograms(img_comp, img_ref, multichannel=True)
    else:
        matched = img_comp

    # shift, error, diffphase = phase_cross_correlation(img_ref, img_comp)
    # ssim_calc = ssim(img_ref, matched,  data_range=img_ref.max() - img_ref.min())
    mse = sqrt(mean_squared_error(img_ref, matched))
    sim = mse
    return sim


def img_similarity(file1, file2, as_gray=False):
    img_ref = img_as_float(io.imread(file1, as_gray=as_gray))
    img_comp = img_as_float(io.imread(file2, as_gray=as_gray))
    ssim_calc = ssim(img_ref, img_comp, multichannel=not (as_gray))
    # return 1 - (1 + ssim_calc ) /2
    return ssim_calc


def has_color_info(file, crop):
    # bw_image = img_as_float(io.imread(file, as_gray = True))
    image = imgcrop(img_as_float(io.imread(file)), crop)
    hsv = rgb2hsv(image)
    # hue = hsv[:,:,0]
    # print(guess_spatial_dimensions(image))
    if (np.median(hsv[1]) == 0 and np.median(hsv[0]) == 0):
        return False
    else:
        return True


from skimage import morphology


def edgeform(img, origfile, overwrite=False, outdir=''):
    if outdir == '':
        outpath = os.path.splitext(origfile)[0] + '_edge.jpg'
    else:
        outpath = os.path.join(outdir, os.path.basename(origfile))
    outimg = morphology.binary_dilation(morphology.binary_dilation(feature.canny(img, sigma=3)))
    if (not os.path.isfile(outpath) or overwrite):  # if it doesn't already exist
        io.imsave(outpath, outimg)
    return outimg, outpath


def getedge(img, crop=[0, 0, 0, 0], outdir=''):
    if crop != [0, 0, 0, 0]:
        image = imgcrop(img_as_float(io.imread(img, as_gray=True)), crop)
    else:
        image = img_as_float(io.imread(img, as_gray=True))
    edge, outfile = edgeform(image, img, outdir=outdir)
    return np.sum(np.absolute(edge)), outfile


from skimage.transform import resize


def img_downsample(file, factor=4.0):
    image = img_as_float(io.imread(file))
    if image.shape[1] > 640:
        ds = resize(image, (int(image.shape[0] // factor), int(image.shape[1] // factor)),
                    anti_aliasing=True)

        io.imsave(file + '_ds.jpg', ds)
        return file + '_ds.jpg'
    else:
        return file


def sizechecker(file, supposed_longside=640):
    image = img_as_float(io.imread(file))
    height, width, depth = image.shape
    if height > supposed_longside:
        factor = height / supposed_longside
        return img_downscale(file, factor)

    else:
        return file


def daycheck(img1, img2):
    edge1 = img_downsample(img1)
    edge2 = img_downsample(img2)
    diff = img_difference(edge1, edge2)
    agreement = diff[0] / min(diff[1], diff[2])
    qual = min(diff[1], diff[2]) / max(diff[1], diff[2])
    return agreement, qual


def battcheck(imgfile):
    # crop = [335,465,367,478]
    crop = inaconf.battcrop
    image = img_as_ubyte(imgcrop(io.imread(imgfile, as_gray=True), crop))
    full = 81000  # counting white pixels
    empty = 98709  # the more white, the emptier

    val = np.sum(image)
    # print(val)
    # io.imsave(r'c:\temp\battimg.jpg',image)
    output = round((val - empty) / (full - empty), 1)
    return output

    # print (diff[0]- min(diff[1], diff[2]))


def img_difference(img1, img2, as_gray=True, crop=[0, 0, 0, 0], edgepath='', outpath=''):
    if crop == [0, 0, 0, 0]:
        image1 = img_as_float(io.imread(img1, as_gray=as_gray))
        image2 = img_as_float(io.imread(img2, as_gray=as_gray))
    else:
        image1 = imgcrop(img_as_float(io.imread(img1, as_gray=as_gray)), crop)
        image2 = imgcrop(img_as_float(io.imread(img2, as_gray=as_gray)), crop)
    can1, can1file = edgeform(image1, img1, outdir=edgepath)
    can2, can2file = edgeform(image2, img2, outdir=edgepath)
    # return cvcomp.comp(can1file, can2file)

    # diff = morphology(morphology.binary_dilation(morphology.binary_erosion(morphology.binary_erosion(compare_images(can1,can2, method='diff')))))
    diff = morphology.closing(morphology.opening(np.bitwise_and(can1, can2)))
    diffsum = np.sum(np.absolute(diff))
    # if outpath =='':
    #     compfile = os.path.splitext(img1)[0]+'_'+os.path.basename(img2)+'_'+diffsum + '.jpg'
    # else:
    #     compfile = os.path.join(outpath, os.path.splitext(os.path.basename(img1))[0] + '_' + os.path.basename(img2) + '_comp.jpg')
    #
    # io.imsave(compfile,diff)
    # fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(8, 3),
    #                                    sharex=True, sharey=True)
    #
    # ax1.imshow(can1, cmap=plt.cm.gray)
    # ax1.axis('off')
    # ax1.set_title(img1, fontsize=20)
    #
    # ax2.imshow(can2, cmap=plt.cm.gray)
    # ax2.axis('off')
    # ax2.set_title(img2, fontsize=20)
    #
    # ax3.imshow(diff, cmap=plt.cm.gray)
    # ax3.axis('off')
    # ax3.set_title('diff', fontsize=20)
    #
    # fig.tight_layout()
    #
    # plt.show()
    #
    #
    # #diffimg = rgb2gray(image1 - image2)
    # #diffimg = (diffimg - np.mean(diffimg))**2
    # #diffimg = mean_squared_error(image1, image2)
    #
    #
    return diffsum, np.sum(np.absolute(can1)), np.sum(np.absolute(can2))
    #


def cropsave(file, crop, as_gray=False):
    image = imgcrop(io.imread(file, as_gray=as_gray), crop)
    outdir = os.path.join(os.path.split(file)[0], 'crop')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
        print("Directory ", outdir, " Created ")
    else:
        print("Directory ", outdir, " already exists")
    outpath = os.path.join(outdir, os.path.splitext(os.path.basename(file))[0] + '_crop.jpg')

    # if not os.path.isfile(outpath):
    io.imsave(outpath, img_as_uint(image))
    # else:
    # print('%s already exists.' % outpath)
    return outpath


def plot_img_and_hist(image, axes, bins=256):
    """Plot an image along with its histogram and cumulative histogram.

    """
    image = img_as_float(image)
    ax_img, ax_hist = axes
    ax_cdf = ax_hist.twinx()

    # Display image
    ax_img.imshow(image, cmap=plt.cm.gray)
    ax_img.set_axis_off()

    # Display histogram
    ax_hist.hist(image.ravel(), bins=bins, histtype='step', color='black')
    ax_hist.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))
    ax_hist.set_xlabel('Pixel intensity')
    ax_hist.set_xlim(0, 1)
    ax_hist.set_yticks([])

    # Display cumulative distribution
    img_cdf, bins = exposure.cumulative_distribution(image, bins)
    ax_cdf.plot(bins, img_cdf, 'r')
    ax_cdf.set_yticks([])

    return ax_img, ax_hist, ax_cdf


from scipy.ndimage import gaussian_filter
from skimage.measure import find_contours, approximate_polygon
from skimage import img_as_float, img_as_uint, exposure
from skimage import feature, measure
from skimage.morphology import reconstruction


def edge(file):
    img = img_as_float(io.imread(file, as_gray=True))
    # edges1 = feature.canny(im, sigma = 2)

    # display results

    outdir = os.path.join(os.path.split(file)[0], 'edge')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
        print("Directory ", outdir, " Created ")
    else:
        print("Directory ", outdir, " already exists")
    outpath = os.path.join(outdir, os.path.splitext(os.path.basename(file))[0] + '_edge.jpg')

    if not os.path.isfile(outpath):
        contours = measure.find_contours(img, 0.8)

        outimg = image - dilated
        io.imsave(outpath, img_as_uint(contours))
    else:
        print('%s already exists.' % outpath)
    return outpath


def canny(image):
    im = img_as_float(io.imread(image, as_gray=True))
    # edges1 = feature.canny(im, sigma = 2)

    # display results

    outdir = os.path.join(os.path.split(image)[0], 'edge')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
        print("Directory ", outdir, " Created ")
    else:
        print("Directory ", outdir, " already exists")
    outpath = os.path.join(outdir, os.path.splitext(os.path.basename(image))[0] + '_edge.jpg')
    if not os.path.isfile(outpath):
        edges2 = feature.canny(im, sigma=2)

        # outimg = image - dilated
        io.imsave(outpath, img_as_uint(edges2))
    else:
        print('%s already exists.' % outpath)
    return outpath


def getavgbrightness(img):
    image = img_as_float(io.imread(img, as_gray=True))
    return np.mean(image)


def reflector_contains_blob(reflector, blob):
    # print blob.ndim
    if blob.ndim == 1:
        d = sqrt((blob[0] - int(reflector[0])) ** 2 + (blob[1] - int(reflector[1])) ** 2)
        if int(reflector[2]) >= (d + blob[2]):
            return True
        else:
            return False
    else:
        for blob_check in blob:
            d = sqrt((blob_check[0] - int(reflector[0])) ** 2 + (blob_check[1] - int(reflector[1])) ** 2)
            if int(reflector[2]) >= (d + blob_check[2]):
                return True
                break
            else:
                return False


def blobtest(img, reflectors):
    blobs = []
    blobs.append(blobdet(img))
    print('Image contains blobs:')
    print(blobs)
    missing_ref = []
    for reflector in reflectors:
        reflector_there = False
        for blob in blobs[len(blobs) - 1][1]:
            reflector_there = reflector_there or reflector_contains_blob(reflector, blob)
        if not reflector_there:
            inaconf.logprint('########## Blob Analysis: Reflector missing at image %s' % (img))
            missing_ref.append(reflector)

        else:
            print('Reflector %s found.' % (','.join(reflector)))
    return missing_ref


def dilate(img):
    image = img_as_float(io.imread(img, as_gray=True))
    image = gaussian_filter(image, 1)
    seed = np.copy(image)
    seed[1:-1, 1:-1] = image.min()
    mask = image

    dilated = reconstruction(seed, mask, method='dilation')
    outpath = os.path.splitext(img)[0] + '_dil.jpg'
    outimg = image - dilated
    io.imsave(outpath, outimg)
    return outpath


def polygonization(file):
    img = img_as_float(io.imread(file, as_gray=True))
    coordinates = []
    for contour in find_contours(img, 0):
        coords = approximate_polygon(contour, tolerance=2.5)
        if len(coords) > 3:
            coordinates.append(coords)
    return coordinates


def blobdet(img, min_sigma=2, max_sigma=30, threshold=0.01):
    image_gray = img_as_float(io.imread(img, as_gray=True))
    # image_gray = rgb2gray(image)

    # blobs_log = blob_log(image_gray, max_sigma=30, num_sigma=10, threshold=.1)

    # Compute radii in the 3rd column.
    # blobs_log[:, 2] = blobs_log[:, 2] * sqrt(2)
    #
    # blobs_dog = blob_dog(image_gray, max_sigma=30, threshold=.1)
    # blobs_dog[:, 2] = blobs_dog[:, 2] * sqrt(2)
    if min_sigma == 0:
        blobs_doh = blob_doh(image_gray, max_sigma=max_sigma, threshold=threshold)
    else:
        blobs_doh = blob_doh(image_gray, min_sigma=min_sigma, max_sigma=max_sigma, threshold=threshold)

    return [os.path.basename(img), blobs_doh]


def blobdraw(file, num, reflectorblob, outimg=''):
    # if isinstance(reflectorblob,list):
    #     expected = [int(reflectorblob[0]), int(reflectorblob[1]), int(reflectorblob[2])]
    # else:
    #     expected = []
    #     for ref in reflectorblob:
    #         expected.append([int(ref[0]), int(ref[1]), int(ref[2])])
    expected = np.array(reflectorblob).astype(np.int)
    if expected.ndim == 1:
        expected = [expected]

    image_gray = img_as_float(io.imread(file, as_gray=True))
    blobs_doh = blob_doh(image_gray, max_sigma=30, threshold=.01)
    # unmarked = [[0,0,0]]
    blobs_list = [blobs_doh, expected]
    colors = ['yellow', 'red']
    titles = ['Detected Blobs',
              'Expected Blobs']
    sequence = zip(blobs_list, colors, titles)

    fig, axes = plt.subplots(1, 2, figsize=(9, 2), sharex=True, sharey=True)
    ax = axes.ravel()

    for idx, (blobs, color, title) in enumerate(sequence):
        ax[idx].set_title(title)
        ax[idx].imshow(image_gray)
        for blob in blobs:
            y, x, r = blob
            c = plt.Circle((x, y), r, color=color, linewidth=2, fill=False)
            ax[idx].add_patch(c)
        ax[idx].set_axis_off()

    plt.tight_layout()
    # plt.title('cam %d, file %s'%(num, file))
    # plt.show()
    if outimg == '':
        outimg = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0] + '_plot.jpg')
    plt.savefig(outimg)
    return outimg


# blobs_list = [blobs_log, blobs_dog, blobs_doh]
# colors = ['yellow', 'lime', 'red']
# titles = ['Image', 'Detected Blobs',
#           'Expected Blobs']
# sequence = zip(blobs_list, colors, titles)
#
# fig, axes = plt.subplots(1, 3, figsize=(9, 3), sharex=True, sharey=True)
# ax = axes.ravel()
#
# for idx, (blobs, color, title) in enumerate(sequence):
#     ax[idx].set_title(title)
#     ax[idx].imshow(image_gray)
#     for blob in blobs:
#         y, x, r = blob
#         c = plt.Circle((x, y), r, color=color, linewidth=2, fill=False)
#         ax[idx].add_patch(c)
#     ax[idx].set_axis_off()
#
# plt.tight_layout()
# plt.show()
def is_highquality(image, night=True):
    lowcont = is_lowcontrast(image)
    if night:
        img = img_as_float(io.imread(image, as_gray=True))
        if exposure.is_low_contrast(img, fraction_threshold=0.35, lower_percentile=20, upper_percentile=99):
            print('low contrast original + night...')
            return False
        else:
            print('higher contrast original + night...')
            return True
    else:
        return True


def is_lowcontrast(image):
    img = img_as_float(io.imread(image, as_gray=True))
    # hist = exposure.histogram(img, nbins=3)
    # if hist[1][0] > 0:
    #     brightness = (hist[1][2]) / hist[1][0]
    # else:
    #     brightness = 0
    lowcont = exposure.is_low_contrast(img, fraction_threshold=0.02, lower_percentile=20, upper_percentile=80)
    return lowcont


def test(image=''):
    # Load an example image
    img = io.imread(image, as_gray=True)
    # img = image

    # Contrast stretching
    p2, p98 = np.percentile(img, (2, 98))
    img_rescale = exposure.rescale_intensity(img, in_range=(p2, p98))

    # Equalization
    img_eq = exposure.equalize_hist(img)

    # Adaptive Equalization
    img_adapteq = exposure.equalize_adapthist(img, clip_limit=0.03)

    # Display results
    fig = plt.figure(figsize=(8, 5))
    axes = np.zeros((2, 4), dtype=np.object)
    axes[0, 0] = fig.add_subplot(2, 4, 1)
    for i in range(1, 4):
        axes[0, i] = fig.add_subplot(2, 4, 1 + i, sharex=axes[0, 0], sharey=axes[0, 0])
    for i in range(0, 4):
        axes[1, i] = fig.add_subplot(2, 4, 5 + i)

    ax_img, ax_hist, ax_cdf = plot_img_and_hist(img, axes[:, 0])
    ax_img.set_title('Low contrast image')

    y_min, y_max = ax_hist.get_ylim()
    ax_hist.set_ylabel('Number of pixels')
    ax_hist.set_yticks(np.linspace(0, y_max, 5))

    ax_img, ax_hist, ax_cdf = plot_img_and_hist(img_rescale, axes[:, 1])
    ax_img.set_title('Contrast stretching')

    ax_img, ax_hist, ax_cdf = plot_img_and_hist(img_eq, axes[:, 2])
    ax_img.set_title('Histogram equalization')

    ax_img, ax_hist, ax_cdf = plot_img_and_hist(img_adapteq, axes[:, 3])
    ax_img.set_title('Adaptive equalization')

    ax_cdf.set_ylabel('Fraction of total intensity')
    ax_cdf.set_yticks(np.linspace(0, 1, 5))

    # prevent overlap of y-axis labels
    fig.tight_layout()


# plt.show()
# io.imsave(r'c:\temp\tst.jpg', plt)
plt.savefig(r'c:\temp\tst.jpg')
