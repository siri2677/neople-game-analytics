const DATA_PATHS = ["/api/dashboard", "data/dashboard.json", "data/demo.json"];

const $ = (selector) => document.querySelector(selector);

const formatNumber = (value, suffix = "") => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(Number(value))}${suffix}`;
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "'": "&#39;",
  '"': "&quot;",
}[character]));

const emptyState = (message) => `<div class="empty-state">${message}</div>`;

function renderBars(target, rows, labelKey, valueKey, formatter, tone = "green") {
  const element = $(target);
  if (!rows?.length) {
    element.innerHTML = emptyState("아직 표시할 데이터가 없습니다.");
    return;
  }
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  element.innerHTML = rows.map((row) => {
    const value = Number(row[valueKey]) || 0;
    const width = Math.max(5, Math.round((value / max) * 100));
    const label = escapeHtml(row[labelKey] ?? "미분류");
    return `<div class="bar-row">
      <span class="bar-label" title="${label}">${label}</span>
      <span class="bar-track"><span class="bar-fill ${tone === "orange" ? "orange" : ""}" style="width:${width}%"></span></span>
      <strong class="bar-value">${formatter(value)}</strong>
    </div>`;
  }).join("");
}

function renderRanks(target, rows) {
  const element = $(target);
  if (!rows?.length) {
    element.innerHTML = emptyState("아직 표시할 데이터가 없습니다.");
    return;
  }
  element.innerHTML = rows.slice(0, 6).map((row, index) => `
    <div class="rank-item">
      <span class="rank-number">0${index + 1}</span>
      <span class="rank-name" title="${escapeHtml(row.item_name)}">${escapeHtml(row.item_name)}</span>
      <span class="rank-meta">${formatNumber(row.median_price)}<br />${formatNumber(row.observations)}건</span>
    </div>
  `).join("");
}

function render(data) {
  const summary = data.summary || {};
  $("#sourceBadge").textContent = data.source === "processed" ? "LIVE CSV DATA" : "DEMO DATA";
  $("#generatedAt").textContent = data.generated_at
    ? `UPDATED ${new Date(data.generated_at).toLocaleDateString("ko-KR")}`
    : "STATIC PREVIEW";
  $("#dnfCharacters").textContent = formatNumber(summary.dnf_characters);
  $("#dnfMedianFame").textContent = formatNumber(summary.dnf_median_fame);
  $("#cyphersMatches").textContent = formatNumber(summary.cyphers_matches);
  $("#cyphersWinRate").textContent = formatNumber(summary.cyphers_win_rate, "%");
  $("#dnfJobCount").textContent = formatNumber(data.dnf?.jobs?.length);
  $("#dnfAuctionCount").textContent = formatNumber(summary.dnf_auction_items);
  $("#cyphersCharacterCount").textContent = formatNumber(data.cyphers?.characters?.length);
  $("#cyphersItemCount").textContent = formatNumber(data.cyphers?.items?.length);

  renderBars("#jobChart", data.dnf?.jobs, "job_name", "median_fame", (value) => formatNumber(value), "green");
  renderRanks("#auctionList", data.dnf?.auctions);
  renderBars("#characterChart", data.cyphers?.characters, "character_name", "win_rate", (value) => formatNumber(value, "%"), "orange");
}

async function loadData() {
  for (const path of DATA_PATHS) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) {
        render(await response.json());
        return;
      }
    } catch (error) {
      // Try the demo payload next. The dashboard remains static-host friendly.
    }
  }
  $("#loadError").hidden = false;
}

function setupViewSwitcher() {
  const buttons = document.querySelectorAll(".view-button");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      buttons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-selected", String(active));
      });
      document.querySelectorAll("[data-panel]").forEach((panel) => {
        panel.hidden = view !== "all" && panel.dataset.panel !== "all" && panel.dataset.panel !== view;
      });
      document.querySelectorAll("[data-detail]").forEach((section) => {
        section.hidden = view === "all" || section.dataset.detail !== view;
      });
    });
  });
}

setupViewSwitcher();
loadData();
