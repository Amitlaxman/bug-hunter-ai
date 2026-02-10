import os
import sys


def parse_alert_threshold(path: str) -> int:
    """
    Very simple parser for the fake IoT DSL in temperature.py.

    It looks for a line starting with '  alert_threshold_c' and
    extracts the integer value after '='.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("alert_threshold_c"):
                # Expect format: alert_threshold_c  = 100
                parts = stripped.split("=")
                if len(parts) != 2:
                    raise ValueError(f"Malformed alert_threshold_c line: {line!r}")
                value_str = parts[1].strip()
                # Remove any trailing comments
                if "#" in value_str:
                    value_str = value_str.split("#", 1)[0].strip()
                return int(value_str, 0)
    raise ValueError("alert_threshold_c not found in configuration")


def main() -> None:
    config_path = os.path.join(os.path.dirname(__file__), "temperature.py")

    try:
        threshold = parse_alert_threshold(config_path)
    except Exception as e:
        print(f"[TEST] Error parsing configuration: {e}")
        sys.exit(1)

    print(f"[TEST] Parsed alert_threshold_c = {threshold}°C")

    expected = 80
    if threshold != expected:
        print(
            f"[TEST] FAIL: alert_threshold_c must be {expected}°C "
            f"but is currently {threshold}°C"
        )
        sys.exit(1)

    print(f"[TEST] PASS: alert_threshold_c correctly set to {expected}°C")
    sys.exit(0)


if __name__ == "__main__":
    main()

