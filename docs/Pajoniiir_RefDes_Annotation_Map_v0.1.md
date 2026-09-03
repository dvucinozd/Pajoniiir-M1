# Pajoniiir-M1 — RefDes Annotation Map v0.1

**Datum:** 2026-09-03  
**Milestone:** M1-SCH-A manufacturing normalization  
**Source electrical baseline:** `276e803ec72994dd6d69dfb1c1e0ad5fbb26a8ef`  
**Status:** Complete traceability map for capture-era descriptive aliases

---

## Purpose

Early Rev-A schematic capture used descriptive reference aliases such as `R_DSI_REXT`, `C_CORE_IN`, `U_USB0` and `TP_5V_SYS`. Native KiCad 9.0.9 manufacturing BOM export correctly flagged those aliases as annotation errors because production RefDes values require a numeric suffix.

The manufacturing normalization changes **Reference fields only**. The safe rewrite in commit `582c9039` was rebuilt from the clean electrical baseline above and constrained to placed-symbol `Reference` properties plus their instance-reference records.

Do not recover semantic meaning by renaming RefDes values again. Use this map, Value/Description fields, net names and subsystem documentation.

Existing valid numeric references were preserved. Planned main-device numbering remains aligned with Engineering BOM v0.2, including `U6` USB0 power switch, `U9` backlight boost, `U12` USB1 power switch, `U13` microSD load switch and `U14` INA238 monitor.

The physical LCD connector remains the unresolved documentation alias **`J_LCD`** because it is not yet instantiated in the schematic. It will receive a real numeric RefDes only when its mechanical/pin-domain gate is closed.

---

## Complete migration map

| Capture alias | Manufacturing RefDes | Leaf sheet |
|---|---|---|
| `FB_C6` | `FB1` | `02_POWER_3V3` |
| `FB_AUDIO` | `FB2` | `02_POWER_3V3` |
| `R_DSI_REXT` | `R24` | `03_P4_CORE` |
| `R_ANA_LINK` | `R25` | `03_P4_CORE` |
| `C_ANA` | `C26` | `03_P4_CORE` |
| `R_USBPHY_LINK` | `R26` | `03_P4_CORE` |
| `C_USBPHY_1` | `C27` | `03_P4_CORE` |
| `C_USBPHY_2` | `C28` | `03_P4_CORE` |
| `C_USBPHY_3` | `C29` | `03_P4_CORE` |
| `C_VDDO_FLASH` | `C30` | `03_P4_CORE` |
| `C_FLASHIO_HF` | `C31` | `03_P4_CORE` |
| `C_VDDO_PSRAM` | `C32` | `03_P4_CORE` |
| `C_PSRAM0_HF` | `C33` | `03_P4_CORE` |
| `C_PSRAM0_LOCAL` | `C34` | `03_P4_CORE` |
| `C_PSRAM1_HF` | `C35` | `03_P4_CORE` |
| `C_PSRAM1_LOCAL` | `C36` | `03_P4_CORE` |
| `C_MIPI_LDO_OUT` | `C37` | `03_P4_CORE` |
| `C_MIPI_10N` | `C38` | `03_P4_CORE` |
| `C_MIPI_100N` | `C39` | `03_P4_CORE` |
| `C_CORE_IN` | `C40` | `03_P4_CORE` |
| `L_CORE` | `L1` | `03_P4_CORE` |
| `C_CORE_OUT` | `C41` | `03_P4_CORE` |
| `R_CORE_FB_TOP` | `R27` | `03_P4_CORE` |
| `R_CORE_FB_BOT` | `R28` | `03_P4_CORE` |
| `C_CORE_FF` | `C42` | `03_P4_CORE` |
| `C_HP_BULK` | `C43` | `03_P4_CORE` |
| `C_HP0` | `C44` | `03_P4_CORE` |
| `C_HP1` | `C45` | `03_P4_CORE` |
| `C_HP2` | `C46` | `03_P4_CORE` |
| `C_HP3` | `C47` | `03_P4_CORE` |
| `C_P4_3V3_BULK` | `C48` | `03_P4_CORE` |
| `C_VDD_LP` | `C49` | `03_P4_CORE` |
| `C_VDD_IO0` | `C50` | `03_P4_CORE` |
| `C_VDD_IO4` | `C51` | `03_P4_CORE` |
| `C_VDD_IO5` | `C52` | `03_P4_CORE` |
| `C_VDD_IO6` | `C53` | `03_P4_CORE` |
| `C_VDD_BAT_HF` | `C54` | `03_P4_CORE` |
| `C_VDD_BAT_BULK` | `C55` | `03_P4_CORE` |
| `C_VDD_LDO_HF` | `C56` | `03_P4_CORE` |
| `C_VDD_LDO_BULK` | `C57` | `03_P4_CORE` |
| `C_VDD_DCDCC_HF` | `C58` | `03_P4_CORE` |
| `C_VDD_DCDCC_BULK` | `C59` | `03_P4_CORE` |
| `R_FLASH_CS` | `R29` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_CLK` | `R30` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_D0` | `R31` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_D1` | `R32` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_D2` | `R33` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_D3` | `R34` | `04_P4_FLASH_CLOCK_RESET` |
| `R_FLASH_CS_PU` | `R35` | `04_P4_FLASH_CLOCK_RESET` |
| `C_FLASH` | `C60` | `04_P4_FLASH_CLOCK_RESET` |
| `R_XTAL_SER` | `R36` | `04_P4_FLASH_CLOCK_RESET` |
| `C_XTAL_P` | `C61` | `04_P4_FLASH_CLOCK_RESET` |
| `C_XTAL_N` | `C62` | `04_P4_FLASH_CLOCK_RESET` |
| `R_CHIP_PU` | `R37` | `04_P4_FLASH_CLOCK_RESET` |
| `C_CHIP_PU` | `C63` | `04_P4_FLASH_CLOCK_RESET` |
| `SW_RESET` | `SW1` | `04_P4_FLASH_CLOCK_RESET` |
| `R_BOOT35_PU` | `R38` | `04_P4_FLASH_CLOCK_RESET` |
| `SW_BOOT` | `SW2` | `04_P4_FLASH_CLOCK_RESET` |
| `R_BOOT36_PU` | `R39` | `04_P4_FLASH_CLOCK_RESET` |
| `R_UART_TX` | `R40` | `04_P4_FLASH_CLOCK_RESET` |
| `R_UART_RX` | `R41` | `04_P4_FLASH_CLOCK_RESET` |
| `C_C6_HF` | `C64` | `05_C6_WIFI` |
| `C_C6_LOCAL` | `C65` | `05_C6_WIFI` |
| `C_C6_BULK` | `C66` | `05_C6_WIFI` |
| `R_C6_RESET_SER` | `R42` | `05_C6_WIFI` |
| `R_C6_EN` | `R43` | `05_C6_WIFI` |
| `C_C6_EN` | `C67` | `05_C6_WIFI` |
| `R_SDIO_CMD` | `R44` | `05_C6_WIFI` |
| `R_SDIO_CMD_PU` | `R45` | `05_C6_WIFI` |
| `R_SDIO_CLK` | `R46` | `05_C6_WIFI` |
| `R_SDIO_D0` | `R47` | `05_C6_WIFI` |
| `R_SDIO_D0_PU` | `R48` | `05_C6_WIFI` |
| `R_SDIO_D1` | `R49` | `05_C6_WIFI` |
| `R_SDIO_D1_PU` | `R50` | `05_C6_WIFI` |
| `R_SDIO_D2` | `R51` | `05_C6_WIFI` |
| `R_SDIO_D2_PU` | `R52` | `05_C6_WIFI` |
| `R_SDIO_D3` | `R53` | `05_C6_WIFI` |
| `R_SDIO_D3_PU` | `R54` | `05_C6_WIFI` |
| `R_C6_UART_TX` | `R55` | `05_C6_WIFI` |
| `R_C6_UART_RX` | `R56` | `05_C6_WIFI` |
| `R_C6_GPIO8_PU` | `R57` | `05_C6_WIFI` |
| `R_C6_GPIO9_PU` | `R58` | `05_C6_WIFI` |
| `C_USB_PWR_LOCAL` | `C68` | `06_USB_POWER` |
| `C_USB0_IN` | `C69` | `06_USB_POWER` |
| `U_USB0` | `U6` | `06_USB_POWER` |
| `R_U_USB0_EN_PD` | `R59` | `06_USB_POWER` |
| `R_U_USB0_FLT_PU` | `R60` | `06_USB_POWER` |
| `R_U_USB0_ILIM` | `R61` | `06_USB_POWER` |
| `R_USB0_SHUNT` | `R62` | `06_USB_POWER` |
| `C_USB0_OUT_HF` | `C70` | `06_USB_POWER` |
| `C_USB0_OUT_BULK` | `C71` | `06_USB_POWER` |
| `C_USB0_OUT_OPT` | `C72` | `06_USB_POWER` |
| `C_USB1_IN` | `C73` | `06_USB_POWER` |
| `U_USB1` | `U12` | `06_USB_POWER` |
| `R_U_USB1_EN_PD` | `R63` | `06_USB_POWER` |
| `R_U_USB1_FLT_PU` | `R64` | `06_USB_POWER` |
| `R_U_USB1_ILIM` | `R65` | `06_USB_POWER` |
| `R_USB1_SHUNT` | `R66` | `06_USB_POWER` |
| `C_USB1_OUT_HF` | `C74` | `06_USB_POWER` |
| `C_USB1_OUT_BULK` | `C75` | `06_USB_POWER` |
| `C_USB1_OUT_OPT` | `C76` | `06_USB_POWER` |
| `R_USB0_DM` | `R67` | `07_USB0_STORAGE` |
| `R_USB0_DP` | `R68` | `07_USB0_STORAGE` |
| `D_USB0_ESD` | `D2` | `07_USB0_STORAGE` |
| `J_USB0` | `J2` | `07_USB0_STORAGE` |
| `R_USB0_SHIELD` | `R69` | `07_USB0_STORAGE` |
| `C_USB0_SHIELD` | `C77` | `07_USB0_STORAGE` |
| `R_USB0_SHIELD_HI` | `R70` | `07_USB0_STORAGE` |
| `R_USB1_DM` | `R71` | `08_USB1_FLX4` |
| `R_USB1_DP` | `R72` | `08_USB1_FLX4` |
| `C_USB1_DM` | `C78` | `08_USB1_FLX4` |
| `C_USB1_DP` | `C79` | `08_USB1_FLX4` |
| `D_USB1_ESD` | `D3` | `08_USB1_FLX4` |
| `J_USB1` | `J3` | `08_USB1_FLX4` |
| `R_USB1_SHIELD` | `R73` | `08_USB1_FLX4` |
| `C_USB1_SHIELD` | `C80` | `08_USB1_FLX4` |
| `R_USB1_SHIELD_HI` | `R74` | `08_USB1_FLX4` |
| `R_I2S_LRCK` | `R75` | `09_AUDIO_PCM5102A` |
| `R_I2S_DATA` | `R76` | `09_AUDIO_PCM5102A` |
| `R_I2S_BCLK` | `R77` | `09_AUDIO_PCM5102A` |
| `R_XSMT_SER` | `R78` | `09_AUDIO_PCM5102A` |
| `R_XSMT_PD` | `R79` | `09_AUDIO_PCM5102A` |
| `C_AUDIO_BRANCH` | `C81` | `09_AUDIO_PCM5102A` |
| `C_CPVDD_HF` | `C82` | `09_AUDIO_PCM5102A` |
| `C_CPVDD_BULK` | `C83` | `09_AUDIO_PCM5102A` |
| `C_DVDD_HF` | `C84` | `09_AUDIO_PCM5102A` |
| `C_DVDD_BULK` | `C85` | `09_AUDIO_PCM5102A` |
| `C_AVDD_HF` | `C86` | `09_AUDIO_PCM5102A` |
| `C_AVDD_BULK` | `C87` | `09_AUDIO_PCM5102A` |
| `C_CP_FLY` | `C88` | `09_AUDIO_PCM5102A` |
| `C_VNEG` | `C89` | `09_AUDIO_PCM5102A` |
| `C_LDOO` | `C90` | `09_AUDIO_PCM5102A` |
| `R_OUT_L` | `R80` | `09_AUDIO_PCM5102A` |
| `C_OUT_L` | `C91` | `09_AUDIO_PCM5102A` |
| `R_OUT_R` | `R81` | `09_AUDIO_PCM5102A` |
| `C_OUT_R` | `C92` | `09_AUDIO_PCM5102A` |
| `J_RCA_L` | `J4` | `09_AUDIO_PCM5102A` |
| `J_RCA_R` | `J5` | `09_AUDIO_PCM5102A` |
| `J_LINE_35` | `J6` | `09_AUDIO_PCM5102A` |
| `FB_LCD` | `FB3` | `10_DISPLAY_MIPI` |
| `C_LCD_HF` | `C93` | `10_DISPLAY_MIPI` |
| `C_LCD_BULK` | `C94` | `10_DISPLAY_MIPI` |
| `TP_3V3_LCD` | `TP1` | `10_DISPLAY_MIPI` |
| `TP_MIPI_2V5` | `TP2` | `10_DISPLAY_MIPI` |
| `R_DSI_D0_P` | `R82` | `10_DISPLAY_MIPI` |
| `R_DSI_D0_N` | `R83` | `10_DISPLAY_MIPI` |
| `R_DSI_D1_P` | `R84` | `10_DISPLAY_MIPI` |
| `R_DSI_D1_N` | `R85` | `10_DISPLAY_MIPI` |
| `R_DSI_CLK_P` | `R86` | `10_DISPLAY_MIPI` |
| `R_DSI_CLK_N` | `R87` | `10_DISPLAY_MIPI` |
| `R_LCD_RST_SER` | `R88` | `10_DISPLAY_MIPI` |
| `R_LCD_RST_PD` | `R89` | `10_DISPLAY_MIPI` |
| `TP_LCD_RST` | `TP3` | `10_DISPLAY_MIPI` |
| `R_LCD_TE_SER` | `R90` | `10_DISPLAY_MIPI` |
| `TP_LCD_TE` | `TP4` | `10_DISPLAY_MIPI` |
| `C_BL_IN` | `C95` | `10_DISPLAY_MIPI` |
| `C_BL_HF` | `C96` | `10_DISPLAY_MIPI` |
| `L_BL` | `L3` | `10_DISPLAY_MIPI` |
| `U_BL` | `U9` | `10_DISPLAY_MIPI` |
| `D_BL` | `D4` | `10_DISPLAY_MIPI` |
| `C_BL_OUT` | `C97` | `10_DISPLAY_MIPI` |
| `C_BL_OUT_HF` | `C98` | `10_DISPLAY_MIPI` |
| `TP_LEDA` | `TP5` | `10_DISPLAY_MIPI` |
| `R_BL_SENSE_A` | `R91` | `10_DISPLAY_MIPI` |
| `R_BL_SENSE_B` | `R92` | `10_DISPLAY_MIPI` |
| `TP_LED_CURRENT` | `TP6` | `10_DISPLAY_MIPI` |
| `R_BL_PWM` | `R93` | `10_DISPLAY_MIPI` |
| `R_BL_EN_PD` | `R94` | `10_DISPLAY_MIPI` |
| `TP_LCD_BL_PWM` | `TP7` | `10_DISPLAY_MIPI` |
| `FB_TOUCH` | `FB4` | `11_TOUCH_GT911` |
| `C_TOUCH_HF` | `C99` | `11_TOUCH_GT911` |
| `C_TOUCH_BULK` | `C100` | `11_TOUCH_GT911` |
| `TP_3V3_TOUCH` | `TP8` | `11_TOUCH_GT911` |
| `R_TOUCH_SDA_SER` | `R95` | `11_TOUCH_GT911` |
| `R_TOUCH_SCL_SER` | `R96` | `11_TOUCH_GT911` |
| `R_TOUCH_SDA_PU` | `R97` | `11_TOUCH_GT911` |
| `R_TOUCH_SCL_PU` | `R98` | `11_TOUCH_GT911` |
| `R_TOUCH_SDA_PU2` | `R99` | `11_TOUCH_GT911` |
| `R_TOUCH_SCL_PU2` | `R100` | `11_TOUCH_GT911` |
| `R_TOUCH_RST_SER` | `R101` | `11_TOUCH_GT911` |
| `R_TOUCH_RST_PU` | `R102` | `11_TOUCH_GT911` |
| `R_TOUCH_INT_SER` | `R103` | `11_TOUCH_GT911` |
| `TP_TOUCH_SDA` | `TP9` | `11_TOUCH_GT911` |
| `TP_TOUCH_SCL` | `TP10` | `11_TOUCH_GT911` |
| `TP_TOUCH_RST` | `TP11` | `11_TOUCH_GT911` |
| `TP_TOUCH_INT` | `TP12` | `11_TOUCH_GT911` |
| `U_SD_PWR` | `U13` | `12_MICROSD` |
| `R_SD_EN_PD` | `R104` | `12_MICROSD` |
| `C_SD_SW_IN_HF` | `C101` | `12_MICROSD` |
| `C_SD_SW_IN` | `C102` | `12_MICROSD` |
| `C_SD_CT` | `C103` | `12_MICROSD` |
| `R_SD_QOD` | `R105` | `12_MICROSD` |
| `C_SD_OUT_HF` | `C104` | `12_MICROSD` |
| `C_SD_OUT` | `C105` | `12_MICROSD` |
| `C_SD_OUT_OPT` | `C106` | `12_MICROSD` |
| `J_SD` | `J7` | `12_MICROSD` |
| `R_SD_D2_SER` | `R106` | `12_MICROSD` |
| `R_SD_D3_SER` | `R107` | `12_MICROSD` |
| `R_SD_CMD_SER` | `R108` | `12_MICROSD` |
| `R_SD_CLK_SER` | `R109` | `12_MICROSD` |
| `R_SD_D0_SER` | `R110` | `12_MICROSD` |
| `R_SD_D1_SER` | `R111` | `12_MICROSD` |
| `R_SD_D2_PU` | `R112` | `12_MICROSD` |
| `R_SD_D3_PU` | `R113` | `12_MICROSD` |
| `R_SD_CMD_PU` | `R114` | `12_MICROSD` |
| `R_SD_D0_PU` | `R115` | `12_MICROSD` |
| `R_SD_D1_PU` | `R116` | `12_MICROSD` |
| `C_SD_CLK_TUNE` | `C107` | `12_MICROSD` |
| `R_SD_CD_PU` | `R117` | `12_MICROSD` |
| `JDBG_P4` | `J8` | `13_DEBUG_SERVICE` |
| `R_USBJTAG_DM` | `R118` | `13_DEBUG_SERVICE` |
| `R_USBJTAG_DP` | `R119` | `13_DEBUG_SERVICE` |
| `C_P4_USBJTAG_DM` | `C108` | `13_DEBUG_SERVICE` |
| `C_P4_USBJTAG_DP` | `C109` | `13_DEBUG_SERVICE` |
| `JDBG_USB` | `J9` | `13_DEBUG_SERVICE` |
| `JDBG_C6` | `J10` | `13_DEBUG_SERVICE` |
| `TP_P4_BOOT36` | `TP13` | `13_DEBUG_SERVICE` |
| `TP_C6_GPIO8` | `TP14` | `13_DEBUG_SERVICE` |
| `TP_P4_UART_TX` | `TP15` | `13_DEBUG_SERVICE` |
| `TP_P4_UART_RX` | `TP16` | `13_DEBUG_SERVICE` |
| `TP_CHIP_PU` | `TP17` | `13_DEBUG_SERVICE` |
| `TP_USBJTAG_DM` | `TP18` | `13_DEBUG_SERVICE` |
| `TP_USBJTAG_DP` | `TP19` | `13_DEBUG_SERVICE` |
| `TP_C6_EN` | `TP20` | `13_DEBUG_SERVICE` |
| `R_SYS_SHUNT` | `R120` | `14_TEST_MONITORING` |
| `U_MON` | `U14` | `14_TEST_MONITORING` |
| `R_INA_P` | `R121` | `14_TEST_MONITORING` |
| `R_INA_N` | `R122` | `14_TEST_MONITORING` |
| `C_INA_DIFF` | `C110` | `14_TEST_MONITORING` |
| `C_INA_HF` | `C111` | `14_TEST_MONITORING` |
| `C_INA_LOCAL` | `C112` | `14_TEST_MONITORING` |
| `R_INA_ALERT_PU` | `R123` | `14_TEST_MONITORING` |
| `TP_5V_PROTECTED` | `TP21` | `14_TEST_MONITORING` |
| `TP_5V_SYS` | `TP22` | `14_TEST_MONITORING` |
| `TP_3V3_SYS` | `TP23` | `14_TEST_MONITORING` |
| `TP_SYS_ALERT` | `TP24` | `14_TEST_MONITORING` |

---

## Manufacturing invariant

Every instantiated non-power symbol must match:

~~~text
^[A-Za-z]+[0-9]+$
~~~

Descriptive names belong in documentation, comments, fields, and net labels. They must not be encoded into the KiCad Reference property.
