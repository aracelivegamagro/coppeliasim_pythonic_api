import copy
import math
import random
import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

from coppeliasimapi import CoppeliaSimAPI

from apartment_creator import *


def furnish_bathroom(room):
    print('___ furnish bathroom ___')

    bathroom_models = {'toilet': './models/infrastructure/bathroom/toilet.ttm',
                       'basin': './models/infrastructure/bathroom/hand basin.ttm'
                       }

    dict_furniture_margins = {'basin': 0.2,
                              'toilet': 0.3}

    dict_angles_sides = {
        'top': 0,
        'right': -1.57,
        'bottom': 3.14,
        'left': 1.57

    }

    for f in bathroom_models.keys():
        point, f_loc = get_point_along_walls(room, dict_furniture_margins[f])
        coppelia.create_model(bathroom_models[f], point.x(), point.y(), 0.425, dict_angles_sides[f_loc])


def furnish_livingroom(room):
    print('___ furnish livingroom ___')

    room_rect = room.room_qrect

    living_models = {'sofa': './models/furniture/chairs/sofa.ttm',
                     'chair': './models/furniture/chairs/dining chair.ttm',
                     'plant': './models/furniture/plants/indoorPlant.ttm',
                     'coffe_table': './models/mymodels/coffe_table.ttm'
                     }

    point = get_point_inside_room(room_rect)
    angle = random.uniform(-0, 3.14 * 2)
    coffe_table = coppelia.create_model(living_models['coffe_table'], point.x(), point.y(), 0, 0)

    # objects_in_room = []
    #
    # n_sofas = random.randint(1, 3)
    # n_sofas = 1
    #
    # for i in range(n_sofas):
    #
    #     count = 0
    #     collision = True
    #
    #     while collision is True and count <= 10:
    #
    #         point = get_point_inside_room(room_rect)
    #         angle = random.uniform(-0, 3.14 * 2)
    #         sofa = coppelia.create_model(living_models['sofa'], point.x(), point.y(), 0.425, 0)
    #         coppelia.set_object_orientation(sofa, -1.57, -1.57 + angle, -1.57)
    #         coppelia.set_collidable(sofa)
    #
    #         if len(objects_in_room) == 0:
    #             collision = False
    #
    #         for obj in objects_in_room:
    #             if coppelia.check_collision(sofa, obj):
    #                 print('Hay colisión')
    #                 coppelia.remove_object(sofa)
    #             else:
    #                 collision = False
    #                 break
    #
    #         count += 1
    #
    #     if count > 10:
    #         print('cant locate furniture')
    #     else:
    #         objects_in_room.append(sofa)

    # point = get_point_inside_room(room_rect)
    # coppelia.create_model(living_models['chair'], point.x(), point.y(), 0.425, 0)
    #
    # point = get_point_inside_room(room_rect)
    # coppelia.create_model(living_models['plant'], point.x(), point.y(), 0.425, 0)


def furnish_kitchen(room):
    print('___ furnish livingroom ___')


def furnish_bedroom(room):
    print('___ furnish livingroom ___')


def get_point_along_walls(room, margin):
    r_aux = copy.deepcopy(room.room_qrect)

    r_aux = r_aux.adjusted(+margin, -margin, -margin, +margin)  # left,top,right,bottom

    lines = {'top': QLineF(r_aux.topLeft(), r_aux.topRight()),
             'right': QLineF(r_aux.topRight(), r_aux.bottomRight()),
             'bottom': QLineF(r_aux.bottomLeft(), r_aux.bottomRight()),
             'left': QLineF(r_aux.topLeft(), r_aux.bottomLeft())}

    del lines[room.door_position]

    side = random.choice(list(lines.keys()))
    p = random.uniform(0.25, 0.75)

    return QPointF(lines[side].pointAt(p).x(), lines[side].pointAt(p).y()), side


def get_point_inside_room(r):
    margin = 0.5
    left_m = r.left() + margin
    right_m = r.right() - margin
    bottom_m = r.bottom() + margin
    top_m = r.top() - margin

    return QPointF(random.uniform(left_m, right_m), random.uniform(bottom_m, top_m))


furnish_room = {'bathroom': furnish_bathroom,
                'livingroom': furnish_livingroom,
                'kitchen': furnish_kitchen,
                'bedroom': furnish_bedroom  }

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
        labels = random.sample(room_labels, k=num_rooms)

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

        furnish_room[room.type](room)

    print(' ----------------------------------------------------------------------- ')
