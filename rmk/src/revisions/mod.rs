#[cfg(all(feature = "hw-r1", feature = "hw-r2"))]
compile_error!("features `hw-r1` and `hw-r2` are mutually exclusive");

#[cfg(not(any(feature = "hw-r1", feature = "hw-r2")))]
compile_error!("select exactly one hardware revision feature: `hw-r1` or `hw-r2`");

#[cfg(feature = "hw-r1")]
pub(crate) mod r1;
#[cfg(feature = "hw-r2")]
pub(crate) mod r2;

#[cfg(feature = "hw-r1")]
pub(crate) use r1 as selected;
#[cfg(feature = "hw-r2")]
pub(crate) use r2 as selected;
