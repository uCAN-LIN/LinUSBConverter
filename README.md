# LUC
Software for LIN(Local Interconnect Network)-USB-CONVERTER(LUC) written for STM32F042C6 mcu, see [ucandevices](https://ucandevices.github.io/ulc.html) web page for full info.
# Build and run
Source code is pure C. Project can be imported directly to Atollic TrueSTUDIO for STM32 9.0.0 
Drivers for USB layer were generated in stm32CubeMX.
# Hardware
Hardware is open source. See PCB directory.
# Bootloader
STM32 have embedded DFU bootloader, for more info see st.com. To enter the bootloader please type boot. See [tutorial](https://www.youtube.com/watch?v=-gnX25AGyI0)
# Tools
Device is partially compatible with SLCAN, A set of tools is available at [ucandevices](https://ucandevices.github.io/ulc.html)
# LIN Implementation
LIN implementation is based on OPEN-LIN project see [openLIN](https://github.com/open-LIN) for details.
