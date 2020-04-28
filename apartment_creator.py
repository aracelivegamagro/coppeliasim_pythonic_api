import math
import random

import numpy as np
import pygame
import setproctitle
from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

from coppeliasimapi import CoppeliaSimAPI


class Room:
    def __init__(self):
        self.type = 'genericRoom'  # En un futuro será corridor, bedroom, kitchen, bathroom, etc
        self.width = -1
        self.height = -1
        self.corridor_position = None
        self.room_qrect = QRectF()
        self.room_qpolygon = QPolygonF()

    def get_random_room(self, corridor_side, add_corridor, dict_rooms_per_side, initial_corridor, fixed_height):

        self.width = random.uniform(3, 6)
        self.height = fixed_height
        self.corridor_position = corridor_side

        new_corridor_width = initial_corridor.height()

        if len(dict_rooms_per_side[self.corridor_position]) == 0:
            if add_corridor:
                if self.corridor_position == 'bottom':
                    random_point = initial_corridor.topLeft()
                    random_point = QPointF(random_point.x() + new_corridor_width, random_point.y())

                else:
                    random_point = initial_corridor.bottomLeft()
                    random_point = QPointF(random_point.x() + new_corridor_width, random_point.y())

            else:
                if self.corridor_position == 'bottom':
                    random_point = initial_corridor.topLeft()
                else:
                    random_point = initial_corridor.bottomLeft()

        else:
            if add_corridor:
                prev = dict_rooms_per_side[self.corridor_position][-1].room_qrect.topRight()
                random_point = QPointF(prev.x() + new_corridor_width, prev.y())
            else:
                random_point = dict_rooms_per_side[self.corridor_position][-1].room_qrect.topRight()

        print(f'random point = {random_point}')

        # posibles signos del width, height en funcion del lado del pasillo en el que estén
        dict_side_sign = {'bottom': [1, -1], 'right': [1, 1], 'top': [1, 1], 'left': [-1, 1]}

        self.width = dict_side_sign[self.corridor_position][0] * self.width
        self.height = dict_side_sign[self.corridor_position][1] * self.height

        print(f'Creating room with width = {self.width} and height = {self.height}')

        self.room_qrect = QRectF(random_point.x(), random_point.y(), self.width, self.height)

    def update_room_dimensions(self):
        self.width = self.room_qrect.width()
        self.height = self.room_qrect.height()

    def get_room_polygon_with_door(self, door_location):
        
        if door_location == 'center':
            line = QLineF(self.room_qrect.topLeft(), self.room_qrect.topRight())

        elif door_location == 'left':
            line = QLineF(self.room_qrect.topLeft(), self.room_qrect.bottomLeft())

        elif door_location == 'right':
            line = QLineF(self.room_qrect.topRight(), self.room_qrect.bottomRight())

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

            self.room_qpolygon = QPolygonF(
                [right_door, self.room_qrect.topRight(), self.room_qrect.bottomRight(), self.room_qrect.bottomLeft(),
                 self.room_qrect.topLeft(), left_door])

        elif door_location == 'left':

            left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
            right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

            if self.corridor_position == 'bottom':
                self.room_qpolygon = QPolygonF(
                    [right_door, self.room_qrect.topLeft(), self.room_qrect.topRight(), self.room_qrect.bottomRight(),
                     self.room_qrect.bottomLeft(), left_door])

            elif self.corridor_position == 'top':
                self.room_qpolygon = QPolygonF(
                    [right_door, self.room_qrect.bottomLeft(), self.room_qrect.bottomRight(),
                     self.room_qrect.topRight(), self.room_qrect.topLeft(), left_door])

        elif door_location == 'right':

            left_door = QPointF(random_center_door.x(), random_center_door.y() - 0.5)
            right_door = QPointF(random_center_door.x(), random_center_door.y() + 0.5)

            if self.corridor_position == 'bottom':
                self.room_qpolygon = QPolygonF(
                    [right_door, self.room_qrect.topRight(), self.room_qrect.topLeft(), self.room_qrect.bottomLeft(),
                     self.room_qrect.bottomRight(), left_door])

            elif self.corridor_position == 'top':
                self.room_qpolygon = QPolygonF(
                    [right_door, self.room_qrect.bottomRight(), self.room_qrect.bottomLeft(), self.room_qrect.topLeft(),
                     self.room_qrect.topRight(), left_door])


class Apartment:

    def __init__(self, n_rooms, asymmetric_rooms=False):

        self.num_rooms = n_rooms
        self.max_rooms_per_side = math.ceil(self.num_rooms / 2)
        self.rooms_list = []  # List of objects Room

        self.initial_corridor_width = -1
        self.initial_corridor_height = -1
        self.initial_corridor = QRectF()
        self.corridor_sides = {}

        # self.result_polygon_rooms_list = []

        self.fixed_height = random.uniform(4, 6)

        # -1 sin pasillo, 0 antes de la primera habitacion, 1 antes de la segunda
        self.dict_corridors_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_rooms_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_opposite_side = {'bottom': 'top', 'right': 'left', 'top': 'bottom', 'left': 'right'}

        self.create_initial_corridor()
        self.select_side_corridors()

        self.get_rooms()
        self.adjust_rooms()  # to avoid narrow corridors

        if asymmetric_rooms:
            self.change_room_heights()

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

        self.dict_corridors_per_side['top'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)
        self.dict_corridors_per_side['bottom'] = random.sample(list(corridor_position), k=possibles_corridors_per_side)

        if -1 in self.dict_corridors_per_side['top']:
            self.dict_corridors_per_side['top'].remove(-1)

        if -1 in self.dict_corridors_per_side['bottom']:
            self.dict_corridors_per_side['bottom'].remove(-1)

        # Si los dos lados tienen ambos pasillos a la derecha o a la izquierda el boundingbox lo va a eliminar -Se intenta evitar
        # REVISAR -- si añado los pasillos como poligonos esto no seria necesario

        if 0 in self.dict_corridors_per_side['top'] and 0 in self.dict_corridors_per_side['bottom']:
            delete_corridor_from = random.choice(['top', 'bottom'])
            self.dict_corridors_per_side[delete_corridor_from].remove(0)

        if (self.max_rooms_per_side - 1) in self.dict_corridors_per_side['top'] and (self.max_rooms_per_side - 1) in \
                self.dict_corridors_per_side[
                    'bottom']:
            delete_corridor_from = random.choice(['top', 'bottom'])
            self.dict_corridors_per_side[delete_corridor_from].remove(self.max_rooms_per_side - 1)

        # --------------------------------------------------------------------------------------------
        print('posicion pasillo parte superior', self.dict_corridors_per_side['top'])
        print('posicion pasillo parte inferior', self.dict_corridors_per_side['bottom'])

    def get_rooms(self):
        for i in range(0, self.num_rooms):

            random_side = random.choice(['top', 'bottom'])

            if len(self.dict_rooms_per_side[random_side]) >= self.max_rooms_per_side:
                random_side = self.dict_opposite_side[random_side]

            print(f'side chosed = {random_side}')

            # si el indice de la habitacion esta en la lista de pasillos se añade un pasillo a la izquierda
            if len(self.dict_rooms_per_side[random_side]) in self.dict_corridors_per_side[random_side]:
                add_corridor = True
            else:
                add_corridor = False

            room = Room()
            room.get_random_room(random_side, add_corridor, self.dict_rooms_per_side, self.initial_corridor,
                                 self.fixed_height)

            self.rooms_list.append(room)

            # obtained_room = room.room_qrect
            # self.random_qrect_room_list.append(obtained_room)  # Revisar si hace falta esta variable

            self.dict_rooms_per_side[random_side].append(room)

        print(f'{len(self.rooms_list)} rooms have been created')

    def adjust_rooms(self):
        if len(self.rooms_list) > 1:
            dict_side_width = {'bottom': 0., 'right': 0., 'top': 0., 'left': 0.}

            for side, rooms_list in self.dict_rooms_per_side.items():
                print(f' side {side} has {len(rooms_list)} rooms ')
                for room in rooms_list:
                    r = room.room_qrect
                    dict_side_width[side] += r.width()

            for side, corridor_w in self.dict_corridors_per_side.items():
                print(f'side {side} has {len(corridor_w)} corridors')
                dict_side_width[side] += self.initial_corridor_height * len(corridor_w)

            room_upper = self.dict_rooms_per_side['top'][-1]
            room_bottom = self.dict_rooms_per_side['bottom'][-1]

            upper_right = room_upper.room_qrect.topRight()
            bottom_right = room_bottom.room_qrect.topRight()

            diff = abs(dict_side_width['top'] - dict_side_width['bottom'])

            # Si la diferencia es muy pequeña ajusto el ancho, si es demasiado grande añado un pasillo
            # Si ensanchamos la habitacion eliminamos el siguiente pasillo si lo hubiese
            if diff < self.initial_corridor_height - 1.:
                print('Modifying corridor --- widening room')

                if dict_side_width['top'] > dict_side_width['bottom']:

                    room_bottom.room_qrect.setTopRight(QPointF(upper_right.x(), bottom_right.y()))
                    room_bottom.update_room_dimensions()

                    self.dict_rooms_per_side['bottom'][-1] = room_bottom

                    corridor_to_remove = len(self.dict_rooms_per_side['bottom'])
                    if corridor_to_remove in self.dict_corridors_per_side['bottom']:
                        self.dict_corridors_per_side['bottom'].remove(corridor_to_remove)

                else:
                    room_upper.room_qrect.setTopRight(QPointF(bottom_right.x(), upper_right.y()))
                    room_upper.update_room_dimensions()

                    self.dict_rooms_per_side['top'][-1] = room_upper

                    corridor_to_remove = len(self.dict_rooms_per_side['top'])
                    if corridor_to_remove in self.dict_corridors_per_side['top']:
                        self.dict_corridors_per_side['top'].remove(corridor_to_remove)

            # Si añadimos un pasillo a la derecha lo añadimos a la lista de pasillos si no estuviese
            elif diff > self.initial_corridor_height:
                print('Modifying corridor --- creating corridor ')

                if dict_side_width['top'] > dict_side_width['bottom']:

                    room_bottom.room_qrect.setTopRight(
                        QPointF(upper_right.x() - self.initial_corridor_height, bottom_right.y()))
                    room_bottom.update_room_dimensions()

                    self.dict_rooms_per_side['bottom'][-1] = room_bottom

                    new_corridor_location = len(self.dict_rooms_per_side['bottom'])
                    if new_corridor_location not in self.dict_corridors_per_side['bottom']:
                        self.dict_corridors_per_side['bottom'].append(new_corridor_location)

                else:

                    room_upper.room_qrect.setTopRight(
                        QPointF(bottom_right.x() - self.initial_corridor_height, upper_right.y()))
                    room_upper.update_room_dimensions()

                    self.dict_rooms_per_side['top'][-1] = room_upper

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
                room.room_qrect.setTopLeft(QPointF(room.topLeft().x(),
                                                   room.topLeft().y() + random.choice(random_sign) * random.choice(
                                                       random_mov)))
                room.update_room_dimensions()

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

                room.get_room_polygon_with_door(door_location)

                # --- Añadir habitaciones al pasillo ----
                # self.result_polygon_rooms_list.append(room.room_qpolygon)
                self.union_polygon = self.union_polygon.united(room.room_qpolygon)  # Para obtener el bounding box

    def add_floor(self):

        self.boundingRect = self.union_polygon.boundingRect()

        fscale_x = self.boundingRect.width() / 5 + 0.5
        fscale_y = self.boundingRect.height() / 5 + 0.5

        # Create and scale a floor
        r = coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm', 0, 0, 0, 0)

        coppelia.scale_object(r, fscale_x, fscale_y, 1)
        for handle in coppelia.get_objects_children(r):
            coppelia.scale_object(handle, fscale_x, fscale_y, 1)

    def add_walls(self):

        center = self.boundingRect.center()

        for i,room in enumerate(self.rooms_list):
            polygon = room.room_qpolygon
            polygon.translate(-center)  # Desplazo los poligonos para que la habitación esté centrada

            self.rooms_list[i] = polygon

            prev_point = polygon[0]
            for i, curr_point in enumerate(polygon):
                if i == 0:
                    continue

                coppelia.create_wall([prev_point.x(), prev_point.y(), 0], [curr_point.x(), curr_point.y(), 0])
                prev_point = curr_point

        if len(self.rooms_list) > 1:
            polygon_br = QPolygonF(self.boundingRect, closed=True)
            polygon_br.translate(-center)

            prev_point_br = polygon_br[0]
            for i, curr_point_br in enumerate(polygon_br):
                if i == 0:
                    continue

                coppelia.create_wall([prev_point_br.x(), prev_point_br.y(), 0], [curr_point_br.x(), curr_point_br.y(), 0])
                prev_point_br = curr_point_br


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

    apartment = Apartment(n_rooms=random.randint(2,10), asymmetric_rooms=False)
