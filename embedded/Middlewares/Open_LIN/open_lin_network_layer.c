/*
 * open_lin_slave_network_layer.c
 *
 *  Created on: 29.01.2018
 *      Author: ay7vi2
 */

#include "open_lin_network_layer.h"

static open_lin_frame_slot_t *slot_array;
static l_u8 slot_array_len;


void open_lin_net_init(open_lin_frame_slot_t *a_slot_array, l_u8 a_slot_array_len)
{
	slot_array = a_slot_array;
	slot_array_len = a_slot_array_len;
}

open_lin_frame_slot_t* open_lin_net_get_slot(open_lin_pid_t pid)
{
	open_lin_frame_slot_t *result = OPEN_LIN_NET_SLOT_EMPTY;
	uint8_t i = 0;
	for(i = 0; i < (slot_array_len); i++)
	{
		if (slot_array[i].pid == pid){
			result = &slot_array[i];
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
