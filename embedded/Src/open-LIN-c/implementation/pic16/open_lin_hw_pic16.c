/*
 * open_lin_frame_st32.c
 *
 *  Created on: 25.01.2018
 *      Author: ay7vi2
 */

#include "../../open_lin_data_layer.h"
#include "../../open_lin_types.h"
#include "../../open_lin_network_layer.h"
#include "../../open_lin_hw.h"
#include "../../open_lin_transport_layer.h"

#include "../../../mcc_generated_files/mcc.h"
#include "../../../mcc_generated_files/eusart1.h"

#define LIN_EUSART_DataReady    EUSART1_DataReady
#define LIN_EUSART_Read         EUSART1_Read
#define LIN_EUSART_Write        EUSART1_Write
#define LIN_TXIE                TX1IE
#define LIN_RCIE                RC1IE

#define LIN_TRMT                TX1STAbits.TRMT
#define LIN_CREN                RC1STAbits.CREN
#define LIN_SENDB               TX1STAbits.SENDB
#define LIN_FERR                RC1STAbits.FERR

//Device Timer
#define LIN_WriteTimer          TMR0_WriteTimer
#define LIN_StartTimer          NOP
#define LIN_StopTimer           NOP
#define LIN_SetInterruptHandler TMR0_SetInterruptHandler

open_lin_NAD_t open_lin_NAD = 0;
uint16_t open_lin_supplier_id = 0x0;
uint16_t open_lin_function_id = 0x0;

void open_lin_error_handler(t_open_lin_error error_code)
{
	/* no error handling */
}

l_bool open_lin_hw_check_for_break(void)
{
	l_bool result = false;
    
    if(LIN_FERR == 1){
        LIN_EUSART_Read();
        result = true;
    }
    
	return result;
}

void open_lin_frame_set_auto_baud(void)
{
	//	UART_AUTOBAUD_REQUEST
}

void open_lin_hw_reset(void) {
	open_lin_hw_check_for_break();
    
}


void open_lin_set_rx_enabled(l_bool v)
{
	if (v == l_true)
	{
		open_lin_hw_reset();
	} else
	{
        LIN_CREN = 1;
        LIN_RCIE = 1;
	}
}

l_bool open_lin_hw_tx_byte(l_u8 byte){

	LIN_EUSART_Write(byte);
    return true;

}

l_bool open_lin_hw_tx_data(l_u8* data, l_u8 len)
{
    
    for (uint8_t i = 0; i < len; i ++)
    {
        open_lin_hw_tx_byte(data[i]);
    }
    return true;
}

