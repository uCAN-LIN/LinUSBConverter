#include "catch.hpp"

extern "C"{

#include "../../open_lin_cfg.h"
#include "../../open_lin_data_layer.h"
#include "../../open_lin_hw.h"
#include "../../open_lin_network_layer.h"
#include "../../open_lin_master_data_layer.h"

extern uint8_t* get_last_tx();
extern uint8_t get_last_tx_index();
extern t_open_lin_error get_and_clear_sim_error();
}

uint8_t master_data_buffer[8];
const t_master_frame_table_item master_frame_table[] = {
		{10,25,{0x01,OPEN_LIN_FRAME_TYPE_RECEIVE,0x08,master_data_buffer}}
};
const uint8_t table_size = sizeof(master_frame_table)/sizeof(t_master_frame_table_item);


TEST_CASE("handler call on not initilized master", "[open_lin_master]" ){
	open_lin_master_dl_handler(10);
}


TEST_CASE("init and work with one item table", "[open_lin_master]" ){

	get_last_tx_index();
	get_and_clear_sim_error();

	open_lin_master_dl_init((t_master_frame_table_item *)master_frame_table,table_size);
	open_lin_master_dl_handler(1);
	CHECK(get_last_tx_index() == 0);
	open_lin_master_dl_handler(10);
	CHECK(get_last_tx_index() == 3);
	CHECK((get_last_tx()[2]) == 0x01); // check for PID
	open_lin_master_dl_handler(10);
	CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
	open_lin_master_dl_handler(16);
	CHECK(get_and_clear_sim_error() == OPEN_LIN_MASTER_ERROR_DATA_RX_TIMEOUT);
	open_lin_master_dl_handler(11);
	CHECK(get_last_tx_index() == 3);
	CHECK((get_last_tx()[2]) == 0x01); // check for PID
}

uint8_t master_data_buffer_tx_1[] = {0xAA,0xBB};
uint8_t master_data_buffer_rx_1[1];
const t_master_frame_table_item master_frame_table2[] = {
		{10,0,{0x02,OPEN_LIN_FRAME_TYPE_TRANSMIT,0x02,master_data_buffer_tx_1}},
		{20,25,{0x03,OPEN_LIN_FRAME_TYPE_RECEIVE,0x01,master_data_buffer_rx_1}}
};
const uint8_t table_size2 = sizeof(master_frame_table2)/sizeof(t_master_frame_table_item);

TEST_CASE("init and work with multiple items table, invalid checksum rx", "[open_lin_master]" ){
	get_last_tx_index();
	get_and_clear_sim_error();

	open_lin_master_dl_init((t_master_frame_table_item *)master_frame_table2,table_size2);
	open_lin_master_dl_handler(11);
	CHECK(get_last_tx_index() == 6);
	CHECK(((get_last_tx()[3] == 0xAA) && (get_last_tx()[4] == 0xBB)));
	CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
	open_lin_master_dl_handler(21);
	CHECK(get_last_tx_index() == 3);
	CHECK((get_last_tx()[2] == 0x03));
	open_lin_master_dl_rx(0x05);
	open_lin_master_dl_rx(0x06);
	CHECK(get_and_clear_sim_error() == OPEN_LIN_MASTER_ERROR_CHECKSUM);
}

TEST_CASE("init and work with multiple items table, valid checksum rx", "[open_lin_master]" ){
	extern open_lin_frame_slot_t* last_rx_slot;

	get_last_tx_index();
	get_and_clear_sim_error();

	open_lin_master_dl_init((t_master_frame_table_item *)master_frame_table2,table_size2);
	open_lin_master_dl_handler(11);
	CHECK(get_last_tx_index() == 6);
	CHECK(((get_last_tx()[3] == 0xAA) && (get_last_tx()[4] == 0xBB)));
	CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
	open_lin_master_dl_handler(21);
	CHECK(get_last_tx_index() == 3);
	CHECK((get_last_tx()[2] == 0x03));
	open_lin_master_dl_rx(0x05);
	open_lin_master_dl_rx(0xF7);
	CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
	CHECK(last_rx_slot->pid == 0x03);
	CHECK(last_rx_slot->data_ptr[0] == 0x05);
}


