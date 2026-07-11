from app.core.profiles import parse_profile


def test_parse_profile_household_types():
    p = parse_profile("household_apartment_family_1269")
    assert p == {"key": "apartment_family", "segment": "hogar", "label": "Apartamento", "people": 4}

    p2 = parse_profile("household_house_family_garden_5836")
    assert p2["label"] == "Casa con jardín"
    assert p2["people"] == 4


def test_parse_profile_hotel_and_pueblo_meters():
    hotel = parse_profile("meter_hotel_1234")
    assert hotel == {"key": "hotel", "label": "Hotel / Balneario", "people": None, "segment": "hotel"}

    pueblo = parse_profile("meter_pueblo_5678")
    assert pueblo["segment"] == "pueblo"
    assert pueblo["label"] == "Pueblo / Sector DMA"


def test_parse_profile_unknown_id_falls_back_gracefully():
    p = parse_profile("hotel_piloto_costa")  # ID real de piloto, sin prefijo del simulador
    assert p["segment"] == "hogar"  # fallback seguro; no debe lanzar excepción
    assert p["label"]  # siempre hay una etiqueta legible
