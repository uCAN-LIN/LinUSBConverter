/**
 * @file open_lin_slave_data_layer.c
 * @brief LIN slave data layer implementation
 */

#include "open_lin_network_layer.h"
#include "open_lin_data_layer.h"
#include "open_lin_types.h"
#include "open_lin_hw.h"
#include "open_lin_slave_data_layer.h"

/**
 * @brief Internal states definition
 */

static t_open_lin_slave_state open_lin_slave_state;

static l_u8 open_lin_slave_state_data_count;

static l_bool open_lin_slave_set_lin_frame(t_open_lin_data_layer_frame *frame){
	l_bool result = false;
	open_lin_frame_slot_t *frame_slot = open_lin_net_get_slot(frame->pid);
	if (frame_slot != OPEN_LIN_NET_SLOT_EMPTY)
	{
		frame->lenght = frame_slot->data_length;
		frame->data_ptr = frame_slot->data_ptr;
		if (frame_slot->frame_type == OPEN_LIN_FRAME_TYPE_TRANSMIT)
		{
			open_lin_slave_state = OPEN_LIN_SLAVE_DATA_TX;
		} else
		{
			open_lin_slave_state = OPEN_LIN_SLAVE_DATA_RX;
		}
		result = true;
	} else
	{
		/* do nothing */
	}
	return result;
}

void open_lin_slave_init(void)
{
	open_lin_slave_reset();
}

void open_lin_slave_reset(void){
	open_lin_slave_state = OPEN_LIN_SLAVE_IDLE;
	open_lin_slave_state_data_count = 0;
}

void open_lin_slave_rx_header(l_u8 rx_byte)
{
	static t_open_lin_data_layer_frame open_lin_data_layer_frame;
	static l_u8 open_lin_slave_data_buff[OPEN_LIN_MAX_FRAME_LENGTH];

	if (open_lin_hw_check_for_break() == l_true)
	{
		if (open_lin_slave_state != OPEN_LIN_SLAVE_IDLE)
		{
			open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_INVALID_BREAK); /* break should be received only in IDLE state */
		} else {
			/* do nothing, go to SYNC rx anyway*/
		}
        #ifdef OPEN_LIN_HW_BREAK_IS_SYNCH_BYTE
        open_lin_slave_state = OPEN_LIN_SLAVE_PID_RX;
        #else
		open_lin_slave_state = OPEN_LIN_SLAVE_SYNC_RX;
        #endif
        #ifdef OPEN_LIN_AUTO_BAUND
			open_lin_hw_set_auto_baud();
		#endif
	} else
	{
		switch (open_lin_slave_state){
			case (OPEN_LIN_SLAVE_SYNC_RX):
			{
				/* synch byte reception do nothing */
				if (rx_byte != OPEN_LIN_SYNCH_BYTE)
				{
					open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_INVALID_SYNCH);
					open_lin_slave_reset();
				} else
				{
					open_lin_slave_state = OPEN_LIN_SLAVE_PID_RX;
                    break;
				}				
			}

			case (OPEN_LIN_SLAVE_PID_RX):
			{
				if (open_lin_data_layer_parity(rx_byte) == rx_byte)
				{
					open_lin_data_layer_frame.pid = (open_lin_pid_t)(rx_byte & OPEN_LIN_ID_MASK);
				} else
				{
					open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_PID_PARITY);
					open_lin_slave_reset();
				}

				if (open_lin_slave_set_lin_frame(&open_lin_data_layer_frame) == true)
				{
					if (open_lin_slave_state == OPEN_LIN_SLAVE_DATA_TX)
					{
						open_lin_data_layer_frame.checksum = open_lin_data_layer_checksum(open_lin_data_layer_frame.pid,
																open_lin_data_layer_frame.lenght, open_lin_data_layer_frame.data_ptr);
						if ((open_lin_hw_tx_data(open_lin_data_layer_frame.data_ptr, open_lin_data_layer_frame.lenght) == l_false) ||
						   (open_lin_hw_tx_data(&open_lin_data_layer_frame.checksum, (l_u8)sizeof(open_lin_data_layer_frame.checksum)) == l_false))
						{
							open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_HW_TX);
							open_lin_slave_reset();
						} else
						{
							open_lin_slave_reset();
						}
						break;
					}
				} else
				{
					open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_ID_NOT_FOUND);
					open_lin_slave_reset();
				}
				break;
			}
			case (OPEN_LIN_SLAVE_DATA_RX):
			{
				if (open_lin_slave_state_data_count < open_lin_data_layer_frame.lenght)
				{
					open_lin_slave_data_buff[open_lin_slave_state_data_count] = rx_byte;
					open_lin_slave_state_data_count ++;
				} else
				{
					/* checksum calculation */
					if (rx_byte == open_lin_data_layer_checksum(open_lin_data_layer_frame.pid,
							open_lin_data_layer_frame.lenght, open_lin_slave_data_buff))
					{
						/* valid checksum, copy frame from internal buffer*/
						open_lin_memcpy(open_lin_data_layer_frame.data_ptr,open_lin_slave_data_buff,open_lin_data_layer_frame.lenght);
						open_lin_net_rx_handler(open_lin_data_layer_frame.pid);
					} else
					{
						open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_INVALID_CHECKSUM);
					}
					open_lin_slave_reset();
				}
				break;
			}
			default:
				open_lin_slave_reset();
				open_lin_error_handler(OPEN_LIN_SLAVE_ERROR_INVALID_DATA_RX);
				break;
		}
	}
}
