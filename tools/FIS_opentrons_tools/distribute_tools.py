def calc_solution(final_vol, factor, preload_dil = 0):
    sol = final_vol/factor
    dil = final_vol - sol - preload_dil
    print("Giving back tuple of volumes: (solute , solvent)")
    return (sol, dil)

def is_integer_num(n):
    if isinstance(n, int):
        return True
    if isinstance(n, float):
        return n.is_integer()
    return False

def split_list(x, n):
    #Obtained from: https://stackoverflow.com/questions/9671224/split-a-python-list-into-other-sublists-i-e-smaller-lists
    return [x[idx:idx+n] for idx in range(0, len(x), n)]

def src_dest_relation(lbw_1_settings, lbw_2_settings, lbw1_count_key, lbw_2_count_key, only_int = True):
    '''
    calculate source and destiny relation
    '''
    relation = lbw_1_settings[lbw1_count_key]/lbw_2_settings[lbw_2_count_key]
    if only_int and not is_integer_num(relation):
        print("Relation between source and dest must be integer")
        print('change only_int arg for change this behaviour')
        return None
    elif relation <1:
        print(f'Relation: 1 labware 1 -> {str(1/relation)} labware 2')
        return 1/relation
    else:
        print(f"Relation: {str(relation)} labware 1 -> 1 labware 2")
        return relation #Hay que rediseñar esto para contemplar src/dest de 0.5, 0.25...

def src_dest_slot_orders(src_lbw_settings, dest_lbw_settings, relation, slots_key): #La relación es src/dest
    '''
    Devuelte un objeto zip para el que cada tupla es la relación de slots entre fuente y destino
    '''
    if relation > 1:
        src_iter = relation
        dest_iter = 1
    elif relation < 1:
        src_iter = 1
        dest_iter = 1/relation
    elif relation == 1:
        src_iter = dest_iter = 1
    else:
        print('relation must be positive')
        return None
    
    src_split = split_list(src_lbw_settings[slots_key], src_iter)
    dest_split = split_list(dest_lbw_settings[slots_key], dest_iter)

    if len(src_split) != len(dest_split):
        print('Relation between source and destination must be integer!')
        return None
    else:
        slot_orders = [element for element in zip(src_split, dest_split)]
        return slot_orders

def src_dest_dimensions(src_lbw, dest_lbw, get_relation = True, src_key = 'src', dest_key='dest', rel_key = 'relation'):

    dim_dict = {
        src_key: [len(src_lbw.rows()), len(src_lbw.columns())],
        dest_key :[len(dest_lbw.rows()), len(dest_lbw.columns())]
    }

    if get_relation:
        dim_dict[rel_key] = [dim_dict[src_key][idx]/dim_dict[dest_key][idx] for idx in range(0,2)]

    return dim_dict

def get_wells_pos(labware_dims, by_row = True):
    wells = labware_dims[0]*labware_dims[1]
    wells_pos = {}
    row_idx = 0
    col_idx = 0
    for well in range(wells):
        wells_pos[well]= (row_idx, col_idx)
        if by_row:
            row_idx, col_idx = increase_idx(row_idx, col_idx, labware_dims[0])
        else:
            col_idx, row_idx = increase_idx(col_idx, row_idx, labware_dims[1])
    return wells_pos

def increase_idx(idx, second_idx, lap):
    idx += 1
    if idx >= lap:
        second_idx += 1
        idx = 0
    return (idx, second_idx)

def get_wells_pos(labware_dims, by_row = True):
    '''
    Crea  un diccionario de celdas con sus coordenadas según las dimensiones
    '''
    wells = labware_dims[0]*labware_dims[1]
    wells_pos = {}
    row_idx = 0
    col_idx = 0
    for well in range(wells):
        wells_pos[well]= (row_idx, col_idx)
        if by_row:
            row_idx, col_idx = increase_idx(row_idx, col_idx, labware_dims[0])
        else:
            col_idx, row_idx = increase_idx(col_idx, row_idx, labware_dims[1])
    return wells_pos

def split_quadrants(big_labware_dims, labware_dim_relations, small_labware_slots, by_row =  True):
    '''
    Distribuye las filas y columnas de los cuadrantes
    '''
    destiny_dict = {}
    row_idx = 0
    col_idx = 0
    row_list = [x for x in range(big_labware_dims[0])]
    col_list = [x for x in range(big_labware_dims[1])]
    rows = split_list(row_list, int(len(row_list)/labware_dim_relations[0]))
    cols = split_list(col_list, int(len(col_list)/labware_dim_relations[1]))
    for slot in small_labware_slots:
        destiny_dict[slot] = (rows[row_idx], cols[col_idx])
        if by_row:
            row_idx, col_idx = increase_idx(row_idx, col_idx, labware_dim_relations[0])
        else:
            col_idx, row_idx = increase_idx(col_idx, row_idx, labware_dim_relations[1])
    return destiny_dict


def tuple_quadrants(quadrants):
    '''
    Recibe un diccionario de cuadrantes y devuelve un diccionario con listas de tuplas de celdas identificadas individualmente por cuadrante
    '''
    tuple_quadrant = {}
    for key, value in quadrants.items():
        tuples_list = [(row, col) for row in value[0] for col in value[1]]
        tuple_quadrant[key] = tuples_list
    return tuple_quadrant

def calc_wells_for_quadrant(tuple_quadrants, well_coords):
    '''
    traduce las coordenads que controla tuple_quadrants a posiciones de celda
    '''
    wells_quadrants = {}
    for key, value in tuple_quadrants.items():
        well_list = []
        for well, coords in well_coords.items():
            if coords in value:
                well_list.append(well)
        well_list.sort()
        wells_quadrants[key] = well_list
    return wells_quadrants

def create_orders_quadrant(well_quad, dest_labw_slot, src_labware, dest_labware, src_key = 'src', dest_key = 'dest', slot_key = 'slot', 
well_key = 'well',labware_key = 'labware'):
    '''
    Traduce los cuadrantes a orden de pipeteo para un algoritmo de transfer
    '''
    orders = {}
    for key, value in well_quad.items():
        small_lbw_well = 0
        for well in value:
            orders[well] = {
                src_key:{
                slot_key: key,
                labware_key: src_labware[key],
                well_key: small_lbw_well}, 
            dest_key: {
                slot_key: dest_labw_slot,
                labware_key : dest_labware[dest_labw_slot[0]],
                well_key : well
                }
            }
            small_lbw_well += 1
    return orders

def build_quadrants_orders(big_labware_dims, labware_relations, small_lbw_slots, big_lbw_slot,
    src_labware, dest_labware, by_row = True):
    #Queda añadirle la gestión de la dirección
    quadrants = split_quadrants(big_labware_dims, labware_relations, small_lbw_slots, by_row)
    tuple_quad = tuple_quadrants(quadrants)
    well_pos = get_wells_pos(big_labware_dims, by_row)
    well_quad = calc_wells_for_quadrant(tuple_quad, well_pos)
    orders = create_orders_quadrant(well_quad, big_lbw_slot, src_labware, dest_labware)
    return orders

    
def distribute_vol_and_offsets(number_of_tubes, tubes_slot_list, source_slot_list, offset_iterates, 
max_tube_by_rack, max_source_tube_by_rack, max_tubes_fill_by_iter, tube_key_preffix = 'tube_',
tube_rack_slot_key = 'rack_tube_slot', tube_well_key = 'tube_well', falcon_tube_rack_slot_key = 'falcon_rack_slot',
falcon_well_key = 'falcon_well', offset_key = 'offset'):
    #Set variables
    dist_dict={}
    epp_rack_idx = 0
    tube_well_idx = 0
    falcon_rack_idx = 0
    falcon_well_idx = 0
    offset_idx = 0
    tubes_fill_in_iter = 0
    #iter by tubes
    for tube in range(number_of_tubes):
        tube_key = tube_key_preffix + str(tube)
        dist_dict[tube_key] = {}
        #set tubes rack and well
        dist_dict[tube_key][tube_rack_slot_key] = tubes_slot_list[epp_rack_idx]
        dist_dict[tube_key][tube_well_key] = tube_well_idx
        tube_well_idx +=1
        # control dest parameters
        if tube_well_idx >= max_tube_by_rack:
            epp_rack_idx +=1
            tube_well_idx = 0
        # set source well, rack and offset 
        dist_dict[tube_key][falcon_tube_rack_slot_key] = source_slot_list[falcon_rack_idx]
        dist_dict[tube_key][falcon_well_key] = falcon_well_idx
        dist_dict[tube_key][offset_key] = offset_iterates[offset_idx]
        tubes_fill_in_iter +=1
        #control source parameters
        if tubes_fill_in_iter >= max_tubes_fill_by_iter:
            offset_idx +=1
            tubes_fill_in_iter = 0
            if offset_idx >=len(offset_iterates):
                falcon_well_idx +=1
                offset_idx = 0
                if falcon_well_idx >= max_source_tube_by_rack:
                    falcon_rack_idx +=1
                    falcon_well_idx = 0
    return(dist_dict)

def reorder_distribute_dict(distribute_dict, labware_dict, falcon_rack_slot = 'falcon_rack_slot',
    falcon_well = 'falcon_well', offset = 'offset', rack_slot_key='rack_tube_slot', tube_well_key = 'tube_well', 
    distribute_well_key = 'distribute_well', pk_sep = "-" , bottom_distance = 5):
    '''
    Reorder the distribute dict according to PBS_dispensing scheme. Input must be output of distribute_vol_and_offsets
    '''
    new_key_builder = [falcon_rack_slot, falcon_well, offset]
    reorder_dict = {} 
    for dict in distribute_dict.values():
        pklist = [str(dict[key]) for key in dict.keys() if key in new_key_builder]
        #create pk
        pk = pk_sep.join(pklist)
        #Create destiny orders
        order = labware_dict[dict[rack_slot_key]].wells()[dict[tube_well_key]].bottom(bottom_distance)
        if pk not in reorder_dict.keys():
            reorder_dict[pk] = {key: value for key, value in dict.items() if key in new_key_builder}
            reorder_dict[pk][distribute_well_key] = [order]
        else:
            reorder_dict[pk][distribute_well_key].append(order)
    return(reorder_dict)