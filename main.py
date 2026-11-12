from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


# -----------------------------------------------------------------------------
# 1. Cau hinh
# -----------------------------------------------------------------------------

CITY = "Ha Noi"
LATITUDE = 21.0285
LONGITUDE = 105.8542
TIMEZONE = "Asia/Ho_Chi_Minh"

API_URL = "https://api.open-meteo.com/v1/forecast"
API_PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": (
        "temperature_2m,relative_humidity_2m,precipitation,"
        "wind_speed_10m,weather_code"
    ),
    "forecast_days": 1,
    "timezone": TIMEZONE,
}

DATA_FILE = Path(__file__).resolve().with_name("weather_data.json")

# Ten truong trong API va ten thuoc tinh se luu trong moi ban ghi.
API_FIELDS = {
    "temperature": "temperature_2m",
    "humidity": "relative_humidity_2m",
    "precipitation": "precipitation",
    "wind_speed": "wind_speed_10m",
    "weather_code": "weather_code",
}


class WeatherDataError(Exception):
    """Loi khi API tra ve du lieu thoi tiet khong hop le."""


# -----------------------------------------------------------------------------
# 2. Tien ich va lam sach du lieu
# -----------------------------------------------------------------------------

def to_number(value: Any, field: str) -> float | int | None:
    """Chuyen gia tri sang so; tra ve None neu gia tri thieu/khong hop le."""
    if value is None or isinstance(value, bool):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    # Kiem tra mien gia tri hop ly cho mot so thuoc tinh.
    if field == "humidity" and not 0 <= number <= 100:
        return None
    if field in {"precipitation", "wind_speed", "weather_code"} and number < 0:
        return None
    if field == "weather_code":
        if not number.is_integer():
            return None
        return int(number)

    return number


def clean_records(hourly: dict[str, Any]) -> list[dict[str, Any]]:
    """Chuan hoa cac mang hourly thanh danh sach cac ban ghi Python."""
    times = hourly.get("time")
    if not isinstance(times, list) or not times:
        raise WeatherDataError("API khong co danh sach thoi gian du bao.")

    # Cac truong du bao phai la mang. Neu mot truong bi thieu/sai kieu,
    # chuong trinh dung lai thay vi am tham tao ra du lieu sai.
    for api_field in API_FIELDS.values():
        if not isinstance(hourly.get(api_field), list):
            raise WeatherDataError(
                f"Du lieu API thieu hoac sai dinh dang truong '{api_field}'."
            )

    records: list[dict[str, Any]] = []
    seen_times: set[str] = set()

    for index, raw_time in enumerate(times):
        # Bo qua ban ghi co thoi gian khong hop le.
        if not isinstance(raw_time, str):
            continue
        try:
            parsed_time = datetime.fromisoformat(raw_time)
        except ValueError:
            continue

        normalized_time = parsed_time.isoformat(timespec="minutes")
        if normalized_time in seen_times:
            continue

        record: dict[str, Any] = {
            "time": normalized_time,
            "city": CITY,
        }

        # Lay gia tri cung vi tri index trong cac mang du bao.
        for output_field, api_field in API_FIELDS.items():
            values = hourly[api_field]
            raw_value = values[index] if index < len(values) else None
            record[output_field] = to_number(raw_value, output_field)

        # Khong giu ban ghi neu tat ca cac chi so thoi tiet deu khong co.
        measurements = [record[field] for field in API_FIELDS]
        if all(value is None for value in measurements):
            continue

        seen_times.add(normalized_time)
        records.append(record)

    records.sort(key=lambda item: item["time"])
    if not records:
        raise WeatherDataError("Khong co ban ghi thoi tiet hop le sau khi lam sach.")

    return records


# -----------------------------------------------------------------------------
# 3. Thu thap va luu tru
# -----------------------------------------------------------------------------

def fetch_weather_data() -> list[dict[str, Any]]:
    """Gui HTTP GET den Open-Meteo va tra ve du lieu da lam sach."""
    print("Dang ket noi Open-Meteo de lay du lieu thoi tiet...")

    response = requests.get(API_URL, params=API_PARAMS, timeout=20)
    response.raise_for_status()

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise WeatherDataError("API khong tra ve JSON hop le.") from error

    if not isinstance(payload, dict):
        raise WeatherDataError("Cau truc JSON tu API khong dung dinh dang.")

    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or not hourly:
        raise WeatherDataError("API khong tra ve du lieu trong truong 'hourly'.")

    return clean_records(hourly)


def save_to_json(records: list[dict[str, Any]]) -> None:
    """Luu danh sach ban ghi vao file JSON."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=4)
    print(f"Da luu {len(records)} ban ghi vao: {DATA_FILE.name}")


def load_from_json() -> list[dict[str, Any]]:
    """Doc va kiem tra du lieu da luu trong file JSON."""
    if not DATA_FILE.exists():
        raise WeatherDataError(f"Khong tim thay file {DATA_FILE.name}.")

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except json.JSONDecodeError as error:
        raise WeatherDataError("File JSON bi loi hoac khong dung dinh dang.") from error
    except OSError as error:
        raise WeatherDataError(f"Khong the doc file JSON: {error}") from error

    if not isinstance(records, list):
        raise WeatherDataError("Du lieu trong JSON phai la mot danh sach.")
    if any(not isinstance(record, dict) for record in records):
        raise WeatherDataError("File JSON chua ban ghi khong dung dinh dang.")
    if not records:
        raise WeatherDataError("File JSON khong co ban ghi nao.")

    print(f"Da doc lai {len(records)} ban ghi tu {DATA_FILE.name}")
    return records


# -----------------------------------------------------------------------------
# 4. Hien thi, tim kiem, loc va sap xep
# -----------------------------------------------------------------------------

def display_records(records: list[dict[str, Any]]) -> None:
    """In danh sach ban ghi theo dang bang don gian."""
    if not records:
        print("Khong co du lieu de hien thi.")
        return

    headers = ["Thoi gian", "Nhiet do", "Do am", "Luong mua", "Toc do gio", "WMO"]
    print("\n" + " | ".join(headers))
    print("-" * 105)

    for record in records:
        values = [
            _format_timestamp(record.get("time")),
            _format_value(record.get("temperature"), " °C"),
            _format_value(record.get("humidity"), " %"),
            _format_value(record.get("precipitation"), " mm"),
            _format_value(record.get("wind_speed"), " km/h"),
            _format_value(record.get("weather_code"), ""),
        ]
        print(" | ".join(values))


def _format_value(value: Any, suffix: str = "") -> str:
    return "N/A" if value is None else f"{value}{suffix}"


def _format_timestamp(value: Any) -> str:
    """Chuyen timestamp ISO sang dinh dang dd/mm/yyyy HH:MM."""
    if not value:
        return "-"

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return str(value)


def search_by_time(records: list[dict[str, Any]]) -> None:
    """Tim ban ghi theo ngay, gio va phut."""

    date_input = input("Nhap ngay (dd/mm/yyyy): ").strip()

    try:
        target_date = datetime.strptime(date_input, "%d/%m/%Y").date()
    except ValueError:
        print("Ngay khong hop le. Vi du: 12/11/2026")
        return

    hour_input = input("Nhap gio (0-23, Enter de bo qua): ").strip()

    target_hour = None
    target_minute = None

    if hour_input:
        try:
            target_hour = int(hour_input)
            if not 0 <= target_hour <= 23:
                raise ValueError
        except ValueError:
            print("Gio khong hop le. Vui long nhap tu 0 den 23.")
            return

        minute_input = input("Nhap phut (0-59, Enter de bo qua): ").strip()

        if minute_input:
            try:
                target_minute = int(minute_input)
                if not 0 <= target_minute <= 59:
                    raise ValueError
            except ValueError:
                print("Phut khong hop le. Vui long nhap tu 0 den 59.")
                return

    results = []

    for record in records:
        try:
            timestamp = datetime.fromisoformat(str(record.get("time", "")))

            if timestamp.date() != target_date:
                continue

            if target_hour is not None and timestamp.hour != target_hour:
                continue

            if target_minute is not None and timestamp.minute != target_minute:
                continue

            results.append(record)

        except (ValueError, TypeError):
            continue

    print(f"\nTim thay {len(results)} ban ghi.")
    display_records(results)


def filter_by_temperature(records: list[dict[str, Any]]) -> None:
    """Loc cac ban ghi co nhiet do lon hon hoac bang nguong nhap vao."""
    try:
        threshold = float(input("Nhap nguong nhiet do (°C): ").strip())
    except ValueError:
        print("Nguong nhiet do phai la mot so.")
        return

    results = [
        record
        for record in records
        if isinstance(record.get("temperature"), (int, float))
        and record["temperature"] >= threshold
    ]
    print(f"Co {len(results)} ban ghi co nhiet do >= {threshold} °C.")
    display_records(results)


def sort_records(records: list[dict[str, Any]]) -> None:
    """Sap xep ban ghi theo mot thuoc tinh."""
    sort_options = {
        "1": ("time", "thoi gian"),
        "2": ("temperature", "nhiet do"),
        "3": ("humidity", "do am"),
        "4": ("precipitation", "luong mua"),
        "5": ("wind_speed", "toc do gio"),
    }

    print("\nSap xep theo:")
    for key, (_, label) in sort_options.items():
        print(f"{key}. {label}")

    choice = input("Chon thuoc tinh: ").strip()
    if choice not in sort_options:
        print("Lua chon khong hop le.")
        return

    order = input("Thu tu (1: tang dan, 2: giam dan): ").strip()
    if order not in {"1", "2"}:
        print("Lua chon thu tu khong hop le.")
        return

    field, label = sort_options[choice]
    valid_records = [record for record in records if record.get(field) is not None]
    missing_records = [record for record in records if record.get(field) is None]

    valid_records.sort(key=lambda record: record[field], reverse=(order == "2"))
    results = valid_records + missing_records

    direction = "tang dan" if order == "1" else "giam dan"
    print(f"\nKet qua sap xep theo {label} ({direction}):")
    display_records(results)


# -----------------------------------------------------------------------------
# 5. Thong ke
# -----------------------------------------------------------------------------

def numeric_values(records: list[dict[str, Any]], field: str) -> list[float]:
    """Lay cac gia tri so hop le cua mot thuoc tinh."""
    return [
        float(record[field])
        for record in records
        if isinstance(record.get(field), (int, float))
        and not isinstance(record.get(field), bool)
        and math.isfinite(float(record[field]))
    ]


def show_statistics(records: list[dict[str, Any]]) -> None:
    """Thuc hien cac thong ke co y nghia tren du lieu thoi tiet."""
    temperatures = numeric_values(records, "temperature")
    humidities = numeric_values(records, "humidity")
    precipitations = numeric_values(records, "precipitation")

    print("\n========== THONG KE THOI TIET ==========")
    print(f"Dia diem: {CITY}")
    print(f"Tong so ban ghi: {len(records)}")

    # Thong ke 1: nhiet do trung binh, cao nhat va thap nhat.
    if temperatures:
        print(f"Nhiet do trung binh: {sum(temperatures) / len(temperatures):.2f} °C")
        print(f"Nhiet do cao nhat: {max(temperatures):.2f} °C")
        print(f"Nhiet do thap nhat: {min(temperatures):.2f} °C")
    else:
        print("Khong du du lieu de thong ke nhiet do.")

    # Thong ke 2: do am trung binh.
    if humidities:
        print(f"Do am trung binh: {sum(humidities) / len(humidities):.2f} %")
    else:
        print("Khong du du lieu de thong ke do am.")

    # Thong ke 3: tong luong mua va so gio co mua.
    if precipitations:
        total_rain = sum(precipitations)
        rainy_hours = sum(amount > 0 for amount in precipitations)
        print(f"Tong luong mua du bao: {total_rain:.2f} mm")
        print(f"So gio co mua: {rainy_hours} gio")
    else:
        print("Khong du du lieu de thong ke luong mua.")

    print("========================================")


# -----------------------------------------------------------------------------
# 6. Chuong trinh chinh va menu
# -----------------------------------------------------------------------------

def run_menu(records: list[dict[str, Any]]) -> None:
    """Menu thao tac voi du lieu da doc tu JSON."""
    while True:
        print(
            "\n========== MENU =========="
            "\n1. Hien thi tat ca du lieu"
            "\n2. Tim kiem theo thoi gian"
            "\n3. Loc theo nhiet do"
            "\n4. Sap xep du lieu"
            "\n5. Thong ke du lieu"
            "\n0. Thoat"
            "\n=========================="
        )
        choice = input("Nhap lua chon: ").strip()

        if choice == "1":
            display_records(records)
        elif choice == "2":
            search_by_time(records)
        elif choice == "3":
            filter_by_temperature(records)
        elif choice == "4":
            sort_records(records)
        elif choice == "5":
            show_statistics(records)
        elif choice == "0":
            print("Ket thuc chuong trinh.")
            break
        else:
            print("Lua chon khong hop le. Vui long chon lai.")


def main() -> None:
    print("=" * 58)
    print("CHUONG TRINH THU THAP DU LIEU THOI TIET - OPEN-METEO")
    print(f"Dia diem: {CITY} ({LATITUDE}, {LONGITUDE})")
    print("=" * 58)

    # Uu tien lay du lieu moi. Neu API gap loi, co the dung file JSON da luu truoc do.
    try:
        records = fetch_weather_data()
        save_to_json(records)
    except (requests.exceptions.RequestException, WeatherDataError, ValueError) as error:
        print(f"Canh bao: Khong the lay du lieu moi tu API. Chi tiet: {error}")
        if not DATA_FILE.exists():
            print("Khong co file du lieu cu de su dung. Chuong trinh ket thuc.")
            return
        print("Chuyen sang su dung du lieu da luu tu lan chay truoc.")

    # Doc lai du lieu tu file JSON de thuc hien cac yeu cau xu ly.
    try:
        records = load_from_json()
    except WeatherDataError as error:
        print(f"Loi doc du lieu: {error}")
        return

    print(f"\nDa san sang xu ly du lieu cua {CITY}.")
    show_statistics(records)
    run_menu(records)


if __name__ == "__main__":
    main()
