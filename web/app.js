const DATA_PATHS = ["data/dashboard.json", "data/demo.json"];

const $ = (selector) => document.querySelector(selector);
let dashboardData = null;

const formatNumber = (value, suffix = "") => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return `${new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(Number(value))}${suffix}`;
};

const formatPercent = (value) => formatNumber(value, "%");

const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "'": "&#39;",
  '"': "&quot;",
}[character]));

const emptyState = (message = "아직 표시할 데이터가 없습니다.") => `<div class="empty-state">${escapeHtml(message)}</div>`;

function renderBars(target, rows, labelKey, valueKey, formatter, tone = "green") {
  const element = $(target);
  if (!element) return;
  if (!rows?.length) {
    element.innerHTML = emptyState();
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

function renderOverview(data) {
  const summary = data.summary || {};
  $("#sourceBadge").textContent = data.source === "processed" ? "LIVE CSV DATA" : "DEMO DATA";
  $("#generatedAt").textContent = data.generated_at
    ? `UPDATED ${new Date(data.generated_at).toLocaleDateString("ko-KR")}`
    : "STATIC PREVIEW";
  $("#dnfCharacters").textContent = formatNumber(summary.dnf_characters);
  $("#dnfMedianFame").textContent = formatNumber(summary.dnf_median_fame);
  $("#cyphersMatches").textContent = formatNumber(summary.cyphers_matches);
  $("#cyphersWinRate").textContent = formatPercent(summary.cyphers_win_rate);
  $("#dnfJobCount").textContent = formatNumber(summary.dnf_characters);
  $("#dnfAuctionCount").textContent = formatNumber(summary.dnf_auction_items);
  $("#dnfTimelineCount").textContent = formatNumber(summary.dnf_timeline_events);
  $("#cyphersCharacterCount").textContent = formatNumber(summary.cyphers_characters);
  $("#cyphersItemCount").textContent = formatNumber(summary.cyphers_items);
  $("#cyphersMinItemMatches").textContent = formatNumber(data.quality?.minimum_cyphers_item_matches);

  renderBars("#jobChart", data.dnf?.jobs, "job_name", "median_fame", formatNumber, "green");
  renderBars("#characterChart", data.cyphers?.characters, "character_name", "win_rate", formatPercent, "orange");
  renderRanks("#auctionList", data.dnf?.auctions, (row) => `${formatNumber(row.median_price)} · ${formatNumber(row.observations)}건`);
}

function renderRanks(target, rows, meta) {
  const element = $(target);
  if (!element) return;
  if (!rows?.length) {
    element.innerHTML = emptyState();
    return;
  }
  element.innerHTML = rows.slice(0, 8).map((row, index) => `
    <div class="rank-item">
      <span class="rank-number">${String(index + 1).padStart(2, "0")}</span>
      <span class="rank-name" title="${escapeHtml(row.item_name ?? row.event_name)}">${escapeHtml(row.item_name ?? row.event_name)}</span>
      <span class="rank-meta">${escapeHtml(meta ? meta(row) : "")}</span>
    </div>
  `).join("");
}

function renderTable(target, headers, rows, emptyMessage = "아직 표시할 데이터가 없습니다.") {
  const element = $(target);
  if (!element) return;
  if (!rows?.length) {
    element.innerHTML = emptyState(emptyMessage);
    return;
  }
  element.innerHTML = `<table><thead><tr>${headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
}

function renderDnf(data) {
  if (!data) return;
  const dnf = data.dnf || {};
  renderBars("#fameBandChart", dnf.fame_bands, "band", "characters", formatNumber, "green");

  renderRanks("#equipmentList", dnf.equipment, (row) => `${formatPercent(row.adoption_rate)} · 명성 ${formatNumber(row.median_fame)}`);
  renderRanks("#timelineList", dnf.timeline, (row) => `${formatNumber(row.events)}건 · ${formatNumber(row.characters)}명`);

  const jobFilter = String($("#dnfJobFilter")?.value || "").trim().toLowerCase();
  const jobs = (dnf.jobs || []).filter((row) => String(row.job_name || "").toLowerCase().includes(jobFilter));
  const jobTable = $("#jobTable tbody");
  if (jobTable) {
    jobTable.innerHTML = jobs.length
      ? jobs.map((row) => `<tr><th scope="row">${escapeHtml(row.job_name)}</th><td>${formatNumber(row.characters)}</td><td>${formatNumber(row.median_fame)}</td><td>${formatNumber(row.iqr_fame)}</td><td>${formatNumber(row.average_fame)}</td></tr>`).join("")
      : `<tr><td colspan="5">${emptyState("검색 조건에 맞는 직업이 없습니다.")}</td></tr>`;
  }

  const sortMode = $("#auctionSort")?.value || "median";
  const auctions = [...(dnf.auctions || [])].sort((left, right) => {
    if (sortMode === "volatility") return (right.price_cv || 0) - (left.price_cv || 0);
    if (sortMode === "observations") return (right.observations || 0) - (left.observations || 0);
    return (right.median_price || 0) - (left.median_price || 0);
  });
  renderTable("#auctionTable", ["아이템", "관측 수", "중앙값", "IQR", "CV"], auctions.slice(0, 12).map((row) => `<tr><th scope="row">${escapeHtml(row.item_name)}</th><td>${formatNumber(row.observations)}</td><td>${formatNumber(row.median_price)}</td><td>${formatNumber(row.price_iqr)}</td><td>${formatNumber(row.price_cv)}</td></tr>`));
}

function renderCyphers(data) {
  if (!data) return;
  const cyphers = data.cyphers || {};
  const minMatches = Number($("#cyphersMinMatches")?.value || 0);
  const enoughOnly = Boolean($("#cyphersEnoughOnly")?.checked);
  const characters = (cyphers.characters || []).filter((row) => (row.matches || 0) >= minMatches);
  renderTable("#cyphersCharacterTable", ["캐릭터", "경기", "승률", "평균 킬", "평균 도움"], characters.map((row) => `<tr><th scope="row">${escapeHtml(row.character_name)}</th><td>${formatNumber(row.matches)}</td><td>${formatPercent(row.win_rate)}</td><td>${formatNumber(row.average_kills)}</td><td>${formatNumber(row.average_assists)}</td></tr>`));

  renderRanks("#cyphersItemList", cyphers.items, (row) => `${formatNumber(row.matches)}경기 · ${formatPercent(row.win_rate)}`);
  const itemPerformance = (cyphers.item_performance || []).filter((row) => !enoughOnly || row.enough_sample);
  renderTable("#cyphersItemPerformance", ["캐릭터", "아이템", "경기", "조합 승률", "기준 승률", "차이"], itemPerformance.map((row) => {
    const lift = row.lift_pp === null || row.lift_pp === undefined ? "—" : `${row.lift_pp > 0 ? "+" : ""}${formatNumber(row.lift_pp, " pp")}`;
    const sampleClass = row.enough_sample ? "sample-ok" : "sample-warning";
    return `<tr><th scope="row">${escapeHtml(row.character_name)}</th><td>${escapeHtml(row.item_name)}</td><td>${formatNumber(row.matches)}</td><td>${formatPercent(row.win_rate)}</td><td>${formatPercent(row.character_win_rate)}</td><td class="${sampleClass}">${lift}${row.enough_sample ? "" : " · 표본 부족"}</td></tr>`;
  }), "아이템 상세 데이터가 없습니다.");
}

function setView(view) {
  document.querySelectorAll(".view-button").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = view !== "all" && panel.dataset.panel !== "all" && panel.dataset.panel !== view;
  });
  document.querySelectorAll("[data-detail]").forEach((section) => {
    section.hidden = view === "all" || section.dataset.detail !== view;
  });
}

function setupInteractions() {
  document.querySelectorAll(".view-button").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  $("#dnfJobFilter")?.addEventListener("input", () => renderDnf(dashboardData));
  $("#auctionSort")?.addEventListener("change", () => renderDnf(dashboardData));
  $("#cyphersMinMatches")?.addEventListener("change", () => renderCyphers(dashboardData));
  $("#cyphersEnoughOnly")?.addEventListener("change", () => renderCyphers(dashboardData));
}

async function loadData() {
  for (const path of DATA_PATHS) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) {
        dashboardData = await response.json();
        renderOverview(dashboardData);
        renderDnf(dashboardData);
        renderCyphers(dashboardData);
        return;
      }
    } catch (error) {
      // Try the demo payload next. The dashboard remains static-host friendly.
    }
  }
  $("#loadError").hidden = false;
}

setupInteractions();
setView("all");
loadData();
