# Architecture

## Target user experience

Install once, approve the macOS camera extension once, then:

1. Plug in PS3 Eye.
2. A small background process detects and opens it.
3. Video frames are passed to a CoreMediaIO Camera Extension.
4. Apps see a normal camera named `PlayStation Eye`.

## Components

```text
PS3 Eye (USB)
      |
      v
userspace capture process
(libUSB + PS3 Eye protocol)
      |
      v
shared frame transport
      |
      v
CoreMediaIO Camera Extension
      |
      v
Zoom / Meet / Discord / QuickTime / OBS / etc.
```

## Why userspace USB

The PS3 Eye is not a normal UVC webcam, so macOS does not expose it automatically as a camera. libusb lets ordinary userspace software communicate with the camera without writing a kernel extension.

## Why a Camera Extension

Modern macOS uses CoreMediaIO Camera Extensions to publish custom cameras. This is Apple's replacement for old DAL plug-ins and avoids disabling System Integrity Protection.

## Implementation order

### Milestone A — included in v0.1

- confirm macOS enumerates the USB device
- open the camera through libusb-backed PS3 Eye code
- read 640x480 RGB frames
- display a stable live preview

### Milestone B — next

- native long-running capture helper
- automatic reconnect after unplug/replug
- efficient shared frame transport
- CoreMediaIO camera extension
- one-time extension installer/approval flow

### Milestone C — polish

- LaunchAgent/login startup
- menu-bar status
- resolution/FPS controls
- optional microphone investigation

## Important engineering choice

The camera extension should not contain the PS3 Eye USB implementation itself. Keeping USB capture in a separate process means the camera can reconnect/crash/restart independently without destabilizing the system camera extension.
