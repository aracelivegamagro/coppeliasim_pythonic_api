import math
import random
import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

from coppeliasimapi import CoppeliaSimAPI

from apartment_creator import *

if '__main__':
    setproctitle.setproctitle('Coppelia_random_appartment')
    pygame.display.init()
    coppelia = CoppeliaSimAPI(['./models/'])

    # Stop the simulator and close the scene, just in case.
    coppelia.stop()
    coppelia.close()

    # Move the floor downwards, as we want to use a prettier floor.
    print('Getting floor name')
    floor = coppelia.get_object_handle('ResizableFloor_5_25')
    # print('ret:', floor)
    coppelia.set_object_transform('ResizableFloor_5_25', 0.0, 0.0, -2.0, 0)
    coppelia.scale_object('ResizableFloor_5_25', 0.1, 0.1, 0.1)
    coppelia.set_object_position('DefaultCamera', 0, 0, 30.)
    coppelia.set_object_orientation('DefaultCamera', 3.14, 0, 3.14)

    num_rooms = 2
    apartment = Apartment(coppelia, n_rooms=num_rooms)

    print('\n ----------------------------------------------------------------------- ')

    room_labels = ['bathroom', 'bedroom', 'kitchen', 'livingroom']

    if num_rooms >= len(room_labels):  # me aseguro que esten todas las habitaciones
        labels = room_labels
        k_ = num_rooms - len(room_labels)

        weights = [15, 15, 1, 1]
        labels.extend(random.choices(room_labels, weights, k=k_))

    else:
        weights = [15, 15, 1, 10]
        labels = random.choices(room_labels, weights, k=num_rooms)
        # labels = random.sample(room_labels, k=num_rooms)

    print(labels)

    print(' ----------------------------------------------------------------------- ')

    areas = []
    for room in apartment.total_rooms_and_corridors:
        if room.type == 'corridor':
            continue

        areas.append(room.area)

    print(areas)

    min_area = min(areas)
    max_area = max(areas)

    equal_rooms = False
    if min_area == max_area:
        equal_rooms = True

    print(f' min_area {min_area} ')
    print(f' max_area {max_area}')

# #Primero asigno la habitación más grande y la más pequeña
#     for room in apartment.total_rooms_and_corridors:
#
#         if room.type != 'genericRoom':
#             continue
#
#         if not equal_rooms:
#             n_bathrooms = labels.count('bathrooms')
#
#             for n in n_bathrooms:
#
#             if room.area == min_area and 'bathroom' in labels:
#                 room.type = 'bathroom'
#                 labels.remove('bathroom')
#                 continue
#
#             if room.area == max_area and 'livingroom' in labels:
#                 room.type = 'livingroom'
#                 labels.remove('livingroom')
#                 continue
#
#
#     for room in apartment.total_rooms_and_corridors:
#         if room.type == 'corridor':
#             continue
#

