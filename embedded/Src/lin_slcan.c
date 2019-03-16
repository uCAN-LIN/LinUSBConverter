#include "slcan.h"

#include <stdbool.h>
#include <string.h>
#include <sys/_stdint.h>
#include "open_lin_cfg.h"
#include "open_lin_slave_data_layer.h"

#include "usbd_cdc_if.h"
#include "stm32f0xx_hal.h"

uint8_t lin_master_data[MAX_SLAVES_COUNT * 8];
t_master_frame_table_item master_frame_table[MAX_SLAVES_COUNT];
uint8_t master_frame_table_size = 0;

t_master_frame_table_item* slcan_get_master_table_row(open_lin_pid_t id, int8_t* out_index){
	uint8_t i = -1;
	for (i = 0; i < master_frame_table_size; i++)
	{
		if (id == master_frame_table[i].slot.pid)
		{
			break;
		}
	}
	(*out_index) = i;
	return &master_frame_table[i];
}

/*
 * t016       3 112233 : id 0x16, dlc 3, data 0x11 0x22 0x33
 * T02BA015 0 2 AA55 : extended id 0x2B period 0xA0 timeout 0x15 , dlc 2, data 0xAA 0x55
 *
 * r1230 : can_id 0x123, can_dlc 0, no data, remote transmission request
 */


//T013151502AA55
//t0163112233

void open_lin_net_init(t_master_frame_table_item *a_slot_array, l_u8 a_slot_array_len);

uint8_t addLinMasterRow(uint8_t* line) {
    uint32_t temp;
    int8_t i,out_index;
    t_master_frame_table_item* array_ptr = 0;
    uint16_t tFrame_Max_ms;
    uint8_t offset = 0;
    if (line[0] < 'Z')
    	offset = 5;
    // reset schedule table
    if (line[1] == '2')
    {
    	open_lin_hw_reset();
        slcan_state = SLCAN_STATE_CONFIG;
        master_frame_table_size = 0;
        return 1;
    }

    // start sending
    if (line[1] == '1'){
    	if (lin_type == LIN_SLAVE)
    	{
    		open_lin_net_init(master_frame_table,master_frame_table_size);
    	} else {
    		open_lin_master_dl_init(master_frame_table,master_frame_table_size);
    		 //wakeUpLin();
    	}
        slcan_state = SLCAN_STATE_OPEN;
        return 1;
    }

    // id
    if (!parseHex(&line[2], 2, &temp)) return 0;

	array_ptr = slcan_get_master_table_row(temp, &out_index);
    array_ptr->slot.pid= temp;
    // len
    if (!parseHex(&line[4 + offset], 1, &temp)) return 0;
    if (array_ptr->slot.data_length  > 8) return 0;
    array_ptr->slot.data_length = temp;

    // type
    if ((line[0] == 'r') || (line[0] == 'R'))
    	array_ptr->slot.frame_type = OPEN_LIN_FRAME_TYPE_RECEIVE;
	else
		array_ptr->slot.frame_type = OPEN_LIN_FRAME_TYPE_TRANSMIT;
    // data
    array_ptr->slot.data_ptr = &(lin_master_data[out_index * 8]); //data is later set in case of override
    // period
    if (line[0] < 'Z') // if upper case
    {
    	if (!parseHex(&line[4], 2, &temp)) return 0;
    	array_ptr->offset_ms = temp;
    	if (!parseHex(&line[6], 2, &temp)) return 0;
    	array_ptr->response_wait_ms	= temp;
    } else
    {
		array_ptr->offset_ms = 15;
		// timeout
		tFrame_Max_ms = (((uint16_t)array_ptr->slot.data_length * 10U + 44U) * 7U / 100U) + 1;
		array_ptr->response_wait_ms = (uint8_t)(tFrame_Max_ms);
    }

    if (array_ptr->slot.frame_type == OPEN_LIN_FRAME_TYPE_TRANSMIT)
    {
        for (i = 0; i < array_ptr->slot.data_length; i++)
        {
            if (!parseHex(&line[5 + offset + i * 2], 2, &temp)) return 0;
            array_ptr->slot.data_ptr[i] = temp;
        }
    }

    if ((out_index == master_frame_table_size) && (master_frame_table_size < MAX_SLAVES_COUNT))
    	 master_frame_table_size ++;

    return 1;
}

static t_open_lin_slave_state slcan_lin_slave_state;
static l_u8 slcan_lin_slave_state_data_count;
static uint8_t slcan_lin_data_array[9];
static t_open_lin_data_layer_frame open_lin_data_layer_frame;
uint32_t slcan_lin_timeout_counter = 0;

void lin_slcan_reset(void){
	slcan_lin_slave_state = OPEN_LIN_SLAVE_IDLE;
	slcan_lin_slave_state_data_count = 0;
	slcan_lin_timeout_counter = 0;
//	open_lin_hw_reset();
}

open_lin_frame_slot_t lin_slcan_slot;
void lin_slcan_rx_handler(t_open_lin_data_layer_frame *f)
{
	lin_slcan_slot.pid = f->pid;
	lin_slcan_slot.data_ptr = f->data_ptr;
	lin_slcan_slot.frame_type = OPEN_LIN_FRAME_TYPE_RECEIVE;
	lin_slcan_slot.data_length = f->lenght;
	slcanReciveCanFrame(&lin_slcan_slot);
}

void open_lin_on_rx_frame(open_lin_frame_slot_t *slot)
{
	slcanReciveCanFrame(slot);
}

void lin_slcan_rx_timeout_handler()
{
	if (slcan_state == SLCAN_STATE_OPEN)
	{
		if (slcan_lin_slave_state_data_count == 0)
		{
			/* header send no respone */
			open_lin_data_layer_frame.lenght = 0;
			lin_slcan_rx_handler(&open_lin_data_layer_frame);
		} else
		{
		open_lin_data_layer_frame.lenght = slcan_lin_slave_state_data_count - 1;
		/* checksum calculation */
		if (slcan_lin_data_array[open_lin_data_layer_frame.lenght] == open_lin_data_layer_checksum(open_lin_data_layer_frame.pid,
				open_lin_data_layer_frame.lenght, open_lin_data_layer_frame.data_ptr)) /* TODO remove from interrupt possible function */
		{
			/* valid checksum */
			lin_slcan_rx_handler(&open_lin_data_layer_frame);
		}
		}
	}
	lin_slcan_reset();
}



void lin_slcan_skip_header_reception(uint8_t pid)
{
	open_lin_hw_reset();
	lin_slcan_reset();
	slcan_lin_slave_state = OPEN_LIN_SLAVE_DATA_RX;
	open_lin_data_layer_frame.pid = pid;
	open_lin_data_layer_frame.data_ptr = slcan_lin_data_array;
	slcan_lin_timeout_counter = HAL_GetTick();
}

void lin_slcan_rx(l_u8 rx_byte)
{
	if (open_lin_hw_check_for_break() == l_true)
	{
		lin_slcan_reset();
		slcan_lin_slave_state = OPEN_LIN_SLAVE_PID_RX;
		#ifdef OPEN_LIN_AUTO_BAUND
			open_lin_hw_set_auto_baud();
		#endif
	} else
	{
		switch (slcan_lin_slave_state){
			case (OPEN_LIN_SLAVE_SYNC_RX):
			{
				/* synch byte reception do nothing */

				if (rx_byte != OPEN_LIN_SYNCH_BYTE)
				{
					lin_slcan_reset();
				} else
				{
					slcan_lin_slave_state = OPEN_LIN_SLAVE_PID_RX;
				}
				break;
			}

			case (OPEN_LIN_SLAVE_PID_RX):
			{
				if (rx_byte == 0) break;
				if (open_lin_data_layer_parity(rx_byte) == rx_byte)
				{
					open_lin_data_layer_frame.pid = (open_lin_pid_t)(rx_byte & OPEN_LIN_ID_MASK);
					open_lin_data_layer_frame.data_ptr = slcan_lin_data_array;
				} else
				{
					lin_slcan_reset();
				}
				slcan_lin_slave_state = OPEN_LIN_SLAVE_DATA_RX;
				// slcan_lin_timeout handled in sys timer interrupt function
				slcan_lin_timeout_counter = HAL_GetTick();
				break;
			}
			case (OPEN_LIN_SLAVE_DATA_RX):
			{

				slcan_lin_timeout_counter = HAL_GetTick();
				if (slcan_lin_slave_state_data_count < 8)
				{
					open_lin_data_layer_frame.data_ptr[slcan_lin_slave_state_data_count] = rx_byte;
					slcan_lin_slave_state_data_count ++;
				} else
				{
					open_lin_data_layer_frame.lenght = slcan_lin_slave_state_data_count;
					/* checksum calculation */
					if (rx_byte == open_lin_data_layer_checksum(open_lin_data_layer_frame.pid,
							open_lin_data_layer_frame.lenght, open_lin_data_layer_frame.data_ptr)) /* TODO remove from interrupt possible function */
					{
						/* valid checksum */
						lin_slcan_rx_handler(&open_lin_data_layer_frame);
					}
					lin_slcan_reset();
				}
				break;
			}
			default:
				lin_slcan_reset();
				break;
		}
	}
}


