device "temp-sensor-1" {
  sample_interval_ms = 1000

  # Temperature alert threshold in degrees Celsius.
  alert_threshold_c  = 80

  # Additional fake configuration settings.
  sensor_bus         = "i2c-1"
  sensor_address     = 0x48
  enable_logging     = true
]