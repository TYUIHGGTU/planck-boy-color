/*
 * nRF52840 flash layout inherited from the working ZMK nrf52840-nosd build:
 *
 *   0x00000000..0x00001000  MBR/reserved
 *   0x00001000..0x000D4000  RMK application (844 KiB)
 *   0x000D4000..0x000F4000  RMK storage (128 KiB, configured in keyboard.toml)
 *   0x000F4000..0x00100000  existing UF2 bootloader (48 KiB)
 *
 * Keeping these boundaries prevents RMK storage from overwriting the existing
 * bootloader and permits recovery through the same UF2 workflow as ZMK.
 */
MEMORY
{
    FLASH : ORIGIN = 0x00001000, LENGTH = 844K
    RAM   : ORIGIN = 0x20000008, LENGTH = 255K
}
