# app/ui/characterEditor/field_schema.py

from PyQt6.QtWidgets import QLineEdit, QComboBox


BIO_FIELDS = [
    {
        "key": "id",
        "label": "ID",
        "widget": QLineEdit,
    },
    {
        "key": "name",
        "label": "Name",
        "widget": QLineEdit,
    },
    {
        "key": "alias",
        "label": "Alias",
        "widget": QLineEdit,
    },
    {
        "key": "gender",
        "label": "Gender",
        "widget": QComboBox,
        "items": ["", "女", "男"]
    },
    {
        "key": "age",
        "label": "Age",
        "widget": QLineEdit,
    },
    {
        "key": "birthdate",
        "label": "Birthdate",
        "widget": QLineEdit,
    },
    {
        "key": "hair_color",
        "label": "Hair",
        "widget": QLineEdit,
    },
    {
        "key": "eye_color",
        "label": "Eyes",
        "widget": QLineEdit,
    },
    {
        "key": "height",
        "label": "Height",
        "widget": QLineEdit,
    },
    {
        "key": "weight",
        "label": "Weight",
        "widget": QLineEdit,
    },
    {
        "key": "bwh",
        "label": "BWH",
        "widget": QLineEdit,
    },
    {
        "key": "weapon",
        "label": "Weapon",
        "widget": QLineEdit,
    },
    {
        "key": "identity",
        "label": "Identity",
        "widget": QLineEdit,
    },
    {
        "key": "rank",
        "label": "Rank",
        "widget": QLineEdit,
    },
]