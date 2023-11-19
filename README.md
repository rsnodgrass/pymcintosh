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

# THIS IS IN DEVELOPMENT - DOES NOT WORK YET!!!

## Support

Visit the [community support discussion thread](https://community.home-assistant.io/t/mcintosh/450908) for issues with this library.

## Supported Equipment

See [SUPPORTED.md](SUPPORTED.md) for the complete list of supported equipment.
an

## Asynchronous / Synchronous

This library provides both an async and a sync implementation. By default, the
synchronous implementation is returned unless an `event_loop` is passed into
the `create_equipment_controller` factory constructor. For example:

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
to use, as defined in [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html).

Examples:

| URL                      | Notes |
|--------------------------|-------|
| `/dev/ttyUSB0`           | directly attached serial device on Linux |
| `COM3`                   | directly attached serial device on Windows |
| `socket://<host>:<port>` | remote host that exposes RS232 over TCP |

See [pyserial](https://pyserial.readthedocs.io/en/latest/url_handlers.html for additional formats supported.

## See Also

* https://github.com/miracle2k/onkyo-eiscp

- has command line utility for control!
- maps commands to RS232 protocoli with descriptions using OrderedDict (https://github.com/miracle2k/onkyo-eiscp/blob/master/eiscp/commands.py) with some range limits
- generates the commands from yaml using 'generate_commands_module.py'
- has config to specify which models a command applies to
- either confusing or brilliant..not sure

"The idea is to have a computer-readable definition of the Onkyo protocol, where Onkyo's internal low-level commands are mapped to identifiers that can be understood by humans, and which include descriptions."

"To summarize, if you are implementing your own interface to Onkyo, even if it's in a language other than Python, I encourage you to consider using this YAML file as a basis for the command interface you provide to users. You'll have a complete list of available commands, values, and even supported devices."


#### NAD

https://github.com/joopert/nad_receiver



#### Kaliedescape

https://github.com/home-assistant/core/tree/dev/homeassistant/components/kaleidescape

- fully config flow
- **recent HA integration, so has all the modern features**

- pykaliedescape was created within last 2 years by a Principal Engineer (https://github.com/SteveEasley/pykaleidescape)




See also: https://drivers.control4.com/solr/drivers/browse?q=mcintosh

# See Also

- [Earlier McIntosh control in Home Assistant](https://community.home-assistant.io/t/need-help-using-rs232-to-control-a-receiver/95210/8)
