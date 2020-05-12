from coppeliasimapi import CoppeliaSimAPI
from apartment_creator import *


def furnish_room(room):
    print('___ furnish livingroom ___')

    room_rect = room.room_qrect

    living_models = {'sofa': './models/furniture/chairs/sofa.ttm',
                     'chair': './models/furniture/chairs/dining chair.ttm',
                     'plant': './models/furniture/plants/indoorPlant.ttm',
                     'coffe_table': './models/mymodels/coffe_table.ttm'
                     }

    objects_in_room = []

    collision = True
    count = 0

    n_sofas = 5

    for i in range(n_sofas):
        count = 0
        collision = True
        valid_object = True

        while collision and count <= 50:

            point = get_point_inside_room(room_rect)
            angle = random.uniform(-0, 3.14 * 2)
            sofa = coppelia.create_model(living_models['coffe_table'], point.x(), point.y(), 0.425, angle)
            # coppelia.set_object_orientation(sofa, -1.57, -1.57 + angle, -1.57)

            coppelia.set_collidable(sofa)

            if len(objects_in_room) == 0:
                collision = False
                valid_object = True

            for obj in objects_in_room:

                if coppelia.check_collision(sofa, obj):
                    print('Hay colisión - se elimina el objeto')
                    coppelia.remove_object(sofa)
                    print('objeto eliminado')

                    valid_object = False
                    break
                else:
                    collision = False

            count += 1

        if count >= 50:
            print('cant locate furniture')

        if valid_object:
            print('adding sofa ')
            objects_in_room.append(sofa)


def get_point_inside_room(r):
    margin = 0.5
    return QPointF(random.uniform(r.left() + margin, r.right() - margin),
                   random.uniform(r.bottom() + margin, r.top() - margin))


if '__main__':

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

    num_rooms = 1
    apartment = Apartment(coppelia, n_rooms=num_rooms)

    print('\n ----------------------------------------------------------------------- ')

    for i, room in enumerate(apartment.total_rooms_and_corridors):
        if room.type != 'corridor':
            room.type = 'livingroom'

            furnish_room(room)

    print(' ----------------------------------------------------------------------- ')
