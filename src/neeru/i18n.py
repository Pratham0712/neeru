"""Bot text in English and Kannada. Have a native speaker proofread the Kannada before the demo."""

TEXT = {
    "welcome": {
        "en": (
            "🌧️ Neeru: know before you ride into it.\n\n"
            "📸 Send a photo of a waterlogged road, then share your location. "
            "I'll check it and put it on the map for everyone.\n"
            "📍 Or just share your location to see flood risk near you for the next 3 hours.\n"
            "🔔 Tap “Alert me” on a spot and I'll message you before it floods.\n\n"
            "/stop turns off all alerts. /lang changes language."
        ),
        "kn": (
            "🌧️ ನೀರು: ಹೋಗುವ ಮೊದಲೇ ತಿಳಿಯಿರಿ.\n\n"
            "📸 ನೀರು ನಿಂತಿರುವ ರಸ್ತೆಯ ಫೋಟೋ ಕಳುಹಿಸಿ, ನಂತರ ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಹಂಚಿಕೊಳ್ಳಿ. "
            "ನಾನು ಅದನ್ನು ಪರಿಶೀಲಿಸಿ ಎಲ್ಲರಿಗಾಗಿ ನಕ್ಷೆಯಲ್ಲಿ ಹಾಕುತ್ತೇನೆ.\n"
            "📍 ಅಥವಾ ನಿಮ್ಮ ಸ್ಥಳವನ್ನು ಮಾತ್ರ ಹಂಚಿಕೊಳ್ಳಿ: ಮುಂದಿನ 3 ಗಂಟೆಗಳಲ್ಲಿ ನಿಮ್ಮ ಹತ್ತಿರ ನೀರು ನಿಲ್ಲುವ ಅಪಾಯ ತಿಳಿಯಿರಿ.\n"
            "🔔 ಯಾವುದೇ ಸ್ಥಳದಲ್ಲಿ “ಎಚ್ಚರಿಸಿ” ಒತ್ತಿ, ನೀರು ತುಂಬುವ ಮೊದಲೇ ನಿಮಗೆ ಸಂದೇಶ ಬರುತ್ತದೆ.\n\n"
            "/stop ಎಲ್ಲಾ ಎಚ್ಚರಿಕೆಗಳನ್ನು ನಿಲ್ಲಿಸುತ್ತದೆ. /lang ಭಾಷೆ ಬದಲಿಸುತ್ತದೆ."
        ),
    },
    "choose_lang": {
        "en": "Choose your language / ನಿಮ್ಮ ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
        "kn": "Choose your language / ನಿಮ್ಮ ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
    },
    "ask_location": {
        "en": "Got the photo 👍 Now tap the button below to share where you took it.",
        "kn": "ಫೋಟೋ ಸಿಕ್ಕಿತು 👍 ಈಗ ಕೆಳಗಿನ ಬಟನ್ ಒತ್ತಿ, ಫೋಟೋ ತೆಗೆದ ಸ್ಥಳವನ್ನು ಹಂಚಿಕೊಳ್ಳಿ.",
    },
    "share_location_button": {"en": "📍 Share location", "kn": "📍 ಸ್ಥಳ ಹಂಚಿಕೊಳ್ಳಿ"},
    "checking": {
        "en": "Checking your photo against live rainfall… ⏳",
        "kn": "ನಿಮ್ಮ ಫೋಟೋವನ್ನು ಈಗಿನ ಮಳೆಯ ಮಾಹಿತಿಯೊಂದಿಗೆ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ… ⏳",
    },
    "outside_city": {
        "en": "That location looks outside Bengaluru. Neeru covers Bengaluru for now.",
        "kn": "ಈ ಸ್ಥಳ ಬೆಂಗಳೂರಿನ ಹೊರಗಿದೆ ಎನಿಸುತ್ತದೆ. ಸದ್ಯಕ್ಕೆ ನೀರು ಬೆಂಗಳೂರಿಗೆ ಮಾತ್ರ.",
    },
    "verdict_flooded": {
        "en": "✅ Verified: water at {depth} level near {place}. It's on the map now. Thank you!",
        "kn": "✅ ದೃಢಪಟ್ಟಿದೆ: {place} ಬಳಿ {depth} ಮಟ್ಟದ ನೀರು. ಈಗ ನಕ್ಷೆಯಲ್ಲಿದೆ. ಧನ್ಯವಾದಗಳು!",
    },
    "verdict_dry": {
        "en": "✅ Checked: the road near {place} looks clear. Thanks for confirming!",
        "kn": "✅ ಪರಿಶೀಲಿಸಲಾಗಿದೆ: {place} ಬಳಿ ರಸ್ತೆ ಸರಿಯಾಗಿದೆ ಎನಿಸುತ್ತದೆ. ಖಚಿತಪಡಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು!",
    },
    "verdict_unverified": {
        "en": "🤔 I couldn't verify this photo confidently. It's saved, but it won't change the map yet.",
        "kn": "🤔 ಈ ಫೋಟೋವನ್ನು ಖಚಿತವಾಗಿ ದೃಢಪಡಿಸಲು ಆಗಲಿಲ್ಲ. ಅದನ್ನು ಉಳಿಸಲಾಗಿದೆ, ಆದರೆ ಸದ್ಯಕ್ಕೆ ನಕ್ಷೆ ಬದಲಾಗುವುದಿಲ್ಲ.",
    },
    "verdict_invalid": {
        "en": "This doesn't look like a photo of a road. Please send a clear photo of the street.",
        "kn": "ಇದು ರಸ್ತೆಯ ಫೋಟೋದಂತೆ ಕಾಣುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ರಸ್ತೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ಕಳುಹಿಸಿ.",
    },
    "new_spot": {
        "en": "📌 This is a new spot on the map. Your report put it there.",
        "kn": "📌 ಇದು ನಕ್ಷೆಯಲ್ಲಿ ಹೊಸ ಸ್ಥಳ. ನಿಮ್ಮ ವರದಿಯಿಂದ ಇದು ಸೇರಿತು.",
    },
    "nearby_header": {
        "en": "Flood risk near you, next 3 hours:",
        "kn": "ನಿಮ್ಮ ಹತ್ತಿರ, ಮುಂದಿನ 3 ಗಂಟೆಗಳ ನೀರು ನಿಲ್ಲುವ ಅಪಾಯ:",
    },
    "no_spots": {
        "en": "No known flood spots within 5 km of you.",
        "kn": "ನಿಮ್ಮಿಂದ 5 ಕಿ.ಮೀ. ಒಳಗೆ ಯಾವುದೇ ತಿಳಿದಿರುವ ನೀರು ನಿಲ್ಲುವ ಸ್ಥಳಗಳಿಲ್ಲ.",
    },
    "alert_me": {"en": "🔔 Alert me: {name}", "kn": "🔔 ಎಚ್ಚರಿಸಿ: {name}"},
    "subscribed": {
        "en": "🔔 Done. I'll message you before {name} floods.",
        "kn": "🔔 ಆಯಿತು. {name} ನಲ್ಲಿ ನೀರು ತುಂಬುವ ಮೊದಲೇ ನಿಮಗೆ ತಿಳಿಸುತ್ತೇನೆ.",
    },
    "alert_red": {
        "en": "🔴 Flood alert: {name}\n{why}\nAvoid it on a two-wheeler for the next few hours.",
        "kn": "🔴 ನೀರು ತುಂಬುವ ಎಚ್ಚರಿಕೆ: {name}\n{why}\nಮುಂದಿನ ಕೆಲವು ಗಂಟೆಗಳ ಕಾಲ ದ್ವಿಚಕ್ರ ವಾಹನದಲ್ಲಿ ಈ ದಾರಿ ತಪ್ಪಿಸಿ.",
    },
    "alert_clear": {
        "en": "🟢 {name} is clearing up.",
        "kn": "🟢 {name} ನಲ್ಲಿ ಪರಿಸ್ಥಿತಿ ಸುಧಾರಿಸುತ್ತಿದೆ.",
    },
    "why_rain": {
        "en": "{mm} mm of rain expected in the next 3 hours.",
        "kn": "ಮುಂದಿನ 3 ಗಂಟೆಗಳಲ್ಲಿ {mm} ಮಿ.ಮೀ. ಮಳೆ ನಿರೀಕ್ಷೆ.",
    },
    "why_report": {
        "en": "A citizen photo shows water at {depth} level.",
        "kn": "ನಾಗರಿಕರ ಫೋಟೋದಲ್ಲಿ {depth} ಮಟ್ಟದ ನೀರು ಕಾಣುತ್ತಿದೆ.",
    },
    "stopped": {"en": "Alerts stopped for {n} spot(s).", "kn": "{n} ಸ್ಥಳಗಳ ಎಚ್ಚರಿಕೆಗಳನ್ನು ನಿಲ್ಲಿಸಲಾಗಿದೆ."},
    "error": {
        "en": "Something went wrong on my side. Please try again in a minute.",
        "kn": "ನನ್ನ ಕಡೆಯಿಂದ ತೊಂದರೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಒಂದು ನಿಮಿಷದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    },
    "replay_note": {"en": "(storm replay demo)", "kn": "(ಮಳೆಯ ಡೆಮೊ)"},
    "your_location": {"en": "your location", "kn": "ನಿಮ್ಮ ಸ್ಥಳ"},
}

LEVEL = {
    "red": {"en": "🔴 Avoid", "kn": "🔴 ತಪ್ಪಿಸಿ"},
    "amber": {"en": "🟠 Caution", "kn": "🟠 ಎಚ್ಚರಿಕೆ"},
    "green": {"en": "🟢 Clear", "kn": "🟢 ಸರಿಯಿದೆ"},
}

DEPTH = {
    "none": {"en": "no", "kn": "ಯಾವುದೇ"},
    "ankle": {"en": "ankle", "kn": "ಪಾದದ"},
    "tyre_hub": {"en": "tyre-hub", "kn": "ಚಕ್ರದ ಮಧ್ಯಭಾಗದ"},
    "knee": {"en": "knee", "kn": "ಮೊಣಕಾಲಿನ"},
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    entry = TEXT[key]
    return entry.get(lang, entry["en"]).format(**kwargs)


def level(name: str, lang: str = "en") -> str:
    return LEVEL[name].get(lang, LEVEL[name]["en"])


def depth(name: str, lang: str = "en") -> str:
    return DEPTH.get(name, DEPTH["none"]).get(lang, name)


def place_name(hotspot: dict, lang: str = "en") -> str:
    """Hotspots carry an optional Kannada name in name_kn."""
    if lang == "kn" and hotspot.get("name_kn"):
        return hotspot["name_kn"]
    return hotspot["name"]
