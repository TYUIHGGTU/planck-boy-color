#![no_main]
#![no_std]

mod revisions;
mod rgb_pwm;

use rmk::macros::rmk_central;

#[rmk_central]
mod keyboard_central {
    #[register_processor(event)]
    fn rgb_status() -> crate::rgb_pwm::RgbPwmProcessor {
        crate::revisions::selected::central_processor!(p)
    }
}
