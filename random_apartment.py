import random
import math
import random

import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF, Qt

from coppeliasimapi import CoppeliaSimAPI

dict_side_sign = {
    # posibles values of width, height
    'bottom': [[1, -1], [-1]],
    'right': [[1], [1, -1]],
    'top': [[1, -1], [1]],
    'left': [[-1], [1, -1]]
}

dict_orientation_sides = {  # para evitar habitaciones en la parte estrecha del pasillo
    'vertical': ['left', 'right'],
    'horizontal': ['top', 'bottom']

}

dict_rooms_per_side = {
    'bottom': 0,
    'right': 0,
    'top': 0,
    'left': 0
}

dict_opposite_side = {
    'bottom': 'top',
    'right': 'left',
    'top': 'bottom',
    'left': 'right'

}


def get_random_room():

    # --- Se elige en que lado del pasillo se va a insertar la habitación ---
    random_side = random.choice(list(dict_orientation_sides[orientation]))

    if dict_rooms_per_side[random_side] > max_rooms_per_side:
        print(f'side {random_side} has already the maximum of rooms')
        random_side = dict_opposite_side[random_side]


    print(f'side chosed = {random_side}')
    # --- Se escoge un punto aleatorio de ese lado ---
    random_point = random.choice(list(corridor_points[random_side]))
    print(f'point = {random_point}')

    # --. Se escogen un ancho y un alto para la habitacion teninedo en cuenta el lado del pasillo en el que estará la
    # habitacion si esta en la parte de abajo del pasillo la altura no puede ser positiva porque se comería el
    # pasillo---
    signed_width = random.choice(dict_side_sign[random_side][0])
    signed_height = random.choice(dict_side_sign[random_side][1])

    random_width = signed_width * (random.uniform(2.5, 5))
    random_height = signed_height * (random.uniform(2.5, 5))

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
        dict_rooms_per_side[random_side] += 1

    return valid_room


# ----------------------------------------------------------------
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
coppelia.set_object_transform('ResizableFloor_5_25', 0.0, 0.0, -1.0, 0)
coppelia.scale_object('ResizableFloor_5_25', 0.1, 0.1, 0.1)
coppelia.set_object_position('DefaultCamera', 0, 0, 25.)
coppelia.set_object_orientation('DefaultCamera', 3.14, 0, 3.14)

# Se seleccionan el numero de habitaicones que va a haber
num_rooms = random.randint(1, 5)

print(f'Creating {num_rooms} rooms')

min_width_room = 2.5
max_width_room = 5

# Crear pasillo initial
corridor_width = random.uniform(num_rooms * min_width_room / 2, num_rooms * max_width_room / 2)
corridor_height = random.uniform(1.5, 3)

print(F'Creating corridor with width = {corridor_width} and height = {corridor_height}')

if random.choice(['vertical', 'horizontal']) == 'horizontal':
    orientation = 'horizontal'
    initial_corridor = QRectF(0, 0, corridor_width, corridor_height)
    initial_corridor_interior = QRectF(0, 0, corridor_width - 0.1,
                                       corridor_height - 0.1)  # auxiliar para que las habitaciones se unan al pasillo
else:
    orientation = 'vertical'
    initial_corridor = QRectF(0, 0, corridor_height, corridor_width)
    initial_corridor_interior = QRectF(0, 0, corridor_height - 0.1, corridor_width - 0.1)

print(f'Corridor orientation is {orientation}')

initial_corridor.translate(-initial_corridor.center())  # Traslado el pasillo al centro
initial_corridor_interior.translate(-initial_corridor_interior.center())  # Traslado el pasillo auxiliar al centro

print('Initial corridor --- ',
      f'Center = {initial_corridor.center()}\n',
      f'Top Left = {initial_corridor.topLeft()}\n',
      f'Top Right = {initial_corridor.topRight()}\n'
      f'Bottom Left = {initial_corridor.bottomLeft()}\n',
      f'Bottom Right = {initial_corridor.bottomRight()}\n')

initial_polygon = QPolygonF(initial_corridor)

corridor_points = {
    'bottom': [],
    'right': [],
    'top': [],
    'left': []
}

corridor_sides = {  # bottom y top deben estar cambiados
    'bottom': [initial_corridor_interior.topLeft(), initial_corridor_interior.topRight()],
    'right': [initial_corridor_interior.topRight(), initial_corridor_interior.bottomRight()],
    'top': [initial_corridor_interior.bottomLeft(), initial_corridor_interior.bottomRight()],
    'left': [initial_corridor_interior.bottomLeft(), initial_corridor_interior.topLeft()]
}

# -------- Recorro el pasillo inicial buscando puntos a lo largo de su perimetro -----------
for side, points in corridor_sides.items():
    line = QLineF(points[0], points[1])
    line_lenght = int(line.length())

    step = line_lenght / 100.

    for t in np.arange(0.20, 0.80, step):  # intento evitar las esquinas empezando en 0.2 y acabando en 0.8
        line_point = line.pointAt(t)
        corridor_points[side].append(QPointF(line_point.x(), line_point.y()))

max_rooms_per_side = math.ceil(num_rooms / 2)

# Dividir la lista de puntos en secciones dependiendo del numero de habitaciones para escoger puntos de esa seccion --- Darle una vuelta

# for side, list_points in corridor_points.items():
#     corridor_points[side] = [list_points[i::max_rooms_per_side] for i in np.arange(max_rooms_per_side)]
#     print(f'tamaño despues de dividir = {len(corridor_points[side])}')
#
# exit(-1)
# -------------- Crear habitaciones aleatorias ---------------

result_polygon = initial_polygon

random_qrect_list = []

for i in range(0, num_rooms):
    print(f'------------ i - {i} ------------')

    valid = False
    count = 0

    while not valid:
        if count > 200:
            break
        else:
            valid = get_random_room()
            count += 1

    if count > 200:
        print(f'room {i} is not valid')
        continue

    print('---------------')

# --- Añadir habitaciones al pasillo ----
print(f'----- {len(random_qrect_list)} have been created -----')

# for room in random_qrect_list:
#     polygon = QPolygonF(room, closed=True)
#     for point in polygon:
#         result_polygon.append(point)


for room in random_qrect_list:
    print(f'qrect {room.topLeft(), room.topRight(), room.bottomRight(), room.bottomLeft()}')
    polygon = QPolygonF(room, closed=True)
    print(f'qpolygon {polygon}')

    result_polygon = result_polygon.united(polygon)

# -------------- Dibujar paredes----------------

# Bounding rect para centrar
boundingRect = result_polygon.boundingRect()
center = boundingRect.center()
result_polygon.translate(-center)
boundingRect = result_polygon.boundingRect()

prev_point = result_polygon[0]

for i, curr_point in enumerate(result_polygon):
    if i == 0:
        continue

    coppelia.create_wall([prev_point.x(), prev_point.y(), 0], [curr_point.x(), curr_point.y(), 0])
    prev_point = curr_point

fscale_x = boundingRect.width() / 5 + 0.25
fscale_y = boundingRect.height() / 5 + 0.25

# Create and scale a floor
r = coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm', 0, 0, 0, 0)

coppelia.scale_object(r, fscale_x, fscale_y, 1)
for handle in coppelia.get_objects_children(r):
    coppelia.scale_object(handle, fscale_x, fscale_y, 1)
