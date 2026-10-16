use embassy_nrf::pwm::{DutyCycle, SimplePwm};
use rmk::event::{LayerChangeEvent, SleepStateEvent};
use rmk::macros::processor;

#[derive(Clone, Copy)]
pub struct RgbChannels {
    pub red: usize,
    pub green: usize,
    pub blue: usize,
}

/// Drives the board's single common-anode RGB status LED through nRF PWM0.
///
/// The channel polarity mirrors the ZMK `PWM_POLARITY_INVERTED` definition.
/// Colors intentionally indicate layers only; the unimplemented ZMK
/// `rgb_ug` keycodes referred to a different, undocumented underglow device.
#[processor(subscribe = [LayerChangeEvent, SleepStateEvent])]
pub struct RgbPwmProcessor {
    pwm: SimplePwm<'static>,
    channels: RgbChannels,
    layer: u8,
    sleeping: bool,
}

impl RgbPwmProcessor {
    pub fn new(mut pwm: SimplePwm<'static>, channels: RgbChannels) -> Self {
        pwm.set_max_duty(255);
        pwm.set_period(1_000);
        pwm.set_all_duties([
            DutyCycle::inverted(0),
            DutyCycle::inverted(0),
            DutyCycle::inverted(0),
            DutyCycle::inverted(0),
        ]);
        pwm.enable();

        let mut processor = Self {
            pwm,
            channels,
            layer: 0,
            sleeping: false,
        };
        processor.render();
        processor
    }

    async fn on_layer_change_event(&mut self, event: LayerChangeEvent) {
        self.layer = event.0;
        self.render();
    }

    async fn on_sleep_state_event(&mut self, event: SleepStateEvent) {
        self.sleeping = event.0;
        self.render();
    }

    fn render(&mut self) {
        let (red, green, blue) = if self.sleeping {
            (0, 0, 0)
        } else {
            match self.layer {
                0 => (0, 0, 0),
                1 => (32, 10, 0),
                2 => (0, 8, 36),
                3 => (24, 0, 28),
                _ => (12, 12, 12),
            }
        };

        self.pwm
            .set_duty(self.channels.red, DutyCycle::inverted(red));
        self.pwm
            .set_duty(self.channels.green, DutyCycle::inverted(green));
        self.pwm
            .set_duty(self.channels.blue, DutyCycle::inverted(blue));
    }
}
