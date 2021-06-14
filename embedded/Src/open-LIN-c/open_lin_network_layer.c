/**
 * @file open_open_lin_network_layer.h
 * @author LJ
 * @date 06.07.2018
 * @brief Open LIN network layer
 */

#include "open_lin_network_layer.h"
#include "open_lin_hw.h"
#include "open_lin_master_data_layer.h"


static t_master_frame_table_item* slot_array;
static l_u8 slot_array_len;


void open_lin_net_init(t_master_frame_table_item *a_slot_array, l_u8 a_slot_array_len)
{
	slot_array = a_slot_array;
	slot_array_len = a_slot_array_len;
	open_lin_set_rx_enabled(true);
}

#ifdef OPEN_LIN_DYNAMIC_IDS
	extern open_lin_id_translation_item_t open_lin_id_translation_tab[];
#endif

open_lin_frame_slot_t* open_lin_net_get_slot(open_lin_pid_t pid)
{
	open_lin_frame_slot_t *result = OPEN_LIN_NET_SLOT_EMPTY;
	uint8_t i = 0;
    
#ifdef OPEN_LIN_DYNAMIC_IDS
    uint8_t translate_found = 0; 
	for(i = 0; i < (slot_array_len); i++)
	{
		if (open_lin_id_translation_tab[i].input_id == pid)
		{
			pid = open_lin_id_translation_tab[i].id_in_lin_table;
            translate_found = 1;
			break;
		} else
		{
			/* do nothing */
		}
	}
    if (translate_found == 0)
    {
        return result; /* MISRA violation */
    } else {
        /* do nothing */
    }
#endif
	for(i = 0; i < (slot_array_len); i++)
	{
		if (slot_array[i].slot.pid == pid){
			result = &slot_array[i].slot;
			break;
		} else
		{
			/* do nothing */
		}
	}

	return result;
};

void open_lin_net_rx_handler(open_lin_pid_t pid) {
	open_lin_frame_slot_t* slot = open_lin_net_get_slot(pid);
	open_lin_on_rx_frame(slot);
};
