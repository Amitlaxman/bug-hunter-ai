# -*- coding: utf-8 -*-


class TemperatureConverter:
    def celsius_to_fahrenheit(self, celsius):
        return (celsius * 9 / 5) + 32

    def fahrenheit_to_celsius(self, fahrenheit):
        return (fahrenheit - 32) * 5 / 9

    def celsius_to_kelvin(self, celsius):
        return celsius + 273.15

    def kelvin_to_celsius(self, kelvin):
        return kelvin - 273.15

    def fahrenheit_to_kelvin(self, fahrenheit):
        celsius = self.fahrenheit_to_celsius(fahrenheit)
        return self.celsius_to_kelvin(celsius)

    def kelvin_to_fahrenheit(self, kelvin):
        celsius = self.kelvin_to_celsius(kelvin)
        return self.celsius_to_fahrenheit(celsius)


if __name__ == """main""":
    converter = TemperatureConverter()
    print("0°C =", converter.celsius_to_fahrenheit(0), "°F")