def get_app_stylesheet() -> str:
    return """
    QWidget {
        font-family: "Vazirmatn", "Vazir", "Shabnam", "Sahel", "IRANSans", "IRANSansX", "Segoe UI", "Tahoma", "Arial";
        font-size: 14px;
        color: #1f2937;
    }
    QMainWindow, QDialog {
        background-color: #f3f5f9;
    }
    QDialog#ProductDialog {
        background-color: #f3f5f9;
    }
    QDialog#ScanDetailFieldsDialog {
        background-color: #f3f5f9;
    }
    QDialog#ScanDetailFieldsDialog QLabel#DialogSubtitle {
        color: #475569;
    }
    QDialog#ScanDetailFieldsDialog QScrollArea#ScanDetailFieldsScroll {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        background-color: #ffffff;
    }
    QDialog#ScanDetailFieldsDialog QScrollArea#ScanDetailFieldsScroll QAbstractScrollArea::viewport {
        background-color: #ffffff;
        border: none;
        border-radius: 12px;
    }
    QDialog#ScanDetailFieldsDialog QWidget#ScanDetailFieldsInner {
        background-color: #ffffff;
    }
    QDialog#ScanDetailFieldsDialog QFrame#ScanDetailFieldRow {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
    QDialog#ScanDetailFieldsDialog QFrame#ScanDetailFieldRow:hover {
        border-color: #93c5fd;
        background-color: #eff6ff;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailFieldToggle {
        min-width: 18px;
        max-width: 18px;
        min-height: 18px;
        max-height: 18px;
        border: 1px solid #94a3b8;
        border-radius: 4px;
        background-color: #ffffff;
        color: #ffffff;
        font-size: 9px;
        font-weight: 800;
        padding: 0px;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailFieldToggle:hover {
        border-color: #2563eb;
        background-color: #f8fafc;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailFieldToggle:checked {
        background-color: #2563eb;
        border: 1px solid #1d4ed8;
        color: #ffffff;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailFieldToggle:checked:hover {
        background-color: #1d4ed8;
        border-color: #1e40af;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailModeToggle {
        min-height: 24px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background-color: #ffffff;
        color: #334155;
        font-size: 12px;
        font-weight: 600;
        padding: 0 8px;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailModeToggle:hover {
        border-color: #93c5fd;
        background-color: #f8fbff;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailModeToggle:checked {
        border-color: #93c5fd;
        background-color: #dbeafe;
        color: #1e40af;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailModeToggle:disabled {
        border-color: #e2e8f0;
        background-color: #f8fafc;
        color: #94a3b8;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#PrimaryButton {
        min-height: 44px;
        min-width: 128px;
        padding: 0 22px;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#SecondaryButton {
        min-height: 44px;
        min-width: 128px;
        padding: 0 22px;
        text-align: center;
    }
    #ScanDetailPickButton {
        border: 1px solid #d8e1ef;
        border-radius: 12px;
        background-color: #ffffff;
        color: #1f2937;
        font-size: 13px;
        font-weight: 600;
        min-height: 36px;
        padding: 0 10px;
        text-align: center;
    }
    #ScanDetailPickButton:hover {
        border-color: #93c5fd;
        background-color: #f8fbff;
    }
    #ScanDetailPickButton:pressed {
        background-color: #f1f5f9;
    }
    #ScanDetailPickButton:disabled {
        color: #94a3b8;
        border-color: #e2e8f0;
        background-color: #f8fafc;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailPresetAll {
        min-height: 38px;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        background-color: #eff6ff;
        color: #1d4ed8;
        font-size: 14px;
        font-weight: 600;
        padding: 0 14px;
        text-align: right;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailPresetAll:hover {
        border-color: #93c5fd;
        background-color: #dbeafe;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailPresetNone {
        min-height: 38px;
        border: 1px solid #d8e1ef;
        border-radius: 12px;
        background-color: #ffffff;
        color: #1f2937;
        font-size: 14px;
        font-weight: 600;
        padding: 0 10px;
        text-align: right;
    }
    QDialog#ScanDetailFieldsDialog QPushButton#ScanDetailPresetNone:hover {
        border-color: #93c5fd;
        background-color: #f8fbff;
    }
    QLineEdit {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        padding: 0 10px;
        background-color: #ffffff;
    }
    QLineEdit:focus {
        border: 1px solid #3b82f6;
    }
    QPlainTextEdit {
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        padding: 8px 10px;
        background-color: #ffffff;
        color: #1f2937;
    }
    QPlainTextEdit:focus {
        border: 1px solid #3b82f6;
    }
    QDateTimeEdit {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        padding: 0 10px;
        background-color: #ffffff;
        color: #1f2937;
    }
    QDateTimeEdit:focus {
        border: 1px solid #3b82f6;
    }
    #StyledComboFieldShell {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        background-color: #ffffff;
    }
    #StyledComboFieldShell:hover {
        border-color: #93c5fd;
    }
    #StyledComboFieldShell[focusWithin="true"] {
        border: 1px solid #3b82f6;
    }
    #StyledComboFieldCombo {
        border: none;
        background-color: transparent;
        padding: 0 8px;
        min-height: 36px;
        color: #1f2937;
        combobox-popup: 0;
    }
    #StyledComboFieldCombo::drop-down {
        width: 0px;
        height: 0px;
        border: none;
        padding: 0px;
    }
    #StyledComboFieldCombo QAbstractItemView {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #94a3b8;
        border-radius: 8px;
        outline: none;
        padding: 4px;
        selection-background-color: #dbeafe;
        selection-color: #1e3a8a;
    }
    #StyledComboFieldCombo QAbstractItemView::item {
        min-height: 32px;
        padding: 6px 10px;
        border-radius: 6px;
    }
    #StyledComboFieldCombo QAbstractItemView::item:hover {
        background-color: #eff6ff;
        color: #1f2937;
    }
    #StyledComboFieldChevron {
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        background-color: #f1f5f9;
        border: none;
        padding: 0px;
    }
    #AppContentScrollArea, #DeviceSettingsScrollArea, #ProductFormScrollArea {
        border: none;
        background: #ffffff;
    }
    #ProductFormScrollArea QAbstractScrollArea::viewport {
        background-color: #ffffff;
        border: none;
    }
    #AppContentScrollArea > QWidget > QWidget,
    #DeviceSettingsScrollArea > QWidget > QWidget,
    #ProductFormScrollArea > QWidget > QWidget,
    #DeviceSettingsScrollContent,
    #ProductFormScrollContent {
        background: #ffffff;
    }
    #AppContentScrollArea QScrollBar:vertical,
    #DeviceSettingsScrollArea QScrollBar:vertical,
    #ProductFormScrollArea QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 2px 2px 2px 0;
        border: none;
    }
    #AppContentScrollArea QScrollBar::handle:vertical,
    #DeviceSettingsScrollArea QScrollBar::handle:vertical,
    #ProductFormScrollArea QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 28px;
        border-radius: 5px;
    }
    #AppContentScrollArea QScrollBar::handle:vertical:hover,
    #DeviceSettingsScrollArea QScrollBar::handle:vertical:hover,
    #ProductFormScrollArea QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    #AppContentScrollArea QScrollBar::add-line:vertical,
    #AppContentScrollArea QScrollBar::sub-line:vertical,
    #DeviceSettingsScrollArea QScrollBar::add-line:vertical,
    #DeviceSettingsScrollArea QScrollBar::sub-line:vertical,
    #ProductFormScrollArea QScrollBar::add-line:vertical,
    #ProductFormScrollArea QScrollBar::sub-line:vertical {
        height: 0px;
        border: none;
        background: transparent;
    }
    #AppContentScrollArea QScrollBar::add-page:vertical,
    #AppContentScrollArea QScrollBar::sub-page:vertical,
    #DeviceSettingsScrollArea QScrollBar::add-page:vertical,
    #DeviceSettingsScrollArea QScrollBar::sub-page:vertical,
    #ProductFormScrollArea QScrollBar::add-page:vertical,
    #ProductFormScrollArea QScrollBar::sub-page:vertical {
        background: transparent;
    }
    #DeviceTypeSelectorShell {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        background-color: #ffffff;
    }
    #DeviceTypeSelectorShell:hover {
        border-color: #93c5fd;
    }
    #DeviceTypeSelectorShell[focusWithin="true"] {
        border: 1px solid #3b82f6;
    }
    #DeviceTypeInnerCombo {
        border: none;
        background-color: transparent;
        padding: 0 8px;
        min-height: 36px;
        color: #1f2937;
        combobox-popup: 0;
    }
    #DeviceTypeInnerCombo::drop-down {
        width: 0px;
        height: 0px;
        border: none;
        padding: 0px;
    }
    #DeviceTypeInnerCombo QAbstractItemView {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #94a3b8;
        border-radius: 8px;
        outline: none;
        padding: 4px;
        selection-background-color: #dbeafe;
        selection-color: #1e3a8a;
    }
    #DeviceTypeInnerCombo QAbstractItemView::item {
        min-height: 32px;
        padding: 6px 10px;
        border-radius: 6px;
    }
    #DeviceTypeInnerCombo QAbstractItemView::item:hover {
        background-color: #eff6ff;
        color: #1f2937;
    }
    #DevicesUserSelectorShell {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        background-color: #ffffff;
    }
    #DevicesUserSelectorShell:hover {
        border-color: #93c5fd;
    }
    #DevicesUserSelectorShell[focusWithin="true"] {
        border: 1px solid #3b82f6;
    }
    #DevicesUserInnerCombo {
        border: none;
        background-color: transparent;
        padding: 0 8px;
        min-height: 36px;
        color: #1f2937;
        combobox-popup: 0;
    }
    #DevicesUserInnerCombo::drop-down {
        width: 0px;
        height: 0px;
        border: none;
        padding: 0px;
    }
    #DevicesUserInnerCombo QAbstractItemView {
        background-color: #ffffff;
        color: #1f2937;
        border: 1px solid #94a3b8;
        border-radius: 8px;
        outline: none;
        padding: 4px;
        selection-background-color: #dbeafe;
        selection-color: #1e3a8a;
    }
    #DevicesUserInnerCombo QAbstractItemView::item {
        min-height: 32px;
        padding: 6px 10px;
        border-radius: 6px;
    }
    #DevicesUserInnerCombo QAbstractItemView::item:hover {
        background-color: #eff6ff;
        color: #1f2937;
    }
    #DevicesUserSelectorChevron {
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        background-color: #f1f5f9;
        border: none;
        padding: 0px;
    }
    #Card {
        background-color: #ffffff;
        border: 1px solid #e4e8f0;
        border-radius: 14px;
    }
    #HomeTopCard {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 4px;
    }
    #HomeDeviceChip {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
    }
    #HomeDeviceName {
        font-weight: 600;
        color: #1f2937;
    }
    #HomeDeviceStatusIdle {
        color: #94a3b8;
        font-weight: 700;
        min-width: 1.2em;
    }
    #HomeDeviceStatusOk {
        color: #15803d;
        font-weight: 700;
        min-width: 1.2em;
    }
    #HomeDeviceStatusFail {
        color: #b91c1c;
        font-weight: 700;
        min-width: 1.2em;
    }
    #DialogTitle {
        font-size: 22px;
        font-weight: 700;
    }
    #DialogSubtitle {
        color: #6b7280;
    }
    #ScanPrintStatus {
        color: #9ca3af;
        font-size: 11px;
    }
    #PageTitle {
        font-size: 22px;
        font-weight: 700;
    }
    #WelcomeText {
        font-size: 16px;
        font-weight: 500;
    }
    #PrimaryButton {
        min-height: 40px;
        border: none;
        border-radius: 10px;
        background-color: #2563eb;
        color: #ffffff;
        font-weight: 600;
    }
    #PrimaryButton:hover {
        background-color: #1d4ed8;
    }
    #IconButton {
        min-width: 40px;
        max-width: 40px;
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        background-color: #ffffff;
        font-size: 16px;
    }
    #IconButton:hover {
        border-color: #93c5fd;
        background-color: #f8fbff;
    }
    #SidebarNav {
        background-color: #0f2557;
        border: none;
        border-radius: 14px;
    }
    #UserBadge {
        background-color: #163472;
        border: 1px solid #2a4ea3;
        border-radius: 12px;
    }
    #UserAvatar {
        background-color: #f97316;
        color: #ffffff;
        border: 2px solid #fdba74;
        border-radius: 32px;
        font-size: 26px;
        font-weight: 800;
        qproperty-alignment: AlignCenter;
    }
    #UserBadgeName {
        color: #f8fafc;
        font-size: 13px;
        font-weight: 800;
    }
    #NavItem {
        border: none;
        border-radius: 10px;
        background-color: transparent;
    }
    #NavItem[active="true"] {
        background-color: #1f3f84;
    }
    #NavItem:hover {
        background-color: #7c441a;
    }
    #NavItem:pressed {
        background-color: #274b96;
    }
    #NavItemText {
        color: #eef3ff;
        font-size: 12px;
        font-weight: 800;
    }
    #NavItemIcon {
        color: #eef3ff;
        font-size: 12px;
    }
    #ManagementTabs::pane {
        border: 1px solid #d8e1ef;
        border-radius: 10px;
        background: #ffffff;
        margin-top: 8px;
    }
    #ManagementTabs QTabBar::tab {
        background: #eef2f9;
        border: 1px solid #d8e1ef;
        border-bottom: none;
        padding: 8px 14px;
        margin-left: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    #ManagementTabs QTabBar::tab:first {
        margin-right: 2px;
    }
    #ManagementTabs QTabBar::tab:selected {
        background: #ffffff;
        color: #0f2557;
        font-weight: 700;
    }
    #CopySettingsSubTabs {
        background: #ffffff;
        margin-top: 10px;
    }
    #CopySettingsSubTabs::pane {
        border: 1px solid #d8e1ef;
        border-radius: 10px;
        background: #ffffff;
        margin-top: 6px;
    }
    #CopySettingsSubTabs QTabBar::tab {
        background: #eef2f9;
        color: #1f2937;
        border: 1px solid #d8e1ef;
        border-bottom: none;
        padding: 6px 12px;
        margin-left: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    #CopySettingsSubTabs QTabBar::tab:selected {
        background: #ffffff;
        color: #0f2557;
        font-weight: 700;
    }
    #SecondaryButton {
        border: 1px solid #d8e1ef;
        border-radius: 12px;
        background-color: #ffffff;
        font-size: 14px;
        font-weight: 600;
        text-align: right;
        padding: 0 10px;
    }
    #SecondaryButton:hover {
        border-color: #93c5fd;
        background-color: #f8fbff;
    }
    #AddFieldButton {
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        background-color: #eff6ff;
        color: #1d4ed8;
        font-size: 14px;
        font-weight: 600;
        padding: 0 10px;
        min-height: 38px;
    }
    #AddFieldButton:hover {
        border-color: #93c5fd;
        background-color: #dbeafe;
    }
    #AddUserButton {
        min-height: 44px;
        border: none;
        border-radius: 12px;
        background-color: #f97316;
        color: #ffffff;
        font-size: 14px;
        font-weight: 600;
        padding: 0 14px;
    }
    #AddUserButton:hover {
        background-color: #ea580c;
    }
    #AddUserButton:pressed {
        background-color: #c2410c;
    }
    #DangerButton {
        border: 1px solid #fecaca;
        border-radius: 12px;
        background-color: #fef2f2;
        color: #b91c1c;
        font-size: 14px;
        font-weight: 600;
        padding: 0 10px;
        min-height: 38px;
    }
    #DangerButton:hover {
        border-color: #fca5a5;
        background-color: #fee2e2;
    }
    #UsersTable {
        border: 1px solid #dbe5f1;
        border-radius: 10px;
        background-color: #ffffff;
        alternate-background-color: #f8fbff;
        gridline-color: #edf2f7;
        selection-background-color: transparent;
        selection-color: #1f2937;
    }
    #UsersTable QHeaderView::section {
        background-color: #f1f5fb;
        color: #334155;
        border: none;
        border-bottom: 1px solid #dbe5f1;
        padding: 8px 10px;
        font-weight: 700;
    }
    #UsersTable::item:selected {
        background-color: transparent;
        color: #1f2937;
    }
    #UsersTable QLineEdit {
        min-height: 32px;
    }
    #UsersTable QScrollBar:vertical {
        background: #f1f5fb;
        width: 12px;
        margin: 2px 2px 2px 0;
        border: none;
        border-radius: 6px;
    }
    #UsersTable QScrollBar::handle:vertical {
        background: #94a3b8;
        min-height: 32px;
        border-radius: 6px;
    }
    #UsersTable QScrollBar::handle:vertical:hover {
        background: #64748b;
    }
    #UsersTable QScrollBar::add-line:vertical,
    #UsersTable QScrollBar::sub-line:vertical {
        height: 0px;
        border: none;
        background: transparent;
    }
    #UsersTable QScrollBar::add-page:vertical,
    #UsersTable QScrollBar::sub-page:vertical {
        background: transparent;
    }
    #RowIconButton, #RowDangerIconButton, #RowConfirmIconButton {
        min-width: 30px;
        max-width: 30px;
        min-height: 30px;
        max-height: 30px;
        border: none;
        background-color: transparent;
        font-size: 14px;
    }
    #RowIconButton {
        color: #2563eb;
    }
    #RowIconButton:hover {
        color: #1d4ed8;
    }
    #RowConfirmIconButton {
        border-color: #bbf7d0;
        background-color: #f0fdf4;
        color: #166534;
    }
    #RowConfirmIconButton:hover {
        border-color: #86efac;
        background-color: #dcfce7;
    }
    #RowDangerIconButton {
        color: #dc2626;
    }
    #RowDangerIconButton:hover {
        color: #b91c1c;
    }
    #FormFieldLabel {
        color: #374151;
        font-size: 14px;
        font-weight: 600;
    }
    #FormFieldGroup {
        background: transparent;
    }
    #AllowedUsersSpin {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        padding: 0 10px;
        background-color: #ffffff;
        font-size: 14px;
    }
    #AllowedUsersSpin:focus {
        border: 1px solid #3b82f6;
        background-color: #ffffff;
    }
    #RejectorMsSpin {
        min-height: 38px;
        border: 1px solid #d0d7e2;
        border-radius: 10px;
        padding: 0 10px;
        background-color: #ffffff;
        font-size: 14px;
        color: #1f2937;
    }
    #RejectorMsSpin:hover {
        border-color: #93c5fd;
    }
    #RejectorMsSpin:focus {
        border: 1px solid #3b82f6;
        background-color: #ffffff;
        color: #1f2937;
    }
    #RejectorMsSpin QLineEdit {
        border: none;
        padding: 0px;
        min-height: 34px;
        background-color: #ffffff;
        color: #1f2937;
        selection-background-color: #bfdbfe;
        selection-color: #1f2937;
    }
    #RejectorMsSpin QLineEdit:focus {
        background-color: #ffffff;
        color: #1f2937;
    }
    #SettingsSaveButton {
        min-height: 38px;
        max-width: 220px;
        border: none;
        border-radius: 10px;
        background-color: #2563eb;
        color: #ffffff;
        font-size: 14px;
        font-weight: 600;
        padding: 0 14px;
    }
    #SettingsSaveButton:hover {
        background-color: #1d4ed8;
    }
    #SettingsSaveButton:pressed {
        background-color: #1e40af;
    }
    #EmptyStateCard {
        background-color: #fff7ed;
        border: 1px solid #fdba74;
        border-radius: 12px;
    }
    #EmptyStateText {
        color: #9a3412;
        font-size: 14px;
        font-weight: 600;
    }
    """
