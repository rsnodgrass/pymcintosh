# Python API for McIntosh and Lyngdorf A/V Processors

![McIntosh](https://raw.githubusercontent.com/rsnodgrass/pymcintosh/main/img/mcintosh-logo.png)

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![PyPi](https://img.shields.io/pypi/v/pymcintosh.svg)](https://pypi.python.org/pypi/pymcintosh)
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)
[![Build Status](https://github.com/rsnodgrass/pymcintosh/actions/workflows/ci.yml/badge.svg)](https://github.com/rsnodgrass/pymcintosh/actions/workflows/ci.yml)

This library was created to control McIntosh and Lyngdorf A/V equipment using their
text-based control protocols over RS232, USB serial connections, and remote IP sockets for the purpose of
building a [Home Assistant](https://home-assistant.io) integration as well as a command line tool.

This has been derived from an earlier effort with [pyxantech](https://github.com/rsnodgrass/pyxantech) to explore a new way to define the protocol to enable
automated or programmatic, along with support for a variety
of amps and protocols.

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=WREP29UDAMB6G)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/DYks67r)

# THIS IS IN DEVELOPMENT - DOES NOT WORK YET!!!

## Support

Visit the [community support discussion thread](https://community.home-assistant.io/t/mcintosh/) for issues with this library.

## Supported Equipment

See [SUPPORTED.md](SUPPORTED.md) for the complete list of supported equipment.
Brands supported:

- McIntosh
- Lyngdorf

## Background

One annoying thing when developing `pyxantech` was that none of the devices
ever had a protocol definition in a machine-readable format. Manufacturers
would provide a PDF or XLS document (if anything at all) that listed
the various commands that could be sent via RS232. However, there was no
consistency for what were generally very similar callable actions when
controlling preamps/receivers/etc.

During the development of `pyxantech` it became clear that other manufacturers
had copied the protocol developed by Xantech, with each
manufacturer just making a very small change in the prefixes or suffixes.
From this, a very primitive mechanism was built. YAML was chosen
to be a machine-readable format that was also easily read/updated by humans
who may have limited programming skills.

This makes it easier and quicker to
add support for new devices without having to build an entirely new library each
time (with varying semantics and degrees of testing/clarity/documentation).
Additionally, these definitions make it possible to create similar libraries in
a variety of languages, all sharing the same protocol definitions.

The evolution found in this `pymcintosh` library takes these ideas further by
having a much more cohesive definition of protocols. Additional ideas were
discovered in [onkyo-eiscp](https://github.com/miracle2k/onkyo-eiscp) around
providing a simple CLI to use the library and grouping commands together
logically. These ideas combined with the argument definitions and pattern
matching from `pyxantech` moved these ideas closer to reality.

If you are trying to implement your own interface to McIntosh in other
languages besides Python, you should consider using the YAML series and
protocol files from this repository as a basis for the interface you provide.
The protocol and series definitions will likely be split out into separate
definition-only package(s) in the future.

## Asynchronous / Synchronous

This library provides both an async and a sync implementation. By default, the
synchronous implementation is returned when instantiating new controller objects
unless an `event_loop` is passed into the `create_equipment_controller` factory
constructor. For example:

```console
    equipment = create_equipment_controller(
        args.type,
        args.url,
        serial_config_overrides=config,
        event_loop=asyncio.get_event_loop(),
    )
    await equipment.power.off()
```

## Connection URL

This interface uses URLs for specifying the communication transport
to use, as defined in [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html), to allow a wide variety of underlying mechanisms.

For example:

| URL                      | Notes                                     |
|--------------------------|-------------------------------------------|
| `/dev/ttyUSB0`           | directly attached serial device (Linux)  |
| `COM3`                   | directly attached serial device (Windows) |
| `socket://<host>:<port>` | remote host that exposes RS232 over TCP (e.g. [IP2SL](https://github.com/rsnodgrass/virtual-ip2sl)) |

See [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html) for additional formats supported.

# Future Ideas

- review [pykaliedescape](https://github.com/SteveEasley/pykaleidescape)
- https://github.com/joopert/nad_receiver
- Add programmatic override/enhancements to the base protocol where pure
  YAML configuration would not work fully. Of course, these overrides would have
  to be implemented in each language, but that surface area should be much smaller.

# See Also

- [Earlier McIntosh control in Home Assistant](https://community.home-assistant.io/t/need-help-using-rs232-to-control-a-receiver/95210/8)
- https://drivers.control4.com/solr/drivers/browse?q=mcintosh
