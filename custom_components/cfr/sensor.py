
from datetime import timedelta
from datetime import datetime
from threading import Thread, Lock

import logging
import copy
import urllib.request
import re
import json
import voluptuous as vol
import time
#import traceback

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, STATE_UNKNOWN, TEMP_CELSIUS, LENGTH_METERS, SPEED_METERS_PER_SECOND)
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
CONF_TIMEOUT = 'timeout'

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
DEFAULT_TIMEOUT = 30

ICON = {TYPE_IDRO : 'mdi:waves', TYPE_PLUVIO : 'mdi:weather-pouring',TYPE_TERMO : 'mdi:thermometer',TYPE_ANEMO :'mdi:weather-windy', TYPE_IGRO : 'mdi:water-percent'}
UNITS = {TYPE_IDRO : LENGTH_METERS, TYPE_PLUVIO : 'mm',TYPE_TERMO : TEMP_CELSIUS,TYPE_ANEMO :'m/s', TYPE_IGRO : '%'}

SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Required(CONF_STATIONID): cv.string,
    vol.Required(CONF_TYPE): 
        vol.In(STATION_TYPES),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the platform."""
    sensors = []
    name = config.get(CONF_NAME)
    stationID = config.get(CONF_STATIONID)
    timeout = config.get(CONF_TIMEOUT)
    dataType = config.get(CONF_TYPE)
    sensors.append(cfr(name, stationID, dataType, timeout))
    async_add_entities(sensors)


class cfr(Entity):
    """The sensor class."""

    def __init__(self, name, stationID, dataType, timeout):
        """Initialize the sensor platform."""
        self._name = name
        self._type = dataType
        self._timeout = timeout
        self._stationID = stationID
        self._unit = UNITS[ self._type]
        self._icon = ICON[ self._type]
        self.data = cfr_data()
        _LOGGER.info('Component %s initialized', name)

    async def async_added_to_hass(self):
        _LOGGER.info('Component %s added to hass', self._name)
        self._updater = cfrUpdater(self._stationID, self._type , self.UpdateNeeded, self._timeout)
        self._updater.StartUpdate()

    async def async_update(self):
        """Update the sensor values."""
        self.data = self._updater.GetLastData()

    def UpdateNeeded(self):
        """Ask to Home Assistant to schedule an update of the sensor"""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.data.state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def should_poll(self):
        """Updates are requested when new data is available by the cfrUpdater"""
        return False

    @property
    def device_state_attributes(self):
        """Return attributes of the sensor."""
        #Common attributes
        attributes = {}
        attributes[ATTR_DATE] = self.data.date
        attributes[ATTR_TIME] = self.data.time
        
        #Specific Attributes
        if self._type == TYPE_IDRO :
            attributes[ATTR_ALTEZZA] = self.data.value1
            attributes[ATTR_PORTATA] = self.data.value2
        elif  self._type == TYPE_PLUVIO: 
            attributes[ATTR_ACCUMULO] = self.data.value1
            attributes[ATTR_PRECIPITAZIONI] = self.data.value2
        elif  self._type == TYPE_ANEMO: 
            attributes[ATTR_VELOCITA] = self.data.value1
            attributes[ATTR_RAFFICA] = self.data.value3
            attributes[ATTR_DIREZIONE] = self.data.value2
        elif  self._type == TYPE_TERMO:
            attributes[ATTR_TEMPERATURA] = self.data.value1
        elif  self._type == TYPE_IGRO:
            attributes[ATTR_UMIDITA] = self.data.value1

        return attributes

    @property
    def extra_state_attributes(self):
        """Return attributes of the sensor."""
        #Common attributes
        attributes = {}
        attributes[ATTR_DATE] = self.data.date
        attributes[ATTR_TIME] = self.data.time
        
        #Specific Attributes
        if self._type == TYPE_IDRO :
            attributes[ATTR_ALTEZZA] = self.data.value1
            attributes[ATTR_PORTATA] = self.data.value2
        elif  self._type == TYPE_PLUVIO: 
            attributes[ATTR_ACCUMULO] = self.data.value1
            attributes[ATTR_PRECIPITAZIONI] = self.data.value2
        elif  self._type == TYPE_ANEMO:
            attributes[ATTR_VELOCITA] = self.data.value1
            attributes[ATTR_RAFFICA] = self.data.value3
            attributes[ATTR_DIREZIONE] = self.data.value2
        elif  self._type == TYPE_TERMO:
            attributes[ATTR_TEMPERATURA] = self.data.value1
        elif  self._type == TYPE_IGRO:
            attributes[ATTR_UMIDITA] = self.data.value1 

        return attributes


class cfr_data:
    def __init__(self):
        self.state = None
        self.date = None
        self.time = None
        self.value1 = None
        self.value2 = None
        self.value3 = None

class cfrUpdater:
    def __init__(self, stationID, dataType, callback, timeout):
        self._stationID = stationID
        self._type = dataType
        self._timeout = timeout
        self._lastData = cfr_data()
        self._data = cfr_data()
        self.updateThread = Thread(target=self.updateLoop)
        self.mutex = Lock()
        self.updaterequiredCallback = callback
    
    def StartUpdate(self):
        """Starts the Thread  used to update the sensor"""
        self.updateThread.start()

    def GetLastData(self):
        """Returns the last available data"""
        self.mutex.acquire()
        try:
            lastData = copy.deepcopy(self._lastData)
        finally:
            self.mutex.release()
        return lastData

    def updateLoop(self):
        """Main update loop"""
        while True:
            try:
                _LOGGER.info('Updater loop started (station:%s  dataType:%s', self._stationID, self._type)
                while (True): 
                    try:           
                        """Update the sensor values."""
                        url = "http://www.cfr.toscana.it/monitoraggio/dettaglio.php?id="+self._stationID+"&type="+self._type+"&"+str(time.time())
                        req = urllib.request.Request(url)
                        with urllib.request.urlopen(req,timeout=self._timeout) as response:
                            respData = response.read()
                        tds = re.findall(r'VALUES\[\d+\] = new Array\("(.*?)","(.*?)","(.*?)","(.*?)"\);',str(respData))
                    except:
                        _LOGGER.error('Connection to the site timed out at URL %s', url)
                        print("CFR: An exception occurred reading from url: ", url)
                        print("CFR: Retrying in 5 seconds.")
                        #traceback.print_exc()
                        time.sleep(5)
                        continue

                    self._value3 = None

                    needUpdate = False

                    if len(tds) > 5:
                        lastEvent = tds[-1]

                        try:
                            date_time = re.findall(r'(\d{2}\/\d{2}\/\d{4}) (\d{2}.\d{2})', lastEvent[1])
                            self._data.date = date_time[0][0]
                            self._data.time = date_time[0][1]
                        except IndexError:
                            _LOGGER.error('Error parsing date/time from url %s (station:%s  dataType:%s)', url, self._stationID, self._type)
                            self._data.date = None
                            self._data.time = None

                        if self._lastData.date !=  self._data.date or self._lastData.time !=  self._data.time:
                            needUpdate = True
                            try:
                                self._data.value1 = lastEvent[2]
                                if self._type== TYPE_ANEMO:
                                    values = self._data.value1.split("/")
                                    self._data.value1 = values[0]
                                    self._data.value3 = values[1]
                                
                            except IndexError:
                                self._data.value1 = None
                            try:
                                self._data.value2 = lastEvent[3]
                            except IndexError:
                                self._data.value2 = None
                    else :
                        _LOGGER.error('Error parsing data from url %s (station:%s  dataType:%s)', url, self._stationID, self._type)
                        self._data.state = None
                        self._data.date = None
                        self._data.time = None
                        self._data.value1 = None
                        self._data.value2 = None
                    self._data.state = self._data.value1

                    if needUpdate :
                        #Make a copy of the data to be returned
                        self.mutex.acquire()
                        try:
                            self._lastData = copy.deepcopy(self._data)
                        finally:
                            self.mutex.release()
                        self.updaterequiredCallback()
                    time.sleep(60)
            except:
                _LOGGER.error('Updater loop unexpectedly ended (station:%s  dataType:%s) restarts in 60 seconds', self._stationID, self._type)
                time.sleep(60)


