from opentrons import protocol_api
from FIS_opentrons_tools import *

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





#Protocol
def run(ctx: protocol_api.ProtocolContext):

    # load labware
    source_racks = {str(slot) : ctx.load_labware(
        source_labware_settings[LABWARE_NAME], slot,
        source_labware_settings[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
        for slot in source_labware_settings[LABWARE_SLOTS]
    }

    temp_mod = ctx.load_module('temperature module', extraction_labw_plate_settings[LABWARE_SLOTS][0]) 
    
    extraction_plate = {str(slot) : temp_mod.load_labware(
    extraction_labw_plate_settings[LABWARE_NAME],
    label = extraction_labw_plate_settings[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
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

    #Invert relations
    relations = [1/x for x in dims[relation_key]]

    orders = build_quadrants_orders(dims[dest_key], relations,source_labware_settings[LABWARE_SLOTS], extraction_labw_plate_settings[LABWARE_SLOTS],
    src_labware=source_racks, dest_labware=extraction_plate)

    #Rates
    p20.flow_rate.aspirate = P20_ASP_RATE_FIRST_STEP
    p20.flow_rate.dispense = P20_DISP_RATE_FIRST_STEP
    p20.flow_rate.blow_out = P20_BLOW_RATE_FIRST_STEP
    
    #distribute eppendorf to extraction plate

    #Sample control

    orders = {idx : orders[idx] for idx in range(NUMBER_OF_SAMPLES) }

    for order in orders.values():
        p20.transfer(
            volume = 10,
            source = order['src']['labware'].wells()[order['src']['well']],
            dest=order['dest']['labware'].wells()[order['dest']['well']],
            disposal_volume=0,
            new_tip = 'always' 
        )
    
    #Extraction
    temp_mod.set_temperature(celsius = 90)
    temp_mod.status
    ctx.delay(minutes=10)
    temp_mod.set_temperature(celsius=25)
    temp_mod.status
    ctx.pause(msg= 'Protocolo en pausa')

    temp_mod.deactivate


