from opentrons import protocol_api
import math
# metadata
metadata = {
    'protocolName': 'PBS_dispensing',
    'author': 'Microbiologia HU La Paz',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}
VERSION = '1.0.0'

#192 es el máximod e tubos que se pueden llenar con 8 racks de 24
NUMBER_OF_TUBES = 192

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

#Variables del programa
DISP_VOLUME_UL = 1000
MAX_EPPENDORF_RACK_ADMIT = 8
MAX_FALCON_RACK_ADMIT = 1
FALCON_VOLUME_ML = 50
PBS_LOST_PERCENT = 0.1 #Calculo en tanto por 1 del excedente de PBS necesario por perdidas de adherencia, etc

# Dict labwares

EPPENDORF_LABWARE = {
    LABWARE_NAME : 'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
    LABWARE_SLOTS : ['10', '7', '4', '1', '11', '8', '5', '2'],
    LABWARE_LABEL : "Opentrons Rack de tubos eppendorf de 2 mL",
    LABWARE_TYPE : TUBERACK_TYPE,
    TUBE_COUNT : 24
}
FALCON_LABWARE = {
    LABWARE_NAME : 'opentrons_6_tuberack_falcon_50ml_conical',
    LABWARE_SLOTS : ['6'],
    LABWARE_LABEL : 'Opentrons Rack de tubos falcon 50 mL' ,
    LABWARE_TYPE : TUBERACK_TYPE,
    TUBE_COUNT : 6
}

P1000_PIPETTE = {
    PIPETTE_LABWARE_NAME_KEY :'p1000_single_gen2',
    PIPETTE_POSITION_KEY : RIGHT_POSITION,
    PIPETTE_LABEL_KEY : 'Opentrons P1000 single gen2',
    TIP_RACK_LABWARE_NAME_KEY : 'opentrons_96_filtertiprack_1000ul',
    TIP_RACK_SLOT_LIST_KEY : ['3'],
    TIP_RACK_LABEL_KEY : '1000µl tiprack'
}

#Calculo de variables

EPPENDORF_RACKS_NEEDED = math.ceil(NUMBER_OF_TUBES/EPPENDORF_LABWARE[TUBE_COUNT])
VOLUME_ML_PBS_NEEDED = DISP_VOLUME_UL * NUMBER_OF_TUBES / 1000
FALCON_TUBES_NEEDED = math.ceil((VOLUME_ML_PBS_NEEDED + VOLUME_ML_PBS_NEEDED * PBS_LOST_PERCENT)/FALCON_VOLUME_ML)

#Buscamos el llenado del último rack

EPPENDORFS_LAST_TUBE = NUMBER_OF_TUBES - EPPENDORF_LABWARE[TUBE_COUNT] * (len(EPPENDORF_LABWARE[LABWARE_SLOTS]) -1) - 1

    
def run(ctx: protocol_api.ProtocolContext):
    if EPPENDORF_RACKS_NEEDED > MAX_EPPENDORF_RACK_ADMIT: #No añado control de los falcon, ya que las 6 posiciones admiten más volumen que eppendorf puedes llenar
        ctx.comment('El número de eppendorf excede el permitido')
        exit()
    else:
        EPPENDORF_LABWARE[LABWARE_SLOTS] = [EPPENDORF_LABWARE[LABWARE_SLOTS][idx] for idx in range(EPPENDORF_RACKS_NEEDED)]
    # load labware
    source_rack = [ctx.load_labware(
        FALCON_LABWARE[LABWARE_NAME], slot,
        FALCON_LABWARE[LABWARE_LABEL]) 
        for slot in FALCON_LABWARE[LABWARE_SLOTS]
        ]
    
    dest_racks1 = [
        ctx.load_labware(
            EPPENDORF_LABWARE[LABWARE_NAME], slot,
            'source tuberack ' + str(i+1))
        for i, slot in enumerate(['10', '7', '4', '1'])
    ]

    dest_racks2 = [
        ctx.load_labware(
            EPPENDORF_LABWARE[LABWARE_NAME], slot,
            'source tuberack ' + str(i+1))
        for i, slot in enumerate(['11', '8', '5', '2'])
    ]
    
    tipracks1000 = [
        ctx.load_labware(
            P1000_PIPETTE[TIP_RACK_LABWARE_NAME_KEY],slot, P1000_PIPETTE[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}') 
            for index, slot in enumerate(P1000_PIPETTE[TIP_RACK_SLOT_LIST_KEY])]

    # load pipette
    p1000 = ctx.load_instrument(
        P1000_PIPETTE[PIPETTE_LABWARE_NAME_KEY], P1000_PIPETTE[PIPETTE_POSITION_KEY], tip_racks=tipracks1000)

    #Rates
    p1000.flow_rate.aspirate = 600
    p1000.flow_rate.dispense = 1000
    p1000.flow_rate.blow_out = 1000
    
    #Calculamos las fuentes

    avl1 = source_rack['A1']
    avl2 = source_rack['B1']


    # transfer
    for idx, dest in enumerate(dest_racks1):
        if idx != 3:
            offset = 60 - (20 * idx)
        else:
            offset = 3
        p1000.distribute(
            volume=500,
            source=avl1.bottom(offset),
            dest=[dest.wells()],
            disposal_volume=0,
            new_tip='never')
        
    # transfer
    for idx, dest in enumerate(dest_racks2):
        if idx != 3:
            offset = 60 - (20 * idx)
        else:
            offset = 3
        p1000.distribute(
            volume=500,
            source=avl2.bottom(offset),
            dest=[dest.wells()],
            disposal_volume=0,
            new_tip='never')

    p1000.drop_tip()  


