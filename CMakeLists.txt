# SPDX-License-Identifier: MIT
# Repo-local ZMK module: web-controlled LED + status indicator for planck_left.
# The reusable ZMK build workflow detects this repo as a Zephyr module because
# of zephyr/module.yml and adds the repo root via ZMK_EXTRA_MODULES.

if(CONFIG_PLANCK_LED_CONTROL)
  target_sources(app PRIVATE src/led_control.c)
  zephyr_include_directories(${APPLICATION_SOURCE_DIR}/include)
endif()
