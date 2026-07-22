(() => {
  const CARD_VERSION = "0.2.0";
  const CARD_TYPE = "erftverband-riverlevel-card";
  const DOMAIN = "erftverband_riverlevel";
  const ATTR = "erftverband_";
  const LEVEL_BACKGROUND_URL = new URL(
    "./assets/level_background.png",
    import.meta.url
  ).href;

  console.info("[erftverband-riverlevel-card] loaded", CARD_VERSION);

  const ROLE_WATER_LEVEL = "water_level";
  const ROLE_DISCHARGE = "discharge";
  const ROLE_WATER_TREND = "water_level_trend";
  const ROLE_DISCHARGE_TREND = "discharge_trend";
  const ROLE_LAST_MEASUREMENT = "last_measurement";
  const ROLE_DATA_AGE = "data_age";
  const ROLE_FLOOD_STATUS = "flood_status";
  const ROLE_DATA_STALE = "data_stale";
  const ROLE_FLOOD_ALARM = "flood_alarm";
  const ROLE_SOURCE_REACHABLE = "source_reachable";

  const ROLES_DISPLAY = [
    ROLE_FLOOD_STATUS,
    ROLE_WATER_LEVEL,
    ROLE_DISCHARGE,
    ROLE_WATER_TREND,
    ROLE_LAST_MEASUREMENT,
    ROLE_DATA_AGE,
  ];

  const HISTORY_CACHE_TTL = 15 * 60 * 1000;
  const HISTORY_DEFAULT_HOURS = 24;

  const _stubConfig = {
    hours_to_show: HISTORY_DEFAULT_HOURS,
    show_history: true,
    show_discharge: true,
    show_source_status: true,
    sort_by: "name",
  };

  const FLOOD_LABELS = {
    normal: "Normal",
    ev_action: "EV-Einsatzplan",
    hq10: "HQ10",
    hq100: "HQ100",
    extreme: "HQextrem",
    unknown: "Unbekannt",
  };

  const FLOOD_COLORS = {
    normal: "var(--state-active-color, #43a047)",
    ev_action: "var(--warning-color, #fdd835)",
    hq10: "var(--accent-color, #ff9800)",
    hq100: "var(--error-color, #e53935)",
    extreme: "#c62828",
    unknown: "var(--disabled-text-color, #9e9e9e)",
  };

  const FLOOD_BG = {
    normal: "rgba(67,160,71,0.15)",
    ev_action: "rgba(253,216,53,0.15)",
    hq10: "rgba(255,152,0,0.15)",
    hq100: "rgba(229,57,53,0.15)",
    extreme: "rgba(198,40,40,0.2)",
    unknown: "rgba(158,158,158,0.15)",
  };

  const FLOOD_WARNING_STATES = new Set([
    "ev_action",
    "hq10",
    "hq100",
    "extreme"
  ]);

  const CARD_STYLES = `
:host {
  display: block;
  width: 100%;
  min-width: 0;
}

ha-card {
  display: block;
  width: 100%;
  overflow: hidden;
  background: transparent;
  box-shadow: none;
  position: relative;
}

ha-card::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image:
    linear-gradient(
      180deg,
      rgba(2, 9, 20, 0.74),
      rgba(2, 8, 18, 0.94)
    ),
    var(--erftverband-bg-url);
  background-position: top center;
  background-size: cover;
  background-repeat: no-repeat;
  background-attachment: local;
  pointer-events: none;
}

ha-card > * {
  position: relative;
  z-index: 1;
}

.erftverband-riverlevel-container {
  width: 100%;
}

.erftverband-riverlevel-empty {
  text-align: center;
  padding: 24px 16px;
  color: var(--primary-text-color, #e0e0e0);
  font-size: 15px;
  background: var(--card-background-color, #1e1e2e);
  border-radius: 16px;
  border: 1px solid var(--divider-color, rgba(255,255,255,0.08));
}

.erftverband-riverlevel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr));
  gap: 16px;
  width: 100%;
  min-width: 0;
}

.erftverband-riverlevel-station {
  position: relative;
  box-sizing: border-box;
  min-width: 0;
  overflow: hidden;
  background: linear-gradient(135deg, var(--card-background-color, #1b1f2e), var(--ha-card-background, #1e1e2e));
  border-radius: 18px;
  border: 1px solid var(--divider-color, rgba(255,255,255,0.1));
  box-shadow: 0 8px 24px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.06);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 0.2s;
}

.erftverband-riverlevel-station:hover {
  box-shadow: 0 12px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
}

.erftverband-riverlevel-alarm-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(198,40,40,0.85);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 3px 10px;
  border-radius: 10px;
  z-index: 1;
  animation: erftverband-riverlevel-pulse 2s infinite;
}

.erftverband-riverlevel-stale-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(253,216,53,0.2);
  color: var(--warning-color, #fdd835);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 3px 10px;
  border-radius: 10px;
  z-index: 1;
}

@keyframes erftverband-riverlevel-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.erftverband-riverlevel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.erftverband-riverlevel-header-icon {
  font-size: 20px;
  line-height: 1;
}

.erftverband-riverlevel-header-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary-text-color, #e8ecf4);
  letter-spacing: 0.02em;
  flex: 1;
}

.erftverband-riverlevel-body {
  display: flex;
  align-items: flex-end;
  gap: 16px;
}

.erftverband-riverlevel-water-level {
  flex: 1;
}

.erftverband-riverlevel-water-level-value {
  font-size: 40px;
  font-weight: 900;
  color: var(--state-icon-active-color, #4fc3f7);
  line-height: 1;
  cursor: pointer;
  transition: opacity 0.15s;
}

.erftverband-riverlevel-water-level-value:hover {
  opacity: 0.8;
}

.erftverband-riverlevel-water-level-value.erftverband-riverlevel-na {
  color: var(--disabled-text-color, #6b7280);
}

.erftverband-riverlevel-unit {
  font-size: 13px;
  font-weight: 600;
  color: var(--secondary-text-color, #8e9bad);
  margin-top: 4px;
}

.erftverband-riverlevel-sidebar {
  text-align: right;
  flex-shrink: 0;
}

.erftverband-riverlevel-metric {
  margin-bottom: 6px;
}

.erftverband-riverlevel-metric:last-child {
  margin-bottom: 0;
}

.erftverband-riverlevel-metric-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--secondary-text-color, #8e9bad);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.erftverband-riverlevel-metric-value {
  font-size: 19px;
  font-weight: 700;
  color: var(--primary-text-color, #e0e4ed);
  line-height: 1.2;
  cursor: pointer;
}

.erftverband-riverlevel-metric-value:hover {
  opacity: 0.8;
}

.erftverband-riverlevel-metric-value.erftverband-riverlevel-na {
  color: var(--disabled-text-color, #6b7280);
  cursor: default;
}

.erftverband-riverlevel-metric-value.erftverband-riverlevel-na:hover {
  opacity: 1;
}

.erftverband-riverlevel-metric-small {
  font-size: 14px;
  font-weight: 600;
  cursor: default;
}

.erftverband-riverlevel-unit-sm {
  font-size: 12px;
  font-weight: 600;
  color: var(--secondary-text-color, #8e9bad);
  margin-left: 2px;
}

.erftverband-riverlevel-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 4px;
  border-top: 1px solid var(--divider-color, rgba(255,255,255,0.06));
}

.erftverband-riverlevel-footer-left {
  flex: 1;
}

.erftverband-riverlevel-footer-right {
  flex: 1;
}

.erftverband-riverlevel-footer-right .erftverband-riverlevel-metric {
  text-align: right;
}

.erftverband-riverlevel-status-bar {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: center;
  padding: 4px 8px;
  border-radius: 10px;
}

.erftverband-riverlevel-chart {
  margin-top: 4px;
  overflow: hidden;
}

.erftverband-riverlevel-chart-svg {
  width: 100%;
  height: auto;
  display: block;
}

.erftverband-riverlevel-chart-loading {
  text-align: center;
  padding: 12px;
  color: var(--secondary-text-color, #8e9bad);
  font-size: 12px;
}

.erftverband-riverlevel-chart-empty {
  text-align: center;
  padding: 12px;
  color: var(--secondary-text-color, #8e9bad);
  font-size: 12px;
  font-style: italic;
}

.erftverband-riverlevel-chart-error {
  text-align: center;
  padding: 12px;
  color: var(--error-color, #e53935);
  font-size: 12px;
}

.erftverband-riverlevel-source-link {
  display: block;
  text-align: right;
  font-size: 10px;
  color: var(--secondary-text-color, #8e9bad);
  text-decoration: none;
  margin-top: 2px;
}

.erftverband-riverlevel-source-link:hover {
  text-decoration: underline;
  color: var(--primary-text-color, #e0e4ed);
}

.erftverband-riverlevel-discharge-value {
  cursor: pointer;
}

.erftverband-riverlevel-discharge-value:hover {
  opacity: 0.8;
}

.erftverband-riverlevel-howis-off {
  text-align: center;
  padding: 8px 16px;
  margin-bottom: 8px;
  color: var(--error-color, #e53935);
  font-size: 13px;
  font-weight: 600;
  background: rgba(229,57,53,0.1);
  border-radius: 10px;
  border: 1px solid rgba(229,57,53,0.25);
}

.erftverband-riverlevel-freshness-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.erftverband-riverlevel-freshness-dot.fresh {
  background: #4ade80;
  box-shadow: 0 0 6px rgba(74,222,128,0.5);
}

.erftverband-riverlevel-freshness-dot.stale {
  background: #facc15;
  box-shadow: 0 0 6px rgba(250,204,21,0.5);
}

.erftverband-riverlevel-freshness-dot.very-stale,
.erftverband-riverlevel-freshness-dot.missing {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239,68,68,0.5);
}

.erftverband-riverlevel-freshness-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 3px 10px;
  border-radius: 10px;
  z-index: 1;
}

.erftverband-riverlevel-freshness-badge-warn {
  background: rgba(253,216,53,0.2);
  color: var(--warning-color, #fdd835);
}

.erftverband-riverlevel-freshness-badge-ko {
  background: rgba(229,57,53,0.2);
  color: var(--error-color, #e53935);
}
`;

  if (!customElements.get(CARD_TYPE)) {
    class ErftverbandRiverlevelCard extends HTMLElement {
      constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this._config = {};
        this._hass = null;
        this._historyCache = {};
        this._historyPromises = {};
        this._updateTimer = null;
        this._attached = false;
        this._abortController = new AbortController();
        this._historyErrorLogged = new Set();
        this.shadowRoot.innerHTML = `<style>${CARD_STYLES}</style><ha-card id="erftverband-riverlevel-card-root"></ha-card>`;
        this._cardRoot = this.shadowRoot.getElementById("erftverband-riverlevel-card-root");
        if (this._cardRoot) {
          this._cardRoot.style.setProperty("--erftverband-bg-url", `url("${LEVEL_BACKGROUND_URL}")`);
        }
      }

      static getStubConfig() {
        return { ..._stubConfig };
      }

      static getConfigElement() {
        return document.createElement("erftverband-riverlevel-card-editor");
      }

      setConfig(config) {
        if (!config || typeof config !== "object") {
          throw new Error("Invalid configuration");
        }
        const hours = Number(config.hours_to_show) || HISTORY_DEFAULT_HOURS;
        this._config = {
          hours_to_show: Math.max(1, Math.min(168, hours)),
          show_history: config.show_history !== false,
          show_discharge: config.show_discharge !== false,
          show_source_status: config.show_source_status !== false,
          sort_by: config.sort_by || "name",
          stations: config.stations,
        };
      }

      set hass(hass) {
        this._hass = hass;
        this._render();
      }

      getCardSize() {
        const stations = this._getStations();
        if (!stations || stations.length === 0) return 2;
        const base = stations.length;
        const hasHistory = this._config.show_history;
        return Math.max(2, base * (hasHistory ? 4 : 2));
      }

      getGridOptions() {
        return {
          columns: "full",
          min_columns: 6,
        };
      }

      connectedCallback() {
        this._attached = true;
        if (this._hass) {
          this._render();
        }
        this._startDisplayTimer();
      }

      disconnectedCallback() {
        this._attached = false;
        this._stopDisplayTimer();
        this._abortController.abort();
        this._abortController = new AbortController();
        if (this._updateTimer) {
          clearTimeout(this._updateTimer);
          this._updateTimer = null;
        }
      }

      _startDisplayTimer() {
        this._stopDisplayTimer();
        this._displayTimer = setInterval(() => {
          if (this._attached && this._hass) {
            this._render();
          }
        }, 60000);
      }

      _stopDisplayTimer() {
        if (this._displayTimer != null) {
          clearInterval(this._displayTimer);
          this._displayTimer = null;
        }
      }

      _getStations() {
        if (!this._hass) return [];
        const states = this._hass.states;
        if (!states) return [];
        const stations = new Map();
        const seen = new Map();
        for (const entityId of Object.keys(states)) {
          const entity = states[entityId];
          if (!entity || !entity.attributes) continue;
          const attrs = entity.attributes;
          if (attrs[`${ATTR}riverlevel`] !== true) continue;
          const rawStationId = attrs[`${ATTR}station_id`];
          if (rawStationId == null || rawStationId === "") continue;
          const stationId = String(rawStationId).trim().toLowerCase();
          const role = String(attrs[`${ATTR}sensor_role`]).trim();
          if (!stationId || !role) continue;
          const key = `${stationId}:${role}`;
          const prev = seen.get(key);
          if (prev) {
            const prevState = prev.entity.state;
            const curState = entity.state;
            const prevOk = prevState !== "unavailable" && prevState !== "unknown" && prevState != null;
            const curOk = curState !== "unavailable" && curState !== "unknown" && curState != null;
            if (curOk && !prevOk) {
              stations.get(stationId).entities[role] = entity;
              seen.set(key, { entity, entityId });
            } else if (curOk === prevOk) {
              const prevTs = prev.entity.last_updated || 0;
              const curTs = entity.last_updated || 0;
              if (curTs > prevTs) {
                stations.get(stationId).entities[role] = entity;
                seen.set(key, { entity, entityId });
              } else if (curTs === prevTs && entityId < prev.entityId) {
                stations.get(stationId).entities[role] = entity;
                seen.set(key, { entity, entityId });
              }
            }
            continue;
          }
          seen.set(key, { entity, entityId });
          if (!stations.has(stationId)) {
            stations.set(stationId, {
              id: stationId,
              name:
                attrs[`${ATTR}station_name`] ||
                String(rawStationId) ||
                stationId,
              waterbody:
                attrs[`${ATTR}waterbody`] || "",
              sourceUrl: attrs[`${ATTR}source_url`] || null,
              source: attrs[`${ATTR}source`] || "HOWIS",
              entities: {},
            });
          }
          stations.get(stationId).entities[role] = entity;
        }
        if (stations.size === 0) return [];
        const result = Array.from(stations.values());
        const sortBy = this._config.sort_by || "name";
        if (sortBy === "name") {
          result.sort((a, b) =>
            a.name.toLowerCase().localeCompare(b.name.toLowerCase())
          );
        } else if (sortBy === "water_level") {
          result.sort((a, b) => {
            const wa = a.entities[ROLE_WATER_LEVEL];
            const wb = b.entities[ROLE_WATER_LEVEL];
            const va = wa ? parseFloat(wa.state) : -Infinity;
            const vb = wb ? parseFloat(wb.state) : -Infinity;
            if (isNaN(va) && isNaN(vb)) return 0;
            if (isNaN(va)) return 1;
            if (isNaN(vb)) return -1;
            return vb - va;
          });
        } else if (sortBy === "waterbody") {
          result.sort((a, b) =>
            (a.waterbody || "").toLowerCase().localeCompare((b.waterbody || "").toLowerCase())
          );
        } else if (sortBy === "data_age") {
          result.sort((a, b) => {
            const aa = a.entities[ROLE_DATA_AGE];
            const ba = b.entities[ROLE_DATA_AGE];
            const va = aa ? parseFloat(aa.state) : Infinity;
            const vb = ba ? parseFloat(ba.state) : Infinity;
            if (isNaN(va) && isNaN(vb)) return 0;
            if (isNaN(va)) return 1;
            if (isNaN(vb)) return -1;
            return va - vb;
          });
        } else if (sortBy === "flood_status") {
          const order = ["extreme", "hq100", "hq10", "ev_action", "normal", "unknown"];
          result.sort((a, b) => {
            const sa = a.entities[ROLE_FLOOD_STATUS];
            const sb = b.entities[ROLE_FLOOD_STATUS];
            const oa = sa ? order.indexOf(sa.state) : order.length;
            const ob = sb ? order.indexOf(sb.state) : order.length;
            return oa - ob;
          });
        }

        const stationIds = Array.isArray(this._config.stations)
          ? this._config.stations
              .map((v) => String(v ?? "").trim().toLowerCase())
              .filter(Boolean)
          : [];

        if (stationIds.length > 0) {
          return result.filter((s) => stationIds.includes(s.id));
        }

        return result;
      }

      _render() {
        const stations = this._getStations();
        const showHistory = this._config.show_history;
        const showDischarge = this._config.show_discharge;

        let howisOff = false;
        if (this._hass) {
          for (const eid of Object.keys(this._hass.states)) {
            const ent = this._hass.states[eid];
            if (!ent || !ent.attributes) continue;
            if (ent.attributes[`${ATTR}riverlevel`] !== true) continue;
            if (String(ent.attributes[`${ATTR}sensor_role`]).trim() !== ROLE_SOURCE_REACHABLE) continue;
            howisOff = ent.state === "off";
            break;
          }
        }

        let content = `<div class="erftverband-riverlevel-container">`;

        if (howisOff && this._config.show_source_status) {
          content += `<div class="erftverband-riverlevel-howis-off">HOWIS nicht erreichbar</div>`;
        }

        if (stations.length === 0) {
          content += `<div class="erftverband-riverlevel-empty">Keine Erftverband-Pegel gefunden</div>`;
        } else {
          content += `<div class="erftverband-riverlevel-grid">`;
          for (const station of stations) {
            content += this._renderStation(station, showDischarge, showHistory);
          }
          content += `</div>`;
        }

        content += `</div>`;

        if (this._cardRoot) {
          this._cardRoot.innerHTML = content;
        }

        const root = this.shadowRoot;
        for (const station of stations) {
          const wl = station.entities[ROLE_WATER_LEVEL];
          if (wl) {
            const header = root.querySelector(`[data-station-id="${station.id}"] .erftverband-riverlevel-header`);
            if (header) {
              header.addEventListener("click", () => this._openMoreInfo(wl.entity_id));
            }
            const value = root.querySelector(`[data-station-id="${station.id}"] .erftverband-riverlevel-water-level-value`);
            if (value) {
              value.addEventListener("click", () => this._openMoreInfo(wl.entity_id));
            }
          }
          if (showDischarge) {
            const q = station.entities[ROLE_DISCHARGE];
            if (q) {
              const qEl = root.querySelector(`[data-station-id="${station.id}"] .erftverband-riverlevel-discharge-value`);
              if (qEl) {
                qEl.addEventListener("click", () => this._openMoreInfo(q.entity_id));
              }
            }
          }
          if (showHistory) {
            this._loadHistory(station);
          }
        }
      }

      _renderStation(station, showDischarge, showHistory) {
        const wl = station.entities[ROLE_WATER_LEVEL];
        const q = station.entities[ROLE_DISCHARGE];
        const trend = station.entities[ROLE_WATER_TREND];
        const last = station.entities[ROLE_LAST_MEASUREMENT];
        const status = station.entities[ROLE_FLOOD_STATUS];
        const alarm = station.entities[ROLE_FLOOD_ALARM];
        const sourceUrl = station.sourceUrl;

        const wlVal = this._safeNum(wl);
        const qVal = this._safeNum(q);
        const trendVal = this._safeNum(trend);
        const lastVal = last ? last.state : null;
        const ageMinutes = this._getAgeMinutes(station);

        const statusState = status ? status.state : "";
        const normalizedStatus = String(statusState).trim().toLowerCase();
        const showFloodStatus = FLOOD_WARNING_STATES.has(normalizedStatus);
        const statusLabel = FLOOD_LABELS[normalizedStatus] || "";
        const isAlarm = alarm ? alarm.state === "on" : false;

        const freshness = this._getFreshness(ageMinutes);
        const freshnessDot = `<span class="erftverband-riverlevel-freshness-dot ${freshness.cls}" title="${freshness.title}" aria-label="${freshness.title}" tabindex="0"></span>`;

        const formattedDate = this._formatDate(lastVal);
        const formattedAge = ageMinutes != null && Number.isFinite(ageMinutes) ? `${Math.round(ageMinutes)} min` : "\u2014";

        let trendHtml = "";
        if (trendVal != null && !isNaN(trendVal)) {
          const arrow = trendVal > 0
            ? "\u25B4"
            : trendVal < 0
              ? "\u25BE"
              : "\u25B8";
          const absVal = Math.abs(trendVal);
          trendHtml = `${arrow} ${this._formatNum(absVal)} cm/h`;
        } else {
          trendHtml = "\u2014";
        }

        let alarmHtml = "";
        if (isAlarm && normalizedStatus !== "normal") {
          alarmHtml = `<div class="erftverband-riverlevel-alarm-badge">HOCHWASSERALARM</div>`;
        }

        const topBadge = alarmHtml;

        const sid = station.id;

        const wlHasValue = wlVal !== null && Number.isFinite(wlVal);
        const qHasValue = qVal !== null && Number.isFinite(qVal);

        const wlNa = !wl || wl.state === "unavailable" || wl.state === "unknown";
        const qNa = !q || q.state === "unavailable" || q.state === "unknown";

        return `<div class="erftverband-riverlevel-station" data-station-id="${sid}">
          ${topBadge}
          <div class="erftverband-riverlevel-header">
            <span class="erftverband-riverlevel-header-icon">&#x1F30A;</span>
            <span class="erftverband-riverlevel-header-name">${station.waterbody ? `${this._esc(station.waterbody)} \u2013 ${this._esc(station.name)}` : this._esc(station.name)}</span>
            ${freshnessDot}
          </div>
          <div class="erftverband-riverlevel-body">
            <div class="erftverband-riverlevel-water-level">
              <div class="erftverband-riverlevel-water-level-value${wlNa ? " erftverband-riverlevel-na" : ""}">
                ${this._esc(wlHasValue ? `${this._formatNum(wlVal)}` : "\u2014")}
              </div>
              <div class="erftverband-riverlevel-unit">cm</div>
            </div>
            <div class="erftverband-riverlevel-sidebar">
              ${showDischarge ? `
              <div class="erftverband-riverlevel-metric">
                <div class="erftverband-riverlevel-metric-label">Abfluss</div>
                <div class="erftverband-riverlevel-metric-value erftverband-riverlevel-discharge-value${qNa ? " erftverband-riverlevel-na" : ""}">
                  ${this._esc(qHasValue ? `${this._formatNum(qVal)}` : "\u2014")}
                  <span class="erftverband-riverlevel-unit-sm">m\u00B3/s</span>
                </div>
              </div>` : ""}
              <div class="erftverband-riverlevel-metric">
                <div class="erftverband-riverlevel-metric-label">Trend</div>
                <div class="erftverband-riverlevel-metric-value">${trendHtml}</div>
              </div>
            </div>
          </div>
          <div class="erftverband-riverlevel-footer">
            <div class="erftverband-riverlevel-footer-left">
              <div class="erftverband-riverlevel-metric">
                <div class="erftverband-riverlevel-metric-label">Messung</div>
                <div class="erftverband-riverlevel-metric-value erftverband-riverlevel-metric-small">${this._esc(formattedDate)}</div>
              </div>
            </div>
            <div class="erftverband-riverlevel-footer-right">
              <div class="erftverband-riverlevel-metric">
                <div class="erftverband-riverlevel-metric-label">Alter</div>
                <div class="erftverband-riverlevel-metric-value erftverband-riverlevel-metric-small">${this._esc(formattedAge)}</div>
              </div>
            </div>
          </div>
          ${showFloodStatus ? `<div class="erftverband-riverlevel-status-bar" style="background:${FLOOD_BG[normalizedStatus]};color:${FLOOD_COLORS[normalizedStatus]}">${this._esc(statusLabel)}</div>` : ""}
          ${showHistory ? `<div class="erftverband-riverlevel-chart" id="erftverband-riverlevel-chart-${sid}"></div>` : ""}
          ${sourceUrl ? `<a href="${this._esc(sourceUrl)}" target="_blank" rel="noopener noreferrer" class="erftverband-riverlevel-source-link">Quelle: HOWIS</a>` : ""}
        </div>`;
      }

      _normalizeHistoryRows(rows) {
        if (!Array.isArray(rows)) return [];
        const result = [];
        for (const row of rows) {
          const rawState = row.state ?? row.s;
          if (rawState == null) continue;
          const value = Number.parseFloat(rawState);
          if (!Number.isFinite(value)) continue;
          const rawTimestamp =
            row.last_changed ??
            row.last_updated ??
            row.lc ??
            row.lu;
          if (rawTimestamp == null) continue;
          const timestamp = typeof rawTimestamp === "number"
            ? rawTimestamp * 1000
            : new Date(rawTimestamp).getTime();
          if (!Number.isFinite(timestamp)) continue;
          result.push({ value, timestamp });
        }
        result.sort((a, b) => a.timestamp - b.timestamp);
        return result;
      }

      async _loadHistory(station) {
        const sid = station.id;
        const wl = station.entities[ROLE_WATER_LEVEL];
        const q = station.entities[ROLE_DISCHARGE];

        const hours = this._config.hours_to_show || HISTORY_DEFAULT_HOURS;
        const cacheKey = `${CARD_VERSION}:${sid}:${hours}`;
        const now = Date.now();
        const cached = this._historyCache[cacheKey];

        if (!wl && !q) {
          this._historyCache[cacheKey] = {
            status: "empty",
            loadedAt: now,
            water: [],
            discharge: [],
          };
          this._renderChart(sid, this._historyCache[cacheKey]);
          return;
        }

        if (cached && now - cached.loadedAt < HISTORY_CACHE_TTL) {
          this._renderChart(sid, cached);
          return;
        }

        if (this._historyPromises[cacheKey]) {
          try {
            await this._historyPromises[cacheKey];
          } catch {
            // ignore
          }
          return;
        }

        const startTime = new Date(now - hours * 3600_000);
        const endTime = new Date(now);

        const entityIds = [];
        if (wl) entityIds.push(wl.entity_id);
        if (q) entityIds.push(q.entity_id);

        const chartEl = this.shadowRoot.querySelector(`#erftverband-riverlevel-chart-${sid}`);
        if (chartEl && !cached) {
          chartEl.innerHTML = `<div class="erftverband-riverlevel-chart-loading">Lade Verlauf...</div>`;
        }

        const promise = this._hass.callWS({
          type: "history/history_during_period",
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
          entity_ids: entityIds,
          include_start_time_state: true,
          significant_changes_only: false,
          minimal_response: false,
          no_attributes: true,
        });
        this._historyPromises[cacheKey] = promise;

        try {
          const response = await promise;
          if (this._abortController.signal.aborted) return;

          const waterRaw = wl ? (response[wl.entity_id] || []) : [];
          const dischargeRaw = q ? (response[q.entity_id] || []) : [];

          const water = this._normalizeHistoryRows(waterRaw);
          const discharge = this._normalizeHistoryRows(dischargeRaw);

          const status = (water.length === 0 && discharge.length === 0) ? "empty" : "ready";

          const entry = {
            status,
            loadedAt: Date.now(),
            water,
            discharge,
          };
          this._historyCache[cacheKey] = entry;

          this._renderChart(sid, entry);
        } catch (err) {
          if (err.name !== "AbortError") {
            if (!this._historyErrorLogged.has(cacheKey)) {
              console.warn("[erftverband-riverlevel-card] history request failed", err);
              this._historyErrorLogged.add(cacheKey);
            }
            const entry = {
              status: "error",
              loadedAt: Date.now(),
              water: [],
              discharge: [],
            };
            this._historyCache[cacheKey] = entry;
            this._renderChart(sid, entry);
          }
        } finally {
          delete this._historyPromises[cacheKey];
          if (this._attached) {
            this._render();
          }
        }
      }

      _renderChart(stationId, history) {
        const chartEl = this.shadowRoot.querySelector(`#erftverband-riverlevel-chart-${stationId}`);
        if (!chartEl) return;

        if (!history) {
          chartEl.innerHTML = `<div class="erftverband-riverlevel-chart-loading">Lade Verlauf...</div>`;
          return;
        }

        if (history.status === "error") {
          chartEl.innerHTML = `<div class="erftverband-riverlevel-chart-error">Verlauf nicht verf\u00FCgbar</div>`;
          return;
        }

        const wlData = history.water || [];
        const qData = history.discharge || [];

        if (wlData.length === 0 && qData.length === 0) {
          chartEl.innerHTML = `<div class="erftverband-riverlevel-chart-empty">Keine Verlaufsdaten</div>`;
          return;
        }

        const padding = { top: 20, right: 50, bottom: 30, left: 45 };
        const width = 600;
        const height = 180;
        const plotW = width - padding.left - padding.right;
        const plotH = height - padding.top - padding.bottom;

        let tMin = Infinity;
        let tMax = -Infinity;
        for (const pt of [...wlData, ...qData]) {
          if (pt.timestamp < tMin) tMin = pt.timestamp;
          if (pt.timestamp > tMax) tMax = pt.timestamp;
        }
        if (!Number.isFinite(tMin)) {
          chartEl.innerHTML = `<div class="erftverband-riverlevel-chart-empty">Keine Verlaufsdaten</div>`;
          return;
        }
        const tRange = tMax - tMin || 1;
        const timeScale = (t) => ((t - tMin) / tRange) * plotW;

        const calcRange = (data) => {
          if (!data || data.length === 0) return null;
          let min = Infinity;
          let max = -Infinity;
          for (const pt of data) {
            if (pt.value < min) min = pt.value;
            if (pt.value > max) max = pt.value;
          }
          const range = max - min || 1;
          return { min: min - range * 0.05, max: max + range * 0.05 };
        };

        const wlRange = calcRange(wlData);
        const qRange = calcRange(qData);

        const makeScale = (range) => {
          if (!range) return () => plotH / 2;
          const r = range.max - range.min || 1;
          return (v) => plotH - ((v - range.min) / r) * plotH;
        };

        const wlScale = makeScale(wlRange);
        const qScale = makeScale(qRange);

        const makePolyline = (data, scale) => {
          if (!data || data.length === 0) return "";
          if (data.length === 1) {
            const y = scale(data[0].value);
            return `0,${y.toFixed(1)} ${plotW},${y.toFixed(1)}`;
          }
          const points = data.map((pt) => {
            const x = timeScale(pt.timestamp);
            const y = scale(pt.value);
            return `${x.toFixed(1)},${y.toFixed(1)}`;
          }).join(" ");
          return points;
        };

        const wlPoints = makePolyline(wlData, wlScale);
        const qPoints = makePolyline(qData, qScale);
        const wlColor = "#4fc3f7";
        const qColor = "#81deea";

        const formatTime = (ts) => {
          const d = new Date(ts);
          try {
            return new Intl.DateTimeFormat(undefined, {
              hour: "2-digit",
              minute: "2-digit",
            }).format(d);
          } catch {
            return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          }
        };

        const clipId = `erftverband-riverlevel-clip-${stationId}`;

        let svg = `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="erftverband-riverlevel-chart-svg">
          <defs>
            <clipPath id="${clipId}">
              <rect x="${padding.left}" y="${padding.top}" width="${plotW}" height="${plotH}" />
            </clipPath>
          </defs>
          <g font-size="9" fill="#8e9bad" font-family="var(--paper-font-body_-_font-family, sans-serif)">
            <text x="${padding.left}" y="12" fill="#b0bcca" font-size="10" font-weight="600">cm</text>
            ${qData.length > 0 ? `<text x="${width - padding.right}" y="12" fill="#b0bcca" font-size="10" font-weight="600" text-anchor="end">m\u00B3/s</text>` : ""}`;

        const numYTicks = 4;
        if (wlRange) {
          for (let i = 0; i <= numYTicks; i++) {
            const v = wlRange.min + (wlRange.max - wlRange.min) * (i / numYTicks);
            const y = wlScale(v) + padding.top;
            svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2,2" />
              <text x="${padding.left - 4}" y="${y + 3}" text-anchor="end">${this._formatNum(v)}</text>`;
          }
        }

        if (qRange && qData.length > 0) {
          for (let i = 0; i <= numYTicks; i++) {
            const v = qRange.min + (qRange.max - qRange.min) * (i / numYTicks);
            const y = qScale(v) + padding.top;
            svg += `<text x="${width - padding.right + 4}" y="${y + 3}" text-anchor="start" fill="${qColor}">${this._formatNum(v)}</text>`;
          }
        }

        svg += `<g clip-path="url(#${clipId})">`;
        if (wlPoints) {
          svg += `<polyline points="${wlPoints}" fill="none" stroke="${wlColor}" stroke-width="1.5" stroke-linejoin="round" />`;
        }
        if (qPoints) {
          svg += `<polyline points="${qPoints}" fill="none" stroke="${qColor}" stroke-width="1.5" stroke-dasharray="4,3" stroke-linejoin="round" />`;
        }
        svg += `</g>`;

        const numXTicks = 5;
        for (let i = 0; i <= numXTicks; i++) {
          const t = tMin + (tRange * i) / numXTicks;
          const x = timeScale(t) + padding.left;
          svg += `<text x="${x}" y="${height - 8}" text-anchor="middle">${formatTime(t)}</text>`;
        }

        svg += `</g>`;
        svg += `<g font-size="9" font-family="var(--paper-font-body_-_font-family, sans-serif)">
          <rect x="${padding.left}" y="${height - 14}" width="8" height="8" fill="${wlColor}" rx="1" />
          <text x="${padding.left + 12}" y="${height - 6}" fill="#b0bcca">Wasserstand</text>`;
        if (qPoints) {
          svg += `<rect x="${padding.left + 90}" y="${height - 14}" width="8" height="8" fill="${qColor}" rx="1" />
            <text x="${padding.left + 102}" y="${height - 6}" fill="#b0bcca">Abfluss</text>`;
        }
        svg += `</g>`;
        svg += `</svg>`;

        chartEl.innerHTML = svg;
      }

      _safeNum(entity) {
        if (!entity) return null;
        const v = entity.state;
        if (v === "unavailable" || v === "unknown" || v === "none" || v == null) return null;
        const n = parseFloat(v);
        return isNaN(n) ? null : n;
      }

      _formatNum(n) {
        if (n == null || isNaN(n)) return "\u2014";
        try {
          return new Intl.NumberFormat(undefined, {
            maximumFractionDigits: 1,
            minimumFractionDigits: 0,
          }).format(n);
        } catch {
          return String(n);
        }
      }

      _getFreshness(ageMinutes) {
        if (ageMinutes == null || !Number.isFinite(ageMinutes)) {
          return { cls: "missing", title: "Keine g\u00FCltigen Messdaten verf\u00FCgbar" };
        }
        if (ageMinutes < 60) {
          const m = Math.round(ageMinutes);
          return { cls: "fresh", title: `Aktuelle Daten \u2013 letzte Messung vor ${m} Minute${m === 1 ? "" : "n"}` };
        }
        if (ageMinutes < 720) {
          const h = Math.round(ageMinutes / 60);
          return { cls: "stale", title: `Daten veraltet \u2013 letzte Messung vor ${h} Stunde${h === 1 ? "" : "n"}` };
        }
        const h = Math.round(ageMinutes / 60);
        return { cls: "very-stale", title: `Daten stark veraltet \u2013 letzte Messung vor ${h} Stunde${h === 1 ? "" : "n"}` };
      }

      _getAgeMinutes(station) {
        const ageEntity = station.entities[ROLE_DATA_AGE];
        let ageMinutes = this._safeNum(ageEntity);
        if (ageMinutes == null) {
          const last = station.entities[ROLE_LAST_MEASUREMENT];
          if (last) {
            try {
              const d = new Date(last.state);
              if (!isNaN(d.getTime())) {
                ageMinutes = (Date.now() - d.getTime()) / 60000;
              }
            } catch { /* ignore */ }
          }
        }
        return ageMinutes;
      }

      _formatDate(iso) {
        if (!iso || iso === "unavailable" || iso === "unknown" || iso === "none") return "\u2014";
        try {
          const d = new Date(iso);
          if (isNaN(d.getTime())) return "\u2014";
          try {
            return new Intl.DateTimeFormat(undefined, {
              day: "2-digit",
              month: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            }).format(d);
          } catch {
            return d.toLocaleString(undefined, {
              day: "2-digit",
              month: "2-digit",
              hour: "2-digit",
              minute: "2-digit",
            });
          }
        } catch {
          return "\u2014";
        }
      }

      _openMoreInfo(entityId) {
        if (!entityId) return;
        this.dispatchEvent(
          new CustomEvent("hass-more-info", {
            detail: { entityId },
            bubbles: true,
            composed: true,
          })
        );
      }

      _esc(str) {
        if (str == null) return "";
        const el = document.createElement("span");
        el.textContent = str;
        return el.innerHTML;
      }
    }

    customElements.define(CARD_TYPE, ErftverbandRiverlevelCard);
  }

  if (!customElements.get("erftverband-riverlevel-card-editor")) {
    class ErftverbandRiverlevelCardEditor extends HTMLElement {
      constructor() {
        super();
        this._config = {};
        this._hass = null;
      }

      setConfig(config) {
        this._config = { ..._stubConfig, ...config };
        this._renderForm();
      }

      set hass(hass) {
        const changed = this._hass !== hass;
        this._hass = hass;
        if (changed) {
          this._renderForm();
        }
      }

      _getStationOptions() {
        if (!this._hass || !this._hass.states) return [];
        const stations = new Map();
        for (const entityId of Object.keys(this._hass.states)) {
          const entity = this._hass.states[entityId];
          if (!entity || !entity.attributes) continue;
          const attrs = entity.attributes;
          if (attrs[`${ATTR}riverlevel`] !== true) continue;
          const rawId = attrs[`${ATTR}station_id`];
          if (rawId == null || rawId === "") continue;
          const stationId = String(rawId).trim().toLowerCase();
          if (!stationId) continue;
          if (!stations.has(stationId)) {
            const name = attrs[`${ATTR}station_name`] || String(rawId);
            const waterbody = attrs[`${ATTR}waterbody`] || "";
            stations.set(stationId, {
              value: stationId,
              label: waterbody ? `${waterbody} \u2013 ${name}` : name,
            });
          }
        }
        return Array.from(stations.values()).sort((a, b) => a.label.localeCompare(b.label));
      }

      _dispatch(config) {
        this._config = config;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config },
            bubbles: true,
            composed: true,
          })
        );
      }

      _renderForm() {
        const stationOptions = this._getStationOptions();

        const form = document.createElement("ha-form");
        form.schema = [
          {
            name: "stations",
            type: "selector",
            selector: {
              select: {
                options: stationOptions,
                multiple: true,
                mode: "dropdown",
                sort: true,
              },
            },
            label: "Angezeigte Pegel",
            description: "Keine Auswahl zeigt alle in der Integration konfigurierten Pegel.",
          },
          { name: "hours_to_show", type: "integer", default: 24, required: false, min: 1, max: 168, label: "Zeitraum der Verlaufsgrafik", description: "Anzahl der dargestellten Stunden." },
          { name: "show_history", type: "boolean", default: true, required: false, label: "Verlauf anzeigen" },
          { name: "show_discharge", type: "boolean", default: true, required: false, label: "Abfluss anzeigen" },
          { name: "show_source_status", type: "boolean", default: true, required: false, label: "Quellenangabe anzeigen" },
          {
            name: "sort_by",
            type: "select",
            default: "name",
            required: false,
            label: "Sortierung",
            options: [
              { value: "name", label: "Name" },
              { value: "waterbody", label: "Gew\u00E4sser" },
              { value: "water_level", label: "Wasserstand" },
              { value: "data_age", label: "Datenalter" },
              { value: "flood_status", label: "Hochwasserstatus" },
            ],
          },
        ];
        form.data = this._config;
        form.addEventListener("value-changed", (ev) => {
          const next = { ...this._config, ...ev.detail.value };
          this._dispatch(next);
        });

        this.innerHTML = "";
        this.appendChild(form);
      }
    }

    customElements.define("erftverband-riverlevel-card-editor", ErftverbandRiverlevelCardEditor);
  }

  if (!window.customCards) window.customCards = [];
  if (!window.customCards.some((c) => c.type === CARD_TYPE)) {
    window.customCards.push({
      type: CARD_TYPE,
      name: "Erftverband Pegelst\u00E4nde",
      description: "Pegelst\u00E4nde der konfigurierten Erftverband-HOWIS-Stationen",
      preview: true,
      documentationURL: "https://github.com/loungelizard2018/ha-riverlevel-erftverband",
    });
  }
})();
