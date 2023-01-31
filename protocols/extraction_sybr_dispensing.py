from math import ceil
from opentrons import protocol_api
from FIS_opentrons_tools.distribute_tools import *
from FIS_opentrons_tools.constants import *

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

NUMBER_OF_SAMPLES = 12

#Variables del programa
MAX_SAMPLES_NUMBER = 94
PRELOAD_VOLUME_UL = 90
FINAL_DILUTION_VOLUME = 100
DILUTION_FACTOR = 10
PCR_VOL_UL = 5
ASP_RATE_FIRST_STEP = 600
DISP_RATE_FIRST_STEP = 1000
BLOW_RATE_FIRST_STEP = 1000
ASP_RATE_SECOND_STEP = 600
DISP_RATE_SECOND_STEP = 1000
BLOW_RATE_SECOND_STEP = 1000
EXTRACTION_TEMP = 90 #Temperatura de extracción
EXTRACTION_TIME = 10
POSTEXTRACTION_TEMP = 25 #TEMPERATURA DE ESPERA
MULTI_PIPETTE = True

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
    TIP_RACK_SLOT_LIST_KEY : ['6'],
    TIP_RACK_LABEL_KEY : '20µl tiprack'
}

multip20_pipette = {    
    PIPETTE_LABWARE_NAME_KEY :'p20_multi_gen2',
    PIPETTE_POSITION_KEY : RIGHT_POSITION,
    PIPETTE_LABEL_KEY : 'Opentrons P20 multi gen2',
    TIP_RACK_LABWARE_NAME_KEY : 'opentrons_96_filtertiprack_20ul',
    TIP_RACK_SLOT_LIST_KEY : ['3'],
    TIP_RACK_LABEL_KEY : 'multichannel 20µl tiprack'

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

#calcs

first_step_src_vol = calc_solution(FINAL_DILUTION_VOLUME, DILUTION_FACTOR, PRELOAD_VOLUME_UL)[0]
last_col = ceil(NUMBER_OF_SAMPLES/8) #Ojo, que esto solo vale para labwares de 8 filas

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

    pcr_plate = {str(slot) : ctx.load_labware(
    pcr_labw_plate_settings[LABWARE_NAME], slot,
    pcr_labw_plate_settings[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
    for slot in pcr_labw_plate_settings[LABWARE_SLOTS]
    }

    tipracks20 = [
        ctx.load_labware(
            p20_pipette[TIP_RACK_LABWARE_NAME_KEY],slot, p20_pipette[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}') 
            for index, slot in enumerate(p20_pipette[TIP_RACK_SLOT_LIST_KEY])
            ]
    multi_tiprack20 = [
        ctx.load_labware(
            multip20_pipette[TIP_RACK_LABWARE_NAME_KEY], slot, multip20_pipette[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}')
            for index, slot in enumerate(multip20_pipette[TIP_RACK_SLOT_LIST_KEY])
    ]

    if MULTI_PIPETTE:
        p20 = ctx.load_instrument(
        p20_pipette[PIPETTE_LABWARE_NAME_KEY], p20_pipette[PIPETTE_POSITION_KEY], tip_racks=tipracks20
        )

        sec_pipette = ctx.load_instrument(
            multip20_pipette[PIPETTE_LABWARE_NAME_KEY], multip20_pipette[PIPETTE_POSITION_KEY], tip_racks=multi_tiprack20
        )
    else:
        p20 = ctx.load_instrument(
        p20_pipette[PIPETTE_LABWARE_NAME_KEY], p20_pipette[PIPETTE_POSITION_KEY], tip_racks=tipracks20.append(multi_tiprack20)
        )
        sec_pipette = p20

    
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
    p20.flow_rate.aspirate = ASP_RATE_FIRST_STEP
    p20.flow_rate.dispense = DISP_RATE_FIRST_STEP
    p20.flow_rate.blow_out = BLOW_RATE_FIRST_STEP
    
    #distribute eppendorf to extraction plate

    #Sample control

    orders = {idx : orders[idx] for idx in range(NUMBER_OF_SAMPLES) }

    for order in orders.values():
        p20.transfer(
            volume = first_step_src_vol,
            source = order['src']['labware'].wells()[order['src']['well']].bottom(5),
            dest=order['dest']['labware'].wells()[order['dest']['well']].bottom(5),
            disposal_volume=0,
            new_tip = 'always' 
        )
    
    #Extraction
    temp_mod.set_temperature(celsius = EXTRACTION_TEMP)
    temp_mod.status
    ctx.delay(minutes=EXTRACTION_TIME)
    temp_mod.set_temperature(celsius=POSTEXTRACTION_TEMP)
    temp_mod.status
    ctx.pause(msg= 'Protocolo en pausa')

    temp_mod.deactivate
    sec_pipette.flow_rate.aspirate = ASP_RATE_SECOND_STEP
    sec_pipette.flow_rate.dispense = DISP_RATE_SECOND_STEP
    sec_pipette.flow_rate.blow_out = BLOW_RATE_SECOND_STEP

    if MULTI_PIPETTE:
        src = extraction_plate['1'].columns()[:last_col]
        dest = pcr_plate['2'].columns()[:last_col]
    else:
        src = extraction_plate['1'].wells()[:NUMBER_OF_SAMPLES]
        dest = pcr_plate['2'].wells()[:NUMBER_OF_SAMPLES]
    
    sec_pipette.transfer(
        volume = PCR_VOL_UL,
        source=src,
        dest = dest,
        disposal_volume=0,
        new_tip = 'always'
    )