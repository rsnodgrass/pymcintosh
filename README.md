# Python API for McIntosh A/V Processors

Library for RS232 serial communication to Xantech, Monoprice, Dayton Audio, Soundavo, and other multi-zone amps.
This supports any serial protocol for communicating with the amps, including RS232 ports,
USB serial ports, and possibly the RS232-over-IP interface for more recent Xantech amps. See below
for exactly which amplifier models are supported.

Based on [pyxantech](https://github.com/rsnodgrass/pyxantech).

*GOAL: To eventually merge this with pymonoprice and get rid of a separate implementation.*

The Monoprice version was originally created by Egor Tsinko for use with [Home-Assistant](http://home-assistant.io).

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![PyPi](https://img.shields.io/pypi/v/pyxantech.svg)](https://pypi.python.org/pypi/pyxantech)
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT)
[![Build Status](https://github.com/rsnodgrass/pyxantech/actions/workflows/ci.yml/badge.svg)](https://github.com/rsnodgrass/pyxantech/actions/workflows/ci.yml)

## Support

Visit the [community support discussion thread](https://community.home-assistant.io/t/xantech-dayton-audio-sonance-multi-zone-amps/450908) for issues with this library.





RS232 control:

- serial
- IP
- USB

independently of the physical communication mechanism (e.g. RS232, USB, IP)

## Example libraries







# See Also

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


## Supported Amplifiers

See *[pymcintosh](https://github.com/rsnodgrass/pymcintosh)* for a full list of supported hardware.

| Model(s) |   Type    | Protocol | Supported | Notes |
|----------|:---------:| :---------:|:-----:|----|
| MX160    | Processor | V2 | YES       |  Serial/IP     |
| MX170    | Processor  | V2 | YES | Serial/IP
| MX180    | Processor  | V2 | *UNTESTED*  | Serial/IP
| MHT300   | Receiver   | V2 | *UNTESTED* |
| MX123    | Processor  | V2 | *UNTESTED* |
| MX100    | Processor  | V2 |*UNTESTED* |
| MAC7200  | Receiver | V? | 2-ch |

| MHT100 | Receiver | V1 | NO | 
| MHT200 | Receiver | V1 | NO |

| MX100  | Processor | V1 | NO |
| MX118  | Processor | V1 | NO |
| MX119 | Processor | V1 | NO |
| MX120 | Processor | V1 | NO |
| MX121 | Processor | V1 | NO | Serial/IP
| MX122 | Processor | V1 | NO |
| MX123 | Processor | V1 | NO |
| MX130 | Processor | V1 | NO |
| MX132 | Processor | V1 | NO |
| MX134 | Processor | V1 | NO |
| MX135 | Processor | V1 | NO |
| MX136 | Processor | V1 | NO |
| MX150 | Processor | V1 | NO |
| MX151  | Processor | V1 | NO | Serial/IP

| C48 | Receiver | ? | NO | serial RS232-C (3.5mm)

| MA5200 | Amp | ? | NO | serial RS232-C (3.5mm)

See also: https://drivers.control4.com/solr/drivers/browse?q=mcintosh

# Example of pyserial over TCP socket

```console
import serial
ser = serial.serial_for_url("socket://10.10.10.152:/")
```

## Later Protocol

<https://www.docdroid.net/OnipkTW/mx160-serial-control-manual-v3-pdf>

## Early Protocol

Two different protocols it seems. The earlier one is documented here:

<https://github.com/RobKikta/IntoBlue/blob/master/McIntosh_RS232ControlApplicationNote.pdf>

Earlier McIntosh control in Home Assistant:
<https://community.home-assistant.io/t/need-help-using-rs232-to-control-a-receiver/95210/8>

Some McIntosh have a 3.5mm RS-232 connector jack (such as the MA5200). Default baudrate is 115,200, 8N1 for those units. The command set differs from later
ones. This is

E.g.

```console
VUP Z1 5
```

Increases volume in Zone 1 by 5 steps.
