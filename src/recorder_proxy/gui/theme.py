from __future__ import annotations


APP_STYLE = """
QWidget {
    background: #F6F8FB;
    color: #172033;
    font-size: 13px;
    font-family: "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei";
}
QFrame#Sidebar {
    background: #111827;
    border: 0;
}
QLabel#SidebarTitle {
    background: transparent;
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 800;
    padding: 4px 4px 10px 4px;
}
QListWidget {
    background: transparent;
    color: #CBD5E1;
    border: 0;
    padding: 0;
}
QListWidget::item {
    min-height: 36px;
    padding: 8px 12px;
    border-radius: 6px;
    color: #9CA3AF;
}
QListWidget::item:hover {
    background: #1F2937;
    color: #E5E7EB;
}
QListWidget::item:selected {
    background: #2563EB;
    color: white;
}
QFrame#Page {
    background: #F6F8FB;
}
QFrame#Panel, QFrame#ConfigCard {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
QLabel#HeroTitle {
    font-size: 28px;
    font-weight: 800;
    color: #0F172A;
}
QLabel#CardTitle, QLabel#ConfigCardTitle {
    font-size: 18px;
    font-weight: 800;
    color: #0F172A;
}
QLabel#SubtleText, QLabel#MutedText, QLabel#FieldName {
    color: #64748B;
}
QLabel#SavedBadge {
    background: #DCFCE7;
    color: #16A34A;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: 700;
}
QLabel#DirtyBadge {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: 700;
}
QLabel#Warning {
    color: #B42318;
    font-weight: 700;
}
QPushButton {
    background: #2563EB;
    color: white;
    border: 0;
    border-radius: 6px;
    min-height: 36px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { background: #1D4ED8; }
QPushButton#PrimaryButton {
    background: #2563EB;
    color: white;
    border: 1px solid #2563EB;
}
QPushButton#SecondaryButton {
    background: #FFFFFF;
    color: #2563EB;
    border: 1px solid #AFC3F6;
}
QPushButton#SecondaryButton:hover {
    background: #EFF6FF;
}
QPushButton#SecondaryButton:checked, QPushButton#PrimaryButton:checked {
    background: #DBEAFE;
    color: #1D4ED8;
    border: 1px solid #2563EB;
}
QPushButton#DangerButton {
    background: #FFFFFF;
    color: #DC2626;
    border: 1px solid #F3B4B4;
}
QPushButton#DangerButton:hover {
    background: #FEF2F2;
}
QPushButton:disabled {
    background: #F3F4F6;
    color: #9CA3AF;
    border: 1px solid #E5E7EB;
}
QLineEdit, QSpinBox, QComboBox {
    min-height: 34px;
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 4px 8px;
}
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8FAFC;
    gridline-color: #E2E8F0;
    selection-background-color: #DBEAFE;
    selection-color: #111827;
    border: 1px solid #E2E8F0;
}
QHeaderView::section {
    background: #EEF2F7;
    color: #334155;
    padding: 7px;
    border: 0;
    border-right: 1px solid #E2E8F0;
    font-weight: 600;
}
QTextEdit {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
}
"""
