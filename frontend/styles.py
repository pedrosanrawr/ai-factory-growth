APP_CSS = """
<style>
header[data-testid="stHeader"] {
    display: none;
}
div[data-testid="stToolbar"] {
    display: none;
}
div[data-testid="stDecoration"] {
    display: none;
}
#MainMenu {
    visibility: hidden;
}
footer {
    visibility: hidden;
}

.stApp {
    background: linear-gradient(180deg, #0a0d14 0%, #0b0e15 100%);
    color: #edf1f7;
}
[data-shell-bg] {
    background: #131722;
}
[data-testid="stSidebar"] {
    display: none;
}
.block-container {
    max-width: 1600px;
    padding-top: 1.35rem;
    padding-bottom: 2rem;
    padding-left: 1.1rem;
    padding-right: 1.1rem;
}
h1, h2, h3, p, div, span, label {
    font-family: "Segoe UI", sans-serif;
}
.top-shell {
    background: #131722;
    border: 1px solid #27304a;
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 22px;
}
.top-shell-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
}
.brand-wrap {
    display: flex;
    align-items: center;
    gap: 14px;
}
.brand-icon {
    color: #a9edf5;
    font-size: 28px;
    line-height: 1;
    display: flex;
    align-items: center;
}
.brand-title {
    font-size: 17px;
    font-weight: 700;
    color: #f4f8fd;
    margin: 0;
}
.brand-subtitle {
    font-size: 13px;
    color: #8d9ab4;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-top: 2px;
}
.export-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    background: #a8eaf2;
    color: #000000 !important;
    text-decoration: none !important;

    border: none;
    border-radius: 10px;

    padding: 9px 15px;

    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
    font-weight: 700;
    line-height: 1;

    text-decoration: none;
    cursor: pointer;

    transition:
        background 0.15s ease,
        transform 0.15s ease;
}
.export-button:hover {
    background: #b8f4fb;
    color: #102131;
    text-decoration: none;
}
.export-button:active {
    transform: translateY(1px);
}
.export-button svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}
.hero-title {
    font-size: 27px;
    font-weight: 800;
    color: #f6f7fb;
    margin: 0 0 4px 0;
}
.hero-subtitle {
    margin: 0 0 34px 0;
    padding-bottom: 28px;
    color: #96a2bd;
    font-size: 14px;
}
.section-card {
    background: #1a1f2b;
    border: 1px solid #2b3550;
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.section-card-title {
    color: #9ca9c2;
    font-size: 12px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.role-filter-title {
    margin-bottom: 14px;
}
.range-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #aab6cd;
    font-size: 14px;
    margin-bottom: 10px;
}
.range-value {
    color: #b3edf5;
    font-size: 14px;
    font-weight: 700;
}
.control-card-marker {
    margin-bottom: 0.75rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.slider-control) *,
div[data-testid="stVerticalBlockBorderWrapper"]:has(.radio-control) * {
    --primary-color: #a9edf5;
    --secondary-background-color: #131722;
    --background-color: #131722;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1a1f2b !important;
    border: 1px solid #2b3550 !important;
    border-radius: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #1a1f2b !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.slider-control) {
    min-height: 112px;
    margin-bottom: -8px;
    padding: 18px 16px 10px 16px;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.radio-control) {
    min-height: 210px;
    padding: 16px 16px 10px 16px;
    display: flex;
    flex-direction: column;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.slider-control) div[data-testid="stSlider"] {
    margin-top: 0.45rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.radio-control) div[data-testid="stRadio"] {
    margin-top: 0.35rem;
    flex: 1 1 auto;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.radio-control) > div {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.radio-spacer {
    flex: 1 1 auto;
    min-height: 86px;
}
.chip-box {
    background: #1a1f2b;
    border: 1px solid #2b3550;
    border-radius: 14px;
    padding: 12px 14px 14px 14px;
    margin-top: 14px;
    margin-bottom: 24px;
}
.chip-title {
    color: #9ca9c2;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 10px;
}
.chip-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.chip {
    background: #2a3247;
    color: #b9c5dc;
    border: 1px solid #34415f;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 13px;
}
.stack-card {
    background: #1a1f2b;
    border: 1px solid #2b3550;
    border-radius: 14px;
    padding: 16px;
    margin: 14px 0 24px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.stack-title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 14px;
}
.stack-title-row .section-card-title { margin-bottom: 4px; }
.stack-subtitle, .profile-section-subtitle { color: #8f9cb5; font-size: 13px; }
.stack-badge {
    background: #223047;
    color: #a9edf5;
    border: 1px solid #34546b;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 700;
}
.stack-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(150px, 1fr));
    gap: 12px;
}
.stack-segment {
    background: #202737;
    border: 1px solid #2d3955;
    border-radius: 10px;
    padding: 11px;
}
.stack-segment-head { display: flex; justify-content: space-between; gap: 8px; color: #dce5f5; font-size: 12px; }
.stack-segment-head strong { color: #a9edf5; }
.stack-track { height: 6px; background: #2d364d; border-radius: 999px; overflow: hidden; margin: 10px 0 7px; }
.stack-fill { height: 100%; border-radius: 999px; background: #a9edf5; }
.stack-segment-foot { color: #8190ad; font-size: 11px; }
td.profile-action-cell { text-align: center; }
.profile-view-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    background: #223047;
    color: #a9edf5 !important;
    border: 1px solid #34546b;
    border-radius: 7px;
    padding: 5px 8px;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none !important;
}
.profile-view-link:hover { background: #2b405c; color: #d7fbff !important; }
.profile-view-link svg { width: 15px; height: 15px; fill: currentColor; }
.profile-modal {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    align-items: center;
    justify-content: center;
    padding: 20px;
    font-family: "Segoe UI", sans-serif;
}
.profile-modal:target { display: flex; }
.profile-modal-backdrop {
    position: absolute;
    inset: 0;
    background: rgba(3, 7, 14, 0.78);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    cursor: default;
}
.profile-modal-panel {
    position: relative;
    z-index: 1;
    width: min(920px, 100%);
    max-height: calc(100vh - 40px);
    overflow-y: auto;
    background: #1a1f2b;
    border: 1px solid #2b3550;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255,255,255,0.02);
}
.profile-modal-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    border-bottom: 1px solid #2b3550;
    margin-bottom: 20px;
    padding-bottom: 16px;
}
.profile-modal-kicker {
    display: block;
    color: #9ca9c2;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    line-height: 1.25;
}
.profile-modal-caption {
    display: block;
    color: #8f9cb5;
    font-size: 13px;
    line-height: 1.45;
    margin-top: 3px;
}
.profile-modal-close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    flex: 0 0 32px;
    background: #223047;
    border: 1px solid #34546b;
    border-radius: 8px;
    color: #a9edf5 !important;
    text-decoration: none !important;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.profile-modal-close:hover { background: #2b405c; border-color: #4b718d; color: #d7fbff !important; }
.profile-modal-close:focus-visible {
    outline: 2px solid #a9edf5;
    outline-offset: 2px;
}
.profile-modal-close svg { width: 18px; height: 18px; fill: currentColor; }
.profile-modal-panel .company-profile { padding: 0; }
.profile-modal-panel .profile-heading {
    background: #202737;
    border: 1px solid #2d3955;
    border-radius: 10px;
    padding: 14px;
}
.profile-modal-panel .profile-rank {
    background: #223047;
    border: 1px solid #34546b;
    border-radius: 8px;
    padding: 5px 7px;
}
@media (max-width: 640px) {
    .profile-modal { padding: 12px; }
    .profile-modal-panel { max-height: calc(100vh - 24px); padding: 14px; border-radius: 14px; }
    .profile-modal-topbar { align-items: flex-start; }
    .profile-modal-caption { max-width: 220px; }
    .profile-metrics { grid-template-columns: 1fr; }
}
.company-profile { padding: 4px 2px 2px; }
.profile-heading { display: flex; align-items: center; gap: 11px; flex-wrap: wrap; }
.profile-rank { color: #a9edf5; font-size: 14px; font-weight: 800; }
.profile-company { color: #f0f5ff; font-weight: 800; font-size: 16px; }
.profile-role { color: #a6b5d0; font-size: 12px; margin-top: 2px; }
.profile-description { color: #b7c3d8; font-size: 13px; line-height: 1.55; margin: 16px 0 !important; }
.profile-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; }
.profile-metrics div { background: #202737; border: 1px solid #2d3955; border-radius: 10px; padding: 10px 11px; }
.profile-metrics span, .profile-detail > span { display: block; color: #8f9cb5; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }
.profile-metrics strong { color: #a9edf5; display: block; margin-top: 3px; font-size: 15px; }
.profile-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.profile-detail { background: #202737; border: 1px solid #2d3955; border-radius: 10px; padding: 12px; }
.profile-detail p { color: #c9d4e7; font-size: 12px; line-height: 1.55; margin: 7px 0 0 !important; }
.moat-detail > span { color: #b8d4ff; }.growth-detail > span { color: #9cf4cb; }.risk-detail > span { color: #ffbd75; }.sources-detail > span { color: #bba6ff; }.evidence-detail > span { color: #f5c9a0; }
.source-links { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 9px; }
.source-link { color: #a9edf5 !important; background: #223047; border: 1px solid #34546b; border-radius: 7px; padding: 4px 7px; font-size: 11px; text-decoration: none !important; }
.profile-empty { color: #8190ad; font-size: 12px; }
.profile-heading-status { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; margin-left: auto; }
.research-as-of { color: #8190ad; font-size: 11px; white-space: nowrap; }
.research-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
}
.research-status-badge.status-verified { background: rgba(11, 129, 93, 0.17); color: #22d29a; }
.research-status-badge.status-needs-review { background: rgba(183, 112, 8, 0.17); color: #ffb62f; }
.research-status-badge.status-fallback { background: rgba(93, 103, 133, 0.25); color: #b7c3db; }
.research-status-badge.status-unavailable { background: rgba(93, 103, 133, 0.25); color: #8190ad; }
.research-status-confidence { color: #8f9cb5; font-size: 11px; }
.evidence-list { list-style: none; margin: 9px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.evidence-item {
    background: #1b2231;
    border: 1px solid #2d3955;
    border-radius: 8px;
    padding: 8px 9px;
}
.evidence-item-title { display: block; color: #edf1f7; font-size: 12px; font-weight: 600; }
.evidence-link { color: #a9edf5 !important; text-decoration: none !important; }
.evidence-link:hover { text-decoration: underline !important; }
.evidence-item-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; margin-top: 5px; }
.evidence-source-type {
    text-transform: uppercase;
    letter-spacing: .03em;
    font-size: 10px;
    color: #8f9cb5;
    background: #223047;
    border: 1px solid #34546b;
    border-radius: 6px;
    padding: 2px 6px;
}
.evidence-retrieved { color: #8190ad; font-size: 10px; }
.research-status-badge.evidence-status { padding: 2px 7px; font-size: 10px; }
@media (max-width: 900px) {
    .stack-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .profile-detail-grid { grid-template-columns: 1fr; }
    .profile-modal-panel { width: 100%; }
}
.table-card {
    background: #1b202c;
    border: 1px solid #2b3550;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 24px;
}
.table-scroll {
    width: 100%;
}
.table-scroll.scroll-enabled {
    max-height: 420px;
    overflow-y: auto;
    overflow-x: hidden;
}
.table-header {
    background: #242a39;
    color: #f1f4fa;
    padding: 12px 16px;
    font-weight: 700;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.table-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}
.table-header-icon {
    color: #a46bf5;
}
.table-header-icon.rank {
    color: #9feaf2;
}
.table-pill {
    background: #235969;
    color: #9eeaf4;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 700;
}
table.dashboard-table {
    width: 100%;
    border-collapse: collapse;
}
table.dashboard-table thead th {
    background: #0f131c;
    color: #7384a4;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    padding: 10px 14px;
    border-bottom: 1px solid #2a334d;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 1;
}
table.dashboard-table tbody td {
    padding: 12px 14px;
    border-bottom: 1px solid #2a334d;
    color: #e8ecf4;
    font-size: 14px;
}
table.dashboard-table tbody tr:last-child td {
    border-bottom: none;
}
td.company-cell {
    font-weight: 700;
}
td.role-cell, td.risk-cell, td.rank-cell, td.status-cell, td.small-center {
    color: #b1bdd5;
}
td.rank-cell, td.small-center {
    text-align: center;
}
td.center-cell {
    text-align: center;
}
td.mini-center {
    text-align: center;
}
td.mini-center .mini-bar-wrap {
    justify-content: center;
    width: 100%;
}
.dot-row {
    display: inline-flex;
    gap: 4px;
    align-items: center;
}
.dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #7182a1;
    display: inline-block;
}
.dot.active {
    background: #b3edf5;
}
.mini-bar-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}
.mini-bar {
    width: 72px;
    height: 8px;
    border-radius: 999px;
    background: #293149;
    overflow: hidden;
    position: relative;
}
.mini-fill {
    height: 100%;
    border-radius: 999px;
}
.fill-purple {
    background: #8d5cf4;
}
.fill-green {
    background: #1fc58f;
}
.fill-red {
    background: #f24d59;
}
.eff-score {
    color: #ffbf35;
    font-weight: 800;
    text-align: center;
}
.risk-badge {
    display: inline-block;
    min-width: 96px;
    text-align: center;
    background: #2a3247;
    color: #b7c3db;
    border: 1px solid #37435f;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px;
}
.metric-moat {
    background: #22315f;
    color: #b8d4ff !important;
    text-align: center;
    font-weight: 700;
}
.metric-margin {
    background: #322f74;
    color: #d8d5ff !important;
    text-align: center;
}
.metric-growth {
    background: #18483f;
    color: #b7f7db !important;
    text-align: center;
}
.metric-eff {
    background: #173c45;
    color: #c3fbff !important;
    text-align: center;
}
.metric-tafgs {
    background: #183646;
    color: #aeefff !important;
    text-align: center;
    font-weight: 800;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 700;
}
.status-badge.profitable {
    background: rgba(11, 129, 93, 0.17);
    color: #22d29a;
}
.status-badge.unprofitable {
    background: rgba(183, 112, 8, 0.17);
    color: #ffb62f;
}
.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    display: inline-block;
}
.summary-bar {
    background: #223047;
    color: #c8d4e8;
    padding: 16px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.summary-icon {
    color: #a6edf4;
    font-size: 16px;
}
.stSlider [data-baseweb="slider"] > div > div {
    background: #a9edf5 !important;
}
.stSlider [data-baseweb="slider"] [aria-valuenow] {
    color: #a9edf5 !important;
}
.stSlider [data-baseweb="slider"] [role="slider"],
.stSlider [data-baseweb="slider"] [aria-valuenow] {
    background: #d8fbff !important;
    border-color: #a9edf5 !important;
    box-shadow: 0 0 0 2px rgba(169, 237, 245, 0.22) !important;
}
.stRadio label, .stMultiSelect label {
    color: #b7c3db !important;
}
.stRadio [role="radiogroup"] {
    gap: 0.85rem;
}
.stRadio [data-baseweb="radio"] {
    accent-color: #a9edf5 !important;
}
.stPills {
    margin-top: 2px;
}
.stRadio [data-baseweb="radio"] label {
    color: #dce4f5 !important;
}
div[data-baseweb="radio"] [role="radio"][aria-checked="true"] {
    border-color: #a9edf5 !important;
    box-shadow: 0 0 0 2px rgba(169, 237, 245, 0.18) !important;
}
div[data-baseweb="radio"] [role="radio"][aria-checked="true"] + div,
div[data-baseweb="radio"] [role="radio"][aria-checked="true"] {
    background-color: #a9edf5 !important;
}
div[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0;
}
</style>
"""
