/*
 * Copyright (c) 2026
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT zmk_input_processor_caret

#include <errno.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/dt-bindings/input/input-event-codes.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/util.h>

#include <drivers/input_processor.h>
#include <zmk/behavior.h>
#include <zmk/keymap.h>
#include <zmk/virtual_key_position.h>

enum caret_direction {
    CARET_LEFT,
    CARET_RIGHT,
    CARET_UP,
    CARET_DOWN,
    CARET_DIRECTION_COUNT,
};

struct caret_input_config {
    uint8_t index;
    int32_t threshold;
    const struct zmk_behavior_binding *bindings;
};

struct caret_input_data {
    int32_t x_accumulator;
    int32_t y_accumulator;
};

static int tap_binding(const struct caret_input_config *config,
                       struct zmk_input_processor_state *state, enum caret_direction direction) {
    struct zmk_behavior_binding_event behavior_event = {
        .position = ZMK_VIRTUAL_KEY_POSITION_BEHAVIOR_INPUT_PROCESSOR(
            state->input_device_index, config->index),
        .timestamp = k_uptime_get(),
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
        .source = ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL,
#endif
    };

    int ret =
        zmk_behavior_invoke_binding(&config->bindings[direction], behavior_event, true);
    if (ret < 0) {
        return ret;
    }

    return zmk_behavior_invoke_binding(&config->bindings[direction], behavior_event, false);
}

static int emit_axis_steps(const struct caret_input_config *config,
                           struct zmk_input_processor_state *state, int32_t *accumulator,
                           enum caret_direction negative, enum caret_direction positive) {
    int emitted = 0;

    while (*accumulator >= config->threshold && emitted < 8) {
        int ret = tap_binding(config, state, positive);
        if (ret < 0) {
            return ret;
        }

        *accumulator -= config->threshold;
        emitted++;
    }

    while (*accumulator <= -config->threshold && emitted < 8) {
        int ret = tap_binding(config, state, negative);
        if (ret < 0) {
            return ret;
        }

        *accumulator += config->threshold;
        emitted++;
    }

    return 0;
}

static int caret_input_handle_event(const struct device *dev, struct input_event *event,
                                    uint32_t param1, uint32_t param2,
                                    struct zmk_input_processor_state *state) {
    const struct caret_input_config *config = dev->config;
    struct caret_input_data *data = dev->data;

    if (event->type != INPUT_EV_REL) {
        return ZMK_INPUT_PROC_CONTINUE;
    }

    int ret;

    switch (event->code) {
    case INPUT_REL_X:
        data->x_accumulator += event->value;
        ret = emit_axis_steps(config, state, &data->x_accumulator, CARET_LEFT, CARET_RIGHT);
        break;
    case INPUT_REL_Y:
        data->y_accumulator += event->value;
        ret = emit_axis_steps(config, state, &data->y_accumulator, CARET_UP, CARET_DOWN);
        break;
    default:
        return ZMK_INPUT_PROC_CONTINUE;
    }

    if (ret < 0) {
        return ret;
    }

    event->value = 0;
    return ZMK_INPUT_PROC_STOP;
}

static int caret_input_init(const struct device *dev) {
    const struct caret_input_config *config = dev->config;

    return config->threshold > 0 ? 0 : -EINVAL;
}

static const struct zmk_input_processor_driver_api caret_input_driver_api = {
    .handle_event = caret_input_handle_event,
};

#define CARET_BINDINGS(n)                                                                          \
    {LISTIFY(DT_INST_PROP_LEN(n, bindings), ZMK_KEYMAP_EXTRACT_BINDING, (, ), DT_DRV_INST(n))}

#define CARET_INPUT_INST(n)                                                                        \
    BUILD_ASSERT(DT_INST_PROP_LEN(n, bindings) == CARET_DIRECTION_COUNT,                            \
                 "caret input processor requires left, right, up, and down bindings");             \
    static const struct zmk_behavior_binding caret_input_bindings_##n[] = CARET_BINDINGS(n);       \
    static const struct caret_input_config caret_input_config_##n = {                              \
        .index = n,                                                                                \
        .threshold = DT_INST_PROP(n, threshold),                                                   \
        .bindings = caret_input_bindings_##n,                                                      \
    };                                                                                             \
    static struct caret_input_data caret_input_data_##n;                                           \
    DEVICE_DT_INST_DEFINE(n, caret_input_init, NULL, &caret_input_data_##n,                         \
                          &caret_input_config_##n, POST_KERNEL,                                    \
                          CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &caret_input_driver_api);

DT_INST_FOREACH_STATUS_OKAY(CARET_INPUT_INST)
