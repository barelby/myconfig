import logging
import time

from homeassistant.const import *

from . import DOMAIN, Gateway3Device
from .gateway3 import Gateway3

_LOGGER = logging.getLogger(__name__)

UNITS = {
    DEVICE_CLASS_TEMPERATURE: TEMP_CELSIUS,
    DEVICE_CLASS_HUMIDITY: '%',
    DEVICE_CLASS_PRESSURE: 'hPa',
    DEVICE_CLASS_ILLUMINANCE: 'lm',
    DEVICE_CLASS_POWER: POWER_WATT,
    'consumption': ENERGY_WATT_HOUR,
    'gas density': '% LEL',
    'smoke density': '% obs/ft',
}

ICONS = {
    'consumption': 'mdi:flash',
    'gas density': 'mdi:google-circles-communities',
    'smoke density': 'mdi:google-circles-communities',
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    def setup(gateway: Gateway3, device: dict, attr: str):
        async_add_entities([
            Gateway3Action(gateway, device, attr)
            if attr == 'action' else
            Gateway3Sensor(gateway, device, attr)
        ])

    gw: Gateway3 = hass.data[DOMAIN][config_entry.unique_id]
    gw.add_setup('sensor', setup)


class Gateway3Sensor(Gateway3Device):
    @property
    def state(self):
        return self._state

    @property
    def device_class(self):
        return self._attr

    @property
    def unit_of_measurement(self):
        return UNITS.get(self._attr)

    @property
    def icon(self):
        return ICONS.get(self._attr)

    def update(self, data: dict = None):
        if self._attr not in data:
            return
        self._state = data[self._attr]
        self.schedule_update_ha_state()


# https://github.com/Koenkk/zigbee-herdsman-converters/blob/master/converters/fromZigbee.js#L4738
BUTTON = {
    1: 'single',
    2: 'double',
    3: 'triple',
    4: 'quadruple',
    16: 'hold',
    17: 'release',
    18: 'shake',
    128: 'many',
}

BUTTON_BOTH = {
    4: 'single',
    5: 'double',
    6: 'triple',
    16: 'hold',
    17: 'release',
}

VIBRATION = {
    1: 'vibration',
    2: 'tilt',
    3: 'drop',
}


class Gateway3Action(Gateway3Device):
    _state = ''

    @property
    def state(self):
        return self._state

    @property
    def state_attributes(self):
        return self._attrs

    def update(self, data: dict = None):
        for k, v in data.items():
            if k == 'button':
                data[self._attr] = BUTTON[v]
                break
            elif k == 'button_both':
                data[self._attr] = k + '_' + BUTTON_BOTH[v]
                break
            elif k.startswith('button'):
                data[self._attr] = k + '_' + BUTTON[v]
                break
            elif k == 'vibration' and v != 2:  # skip tilt and wait tilt_angle
                data[self._attr] = VIBRATION[v]
                break
            elif k == 'tilt_angle':
                data = {'vibration': 2, 'angle': v, self._attr: 'tilt'}
                break

        if self._attr not in data:
            return

        self._attrs = data
        self._state = data[self._attr]
        self.async_write_ha_state()

        time.sleep(.1)

        self._state = ''
        self.async_schedule_update_ha_state()
