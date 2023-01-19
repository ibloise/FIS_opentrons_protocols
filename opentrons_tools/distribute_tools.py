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
        
    new_key_builder = [falcon_rack_slot, falcon_well, offset]
    reorder_dict = {} 
    for dict in distribute_dict.values():
        pklist = [str(dict[key]) for key in dict.keys() if key in new_key_builder]
        pk = pk_sep.join(pklist)
        order = labware_dict[dict[rack_slot_key]].wells()[dict[tube_well_key]].bottom(bottom_distance)
        if pk not in reorder_dict.keys():
            reorder_dict[pk] = {key: value for key, value in dict.items() if key in new_key_builder}
            reorder_dict[pk][distribute_well_key] = [order]
        else:
            reorder_dict[pk][distribute_well_key].append(order)
    return(reorder_dict)