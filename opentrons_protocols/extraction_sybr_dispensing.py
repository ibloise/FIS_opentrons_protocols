from opentrons import protocol_api

# metadata
metadata = {
    'protocolName': 'extraction_sybr_dispensing',
    'author': 'Microbiologia HU La Paz',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3',
    'author' : 'Iván Bloise-Sánchez',
    'description' : '''This protocol extract rectal swab and dispensing into PCR plate for screening PCR'''
}
VERSION = '0.1.0'

# samples

NUMBER_OF_SAMPLES = 94

#Variables del programa
MAX_SAMPLES_NUMBER = 94
PRELOAD_VOLUME_UL = 60
DILUTION_COCIENT = 10
P20_ASP_RATE_FIRST_STEP = 600
P20_DISP_RATE_FIRST_STEP = 1000
P20_BLOW_RATE_FIRST_STEP = 1000
P20_ASP_RATE_SECOND_STEP = 600
P20_DISP_RATE_SECOND_STEP = 1000
P20_BLOW_RATE_SECOND_STEP = 1000


#Variables de configuracion
PIPETTE_LABWARE_NAME_KEY = "pipette_labware_name"
PIPETTE_LABEL_KEY = "pipette_label"
PIPETTE_POSITION_KEY = "position"
TIP_RACK_LABWARE_NAME_KEY = "tip_rack_labware_name"
TIP_RACK_SLOT_LIST_KEY = "tip_rack_slots"
TIP_RACK_LABEL_KEY = "tip_rack_label"
LABWARE_NAME = 'labware_name'
LABWARE_SLOTS = 'labware_slots'
LABWARE_LABEL = 'labware_label'
LABWARE_TYPE = 'labware_type'
LEFT_POSITION = 'left'
RIGHT_POSITION = 'right'
TUBERACK_TYPE = 'tube_rack'
WELLPLATE_TYPE = 'well_plate'
TUBE_COUNT = 'tube_count'
WELLS_COUNT  = 'wells_count'
SLOT_LABEL_SUFFIX = '_slot_'


#Labwares
source_labware_settings = {
    LABWARE_NAME : 'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
    LABWARE_SLOTS : ['7', '8', '4', '5'],
    LABWARE_LABEL : "Opentrons Rack de tubos eppendorf de 2 mL",
    LABWARE_TYPE : TUBERACK_TYPE,
    TUBE_COUNT : 24
}

p20_pipette = {
    PIPETTE_LABWARE_NAME_KEY :'p20_single_gen2',
    PIPETTE_POSITION_KEY : LEFT_POSITION,
    PIPETTE_LABEL_KEY : 'Opentrons P20 single gen2',
    TIP_RACK_LABWARE_NAME_KEY : 'opentrons_96_filtertiprack_20ul',
    TIP_RACK_SLOT_LIST_KEY : ['3'],
    TIP_RACK_LABEL_KEY : '20µl tiprack'
}

extraction_labw_plate_settings = {    
    LABWARE_NAME : 'nest_96_wellplate_200ul_flat', 
    LABWARE_SLOTS : ['1'],
    LABWARE_LABEL : "Placa de PCR de nest 200 ul",
    LABWARE_TYPE : WELLPLATE_TYPE,
    WELLS_COUNT : 96
}

pcr_labw_plate_settings = {    
    LABWARE_NAME : 'biorad_96_wellplate_200ul_pcr',
    LABWARE_SLOTS : ['2'],
    LABWARE_LABEL : "Placa de PCR de biorad 200 ul",
    LABWARE_TYPE : WELLPLATE_TYPE,
    WELLS_COUNT : 96
}

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


#Protocol
def run(ctx: protocol_api.ProtocolContext):

    # load labware
    source_racks = {str(slot) : ctx.load_labware(
        source_labware_settings[LABWARE_NAME], slot,
        source_labware_settings[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
        for slot in source_labware_settings[LABWARE_SLOTS]
    }
    
    extraction_plate = {str(slot) : ctx.load_labware(
    extraction_labw_plate_settings[LABWARE_NAME], slot,
    extraction_labw_plate_settings[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
    for slot in extraction_labw_plate_settings[LABWARE_SLOTS]
    }

    tipracks20 = [
        ctx.load_labware(
            p20_pipette[TIP_RACK_LABWARE_NAME_KEY],slot, p20_pipette[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}') 
            for index, slot in enumerate(p20_pipette[TIP_RACK_SLOT_LIST_KEY])]

    # load pipette
    p20 = ctx.load_instrument(
        p20_pipette[PIPETTE_LABWARE_NAME_KEY], p20_pipette[PIPETTE_POSITION_KEY], tip_racks=tipracks20)
    
    #****First step*****
    # get orders
    #dimensions
    dest_key = 'extraction'
    relation_key = 'relation'

    dims = src_dest_dimensions(source_racks[source_labware_settings[LABWARE_SLOTS][0]], extraction_plate[extraction_labw_plate_settings[LABWARE_SLOTS][0]], 
    dest_key=dest_key, rel_key = relation_key)
    relations = [1/x for x in dims[relation_key]]

    orders = build_quadrants_orders(dims[dest_key], relations,source_labware_settings[LABWARE_SLOTS], extraction_labw_plate_settings[LABWARE_SLOTS],
    src_labware=source_racks, dest_labware=extraction_plate)

    #Rates
    #p20.flow_rate.aspirate = P1000_FLOW_ASPIRATE
    #p20.flow_rate.dispense = P100_FLOW_DISPENSE
    #p20.flow_rate.blow_out = P1000_FLOW_BLOWOUT
    
    #distribute eppendorf to extraction plate

    p20.pick_up_tip()

    for order in orders.values():
        p20.transfer(
            volume = 10,
            source = order['src']['labware'].wells()[order['src']['well']],
            dest=order['dest']['labware'].wells()[order['dest']['well']],
            disposal_volume=0,
            new_tip = 'never' 
        )
    p20.drop_tip()