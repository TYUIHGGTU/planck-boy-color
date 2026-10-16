#[allow(unused_macros)]
macro_rules! central_processor {
    ($p:ident) => {{
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm =
            embassy_nrf::pwm::SimplePwm::new_3ch($p.PWM0, $p.P1_06, $p.P1_04, $p.P0_09, &config);
        crate::rgb_pwm::RgbPwmProcessor::new(
            pwm,
            crate::rgb_pwm::RgbChannels {
                red: 0,
                green: 1,
                blue: 2,
            },
        )
    }};
}

#[allow(unused_macros)]
macro_rules! peripheral_processor {
    ($p:ident) => {{
        let config = embassy_nrf::pwm::SimpleConfig::default();
        let pwm =
            embassy_nrf::pwm::SimplePwm::new_3ch($p.PWM0, $p.P1_07, $p.P1_05, $p.P1_03, &config);
        crate::rgb_pwm::RgbPwmProcessor::new(
            pwm,
            crate::rgb_pwm::RgbChannels {
                red: 1,
                green: 0,
                blue: 2,
            },
        )
    }};
}

#[allow(unused_imports)]
pub(crate) use central_processor;
#[allow(unused_imports)]
pub(crate) use peripheral_processor;
