#[allow(unused_macros)]
macro_rules! central_processor {
    ($p:ident) => {{
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm =
            embassy_nrf::pwm::SimplePwm::new_3ch($p.PWM0, $p.P0_09, $p.P1_06, $p.P1_04, &config);
        crate::rgb_pwm::RgbPwmProcessor::new(
            pwm,
            crate::rgb_pwm::RgbChannels {
                red: 1,
                green: 2,
                blue: 0,
            },
        )
    }};
}

#[allow(unused_macros)]
macro_rules! peripheral_processor {
    ($p:ident) => {{
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm =
            embassy_nrf::pwm::SimplePwm::new_3ch($p.PWM0, $p.P1_03, $p.P1_07, $p.P1_05, &config);
        crate::rgb_pwm::RgbPwmProcessor::new(
            pwm,
            crate::rgb_pwm::RgbChannels {
                red: 2,
                green: 1,
                blue: 0,
            },
        )
    }};
}

#[allow(unused_imports)]
pub(crate) use central_processor;
#[allow(unused_imports)]
pub(crate) use peripheral_processor;
