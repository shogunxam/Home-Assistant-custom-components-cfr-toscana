# Home-Assistant-custom-components-cfr-toscana
HA Integration for Centro Funzionale Regione Toscana

Tuscany METEO-HYDRO Monitor System
To get more detailed information about parameters visit [*CENTRO FUNZIONALE*](http://www.cfr.toscana.it/).

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Latest value registered by the station.


## Configuration options

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | `string` | `False` | `CFRToscana` | Name of sensor |
| `station` | `string` | `True` | - | Station code |
| `type` | `string` | `False` | `idro` | Type of the monitored data |

### Possible values for type

| Key | Description |
| --- | --- | 
| `idro` | Hydrometric Height of the river |
| `pluvio` | Cumulated precipitation |
| `termo` | Temperature |
| `anemo` | Wind speed |
| `igro` | Humidity |

The same sation can monitor one or more data types, please reffer to [*CENTRO FUNZIONALE*](http://www.cfr.toscana.it/) to understand which data types are monitored.
<br>

| Stations' code by data type | |
| --- | --- |
| [Hydrometric Height of the river](http://www.cfr.toscana.it/monitoraggio/stazioni.php?type=idro) | [Temperature](http://www.cfr.toscana.it/monitoraggio/stazioni.php?type=termo) |
| [Cumulated precipitation](http://www.cfr.toscana.it/monitoraggio/stazioni.php?type=pluvio) | [Wind speed](http://www.cfr.toscana.it/monitoraggio/stazioni.php?type=anemo) |
| [Humidity](http://www.cfr.toscana.it/monitoraggio/stazioni.php?type=igro) | |

## Example usage

```
sensor:
  - platform: cfr
    name: Arno_Firenze_Uffizi
    station: TOS01004679
    type: idro
```

## Note

Depending on the monitored data type, additional attributes could be returned by the sensor such as date and time of the registered event.<br>


## License

_Information provided by [*CENTRO FUNZIONALE*](http://www.cfr.toscana.it/)

_Dati forniti dal [*CENTRO FUNZIONALE*](http://www.cfr.toscana.it/)


## Contributions are welcome!

***

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg
