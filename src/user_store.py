import json
import uuid

from PySide6.QtCore import QSettings

from settings import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME


_ORG_NAME = "HenProject"
_APP_NAME = "HenApp"
_USERS_KEY = "users/list"
_ALLOWED_USERS_KEY = "general/allowed_users"
_SCAN_RESULTS_LIMIT_KEY = "general/scan_results_limit"
_APP_NAME_KEY = "general/app_name"
_DEVICES_KEY = "devices/by_user"
_PRODUCT_STRUCTURES_KEY = "products/structures"
_PRODUCT_STRUCTURE_BY_USER_KEY = "products/structure_by_user"
_PRODUCT_SCAN_DETAIL_FIELDS_BY_USER_KEY = "products/scan_detail_fields_by_user"
_PRODUCTS_BY_USER_KEY = "products/items_by_user"
_DEVICE_CONNECTIONS_BY_USER_KEY = "devices/connections_by_user"


def _settings() -> QSettings:
    return QSettings(_ORG_NAME, _APP_NAME)


def _non_negative_ms_string(raw: object) -> str:
    try:
        return str(max(0, int(str(raw).strip())))
    except (TypeError, ValueError):
        return "0"


def get_allowed_users_limit() -> int:
    value = _settings().value(_ALLOWED_USERS_KEY, 1)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, parsed)


def get_scan_results_limit() -> int:
    value = _settings().value(_SCAN_RESULTS_LIMIT_KEY, 200)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 200
    return max(1, parsed)


def get_app_name(default: str = "") -> str:
    raw = _settings().value(_APP_NAME_KEY, default)
    text = str(raw).strip() if raw is not None else ""
    return text or default


def save_app_name(value: str) -> bool:
    settings = _settings()
    settings.setValue(_APP_NAME_KEY, str(value).strip())
    settings.sync()
    return settings.status() == QSettings.NoError


def get_users() -> list[dict[str, str]]:
    raw_value = _settings().value(_USERS_KEY, "")
    if not raw_value:
        default_users = _default_users()
        save_users(default_users)
        return default_users

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        default_users = _default_users()
        save_users(default_users)
        return default_users

    users: list[dict[str, str]] = []
    for item in parsed if isinstance(parsed, list) else []:
        if not isinstance(item, dict):
            continue
        username = str(item.get("username", "")).strip()
        password = str(item.get("password", "")).strip()
        role = str(item.get("role", "")).strip().lower()
        if role not in {"admin", "normal"}:
            role = "admin" if username == DEFAULT_ADMIN_USERNAME else "normal"
        if username and password:
            users.append({"username": username, "password": password, "role": role})

    if users:
        return users

    default_users = _default_users()
    save_users(default_users)
    return default_users


def save_users(users: list[dict[str, str]]) -> bool:
    clean_users: list[dict[str, str]] = []
    for user in users:
        username = str(user.get("username", "")).strip()
        password = str(user.get("password", "")).strip()
        role = str(user.get("role", "")).strip().lower()
        if role not in {"admin", "normal"}:
            role = "admin" if username == DEFAULT_ADMIN_USERNAME else "normal"
        if username and password:
            clean_users.append({"username": username, "password": password, "role": role})

    settings = _settings()
    settings.setValue(_USERS_KEY, json.dumps(clean_users, ensure_ascii=False))
    settings.sync()
    return settings.status() == QSettings.NoError


def _default_users() -> list[dict[str, str]]:
    return [
        {
            "username": DEFAULT_ADMIN_USERNAME,
            "password": DEFAULT_ADMIN_PASSWORD,
            "role": "admin",
        }
    ]


def get_devices_by_user() -> dict[str, list[dict[str, str]]]:
    raw_value = _settings().value(_DEVICES_KEY, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    devices_by_user: dict[str, list[dict[str, str]]] = {}
    if not isinstance(parsed, dict):
        return devices_by_user

    for username, devices in parsed.items():
        clean_username = str(username).strip()
        if not clean_username or not isinstance(devices, list):
            continue

        clean_devices: list[dict[str, str]] = []
        for device in devices:
            if not isinstance(device, dict):
                continue
            name = str(device.get("name", "")).strip()
            device_type = str(device.get("type", "")).strip() or "scanner"
            if name:
                clean_devices.append({"name": name, "type": device_type})

        devices_by_user[clean_username] = clean_devices

    return devices_by_user


def save_devices_by_user(devices_by_user: dict[str, list[dict[str, str]]]) -> bool:
    clean_data: dict[str, list[dict[str, str]]] = {}
    for username, devices in devices_by_user.items():
        clean_username = str(username).strip()
        if not clean_username:
            continue

        clean_devices: list[dict[str, str]] = []
        for device in devices:
            name = str(device.get("name", "")).strip()
            device_type = str(device.get("type", "")).strip() or "scanner"
            if name:
                clean_devices.append({"name": name, "type": device_type})

        clean_data[clean_username] = clean_devices

    settings = _settings()
    settings.setValue(_DEVICES_KEY, json.dumps(clean_data, ensure_ascii=False))
    settings.sync()
    return settings.status() == QSettings.NoError


def get_product_structures() -> list[dict[str, object]]:
    raw_value = _settings().value(_PRODUCT_STRUCTURES_KEY, "")
    if not raw_value:
        return []

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    structures: list[dict[str, object]] = []
    for item in parsed if isinstance(parsed, list) else []:
        if not isinstance(item, dict):
            continue
        structure_name = str(item.get("name", "")).strip()
        fields = item.get("fields", [])
        if not structure_name or not isinstance(fields, list):
            continue

        clean_fields: list[dict[str, object]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "")).strip()
            field_type = str(field.get("type", "")).strip()
            if field_name and field_type:
                uniq_raw = field.get("unique", False)
                unique = uniq_raw is True or str(uniq_raw).strip().lower() in {"true", "1", "yes"}
                clean_fields.append({"name": field_name, "type": field_type, "unique": unique})

        structures.append({"name": structure_name, "fields": clean_fields})

    return structures


def save_product_structures(structures: list[dict[str, object]]) -> bool:
    clean_structures: list[dict[str, object]] = []
    for item in structures:
        structure_name = str(item.get("name", "")).strip()
        fields = item.get("fields", [])
        if not structure_name or not isinstance(fields, list):
            continue

        clean_fields: list[dict[str, object]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            field_name = str(field.get("name", "")).strip()
            field_type = str(field.get("type", "")).strip()
            if field_name and field_type:
                uniq_raw = field.get("unique", False)
                unique = uniq_raw is True or str(uniq_raw).strip().lower() in {"true", "1", "yes"}
                clean_fields.append({"name": field_name, "type": field_type, "unique": unique})

        clean_structures.append({"name": structure_name, "fields": clean_fields})

    settings = _settings()
    settings.setValue(_PRODUCT_STRUCTURES_KEY, json.dumps(clean_structures, ensure_ascii=False))
    settings.sync()
    return settings.status() == QSettings.NoError


def get_product_structure_by_user() -> dict[str, str]:
    raw_value = _settings().value(_PRODUCT_STRUCTURE_BY_USER_KEY, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    assignments: dict[str, str] = {}
    if not isinstance(parsed, dict):
        return assignments

    for username, structure_name in parsed.items():
        clean_username = str(username).strip()
        clean_structure_name = str(structure_name).strip()
        if clean_username and clean_structure_name:
            assignments[clean_username] = clean_structure_name
    return assignments


def get_products_by_user() -> dict[str, list[dict[str, object]]]:
    raw_value = _settings().value(_PRODUCTS_BY_USER_KEY, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    result: dict[str, list[dict[str, object]]] = {}
    if not isinstance(parsed, dict):
        return result

    for username, items in parsed.items():
        clean_username = str(username).strip()
        if not clean_username:
            continue

        clean_items: list[dict[str, object]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("id", "")).strip()
            if not pid:
                pid = uuid.uuid4().hex
            raw_values = item.get("values", {})
            values: dict[str, object] = {}
            if isinstance(raw_values, dict):
                for key, val in raw_values.items():
                    fk = str(key).strip()
                    if fk:
                        values[fk] = val
            clean_items.append({"id": pid, "values": values})

        result[clean_username] = clean_items

    return result


def save_products_by_user(products_by_user: dict[str, list[dict[str, object]]]) -> bool:
    clean_outer: dict[str, list[dict[str, object]]] = {}
    for username, items in products_by_user.items():
        clean_username = str(username).strip()
        if not clean_username:
            continue

        clean_items: list[dict[str, object]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("id", "")).strip()
            if not pid:
                pid = uuid.uuid4().hex
            raw_values = item.get("values", {})
            values: dict[str, object] = {}
            if isinstance(raw_values, dict):
                for key, val in raw_values.items():
                    fk = str(key).strip()
                    if fk:
                        values[fk] = val
            clean_items.append({"id": pid, "values": values})

        clean_outer[clean_username] = clean_items

    settings = _settings()
    settings.setValue(_PRODUCTS_BY_USER_KEY, json.dumps(clean_outer, ensure_ascii=False))
    settings.sync()
    return settings.status() == QSettings.NoError


def save_product_structure_by_user(assignments: dict[str, str]) -> bool:
    clean_assignments: dict[str, str] = {}
    for username, structure_name in assignments.items():
        clean_username = str(username).strip()
        clean_structure_name = str(structure_name).strip()
        if clean_username and clean_structure_name:
            clean_assignments[clean_username] = clean_structure_name

    settings = _settings()
    settings.setValue(
        _PRODUCT_STRUCTURE_BY_USER_KEY,
        json.dumps(clean_assignments, ensure_ascii=False),
    )
    settings.sync()
    return settings.status() == QSettings.NoError


def get_product_scan_detail_fields_by_user() -> dict[str, list[dict[str, object]]]:
    """تنظیم نمایش فیلدها در جزئیات اسکن (صفحهٔ خانه) برای هر کاربر.

    هر ورودی کاربر یک لیست از آبجکت‌هاست:
    {"name": "<field_name>", "show_name": <bool>}

    سازگاری عقب‌رو:
    - نسخهٔ قدیمی که فقط list[str] بوده نیز پذیرفته می‌شود و معادل show_name=True است.
    - اگر کاربری در این نقشه نباشد، UI حالت پیش‌فرض (نمایش همهٔ فیلدها با نام) را اعمال می‌کند.
    - اگر کاربر وجود داشته باشد ولی لیستش خالی باشد، یعنی هیچ فیلدی در جزئیات نمایش داده نشود.
    """
    raw_value = _settings().value(_PRODUCT_SCAN_DETAIL_FIELDS_BY_USER_KEY, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    result: dict[str, list[dict[str, object]]] = {}
    if not isinstance(parsed, dict):
        return result

    for username, raw_entries in parsed.items():
        clean_username = str(username).strip()
        if not clean_username or not isinstance(raw_entries, list):
            continue
        entries: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in raw_entries:
            name = ""
            show_name = True
            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                show_name_raw = item.get("show_name", True)
                show_name = show_name_raw is True or str(show_name_raw).strip().lower() in {
                    "true",
                    "1",
                    "yes",
                }
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            entries.append({"name": name, "show_name": show_name})
        result[clean_username] = entries
    return result


def save_product_scan_detail_fields_by_user(mapping: dict[str, list[dict[str, object]]]) -> bool:
    clean_outer: dict[str, list[dict[str, object]]] = {}
    for username, entries in mapping.items():
        clean_username = str(username).strip()
        if not clean_username:
            continue
        if not isinstance(entries, list):
            continue
        clean_entries: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in entries:
            name = ""
            show_name = True
            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                show_name_raw = item.get("show_name", True)
                show_name = show_name_raw is True or str(show_name_raw).strip().lower() in {
                    "true",
                    "1",
                    "yes",
                }
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            clean_entries.append({"name": name, "show_name": show_name})
        clean_outer[clean_username] = clean_entries

    settings = _settings()
    settings.setValue(
        _PRODUCT_SCAN_DETAIL_FIELDS_BY_USER_KEY,
        json.dumps(clean_outer, ensure_ascii=False),
    )
    settings.sync()
    return settings.status() == QSettings.NoError


def get_device_connections_by_user() -> dict[str, dict[str, dict[str, str]]]:
    raw_value = _settings().value(_DEVICE_CONNECTIONS_BY_USER_KEY, "")
    if not raw_value:
        return {}

    try:
        parsed = json.loads(str(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    result: dict[str, dict[str, dict[str, str]]] = {}
    if not isinstance(parsed, dict):
        return result

    for username, device_map in parsed.items():
        clean_username = str(username).strip()
        if not clean_username or not isinstance(device_map, dict):
            continue

        clean_device_map: dict[str, dict[str, str]] = {}
        for device_name, config in device_map.items():
            clean_device_name = str(device_name).strip()
            if not clean_device_name or not isinstance(config, dict):
                continue

            mode = str(config.get("mode", "")).strip().lower()
            if mode not in {"ip", "com"}:
                mode = "ip"
            ip = str(config.get("ip", "")).strip()
            port = str(config.get("port", "")).strip()
            com_port = str(config.get("com", "")).strip()
            target_printer = str(config.get("target_printer", "")).strip()
            target_rejector = str(config.get("target_rejector", "")).strip()
            lookup_field = str(config.get("lookup_field", "")).strip()
            printer_type = str(config.get("printer_type", "")).strip().upper()
            if printer_type not in {"A", "B"}:
                printer_type = "A"
            print_priority_1 = str(config.get("print_priority_1", "")).strip()
            print_priority_2 = str(config.get("print_priority_2", "")).strip()
            print_priority_3 = str(config.get("print_priority_3", "")).strip()
            raw_print_priorities = config.get("print_priorities", [])
            print_priorities: list[dict[str, str]] = []
            if isinstance(raw_print_priorities, list):
                for item in raw_print_priorities:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).strip()
                    source_type = str(item.get("source_type", "")).strip()
                    source_value = str(item.get("source_value", "")).strip()
                    is_valid = source_type in {"manual", "product_field"} and bool(name)
                    if source_type == "product_field":
                        is_valid = is_valid and bool(source_value)
                    if is_valid:
                        print_priorities.append(
                            {"name": name, "source_type": source_type, "source_value": source_value}
                        )
            rejector_delay_before_ms = _non_negative_ms_string(
                config.get("rejector_delay_before_ms", "0")
            )
            rejector_open_duration_ms = _non_negative_ms_string(
                config.get("rejector_open_duration_ms", "0")
            )
            clean_device_map[clean_device_name] = {
                "mode": mode,
                "ip": ip,
                "port": port,
                "com": com_port,
                "target_printer": target_printer,
                "target_rejector": target_rejector,
                "lookup_field": lookup_field,
                "printer_type": printer_type,
                "print_priority_1": print_priority_1,
                "print_priority_2": print_priority_2,
                "print_priority_3": print_priority_3,
                "print_priorities": print_priorities,
                "rejector_delay_before_ms": rejector_delay_before_ms,
                "rejector_open_duration_ms": rejector_open_duration_ms,
            }

        result[clean_username] = clean_device_map

    return result


def save_device_connections_by_user(connections_by_user: dict[str, dict[str, dict[str, str]]]) -> bool:
    clean_data: dict[str, dict[str, dict[str, str]]] = {}
    for username, device_map in connections_by_user.items():
        clean_username = str(username).strip()
        if not clean_username or not isinstance(device_map, dict):
            continue

        clean_device_map: dict[str, dict[str, str]] = {}
        for device_name, config in device_map.items():
            clean_device_name = str(device_name).strip()
            if not clean_device_name or not isinstance(config, dict):
                continue

            mode = str(config.get("mode", "")).strip().lower()
            if mode not in {"ip", "com"}:
                mode = "ip"
            ip = str(config.get("ip", "")).strip()
            port = str(config.get("port", "")).strip()
            com_port = str(config.get("com", "")).strip()
            target_printer = str(config.get("target_printer", "")).strip()
            target_rejector = str(config.get("target_rejector", "")).strip()
            lookup_field = str(config.get("lookup_field", "")).strip()
            printer_type = str(config.get("printer_type", "")).strip().upper()
            if printer_type not in {"A", "B"}:
                printer_type = "A"
            print_priority_1 = str(config.get("print_priority_1", "")).strip()
            print_priority_2 = str(config.get("print_priority_2", "")).strip()
            print_priority_3 = str(config.get("print_priority_3", "")).strip()
            raw_print_priorities = config.get("print_priorities", [])
            print_priorities: list[dict[str, str]] = []
            if isinstance(raw_print_priorities, list):
                for item in raw_print_priorities:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).strip()
                    source_type = str(item.get("source_type", "")).strip()
                    source_value = str(item.get("source_value", "")).strip()
                    is_valid = source_type in {"manual", "product_field"} and bool(name)
                    if source_type == "product_field":
                        is_valid = is_valid and bool(source_value)
                    if is_valid:
                        print_priorities.append(
                            {"name": name, "source_type": source_type, "source_value": source_value}
                        )
            rejector_delay_before_ms = _non_negative_ms_string(
                config.get("rejector_delay_before_ms", "0")
            )
            rejector_open_duration_ms = _non_negative_ms_string(
                config.get("rejector_open_duration_ms", "0")
            )
            clean_device_map[clean_device_name] = {
                "mode": mode,
                "ip": ip,
                "port": port,
                "com": com_port,
                "target_printer": target_printer,
                "target_rejector": target_rejector,
                "lookup_field": lookup_field,
                "printer_type": printer_type,
                "print_priority_1": print_priority_1,
                "print_priority_2": print_priority_2,
                "print_priority_3": print_priority_3,
                "print_priorities": print_priorities,
                "rejector_delay_before_ms": rejector_delay_before_ms,
                "rejector_open_duration_ms": rejector_open_duration_ms,
            }

        clean_data[clean_username] = clean_device_map

    settings = _settings()
    settings.setValue(
        _DEVICE_CONNECTIONS_BY_USER_KEY,
        json.dumps(clean_data, ensure_ascii=False),
    )
    settings.sync()
    return settings.status() == QSettings.NoError
