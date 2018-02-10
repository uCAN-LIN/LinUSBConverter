/*
 * open_lin_frame_st32.c
 *
 *  Created on: 25.01.2018
 *      Author: ay7vi2
 */
#include "../../open_lin_cfg.h"
#include "../../open_lin_data_layer.h"
#include "../../open_lin_hw.h"
#include "../../open_lin_network_layer.h"

t_open_lin_error sim_handler_called = OPEN_LIN_NO_ERROR;

t_open_lin_error get_and_clear_sim_error()
{
	t_open_lin_error res = sim_handler_called;
	sim_handler_called = OPEN_LIN_NO_ERROR;
	return res;
}
void open_lin_error_handler(t_open_lin_error error_code)
{
	sim_handler_called = error_code;
	/* no error handling */
}

l_bool sim_break = false;
l_bool open_lin_hw_check_for_break(void)
{
	l_bool res = sim_break;
	sim_break = false;
	return res;
}

uint8_t lasttx[255];
uint8_t tx_index;

uint8_t* get_last_tx()
{
	return lasttx;
}

uint8_t get_last_tx_index()
{
	uint8_t res = tx_index;
	tx_index = 0;
	return res;
}

l_bool open_lin_hw_tx_break(void){
	lasttx[tx_index] = 0;
	if (tx_index < sizeof(lasttx))
		tx_index ++;
	return true;
}

void open_lin_frame_set_auto_baud(void)
{

}

l_bool open_lin_hw_tx_byte(l_u8 byte)
{
	lasttx[tx_index] = byte;
	if (tx_index < sizeof(lasttx))
		tx_index ++;
	return true;
}

void open_lin_hw_reset(void) {
	tx_index = 0;
}

open_lin_frame_slot_t* last_rx_slot;
void open_lin_master_dl_rx_callback(open_lin_frame_slot_t* slot)
{
	last_rx_slot  = slot;
}
