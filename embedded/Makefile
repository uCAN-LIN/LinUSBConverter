# Command-line firmware build, used by CI.
# Same sources and flags as the STM32CubeIDE project in TrueSTUDIO/LUCEmbedded.
#
#   make            -> build/LUCEmbedded.elf, .bin, .map
#   make clean

TARGET  = LUCEmbedded
BUILD   = build
PREFIX ?= arm-none-eabi-
CC      = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
SIZE    = $(PREFIX)size

LDSCRIPT = TrueSTUDIO/LUCEmbedded/STM32F042G4_FLASH.ld

HAL = Drivers/STM32F0xx_HAL_Driver/Src/stm32f0xx_hal
USBLIB = Middlewares/ST/STM32_USB_Device_Library

C_SRCS = \
	Src/bootloader.c \
	Src/lin_slcan.c \
	Src/main.c \
	Src/open_lin_data_layer.c \
	Src/open_lin_master_data_layer.c \
	Src/open_lin_network_layer.c \
	Src/open_lin_slave_data_layer.c \
	Src/open_lin_transport_layer.c \
	Src/slcan.c \
	Src/stm32f0xx_hal_msp.c \
	Src/stm32f0xx_it.c \
	Src/usb_device.c \
	Src/usbd_cdc_if.c \
	Src/usbd_conf.c \
	Src/usbd_desc.c \
	Src/system_stm32f0xx.c \
	Src/implementation/ST32/open_lin_hw_st32.c \
	$(HAL).c \
	$(HAL)_cortex.c \
	$(HAL)_dma.c \
	$(HAL)_flash.c \
	$(HAL)_flash_ex.c \
	$(HAL)_gpio.c \
	$(HAL)_i2c.c \
	$(HAL)_i2c_ex.c \
	$(HAL)_pcd.c \
	$(HAL)_pcd_ex.c \
	$(HAL)_pwr.c \
	$(HAL)_pwr_ex.c \
	$(HAL)_rcc.c \
	$(HAL)_rcc_ex.c \
	$(HAL)_tim.c \
	$(HAL)_tim_ex.c \
	$(HAL)_uart.c \
	$(HAL)_uart_ex.c \
	$(USBLIB)/Class/CDC/Src/usbd_cdc.c \
	$(USBLIB)/Core/Src/usbd_core.c \
	$(USBLIB)/Core/Src/usbd_ctlreq.c \
	$(USBLIB)/Core/Src/usbd_ioreq.c

S_SRCS = TrueSTUDIO/startup_stm32f042x6.s

MCU = -mcpu=cortex-m0 -mthumb -mfloat-abi=soft --specs=nano.specs

DEFS = '-D__weak=__attribute__((weak))' '-D__packed=__attribute__((__packed__))' \
	-DUSE_HAL_DRIVER -DSTM32F042x6

INCS = -IInc -ISrc \
	-IDrivers/STM32F0xx_HAL_Driver/Inc \
	-IDrivers/STM32F0xx_HAL_Driver/Inc/Legacy \
	-I$(USBLIB)/Core/Inc \
	-I$(USBLIB)/Class/CDC/Inc \
	-IDrivers/CMSIS/Device/ST/STM32F0xx/Include \
	-IDrivers/CMSIS/Include

CFLAGS  = $(MCU) -std=gnu11 -g -Os -ffunction-sections -fdata-sections -Wall -Wextra $(DEFS) $(INCS) -MMD -MP
ASFLAGS = $(MCU) -g -x assembler-with-cpp
LDFLAGS = $(MCU) -T$(LDSCRIPT) --specs=nosys.specs -static -Wl,--gc-sections \
	-Wl,-Map=$(BUILD)/$(TARGET).map -Wl,--start-group -lc -lm -Wl,--end-group

OBJS = $(addprefix $(BUILD)/,$(C_SRCS:.c=.o) $(S_SRCS:.s=.o))

all: $(BUILD)/$(TARGET).bin

$(BUILD)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.s
	@mkdir -p $(dir $@)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS) $(LDSCRIPT)
	$(CC) $(OBJS) $(LDFLAGS) -o $@
	$(SIZE) $@

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf $(BUILD)

-include $(OBJS:.o=.d)

.PHONY: all clean
