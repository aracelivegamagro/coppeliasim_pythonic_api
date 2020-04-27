import math
import random

import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

from coppeliasimapi import CoppeliaSimAPI


class Room:

    # posibles signos del width, height en funcion del lado del pasillo en el que estén

    def __init__(self, random_side, add_corridor, dict_rooms_per_side, initial_corridor, fixed_height):

        self.type = 'genericRoom'  # En un futuro será corridor, bedroom, kitchen, bathroom, etc

        print(f'el tamaño fijado es de {fixed_height}')

        new_corridor_width = initial_corridor.height()

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
        dict_side_sign = {'bottom': [1, -1], 'right': [1, 1], 'top': [1, 1], 'left': [-1, 1]}

        signed_width = dict_side_sign[random_side][0]
        signed_height = dict_side_sign[random_side][1]

        random_width = signed_width * (random.uniform(3, 6))
        random_height = signed_height * fixed_height

        print(f'Creating room with width = {random_width} and height = {random_height}')

        # --- Se crea un rectangulo con el ancho y alto seleccionado
        self.room_qrect = QRectF(random_point.x(), random_point.y(), random_width, random_height)



class Apartment:

    def __init__(self, n_rooms, asymmetric_rooms=False):
        self.num_rooms = n_rooms
        self.max_rooms_per_side = math.ceil(self.num_rooms / 2)

        # Variables auxiliares
        # -1 sin pasillo, 0 antes de la primera habitacion, 1 antes de la segunda
        self.dict_corridors_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_rooms_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_opposite_side = {'bottom': 'top', 'right': 'left', 'top': 'bottom', 'left': 'right'}

        self.create_initial_corridor()
        self.select_side_corridors()

        self.fixed_height = random.uniform(4, 6)
        self.random_qrect_room_list = []
        self.get_rooms()
        self.adjust_rooms()  # to avoid narrow corridors

        if asymmetric_rooms:
            self.change_room_heights()

        self.result_polygon_rooms_list = []
        self.add_doors()
        self.add_floor()
        self.add_walls()

    def create_initial_corridor(self):

        self.initial_corridor_height = random.uniform(1.5, 3)
        self.initial_corridor_width = random.uniform(self.num_rooms * 4 / 2, self.num_rooms * 8 / 2)
        print(
            F'Creating corridor with width = {self.initial_corridor_width} and height = {self.initial_corridor_height}')

        self.initial_corridor = QRectF(0, 0, self.initial_corridor_width, self.initial_corridor_height)
        self.initial_corridor.translate(-self.initial_corridor.center())  # Traslado el pasillo al centro

        print('Initial corridor --- ',
              f'Center = {self.initial_corridor.center()}\n',
              f'Top Left = {self.initial_corridor.topLeft()}\n',
              f'Top Right = {self.initial_corridor.topRight()}\n'
              f'Bottom Left = {self.initial_corridor.bottomLeft()}\n',
              f'Bottom Right = {self.initial_corridor.bottomRight()}\n')

        self.corridor_sides = {  # bottom y top deben estar cambiados
            'bottom': [self.initial_corridor.topLeft(), self.initial_corridor.topRight()],
            'right': [self.initial_corridor.topRight(), self.initial_corridor.bottomRight()],
            'top': [self.initial_corridor.bottomLeft(), self.initial_corridor.bottomRight()],
            'left': [self.initial_corridor.topLeft(), self.initial_corridor.bottomLeft()]
        }

    def select_side_corridors(self):

        corridor_position = np.arange(-1, self.max_rooms_per_side)
        print(corridor_position)

        possibles_corridors_per_side = round(self.max_rooms_per_side / 2)
        if possibles_corridors_per_side == 0:
            possibles_corridors_per_side = 1

        print(f'k {possibles_corridors_per_side}')

        self.dict_corridors_per_side['top'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)
        self.dict_corridors_per_side['bottom'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)

        # Si los dos lados tienen ambos pasillos a la derecha o a la izquierda el boundingbox lo va a eliminar -Se intenta evitar
        # REVISAR

        if 0 in self.dict_corridors_per_side['top'] and 0 in self.dict_corridors_per_side['bottom']:
            delete_corridor_from = random.choice(['top', 'bottom'])
            self.dict_corridors_per_side[delete_corridor_from].remove(0)

        if (self.max_rooms_per_side - 1) in self.dict_corridors_per_side['top'] and (self.max_rooms_per_side - 1) in \
                self.dict_corridors_per_side[
                    'bottom']:
            delete_corridor_from = random.choice(['top', 'bottom'])
            self.dict_corridors_per_side[delete_corridor_from].remove(self.max_rooms_per_side - 1)

        print('posicion pasillo parte superior', self.dict_corridors_per_side['top'])
        print('posicion pasillo parte inferior', self.dict_corridors_per_side['bottom'])

    def get_rooms(self):
        for i in range(0, self.num_rooms):

            random_side = random.choice(['top', 'bottom'])

            if len(self.dict_rooms_per_side[random_side]) >= self.max_rooms_per_side:
                print(f'side {random_side} has already the maximum of rooms')
                random_side = self.dict_opposite_side[random_side]

            print(f'side chosed = {random_side}')

            corridor_locations = self.dict_corridors_per_side[random_side]

            if len(self.dict_rooms_per_side[random_side]) in corridor_locations:
                add_corridor = True
            else:
                add_corridor = False

            room = Room(random_side, add_corridor, self.dict_rooms_per_side, self.initial_corridor, self.fixed_height)

            obtained_room = room.room_qrect

            self.random_qrect_room_list.append(obtained_room)  # Revisar si hace falta esta variable
            self.dict_rooms_per_side[random_side].append(obtained_room)

        print(f'{len(self.random_qrect_room_list)} rooms have been created')

    def adjust_rooms(self):

        if len(self.random_qrect_room_list) > 1:

            dict_side_width = {'bottom': 0., 'right': 0., 'top': 0., 'left': 0.}

            for side, rooms_list in self.dict_rooms_per_side.items():
                print(f' side {side} has {len(rooms_list)} rooms ')
                for r in rooms_list:
                    dict_side_width[side] += r.width()

            for side, corridor_w in self.dict_corridors_per_side.items():
                print(f'side {side} has {len(corridor_w)} corridors')
                for w in corridor_w:
                    if w != -1:
                        dict_side_width[side] += self.initial_corridor_height

            UpperRight = self.dict_rooms_per_side['top'][-1].topRight()
            bottomRight = self.dict_rooms_per_side['bottom'][-1].topRight()

            diff = abs(dict_side_width['top'] - dict_side_width['bottom'])

            # Si la diferencia es muy pequeña ajusto el ancho, si es demasiado grande añado un pasillo
            # Si ensanchamos la habitacion eliminamos el siguiente pasillo si lo hubiese
            if diff < self.initial_corridor_height - 1.:
                print('Modifying corridor --- widening room')

                if dict_side_width['top'] > dict_side_width['bottom']:

                    self.dict_rooms_per_side['bottom'][-1].setTopRight(QPointF(UpperRight.x(), bottomRight.y()))
                    corridor_to_remove = len(self.dict_rooms_per_side['bottom'])
                    if corridor_to_remove in self.dict_corridors_per_side['bottom']:
                        self.dict_corridors_per_side['bottom'].remove(corridor_to_remove)

                else:
                    self.dict_rooms_per_side['top'][-1].setTopRight(QPointF(bottomRight.x(), UpperRight.y()))
                    corridor_to_remove = len(self.dict_rooms_per_side['top'])
                    if corridor_to_remove in self.dict_corridors_per_side['top']:
                        self.dict_corridors_per_side['top'].remove(corridor_to_remove)

            # Si añadimos un pasillo a la derecha lo añadimos a la lista de pasillos si no estuviese
            elif diff > self.initial_corridor_height:
                print('Modifying corridor --- creating corridor ')

                if dict_side_width['top'] > dict_side_width['bottom']:
                    self.dict_rooms_per_side['bottom'][-1].setTopRight(
                        QPointF(UpperRight.x() - self.initial_corridor_height, bottomRight.y()))
                    new_corridor_location = len(self.dict_rooms_per_side['bottom'])
                    if new_corridor_location not in self.dict_corridors_per_side['bottom']:
                        self.dict_corridors_per_side['bottom'].append(new_corridor_location)

                else:
                    self.dict_rooms_per_side['top'][-1].setTopRight(
                        QPointF(bottomRight.x() - self.initial_corridor_height, UpperRight.y()))
                    new_corridor_location = len(self.dict_rooms_per_side['top'])
                    if new_corridor_location not in self.dict_corridors_per_side['top']:
                        self.dict_corridors_per_side['top'].append(new_corridor_location)
            else:
                print('Not modifying last corridor')

    def change_room_heights(self):

        for side, rooms_list in self.dict_rooms_per_side.items():
            for i, room in enumerate(rooms_list):
                # Cambio el ancho de la habitación de forma aleatoria (para no quedarme sin pasillo como maximo la muevo un tercio de este)
                random_sign = [1, -1]
                random_mov = list(np.arange(0, self.initial_corridor_height / 3, 0.05))
                room.setTopLeft(QPointF(room.topLeft().x(),
                                        room.topLeft().y() + random.choice(random_sign) * random.choice(random_mov)))

    def add_doors(self):

        self.union_polygon = QPolygonF()

        for current_side, rooms_list in self.dict_rooms_per_side.items():

            for i, room in enumerate(rooms_list):

                possibles_door_locations = ['center']
                if i in self.dict_corridors_per_side[current_side]:  # Pasillo a la izquierda
                    possibles_door_locations.append('left')

                if i + 1 in self.dict_corridors_per_side[current_side]:
                    possibles_door_locations.append('right')

                door_location = random.choice(possibles_door_locations)

                room_polygon_with_door = self.get_room_polygon_with_door(room, door_location, current_side)

                # --- Añadir habitaciones al pasillo ----
                self.result_polygon_rooms_list.append(room_polygon_with_door)
                self.union_polygon = self.union_polygon.united(room_polygon_with_door)  # Para obtener el bounding box


    def get_room_polygon_with_door(self, room_, door_location, current_side):

        if door_location == 'center':
            line = QLineF(room_.topLeft(), room_.topRight())

        elif door_location == 'left':
            line = QLineF(room_.topLeft(), room_.bottomLeft())

        elif door_location == 'right':
            line = QLineF(room_.topRight(), room_.bottomRight())

        line_lenght = int(line.length())
        step = line_lenght / 100.

        line_points = []
        for t in np.arange(0.25, 0.75, step):
            line_point = line.pointAt(t)
            line_points.append(QPointF(line_point.x(), line_point.y()))

        random_center_door = random.choice(line_points)

        if door_location == 'center':
            left_door = QPointF(random_center_door.x() - 0.5, random_center_door.y())
            right_door = QPointF(random_center_door.x() + 0.5, random_center_door.y())

            room_polygon = QPolygonF(
                [right_door, room_.topRight(), room_.bottomRight(), room_.bottomLeft(), room_.topLeft(), left_door])

        elif door_location == 'left':

            left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
            right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

            if current_side == 'bottom':
                room_polygon = QPolygonF(
                    [right_door, room_.topLeft(), room_.topRight(), room_.bottomRight(), room_.bottomLeft(), left_door])

            elif current_side == 'top':
                room_polygon = QPolygonF(
                    [right_door, room_.bottomLeft(), room_.bottomRight(), room_.topRight(), room_.topLeft(), left_door])

        elif door_location == 'right':

            left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
            right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

            if current_side == 'bottom':
                room_polygon = QPolygonF(
                    [right_door, room_.topRight(), room_.topLeft(), room_.bottomLeft(), room_.bottomRight(), left_door])

            elif current_side == 'top':
                room_polygon = QPolygonF(
                    [right_door, room_.bottomRight(), room_.bottomLeft(), room_.topLeft(), room_.topRight(), left_door])

        return room_polygon

    def add_floor(self):

        self.boundingRect = self.union_polygon.boundingRect()

        if len(self.result_polygon_rooms_list) > 1:
            self.result_polygon_rooms_list.append(QPolygonF(self.boundingRect, closed=True))

        fscale_x = self.boundingRect.width() / 5 + 0.5
        fscale_y = self.boundingRect.height() / 5 + 0.5

        # Create and scale a floor
        r = coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm', 0, 0, 0, 0)

        coppelia.scale_object(r, fscale_x, fscale_y, 1)
        for handle in coppelia.get_objects_children(r):
            coppelia.scale_object(handle, fscale_x, fscale_y, 1)

    def add_walls(self):

        for polygon in self.result_polygon_rooms_list:
            center = self.boundingRect.center()

            polygon.translate(-center)  # Desplazo los poligonos para que la habitación esté centrada

            prev_point = polygon[0]

            for i, curr_point in enumerate(polygon):
                if i == 0:
                    continue

                coppelia.create_wall([prev_point.x(), prev_point.y(), 0], [curr_point.x(), curr_point.y(), 0])
                prev_point = curr_point


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

    apartment = Apartment(n_rooms= 5, asymmetric_rooms=False)
