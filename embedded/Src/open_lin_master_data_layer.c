/*
 * open_lin_master_data_layer.c
 *
 *  Created on: 30.01.2018
 *      Author: ay7vi2
 */

#include "open_lin_types.h"
#include "open_lin_data_layer.h"
#include "open_lin_network_layer.h"
#include "open_lin_hw.h"
#include "open_lin_master_data_layer.h"

typedef enum {
	OPEN_LIN_MASTER_IDLE,
	OPEN_LIN_MASTER_DATA_RX,
	OPEN_LIN_MASTER_TX_DATA,
} t_open_lin_master_state;

static t_open_lin_master_state lin_master_state;
static l_u8 master_rx_count = 0;
static l_u8 master_table_index = 0;
static t_master_frame_table_item *master_frame_table;
static l_u8 master_frame_table_size = 0;
static l_u16 time_passed_since_last_frame_ms = 0;

static void open_lin_master_goto_idle(l_bool next_item);
static void data_layer_next_item(void);
static t_master_frame_table_item* get_current_item(void);

static void open_lin_master_goto_idle(l_bool next_item)
{
	master_rx_count = 0;
	lin_master_state = OPEN_LIN_MASTER_IDLE;
	time_passed_since_last_frame_ms = 0;
	if (next_item)
	{
		data_layer_next_item();
	} else {
		/* do nothing */
	}
}


void open_lin_master_dl_init(t_master_frame_table_item *p_master_frame_table, l_u8 p_master_frame_table_size)
{
	master_frame_table = p_master_frame_table;
	master_frame_table_size = p_master_frame_table_size;
	open_lin_master_goto_idle(l_false);
}

static t_master_frame_table_item* get_current_item(void)
{
	return &(master_frame_table[master_table_index]);
}

static void data_layer_next_item(void)
{

	if (master_table_index >= (l_u8)(master_frame_table_size - 1u))
	{
		master_table_index = 0;
	} else {
		master_table_index ++;
	}
}


l_bool open_lin_master_data_tx_header(open_lin_frame_slot_t  *slot)
{
	l_bool result = l_true;
	result = (open_lin_hw_tx_break()) && result;
	result = (open_lin_hw_tx_byte(0x55)) && result;
	result = (open_lin_hw_tx_byte(open_lin_data_layer_parity(slot->pid))) && result;
	return result;
}

l_bool open_lin_master_data_tx_data(open_lin_frame_slot_t *slot)
{
	l_u8 i = 0;
	l_bool result = l_true;
	for (i = 0; i < slot->data_length; i++)
	{
		result = (open_lin_hw_tx_byte(slot->data_ptr[i])) && result;
	}

	result = (open_lin_hw_tx_byte(open_lin_data_layer_checksum(slot->pid, slot->data_length, slot->data_ptr))) && result;
	return result;
}

l_bool open_lin_master_dl_rx(l_u8 rx_byte)
{
	open_lin_frame_slot_t* slot = &(get_current_item()->slot);
	static l_u8 frame_tmp_buffer[OPEN_LIN_MAX_FRAME_LENGTH];
	l_bool pending = false;

	if (lin_master_state == OPEN_LIN_MASTER_DATA_RX)
	{
		if (master_rx_count < slot->data_length)
		{
			frame_tmp_buffer[master_rx_count] = rx_byte;
			master_rx_count ++;
			pending = l_true;
		} else
		{
			if (rx_byte == open_lin_data_layer_checksum(slot->pid,slot->data_length,frame_tmp_buffer))
			{
				(void)open_lin_memcpy(slot->data_ptr,frame_tmp_buffer,slot->data_length);
				open_lin_master_dl_rx_callback(slot);
			} else
			{
				open_lin_error_handler(OPEN_LIN_MASTER_ERROR_CHECKSUM);
			}
			open_lin_master_goto_idle(l_true);
		}
	}
	return pending;
}


void open_lin_master_dl_handler(l_u8 ms_passed)
{
	t_master_frame_table_item* master_table_item = get_current_item();

	if (master_frame_table_size > 0u)
	{
		time_passed_since_last_frame_ms += ms_passed;
		if (lin_master_state == OPEN_LIN_MASTER_IDLE)
		{
			if ((master_table_item->offset_ms) < time_passed_since_last_frame_ms)
			{
				time_passed_since_last_frame_ms = 0;
				if (open_lin_master_data_tx_header(&master_table_item->slot) == l_true)
				{
					if (master_table_item->slot.frame_type == OPEN_LIN_FRAME_TYPE_TRANSMIT)
					{
						lin_master_state = OPEN_LIN_MASTER_TX_DATA;
					} else
					{
						lin_master_state = OPEN_LIN_MASTER_DATA_RX;
						master_rx_count = 0;
						open_lin_set_rx_enabled(true);
					}
				} else
				{
					open_lin_error_handler(OPEN_LIN_MASTER_ERROR_HEADER_TX);
					lin_master_state = OPEN_LIN_MASTER_IDLE;
				}
			}
		} else
		{
			/* do nothing */
		}
		switch (lin_master_state)
		{
			case OPEN_LIN_MASTER_IDLE:
			{
				open_lin_set_rx_enabled(false);
				/* do nothing */
				break;
			}
			case OPEN_LIN_MASTER_DATA_RX:
			{
				if (time_passed_since_last_frame_ms > master_table_item->response_wait_ms)
				{
					open_lin_error_handler(OPEN_LIN_MASTER_ERROR_DATA_RX_TIMEOUT);
					open_lin_master_goto_idle(l_true);
				} else
				{
					/*data reception handled by open_lin_master_data_layer_rx, timeout handled here*/
				}
				break;
			}

			case OPEN_LIN_MASTER_TX_DATA:
			{
				if (open_lin_master_data_tx_data(&master_table_item->slot) == l_true)
				{
					open_lin_master_goto_idle(l_true);
				} else
				{
					open_lin_error_handler(OPEN_LIN_MASTER_ERROR_DATA_TX);
					lin_master_state = OPEN_LIN_MASTER_IDLE;
				}
				break;
			}
			default:
				/* do nothing */
				break;
		}
	} else {
		/* empty master table do nothing */
	}
}



