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

    obj_list = []

    parent = coppelia.create_model(living_models['coffe_table'], 0, 0, 0, 0)
    children = coppelia.get_objects_children(parent, children_type='sim.all_type', filter_children=1 + 2)

    for child in children:
        name = coppelia.get_object_name(child)
        print(f' ---- {name} ----')

        if random.randint(0, 1):
            remove_object(name)

        else:
            if random.randint(0, 1):
                rotate_object(name, parent)

            if random.randint(0, 1):
                translate_object(name, obj_list)

            obj_list.append(name)

    if len(obj_list) == 0:
        coppelia.remove_object(parent)

    # trasladar el modelo a una posición aleatoria  y girarla


def remove_object(obj):
    print(f'Removing {obj}')
    coppelia.remove_object(obj)


def rotate_object(obj, parent):
    print(f'Rotating {obj}')

    x, y, z = coppelia.get_object_position(obj)
    px, py, pz = coppelia.get_object_position(parent)

    if x < px:
        sign = -1

    else:
        sign = 1

    alpha, betta, gamma = coppelia.get_object_orientation(obj)

    if 'sofa' in obj:
        new_betta = random.uniform(0, 1.57 * sign)
        print('new angle', new_betta)
        coppelia.set_object_orientation(obj, -1.57, betta + new_betta, -1.57)
        return

    elif 'Table' in obj:
        print('not rotating table')
        return

    new_gamma = random.uniform(- 1.57 / 2, + 1.57 / 2)
    coppelia.set_object_orientation(obj, alpha, betta, new_gamma)
    print('new', alpha, betta, new_gamma)


def translate_object(obj, obj_list):
    x, y, z = coppelia.get_object_position(obj)
    print('old pose ', x, y, z)

    nx = x
    ny = y

    margin = 0.5
    if random.randint(0, 1):
        print(f'Moving x - {obj}')

        nx = x + (random.uniform(0, margin) * random.randint(-1, 1))

    if random.randint(0, 1):
        print(f'Moving y - {obj}')

        ny = y + (random.uniform(0, margin) * random.randint(-1, 1))

    coppelia.set_object_position(obj, nx, ny, z)
    print('new pose ', x, y, z)

    valid_object = check_object_collision(obj, obj_list)

    if not valid_object:
        print('object not valid, trying to move again')
        coppelia.set_object_position(obj, x, y, z)
        translate_object(obj, obj_list)


def check_object_collision(obj, object_list):
    valid_object = True

    for o in object_list:

        if coppelia.check_collision(obj, o):
            valid_object = False
            break

    return valid_object


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

    print('\n ----------------------------------------------------------------------- ')

    num_rooms = 1
    apartment = Apartment(coppelia, n_rooms=num_rooms)

    print('\n ----------------------------------------------------------------------- ')

    for i, room in enumerate(apartment.total_rooms_and_corridors):
        if room.type != 'corridor':
            furnish_room(room)

    print(' ----------------------------------------------------------------------- ')
