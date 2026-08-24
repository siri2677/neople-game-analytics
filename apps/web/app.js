const statusElement = document.getElementById("report-status");
const reportContainer = document.getElementById("report-container");

function setStatus(message, error = false) {
  statusElement.textContent = message;
  statusElement.classList.toggle("error", error);
}

async function loadReport() {
  try {
    const response = await fetch("/api/powerbi/embed-config");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Power BI 설정을 가져오지 못했습니다.");
    }
    const models = window["powerbi-client"].models;
    window.powerbi.embed(reportContainer, {
      type: payload.type,
      id: payload.reportId,
      embedUrl: payload.embedUrl,
      accessToken: payload.accessToken,
      tokenType: models.TokenType.Embed,
      permissions: models.Permissions.View,
      settings: {
        panes: { filters: { visible: false }, pageNavigation: { visible: true } },
        navContentPaneEnabled: true,
      },
    });
    setStatus("Power BI 리포트 연결 완료");
  } catch (error) {
    setStatus(error.message, true);
    reportContainer.innerHTML = "<p class='error-panel'>Power BI Service 설정 또는 Embed Token을 확인하세요.</p>";
  }
}

loadReport();
