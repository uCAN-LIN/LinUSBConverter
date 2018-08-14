/*
 * lin_slcan.h
 *
 *  Created on: 10.02.2018
 *      Author: ay7vi2
 */

#ifndef LIN_SLCAN_H_
#define LIN_SLCAN_H_

t_master_frame_table_item* slcan_get_master_table_row(open_lin_pid_t id, uint8_t* out_index);
uint8_t addLinMasterRow(uint8_t* line);
void lin_slcan_rx(l_u8 rx_byte);
void lin_slcan_rx_timeout_handler();
void lin_slcan_skip_header_reception(uint8_t pid);
void lin_slcan_reset(void);
#endif /* LIN_SLCAN_H_ */
