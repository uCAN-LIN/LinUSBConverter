/*
 * bootloader.c taken from krasutski.denis https://my.st.com/public/STe2ecommunities/mcu/Lists/cortex_mx_stm32/Flat.aspx?RootFolder=%2Fpublic%2FSTe2ecommunities%2Fmcu%2FLists%2Fcortex_mx_stm32%2FJump%20to%20USB%20DFU%20Bootloader%20in%20startup%20code%20on%20STM32F042&FolderCTID=0x01200200770978C69A1141439FE559EB459D7580009C4E14902C3CDE46A77F0FFD06506F5B&currentviews=2147
 * Thanks Denis!
 */

#include "stm32f0xx_hal.h"
#include "usb_device.h"

//call this at any time to initiate a reboot into bootloader
void RebootToBootloader(){


    FLASH_OBProgramInitTypeDef OBParam;

    HAL_FLASHEx_OBGetConfig(&OBParam);

    OBParam.OptionType = OPTIONBYTE_USER;
    /*Reset NBOOT0 and BOOT_SEL,  see: RM 2.5 Boot configuration*/
    OBParam.USERConfig = 0x77; //Sorry for magic number :)

    HAL_FLASH_Unlock();
    HAL_FLASH_OB_Unlock();

    HAL_FLASHEx_OBErase();

    HAL_FLASHEx_OBProgram(&OBParam);

    HAL_FLASH_OB_Lock();
    HAL_FLASH_Lock();

    HAL_FLASH_OB_Launch();
}

volatile uint8_t ttt;
//turns off BOOT0 pin
void bootloaderSwitcher(){


	FLASH_OBProgramInitTypeDef OBParam;


    HAL_FLASHEx_OBGetConfig(&OBParam);

    ttt = OBParam.USERConfig;
    // BOOT_SEL = 0, nBOOT0 = 1
    if(((OBParam.USERConfig & OB_BOOT0_SET) == 0) || ((OBParam.USERConfig & OB_BOOT_SEL_SET) == OB_BOOT_SEL_SET))
    {

        OBParam.OptionType = OPTIONBYTE_USER;
        OBParam.USERConfig = OBParam.USERConfig | OB_BOOT0_SET;
        OBParam.USERConfig = OBParam.USERConfig & (~OB_BOOT_SEL_SET);

        HAL_FLASH_Unlock();
        HAL_FLASH_OB_Unlock();
        HAL_FLASHEx_OBErase();
        HAL_FLASHEx_OBProgram(&OBParam);
        HAL_FLASH_OB_Lock();
        HAL_FLASH_OB_Launch();
    }
}

