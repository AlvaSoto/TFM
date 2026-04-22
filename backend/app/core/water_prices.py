#Data from INE 2022 and OCU
#Unit price which includes supplu and sanitation

"""
This is the price for 1000L=1m3 of water consumption in different regions of Spain in euros.
"""


REGIONAL_PRICES = {
    "Andalucía": 1.92,
    "Aragón": 1.84,
    "Asturias": 1.43,
    "Baleares": 2.52,
    "Canarias": 2.32,
    "Cantabria": 1.57,
    "Castilla y León": 1.24,
    "Castilla - La Mancha": 1.60,
    "Cataluña": 2.98,
    "Comunidad Valenciana": 1.94,
    "Extremadura": 1.52,
    "Galicia": 1.96,
    "Madrid": 1.80,
    "Murcia": 2.43,
    "Navarra": 1.63,
    "País Vasco": 2.51,
    "La Rioja": 1.46,
    "Ceuta y Melilla": 1.74,
    "Promedio Nacional": 1.92  # Valor por defecto
}

# Fix monthly fee (service + water meter)

FIXED_MONTHLY_FEE = 12.50  # 