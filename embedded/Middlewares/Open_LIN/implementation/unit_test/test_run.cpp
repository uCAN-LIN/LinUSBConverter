#define CATCH_CONFIG_MAIN  // This tells Catch to provide a main() - only do this in one cpp file
#include "catch.hpp"
#include "iostream"

extern "C"{

#include "../../open_lin_cfg.h"
#include "../../open_lin_data_layer.h"
#include "../../open_lin_slave_data_layer.h"
#include "../../open_lin_hw.h"
#include "../../open_lin_network_layer.h"

extern l_u8 open_lin_frame_parity(l_u8 pid);
extern void open_lin_frame_byte_process(l_u8 rx_byte);

l_u8 dataBuffer1[] = {0,0,0,0};
l_u8 dataBuffer2[] = {0,1,2,3,4,5,6,7};

open_lin_frame_slot_t slot_array[] =
{
		{0x12,OPEN_LIN_FRAME_TYPE_RECEIVE,sizeof(dataBuffer1),dataBuffer1},
		{0x01,OPEN_LIN_FRAME_TYPE_TRANSMIT,sizeof(dataBuffer2),dataBuffer2}
};

const l_u8 lenght_of_slot_array = sizeof( slot_array ) / sizeof( open_lin_frame_slot_t );


}

TEST_CASE( "calc_parity", "[open_lin_data_layer]" ) {

	uint16_t id = open_lin_data_layer_parity(0x80);
	INFO("PID " << std::hex << id);
	CHECK(open_lin_data_layer_parity(0x80) == 0x80);
	CHECK(open_lin_data_layer_parity(0) == 0x80);
	CHECK(open_lin_data_layer_parity(12) == 0x4c);
}

TEST_CASE("calc_checksum", "[open_lin_data_layer]" ) {

	t_open_lin_data_layer_frame frame;
	l_u8 data[] = {0x22,0xAA} ;
	frame.lenght = sizeof(data);
	frame.data_ptr = data;
	frame.pid = 0x15;
	CHECK((uint16_t)open_lin_data_layer_checksum(frame.pid,frame.lenght,frame.data_ptr) == (uint16_t)0xDD);

	l_u8 data2[] = {0x11} ;
	frame.lenght = sizeof(data2);
	frame.data_ptr = data2;
	frame.pid = 0x01;
	CHECK((uint16_t)open_lin_data_layer_checksum(frame.pid,frame.lenght,frame.data_ptr) == (uint16_t)0x2D);
}

extern "C"{

extern l_bool sim_break;
extern t_open_lin_error get_and_clear_sim_error();

}

TEST_CASE("slave break detection", "[open_lin_slave]" ) {
	open_lin_net_init(slot_array,lenght_of_slot_array);
	open_lin_slave_reset();
	/* first brake ok */
//	SECTION( "sec brake cause err wait for sync" ){
		sim_break = true;
		open_lin_slave_rx_header(0);
		{
			CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
		}
//	}

//	SECTION( "sec brake cause err wait for sync" ){
		sim_break = true;
		open_lin_slave_rx_header(0);
		CHECK(get_and_clear_sim_error() == OPEN_LIN_SLAVE_ERROR_INVALID_BREAK);

		sim_break = true;
		open_lin_slave_rx_header(0);
		CHECK(get_and_clear_sim_error() == OPEN_LIN_SLAVE_ERROR_INVALID_BREAK);
//	}

//	SECTION( "sync no err" ){
		sim_break = false;
		open_lin_slave_rx_header(0x55);
		CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
//	}
}

TEST_CASE("reset test", "[open_lin_slave]" ) {
	open_lin_slave_reset();
	sim_break = true;
	open_lin_slave_rx_header(0);
	CHECK(get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);
}

l_bool tx_invalid = false;
l_bool tx_done = true;

extern l_u8 dataBuffer2[8];

l_bool open_lin_hw_tx_data(l_u8* data, l_u8 len){
	if (sizeof(dataBuffer2) == len)
	{
		if (memcmp(data,dataBuffer2,len) != 0)
		{
			tx_invalid = true;
		}

	} else
	{
		if (len == 1)
		{
			// checksum
			if (data[0] != 0x22)
			{
				tx_invalid = true;
			} else
			{
				tx_done = true;
			}
		} else
		{
			tx_invalid = true;
		}
	}
	return true;
}

TEST_CASE("valid frame reception, tx header", "[open_lin_slave]" ) {
	open_lin_slave_reset();
	sim_break = true;
	open_lin_slave_rx_header(0);
	open_lin_slave_rx_header(0x55);
	open_lin_slave_rx_header(0xC1);
	CHECK(tx_invalid == false);
	CHECK(tx_done == true);
}

TEST_CASE("valid frame reception, rx header invalid checksum", "[open_lin_slave]" ) {
	open_lin_slave_reset();
	sim_break = true;
	open_lin_slave_rx_header(0);
	open_lin_slave_rx_header(0x55);
	open_lin_slave_rx_header(0x92); // 0x01

	open_lin_slave_rx_header(0x00);
	open_lin_slave_rx_header(0x01);
	open_lin_slave_rx_header(0x02);
	open_lin_slave_rx_header(0x03);
	open_lin_slave_rx_header(0x22);

	CHECK (get_and_clear_sim_error() == OPEN_LIN_SLAVE_ERROR_INVALID_CHECKSUM);
}

TEST_CASE("valid frame reception, rx header valid checksum", "[open_lin_slave]" )
{
	open_lin_slave_reset();
	sim_break = true;
	open_lin_slave_rx_header(0);
	open_lin_slave_rx_header(0x55);
	open_lin_slave_rx_header(0x92); // 0x01

	open_lin_slave_rx_header(0x00);
	open_lin_slave_rx_header(0x01);
	open_lin_slave_rx_header(0x02);
	open_lin_slave_rx_header(0x03);
	open_lin_slave_rx_header(0x67);

	extern l_u8 dataBuffer1[4];
	l_u8 e_dataBuffer1[4] = {0,1,2,3};
	CHECK (get_and_clear_sim_error() == OPEN_LIN_NO_ERROR);

	CHECK(memcmp(dataBuffer1,e_dataBuffer1,sizeof(e_dataBuffer1)) == 0);
}


