/*
 * open_lin_frame_st32.c
 *
 *  Created on: 25.01.2018
 *      Author: ay7vi2
 */

#include <open_lin_data_layer.h>
#include "../../open_lin_types.h"
#include "../../open_lin_network_layer.h"
#include "../../open_lin_hw.h"
#include "../../../../Src/slcan.h"
#include <stm32f0xx_hal.h>
#include <stm32f0xx_hal_uart_ex.h>
#include <stm32f0xx_hal_uart.h>

extern UART_HandleTypeDef huart1;

void open_lin_error_handler(t_open_lin_error error_code)
{
	/* no error handling */
}

l_bool open_lin_hw_check_for_break(void)
{
	l_bool result = __HAL_UART_GET_FLAG(&huart1,UART_FLAG_LBDF);
	if (result == true)
		__HAL_UART_CLEAR_FLAG(&huart1,UART_CLEAR_LBDF);
	return result;
}

void open_lin_frame_set_auto_baud(void)
{
	//	UART_AUTOBAUD_REQUEST
}

void open_lin_hw_reset(void) {

}

l_bool open_lin_hw_tx_break(void){
	HAL_LIN_SendBreak(&huart1);

	return true;
}

l_bool open_lin_hw_tx_data(l_u8* data, l_u8 len)
{
	HAL_UART_Transmit(&huart1,data,len,1000);
//	add buffers to use
//	HAL_UART_Transmit_IT(huart1,data,len);
	return true;
}

void open_lin_on_rx_frame(open_lin_frame_slot_t *slot)
{

}

void open_lin_master_dl_rx_callback(open_lin_frame_slot_t* slot)
{
	slcanReciveCanFrame(slot);
}
