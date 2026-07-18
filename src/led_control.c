/*
 * SPDX-License-Identifier: MIT
 *
 * planck_left web-controlled LED + status indicator.
 *
 * Host -> keyboard: the companion web page sends a 32-byte Raw HID report
 * (usage page 0xFF60, provided by the zmk-raw-hid module). Byte 0 is a magic
 * opcode, byte 1 is a bitmask selecting which of the three onboard LEDs are on.
 *
 * The host-set state is the "resting" state. Battery / connection changes only
 * flash a status color briefly and then the LEDs return to the resting state,
 * so the two responsibilities never fight over the LEDs.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/init.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

#include <zmk/event_manager.h>
#include <raw_hid/events.h>

#if IS_ENABLED(CONFIG_PLANCK_LED_STATUS)
#include <zmk/endpoints.h>
#include <zmk/endpoints_types.h>
#if IS_ENABLED(CONFIG_ZMK_BLE)
#include <zmk/ble.h>
#include <zmk/events/ble_active_profile_changed.h>
#endif
#include <zmk/events/endpoint_changed.h>
#if IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)
#include <zmk/events/battery_state_changed.h>
#endif
#endif /* CONFIG_PLANCK_LED_STATUS */

LOG_MODULE_REGISTER(planck_led, CONFIG_ZMK_LOG_LEVEL);

/* Raw HID protocol (host -> keyboard) */
#define PLANCK_LED_CMD_SET 0xAB
#define PLANCK_LED_MASK    0x07

/* Physical LED bit positions (see leds_left.dtsi aliases). */
#define LED_BIT_BLUE  BIT(0) /* led0 */
#define LED_BIT_RED   BIT(1) /* led1 */
#define LED_BIT_GREEN BIT(2) /* led2 */
#define LED_BIT_YELLOW (LED_BIT_RED | LED_BIT_GREEN)

#define LED_COUNT 3

static const struct gpio_dt_spec leds[LED_COUNT] = {
	GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios), /* blue  */
	GPIO_DT_SPEC_GET(DT_NODELABEL(led1), gpios), /* red   */
	GPIO_DT_SPEC_GET(DT_NODELABEL(led2), gpios), /* green */
};

/* Host-set resting state (bitmask, bits 0..2). */
static atomic_t web_state = ATOMIC_INIT(0);
/* Transient status color, or -1 when no status flash is active. */
static atomic_t status_color = ATOMIC_INIT(-1);
static bool leds_ready;

static void render(void)
{
	if (!leds_ready) {
		return;
	}

	int sc = (int)atomic_get(&status_color);
	uint8_t bits = (sc >= 0) ? (uint8_t)sc : (uint8_t)atomic_get(&web_state);

	for (int i = 0; i < LED_COUNT; i++) {
		gpio_pin_set_dt(&leds[i], (bits & BIT(i)) ? 1 : 0);
	}
}

static void render_work_fn(struct k_work *work)
{
	ARG_UNUSED(work);
	render();
}
static K_WORK_DEFINE(render_work, render_work_fn);

#if IS_ENABLED(CONFIG_PLANCK_LED_STATUS)
static void status_clear_fn(struct k_work *work)
{
	ARG_UNUSED(work);
	atomic_set(&status_color, -1);
	k_work_submit(&render_work);
}
static K_WORK_DELAYABLE_DEFINE(status_clear_work, status_clear_fn);

static void flash_status(uint8_t color_bits)
{
	atomic_set(&status_color, (atomic_val_t)color_bits);
	k_work_submit(&render_work);
	k_work_reschedule(&status_clear_work, K_MSEC(CONFIG_PLANCK_LED_STATUS_BLINK_MS));
}

static uint8_t conn_color(void)
{
	struct zmk_endpoint_instance ep = zmk_endpoint_get_selected();

	if (ep.transport == ZMK_TRANSPORT_USB) {
		return LED_BIT_BLUE;
	}

#if IS_ENABLED(CONFIG_ZMK_BLE)
	if (zmk_ble_active_profile_is_connected()) {
		return LED_BIT_BLUE;
	}
	if (zmk_ble_active_profile_is_open()) {
		return LED_BIT_YELLOW;
	}
	return LED_BIT_RED;
#else
	return LED_BIT_BLUE;
#endif
}

static int conn_listener(const zmk_event_t *eh)
{
	ARG_UNUSED(eh);
	flash_status(conn_color());
	return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(planck_led_conn, conn_listener);
ZMK_SUBSCRIPTION(planck_led_conn, zmk_endpoint_changed);
#if IS_ENABLED(CONFIG_ZMK_BLE)
ZMK_SUBSCRIPTION(planck_led_conn, zmk_ble_active_profile_changed);
#endif

#if IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING)
static int battery_listener(const zmk_event_t *eh)
{
	const struct zmk_battery_state_changed *ev = as_zmk_battery_state_changed(eh);

	if (!ev) {
		return ZMK_EV_EVENT_BUBBLE;
	}

	uint8_t color;
	if (ev->state_of_charge > 80) {
		color = LED_BIT_GREEN;
	} else if (ev->state_of_charge >= 20) {
		color = LED_BIT_YELLOW;
	} else {
		color = LED_BIT_RED;
	}

	flash_status(color);
	return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(planck_led_battery, battery_listener);
ZMK_SUBSCRIPTION(planck_led_battery, zmk_battery_state_changed);
#endif /* CONFIG_ZMK_BATTERY_REPORTING */
#endif /* CONFIG_PLANCK_LED_STATUS */

static int raw_hid_listener(const zmk_event_t *eh)
{
	const struct raw_hid_received_event *ev = as_raw_hid_received_event(eh);

	if (!ev || ev->data == NULL || ev->length < 2) {
		return ZMK_EV_EVENT_BUBBLE;
	}

	if (ev->data[0] != PLANCK_LED_CMD_SET) {
		return ZMK_EV_EVENT_BUBBLE;
	}

	atomic_set(&web_state, (atomic_val_t)(ev->data[1] & PLANCK_LED_MASK));
	k_work_submit(&render_work);

	return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(planck_led_raw_hid, raw_hid_listener);
ZMK_SUBSCRIPTION(planck_led_raw_hid, raw_hid_received_event);

static int planck_led_init(void)
{
	for (int i = 0; i < LED_COUNT; i++) {
		if (!gpio_is_ready_dt(&leds[i])) {
			LOG_ERR("LED %d GPIO not ready", i);
			return -ENODEV;
		}
		int ret = gpio_pin_configure_dt(&leds[i], GPIO_OUTPUT_INACTIVE);
		if (ret < 0) {
			LOG_ERR("Failed to configure LED %d: %d", i, ret);
			return ret;
		}
	}

	leds_ready = true;
	render();
	return 0;
}

SYS_INIT(planck_led_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
