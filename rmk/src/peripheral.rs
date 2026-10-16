#![no_main]
#![no_std]

mod revisions;
mod rgb_pwm;

use rmk::macros::rmk_peripheral;

#[rmk_peripheral(id = 0)]
mod keyboard_peripheral {
    use crate::rgb_pwm::RgbPwmProcessor;

    #[register_processor(event)]
    fn rgb_status() -> RgbPwmProcessor {
        crate::revisions::selected::peripheral_processor!(p)
    }
}
