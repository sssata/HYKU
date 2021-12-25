from typing import Tuple
import numpy as np
import logging
import datetime

import matplotlib.pyplot as plt
from numpy.lib.function_base import meshgrid

logging.basicConfig()



def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


lin = np.linspace(0, 5, 500, endpoint=False)
yCoord, xCoord = np.meshgrid(lin, lin)


def sensorNoise():
    """
    Model AS5600 sensor noise
    """
    return np.random.normal(loc=0, scale=0.042*10)


def sensorNoise2():
    """
    Model AS5600 sensor noise
    """
    return np.random.uniform(low=-360/4096,high=360/4096)

def pMap(xCord, yCord):
    """
    Outputs the probability that the end effector is at the given 2d area.
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.ERROR)

    p = np.zeros((len(yCord), len(xCord)))
    logger.debug(f"x: {xCord}")
    logger.debug(f"y: {yCord}")

    length1 = 60
    length2 = 60

    for i in range(len(yCord)):
        for j in range(len(xCord)):

            logger.debug(f"P2x_ideal: {xCord[j]}, P2y_ideal: {yCord[i]}")

            distance_from_actual = list()
            error = 360/4096
            error_list = [
                [error, error],
                [error, -error],
                [-error, error],
                [-error, -error],
            ]
            for k in range(len(error_list)):

                P2x_ideal = xCord[j]
                P2y_ideal = yCord[i]

                P2_dist = np.sqrt(P2x_ideal ** 2 + P2y_ideal ** 2)
                alpha = np.arccos(
                    (length1 ** 2 + length2 ** 2 - P2_dist ** 2)
                    / (2 * length1 * length2)
                )
                logger.debug(f"alpha: {np.rad2deg(alpha)}")
                theta2 = np.rad2deg(alpha - np.pi)
                theta1 = np.rad2deg(
                    np.arctan2(P2y_ideal, P2x_ideal)
                    + np.arcsin((np.sin(alpha) * length2) / P2_dist)
                )

                theta1_error = theta1 + error_list[k][0]
                theta2_error = theta2 + error_list[k][1]
                logger.debug(
                    f"theta1_error: {theta1_error}, theta2_error: {theta2_error}"
                )

                p1x = length1 * np.cos(np.radians(theta1_error))
                p1y = length1 * np.sin(np.radians(theta1_error))

                p2x = p1x + length2 * np.cos(np.radians(theta1_error + theta2_error))
                p2y = p1y + length2 * np.sin(np.radians(theta1_error + theta2_error))

                logger.debug(f"p2x: {p2x}, p2y: {p2y}")

                distance_from_actual.append(
                    np.sqrt((p2x - P2x_ideal) ** 2 + (p2y - P2y_ideal) ** 2)
                )

                """xIndex = find_nearest(x, p2x)
                yIndex = find_nearest(y, p2y)

                if xIndex is not None and yIndex is not None:
                    p[yIndex, xIndex] += 1"""

            mean_dist = np.mean(distance_from_actual)

            p[i][j] = mean_dist

    print(p)

    return p


def pMap2(xCord, yCord):
    """
    Outputs the probability that the end effector is at the given 2d area.
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.ERROR)

    logger.debug(f"x: {xCord}")
    logger.debug(f"y: {yCord}")

    sampleListX = list()
    sampleListY = list()

    length1 = 60
    length2 = 60

    for i in range(len(yCord)):
        for j in range(len(xCord)):

            logger.debug(f"P2x_ideal: {xCord[j]}, P2y_ideal: {yCord[i]}")

            sample_count = 500

            for k in range(sample_count):

                P2x_ideal = xCord[j]
                P2y_ideal = yCord[i]

                P2_dist = np.sqrt(P2x_ideal ** 2 + P2y_ideal ** 2)
                alpha = np.arccos(
                    (length1 ** 2 + length2 ** 2 - P2_dist ** 2)
                    / (2 * length1 * length2)
                )
                logger.debug(f"alpha: {np.rad2deg(alpha)}")
                theta2 = np.rad2deg(alpha - np.pi)
                theta1 = np.rad2deg(
                    np.arctan2(P2y_ideal, P2x_ideal)
                    + np.arcsin((np.sin(alpha) * length2) / P2_dist)
                )

                theta1_error = theta1 + sensorNoise()
                theta2_error = theta2 + sensorNoise()
                logger.debug(
                    f"theta1_error: {theta1_error}, theta2_error: {theta2_error}"
                )

                p1x = length1 * np.cos(np.radians(theta1_error))
                p1y = length1 * np.sin(np.radians(theta1_error))

                p2x = p1x + length2 * np.cos(np.radians(theta1_error + theta2_error))
                p2y = p1y + length2 * np.sin(np.radians(theta1_error + theta2_error))

                logger.debug(f"p2x: {p2x}, p2y: {p2y}")

                sampleListX.append(p2x)
                sampleListY.append(p2y)

    print(sampleListX)
    print(sampleListY)

    return (sampleListX, sampleListY)

X_RES = 1920
Y_RES = 1080
X_NUM_POINTS = 50
Y_NUM_POINTS = 50

X_LEFT_SIDE_MM = 30
Y_BOTTOM_SIDE_MM = -20
HEIGHT_MM = 40
WIDTH_MM = HEIGHT_MM * (X_RES / Y_RES)
MM_TO_PIXEL_FACTOR = Y_RES/HEIGHT_MM

print(f"X_RES: {X_RES}")
print(f"Y_RES: {Y_RES}")
print(f"X_RES")

x = np.linspace(X_LEFT_SIDE_MM, X_LEFT_SIDE_MM + WIDTH_MM, X_NUM_POINTS)
y = np.linspace(Y_BOTTOM_SIDE_MM, Y_BOTTOM_SIDE_MM + HEIGHT_MM, X_NUM_POINTS)

xPixels = np.linspace(0, X_RES, X_NUM_POINTS)
yPixels = np.linspace(0, Y_RES, Y_NUM_POINTS)

mapResult = pMap(x, y)

mapResult *= MM_TO_PIXEL_FACTOR

FIG_HEIGHT= 9
fig, ax1 = plt.subplots(1,1, figsize=(FIG_HEIGHT,FIG_HEIGHT*Y_RES/X_RES)) # (width, height) in inches

ax1.set_xlabel("On Screen X Position [px]")
ax1.set_ylabel("On Screen Y Position [px]")


#ax1.set_aspect("equal", adjustable="datalim")

ax2 = ax1.twiny()
ax2.set_xlabel("Real X Position [cm]")
ax2.set_xlim(X_LEFT_SIDE_MM, X_LEFT_SIDE_MM + WIDTH_MM)
ax3 = ax1.twinx()
ax3.set_ylabel("Real Y  Position [cm]")
ax3.set_ylim(Y_BOTTOM_SIDE_MM, Y_BOTTOM_SIDE_MM + HEIGHT_MM)

cs = ax1.contourf(xPixels, yPixels, mapResult)

cbar = fig.colorbar(cs, ax=ax1, pad=0.05)

fig2, newax = plt.subplots(1,1) 

x = np.linspace(X_LEFT_SIDE_MM, X_LEFT_SIDE_MM + WIDTH_MM, 10)
y = np.linspace(Y_BOTTOM_SIDE_MM, Y_BOTTOM_SIDE_MM + HEIGHT_MM, 10)

something = pMap2(x, y)
newax.hist2d(something[0],something[1], bins=[int(X_RES/2),int(Y_RES/2)])


figManager = plt.get_current_fig_manager()
#plt.show()

plt.savefig('output_'+datetime.date.today().isoformat()+".png", dpi=1200)