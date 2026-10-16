#![no_main]
#![no_std]

mod rgb_pwm;

use rmk::macros::rmk_central;

#[rmk_central]
mod keyboard_central {
    use crate::rgb_pwm::{RgbChannels, RgbPwmProcessor};

    #[register_processor(event)]
    fn rgb_status() -> RgbPwmProcessor {
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm = embassy_nrf::pwm::SimplePwm::new_3ch(p.PWM0, p.P1_06, p.P1_04, p.P0_09, &config);
        RgbPwmProcessor::new(
            pwm,
            RgbChannels {
                red: 1,
                green: 2,
                blue: 0,
            },
        )
    }
}
