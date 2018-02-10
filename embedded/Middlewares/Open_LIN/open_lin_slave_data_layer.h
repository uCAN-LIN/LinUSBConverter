/**
 * @file open_lin_types.h
 * @brief LIN types declaration according to LIN Specification Package
 */
#ifndef OPEN_LIN_SLAVE_DATA_LAYER_H_
#define OPEN_LIN_SLAVE_DATA_LAYER_H_

#include "open_lin_types.h"

typedef enum {
	OPEN_LIN_SLAVE_IDLE,
	OPEN_LIN_SLAVE_SYNC_RX,
	OPEN_LIN_SLAVE_PID_RX,
	OPEN_LIN_SLAVE_DATA_RX,
	OPEN_LIN_SLAVE_DATA_TX
} t_open_lin_slave_state;

/**
 * @brief Init LIN slave component
 */
void open_lin_slave_init(void);

/**
 * @brief Reset LIN slave component
 */
void open_lin_slave_reset(void);

/**
 * @brief byte reception handler function
 * @param rx_byte
 */
void open_lin_slave_rx_header(l_u8 rx_byte);

#endif /* OPEN_LIN_SLAVE_DATA_LAYER_H_ */
