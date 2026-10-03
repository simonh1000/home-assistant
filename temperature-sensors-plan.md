# Temperature sensors: action plan

## Goal

Record the real room temperature in the living zone (lounge, kitchen, master bedroom) and outdoors, in Home Assistant, over days and seasons. Start before the heat pump is installed, so there is a winter baseline to compare against afterwards.

The heat pump's own sensor is not enough. It sits high on the wall at the indoor unit and reads warm while heating and cool while cooling.

## Setup at a glance

- Home Assistant runs in the garage (north side of the house).
- Kitchen is directly above the garage. Lounge Wi-Fi is sometimes patchy.
- Zigbee sensors (battery) report to a Zigbee coordinator plugged into the Home Assistant machine.
- Mains-powered Zigbee plugs act as relays, but only add them where the signal is weak.

## Shopping list

| Item | Qty | Notes |
|------|-----|-------|
| Home Assistant Connect ZBT-2 (Zigbee coordinator) | 1 | Official stick, comes with a USB cable. Zigbee or Thread, not both; Zigbee is what we need. |
| Zigbee temperature/humidity sensor (e.g. Aqara) | 4 | Lounge, kitchen, master bedroom, outdoors. Confirm the current model and that it works with ZHA before buying. |
| Mains Zigbee smart plug | 0 for now | Buy 1-2 only if the signal test fails (see phase 3). |

## Phases

### 1. Before ordering
- [ ] Confirm the garage machine has a free USB-A port.
- [ ] Note what Home Assistant runs on (Raspberry Pi, mini PC, virtual machine). A virtual machine needs the USB device passed through.
- [ ] Check the shop page for what comes in the box and the price.

### 2. Set up the coordinator
- [ ] Plug in the ZBT-2 using its cable, upright and a metre or so from the computer, away from metal and USB 3 ports, as high as practical.
- [ ] Home Assistant should detect it and offer Zigbee (ZHA). Accept the recommended settings.
- [ ] Choose Zigbee channel 15, 20 or 25 and fix the router's 2.4 GHz Wi-Fi channel to 1, 6 or 11, to avoid interference.
- [ ] Pair one sensor next to the coordinator and confirm it shows a temperature.

### 3. Test the signal room by room
- [ ] Place a sensor in the kitchen, check signal quality (LQI) and look at the history for a day or two.
- [ ] Repeat for the lounge and the master bedroom.
- [ ] Weak or dropping out? Add a mains Zigbee plug between that room and the garage, then re-test. Kitchen is the most likely room to need one (concrete floor above the garage).
- [ ] Strong everywhere? No plugs needed.

### 4. Permanent positions
- [ ] Lounge: at sofa height, away from sun and from where the indoor unit will blow.
- [ ] Kitchen: away from the hob, oven and kettle.
- [ ] Master bedroom: at bed height.
- [ ] Outdoors: north side near the garage, shaded and sheltered from rain, clear of vents and the garage door, and away from where the outdoor heat pump will blow.

### 5. Record and display in Home Assistant
- [ ] Name the sensors clearly, for example `lounge_temperature`.
- [ ] Build one history graph: three room temperatures, outdoor temperature, and later the heat pump's setpoint and its own temperature.
- [ ] Keep the baseline running through the winter before the installation if timing allows.

### 6. After the heat pump is installed
- [ ] Add the heat pump's own temperature and mode to the same graph (via its Home Assistant integration or adapter).
- [ ] Compare the real room temperature with the setpoint across cold days and heatwaves.

## Open questions

- What does the Home Assistant machine run on?
- Which exact sensor model? Check availability and Home Assistant support.
- Does the heat pump's local interface expose indoor and outdoor temperature and power? Ask the installer (checklist questions 4.1 and 4.3).
