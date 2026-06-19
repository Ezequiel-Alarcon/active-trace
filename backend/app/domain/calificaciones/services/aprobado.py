"""Logica de derivacion aprobado (C-10).

Deriva si una calificacion esta aprobada segun el tipo de nota y el umbral.
"""

from __future__ import annotations

from typing import Any


def derivar_aprobado(
    nota: Any,
    umbral_pct: int,
    conjunto_aprobado: list[str] | None,
    escala_max: int = 10,
) -> bool:
    """Deriva si una nota aprueba segun el umbral configurado.

    Args:
        nota: El valor de la calificacion (None, int, float, str, list)
        umbral_pct: El umbral de aprobacion porcentual (0-100)
        conjunto_aprobado: Lista de valores textuales que indican aprobacion
        escala_max: Escala maxima de la nota (default 10). Se usa para convertir
            la nota a porcentaje: ``nota / escala_max * 100 >= umbral_pct``.

    Returns:
        True si la nota aprueba, False en caso contrario
    """
    if nota is None:
        return False

    if isinstance(nota, (int, float)):
        return nota / escala_max * 100 >= umbral_pct

    if isinstance(nota, str):
        if conjunto_aprobado is None:
            return False
        return nota in conjunto_aprobado

    if isinstance(nota, list):
        if conjunto_aprobado is None:
            return False
        return any(item in conjunto_aprobado for item in nota)

    return False