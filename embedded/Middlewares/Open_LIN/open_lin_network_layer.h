/*
 * open_lin_slave_network_layer.h
 *
 *  Created on: 29.01.2018
 *      Author: ay7vi2
 */

#ifndef OPEN_LIN_NETWORK_LAYER_H_
#define OPEN_LIN_NETWORK_LAYER_H_

#include "open_lin_types.h"

#define OPEN_LIN_NET_SLOT_EMPTY ((void*)0)

typedef struct {
	open_lin_pid_t pid;
	open_lin_frame_type_t frame_type;
	l_u8 data_length;
	l_u8 *data_ptr;
} open_lin_frame_slot_t;

open_lin_frame_slot_t* open_lin_net_get_slot(open_lin_pid_t pid);
void open_lin_net_rx_handler(open_lin_pid_t pid);
void open_lin_net_init(open_lin_frame_slot_t *a_slot_array, l_u8 a_slot_array_len);
void open_lin_on_rx_frame(open_lin_frame_slot_t *slot);

#endif /* OPEN_LIN_NETWORK_LAYER_H_ */
