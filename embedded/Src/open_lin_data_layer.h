/**
 * @file open_lin_frame.h
 * @author LJ
 * @date 25.01.2018
 * @brief LIN data layer definition
 *
 */

#ifndef OPEN_LIN_OPEN_LIN_DATA_LAYER_H_
#define OPEN_LIN_OPEN_LIN_DATA_LAYER_H_

#include "open_lin_types.h"

/**
 * @brief LIN frame structure definition
 */
typedef struct {
	open_lin_pid_t pid; /**< frame identifier field t_open_lin_frame#pid. */
	l_u8 lenght;
	l_u8* data_ptr;
	open_lin_checksum_t checksum;
} t_open_lin_data_layer_frame;

extern open_lin_pid_t open_lin_data_layer_parity(open_lin_pid_t pid);
extern open_lin_checksum_t open_lin_data_layer_checksum(open_lin_pid_t pid, l_u8 lenght,const l_u8* data_ptr);

#endif /* OPEN_LIN_OPEN_LIN_DATA_LAYER_H_ */
