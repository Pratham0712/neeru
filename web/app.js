// Neeru web app: map for riders, photo reports, dispatch list for engineers.
// Plain JavaScript, no build step. Talks to the API at window.NEERU_API.

const API = (window.NEERU_API || "").replace(/\/$/, "");
const BOT = window.NEERU_BOT || "";
const REFRESH_MS = 60_000;

// ---------------------------------------------------------------- text
const TEXT = {
  en: {
    tagline: "Know before you ride into it.",
    replay: "Storm replay demo: rainfall below is simulated.",
    nearYou: "Next 3 hours",
    nearYouLocated: "Near you · next 3 hours",
    tabMap: "Map", tabReport: "Report", tabOps: "Ops",
    reportTitle: "Report waterlogging",
    reportHelp: "One photo helps every rider behind you. An AI agent checks it against live rainfall before it goes on the map.",
    takePhoto: "Take a photo of the road",
    useLocation: "Use my location",
    locating: "Finding you…",
    located: (lat, lon) => `Location set (${lat.toFixed(4)}, ${lon.toFixed(4)})`,
    locationFailed: "Couldn't get your location. Allow location access and try again.",
    send: "Send report",
    step1: "Looking at your photo", step2: "Checking live rainfall here", step3: "Comparing with nearby reports",
    opsTitle: "Dispatch priority",
    opsHelp: "For ward engineers and traffic police: where to send pumps and staff first. Ranked by risk × road importance × verified citizen reports.",
    red: "Avoid", amber: "Caution", green: "Clear",
    avoidCount: "avoid", cautionCount: "caution", clearCount: "clear",
    tilesRed: "red now", tilesAmber: "amber", tilesReports: "verified photos (2 h)", tilesCitizen: "citizen-found spots",
    noRain: "No significant rain",
    rainNext: (mm) => `${mm} mm rain in the next 3 h`,
    rainPast: (mm) => `${mm} mm fell in the last 3 h`,
    photoSays: (d) => `Citizen photo: water at ${d} level`,
    depth: { none: "no", ankle: "ankle", tyre_hub: "tyre-hub", knee: "knee" },
    km: (d) => `${d.toFixed(1)} km`,
    updated: (m) => (m < 1 ? "Updated just now" : `Updated ${m} min ago`),
    thresholdNote: (mm) => `Floods at about ${mm} mm of rain load. This number learns from citizen photos.`,
    rainChart: "Rain, mm per hour (3 h past → 3 h ahead)",
    recentPhotos: "Citizen photos (last 6 h)",
    noPhotos: "No photos yet. Be the first to report.",
    verified: "verified", unverified: "unverified",
    alertsTelegram: "🔔 Get alerts for this spot on Telegram",
    vFlooded: (d, p) => `Water at ${d} level near ${p}`,
    vDry: (p) => `Road near ${p} looks clear`,
    vUnverified: "Saved, but not confident enough to change the map yet",
    vInvalid: "That doesn't look like a road. Try a clear street photo.",
    vOutside: "Neeru covers Bengaluru only for now.",
    vError: "Something went wrong. Please try again.",
    newSpot: "📌 New spot! Your report put it on the map.",
    agentUsed: "Agent steps",
    viewMap: "View on map",
    yourLocation: "your location",
    noDispatch: "Nothing to dispatch right now. All spots are clear.",
    noApi: "API URL not set. Run scripts/build_web.py.",
    verifiedReports: (n) => `${n} verified photo${n === 1 ? "" : "s"}`,
    kinds: { underpass: "Underpass", junction: "Junction", road: "Road", citizen: "Citizen-found" },
    routeCta: "Safe route: is my ride flooded?",
    routeTitle: "Safe route",
    cancel: "Cancel",
    fromMe: "📍 Start from my location",
    tapStart: "Tap your starting point on the map.",
    tapEnd: "Now tap where you're going.",
    routing: "Checking routes against live flood risk…",
    routeFailed: "Couldn't get routes right now. Try again in a minute.",
    vClear: "Your fastest route is clear",
    vClearSub: "No amber or red spots on the way.",
    vDetour: "Take the safer route",
    vDetourSub: (min, names) => `+${min} min, but it avoids ${names}.`,
    vCaution: "Ride with caution",
    vCautionSub: "The best route still passes amber spots. Go slow at the dips.",
    vNoSafe: "Every route passes a flooded spot",
    vNoSafeSub: "If you can, wait it out or take public transport.",
    routeOption: (i) => `Route ${i + 1}`,
    fastest: "fastest", recommended: "recommended",
    passes: (n) => (n ? `passes ${n} risky spot${n === 1 ? "" : "s"}` : "no risky spots"),
    copilot: "Ops Copilot",
    getBriefing: "Get dispatch briefing",
    briefingLoading: "Ops Copilot is reading the dispatch list and citizen reports…",
    briefingFailed: "Briefing unavailable right now.",
    priorityList: "Priority list",
    generatedAt: (m, cached) => `${m < 1 ? "Just now" : `${m} min ago`}${cached ? " · cached" : ""}`,
    actions: { deploy_pump: "Pump", divert_traffic: "Divert", close_underpass: "Close", clear_drain: "Clear drain", monitor: "Monitor" },
  },
  kn: {
    tagline: "ಹೋಗುವ ಮೊದಲೇ ತಿಳಿಯಿರಿ.",
    replay: "ಮಳೆಯ ಡೆಮೊ: ಇಲ್ಲಿನ ಮಳೆ ಮಾಹಿತಿ ಅನುಕರಿಸಲಾಗಿದೆ.",
    nearYou: "ಮುಂದಿನ 3 ಗಂಟೆಗಳು",
    nearYouLocated: "ನಿಮ್ಮ ಹತ್ತಿರ · ಮುಂದಿನ 3 ಗಂಟೆಗಳು",
    tabMap: "ನಕ್ಷೆ", tabReport: "ವರದಿ", tabOps: "ಕಾರ್ಯಾಚರಣೆ",
    reportTitle: "ನೀರು ನಿಂತಿರುವುದನ್ನು ವರದಿ ಮಾಡಿ",
    reportHelp: "ನಿಮ್ಮ ಒಂದು ಫೋಟೋ ನಿಮ್ಮ ಹಿಂದೆ ಬರುವ ಎಲ್ಲಾ ಸವಾರರಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತದೆ. ನಕ್ಷೆಗೆ ಸೇರಿಸುವ ಮೊದಲು AI ಏಜೆಂಟ್ ಅದನ್ನು ಈಗಿನ ಮಳೆಯೊಂದಿಗೆ ಪರಿಶೀಲಿಸುತ್ತದೆ.",
    takePhoto: "ರಸ್ತೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ",
    useLocation: "ನನ್ನ ಸ್ಥಳ ಬಳಸಿ",
    locating: "ನಿಮ್ಮ ಸ್ಥಳ ಹುಡುಕುತ್ತಿದ್ದೇನೆ…",
    located: (lat, lon) => `ಸ್ಥಳ ಸಿಕ್ಕಿದೆ (${lat.toFixed(4)}, ${lon.toFixed(4)})`,
    locationFailed: "ನಿಮ್ಮ ಸ್ಥಳ ಸಿಗಲಿಲ್ಲ. ಸ್ಥಳ ಅನುಮತಿ ನೀಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    send: "ವರದಿ ಕಳುಹಿಸಿ",
    step1: "ನಿಮ್ಮ ಫೋಟೋ ನೋಡುತ್ತಿದ್ದೇನೆ", step2: "ಇಲ್ಲಿನ ಈಗಿನ ಮಳೆ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ", step3: "ಹತ್ತಿರದ ವರದಿಗಳೊಂದಿಗೆ ಹೋಲಿಸುತ್ತಿದ್ದೇನೆ",
    opsTitle: "ಕಾರ್ಯಾಚರಣೆಯ ಆದ್ಯತೆ",
    opsHelp: "ವಾರ್ಡ್ ಎಂಜಿನಿಯರ್‌ಗಳು ಮತ್ತು ಸಂಚಾರ ಪೊಲೀಸರಿಗಾಗಿ: ಪಂಪ್‌ಗಳು ಮತ್ತು ಸಿಬ್ಬಂದಿಯನ್ನು ಮೊದಲು ಎಲ್ಲಿಗೆ ಕಳುಹಿಸಬೇಕು.",
    red: "ತಪ್ಪಿಸಿ", amber: "ಎಚ್ಚರಿಕೆ", green: "ಸರಿಯಿದೆ",
    avoidCount: "ತಪ್ಪಿಸಿ", cautionCount: "ಎಚ್ಚರಿಕೆ", clearCount: "ಸರಿಯಿದೆ",
    tilesRed: "ಕೆಂಪು", tilesAmber: "ಹಳದಿ", tilesReports: "ದೃಢಪಟ್ಟ ಫೋಟೋಗಳು (2 ಗಂ)", tilesCitizen: "ನಾಗರಿಕರು ಕಂಡ ಸ್ಥಳಗಳು",
    noRain: "ಗಮನಾರ್ಹ ಮಳೆ ಇಲ್ಲ",
    rainNext: (mm) => `ಮುಂದಿನ 3 ಗಂಟೆಗಳಲ್ಲಿ ${mm} ಮಿ.ಮೀ. ಮಳೆ`,
    rainPast: (mm) => `ಕಳೆದ 3 ಗಂಟೆಗಳಲ್ಲಿ ${mm} ಮಿ.ಮೀ. ಮಳೆ`,
    photoSays: (d) => `ನಾಗರಿಕರ ಫೋಟೋ: ${d} ಮಟ್ಟದ ನೀರು`,
    depth: { none: "ಯಾವುದೇ", ankle: "ಪಾದದ", tyre_hub: "ಚಕ್ರದ ಮಧ್ಯಭಾಗದ", knee: "ಮೊಣಕಾಲಿನ" },
    km: (d) => `${d.toFixed(1)} ಕಿ.ಮೀ.`,
    updated: (m) => (m < 1 ? "ಈಗಷ್ಟೇ ನವೀಕರಿಸಲಾಗಿದೆ" : `${m} ನಿಮಿಷಗಳ ಹಿಂದೆ ನವೀಕರಿಸಲಾಗಿದೆ`),
    thresholdNote: (mm) => `ಸುಮಾರು ${mm} ಮಿ.ಮೀ. ಮಳೆಯಲ್ಲಿ ಇಲ್ಲಿ ನೀರು ತುಂಬುತ್ತದೆ. ಈ ಸಂಖ್ಯೆ ನಾಗರಿಕರ ಫೋಟೋಗಳಿಂದ ಕಲಿಯುತ್ತದೆ.`,
    rainChart: "ಮಳೆ, ಗಂಟೆಗೆ ಮಿ.ಮೀ. (ಹಿಂದಿನ 3 ಗಂ → ಮುಂದಿನ 3 ಗಂ)",
    recentPhotos: "ನಾಗರಿಕರ ಫೋಟೋಗಳು (ಕಳೆದ 6 ಗಂ)",
    noPhotos: "ಇನ್ನೂ ಫೋಟೋಗಳಿಲ್ಲ. ಮೊದಲು ವರದಿ ಮಾಡಿ.",
    verified: "ದೃಢಪಟ್ಟಿದೆ", unverified: "ದೃಢಪಟ್ಟಿಲ್ಲ",
    alertsTelegram: "🔔 ಈ ಸ್ಥಳದ ಎಚ್ಚರಿಕೆಗಳನ್ನು ಟೆಲಿಗ್ರಾಮ್‌ನಲ್ಲಿ ಪಡೆಯಿರಿ",
    vFlooded: (d, p) => `${p} ಬಳಿ ${d} ಮಟ್ಟದ ನೀರು`,
    vDry: (p) => `${p} ಬಳಿ ರಸ್ತೆ ಸರಿಯಾಗಿದೆ`,
    vUnverified: "ಉಳಿಸಲಾಗಿದೆ, ಆದರೆ ನಕ್ಷೆ ಬದಲಿಸುವಷ್ಟು ಖಚಿತತೆ ಇಲ್ಲ",
    vInvalid: "ಇದು ರಸ್ತೆಯಂತೆ ಕಾಣುತ್ತಿಲ್ಲ. ರಸ್ತೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ಕಳುಹಿಸಿ.",
    vOutside: "ಸದ್ಯಕ್ಕೆ ನೀರು ಬೆಂಗಳೂರಿಗೆ ಮಾತ್ರ.",
    vError: "ತೊಂದರೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    newSpot: "📌 ಹೊಸ ಸ್ಥಳ! ನಿಮ್ಮ ವರದಿಯಿಂದ ಇದು ನಕ್ಷೆಗೆ ಸೇರಿತು.",
    agentUsed: "ಏಜೆಂಟ್ ಹಂತಗಳು",
    viewMap: "ನಕ್ಷೆಯಲ್ಲಿ ನೋಡಿ",
    yourLocation: "ನಿಮ್ಮ ಸ್ಥಳ",
    noDispatch: "ಸದ್ಯಕ್ಕೆ ಯಾವುದೇ ಕಾರ್ಯಾಚರಣೆ ಬೇಕಿಲ್ಲ. ಎಲ್ಲಾ ಸ್ಥಳಗಳು ಸರಿಯಾಗಿವೆ.",
    noApi: "API URL ಹೊಂದಿಸಿಲ್ಲ.",
    verifiedReports: (n) => `${n} ದೃಢಪಟ್ಟ ಫೋಟೋ`,
    kinds: { underpass: "ಅಂಡರ್‌ಪಾಸ್", junction: "ಜಂಕ್ಷನ್", road: "ರಸ್ತೆ", citizen: "ನಾಗರಿಕರು ಕಂಡದ್ದು" },
    routeCta: "ಸುರಕ್ಷಿತ ದಾರಿ: ನನ್ನ ದಾರಿಯಲ್ಲಿ ನೀರಿದೆಯೇ?",
    routeTitle: "ಸುರಕ್ಷಿತ ದಾರಿ",
    cancel: "ರದ್ದುಮಾಡಿ",
    fromMe: "📍 ನನ್ನ ಸ್ಥಳದಿಂದ ಪ್ರಾರಂಭಿಸಿ",
    tapStart: "ನಕ್ಷೆಯಲ್ಲಿ ನಿಮ್ಮ ಪ್ರಾರಂಭದ ಸ್ಥಳವನ್ನು ಒತ್ತಿ.",
    tapEnd: "ಈಗ ನೀವು ಹೋಗುವ ಸ್ಥಳವನ್ನು ಒತ್ತಿ.",
    routing: "ದಾರಿಗಳನ್ನು ಈಗಿನ ನೀರಿನ ಅಪಾಯದೊಂದಿಗೆ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದೇನೆ…",
    routeFailed: "ಸದ್ಯಕ್ಕೆ ದಾರಿ ಸಿಗಲಿಲ್ಲ. ಒಂದು ನಿಮಿಷದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.",
    vClear: "ನಿಮ್ಮ ವೇಗದ ದಾರಿ ಸುರಕ್ಷಿತವಾಗಿದೆ",
    vClearSub: "ದಾರಿಯಲ್ಲಿ ಯಾವುದೇ ಅಪಾಯದ ಸ್ಥಳಗಳಿಲ್ಲ.",
    vDetour: "ಸುರಕ್ಷಿತ ದಾರಿಯಲ್ಲಿ ಹೋಗಿ",
    vDetourSub: (min, names) => `+${min} ನಿಮಿಷ, ಆದರೆ ${names} ತಪ್ಪಿಸುತ್ತದೆ.`,
    vCaution: "ಎಚ್ಚರಿಕೆಯಿಂದ ಹೋಗಿ",
    vCautionSub: "ಉತ್ತಮ ದಾರಿಯಲ್ಲೂ ಹಳದಿ ಸ್ಥಳಗಳಿವೆ. ತಗ್ಗುಗಳಲ್ಲಿ ನಿಧಾನವಾಗಿ ಹೋಗಿ.",
    vNoSafe: "ಎಲ್ಲಾ ದಾರಿಗಳಲ್ಲೂ ನೀರು ನಿಂತ ಸ್ಥಳವಿದೆ",
    vNoSafeSub: "ಸಾಧ್ಯವಾದರೆ ಕಾಯಿರಿ ಅಥವಾ ಸಾರ್ವಜನಿಕ ಸಾರಿಗೆ ಬಳಸಿ.",
    routeOption: (i) => `ದಾರಿ ${i + 1}`,
    fastest: "ವೇಗದ್ದು", recommended: "ಶಿಫಾರಸು",
    passes: (n) => (n ? `${n} ಅಪಾಯದ ಸ್ಥಳ` : "ಅಪಾಯದ ಸ್ಥಳಗಳಿಲ್ಲ"),
    copilot: "ಕಾರ್ಯಾಚರಣೆ ಸಹಾಯಕ",
    getBriefing: "ಕಾರ್ಯಾಚರಣೆ ವರದಿ ಪಡೆಯಿರಿ",
    briefingLoading: "ಸಹಾಯಕ ಪಟ್ಟಿ ಮತ್ತು ನಾಗರಿಕರ ವರದಿಗಳನ್ನು ಓದುತ್ತಿದೆ…",
    briefingFailed: "ಸದ್ಯಕ್ಕೆ ವರದಿ ಲಭ್ಯವಿಲ್ಲ.",
    priorityList: "ಆದ್ಯತೆಯ ಪಟ್ಟಿ",
    generatedAt: (m, cached) => `${m < 1 ? "ಈಗಷ್ಟೇ" : `${m} ನಿಮಿಷಗಳ ಹಿಂದೆ`}${cached ? " · ಉಳಿಸಿದ್ದು" : ""}`,
    actions: { deploy_pump: "ಪಂಪ್", divert_traffic: "ತಿರುಗಿಸಿ", close_underpass: "ಮುಚ್ಚಿ", clear_drain: "ಚರಂಡಿ", monitor: "ಗಮನಿಸಿ" },
  },
};

const state = {
  lang: localGet("neeru-lang") || "en",
  hotspots: [],
  replay: null,
  generatedAt: null,
  me: null,           // {lat, lon} once the user shares location
  photo: null,        // base64 data URL, resized
  reportPos: null,
  map: null,
  markers: {},
  route: { mode: null, from: null, to: null, layers: [], result: null },
};

function t(key, ...args) {
  const entry = TEXT[state.lang][key] ?? TEXT.en[key];
  return typeof entry === "function" ? entry(...args) : entry;
}

function localGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
function localSet(key, value) { try { localStorage.setItem(key, value); } catch { /* private mode */ } }

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function placeName(h) { return state.lang === "kn" && h.name_kn ? h.name_kn : h.name; }

function distanceKm(a, b) {
  const R = 6371, rad = (x) => (x * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat), dLon = rad(b.lon - a.lon);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

// Explain a hotspot's risk from the numbers, in the current language.
function why(h) {
  const risk = h.risk || {};
  const parts = [];
  if (risk.report_depth) parts.push(t("photoSays", t("depth")[risk.report_depth]));
  if ((risk.next_mm || 0) >= 1) parts.push(t("rainNext", Math.round(risk.next_mm)));
  if ((risk.past_mm || 0) >= 1) parts.push(t("rainPast", Math.round(risk.past_mm)));
  return parts.length ? parts.join(" · ") : t("noRain");
}

async function api(path, options = {}) {
  if (!API) throw new Error(t("noApi"));
  const response = await fetch(API + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok && response.status !== 422) throw new Error(body.error || response.statusText);
  return { status: response.status, body };
}

// ---------------------------------------------------------------- language + tabs
function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.body.classList.toggle("kn", state.lang === "kn");
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.lang));
  renderAll();
}

document.querySelectorAll(".lang button").forEach((button) =>
  button.addEventListener("click", () => {
    state.lang = button.dataset.lang;
    localSet("neeru-lang", state.lang);
    applyLanguage();
  })
);

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  if (name === "map" && state.map) setTimeout(() => state.map.invalidateSize(), 50);
  if (name === "ops") loadOps();
}
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));

// ---------------------------------------------------------------- map
function initMap() {
  state.map = L.map("map", { zoomControl: false }).setView([12.955, 77.64], 12);
  L.control.zoom({ position: "topright" }).addTo(state.map);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · Rain: <a href="https://open-meteo.com">Open-Meteo</a> · Routes: <a href="https://project-osrm.org">OSRM</a>',
  }).addTo(state.map);

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        state.me = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        L.circleMarker([state.me.lat, state.me.lon], { radius: 7, color: "#fff", weight: 3, fillColor: "#1f6fb2", fillOpacity: 1 }).addTo(state.map);
        renderList();
      },
      () => {},
      { timeout: 8000 }
    );
  }
}

function renderMarkers() {
  for (const h of state.hotspots) {
    const level = h.risk?.level || "green";
    const icon = L.divIcon({
      className: "",
      html: `<div class="pulse ${level} ${h.kind === "citizen" ? "citizen" : ""}"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9],
    });
    if (state.markers[h.id]) {
      state.markers[h.id].setIcon(icon);
    } else {
      state.markers[h.id] = L.marker([h.lat, h.lon], { icon, title: h.name }).addTo(state.map).on("click", () => openDetail(h.id));
    }
    state.markers[h.id].bindTooltip(`${esc(placeName(h))} · ${t(level)}`);
  }
}

function renderSummary() {
  const count = { red: 0, amber: 0, green: 0 };
  state.hotspots.forEach((h) => { count[h.risk?.level || "green"]++; });
  document.getElementById("summary").innerHTML = `
    <div class="pill red"><b>${count.red}</b>${t("avoidCount")}</div>
    <div class="pill amber"><b>${count.amber}</b>${t("cautionCount")}</div>
    <div class="pill green"><b>${count.green}</b>${t("clearCount")}</div>`;
}

function renderList() {
  const rows = state.hotspots.map((h) => ({ h, d: state.me ? distanceKm(state.me, h) : null }));
  rows.sort(state.me ? (a, b) => a.d - b.d : (a, b) => (b.h.risk?.score || 0) - (a.h.risk?.score || 0));
  document.querySelector(".sheet-title").textContent = state.me ? t("nearYouLocated") : t("nearYou");

  document.getElementById("spot-list").innerHTML = rows.slice(0, 8).map(({ h, d }) => {
    const level = h.risk?.level || "green";
    const distance = d === null ? "" : ` · ${t("km", d)}`;
    return `<li class="spot" data-id="${esc(h.id)}">
      <span class="dot ${level}"></span>
      <span class="spot-name">${esc(placeName(h))}</span>
      <span class="chip ${level}">${t(level)}</span>
      <span class="spot-why">${esc(why(h))}${distance}</span>
    </li>`;
  }).join("");
  document.querySelectorAll(".spot").forEach((li) => li.addEventListener("click", () => openDetail(li.dataset.id)));

  if (state.generatedAt) {
    const newest = Math.max(...state.hotspots.map((h) => Date.parse(h.updated_at || 0) || 0));
    const minutes = newest ? Math.round((Date.now() - newest) / 60000) : 0;
    document.getElementById("updated").textContent = t("updated", minutes);
  }
}

function renderAll() {
  document.getElementById("replay-banner").hidden = !state.replay;
  if (state.route.result) renderRouteResult();
  if (!state.map) return;
  renderMarkers();
  renderSummary();
  renderList();
}

async function loadHotspots() {
  try {
    const { body } = await api("/hotspots");
    state.hotspots = body.hotspots;
    state.replay = body.storm_replay;
    state.generatedAt = body.generated_at;
    renderAll();
  } catch (err) {
    document.getElementById("spot-list").innerHTML = `<li class="empty">${esc(err.message)}</li>`;
  }
}

// ---------------------------------------------------------------- detail sheet
function rainBars(h) {
  const past = h.rain_past || [], next = h.rain_next || [];
  const all = [...past, ...next];
  const max = Math.max(5, ...all);
  const labels = ["-3h", "-2h", "-1h", "now", "+1h", "+2h"];
  return `<div class="rainbars">${all.map((mm, i) =>
    `<div class="${i >= past.length ? "future" : ""}" style="height:${Math.max(2, (mm / max) * 100)}%" title="${mm} mm"><span>${labels[i] || ""}</span></div>`
  ).join("")}</div>`;
}

async function openDetail(id) {
  const panel = document.getElementById("detail");
  const body = document.getElementById("detail-body");
  panel.hidden = false;
  body.innerHTML = "…";
  try {
    const { body: data } = await api(`/hotspots/${encodeURIComponent(id)}`);
    const h = data.hotspot, level = h.risk?.level || "green";
    const photos = data.reports.length
      ? `<div class="photos">${data.reports.map((r) => `
          <figure><img src="${esc(r.photo_url)}" alt="" loading="lazy">
          <figcaption>${r.verified ? "✓ " + t("verified") : t("unverified")} · ${esc(t("depth")[r.depth] || "")}</figcaption></figure>`).join("")}</div>`
      : `<p class="muted">${t("noPhotos")}</p>`;
    const telegram = BOT ? `<a class="telegram-cta" href="https://t.me/${encodeURIComponent(BOT)}" target="_blank" rel="noopener">${t("alertsTelegram")}</a>` : "";
    body.innerHTML = `
      <span class="chip ${level}">${t(level)}</span>
      <h1>${esc(placeName(h))}</h1>
      <p class="muted">${esc(t("kinds")[h.kind] || h.kind || "")} · ${esc(why(h))}</p>
      <h3 class="sheet-title">${t("rainChart")}</h3>
      ${rainBars(h)}
      <p class="small muted">${t("thresholdNote", Math.round(h.threshold_mm || 0))}</p>
      <h3 class="sheet-title">${t("recentPhotos")}</h3>
      ${photos}
      ${telegram}`;
  } catch (err) {
    body.textContent = err.message;
  }
}
document.getElementById("detail-close").addEventListener("click", () => { document.getElementById("detail").hidden = true; });
document.getElementById("detail").addEventListener("click", (e) => { if (e.target.id === "detail") e.currentTarget.hidden = true; });

// ---------------------------------------------------------------- report
function resizeImage(file, maxSide = 1280) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * scale);
      canvas.height = Math.round(img.height * scale);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(img.src);
      resolve(canvas.toDataURL("image/jpeg", 0.82));
    };
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}

function updateSubmit() {
  document.getElementById("submit").disabled = !(state.photo && state.reportPos);
}

document.getElementById("photo").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  state.photo = await resizeImage(file);
  const preview = document.getElementById("preview");
  preview.src = state.photo;
  preview.hidden = false;
  document.getElementById("camera-cta").hidden = true;
  document.getElementById("verdict").hidden = true;
  if (!state.reportPos) document.getElementById("locate").click();
  updateSubmit();
});

document.getElementById("locate").addEventListener("click", () => {
  const status = document.getElementById("loc-status");
  status.textContent = t("locating");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.reportPos = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      status.textContent = t("located", state.reportPos.lat, state.reportPos.lon);
      updateSubmit();
    },
    () => { status.textContent = t("locationFailed"); },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

function animateSteps() {
  const steps = [...document.querySelectorAll(".checking li")];
  let i = 0;
  const tick = () => {
    steps.forEach((li, j) => { li.className = j < i ? "done" : j === i ? "active" : ""; });
    if (i < steps.length - 1) i++;
  };
  tick();
  const timer = setInterval(tick, 2500);
  return () => { clearInterval(timer); steps.forEach((li) => { li.className = "done"; }); };
}

function depthGauge(depth) {
  const order = ["none", "ankle", "tyre_hub", "knee"];
  const reached = order.indexOf(depth);
  return `<div class="gauge">${order.slice(1).map((d, i) =>
    `<div class="${i + 1 <= reached ? "on" : ""}" style="height:${(i + 1) * 33}%"><span>${t("depth")[d]}</span></div>`
  ).join("")}</div>`;
}

function renderVerdict(status, result) {
  const box = document.getElementById("verdict");
  box.hidden = false;
  if (status === 422 || result.status === "outside_city") { box.innerHTML = `<h2>${t("vOutside")}</h2>`; return; }

  const v = result.verdict, h = result.hotspot;
  const place = h ? placeName(h) : t("yourLocation");
  let headline;
  if (!v.is_valid_photo) headline = `🚫 ${t("vInvalid")}`;
  else if (!v.verified) headline = `🤔 ${t("vUnverified")}`;
  else if (v.is_waterlogging) headline = `✅ ${t("vFlooded", t("depth")[v.depth], place)}`;
  else headline = `✅ ${t("vDry", place)}`;

  const trace = (v.tools_used || []).map((name) => `<span>→ ${esc(name)}()</span>`).join("");
  box.innerHTML = `
    <h2>${esc(headline)}</h2>
    ${v.verified && v.is_waterlogging ? depthGauge(v.depth) : ""}
    ${v.rider_advice ? `<p class="advice">${esc(v.rider_advice)}</p>` : ""}
    ${result.new_spot ? `<p><b>${t("newSpot")}</b></p>` : ""}
    ${trace ? `<p class="small muted">${t("agentUsed")}</p><div class="trace">${trace}</div>` : ""}
    ${h ? `<button class="secondary" id="see-on-map">${t("viewMap")}</button>` : ""}`;
  const seeOnMap = document.getElementById("see-on-map");
  if (seeOnMap) seeOnMap.addEventListener("click", async () => {
    await loadHotspots();
    showView("map");
    state.map.setView([h.lat, h.lon], 15);
    openDetail(h.id);
  });
}

document.getElementById("submit").addEventListener("click", async () => {
  const submit = document.getElementById("submit");
  submit.disabled = true;
  document.getElementById("verdict").hidden = true;
  document.getElementById("checking").hidden = false;
  const stop = animateSteps();
  try {
    const { status, body } = await api("/reports", {
      method: "POST",
      body: JSON.stringify({ ...state.reportPos, image_base64: state.photo, lang: state.lang }),
    });
    stop();
    renderVerdict(status, body);
    loadHotspots();
  } catch (err) {
    stop();
    document.getElementById("verdict").hidden = false;
    document.getElementById("verdict").innerHTML = `<h2>${t("vError")}</h2><p class="muted small">${esc(err.message)}</p>`;
  } finally {
    document.getElementById("checking").hidden = true;
    submit.disabled = false;
  }
});

// ---------------------------------------------------------------- ops
async function loadOps() {
  try {
    const [{ body: pri }, { body: all }] = await Promise.all([api("/priority"), api("/hotspots")]);
    const spots = all.hotspots;
    const red = spots.filter((h) => h.risk?.level === "red").length;
    const amber = spots.filter((h) => h.risk?.level === "amber").length;
    const reports = spots.reduce((n, h) => n + (h.verified_reports_recent || 0), 0);
    const citizen = spots.filter((h) => h.kind === "citizen").length;
    document.getElementById("tiles").innerHTML = `
      <div class="tile"><b style="color:var(--red)">${red}</b><span>${t("tilesRed")}</span></div>
      <div class="tile"><b style="color:var(--amber)">${amber}</b><span>${t("tilesAmber")}</span></div>
      <div class="tile"><b>${reports}</b><span>${t("tilesReports")}</span></div>
      <div class="tile"><b>${citizen}</b><span>${t("tilesCitizen")}</span></div>`;

    document.getElementById("dispatch").innerHTML = pri.dispatch.length
      ? pri.dispatch.map((h) => `
        <li class="${h.risk.level}" data-id="${esc(h.id)}">
          <span><b>${esc(placeName(h))}</b></span>
          <span class="score">${(h.priority || 0).toFixed(1)}</span>
          <span class="meta">${esc(t("kinds")[h.kind] || h.kind)} · ${esc(why(h))}${h.verified_reports_recent ? " · " + t("verifiedReports", h.verified_reports_recent) : ""}</span>
        </li>`).join("")
      : `<li class="empty" style="display:block;box-shadow:none;background:none">${t("noDispatch")}</li>`;
    document.querySelectorAll(".dispatch li[data-id]").forEach((li) => li.addEventListener("click", () => openDetail(li.dataset.id)));
  } catch (err) {
    document.getElementById("dispatch").innerHTML = `<li class="empty">${esc(err.message)}</li>`;
  }
}


// ---------------------------------------------------------------- safe route
const ROUTE_COLORS = ["#1f6fb2", "#8a9aa6", "#b0bcc5"];

function pinIcon(letter) {
  return L.divIcon({ className: "", html: `<div class="pin ${letter.toLowerCase()}"><span>${letter}</span></div>`, iconSize: [26, 26], iconAnchor: [13, 26] });
}

function clearRouteLayers() {
  state.route.layers.forEach((layer) => state.map.removeLayer(layer));
  state.route.layers = [];
}

function setRouteStep(text) { document.getElementById("route-step").textContent = text; }

function startRoute() {
  clearRouteLayers();
  Object.assign(state.route, { mode: "from", from: null, to: null, result: null });
  document.getElementById("route-start").hidden = true;
  document.getElementById("route-panel").hidden = false;
  document.getElementById("sheet-default").hidden = true;
  document.getElementById("route-from-me").hidden = !state.me;
  document.getElementById("route-result").innerHTML = "";
  setRouteStep(t("tapStart"));
}

function cancelRoute() {
  clearRouteLayers();
  Object.assign(state.route, { mode: null, from: null, to: null, result: null });
  document.getElementById("route-start").hidden = false;
  document.getElementById("route-panel").hidden = true;
  document.getElementById("sheet-default").hidden = false;
}

function setPoint(which, latlng) {
  state.route[which] = { lat: latlng.lat, lon: latlng.lng };
  const marker = L.marker(latlng, { icon: pinIcon(which === "from" ? "A" : "B"), zIndexOffset: 1000 }).addTo(state.map);
  state.route.layers.push(marker);
  if (which === "from") {
    state.route.mode = "to";
    document.getElementById("route-from-me").hidden = true;
    setRouteStep(t("tapEnd"));
  } else {
    state.route.mode = null;
    checkRoute();
  }
}

async function checkRoute() {
  const { from, to } = state.route;
  setRouteStep(t("routing"));
  try {
    const query = `from=${from.lat.toFixed(5)},${from.lon.toFixed(5)}&to=${to.lat.toFixed(5)},${to.lon.toFixed(5)}`;
    const { body } = await api(`/route?${query}`);
    if (!body.routes || !body.routes.length) throw new Error(body.error || t("routeFailed"));
    state.route.result = body;
    drawRoutes(body);
    renderRouteResult();
    setRouteStep("");
  } catch (err) {
    setRouteStep(`${t("routeFailed")} (${err.message})`);
  }
}

function drawRoutes(result) {
  // other routes first (grey, underneath), recommended last (blue, on top)
  const order = result.routes.map((r) => r.index).sort((a, b) => (a === result.recommended) - (b === result.recommended));
  const bounds = [];
  order.forEach((index, drawn) => {
    const r = result.routes[index];
    const latlngs = r.geometry.map(([lon, lat]) => [lat, lon]);
    latlngs.forEach((p) => bounds.push(p));
    const best = index === result.recommended;
    const line = L.polyline(latlngs, {
      color: best ? ROUTE_COLORS[0] : ROUTE_COLORS[Math.min(drawn + 1, 2)],
      weight: best ? 7 : 5, opacity: best ? 0.95 : 0.7, dashArray: best ? null : "8 8",
    }).addTo(state.map).on("click", () => highlightRoute(index));
    state.route.layers.push(line);
  });
  // ring the spots the fastest route would have taken you through
  result.avoided.forEach((p) => {
    const ring = L.circleMarker([p.lat, p.lon], { radius: 16, color: "#d33b32", weight: 3, fill: false, dashArray: "4 4" }).addTo(state.map);
    state.route.layers.push(ring);
  });
  state.map.fitBounds(bounds, { padding: [40, 40] });
}

function highlightRoute(index) {
  const route = state.route.result.routes[index];
  state.map.fitBounds(route.geometry.map(([lon, lat]) => [lat, lon]), { padding: [40, 40] });
}

function renderRouteResult() {
  const r = state.route.result;
  const names = r.avoided.map((p) => placeName(p)).join(", ");
  const verdicts = {
    clear: ["good", "✅ " + t("vClear"), t("vClearSub")],
    detour_clear: ["good", "🧭 " + t("vDetour"), t("vDetourSub", r.extra_min, names || "—")],
    caution: ["warn", "🟠 " + t("vCaution"), t("vCautionSub")],
    no_safe_route: ["bad", "🔴 " + t("vNoSafe"), t("vNoSafeSub")],
  };
  const [tone, title, sub] = verdicts[r.verdict] || verdicts.caution;
  const options = r.routes.map((route) => {
    const tags = [route.index === r.recommended ? t("recommended") : "", route.is_fastest ? t("fastest") : ""].filter(Boolean).join(" · ");
    const risky = route.passes.filter((p) => p.level !== "green");
    const where = risky.slice(0, 2).map((p) => placeName(p)).join(", ");
    const color = route.index === r.recommended ? ROUTE_COLORS[0] : ROUTE_COLORS[1];
    return `<div class="route-option ${route.index === r.recommended ? "best" : ""}" data-index="${route.index}">
      <span class="swatch" style="background:${color}"></span>
      <span><b>${route.duration_min.toFixed(0)} min</b> · ${route.distance_km.toFixed(1)} km</span>
      <span class="tag">${esc(tags || t("routeOption", route.index))}</span>
      <span class="meta">${route.red ? "🔴 " : route.amber ? "🟠 " : "🟢 "}${esc(t("passes", risky.length))}${where ? ": " + esc(where) : ""}</span>
    </div>`;
  }).join("");
  document.getElementById("route-result").innerHTML = `
    <div class="route-verdict ${tone}"><h3>${esc(title)}</h3><p>${esc(sub)}</p></div>
    ${options}
    ${r.storm_replay ? `<p class="small muted">${t("replay")}</p>` : ""}`;
  document.querySelectorAll(".route-option").forEach((el) => el.addEventListener("click", () => highlightRoute(Number(el.dataset.index))));
}

document.getElementById("route-start").addEventListener("click", startRoute);
document.getElementById("route-cancel").addEventListener("click", cancelRoute);
document.getElementById("route-from-me").addEventListener("click", () => {
  if (state.me) setPoint("from", { lat: state.me.lat, lng: state.me.lon });
});

// ---------------------------------------------------------------- ops copilot
async function loadBriefing(force = false) {
  const box = document.getElementById("briefing");
  const button = document.getElementById("briefing-btn");
  button.disabled = true;
  box.innerHTML = `<p class="muted small">${t("briefingLoading")}</p>`;
  try {
    const { body: b } = await api("/ops/briefing", { method: "POST", body: JSON.stringify({ force }) });
    const minutes = Math.max(0, Math.round((Date.now() - Date.parse(b.generated_at)) / 60000));
    const actions = (b.actions || []).map((a) => `
      <li><span class="act ${esc(a.action)}">${esc(t("actions")[a.action] || a.action)}</span>
      <b>${esc(a.name)}</b><span class="reason">${esc(a.reason)}</span></li>`).join("");
    const summary = state.lang === "kn" ? b.summary_kn : b.summary_en;
    const trace = (b.tools_used || []).map((name) => `<span>→ ${esc(name)}</span>`).join("");
    box.innerHTML = `
      <p class="headline">${esc(b.headline)}</p>
      ${actions ? `<ul class="actions">${actions}</ul>` : ""}
      <div class="summary-box">${esc(summary)}</div>
      ${trace ? `<div class="trace">${trace}</div>` : ""}
      <p class="meta">${t("generatedAt", minutes, b.cached)}${b.source === "fallback" ? " · fallback" : ""}</p>`;
  } catch (err) {
    box.innerHTML = `<p class="muted small">${t("briefingFailed")} ${esc(err.message)}</p>`;
  } finally {
    button.disabled = false;
  }
}
document.getElementById("briefing-btn").addEventListener("click", () => loadBriefing());

// ---------------------------------------------------------------- start
initMap();
state.map.on("click", (e) => {
  if (state.route.mode === "from") setPoint("from", e.latlng);
  else if (state.route.mode === "to") setPoint("to", e.latlng);
});
applyLanguage();
loadHotspots();
setInterval(() => {
  loadHotspots();
  if (document.getElementById("view-ops").classList.contains("active")) loadOps();
}, REFRESH_MS);
