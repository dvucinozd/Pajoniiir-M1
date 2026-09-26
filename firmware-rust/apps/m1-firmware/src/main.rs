#![no_std]
#![no_main]
#![deny(clippy::mem_forget)]

use esp_hal::{clock::CpuClock, main};

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    esp_hal::system::software_reset()
}

#[main]
fn main() -> ! {
    let config = esp_hal::Config::default().with_cpu_clock(CpuClock::max());
    let _peripherals = esp_hal::init(config);

    // Compile-time anchors: the production target must keep the host-tested
    // product crates no_std-compatible on the real ESP32-P4 architecture.
    let _ = core::mem::size_of::<pajoniiir_controller_session::ControllerSession>();
    let _ = core::mem::size_of::<pajoniiir_deck::DeckProductState>();
    let _ = core::mem::size_of::<pajoniiir_hot_cues::HotCueBank>();
    let _ = core::mem::size_of::<pajoniiir_mixer::MixerState>();
    let _ = core::mem::size_of::<pajoniiir_media_usb_msc::UsbMscCapacity>();
    let _ = core::mem::size_of::<pajoniiir_ui_model::UiSnapshot>();
    let _ = core::mem::size_of::<pajoniiir_waveform::WaveformColumn>();

    loop {
        core::hint::spin_loop();
    }
}
