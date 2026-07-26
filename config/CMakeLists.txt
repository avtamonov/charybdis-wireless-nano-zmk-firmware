if(CONFIG_ZMK_INPUT_PROCESSOR_CARET)
  zephyr_library()
  zephyr_library_sources(src/input_processor_caret.c)
endif()
