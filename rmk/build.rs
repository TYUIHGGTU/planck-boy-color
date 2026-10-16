use std::env;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use const_gen::{CompileConst, const_declaration};
use xz2::read::XzEncoder;

fn main() {
    println!("cargo:rerun-if-changed=keyboard.toml");
    println!("cargo:rerun-if-changed=vial.json");
    println!("cargo:rerun-if-changed=memory.x");

    generate_vial_config();

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR is set by Cargo"));
    File::create(out.join("memory.x"))
        .expect("create generated memory.x")
        .write_all(include_bytes!("memory.x"))
        .expect("copy memory.x");
    println!("cargo:rustc-link-search={}", out.display());
    println!("cargo:rustc-link-arg=--nmagic");
    println!("cargo:rustc-link-arg=-Tlink.x");
    println!("cargo:rustc-link-arg=-Tdefmt.x");
}

fn generate_vial_config() {
    let out_file = Path::new(&env::var_os("OUT_DIR").expect("OUT_DIR is set by Cargo"))
        .join("config_generated.rs");
    let mut content = String::new();
    File::open("vial.json")
        .expect("open vial.json")
        .read_to_string(&mut content)
        .expect("read vial.json");

    let vial_config = json::stringify(json::parse(&content).expect("parse vial.json"));
    let mut keyboard_def_compressed = Vec::new();
    XzEncoder::new(vial_config.as_bytes(), 6)
        .read_to_end(&mut keyboard_def_compressed)
        .expect("compress vial.json");

    // Stable project-local ID. Change this if this layout is forked incompatibly.
    let keyboard_id: Vec<u8> = vec![0x50, 0x42, 0x43, 0x52, 0x4D, 0x4B, 0x00, 0x01];
    let declarations = [
        const_declaration!(pub VIAL_KEYBOARD_DEF = keyboard_def_compressed),
        const_declaration!(pub VIAL_KEYBOARD_ID = keyboard_id),
    ]
    .map(|declaration| {
        "#[allow(clippy::redundant_static_lifetimes)]\n".to_owned() + declaration.as_str()
    })
    .join("\n");

    fs::write(out_file, declarations).expect("write generated Vial configuration");
}
