import math
import random
import threading

import numpy as np
from coppeliasimapi import CoppeliaSimAPI

from PySide2.QtCore import QRectF, QPointF, QLineF
from PySide2.QtGui import QPolygonF

data = {
    'walls': [],
    'walls_mutex': threading.Lock(),
}


class WallCreator(threading.Thread):
    def __init__(self, data, wall_data):
        super(WallCreator, self).__init__()
        self.coppelia = CoppeliaSimAPI(['./scenes/'])
        self.data = data
        self.wall_data = wall_data

    def run(self):
        if len(self.wall_data) > 2:
            for wall in self.wall_data:
                wall_object = self.coppelia.create_wall(wall[0], wall[1])
                self.data['walls_mutex'].acquire()
                self.data['walls'].append(wall_object)
                self.data['walls_mutex'].release()

        else:
            wall_object = self.coppelia.create_wall(self.wall_data[0], self.wall_data[1])
            self.data['walls_mutex'].acquire()
            self.data['walls'].append(wall_object)
            self.data['walls_mutex'].release()


class Room:
    def __init__(self, type='genericRoom', p=QPointF(), w=-1, h=-1):
        self.type = type  # corridor, bedroom, kitchen, bathroom, etc
        self.width = w
        self.height = h
        self.initial_point = p
        self.room_qrect = QRectF()
        self.room_qpolygon = QPolygonF()
        self.area = -1
        self.side = None
        self.door_loc = -1  # 0 entre topL y topR, 1 entre topR y bottomR, 2 entre bottomR y bottomL y 3 entr bL y tL

        self.create_room()

    def create_room(self):
        print(f'Creating room of type {self.type} with width = {self.width} and height = {self.height}')
        self.room_qrect = QRectF(self.initial_point.x(), self.initial_point.y(), self.width, self.height)
        self.room_qpolygon = QPolygonF(self.room_qrect)
        self.area = abs(self.width * self.height)

    def update_room_dimensions(self):
        self.width = self.room_qrect.width()
        self.height = self.room_qrect.height()
        self.area = abs(self.width * self.height)
        self.room_qpolygon = QPolygonF(self.room_qrect)

    def add_door(self, door_location, room_side):

        self.side = room_side

        dict_location_line = {'center': QLineF(self.room_qrect.topLeft(), self.room_qrect.topRight()),
                              'left': QLineF(self.room_qrect.topLeft(), self.room_qrect.bottomLeft()),
                              'right': QLineF(self.room_qrect.topRight(), self.room_qrect.bottomRight())}

        line = dict_location_line[door_location]
        line_lenght = int(line.length())
        step = line_lenght / 100.

        line_points = []
        for t in np.arange(0.25, 0.75, step):
            line_point = line.pointAt(t)
            line_points.append(QPointF(line_point.x(), line_point.y()))

        random_center_door = random.choice(line_points)

        door_sides = {
            'center': {'left_door': QPointF(random_center_door.x() - 0.5, random_center_door.y()),
                       'right_door': QPointF(random_center_door.x() + 0.5, random_center_door.y())},
            'left': {'left_door': QPointF(random_center_door.x(), random_center_door.y() - 0.5),
                     'right_door': QPointF(random_center_door.x(), random_center_door.y() + 0.5)},
            'right': {'left_door': QPointF(random_center_door.x(), random_center_door.y() - 0.5),
                      'right_door': QPointF(random_center_door.x(), random_center_door.y() + 0.5)}
        }

        if door_location == 'center':
            self.room_qpolygon = QPolygonF(
                [door_sides[door_location]['right_door'], self.room_qrect.topRight(), self.room_qrect.bottomRight(),
                 self.room_qrect.bottomLeft(), self.room_qrect.topLeft(), door_sides[door_location]['left_door']])

            self.door_loc = 0

        elif door_location == 'right':

            if room_side == 'bottom':
                self.room_qpolygon = QPolygonF(
                    [door_sides[door_location]['right_door'], self.room_qrect.topRight(), self.room_qrect.topLeft(),
                     self.room_qrect.bottomLeft(), self.room_qrect.bottomRight(),
                     door_sides[door_location]['left_door']])

            elif room_side == 'top':
                self.room_qpolygon = QPolygonF(
                    [door_sides[door_location]['right_door'], self.room_qrect.bottomRight(),
                     self.room_qrect.bottomLeft(),
                     self.room_qrect.topLeft(), self.room_qrect.topRight(), door_sides[door_location]['left_door']])

            self.door_loc = 1

        elif door_location == 'left':
            if room_side == 'bottom':
                self.room_qpolygon = QPolygonF(
                    [door_sides[door_location]['right_door'], self.room_qrect.topLeft(), self.room_qrect.topRight(),
                     self.room_qrect.bottomRight(), self.room_qrect.bottomLeft(),
                     door_sides[door_location]['left_door']])


            elif room_side == 'top':
                self.room_qpolygon = QPolygonF(
                    [door_sides[door_location]['right_door'], self.room_qrect.bottomLeft(),
                     self.room_qrect.bottomRight(),
                     self.room_qrect.topRight(), self.room_qrect.topLeft(), door_sides[door_location]['left_door']])

            self.door_loc = 3


class Apartment:

    def __init__(self, coppelia_, n_rooms):

        self.coppelia = coppelia_

        self.num_rooms = n_rooms
        self.max_rooms_per_side = math.ceil(self.num_rooms / 2)

        self.initial_corridor_width = -1
        self.initial_corridor_height = -1

        self.initial_corridor = QRectF()
        self.initial_corridor_sides = {}

        self.fixed_height = random.uniform(4, 6)

        # Almacena los indices de las habitaciones que tendrán a su izquierda un pasillo
        self.dict_corridors_index_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_rooms_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}
        self.dict_rooms_and_corridors_per_side = {'bottom': [], 'right': [], 'top': [], 'left': []}

        # Lista final una vez hechas todas las transformaciones
        self.total_rooms_and_corridors = []

        self.create_initial_corridor()
        self.select_side_corridors()
        self.get_random_rooms()
        self.adjust_rooms()  # to avoid narrow corridors

        self.add_doors()
        self.center_apartment()
        self.add_floor_per_room()
        self.add_walls()

    def create_initial_corridor(self):
        self.initial_corridor_height = random.uniform(1.5, 3)
        self.initial_corridor_width = random.uniform(self.num_rooms * 4 / 2, self.num_rooms * 8 / 2)

        self.initial_corridor = QRectF(0, 0, self.initial_corridor_width, self.initial_corridor_height)
        self.initial_corridor.translate(-self.initial_corridor.center())

        self.initial_corridor_sides = {  # bottom y top deben estar cambiados
            'bottom': [self.initial_corridor.topLeft(), self.initial_corridor.topRight()],
            'right': [self.initial_corridor.topRight(), self.initial_corridor.bottomRight()],
            'top': [self.initial_corridor.bottomLeft(), self.initial_corridor.bottomRight()],
            'left': [self.initial_corridor.topLeft(), self.initial_corridor.bottomLeft()]
        }

    def select_side_corridors(self):
        # -1 sin pasillo, 0 antes de la primera habitacion, 1 antes de la segunda
        corridor_position = np.arange(-1, self.max_rooms_per_side)

        possibles_corridors_per_side = round(self.max_rooms_per_side / 2)

        if possibles_corridors_per_side == 0:
            possibles_corridors_per_side = 1

        self.dict_corridors_index_per_side['top'] = random.sample(list(corridor_position),
                                                                  k=possibles_corridors_per_side)
        self.dict_corridors_index_per_side['bottom'] = random.sample(list(corridor_position),
                                                                     k=possibles_corridors_per_side)

        while -1 in self.dict_corridors_index_per_side['top']:
            self.dict_corridors_index_per_side['top'].remove(-1)

        while -1 in self.dict_corridors_index_per_side['bottom']:
            self.dict_corridors_index_per_side['bottom'].remove(-1)

        print('posicion pasillo parte superior', self.dict_corridors_index_per_side['top'])
        print('posicion pasillo parte inferior', self.dict_corridors_index_per_side['bottom'])

    def get_random_rooms(self):

        dict_opposite_side = {'bottom': 'top', 'right': 'left', 'top': 'bottom', 'left': 'right'}

        for i in range(0, self.num_rooms):

            random_side = random.choice(['top', 'bottom'])

            if len(self.dict_rooms_per_side[random_side]) >= self.max_rooms_per_side:
                random_side = dict_opposite_side[random_side]

            # El indice de mi habitacion está en la lista de pasillos por indice luego tengo que añadir un pasillo a
            # su izquierda
            if len(self.dict_rooms_per_side[random_side]) in self.dict_corridors_index_per_side[random_side]:
                # self.add_corridor(random_side, random.uniform(1.5, 3), self.fixed_height)
                self.add_corridor(random_side, self.initial_corridor_height, self.fixed_height)

            if len(self.dict_rooms_and_corridors_per_side[random_side]) == 0:

                if random_side == 'bottom':
                    initial_point = self.initial_corridor.topLeft()
                else:
                    initial_point = self.initial_corridor.bottomLeft()

            else:
                initial_point = self.dict_rooms_and_corridors_per_side[random_side][-1].room_qrect.topRight()

            # posibles signos del width, height en funcion del lado del pasillo en el que estén
            dict_side_sign = {'bottom': [1, -1], 'right': [1, 1], 'top': [1, 1], 'left': [-1, 1]}

            width = dict_side_sign[random_side][0] * random.uniform(3.5, 6)
            height = dict_side_sign[random_side][1] * self.fixed_height

            room = Room(type='genericRoom', p=initial_point, w=width, h=height)

            self.dict_rooms_and_corridors_per_side[random_side].append(room)
            self.dict_rooms_per_side[random_side].append(room)

        for room_location in ['top', 'bottom']:
            if len(self.dict_rooms_per_side[room_location]) in self.dict_corridors_index_per_side[room_location]:
                if self.dict_rooms_and_corridors_per_side[room_location][-1].type != 'corridor':
                    # self.add_corridor(random_side, random.uniform(1.5, 3), self.fixed_height)
                    self.add_corridor(random_side, self.initial_corridor_height, self.fixed_height)

    def add_corridor(self, side, corridor_width, corridor_height):

        if len(self.dict_rooms_and_corridors_per_side[side]) == 0:
            if side == 'bottom':
                corridor_initial_point = self.initial_corridor.topLeft()
            else:
                corridor_initial_point = self.initial_corridor.bottomLeft()

        else:
            corridor_initial_point = self.dict_rooms_and_corridors_per_side[side][-1].room_qrect.topRight()

        if side == 'bottom':
            corridor = Room(type='corridor', p=corridor_initial_point, w=corridor_width,
                            h=-corridor_height)
        else:
            corridor = Room(type='corridor', p=corridor_initial_point, w=corridor_width,
                            h=corridor_height)

        self.dict_rooms_and_corridors_per_side[side].append(corridor)

    def adjust_rooms(self):

        if self.num_rooms == 1:
            return

        dict_side_width = {'bottom': 0., 'right': 0., 'top': 0., 'left': 0.}

        for side, rooms in self.dict_rooms_per_side.items():
            print(f' side {side} has {len(rooms)} rooms ')
            for room in rooms:
                r = room.room_qrect
                dict_side_width[side] += r.width()

        diff = abs(dict_side_width['top'] - dict_side_width['bottom'])

        dict_opposite_side = {'bottom': 'top', 'right': 'left', 'top': 'bottom', 'left': 'right'}

        if dict_side_width['top'] > dict_side_width['bottom']:
            print('top side is longer')
            side_to_modify = 'bottom'
        else:
            print('bottom side is longer')
            side_to_modify = 'top'

        print(f'--- Modifying {side_to_modify} room ---')

        room_to_modify = self.dict_rooms_and_corridors_per_side[side_to_modify][-1]
        opposite_room = self.dict_rooms_and_corridors_per_side[dict_opposite_side[side_to_modify]][-1]

        my_side_right = room_to_modify.room_qrect.topRight()
        opposite_side_right = opposite_room.room_qrect.topRight()

        if room_to_modify.type == 'corridor':
            print(f' Room of type {room_to_modify.type} ')

            room_to_modify.room_qrect.setTopRight(
                QPointF(opposite_side_right.x(), my_side_right.y()))

            self.dict_rooms_and_corridors_per_side[side_to_modify][-1] = room_to_modify
            self.dict_rooms_and_corridors_per_side[side_to_modify][-1].update_room_dimensions()

        else:
            if diff < self.initial_corridor_height:
                print('widening room')
                num_corridors_to_add = 0
            else:
                print('widening room and creating corridor')
                num_corridors_to_add = 1

            print(f' Room of type {room_to_modify.type}  -- adding {num_corridors_to_add} corridors')

            room_to_modify.room_qrect.setTopRight(
                QPointF(opposite_side_right.x() - num_corridors_to_add * self.initial_corridor_height,
                        my_side_right.y()))
            self.dict_rooms_and_corridors_per_side[side_to_modify][-1] = room_to_modify
            self.dict_rooms_and_corridors_per_side[side_to_modify][-1].update_room_dimensions()

            if num_corridors_to_add > 0:
                self.add_corridor(side=side_to_modify,
                                  corridor_width=num_corridors_to_add * self.initial_corridor_height,
                                  corridor_height=self.fixed_height)

    def add_doors(self):
        for current_side, rooms in self.dict_rooms_per_side.items():

            for i, room in enumerate(rooms):

                possibles_door_locations = ['center']
                if i in self.dict_corridors_index_per_side[current_side]:  # Pasillo a la izquierda
                    possibles_door_locations.append('left')

                if i + 1 in self.dict_corridors_index_per_side[current_side]:
                    possibles_door_locations.append('right')

                door_location = random.choice(possibles_door_locations)

                room.add_door(door_location, current_side)

    def center_apartment(self):
        union_polygon = QPolygonF()

        for list in self.dict_rooms_and_corridors_per_side.values():
            for room in list:
                union_polygon = union_polygon.united(room.room_qpolygon)  # Para obtener el bounding box
                self.total_rooms_and_corridors.append(room)

        self.initial_corridor.setLeft(union_polygon.boundingRect().left())
        self.initial_corridor.setRight(union_polygon.boundingRect().right())

        self.total_rooms_and_corridors.append(Room(type='corridor', p=self.initial_corridor.topLeft(),
                                                   w=self.initial_corridor.width(), h=self.initial_corridor.height()))

        union_polygon = union_polygon.united(self.initial_corridor)

        initial_center = union_polygon.boundingRect().center()
        union_polygon.translate(-initial_center)

        self.apartment_boundingRect = union_polygon.boundingRect()

        # Desplazo habitaciones y pasillos al centro
        for i, room in enumerate(self.total_rooms_and_corridors):
            room.room_qpolygon.translate(-initial_center)  # Desplazo los poligonos para que la habitación esté centrada
            room.room_qrect.translate(-initial_center)

    def add_walls(self):

        for i, room in enumerate(self.total_rooms_and_corridors):
            walls = []
            if room.type == 'corridor':
                continue

            polygon = room.room_qpolygon

            prev_point = polygon[0]
            for i, curr_point in enumerate(polygon):
                if i == 0:
                    continue
                walls.append(([prev_point.x(), prev_point.y(), .4], [curr_point.x(), curr_point.y(), .4]))
                prev_point = curr_point

            wall_thread = WallCreator(data, walls)
            wall_thread.start()

        walls = []

        polygon_br = QPolygonF(self.apartment_boundingRect, closed=True)
        prev_point_br = polygon_br[0]
        for i, curr_point_br in enumerate(polygon_br):
            if i == 0:
                continue

            walls.append(([prev_point_br.x(), prev_point_br.y(), .4], [curr_point_br.x(), curr_point_br.y(), .4]))
            prev_point_br = curr_point_br

        wall_thread = WallCreator(data, walls)
        wall_thread.start()

    def add_floor(self):  # un suelo conjunto para el apartamento

        fscale_x = self.apartment_boundingRect.width() / 5 + 0.5
        fscale_y = self.apartment_boundingRect.height() / 5 + 0.5

        # Create and scale a floor
        r = self.coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm', 0, 0, 0, 0)

        self.coppelia.scale_object(r, fscale_x, fscale_y, 1)
        for handle in self.coppelia.get_objects_children(r):
            self.coppelia.scale_object(handle, fscale_x, fscale_y, 1)

    def add_floor_per_room(self):

        for room in self.total_rooms_and_corridors:

            room_boundingRect = room.room_qpolygon.boundingRect()
            room_center = room_boundingRect.center()

            fscale_x = room_boundingRect.width() / 5
            fscale_y = room_boundingRect.height() / 5

            if room.type == 'corridor':
                floor = self.coppelia.create_model('models/infrastructure/floors/5mX5m wooden floor.ttm',
                                                   room_center.x(),
                                                   room_center.y(), -0.1, 0)
            else:
                floor = self.coppelia.create_model('models/infrastructure/floors/5mX5m concrete floor.ttm',
                                                   room_center.x(),
                                                   room_center.y(), 0, 0)

            self.coppelia.scale_object(floor, fscale_x, fscale_y, 1)
