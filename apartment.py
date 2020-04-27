import math
import random

import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

from coppeliasimapi import CoppeliaSimAPI

# posibles signos del width, height en funcion del lado del pasillo
dict_side_sign = {
    'bottom': [1, -1],
    'right': [1, 1],
    'top': [1, 1],
    'left': [-1, 1]
}

dict_opposite_side = {
    'bottom': 'top',
    'right': 'left',
    'top': 'bottom',
    'left': 'right'

}

# Almacena los qrect que serán las habitaciones a cada lado
dict_rooms_per_side = {
    'bottom': [],
    'right': [],
    'top': [],
    'left': []
}

# Indica en que posicion habrá un pasillo
# -1 no hay pasillo, 0 - a la izquierda, 1 - despues de la 1ª habitacion, 2 - despues de la 2ª habitación
dict_corridors_per_side = {
    'bottom': [],
    'right': [],
    'top': [],
    'left': []
}


def get_random_room():  # corridor_height, initial_corridor

    random_side = random.choice(['top', 'bottom'])

    if len(dict_rooms_per_side[random_side]) >= max_rooms_per_side:
        print(f'side {random_side} has already the maximum of rooms')
        random_side = dict_opposite_side[random_side]

    print(f'side chosed = {random_side}')

    corridor_locations = dict_corridors_per_side[random_side]
    new_corridor_width = initial_corridor.height()

    add_corridor = False
    # if corridor_location == len(dict_rooms_per_side[random_side]):
    if len(dict_rooms_per_side[random_side]) in corridor_locations:
        add_corridor = True

    if len(dict_rooms_per_side[random_side]) == 0:
        if add_corridor:
            if random_side == 'bottom':
                random_point = initial_corridor.topLeft()
                random_point = QPointF(random_point.x() + new_corridor_width, random_point.y())

            else:
                random_point = initial_corridor.bottomLeft()
                random_point = QPointF(random_point.x() + new_corridor_width, random_point.y())

        else:
            if random_side == 'bottom':
                random_point = initial_corridor.topLeft()
            else:
                random_point = initial_corridor.bottomLeft()

        # random_point = random.choice(list(dict_corridor_points[random_side]))

    else:
        if add_corridor:
            prev = dict_rooms_per_side[random_side][-1].topRight()
            random_point = QPointF(prev.x() + new_corridor_width, prev.y())
        else:
            random_point = dict_rooms_per_side[random_side][-1].topRight()

    print(f'random point = {random_point}')

    # --. Se escogen un ancho y un alto para la habitacion teninedo en cuenta el lado del pasillo en el que estará la
    # habitacion si esta en la parte de abajo del pasillo la altura no puede ser positiva porque se comería el
    # pasillo---
    signed_width = dict_side_sign[random_side][0]
    signed_height = dict_side_sign[random_side][1]

    random_width = signed_width * (random.uniform(3, 6))
    random_height = signed_height * fixed_w_h_room

    print(f'Creating room with width = {random_width} and height = {random_height}')

    # --- Se crea un rectangulo con el ancho y alto seleccionado
    random_room = QRectF(random_point.x(), random_point.y(), random_width, random_height)

    # Se comprueba que la habitación no interseccione con ninguna otra o no contenga a alguan otra
    valid_room = True

    for prev_room in random_qrect_list:
        intersected = random_room.intersects(prev_room)
        room_contained_in_prev = prev_room.contains(random_room)
        prev_contained_in_room = random_room.contains(prev_room)

        if intersected or room_contained_in_prev or prev_contained_in_room:
            print('room intersects with existing room')
            valid_room = False
            break

    if valid_room:
        random_qrect_list.append(random_room)
        dict_rooms_per_side[random_side].append(random_room)

    return valid_room


def add_door_center(room_):
    line = QLineF(room_.topLeft(), room_.topRight())
    line_lenght = int(line.length())        # -1 sin pasillo, 0 antes de la primera habitacion, 1 antes de la segunda

    step = line_lenght / 100.

    line_points = []
    for t in np.arange(0.25, 0.75, step):
        line_point = line.pointAt(t)
        line_points.append(QPointF(line_point.x(), line_point.y()))

    random_center_door = random.choice(line_points)

    left_door = QPointF(random_center_door.x() - 0.5, random_center_door.y())
    right_door = QPointF(random_center_door.x() + 0.5, random_center_door.y())

    polygon = QPolygonF(
        [right_door, room_.topRight(), room_.bottomRight(), room_.bottomLeft(), room_.topLeft(), left_door])

    return polygon


def add_door_left(room_, side_):
    line = QLineF(room_.topLeft(), room_.bottomLeft())

    line_lenght = int(line.length())
    step = line_lenght / 100.

    line_points = []
    for t in np.arange(0.25, 0.75, step):
        line_point = line.pointAt(t)
        line_points.append(QPointF(line_point.x(), line_point.y()))

    random_center_door = random.choice(line_points)

    left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
    right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

    if side_ == 'bottom':
        polygon = QPolygonF(
            [right_door, room_.topLeft(), room_.topRight(), room_.bottomRight(), room_.bottomLeft(), left_door])

    elif side_ == 'top':
        polygon = QPolygonF(
            [right_door, room_.bottomLeft(), room_.bottomRight(), room_.topRight(), room_.topLeft(), left_door])

    return polygon


def add_door_right(room_, side_):
    line = QLineF(room_.topRight(), room_.bottomRight())

    line_lenght = int(line.length())
    step = line_lenght / 100.

    line_points = []
    for t in np.arange(0.25, 0.75, step):
        line_point = line.pointAt(t)
        line_points.append(QPointF(line_point.x(), line_point.y()))

    random_center_door = random.choice(line_points)

    left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
    right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

    if side_ == 'bottom':
        polygon = QPolygonF(
            [right_door, room_.topRight(), room_.topLeft(), room_.bottomLeft(), room_.bottomRight(), left_door])

    elif side_ == 'top':
        polygon = QPolygonF(
            [right_door, room_.bottomRight(), room_.bottomLeft(), room_.topLeft(), room_.topRight(), left_door])

    return polygon


# --------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------

setproctitle.setproctitle('Coppelia_random_appartment')
pygame.display.init()
coppelia = CoppeliaSimAPI(['./models/'])

# Stop the simulator and close the scene, just in case.
coppelia.stop()
coppelia.close()
coppelia.stop()
coppelia.close()

# Move the floor downwards, as we want to use a prettier floor.
print('Getting floor name')
floor = coppelia.get_object_handle('ResizableFloor_5_25')
# print('ret:', floor)
coppelia.set_object_transform('ResizableFloor_5_25', 0.0, 0.0, -2.0, 0)
coppelia.scale_object('ResizableFloor_5_25', 0.1, 0.1, 0.1)
coppelia.set_object_position('DefaultCamera', 0, 0, 25.)
coppelia.set_object_orientation('DefaultCamera', 3.14, 0, 3.14)

# --------------------------------------------------------------------------------------------------------
# ----------------------------- Se selecciona el numero de habitaciones ----------------------------------
# --------------------------------------------------------------------------------------------------------

num_rooms = random.randint(1, 2)
max_rooms_per_side = math.ceil(num_rooms / 2)

print(f'Creating {num_rooms} rooms', f' with max rooms per side {max_rooms_per_side}')

# --------------------------------------------------------------------------------------------------------
# ----------------------------- Se eligen de forma aleatoria los pasillos --------------------------------
# --------------------------------------------------------------------------------------------------------

# -1 sin pasillo, 0 antes de la primera habitacion, 1 antes de la segunda

corridor_position = np.arange(-1, max_rooms_per_side)
print(corridor_position)

possibles_corridors_per_side = round(max_rooms_per_side / 2)
if possibles_corridors_per_side == 0:
    possibles_corridors_per_side = 1

print(f'k {possibles_corridors_per_side}')

dict_corridors_per_side['top'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)
dict_corridors_per_side['bottom'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)

# Si los dos lados tienen ambos pasillos a la derecha o a la izquierda el boundingbox lo va a eliminar -Se intenta evitar
# REVISAR

if 0 in dict_corridors_per_side['top'] and 0 in dict_corridors_per_side['bottom']:
    delete_corridor_from = random.choice(['top', 'bottom'])
    dict_corridors_per_side[delete_corridor_from].remove(0)

if (max_rooms_per_side - 1) in dict_corridors_per_side['top'] and (max_rooms_per_side - 1) in dict_corridors_per_side[
    'bottom']:
    delete_corridor_from = random.choice(['top', 'bottom'])
    dict_corridors_per_side[delete_corridor_from].remove(max_rooms_per_side - 1)

print('posicion pasillo parte superior', dict_corridors_per_side['top'])
print('posicion pasillo parte inferior', dict_corridors_per_side['bottom'])

# --------------------------------------------------------------------------------------------------------
# ----------- Crear pasillo inicial a partir del que se construyen las habitaciones ----------------------
# --------------------------------------------------------------------------------------------------------

# quiero que todas las habitaciones a un mismo lado tengan el mismo ancho o alto (si el pasillo es horizontal sera el alto)
fixed_w_h_room = random.uniform(4, 6)
print(f'el tamaño fijado es de {fixed_w_h_room}')

# Crear pasillo initial
corridor_width = random.uniform(num_rooms * 4 / 2, num_rooms * 8 / 2)
corridor_height = random.uniform(1.5, 3)

print(F'Creating corridor with width = {corridor_width} and height = {corridor_height}')

initial_corridor = QRectF(0, 0, corridor_width, corridor_height)
initial_corridor.translate(-initial_corridor.center())  # Traslado el pasillo al centro

print('Initial corridor --- ',
      f'Center = {initial_corridor.center()}\n',
      f'Top Left = {initial_corridor.topLeft()}\n',
      f'Top Right = {initial_corridor.topRight()}\n'
      f'Bottom Left = {initial_corridor.bottomLeft()}\n',
      f'Bottom Right = {initial_corridor.bottomRight()}\n')

corridor_sides = {  # bottom y top deben estar cambiados
    'bottom': [initial_corridor.topLeft(), initial_corridor.topRight()],
    'right': [initial_corridor.topRight(), initial_corridor.bottomRight()],
    'top': [initial_corridor.bottomLeft(), initial_corridor.bottomRight()],
    'left': [initial_corridor.topLeft(), initial_corridor.bottomLeft()]
}

# --------------------------------------------------------------------------------------------------------
# ------------ Se buscan n habitaciones que no interseccionen ni contengan a ninguna otra  --------------
# --------------------------------------------------------------------------------------------------------
random_qrect_list = []

for i in range(0, num_rooms):
    print(f'------------ i - {i} ------------')

    valid = False
    count = 0

    while not valid:
        if count > 100:
            break
        else:
            valid = get_random_room()
            count += 1

    if count > 100:
        print(f'room {i} is not valid')
        continue

    print('---------------')

# --------------------------------------------------------------------------------------------------------
# ----------------------- Ajustar la habitacion para que no queden pasillos estrechos -------------------
# --------------------------------------------------------------------------------------------------------


print(f'----- {len(random_qrect_list)} have been created -----')

if len(random_qrect_list) > 1:

    dict_side_width = {
        'bottom': 0.,
        'right': 0.,
        'top': 0.,
        'left': 0.
    }

    print(f'num max rooms per side {max_rooms_per_side}')

    for side, rooms_list in dict_rooms_per_side.items():
        print(f' side {side} has {len(rooms_list)} rooms ')
        for r in rooms_list:
            dict_side_width[side] += r.width()

    for side, corridor_w in dict_corridors_per_side.items():
        print(f'side {side} has {len(corridor_w)} corridors')
        for w in corridor_w:
            if w != -1:
                dict_side_width[side] += corridor_height

    print(f'dict_side_width {dict_side_width}')

    UpperRight = dict_rooms_per_side['top'][-1].topRight()
    bottomRight = dict_rooms_per_side['bottom'][-1].topRight()

    diff = abs(dict_side_width['top'] - dict_side_width['bottom'])

    # Si la diferencia es muy pequeña ajusto el ancho, si es demasiado grande añado un pasillo
    # Si ensanchamos la habitacion eliminamos el siguiente pasillo si lo hubiese
    if diff < corridor_height - 1.:
        print('Modifying corridor --- widening room')

        if dict_side_width['top'] > dict_side_width['bottom']:

            dict_rooms_per_side['bottom'][-1].setTopRight(QPointF(UpperRight.x(), bottomRight.y()))
            corridor_to_remove = len(dict_rooms_per_side['bottom'])
            if corridor_to_remove in dict_corridors_per_side['bottom']:
                dict_corridors_per_side['bottom'].remove(corridor_to_remove)

        else:
            dict_rooms_per_side['top'][-1].setTopRight(QPointF(bottomRight.x(), UpperRight.y()))
            corridor_to_remove = len(dict_rooms_per_side['top'])
            if corridor_to_remove in dict_corridors_per_side['top']:
                dict_corridors_per_side['top'].remove(corridor_to_remove)

    # Si añadimos un pasillo a la derecha lo añadimos a la lista de pasillos si no estuviese
    elif diff > corridor_height:
        print('Modifying corridor --- creating corridor ')

        if dict_side_width['top'] > dict_side_width['bottom']:
            dict_rooms_per_side['bottom'][-1].setTopRight(QPointF(UpperRight.x() - corridor_height, bottomRight.y()))
            new_corridor_location = len(dict_rooms_per_side['bottom'])
            if new_corridor_location not in dict_corridors_per_side['bottom']:
                dict_corridors_per_side['bottom'].append(new_corridor_location)

        else:
            dict_rooms_per_side['top'][-1].setTopRight(QPointF(bottomRight.x() - corridor_height, UpperRight.y()))
            new_corridor_location = len(dict_rooms_per_side['top'])
            if new_corridor_location not in dict_corridors_per_side['top']:
                dict_corridors_per_side['top'].append(new_corridor_location)

    else:

        print('Not modifying last corridor')

# --------------------------------------------------------------------------------------------------------
# -------------------- Cambiamos la dimensión de la habitación de forma aleatoria ----------------------
# ----------------------------------------y añadimos puertas -------------------------------------------
# --------------------------------------------------------------------------------------------------------

print('posicion pasillo parte superior', dict_corridors_per_side['top'])
print('posicion pasillo parte inferior', dict_corridors_per_side['bottom'])

union_polygon = QPolygonF()
result_polygon_list = []

for side, rooms_list in dict_rooms_per_side.items():

    for i, room in enumerate(rooms_list):

        # #Cambio el ancho de la habitación de forma aleatoria (para no quedarme sin pasillo como maximo la muevo un tercio de este)
        # random_sign = [1,-1]
        # random_mov = list(np.arange(0, corridor_height/3, 0.05))
        # room.setTopLeft(QPointF(room.topLeft().x(),room.topLeft().y() + random.choice(random_sign)*random.choice(random_mov)))

        # Selecciono dónde va a estar la puerta
        possibles_door_locations = ['center']
        if i in dict_corridors_per_side[side]:  # Pasillo a la izquierda
            possibles_door_locations.append('left')

        if i + 1 in dict_corridors_per_side[side]:
            possibles_door_locations.append('right')

        door_location = random.choice(possibles_door_locations)

        if door_location == 'center':
            room_polygon_with_door = add_door_center(room)
        elif door_location == 'left':
            room_polygon_with_door = add_door_left(room, side)
        elif door_location == 'right':
            room_polygon_with_door = add_door_right(room, side)

        # --- Añadir habitaciones al pasillo ----
        result_polygon_list.append(room_polygon_with_door)
        union_polygon = union_polygon.united(room_polygon_with_door)  # Para obtener el bounding box

# --------------------------------------------------------------------------------------------------------
# ------------------------------------------- Dibujar paredes -------------------------------------------
# --------------------------------------------------------------------------------------------------------

# Bounding rect para centrar
boundingRect = union_polygon.boundingRect()

if len(result_polygon_list) > 1:
    result_polygon_list.append(QPolygonF(boundingRect, closed=True))

center = boundingRect.center()

for polygon in result_polygon_list:

    polygon.translate(-center)  # Desplazo los poligonos para que la habitación esté centrada

    prev_point = polygon[0]

    for i, curr_point in enumerate(polygon):
        if i == 0:
            continue

        coppelia.create_wall([prev_point.x(), prev_point.y(), 0], [curr_point.x(), curr_point.y(), 0])
        prev_point = curr_point

fscale_x = boundingRect.width() / 5 + 0.5
fscale_y = boundingRect.height() / 5 + 0.5

# Create and scale a floor
r = coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm', 0, 0, 0, 0)

coppelia.scale_object(r, fscale_x, fscale_y, 1)
for handle in coppelia.get_objects_children(r):
    coppelia.scale_object(handle, fscale_x, fscale_y, 1)
