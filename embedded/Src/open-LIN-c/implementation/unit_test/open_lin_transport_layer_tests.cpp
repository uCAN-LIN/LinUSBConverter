/*
 * open_lin_transport_layer_tests.cpp
 *
 *  Created on: 21 cze 2018
 *      Author: ay7vi2
 */



#include "catch.hpp"
#include "iostream"

extern "C"{

#include "../../open_lin_cfg.h"
#include "../../open_lin_master_data_layer.h"
#include "../../open_lin_transport_layer.h"

open_lin_NAD_t open_lin_NAD = 0;
uint16_t open_lin_supplier_id = 0x1234;
uint16_t open_lin_function_id = 0x5678;
}
/* frame from Table 4.7 LIN spec 2.1 */
uint8_t request_data_1[] = {OPEN_LIN_NAD_BROADCAST, 0x06,0xB0,0x12,0x34,0x56,0x78,0x34};

open_lin_frame_slot_t slot_1 = {OPEN_LIN_DIAG_REQUEST, OPEN_LIN_FRAME_TYPE_TRANSMIT, 8, request_data_1};

TEST_CASE("change NAD test", "[open_lin_transport_layer]"){
	open_lin_NAD = 0;
	open_lin_transport_layer_handle(&slot_1);
	CHECK(open_lin_NAD == 0x34);
}


