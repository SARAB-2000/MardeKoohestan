"""
تب «کپی تنظیمات کاربر»: شامل سه زیربخش است:

1. کپی بین کاربران: تنظیمات یک کاربر را به کاربر دیگر منتقل می‌کند.
2. دریافت خروجی: تنظیمات کاربر را به‌صورت فایل JSON روی سیستم ذخیره می‌کند.
3. بارگذاری از فایل: یک فایل JSON خروجی‌گرفته‌شده را روی کاربر مقصد اعمال می‌کند.

در حالت‌های کپی و بارگذاری، دو نحوهٔ اعمال «جایگزینی کامل» یا «ادغام» در دسترس است
و موارد تکراری در حالت ادغام نادیده گرفته شده و در گزارش پایان درج می‌شوند.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from settings import DEFAULT_ADMIN_USERNAME
from ui.widgets.styled_combo_field import StyledComboField
from user_store import (
    get_device_connections_by_user,
    get_devices_by_user,
    get_product_structure_by_user,
    get_product_structures,
    get_products_by_user,
    get_users,
    save_device_connections_by_user,
    save_devices_by_user,
    save_product_structure_by_user,
    save_product_structures,
    save_products_by_user,
)


_MODE_REPLACE = "replace"
_MODE_MERGE = "merge"
_FILE_VERSION = 1


def _configure_wrap_label(label: QLabel) -> None:
    """پیکربندی استاندارد برای یک QLabel با شکستن خط؛ تا در عرض‌های کم مرتب جمع شود."""
    label.setWordWrap(True)
    label.setMinimumWidth(0)
    policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
    policy.setHeightForWidth(True)
    label.setSizePolicy(policy)


def _normalize_field_type(raw: object) -> str:
    return str(raw).strip().lower()


def _field_unique_flag(raw: object) -> bool:
    return raw is True or str(raw).strip().lower() in {"true", "1", "yes"}


def _value_present_for_unique(field_type: str, value: object) -> bool:
    if value is None:
        return False
    if field_type == "text":
        return str(value).strip() != ""
    if field_type == "number":
        if isinstance(value, bool):
            return False
        return True
    if field_type == "boolean":
        return True
    if field_type == "datetime":
        return str(value).strip() != ""
    if field_type == "dictionary":
        return isinstance(value, dict) and len(value) > 0
    if field_type == "list":
        return isinstance(value, list) and len(value) > 0
    return str(value).strip() != ""


def _normalize_number_for_unique(value: object) -> int | float:
    x = float(value)  # type: ignore[arg-type]
    if math.isfinite(x) and math.isclose(x, round(x), rel_tol=0.0, abs_tol=1e-9):
        return int(round(x))
    return x


def _canonical_unique_token(field_type: str, value: object) -> object | None:
    if not _value_present_for_unique(field_type, value):
        return None
    if field_type == "text":
        return ("t", str(value).strip())
    if field_type == "number":
        if isinstance(value, bool):
            return None
        try:
            return ("n", _normalize_number_for_unique(value))
        except (TypeError, ValueError):
            return None
    if field_type == "boolean":
        return ("b", bool(value))
    if field_type == "datetime":
        return ("d", str(value).strip())
    if field_type == "dictionary":
        if not isinstance(value, dict):
            return None
        try:
            return ("j", json.dumps(value, sort_keys=True, ensure_ascii=False))
        except TypeError:
            return ("j", str(value))
    if field_type == "list":
        if not isinstance(value, list):
            return None
        try:
            return ("j", json.dumps(value, sort_keys=True, ensure_ascii=False))
        except TypeError:
            return ("j", str(value))
    return ("t", str(value).strip())


def _clone_product(product: object) -> dict[str, object]:
    if not isinstance(product, dict):
        return {"id": "", "values": {}}
    pid = str(product.get("id", "")).strip()
    raw_values = product.get("values", {})
    values: dict[str, Any] = {}
    if isinstance(raw_values, dict):
        for key, val in raw_values.items():
            fk = str(key).strip()
            if fk:
                values[fk] = val
    return {"id": pid, "values": values}


def _lookup_structure_fields(
    structures: list[dict[str, object]],
    structure_name: str,
) -> list[dict[str, object]]:
    for structure in structures:
        if not isinstance(structure, dict):
            continue
        if str(structure.get("name", "")).strip() != structure_name:
            continue
        fields = structure.get("fields", [])
        cleaned: list[dict[str, object]] = []
        if isinstance(fields, list):
            for fd in fields:
                if not isinstance(fd, dict):
                    continue
                fname = str(fd.get("name", "")).strip()
                ftype = _normalize_field_type(fd.get("type", "text"))
                unique = _field_unique_flag(fd.get("unique", False))
                if fname:
                    cleaned.append({"name": fname, "type": ftype, "unique": unique})
        return cleaned
    return []


def _find_unique_conflict(
    existing_products: list[dict[str, object]],
    values: dict[str, object],
    structure_fields: list[dict[str, object]],
) -> str | None:
    for fd in structure_fields:
        if not _field_unique_flag(fd.get("unique", False)):
            continue
        fname = str(fd.get("name", "")).strip()
        if not fname:
            continue
        ftype = _normalize_field_type(fd.get("type", "text"))
        new_token = _canonical_unique_token(ftype, values.get(fname))
        if new_token is None:
            continue
        for product in existing_products:
            if not isinstance(product, dict):
                continue
            pv = product.get("values", {})
            if not isinstance(pv, dict):
                continue
            old_token = _canonical_unique_token(ftype, pv.get(fname))
            if old_token is not None and old_token == new_token:
                return fname
    return None


def _gather_source_from_user(username: str) -> dict[str, Any]:
    devices_by_user = get_devices_by_user()
    connections_by_user = get_device_connections_by_user()
    structure_by_user = get_product_structure_by_user()
    products_by_user = get_products_by_user()
    structures = get_product_structures()

    structure_name = str(structure_by_user.get(username, "")).strip()
    structure_def: dict[str, Any] | None = None
    if structure_name:
        for st in structures:
            if isinstance(st, dict) and str(st.get("name", "")).strip() == structure_name:
                structure_def = st
                break

    return {
        "devices": list(devices_by_user.get(username, [])),
        "connections": dict(connections_by_user.get(username, {})),
        "structure_name": structure_name,
        "structure_definition": structure_def,
        "products": list(products_by_user.get(username, [])),
    }


def _gather_source_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    products_section = payload.get("products")
    devices_section = payload.get("devices")
    if not isinstance(products_section, dict):
        products_section = {}
    if not isinstance(devices_section, dict):
        devices_section = {}

    structure_def = products_section.get("structure_definition")
    if not isinstance(structure_def, dict):
        structure_def = None

    raw_items = products_section.get("items", [])
    raw_list = devices_section.get("list", [])
    raw_connections = devices_section.get("connections", {})

    return {
        "devices": list(raw_list) if isinstance(raw_list, list) else [],
        "connections": dict(raw_connections) if isinstance(raw_connections, dict) else {},
        "structure_name": str(products_section.get("structure_name", "")).strip(),
        "structure_definition": structure_def,
        "products": list(raw_items) if isinstance(raw_items, list) else [],
        "_has_products_section": "products" in payload,
        "_has_devices_section": "devices" in payload,
    }


def _ensure_structure_registered(
    structure_name: str,
    structure_def: Any,
    report: list[str],
) -> None:
    """اگر ساختار محصول از فایل وارد شده در فهرست ساختارهای ثبت‌شده نبود، اضافه‌اش می‌کند."""
    if not structure_name or not isinstance(structure_def, dict):
        return
    structures = get_product_structures()
    existing_names = {
        str(s.get("name", "")).strip()
        for s in structures
        if isinstance(s, dict)
    }
    if structure_name in existing_names:
        return

    fields = structure_def.get("fields", [])
    cleaned_fields: list[dict[str, Any]] = []
    if isinstance(fields, list):
        for fd in fields:
            if not isinstance(fd, dict):
                continue
            fname = str(fd.get("name", "")).strip()
            ftype = _normalize_field_type(fd.get("type", "text"))
            unique = _field_unique_flag(fd.get("unique", False))
            if fname and ftype:
                cleaned_fields.append({"name": fname, "type": ftype, "unique": unique})
    structures.append({"name": structure_name, "fields": cleaned_fields})
    if save_product_structures(structures):
        report.append(f"  ساختار محصول «{structure_name}» به فهرست ساختارها اضافه شد.")


def _apply_replace_from_data(
    target: str,
    source: dict[str, Any],
    report: list[str],
    *,
    apply_devices: bool = True,
    apply_products: bool = True,
) -> bool:
    devices_by_user = get_devices_by_user()
    connections_by_user = get_device_connections_by_user()
    structure_by_user = get_product_structure_by_user()
    products_by_user = get_products_by_user()

    source_devices = list(source.get("devices") or [])
    source_connections = dict(source.get("connections") or {})
    source_structure = str(source.get("structure_name", "")).strip()
    source_structure_def = source.get("structure_definition")
    source_products = list(source.get("products") or [])

    previous_target_devices = list(devices_by_user.get(target, []))
    previous_target_connections = dict(connections_by_user.get(target, {}))
    previous_target_structure = str(structure_by_user.get(target, "")).strip()
    previous_target_products = list(products_by_user.get(target, []))

    if apply_devices:
        report.append("[دستگاه‌ها]")
        report.append(f"  پاک شد: {len(previous_target_devices)} دستگاه قبلی مقصد")
        report.append(f"  جایگزین شد: {len(source_devices)} دستگاه از مبدأ")
        if source_devices:
            report.append(
                "  نام دستگاه‌های منتقل‌شده: "
                + "، ".join(str(d.get("name", "")) for d in source_devices if isinstance(d, dict))
            )
        report.append("")

        valid_device_names = {
            str(d.get("name", "")).strip()
            for d in source_devices
            if isinstance(d, dict) and str(d.get("name", "")).strip()
        }
        clean_connections: dict[str, dict[str, str]] = {}
        skipped_orphan_connections: list[str] = []
        for device_name, cfg in source_connections.items():
            name = str(device_name).strip()
            if not name or not isinstance(cfg, dict):
                continue
            if name not in valid_device_names:
                skipped_orphan_connections.append(name)
                continue
            clean_connections[name] = dict(cfg)

        report.append("[تنظیمات اتصال دستگاه‌ها]")
        report.append(f"  پاک شد: {len(previous_target_connections)} تنظیمات قبلی مقصد")
        report.append(f"  جایگزین شد: {len(clean_connections)} تنظیمات از مبدأ")
        if skipped_orphan_connections:
            report.append(
                "  تنظیمات نادیده‌گرفته‌شده (دستگاه متناظر در مبدأ نبود): "
                + "، ".join(skipped_orphan_connections)
            )
        report.append("")

        devices_by_user[target] = source_devices
        connections_by_user[target] = clean_connections

    if apply_products:
        _ensure_structure_registered(source_structure, source_structure_def, report)

        report.append("[ساختار محصول]")
        if source_structure:
            if previous_target_structure and previous_target_structure != source_structure:
                report.append(
                    f"  ساختار قبلی مقصد «{previous_target_structure}» با «{source_structure}» جایگزین شد."
                )
            elif previous_target_structure == source_structure:
                report.append(f"  ساختار «{source_structure}» از قبل در مقصد بود؛ بدون تغییر.")
            else:
                report.append(f"  ساختار «{source_structure}» به مقصد اختصاص داده شد.")
        else:
            if previous_target_structure:
                report.append(
                    f"  ساختار قبلی مقصد «{previous_target_structure}» پاک شد (مبدأ ساختاری ندارد)."
                )
            else:
                report.append("  ساختاری برای انتقال وجود نداشت.")
        report.append("")

        report.append("[محصولات]")
        report.append(f"  پاک شد: {len(previous_target_products)} محصول قبلی مقصد")
        if source_structure:
            clean_products = [_clone_product(p) for p in source_products]
            report.append(f"  جایگزین شد: {len(clean_products)} محصول از مبدأ")
        else:
            clean_products = []
            report.append("  هیچ محصولی منتقل نشد (مبدأ ساختاری برای محصولات نداشت).")
        report.append("")

        if source_structure:
            structure_by_user[target] = source_structure
        else:
            structure_by_user.pop(target, None)
        products_by_user[target] = clean_products

    return _persist_all(
        devices_by_user,
        connections_by_user,
        structure_by_user,
        products_by_user,
        report,
    )


def _apply_merge_from_data(
    target: str,
    source: dict[str, Any],
    report: list[str],
    *,
    apply_devices: bool = True,
    apply_products: bool = True,
) -> bool:
    devices_by_user = get_devices_by_user()
    connections_by_user = get_device_connections_by_user()
    structure_by_user = get_product_structure_by_user()
    products_by_user = get_products_by_user()

    source_devices = list(source.get("devices") or [])
    source_connections = dict(source.get("connections") or {})
    source_structure = str(source.get("structure_name", "")).strip()
    source_structure_def = source.get("structure_definition")
    source_products = list(source.get("products") or [])

    target_devices = list(devices_by_user.get(target, []))
    target_connections = dict(connections_by_user.get(target, {}))
    target_structure = str(structure_by_user.get(target, "")).strip()
    target_products = list(products_by_user.get(target, []))

    new_devices = list(target_devices)
    new_connections = dict(target_connections)
    final_structure_name = target_structure
    new_products = list(target_products)

    if apply_devices:
        report.append("[دستگاه‌ها]")
        existing_device_names = {
            str(d.get("name", "")).strip()
            for d in target_devices
            if isinstance(d, dict) and str(d.get("name", "")).strip()
        }
        added_devices: list[str] = []
        skipped_devices: list[str] = []
        for device in source_devices:
            if not isinstance(device, dict):
                continue
            name = str(device.get("name", "")).strip()
            if not name:
                continue
            if name in existing_device_names:
                skipped_devices.append(name)
                continue
            new_devices.append(
                {
                    "name": name,
                    "type": str(device.get("type", "")).strip().lower() or "scanner",
                }
            )
            existing_device_names.add(name)
            added_devices.append(name)
        report.append(
            f"  افزوده شد: {len(added_devices)} دستگاه"
            + (f" ({'، '.join(added_devices)})" if added_devices else "")
        )
        report.append(
            f"  تکراری (نادیده گرفته شد): {len(skipped_devices)} دستگاه"
            + (f" ({'، '.join(skipped_devices)})" if skipped_devices else "")
        )
        report.append("")

        report.append("[تنظیمات اتصال دستگاه‌ها]")
        added_connections: list[str] = []
        skipped_connections: list[str] = []
        skipped_orphan: list[str] = []
        for device_name, cfg in source_connections.items():
            name = str(device_name).strip()
            if not name or not isinstance(cfg, dict):
                continue
            if name not in existing_device_names:
                skipped_orphan.append(name)
                continue
            if name in target_connections:
                skipped_connections.append(name)
                continue
            new_connections[name] = dict(cfg)
            added_connections.append(name)
        report.append(
            f"  افزوده شد: {len(added_connections)} تنظیمات اتصال"
            + (f" ({'، '.join(added_connections)})" if added_connections else "")
        )
        report.append(
            f"  تکراری (نادیده گرفته شد): {len(skipped_connections)} تنظیمات"
            + (f" ({'، '.join(skipped_connections)})" if skipped_connections else "")
        )
        if skipped_orphan:
            report.append(
                "  نادیده گرفته شد به دلیل نبود دستگاه متناظر در مقصد: "
                + "، ".join(skipped_orphan)
            )
        report.append("")

    if apply_products:
        _ensure_structure_registered(source_structure, source_structure_def, report)

        report.append("[ساختار محصول]")
        if source_structure and not target_structure:
            final_structure_name = source_structure
            report.append(f"  ساختار «{source_structure}» به مقصد اختصاص داده شد.")
        elif source_structure and target_structure:
            if source_structure == target_structure:
                report.append(
                    f"  ساختار «{source_structure}» در هر دو طرف یکسان است؛ بدون تغییر."
                )
            else:
                report.append(
                    f"  تکراری (نادیده گرفته شد): مقصد ساختار «{target_structure}» دارد و"
                    f" در حالت ادغام، با ساختار «{source_structure}» مبدأ جایگزین نمی‌شود."
                )
        elif not source_structure:
            report.append("  مبدأ ساختاری ندارد؛ تغییری اعمال نشد.")
        report.append("")

        report.append("[محصولات]")
        added_products = 0
        skipped_id_dups = 0
        skipped_unique_dups: list[str] = []
        if not source_products:
            report.append("  مبدأ محصولی برای انتقال ندارد.")
        elif not source_structure:
            report.append("  مبدأ ساختار محصولی ندارد؛ محصولی منتقل نشد.")
        elif not final_structure_name:
            report.append("  مقصد ساختار محصولی ندارد؛ محصولی منتقل نشد.")
        elif source_structure != final_structure_name:
            report.append(
                f"  ساختار مبدأ «{source_structure}» با ساختار مقصد «{final_structure_name}» متفاوت است؛"
                " هیچ محصولی منتقل نشد."
            )
        else:
            structures = get_product_structures()
            structure_field_defs = _lookup_structure_fields(
                structures, final_structure_name
            )
            existing_ids = {
                str(p.get("id", "")).strip()
                for p in target_products
                if isinstance(p, dict) and str(p.get("id", "")).strip()
            }
            for src_prod in source_products:
                if not isinstance(src_prod, dict):
                    continue
                pid = str(src_prod.get("id", "")).strip()
                if pid and pid in existing_ids:
                    skipped_id_dups += 1
                    continue
                values = src_prod.get("values", {})
                if not isinstance(values, dict):
                    continue
                conflict = _find_unique_conflict(new_products, values, structure_field_defs)
                if conflict is not None:
                    skipped_unique_dups.append(conflict)
                    continue
                cloned = _clone_product(src_prod)
                cloned_id = str(cloned.get("id", "")).strip()
                if cloned_id:
                    existing_ids.add(cloned_id)
                new_products.append(cloned)
                added_products += 1

            report.append(f"  افزوده شد: {added_products} محصول")
            if skipped_id_dups:
                report.append(
                    f"  تکراری بر اساس شناسه (نادیده گرفته شد): {skipped_id_dups} محصول"
                )
            if skipped_unique_dups:
                fields_summary = ", ".join(f"«{name}»" for name in skipped_unique_dups[:6])
                more = (
                    f" و {len(skipped_unique_dups) - 6} مورد دیگر"
                    if len(skipped_unique_dups) > 6
                    else ""
                )
                report.append(
                    f"  تکراری بر اساس فیلد یکتا (نادیده گرفته شد): {len(skipped_unique_dups)}"
                    f" محصول (فیلدهای: {fields_summary}{more})"
                )
        report.append("")

    if apply_devices:
        devices_by_user[target] = new_devices
        connections_by_user[target] = new_connections
    if apply_products:
        if final_structure_name:
            structure_by_user[target] = final_structure_name
        else:
            structure_by_user.pop(target, None)
        products_by_user[target] = new_products

    return _persist_all(
        devices_by_user,
        connections_by_user,
        structure_by_user,
        products_by_user,
        report,
    )


def _persist_all(
    devices_by_user: dict[str, list[dict[str, str]]],
    connections_by_user: dict[str, dict[str, dict[str, str]]],
    structure_by_user: dict[str, str],
    products_by_user: dict[str, list[dict[str, object]]],
    report: list[str],
) -> bool:
    report.append("[ذخیره‌سازی]")
    all_ok = True
    if not save_devices_by_user(devices_by_user):
        report.append("  ✗ ذخیرهٔ دستگاه‌ها ناموفق بود.")
        all_ok = False
    else:
        report.append("  ✓ دستگاه‌ها ذخیره شد.")

    if not save_device_connections_by_user(connections_by_user):
        report.append("  ✗ ذخیرهٔ تنظیمات اتصال ناموفق بود.")
        all_ok = False
    else:
        report.append("  ✓ تنظیمات اتصال ذخیره شد.")

    if not save_product_structure_by_user(structure_by_user):
        report.append("  ✗ ذخیرهٔ اختصاص ساختار محصول ناموفق بود.")
        all_ok = False
    else:
        report.append("  ✓ اختصاص ساختار محصول ذخیره شد.")

    if not save_products_by_user(products_by_user):
        report.append("  ✗ ذخیرهٔ محصولات ناموفق بود.")
        all_ok = False
    else:
        report.append("  ✓ محصولات ذخیره شد.")

    return all_ok


def _make_report_view(placeholder: str) -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setReadOnly(True)
    view.setPlaceholderText(placeholder)
    view.setMinimumHeight(180)
    view.setMinimumWidth(0)
    view.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
    text_option = view.document().defaultTextOption()
    text_option.setAlignment(Qt.AlignRight)
    view.document().setDefaultTextOption(text_option)
    return view


def _make_user_selector(label_text: str) -> tuple[QLabel, StyledComboField]:
    label = QLabel(label_text)
    label.setObjectName("FormFieldLabel")
    selector = StyledComboField()
    selector.setMinimumWidth(0)
    selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    selector.combo_box.setMinimumContentsLength(4)
    selector.combo_box.setSizeAdjustPolicy(
        QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    )
    return label, selector


def _list_managed_users() -> list[str]:
    return [
        user["username"]
        for user in get_users()
        if user.get("username", "").strip() != DEFAULT_ADMIN_USERNAME
    ]


def _populate_user_combo(
    selector: StyledComboField,
    users: list[str],
    *,
    placeholder: str = "— انتخاب —",
    empty_text: str = "کاربری وجود ندارد",
    keep_value: str = "",
) -> None:
    combo = selector.combo_box
    combo.clear()
    if not users:
        combo.addItem(empty_text, "")
        combo.setEnabled(False)
        return
    combo.setEnabled(True)
    combo.addItem(placeholder, "")
    for username in users:
        combo.addItem(username, username)
    if keep_value and keep_value in users:
        combo.setCurrentText(keep_value)


class _ModeRadios(QWidget):
    """دو رادیو «جایگزینی» و «ادغام» با توضیح زیرش."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.setLayout(layout)

        self.group = QButtonGroup(self)
        self.replace_radio = QRadioButton("جایگزینی")
        self.replace_radio.setMinimumWidth(0)
        self.replace_radio.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        replace_hint = QLabel(
            "تنظیمات فعلی مقصد پاک می‌شود و داده‌های مبدأ جایگزین می‌گردد."
        )
        replace_hint.setObjectName("DialogSubtitle")
        _configure_wrap_label(replace_hint)

        self.merge_radio = QRadioButton("ادغام")
        self.merge_radio.setMinimumWidth(0)
        self.merge_radio.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        merge_hint = QLabel(
            "داده‌های مبدأ به اطلاعات فعلی اضافه می‌شوند و موارد تکراری نادیده گرفته می‌شوند."
        )
        merge_hint.setObjectName("DialogSubtitle")
        _configure_wrap_label(merge_hint)

        self.replace_radio.setChecked(True)
        self.group.addButton(self.replace_radio)
        self.group.addButton(self.merge_radio)

        layout.addWidget(self.replace_radio)
        layout.addWidget(replace_hint)
        layout.addWidget(self.merge_radio)
        layout.addWidget(merge_hint)

    def selected_mode(self) -> str:
        return _MODE_REPLACE if self.replace_radio.isChecked() else _MODE_MERGE


class _CopyBetweenUsersSection(QWidget):
    """زیربخش «کپی بین کاربران»."""

    def __init__(self) -> None:
        super().__init__()
        self._managed_users: list[str] = []
        self._suspend_selectors = False

        layout = QVBoxLayout()
        layout.setSpacing(14)
        self.setLayout(layout)

        intro = QLabel(
            "تنظیمات کامل یک کاربر (دستگاه‌ها، تنظیمات اتصال، ساختار محصول و محصولات)"
            " را به کاربر دیگری منتقل می‌کند."
        )
        intro.setObjectName("DialogSubtitle")
        _configure_wrap_label(intro)
        layout.addWidget(intro)

        selectors_card = QFrame()
        selectors_card.setObjectName("EmptyStateCard")
        selectors_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        selectors_card.setMinimumWidth(0)
        selectors_layout = QVBoxLayout()
        selectors_layout.setContentsMargins(16, 14, 16, 14)
        selectors_layout.setSpacing(10)

        source_label, self.source_selector = _make_user_selector("کاربر مبدأ:")
        self.source_selector.currentIndexChanged.connect(self._on_selectors_changed)
        selectors_layout.addWidget(source_label)
        selectors_layout.addWidget(self.source_selector)

        target_label, self.target_selector = _make_user_selector("کاربر مقصد:")
        self.target_selector.currentIndexChanged.connect(self._on_selectors_changed)
        selectors_layout.addWidget(target_label)
        selectors_layout.addWidget(self.target_selector)

        selectors_card.setLayout(selectors_layout)
        layout.addWidget(selectors_card)

        mode_title = QLabel("نحوهٔ اعمال:")
        mode_title.setObjectName("FormFieldLabel")
        layout.addWidget(mode_title)

        self.mode_radios = _ModeRadios()
        layout.addWidget(self.mode_radios)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.apply_button = QPushButton("اعمال تنظیمات")
        self.apply_button.setObjectName("AddUserButton")
        self.apply_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.apply_button.clicked.connect(self._on_apply_clicked)
        action_row.addWidget(self.apply_button)
        layout.addLayout(action_row)

        report_title = QLabel("گزارش آخرین اعمال:")
        report_title.setObjectName("FormFieldLabel")
        layout.addWidget(report_title)

        self.report_view = _make_report_view("هنوز عملیاتی انجام نشده است.")
        layout.addWidget(self.report_view, 1)

        self.reload_users()

    def reload_users(self) -> None:
        previous_source = str(self.source_selector.combo_box.currentData() or "")
        previous_target = str(self.target_selector.combo_box.currentData() or "")
        self._managed_users = _list_managed_users()
        self._suspend_selectors = True
        try:
            _populate_user_combo(
                self.source_selector,
                self._managed_users,
                empty_text="کاربری برای کپی وجود ندارد",
                keep_value=previous_source,
            )
            _populate_user_combo(
                self.target_selector,
                self._managed_users,
                empty_text="کاربری برای کپی وجود ندارد",
                keep_value=previous_target,
            )
        finally:
            self._suspend_selectors = False
        self._update_apply_button_state()

    def _on_selectors_changed(self) -> None:
        if self._suspend_selectors:
            return
        self._update_apply_button_state()

    def _selected_source(self) -> str:
        return str(self.source_selector.combo_box.currentData() or "").strip()

    def _selected_target(self) -> str:
        return str(self.target_selector.combo_box.currentData() or "").strip()

    def _update_apply_button_state(self) -> None:
        source = self._selected_source()
        target = self._selected_target()
        ok = bool(source) and bool(target) and source != target
        self.apply_button.setEnabled(ok)

    def _on_apply_clicked(self) -> None:
        source = self._selected_source()
        target = self._selected_target()
        if not source or not target:
            QMessageBox.warning(self, "کپی تنظیمات", "کاربر مبدأ و مقصد را انتخاب کنید.")
            return
        if source == target:
            QMessageBox.warning(
                self, "کپی تنظیمات", "کاربر مبدأ و مقصد نمی‌توانند یکسان باشند."
            )
            return

        mode = self.mode_radios.selected_mode()
        mode_label = "جایگزینی کامل" if mode == _MODE_REPLACE else "ادغام"
        confirm = QMessageBox(self)
        confirm.setIcon(QMessageBox.Warning)
        confirm.setWindowTitle("تایید کپی تنظیمات")
        confirm.setText(
            f"تنظیمات کاربر «{source}» با حالت «{mode_label}» روی کاربر «{target}» اعمال شود؟"
        )
        if mode == _MODE_REPLACE:
            confirm.setInformativeText(
                "این کار، تمام تنظیمات فعلی مقصد را پاک کرده و با تنظیمات مبدأ جایگزین می‌کند."
            )
        else:
            confirm.setInformativeText(
                "موارد تکراری نادیده گرفته می‌شوند و در گزارش پایان درج خواهند شد."
            )
        ok_btn = confirm.addButton("اعمال", QMessageBox.AcceptRole)
        confirm.addButton("لغو", QMessageBox.RejectRole)
        confirm.exec()
        if confirm.clickedButton() is not ok_btn:
            return

        source_data = _gather_source_from_user(source)
        report_lines: list[str] = [
            f"حالت: {mode_label} از «{source}» به «{target}»",
            "",
        ]
        if mode == _MODE_REPLACE:
            ok = _apply_replace_from_data(target, source_data, report_lines)
        else:
            ok = _apply_merge_from_data(target, source_data, report_lines)

        self.report_view.setPlainText("\n".join(report_lines))
        if ok:
            QMessageBox.information(
                self,
                "کپی تنظیمات",
                "عملیات کپی با موفقیت انجام شد. جزئیات در گزارش پایین قابل مشاهده است.",
            )
        else:
            QMessageBox.critical(
                self,
                "کپی تنظیمات",
                "خطایی هنگام ذخیرهٔ تغییرات رخ داد. جزئیات در گزارش پایین قابل مشاهده است.",
            )


class _ExportSection(QWidget):
    """زیربخش «دریافت خروجی»."""

    def __init__(self) -> None:
        super().__init__()
        self._managed_users: list[str] = []
        self._suspend_selectors = False

        layout = QVBoxLayout()
        layout.setSpacing(14)
        self.setLayout(layout)

        intro = QLabel(
            "تنظیمات کاربر را به‌صورت یک فایل JSON روی سیستم ذخیره کنید تا بعداً برای کاربر دیگری بارگذاری شود."
        )
        intro.setObjectName("DialogSubtitle")
        _configure_wrap_label(intro)
        layout.addWidget(intro)

        selector_card = QFrame()
        selector_card.setObjectName("EmptyStateCard")
        selector_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        selector_card.setMinimumWidth(0)
        selector_layout = QVBoxLayout()
        selector_layout.setContentsMargins(16, 14, 16, 14)
        selector_layout.setSpacing(10)

        source_label, self.source_selector = _make_user_selector("کاربر مبدأ:")
        self.source_selector.currentIndexChanged.connect(self._on_selectors_changed)
        selector_layout.addWidget(source_label)
        selector_layout.addWidget(self.source_selector)
        selector_card.setLayout(selector_layout)
        layout.addWidget(selector_card)

        options_title = QLabel("چه چیزی در فایل خروجی قرار گیرد:")
        options_title.setObjectName("FormFieldLabel")
        layout.addWidget(options_title)

        self.products_check = QCheckBox("ساختار محصول و محصولات")
        self.products_check.setChecked(True)
        self.products_check.toggled.connect(self._on_selectors_changed)
        layout.addWidget(self.products_check)

        self.devices_check = QCheckBox("دستگاه‌ها و تنظیمات اتصال دستگاه‌ها")
        self.devices_check.setChecked(True)
        self.devices_check.toggled.connect(self._on_selectors_changed)
        layout.addWidget(self.devices_check)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.export_button = QPushButton("ذخیرهٔ فایل خروجی…")
        self.export_button.setObjectName("AddUserButton")
        self.export_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.export_button.clicked.connect(self._on_export_clicked)
        action_row.addWidget(self.export_button)
        layout.addLayout(action_row)

        report_title = QLabel("گزارش آخرین خروجی:")
        report_title.setObjectName("FormFieldLabel")
        layout.addWidget(report_title)

        self.report_view = _make_report_view("هنوز خروجی گرفته نشده است.")
        layout.addWidget(self.report_view, 1)

        self.reload_users()

    def reload_users(self) -> None:
        previous_source = str(self.source_selector.combo_box.currentData() or "")
        self._managed_users = _list_managed_users()
        self._suspend_selectors = True
        try:
            _populate_user_combo(
                self.source_selector,
                self._managed_users,
                empty_text="کاربری برای خروجی وجود ندارد",
                keep_value=previous_source,
            )
        finally:
            self._suspend_selectors = False
        self._update_export_button_state()

    def _on_selectors_changed(self) -> None:
        if self._suspend_selectors:
            return
        self._update_export_button_state()

    def _selected_source(self) -> str:
        return str(self.source_selector.combo_box.currentData() or "").strip()

    def _update_export_button_state(self) -> None:
        ok = (
            bool(self._selected_source())
            and (self.products_check.isChecked() or self.devices_check.isChecked())
        )
        self.export_button.setEnabled(ok)

    def _on_export_clicked(self) -> None:
        source = self._selected_source()
        if not source:
            QMessageBox.warning(self, "دریافت خروجی", "کاربر مبدأ را انتخاب کنید.")
            return
        include_products = self.products_check.isChecked()
        include_devices = self.devices_check.isChecked()
        if not include_products and not include_devices:
            QMessageBox.warning(
                self, "دریافت خروجی", "حداقل یکی از دسته‌ها را برای خروجی انتخاب کنید."
            )
            return

        source_data = _gather_source_from_user(source)
        timestamp_iso = datetime.now().isoformat(timespec="seconds")
        payload: dict[str, Any] = {
            "version": _FILE_VERSION,
            "exported_from": source,
            "exported_at": timestamp_iso,
        }
        if include_products:
            payload["products"] = {
                "structure_name": source_data["structure_name"],
                "structure_definition": source_data["structure_definition"],
                "items": source_data["products"],
            }
        if include_devices:
            payload["devices"] = {
                "list": source_data["devices"],
                "connections": source_data["connections"],
            }

        timestamp_for_name = timestamp_iso.replace(":", "-")
        suggested_name = f"settings_{source}_{timestamp_for_name}.json"
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "ذخیرهٔ فایل خروجی تنظیمات",
            suggested_name,
            "JSON (*.json)",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path = path + ".json"

        report_lines: list[str] = [
            f"کاربر مبدأ: {source}",
            f"زمان: {timestamp_iso}",
            "",
            "[محتویات فایل]",
        ]
        if include_products:
            structure_name = source_data["structure_name"] or "(بدون ساختار)"
            report_lines.append(
                f"  ساختار محصول: {structure_name}"
                f" — {len(source_data['products'])} محصول"
            )
        else:
            report_lines.append("  محصولات: شامل نشد")
        if include_devices:
            report_lines.append(
                f"  دستگاه‌ها: {len(source_data['devices'])} دستگاه"
                f" — {len(source_data['connections'])} تنظیمات اتصال"
            )
        else:
            report_lines.append("  دستگاه‌ها: شامل نشد")
        report_lines.append("")

        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
        except OSError as exc:
            report_lines.append(f"[ذخیره‌سازی]\n  ✗ خطا در نوشتن فایل: {exc}")
            self.report_view.setPlainText("\n".join(report_lines))
            QMessageBox.critical(
                self,
                "دریافت خروجی",
                f"ذخیرهٔ فایل ناموفق بود:\n{exc}",
            )
            return

        report_lines.append("[ذخیره‌سازی]")
        report_lines.append(f"  ✓ فایل با موفقیت ذخیره شد:\n  {path}")
        self.report_view.setPlainText("\n".join(report_lines))
        QMessageBox.information(
            self,
            "دریافت خروجی",
            f"فایل با موفقیت ذخیره شد:\n{path}",
        )


class _ImportSection(QWidget):
    """زیربخش «بارگذاری از فایل»."""

    def __init__(self) -> None:
        super().__init__()
        self._managed_users: list[str] = []
        self._suspend_selectors = False
        self._loaded_path: str = ""
        self._loaded_payload: dict[str, Any] | None = None

        layout = QVBoxLayout()
        layout.setSpacing(14)
        self.setLayout(layout)

        intro = QLabel(
            "یک فایل JSON خروجی‌گرفته‌شده را انتخاب کنید و آن را روی کاربر مقصد اعمال نمایید."
            " بسته به محتوای فایل، ممکن است شامل محصولات، دستگاه‌ها یا هر دو باشد."
        )
        intro.setObjectName("DialogSubtitle")
        _configure_wrap_label(intro)
        layout.addWidget(intro)

        target_card = QFrame()
        target_card.setObjectName("EmptyStateCard")
        target_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        target_card.setMinimumWidth(0)
        target_layout = QVBoxLayout()
        target_layout.setContentsMargins(16, 14, 16, 14)
        target_layout.setSpacing(10)

        target_label, self.target_selector = _make_user_selector("کاربر مقصد:")
        self.target_selector.currentIndexChanged.connect(self._on_selectors_changed)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_selector)
        target_card.setLayout(target_layout)
        layout.addWidget(target_card)

        file_title = QLabel("فایل خروجی:")
        file_title.setObjectName("FormFieldLabel")
        layout.addWidget(file_title)

        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        self.choose_file_button = QPushButton("انتخاب فایل…")
        self.choose_file_button.setObjectName("AddUserButton")
        self.choose_file_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.choose_file_button.clicked.connect(self._on_choose_file)
        file_row.addWidget(self.choose_file_button, 0, Qt.AlignTop)

        self.file_status_label = QLabel("هنوز فایلی انتخاب نشده است.")
        self.file_status_label.setObjectName("DialogSubtitle")
        _configure_wrap_label(self.file_status_label)
        file_row.addWidget(self.file_status_label, 1)
        layout.addLayout(file_row)

        mode_title = QLabel("نحوهٔ اعمال:")
        mode_title.setObjectName("FormFieldLabel")
        layout.addWidget(mode_title)

        self.mode_radios = _ModeRadios()
        layout.addWidget(self.mode_radios)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.apply_button = QPushButton("اعمال فایل")
        self.apply_button.setObjectName("AddUserButton")
        self.apply_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.apply_button.clicked.connect(self._on_apply_clicked)
        action_row.addWidget(self.apply_button)
        layout.addLayout(action_row)

        report_title = QLabel("گزارش آخرین بارگذاری:")
        report_title.setObjectName("FormFieldLabel")
        layout.addWidget(report_title)

        self.report_view = _make_report_view("هنوز فایلی اعمال نشده است.")
        layout.addWidget(self.report_view, 1)

        self.reload_users()

    def reload_users(self) -> None:
        previous_target = str(self.target_selector.combo_box.currentData() or "")
        self._managed_users = _list_managed_users()
        self._suspend_selectors = True
        try:
            _populate_user_combo(
                self.target_selector,
                self._managed_users,
                empty_text="کاربری برای بارگذاری وجود ندارد",
                keep_value=previous_target,
            )
        finally:
            self._suspend_selectors = False
        self._update_apply_button_state()

    def _on_selectors_changed(self) -> None:
        if self._suspend_selectors:
            return
        self._update_apply_button_state()

    def _selected_target(self) -> str:
        return str(self.target_selector.combo_box.currentData() or "").strip()

    def _update_apply_button_state(self) -> None:
        ok = bool(self._selected_target()) and self._loaded_payload is not None
        self.apply_button.setEnabled(ok)

    def _on_choose_file(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "انتخاب فایل خروجی تنظیمات",
            "",
            "JSON (*.json);;All Files (*)",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            self._loaded_payload = None
            self._loaded_path = ""
            self.file_status_label.setText(f"خواندن فایل ناموفق بود: {exc}")
            self._update_apply_button_state()
            QMessageBox.critical(
                self,
                "بارگذاری فایل",
                f"خواندن فایل ناموفق بود:\n{exc}",
            )
            return

        if not isinstance(payload, dict):
            self._loaded_payload = None
            self._loaded_path = ""
            self.file_status_label.setText("ساختار فایل معتبر نیست.")
            self._update_apply_button_state()
            QMessageBox.critical(
                self,
                "بارگذاری فایل",
                "ساختار فایل JSON معتبر نیست.",
            )
            return

        has_products = "products" in payload and isinstance(payload.get("products"), dict)
        has_devices = "devices" in payload and isinstance(payload.get("devices"), dict)
        if not has_products and not has_devices:
            self._loaded_payload = None
            self._loaded_path = ""
            self.file_status_label.setText(
                "این فایل هیچ بخش قابل اعمالی (محصولات یا دستگاه‌ها) ندارد."
            )
            self._update_apply_button_state()
            QMessageBox.warning(
                self,
                "بارگذاری فایل",
                "این فایل بخش قابل اعمالی ندارد.",
            )
            return

        self._loaded_payload = payload
        self._loaded_path = path

        exported_from = str(payload.get("exported_from", "")).strip() or "(نامشخص)"
        exported_at = str(payload.get("exported_at", "")).strip() or "(نامشخص)"
        sections: list[str] = []
        if has_products:
            products = payload["products"]
            structure_name = str(products.get("structure_name", "")).strip() or "(بدون ساختار)"
            items_count = (
                len(products.get("items", []))
                if isinstance(products.get("items"), list)
                else 0
            )
            sections.append(f"محصولات (ساختار: {structure_name}، {items_count} مورد)")
        if has_devices:
            devices = payload["devices"]
            list_count = (
                len(devices.get("list", []))
                if isinstance(devices.get("list"), list)
                else 0
            )
            connections_count = (
                len(devices.get("connections", {}))
                if isinstance(devices.get("connections"), dict)
                else 0
            )
            sections.append(
                f"دستگاه‌ها ({list_count} دستگاه، {connections_count} تنظیمات اتصال)"
            )
        self.file_status_label.setText(
            f"فایل: {path}\n"
            f"خروجی‌گرفته‌شده از: {exported_from} — زمان: {exported_at}\n"
            f"شامل: {' | '.join(sections)}"
        )
        self._update_apply_button_state()

    def _on_apply_clicked(self) -> None:
        target = self._selected_target()
        if not target or not self._loaded_payload:
            return

        payload = self._loaded_payload
        source_data = _gather_source_from_payload(payload)
        apply_devices = bool(source_data.get("_has_devices_section"))
        apply_products = bool(source_data.get("_has_products_section"))

        mode = self.mode_radios.selected_mode()
        mode_label = "جایگزینی کامل" if mode == _MODE_REPLACE else "ادغام"

        confirm = QMessageBox(self)
        confirm.setIcon(QMessageBox.Warning)
        confirm.setWindowTitle("تایید بارگذاری از فایل")
        confirm.setText(
            f"محتوای فایل با حالت «{mode_label}» روی کاربر «{target}» اعمال شود؟"
        )
        sections: list[str] = []
        if apply_products:
            sections.append("محصولات و ساختار محصول")
        if apply_devices:
            sections.append("دستگاه‌ها و تنظیمات اتصال")
        confirm.setInformativeText("بخش‌های قابل اعمال: " + " — ".join(sections))
        ok_btn = confirm.addButton("اعمال", QMessageBox.AcceptRole)
        confirm.addButton("لغو", QMessageBox.RejectRole)
        confirm.exec()
        if confirm.clickedButton() is not ok_btn:
            return

        exported_from = str(payload.get("exported_from", "")).strip() or "(نامشخص)"
        report_lines: list[str] = [
            f"حالت: {mode_label} از فایل (مبدأ: {exported_from}) به کاربر «{target}»",
            f"فایل: {self._loaded_path}",
            "",
        ]
        if mode == _MODE_REPLACE:
            ok = _apply_replace_from_data(
                target,
                source_data,
                report_lines,
                apply_devices=apply_devices,
                apply_products=apply_products,
            )
        else:
            ok = _apply_merge_from_data(
                target,
                source_data,
                report_lines,
                apply_devices=apply_devices,
                apply_products=apply_products,
            )

        self.report_view.setPlainText("\n".join(report_lines))
        if ok:
            QMessageBox.information(
                self,
                "بارگذاری فایل",
                "بارگذاری با موفقیت انجام شد. جزئیات در گزارش پایین قابل مشاهده است.",
            )
        else:
            QMessageBox.critical(
                self,
                "بارگذاری فایل",
                "خطایی هنگام ذخیرهٔ تغییرات رخ داد. جزئیات در گزارش پایین قابل مشاهده است.",
            )


class CopyUserSettingsTab(QWidget):
    """تب «کپی تنظیمات کاربر» با سه زیربخش: کپی، خروجی، بارگذاری."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        self.setLayout(layout)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("CopySettingsSubTabs")

        self.copy_section = _CopyBetweenUsersSection()
        self.export_section = _ExportSection()
        self.import_section = _ImportSection()

        self._tabs.addTab(self.copy_section, "کپی بین کاربران")
        self._tabs.addTab(self.export_section, "دریافت خروجی")
        self._tabs.addTab(self.import_section, "بارگذاری از فایل")

        layout.addWidget(self._tabs)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.copy_section.reload_users()
        self.export_section.reload_users()
        self.import_section.reload_users()
