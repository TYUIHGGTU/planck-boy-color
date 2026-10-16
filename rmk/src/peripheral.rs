#![no_main]
#![no_std]

mod rgb_pwm;

use rmk::macros::rmk_peripheral;

#[rmk_peripheral(id = 0)]
mod keyboard_peripheral {
    use crate::rgb_pwm::{RgbChannels, RgbPwmProcessor};

    #[register_processor(event)]
    fn rgb_status() -> RgbPwmProcessor {
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm = embassy_nrf::pwm::SimplePwm::new_3ch(p.PWM0, p.P1_07, p.P1_05, p.P1_03, &config);
        RgbPwmProcessor::new(
            pwm,
            RgbChannels {
                red: 2,
                green: 1,
                blue: 0,
            },
        )
    }
}
