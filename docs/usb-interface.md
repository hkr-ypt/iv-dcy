# USB interface

All values below come from
[`firmware/src/usb_identity.h`](../firmware/src/usb_identity.h) and
[`firmware/src/usb_descriptors.c`](../firmware/src/usb_descriptors.c).
The host unit test `descriptors` checks them.

## Device

| Field | Value |
|---|---|
| bcdUSB | 2.00 (full speed, 12 Mbit/s) |
| idVendor | `0x1209` (pid.codes) |
| idProduct | `0x6767`: to be requested from pid.codes, **not yet assigned** |
| bcdDevice | firmware version as `0xJJMN` (0.1.0 → `0x0010`) |
| Class / subclass / protocol | `0xEF` / `0x02` / `0x01`: miscellaneous, interface association |
| bMaxPacketSize0 | 64 |
| Manufacturer string | `IV-DCY project` |
| Product string | `IV-DCY USB reference` |
| Serial number string | the STM32's 96-bit unique ID as 24 upper-case hex digits |
| Configurations | 1: bus powered, 100 mA maximum, no remote wake-up |

## Configuration 1

| Interface | Class | Endpoints | String |
|---|---|---|---|
| 0: CDC communication | `0x02` / ACM `0x02` / no protocol | `0x81` interrupt IN, 8 bytes (notifications) | `IV-DCY CDC` |
| 1: CDC data | `0x0A` | `0x02` bulk OUT, 64 bytes; `0x82` bulk IN, 64 bytes | none |

An interface association descriptor groups interfaces 0 and 1 into one CDC
function. The total configuration descriptor length is 75 bytes. Linux, macOS
and Windows 10 or later bind their built-in CDC-ACM drivers; no driver or INF
file is needed.

## Command protocol

The command protocol runs over the CDC data interface. The line coding
(baud rate, parity) is accepted and ignored. Commands are ASCII, one per
line, terminated by CR, LF or CR LF. They are case-insensitive, at most 32
characters long, and are not echoed. Each command produces exactly one reply
line ending in CR LF. Blank lines produce no reply.

| Command | Reply |
|---|---|
| `PING` | `PONG` |
| `VERSION` | firmware version, `MAJOR.MINOR.PATCH` |
| `INFO` | `<product> fw=<version> vid=0x1209 pid=0x6767 serial=<24 hex digits>` |
| `LED ON` / `LED OFF` / `LED AUTO` | `OK` |
| `BUTTON` | `PRESSED` or `RELEASED` (state of the BOOT button) |
| `HELP` | `commands: PING VERSION INFO LED ON\|OFF\|AUTO BUTTON HELP` |

Errors: `ERR unknown command`, `ERR unexpected argument`,
`ERR usage: LED ON|OFF|AUTO`, `ERR line too long`. After a line that is too
long, the rest of that line is discarded.

Example session:

```
> PING
< PONG
> INFO
< IV-DCY USB reference fw=0.1.0 vid=0x1209 pid=0x6767 serial=003800273536510B20313748
```

The serial number shown is an example.

## Linux note

On some distributions ModemManager briefly probes every new `ttyACM` port. To
stop it doing so for this device, add a udev rule such as:

```
ATTRS{idVendor}=="1209", ATTRS{idProduct}=="6767", ENV{ID_MM_DEVICE_IGNORE}="1"
```
