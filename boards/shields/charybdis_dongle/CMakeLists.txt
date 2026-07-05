if(CONFIG_ZMK_DISPLAY AND CONFIG_CHARYBDIS_DONGLE_STATUS_SCREEN)
  zephyr_library_include_directories(${CMAKE_SOURCE_DIR}/include)
  zephyr_library_sources(charybdis_dongle_status_screen.c)
endif()
