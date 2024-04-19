"""Support for xsense sensors."""
from __future__ import annotations

from xsense.device import Device
from xsense.entity import Entity

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XSenseDataUpdateCoordinator
from .entity import XSenseEntity, XSenseSensorEntityDescription

STATION_SENSORS: tuple[XSenseSensorEntityDescription, ...] = (
    XSenseSensorEntityDescription(
        key="wifi_rssi",
        translation_key="wifi_rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda device: "wifiRSSI" in device.data,
        value_fn=lambda station: station.data["wifiRSSI"],
    ),
    XSenseSensorEntityDescription(
        key="sw_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda device: "sw" in device.data,
        value_fn=lambda station: station.data["sw"],
    ),
    XSenseSensorEntityDescription(
        key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda station: station.sn,
    ),
    XSenseSensorEntityDescription(
        key="ip",
        translation_key="ip",
        entity_category=EntityCategory.DIAGNOSTIC,
        exists_fn=lambda device: "ip" in device.data,
        value_fn=lambda device: device.data["ip"],
    ),
    XSenseSensorEntityDescription(
        key="alarm_vol",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        exists_fn=lambda device: "alarmVol" in device.data,
        value_fn=lambda device: device.data["alarmVol"],
    ),
    XSenseSensorEntityDescription(
        key="voice_vol",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        exists_fn=lambda device: "voiceVol" in device.data,
        value_fn=lambda device: device.data["voiceVol"],
    ),
)

SENSORS: tuple[XSenseSensorEntityDescription, ...] = (
    XSenseSensorEntityDescription(
        key="co",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.CO,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.data["coPpm"],
        exists_fn=lambda device: "coPpm" in device.data,
    ),
    XSenseSensorEntityDescription(
        key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.data["temperature"],
        exists_fn=lambda device: "temperature" in device.data,
    ),
    XSenseSensorEntityDescription(
        key="humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.data["humidity"],
        exists_fn=lambda device: "humidity" in device.data,
    ),
    XSenseSensorEntityDescription(
        key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: (int(device.data["batInfo"]) * 100) / 3,
        exists_fn=lambda device: "batInfo" in device.data,
    ),
)

# BINARY_SENSORS = tuple[XSenseSensorEntityDescription, ...] = (
#     XSenseSensorEntityDescription(
#         key=
#     )
# )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the xsense sensor entry."""
    devices: list[Device] = []
    coordinator: XSenseDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for _, station in coordinator.data["stations"].items():
        devices.extend(
            XSenseSensorEntity(coordinator, station, description)
            for description in STATION_SENSORS
            if description.exists_fn(station)
        )
    for _, dev in coordinator.data["devices"].items():
        devices.extend(
            XSenseSensorEntity(
                coordinator, dev, description, station_id=dev.station.entity_id
            )
            for description in SENSORS
            if description.exists_fn(dev)
        )

    async_add_entities(devices)


class XSenseSensorEntity(XSenseEntity, SensorEntity):
    """Representation of a xsense device."""

    entity_description: XSenseSensorEntityDescription

    def __init__(
        self,
        coordinator: XSenseDataUpdateCoordinator,
        entity: Entity,
        entity_description: XSenseSensorEntityDescription,
        station_id: str | None = None,
    ) -> None:
        """Set up the instance."""
        self._station_id = station_id
        self.entity_description = entity_description
        self._attr_available = False  # This overrides the default

        super().__init__(coordinator, entity, station_id)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if self._station_id:
            device = self.coordinator.data["devices"][self._dev_id]
        else:
            device = self.coordinator.data["stations"][self._dev_id]

        return self.entity_description.value_fn(device)
