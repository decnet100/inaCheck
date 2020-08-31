import cv2
import numpy as np


def comp(file1, file2):
    original = cv2.imread(file1)
    image_to_compare = cv2.imread(file2)

    # 1) Check if 2 images are equals
    if original.shape == image_to_compare.shape:
        # print("The images have same size and channels")
        difference = cv2.subtract(original, image_to_compare)
        b, g, r = cv2.split(difference)
        return np.mean(b) + np.mean(g) + np.mean(r)

        # if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
        # print("The images are completely Equal")
        # else:
        # print("The images are NOT equal")

    # 2) Check for similarities between the 2 images

    sift = cv2.xfeatures2d.SIFT_create()
    kp_1, desc_1 = sift.detectAndCompute(original, None)
    kp_2, desc_2 = sift.detectAndCompute(image_to_compare, None)

    index_params = dict(algorithm=0, trees=5)
    search_params = dict()
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(desc_1, desc_2, k=2)

    good_points = []
    ratio = 0.6
    for m, n in matches:
        if m.distance < ratio * n.distance:
            good_points.append(m)
    print(len(good_points))

    # Define how similar they are
    number_keypoints = 0
    number_keypoints = min(len(kp_1), len(kp_2))

    print("Keypoints 1ST Image: " + str(len(kp_1)))
    print("Keypoints 2ND Image: " + str(len(kp_2)))
    print("GOOD Matches:", len(good_points))
    result = cv2.drawMatches(original, kp_1, image_to_compare, kp_2, good_points, None)

    cv2.imshow("result", result)
    cv2.imshow("Original", original)
    cv2.imshow("Duplicate", image_to_compare)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    if number_keypoints > 0:
        print("How good is the match: ", len(good_points) / number_keypoints * 100, "%")

        return (len(good_points) / number_keypoints * 100)
    else:
        print("How good is the match: 0")
        return 0
