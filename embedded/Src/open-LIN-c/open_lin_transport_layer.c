/**
 * @file open_lin_transport_layer.c
 * @brief LIN transport layer implementation
 */

#include "open_lin_transport_layer.h"
#include "open_lin_network_layer.h"

#ifdef OPEN_LIN_TRANSPORT_LAYER

extern open_lin_NAD_t open_lin_NAD;
extern l_u16 open_lin_supplier_id;
extern l_u16 open_lin_function_id;
extern void open_lin_sid_callback(open_lin_frame_slot_t* slot);

typedef struct {
	open_lin_SID_t sid;
	void (*handler)(open_lin_frame_slot_t* slot);
} t_open_lin_sid_handler_item;


/* static function definitions */
static void open_lin_assign_nad_handler(open_lin_frame_slot_t* slot);

/* static service handlers */
t_open_lin_sid_handler_item open_lin_sid_handlers[] = {
		{OPEN_LIN_SID_ASSIGN_NAD,open_lin_assign_nad_handler}
};

/* assign NAD service implementation */
static void open_lin_assign_nad_handler(open_lin_frame_slot_t* slot)
{
	t_open_lin_sf_request* t_request = (t_open_lin_sf_request*)(slot->data_ptr);

#ifdef PLATFORM_IS_BIG_ENDIAN
		uint16_t sup = (t_request->data[1]) | (((uint16_t)t_request->data[0]) << 8);
		uint16_t fun = (t_request->data[3]) | (((uint16_t)t_request->data[2]) << 8);
#else
		uint16_t sup = (t_request->data[1]) | (((uint16_t)t_request->data[0]) << 8);
		uint16_t fun = (t_request->data[3]) | (((uint16_t)t_request->data[2]) << 8);
#endif

	if ((open_lin_supplier_id == sup) && (open_lin_function_id == fun))
	{
		/* update NAD */
		open_lin_NAD = t_request->data[4];
	} else {
		/* invalid id, this device is not addressed do nothing */
	}
}


static void open_lin_transport_layer_request_handling(open_lin_frame_slot_t* slot)
{
	t_open_lin_sf_request* t_request = (t_open_lin_sf_request*)(slot->data_ptr);
	switch (t_request->pci.PCI_type)
	{
		case (OPEN_LIN_PCI_SF):
			if ((t_request->nad == open_lin_NAD) || (t_request->nad == OPEN_LIN_NAD_BROADCAST))
			{
				uint8_t i = 0;
				for (i = 0; i < (sizeof(open_lin_sid_handlers)/sizeof(open_lin_sid_handlers[0])); i++)
				{
					if (open_lin_sid_handlers[i].sid == t_request->sid)
					{
						/* call handler */
						open_lin_sid_handlers[i].handler(slot);
                        open_lin_sid_callback(slot); 
					} else {
						/* do nothing, go to next handler */
					}
				}
			} else
			{
				/* different NAD */
			}
		break;
		/* TODO implement segmentation*/
		default:
        #ifdef __XC8 /* welcome to beautiful world of XC8 compilers, -- compiler bug*/
            t_request->pci.PCI_type ++;
            t_request->pci.PCI_type --;
        #endif
			/* unknown pci type */
		break;
	}
}

void open_lin_transport_layer_handle(open_lin_frame_slot_t *slot)
{
	switch (slot->pid)
	{
		case OPEN_LIN_DIAG_REQUEST:
			open_lin_transport_layer_request_handling(slot);
		break;

		case OPEN_LIN_DIAG_RESPONSE:

		break;

		default:
			/* do nothing */
		break;
	}
}

#endif
