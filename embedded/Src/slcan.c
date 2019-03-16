/*
 * slcan_interface.c
 *
 *  Created on: Apr 2, 2016
 *      Author: Vostro1440
 */

#include "slcan.h"

#include <stdbool.h>
#include <string.h>
#include <sys/_stdint.h>

#include "usbd_cdc_if.h"
#include "stm32f0xx_hal.h"
#include "lin_slcan.h"

#define SLCAN_BELL 7
#define SLCAN_CR 13
#define SLCAN_LR 10

extern int32_t serialNumber;

void RebootToBootloader();
uint8_t slcan_state = SLCAN_STATE_CONFIG;
LinType_t lin_type = LIN_MONITOR;
static uint8_t terminator = SLCAN_CR;

extern USBD_HandleTypeDef hUsbDeviceFS;

uint8_t sl_frame[LINE_MAXLEN];
uint8_t sl_frame_len=0;
/**
  * @brief  Adds data to send buffer
  * @param  c - data to add
  * @retval None
  */
static void slcanSetOutputChar(uint8_t c)
{
	if (sl_frame_len < sizeof(sl_frame))
	{
		sl_frame[sl_frame_len] = c;
		sl_frame_len ++;
	}
}

/**
  * @brief  Add given nible value as hexadecimal string to bufferr
  * @param  c - data to add
  * @retval None
  */
static void slCanSendNibble(uint8_t ch)
{
	ch = ch > 9 ? ch - 10 + 'A' : ch + '0';
	slcanSetOutputChar(ch);
}

/**
  * @brief  Add given byte value as hexadecimal string to buffer
  * @param  value - data to add
  * @retval None
  */
static void slcanSetOutputAsHex(uint8_t ch) {
	slCanSendNibble(ch >> 4);
	slCanSendNibble(ch & 0x0F);
}

static void slcanOutputFlush(void)
{
	while (((USBD_CDC_HandleTypeDef*)hUsbDeviceFS.pClassData)->TxState){;} //should change by hardware
	while (CDC_Transmit_FS(sl_frame, sl_frame_len) != USBD_OK);
    sl_frame_len = 0;
}

void slCanHandler(uint8_t time_passed_ms)
{
    if (slcan_state == SLCAN_STATE_OPEN)
    {
        if (lin_type == LIN_MASTER)
        	open_lin_master_dl_handler(time_passed_ms);
    }
}

/**
  * @brief  Add to input buffer data from interfaces
  * @param  ch - data to add
  * @retval None
  */
static uint8_t command[LINE_MAXLEN];
int slCanProccesInput(uint8_t ch)
{
	static uint8_t line[LINE_MAXLEN];
	static uint8_t linepos = 0;

    if (ch == SLCAN_CR) {
        line[linepos] = 0;
        memcpy(command,line,linepos);
        linepos = 0;
        return 1;
    } else if (ch != SLCAN_LR) {
        line[linepos] = ch;
        if (linepos < LINE_MAXLEN - 1) linepos++;
    }
    return 0;
}


/**
  * @brief  Parse hex value of given string
  * @param  canmsg - line Input string
  * 		len    - of characters to interpret
  * 		value  - Pointer to variable for the resulting decoded value
  * @retval 0 on error, 1 on success
  */
uint8_t parseHex(uint8_t* line, uint8_t len, uint32_t* value) {
    *value = 0;
    while (len--) {
        if (*line == 0) return 0;
        *value <<= 4;
        if ((*line >= '0') && (*line <= '9')) {
           *value += *line - '0';
        } else if ((*line >= 'A') && (*line <= 'F')) {
           *value += *line - 'A' + 10;
        } else if ((*line >= 'a') && (*line <= 'f')) {
           *value += *line - 'a' + 10;
        } else return 0;
        line++;
    }
    return 1;
}


/**
 * @brief  Interprets given line and transmit can message
 * @param  line Line string which contains the transmit command
 * @retval HAL status
 */
static uint8_t transmitStd(uint8_t* line) {
    uint32_t temp;
    open_lin_frame_slot_t slot;
    uint8_t data_buff[8];
    uint8_t offset = 0;

    bool lin_data = ((line[0] == 't') || (line[0] == 'T'));

    slot.data_ptr = data_buff;
    if (line[0] < 'Z')
		offset = 5;
    // id
    if (!parseHex(&line[2 + offset], 2, &temp)) return 0;
    	slot.pid = open_lin_data_layer_parity((open_lin_pid_t)temp); // add parity
    // len
    if (!parseHex(&line[4 + offset], 1, &temp)) return 0;
    slot.data_length = temp;

    if (slot.data_length > 8) return 0;
    if (lin_data)
    {
        uint8_t i;
        for (i = 0; i < slot.data_length; i++) {
            if (!parseHex(&line[5 + offset + i*2], 2, &temp)) return 0;
            slot.data_ptr[i] = temp;
        }
    }

    if (offset == 0)
    {
    	open_lin_master_data_tx_header(&slot);
    }
    if (lin_data)
    {
    	open_lin_master_data_tx_data(&slot);
    }
    /* set data recepcion state machine */
	lin_slcan_skip_header_reception(slot.pid);

    return 1;
}


/**
 * @brief  Parse given command line
 * @param  line Line string to parse
 * @retval None
 */
extern void MX_USART1_UART_Init(void);
extern uint32_t lin_baund_rate;

void slCanCheckCommand()
{
	uint8_t result = SLCAN_BELL;
	uint8_t *line = command;

    switch (line[0]) {
    	case 0:
    		return;
    	case 'a':
    	{
    		if (terminator == SLCAN_CR)
    			terminator = SLCAN_LR;
    		else
    			terminator = SLCAN_CR;
    		result = terminator;
    		break;
    	}
        case 'S':
        case 'G':
        case 'W':
        case 's':
        	if (line[0] == '2')
        	{
        		lin_baund_rate = 9600;
        	} else
        	{
        		lin_baund_rate = 19200;

        	}
        	MX_USART1_UART_Init();
        	open_lin_hw_reset();

        case 'F': // Read status flags
      		result = terminator;
            break;
        case 'V': // Get hardware version
            {
                slcanSetOutputChar('V');
                slcanSetOutputAsHex(VERSION_HARDWARE_MAJOR);
                slcanSetOutputAsHex(VERSION_HARDWARE_MINOR);
                result = terminator;
            }
            break;
        case 'v': // Get firmware version
            {
                slcanSetOutputChar('v');
                slcanSetOutputAsHex(VERSION_FIRMWARE_MAJOR);
                slcanSetOutputAsHex(VERSION_FIRMWARE_MINOR);
                result = terminator;
            }
            break;
        case 'N': // Get serial number
            {
                slcanSetOutputChar('N');
                slcanSetOutputAsHex((uint8_t)(serialNumber));
                slcanSetOutputAsHex((uint8_t)(serialNumber>>8));
                slcanSetOutputAsHex((uint8_t)(serialNumber>>16));
                slcanSetOutputAsHex((uint8_t)(serialNumber>>24));
                result = terminator;
            }
            break;
        case 'o':  // master mode
        case 'O':
            if (slcan_state == SLCAN_STATE_CONFIG)
            {
                lin_type = LIN_MASTER;
                result = terminator;
            }
            break;
        case 'L': // slave mode
        	 if (slcan_state == SLCAN_STATE_CONFIG){
        		 result = terminator;
				 lin_type = LIN_SLAVE;
				 slcan_state = SLCAN_STATE_OPEN;
				 open_lin_hw_reset();
				 lin_slcan_reset();
        	 }
        case 'l':  // monitor
            if (slcan_state == SLCAN_STATE_CONFIG)
            {
				result = terminator;
                lin_type = LIN_MONITOR;
                slcan_state = SLCAN_STATE_OPEN;
            	open_lin_hw_reset();
            	lin_slcan_reset();
            }
            break;

        case 'C': // Close LIN channel
            slcan_state = SLCAN_STATE_CONFIG;
            result = terminator;
            lin_type = LIN_MASTER;
            break;

        case 'R':
        case 'r': // Transmit header
        case 'T':
        case 't': // Transmit full frame
        	switch (lin_type)
        	{
				case LIN_MASTER:
				case LIN_SLAVE:
	                if (addLinMasterRow(line) == 1){
	                	if (line[0] < 'Z') slcanSetOutputChar('Z');
	                	else slcanSetOutputChar('z');
	                }
	                result = terminator;
					break;
				case LIN_MONITOR:
	                if (slcan_state == SLCAN_STATE_OPEN)
	                {
	                    if (transmitStd(line) == 1) {
	                        if (line[0] < 'Z') slcanSetOutputChar('Z');
	                        else slcanSetOutputChar('z');
	                        result = terminator;
	                    }
	                }
					break;
				default:
					break;
        	}
            break;
    }

    if ((line[0] == 'b') && (line[1] == 'o') && (line[2] == 'o') && (line[3] == 't'))
    {
    	RebootToBootloader();
    }

   line[0] = 0;
   slcanSetOutputChar(result);
   slcanOutputFlush();
}


/**
 * @brief  reciving CAN frame
 * @param  canmsg Pointer to can message
 * 			step Current step
 * @retval Next character to print out
 */
uint8_t slcanReciveCanFrame(open_lin_frame_slot_t *pRxMsg)
{
	uint8_t i;
	open_lin_pid_t pid;

    slcanSetOutputChar('t');

    pid = pRxMsg->pid & 0x3F;

    slCanSendNibble(0); // for slcan compatibility
    slcanSetOutputAsHex(pid);
	slCanSendNibble(pRxMsg->data_length);
	if (pRxMsg->data_length > 0)
	{
		for (i = 0;  i != pRxMsg->data_length; i ++)
		{
			slcanSetOutputAsHex(pRxMsg->data_ptr[i]);
		}
	}
	slcanSetOutputChar(terminator);
	slcanOutputFlush();
	return 0;
}
