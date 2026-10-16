#![no_main]
#![no_std]

mod revisions;
mod rgb_pwm;

use rmk::macros::rmk_peripheral;

#[rmk_peripheral(id = 0)]
mod keyboard_peripheral {
    #[register_processor(event)]
    fn rgb_status() -> crate::rgb_pwm::RgbPwmProcessor {
        crate::revisions::selected::peripheral_processor!(p)
    }
}
