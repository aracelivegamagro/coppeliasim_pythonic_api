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

    num_rooms = 4
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

    areas = []
    for room in apartment.total_rooms_and_corridors:
        if room.type == 'corridor':
            continue
        areas.append(room.area)

    print(areas)

    n_bathrooms = labels.count('bathroom')
    n_livingrooms = labels.count('livingroom')
    print(f' baños = {n_bathrooms}    salones = {n_livingrooms}')

    areas_aux = areas

    min_areas = []
    for n in range(n_bathrooms):
        minimum = min(areas_aux)

        areas_aux.remove(minimum)
        min_areas.append(minimum)

    areas_aux = areas

    max_areas = []
    for n in range(n_livingrooms):
        maximum = max(areas_aux)
        areas_aux.remove(maximum)
        max_areas.append(maximum)

    print(f'min_areas ={min_areas}    max_areas = {max_areas}')
    # Primero asigno la habitación más grande y la más pequeña
    for room in apartment.total_rooms_and_corridors:
        if room.type != 'genericRoom':
            continue

        if room.area in min_areas:
            room.type = 'bathroom'
            labels.remove('bathroom')
            min_areas.remove(room.area)

        elif room.area in max_areas:
            room.type = 'livingroom'
            labels.remove('livingroom')
            max_areas.remove(room.area)

    # Después se etiquetan el resto de las habitaciones
    for room in apartment.total_rooms_and_corridors:

        if room.type != 'genericRoom':
            continue

        choice = random.choice(labels)
        room.type = choice
        labels.remove(choice)

    for i, room in enumerate(apartment.total_rooms_and_corridors):
        if room.type == 'corridor':
            continue
        print(f'Room {i} with area of {room.area} is of type {room.type}')

    print(' ----------------------------------------------------------------------- ')
