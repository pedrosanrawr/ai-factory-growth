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
