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

#include "rs232.h"
#include <pthread.h>


extern int cport_nr;

unsigned char str[512] = {0};
int send_index = 0;
unsigned char gl_buf[4096] = {0};
volatile bool breakFlag = false;
pthread_t tid;

void open_lin_error_handler(t_open_lin_error error_code)
{
	printf("Open-LIN err %d \n", error_code);
	/* no error handling */
}

l_bool rx_enabled = false;

void open_lin_set_rx_enabled(l_bool status)
{
	rx_enabled = status;
	RS232_flushRX(cport_nr);
}

l_bool open_lin_hw_check_for_break(void)
{
	l_bool result = false;
	result = breakFlag;
	breakFlag = false;
	return result;
}

l_bool open_lin_hw_tx_break(void){
	RS232_setBreak(cport_nr);
	Sleep(2);
	RS232_clearBreak(cport_nr);
//	open_lin_hw_tx_byte(0);
	return TRUE;
}

void open_lin_frame_set_auto_baud(void)
{

}

l_bool open_lin_hw_tx_byte(l_u8 byte)
{
	RS232_SendByte(cport_nr, byte);
	return true;
}

l_bool open_lin_hw_tx_data(l_u8* data, l_u8 len)
{
	for (int i = 0; i < len; i++)
	{
		open_lin_hw_tx_byte(data[i]);
	}
	return true;
}

void open_lin_hw_reset(void) {
	RS232_flushRXTX(cport_nr);
}
extern void rx_byte_handle(uint8_t byte);
static unsigned char buf[64];
void *rxDataThread(void *vargp)
{

	int size = sizeof(buf);
	int out_break = 0;
	int out_size = 0;

	while (1)
	{
		if (rx_enabled == true)
		{
			out_size = RS232_PollComportEx(cport_nr,buf,size,&out_break);
			breakFlag = out_break;
			for (int i = 0; i < out_size; i++)
			{
				rx_byte_handle(buf[i]);
			}
		} else {
			Sleep(1);
		}
	}
	return NULL;
}


void open_lin_hw_init(void)
{
	int bdrate=19200;

	char mode[]={'8','N','1',0};

	if(RS232_OpenComport(cport_nr, bdrate, mode))
	{
		printf("Can not open comport\n");
	}
	send_index  = 0;
	pthread_create(&tid, NULL, rxDataThread, NULL);
}


