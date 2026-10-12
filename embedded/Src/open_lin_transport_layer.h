/**
 * @file open_lin_transport_layer.h
 * @brief LIN transport layer definition
 */
#ifndef OPEN_LIN_TRANSPORT_LAYER_H_
#define OPEN_LIN_TRANSPORT_LAYER_H_

#include "open_lin_types.h"
#include "open_lin_network_layer.h"

#ifdef OPEN_LIN_TRANSPORT_LAYER

typedef l_u8 open_lin_NAD_t;
typedef l_u8 open_lin_SID_t;

typedef enum {
	OPEN_LIN_SID_ASSIGN_NAD = 0xB0,
	OPEN_LIN_SID_READ_BY_ID = 0xB2,
	OPEN_LIN_SID_CONDITIONAL_CHANGE_NAD = 0xB3,
	OPEN_LIN_SID_DUMP_DATA = 0xB4,
	OPEN_LIN_SID_SAVED_CONFIGURATION = 0xB6,
	OPEN_LIN_SID_ASSIGN_FRAME_ID_RANGE = 0xB7
}open_lin_SID_enum_t;

typedef struct {
	l_u8 additional: 4;
	l_u8 PCI_type : 4;
} open_lin_PCI_t;

typedef enum {
	OPEN_LIN_PCI_SF = 0,
	OPEN_LIN_PCI_FF = 1,
	OPEN_LIN_PCI_CF = 2
} t_open_lin_pci_type;

typedef enum {
	OPEN_LIN_NAD_SLEEP = 0x00,
	OPEN_LIN_NAD_FUNCTIONAL = 0x7E,
	OPEN_LIN_NAD_BROADCAST = 0x7F
} t_open_lin_nad_type;

typedef struct {
	open_lin_NAD_t nad;
	open_lin_PCI_t pci;
	open_lin_SID_t sid;
	l_u8 data[5];
} t_open_lin_sf_request;

typedef struct {
	open_lin_NAD_t nad;
	open_lin_PCI_t pci;
	l_u8 rsid;
	l_u8 data[5];
} t_open_lin_sf_response;

void open_lin_transport_layer_handle(open_lin_frame_slot_t *slot);


#endif /* OPEN_LIN_TRANSPORT_LAYER */

#endif /* OPEN_LIN_TRANSPORT_LAYER_H_ */


