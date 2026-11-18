"""Pruebas de como se limpian los datos de conexion que pega la gente."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mostrador.tiendanube import limpiar_conexion  # noqa: E402

TOKEN = "3f8a9c2b1d4e5f60718293a4b5c6d7e8f9012345"


@pytest.mark.parametrize("tid,tok", [
    ("1234567", TOKEN),
    (" 1234567 ", f"  {TOKEN}  "),
    ("Número de tienda: 1234567", f"Token: {TOKEN}"),
    ("TN_STORE_ID=1234567", f"TN_TOKEN={TOKEN}"),
    ("1234567", f"bearer {TOKEN}"),
    ("1234567", f"'{TOKEN}'"),
    ("#1234567", f"Token de acceso: {TOKEN}"),
])
def test_un_dato_por_campo(tid, tok):
    assert limpiar_conexion(tid, tok) == ("1234567", TOKEN)


def test_mensaje_entero_en_un_campo():
    mensaje = f"Hola! Tus datos para Mostrador:\nNúmero de tienda: 1234567\nToken: {TOKEN}\n"
    assert limpiar_conexion(mensaje, "") == ("1234567", TOKEN)
    assert limpiar_conexion("", mensaje) == ("1234567", TOKEN)


def test_vacios():
    assert limpiar_conexion("", "") == ("", "")
    assert limpiar_conexion(None, None) == ("", "")
    assert limpiar_conexion("abc", TOKEN) == ("", TOKEN)
