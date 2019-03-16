#ifndef SLCAN_H_
#define SLCAN_H_

#include "stdint.h"

#include "open_lin_cfg.h"
#include "open_lin_data_layer.h"
#include "open_lin_master_data_layer.h"
#include "open_lin_network_layer.h"
#include "open_lin_hw.h"
#include "open_lin_slave_data_layer.h"

#define VERSION_FIRMWARE_MAJOR 1
#define VERSION_FIRMWARE_MINOR 2

#define VERSION_HARDWARE_MAJOR 0
#define VERSION_HARDWARE_MINOR 1

#define LINE_MAXLEN 62
#define MAX_SLAVES_COUNT 16
#define LIN_SLAVE_SIGNALS 5

#define SLCAN_STATE_CONFIG 0
#define SLCAN_STATE_OPEN 2

extern uint8_t slcan_state;

void slcanClose();
uint8_t slcanReciveCanFrame(open_lin_frame_slot_t *pRxMsg);
int slCanProccesInput(uint8_t ch);
void slCanCheckCommand();
void slCanHandler(uint8_t time_passed_ms);

uint8_t parseHex(uint8_t* line, uint8_t len, uint32_t* value) ;

typedef enum {
    LIN_MASTER,
    LIN_MONITOR,
	LIN_SLAVE
} LinType_t ;

extern LinType_t lin_type;


#endif /* SLCAN_H_ */
