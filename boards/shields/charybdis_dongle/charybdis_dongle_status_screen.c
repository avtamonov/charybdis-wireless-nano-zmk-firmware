/*
 * SPDX-License-Identifier: MIT
 */

#include <stdio.h>
#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

#include <zmk/display.h>
#include <zmk/display/status_screen.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>
#include <zmk/split/central.h>

LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#define LEFT_SOURCE 0
#define RIGHT_SOURCE 1

static lv_obj_t *battery_label;
static lv_obj_t *layer_label;
static bool peripheral_battery_seen[CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS];

struct charybdis_status_state {
    uint8_t battery[CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS];
    bool battery_seen[CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS];
    zmk_keymap_layer_index_t layer_index;
    const char *layer_name;
};

static const char *layer_text(struct charybdis_status_state state) {
    if (state.layer_name != NULL && strlen(state.layer_name) > 0) {
        return state.layer_name;
    }

    static char fallback[8];
    snprintf(fallback, sizeof(fallback), "%u", state.layer_index);
    return fallback;
}

static void format_battery(char *buf, size_t len, uint8_t source,
                           struct charybdis_status_state state) {
    if (source >= CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS || !state.battery_seen[source]) {
        snprintf(buf, len, "--");
        return;
    }

    snprintf(buf, len, "%u%%", state.battery[source]);
}

static void draw_status(struct charybdis_status_state state) {
    char left[5];
    char right[5];
    char text[32];

    format_battery(left, sizeof(left), LEFT_SOURCE, state);
    format_battery(right, sizeof(right), RIGHT_SOURCE, state);

    snprintf(text, sizeof(text), "L %s   R %s", left, right);
    lv_label_set_text(battery_label, text);

    snprintf(text, sizeof(text), "Layer %s", layer_text(state));
    lv_label_set_text(layer_label, text);
}

static struct charybdis_status_state get_status_state(const zmk_event_t *eh) {
    const struct zmk_peripheral_battery_state_changed *battery_ev =
        as_zmk_peripheral_battery_state_changed(eh);

    if (battery_ev != NULL && battery_ev->source < ARRAY_SIZE(peripheral_battery_seen)) {
        peripheral_battery_seen[battery_ev->source] = true;
    }

    struct charybdis_status_state state = {
        .layer_index = zmk_keymap_highest_layer_active(),
    };

    state.layer_name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(state.layer_index));

    for (int i = 0; i < CONFIG_ZMK_SPLIT_BLE_CENTRAL_PERIPHERALS; i++) {
        uint8_t level = 0;

        if (zmk_split_central_get_peripheral_battery_level(i, &level) == 0) {
            state.battery[i] = level;
            state.battery_seen[i] = peripheral_battery_seen[i];
        }
    }

    return state;
}

ZMK_DISPLAY_WIDGET_LISTENER(charybdis_dongle_status, struct charybdis_status_state, draw_status,
                            get_status_state)

ZMK_SUBSCRIPTION(charybdis_dongle_status, zmk_peripheral_battery_state_changed);
ZMK_SUBSCRIPTION(charybdis_dongle_status, zmk_layer_state_changed);

lv_obj_t *zmk_display_status_screen() {
    lv_obj_t *screen = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(screen, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, LV_PART_MAIN);

    battery_label = lv_label_create(screen);
    lv_obj_set_style_text_color(battery_label, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_text_font(battery_label, &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(battery_label, LV_ALIGN_TOP_LEFT, 0, 0);

    layer_label = lv_label_create(screen);
    lv_obj_set_style_text_color(layer_label, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_text_font(layer_label, &lv_font_montserrat_12, LV_PART_MAIN);
    lv_obj_align(layer_label, LV_ALIGN_BOTTOM_LEFT, 0, 0);

    charybdis_dongle_status_init();

    return screen;
}
