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
DILUTION_COCIENT = 5

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
eppendorf_labware = {
    LABWARE_NAME : 'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
    LABWARE_SLOTS : ['7', '8', '4', '5'],
    LABWARE_LABEL : "Opentrons Rack de tubos eppendorf de 2 mL",
    LABWARE_TYPE : WELLPLATE_TYPE,
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

inactivation_plate_labware = {    
    LABWARE_NAME : 'biorad_96_wellplate_200ul_pcr',
    LABWARE_SLOTS : ['1'],
    LABWARE_LABEL : "Placa de PCR de biorad 200 ul",
    LABWARE_TYPE : WELLPLATE_TYPE,
    WELLS_COUNT : 96
}

pcr_plate_labware = {    
    LABWARE_NAME : 'biorad_96_wellplate_200ul_pcr',
    LABWARE_SLOTS : ['2'],
    LABWARE_LABEL : "Placa de PCR de biorad 200 ul",
    LABWARE_TYPE : WELLPLATE_TYPE,
    WELLS_COUNT : 96
}


def transfer_orders(tubes_number, source_labware, dest_labware, source_offset, dest_offset, transpose = False):
    '''
    create sequential orders for transfer liquid according to InstrumentContext.transfer() opentrons API function
    '''
    pass

def run(ctx: protocol_api.ProtocolContext):
    #ToDO: comprobar que todo cuadra

    # load labware
    source_rack = {str(slot) : ctx.load_labware(
        eppendorf_labware[LABWARE_NAME], slot,
        eppendorf_labware[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
        for slot in eppendorf_labware[LABWARE_SLOTS]
    }
    
    inactivation_plate = {str(slot) : ctx.load_labware(
    inactivation_plate_labware[LABWARE_NAME], slot,
    inactivation_plate_labware[LABWARE_LABEL] + SLOT_LABEL_SUFFIX + str(slot)) 
    for slot in inactivation_plate_labware[LABWARE_SLOTS]
    }

    tipracks20 = [
        ctx.load_labware(
            p20_pipette[TIP_RACK_LABWARE_NAME_KEY],slot, p20_pipette[TIP_RACK_LABEL_KEY] + f'_slot {str(index)}') 
            for index, slot in enumerate(p20_pipette[TIP_RACK_SLOT_LIST_KEY])]

    # load pipette
    p20 = ctx.load_instrument(
        p20_pipette[PIPETTE_LABWARE_NAME_KEY], p20_pipette[PIPETTE_POSITION_KEY], tip_racks=tipracks20)

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