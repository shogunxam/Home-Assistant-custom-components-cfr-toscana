

from datetime import timedelta
import logging
import urllib.request
import re
import json
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, STATE_UNKNOWN, TEMP_CELSIUS, LENGTH_METERS, SPEED_MS)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

__version__ = '1.1.0'

TYPE_IDRO = 'idro'
TYPE_PLUVIO = 'pluvio'
TYPE_TERMO = 'termo'
TYPE_ANEMO = 'anemo'
TYPE_IGRO = 'igro'
STATION_TYPES = [TYPE_IDRO,TYPE_PLUVIO,TYPE_TERMO,TYPE_ANEMO,TYPE_IGRO]

CONF_STATIONID = 'station'
CONF_TYPE = 'type'

ATTR_DATE = 'data'
ATTR_TIME = 'time'
ATTR_ALTEZZA = 'altezza'
ATTR_PORTATA = 'portata'
ATTR_ACCUMULO = 'accumulo' 
ATTR_PRECIPITAZIONI = 'precipitazioni' 
ATTR_TEMPERATURA = 'temperatura'
ATTR_VELOCITA = 'velocita'
ATTR_RAFFICA = 'raffica'
ATTR_DIREZIONE = 'direzione'
ATTR_UMIDITA = 'umidita'

DEFAULT_NAME = 'CFRToscana'
#Arno Firenze Uffizi
DEFAULT_STATIONID = 'TOS01004679'
DEFAULT_TYPE = TYPE_IDRO

ICON = {TYPE_IDRO : 'mdi:waves', TYPE_PLUVIO : 'mdi:weather-pouring',TYPE_TERMO : 'mdi:thermometer',TYPE_ANEMO :'mdi:weather-windy', TYPE_IGRO : 'mdi:water-percent'}

SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_STATIONID): cv.string,
    vol.Required(CONF_TYPE): 
        vol.In(STATION_TYPES),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    name = config.get(CONF_NAME)
    stationID = config.get(CONF_STATIONID)
    dataType = config.get(CONF_TYPE)
    add_entities([cfr(name,stationID, dataType)])


class cfr(Entity):
    """The sensor class."""

    def __init__(self, name, stationID, dataType):
        """Initialize the sensor platform."""
        self._name = name
        self._stationID = stationID
        self._type = dataType
        self._state = None
        self._date = None
        self._time = None
        self._value1 = None
        self._value2 = None
        self.update()

    @Throttle(SCAN_INTERVAL)
    def update(self):

        """Update the sensor values."""
        url = "http://www.cfr.toscana.it/monitoraggio/dettaglio.php?id="+self._stationID+"&type="+self._type
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        respData = resp.read()

        tds = re.findall(r'VALUES\[\d+\] = new Array\("(.*?)","(.*?)","(.*?)","(.*?)"\);',str(respData))

        self._value3 = None

        if len(tds) > 5:
            self._state = 'on'
            lastEvent = tds[-1]

            try:
                date_time = re.findall(r'(\d{2}\/\d{2}\/\d{4}) (\d{2}.\d{2})', lastEvent[1])
                self._date = date_time[0][0]
                self._time = date_time[0][1]
            except IndexError:
                self._date = None
                self._time = None
            try:
                self._value1 = lastEvent[2]
                if self._type== TYPE_ANEMO:
                    values = self._value1.split("/")
                    self._value1 = values[0]
                    self._value3 = values[1]
                
            except IndexError:
                self._value1 = None
            try:
                self._value2 = lastEvent[3]
            except IndexError:
                self._value2 = None
        else :
            self._state = None
            self._date = None
            self._time = None
            self._value1 = None
            self._value2 = None
        self._state = self._value1

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON[self._type]

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._type == TYPE_IDRO :
            return LENGTH_METERS
        elif self._type == TYPE_PLUVIO:
            return 'mm'
        elif self._type == TYPE_ANEMO:
            return 'ms'
        elif self._type == TYPE_TERMO:
            return TEMP_CELSIUS
        elif self._type == TYPE_IGRO:
            return '%'

    @property
    def device_state_attributes(self):
        """Return attributes of the sensor."""
        #Common attributes
        attributes = {}
        attributes[ATTR_DATE] = self._date
        attributes[ATTR_TIME] = self._time
        
        #Specific Attributes
        if self._type == TYPE_IDRO :
            attributes[ATTR_ALTEZZA] = self._value1
            attributes[ATTR_PORTATA] = self._value2
        elif  self._type == TYPE_PLUVIO: 
            attributes[ATTR_ACCUMULO] = self._value1
            attributes[ATTR_PRECIPITAZIONI] = self._value2
        elif  self._type == TYPE_ANEMO:            
            attributes[ATTR_VELOCITA] = self._value1
            attributes[ATTR_RAFFICA] = self._value3
            attributes[ATTR_DIREZIONE] = self._value2
        elif  self._type == TYPE_TERMO:
            attributes[ATTR_TEMPERATURA] = self._value1
        elif  self._type == TYPE_IGRO:
            attributes[ATTR_UMIDITA] = self._value1          

        return attributes

