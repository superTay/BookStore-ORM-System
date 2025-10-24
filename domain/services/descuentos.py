"""Domain pricing services: discounts.

Provides a simple helper to apply percentage-based discounts to prices with
input validation and predictable rounding behavior.
"""

from typing import Union

Number = Union[int, float]


def aplicar_descuento(precio_original: Number, porcentaje_descuento: Number) -> float:
    """Apply a percentage discount to a given price.

    Parameters
    - precio_original: The original price before discount. Must be >= 0.
    - porcentaje_descuento: The discount percentage (e.g., 10 for 10%).
      Can be any real number; negative values will effectively increase the price,
      values greater than 100 will reduce below zero unless clamped by caller.

    Returns
    - The discounted price as a float.

    Notes
    - This function does not clamp the result; callers may add their own
      business rules (e.g., minimum price of 0.0).
    - For currency-sensitive contexts, prefer Decimal with appropriate quantize.
    """
    if precio_original < 0:
        raise ValueError("precio_original must be non-negative")

    factor = 1.0 - float(porcentaje_descuento) / 100.0
    return float(precio_original) * factor

