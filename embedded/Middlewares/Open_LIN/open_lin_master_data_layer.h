/*
 * open_lin_master_data_layer.h
 *
 *  Created on: 30.01.2018
 *      Author: ay7vi2
 */

#ifndef OPEN_LIN_OPEN_LIN_MASTER_DATA_LAYER_H_
#define OPEN_LIN_OPEN_LIN_MASTER_DATA_LAYER_H_

#include "open_lin_types.h"
#include "open_lin_network_layer.h"
typedef struct {
	uint8_t offset_ms;
	uint8_t response_wait_ms;
	open_lin_frame_slot_t slot;
} t_master_frame_table_item;

void open_lin_master_dl_init(t_master_frame_table_item *p_master_frame_table, l_u8 p_master_frame_table_size);
l_bool open_lin_master_dl_rx(l_u8 rx_byte);
void open_lin_master_dl_handler(l_u8 ms_passed);
void open_lin_master_dl_rx_callback(open_lin_frame_slot_t* slot);

/* this functions by default are handled by open_lin_mastr_dl_handler */
l_bool open_lin_master_data_tx_header(open_lin_frame_slot_t  *slot);
l_bool open_lin_master_data_tx_data(open_lin_frame_slot_t *slot);


#endif /* OPEN_LIN_OPEN_LIN_MASTER_DATA_LAYER_H_ */
