#include "../../open_lin_cfg.h"
#include "../../open_lin_data_layer.h"
#include "../../open_lin_hw.h"
#include "../../open_lin_network_layer.h"
#include "../../open_lin_master_data_layer.h"

#include <stdio.h>
#include <synchapi.h>

int cport_nr=13;        /* /dev/ttyS0 (COM5 on windows) */

uint8_t master_data_buffer_tx_1[] = {0xAA};
uint8_t master_data_buffer_rx_1[1];
const t_master_frame_table_item master_frame_table[] = {
		{10,1,{0x23,OPEN_LIN_FRAME_TYPE_TRANSMIT,sizeof(master_data_buffer_tx_1),master_data_buffer_tx_1}},
		{25,25,{0x22,OPEN_LIN_FRAME_TYPE_RECEIVE,sizeof(master_data_buffer_rx_1),master_data_buffer_rx_1}}
};
const uint8_t table_size = sizeof(master_frame_table)/sizeof(t_master_frame_table_item);

void open_lin_on_rx_frame(open_lin_frame_slot_t *slot){
	printf("NOT USED IN MASTER SHOULD BE FIXED!");
}

void open_lin_master_dl_rx_callback(open_lin_frame_slot_t* slot)
{
	printf("LIN(%d)>", slot->pid);
	for (int i = 0; i < slot->data_length; i++)
	{
		printf(" %d",slot->data_ptr[i]);
	}
	printf("\n");
}

void rx_byte_handle(uint8_t byte)
{
	open_lin_master_dl_rx(byte);
}

int main()
{
	setbuf(stdout, NULL);
	printf("Open-LIN master example\n");

	open_lin_hw_init();
	open_lin_master_dl_init((t_master_frame_table_item *)master_frame_table,table_size);

	while (1)
	{
		Sleep(1);
		open_lin_master_dl_handler(1);
	}

	return 1;
}
