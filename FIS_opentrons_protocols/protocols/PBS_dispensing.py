from opentrons import protocol_api
from FIS_opentrons_tools import *
import math

# metadata
metadata = {
    'protocolName': 'PBS_dispensing',
    'author': 'Microbiologia HU La Paz',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3',
    'author' : 'Iván Bloise-Sánchez'
}
VERSION = '1.0.0'

#192 es el máximod e tubos que se pueden llenar con 8 racks de 24
NUMBER_OF_TUBES = 192

#Variables del programa
DISP_VOLUME_UL = 500
DISP_VOLUME_ML = DISP_VOLUME_UL / 1000
MAX_EPPENDORF_RACK_ADMIT = 8
MAX_FALCON_RACK_ADMIT = 1
FALCON_VOLUME_ML = 50
PBS_LOST_PERCENT = 0.025 #Calculo en tanto por 1 del excedente de PBS necesario por perdidas de adherencia, etc
OFFSET_ITERATES = [80, 50, 20, 5]
P1000_FLOW_ASPIRATE = 600
P100_FLOW_DISPENSE = 1000
P1000_FLOW_BLOWOUT = 1000
START_WELL = 0

#Variables de configuracion
## Mandar a un modulo
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
TUBE_COUNT = 'tube_count'
SLOT_LABEL_SUFFIX = ' slot '
FALCON_DICT_PREFFIX = 'falcon_'
FALCON_SLOT_KEY = 'slot'
FALCON_DICT_KEY = 'falcon'
ORDER_FALCON_KEY = 'order'
OFFSET_KEY = 'offset'
OFFSET_VALUE_KEY = 'offset_value'
DEST_WELLS_KEY = 'dest_wells'
SRC_LBW_SLOT_KEY = 'source_labware_slot'
SRC_LBW_WELL_KEY = 'source_labware_well'
DEST_LBW_SLOT_KEY = 'dest_labware_slot'
DEST_LBW_WELL_KEY = "dest_labware_well"
OFFSET_SLOT = 'offset_slot' 
DISTRIBUTE_WELL_KEY = 'distribute_wells'

# Dict labwares-> habría que pasarlo a clases

eppendorf_labware = {
    LABWARE_NAME : 'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
    LABWARE_SLOTS : ['10', '7', '4', '1', '11', '8', '5', '2'],
    LABWARE_LABEL : "Opentrons Rack de tubos eppendorf de 2 mL",
    LABWARE_TYPE : TUBERACK_TYPE,
    TUBE_COUNT : 24
}
falcon_labware = {
    LABWARE_NAME : 'opentrons_6_tuberack_falcon_50ml_conical',
    LABWARE_SLOTS : ['6'],
    LABWARE_LABEL : 'Opentrons Rack de tubos falcon 50 mL' ,
    LABWARE_TYPE : TUBERACK_TYPE,
    TUBE_COUNT : 6
}

p1000_pipette = {
    PIPETTE_LABWARE_NAME_KEY :'p1000_single_gen2',
    PIPETTE_POSITION_KEY : RIGHT_POSITION,
    PIPETTE_LABEL_KEY : 'Opentrons P1000 single gen2',
    TIP_RACK_LABWARE_NAME_KEY : 'opentrons_96_filtertiprack_1000ul',
    TIP_RACK_SLOT_LIST_KEY : ['3'],
    TIP_RACK_LABEL_KEY : '1000µl tiprack'
}

#Calculo de variables
eppendorfs_racks_needed = math.ceil(NUMBER_OF_TUBES/eppendorf_labware[TUBE_COUNT])
volume_ml_pbs_needed = DISP_VOLUME_ML * NUMBER_OF_TUBES
falcon_tubes_needed = math.ceil((volume_ml_pbs_needed + volume_ml_pbs_needed * PBS_LOST_PERCENT)/FALCON_VOLUME_ML)
falcons_racks_needed = math.ceil(falcon_tubes_needed/falcon_labware[TUBE_COUNT])
eppendorfs_fill_falcon = math.floor(FALCON_VOLUME_ML / (DISP_VOLUME_ML + DISP_VOLUME_ML * PBS_LOST_PERCENT))
racks_fill_falcon = math.floor(eppendorfs_fill_falcon / eppendorf_labware[TUBE_COUNT]) # Vamos a RACKS completos
eppendors_fill_offset_iter = math.floor(racks_fill_falcon * eppendorf_labware[TUBE_COUNT] / len(OFFSET_ITERATES))
racks_fill_iter = math.floor(eppendors_fill_offset_iter/eppendorf_labware[TUBE_COUNT])
eppendorf_fill_last_iter = racks_fill_falcon * eppendorf_labware[TUBE_COUNT] - eppendors_fill_offset_iter * (len(OFFSET_ITERATES)- 1)

#Calculamos la iteración de pipeteo
distribute_dict = distribute_vol_and_offsets(NUMBER_OF_TUBES, eppendorf_labware[LABWARE_SLOTS], falcon_labware[LABWARE_SLOTS],
OFFSET_ITERATES,eppendorf_labware[TUBE_COUNT],falcon_labware[TUBE_COUNT], eppendors_fill_offset_iter, tube_rack_slot_key=DEST_LBW_SLOT_KEY,
tube_well_key=DEST_LBW_WELL_KEY, falcon_tube_rack_slot_key=SRC_LBW_SLOT_KEY, falcon_well_key=SRC_LBW_WELL_KEY, offset_key=OFFSET_KEY)

def run(ctx: protocol_api.ProtocolContext):
    if eppendorfs_racks_needed > MAX_EPPENDORF_RACK_ADMIT or falcons_racks_needed > MAX_FALCON_RACK_ADMIT: 
        ctx.comment('El número de eppendorf o de tubos falcon excede el permitido')
        exit()
    else:
        eppendorf_labware[LABWARE_SLOTS] = [eppendorf_labware[LABWARE_SLOTS][idx] for idx in range(eppendorfs_racks_needed)]
    # load labware
    source_rack = {str(slot) : ctx.load_labware(
        falcon_labware[LABWARE_NAME], slot,
        falcon_labware[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
        for slot in falcon_labware[LABWARE_SLOTS]
    }
    
    eppendorf_racks = {str(slot) : ctx.load_labware(
        eppendorf_labware[LABWARE_NAME], slot,
        eppendorf_labware[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot))
        for slot in eppendorf_labware[LABWARE_SLOTS]
    }

    tipracks1000 = [
        ctx.load_labware(
            p1000_pipette[TIP_RACK_LABWARE_NAME_KEY],slot, p1000_pipette[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}') 
            for index, slot in enumerate(p1000_pipette[TIP_RACK_SLOT_LIST_KEY])]

    # load pipette
    p1000 = ctx.load_instrument(
        p1000_pipette[PIPETTE_LABWARE_NAME_KEY], p1000_pipette[PIPETTE_POSITION_KEY], tip_racks=tipracks1000)

    #Rates
    p1000.flow_rate.aspirate = P1000_FLOW_ASPIRATE
    p1000.flow_rate.dispense = P100_FLOW_DISPENSE
    p1000.flow_rate.blow_out = P1000_FLOW_BLOWOUT
    
    #get orders
    orders = reorder_distribute_dict(distribute_dict, eppendorf_racks, falcon_rack_slot=SRC_LBW_SLOT_KEY, falcon_well= SRC_LBW_WELL_KEY,
    offset=OFFSET_KEY, rack_slot_key= DEST_LBW_SLOT_KEY, tube_well_key=DEST_LBW_WELL_KEY, distribute_well_key=DISTRIBUTE_WELL_KEY)

    #distribute
    p1000.pick_up_tip()
    for order in orders.values():
        source = source_rack[order[SRC_LBW_SLOT_KEY]].wells()[order[SRC_LBW_WELL_KEY]]
        p1000.distribute(
            volume = DISP_VOLUME_UL,
            source = source.bottom(order[OFFSET_KEY]),
            dest=order[DISTRIBUTE_WELL_KEY],
            disposal_volume=0,
            new_tip = 'never'
        )
    p1000.drop_tip()