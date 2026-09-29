/**
 * RazorMind AI — Frontend Interactive Application Logic
 * Integrates Chart.js, Real-time Fraud Simulator, Smart Router, and Conversational Assistant
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Feather Icons
  if (window.feather) {
    feather.replace();
  }

  // Navigation Tabs
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanels = document.querySelectorAll(".tab-panel");

  navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      navTabs.forEach(t => t.classList.remove("active"));
      tabPanels.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const activePanel = document.getElementById(`tab-${target}`);
      if (activePanel) {
        activePanel.classList.add("active");
      }
    });
  });

  // Global Chart References
  let trendChartInstance = null;
  let methodChartInstance = null;

  // Dynamic API Base URL resolution:
  // If served directly from FastAPI (port 8000), use relative paths ("/api/...").
  // If served from Live Server (port 5500), Vite (3000/5173), or file://, link directly to http://127.0.0.1:8000.
  const API_BASE = (window.location.port === "8000") ? "" : "http://127.0.0.1:8000";

  // Backend Heartbeat & Live Relink Status
  const statusLabel = document.getElementById("connectionStatus");
  const livePulseDot = document.getElementById("livePulseDot") || document.querySelector(".pulse-dot");
  const btnRelink = document.getElementById("btnRelink");
  const apiDocsLink = document.getElementById("apiDocsLink");
  if (apiDocsLink) {
    apiDocsLink.href = `${API_BASE || ''}/docs`;
  }

  async function checkBackendHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
      if (res.ok) {
        if (statusLabel) {
          statusLabel.innerText = "LIVE • CONNECTED";
          statusLabel.style.color = "var(--emerald)";
        }
        if (livePulseDot) {
          livePulseDot.style.background = "var(--emerald)";
          livePulseDot.style.boxShadow = "0 0 10px rgba(16, 185, 129, 0.7)";
        }
        return true;
      }
    } catch (e) {
      if (statusLabel) {
        statusLabel.innerText = "OFFLINE • CLICK RELINK";
        statusLabel.style.color = "var(--crimson)";
      }
      if (livePulseDot) {
        livePulseDot.style.background = "var(--crimson)";
        livePulseDot.style.boxShadow = "0 0 10px rgba(239, 68, 68, 0.7)";
      }
      return false;
    }
  }

  // ================= 1. OVERVIEW & METRICS =================
  async function loadOverviewData() {
    try {
      const [overviewRes, trendsRes, banksRes, methodsRes, diagnosisRes] = await Promise.all([
        fetch(`${API_BASE}/api/analytics/overview`).then(r => r.json()),
        fetch(`${API_BASE}/api/analytics/trends?days=14`).then(r => r.json()),
        fetch(`${API_BASE}/api/analytics/banks`).then(r => r.json()),
        fetch(`${API_BASE}/api/analytics/methods`).then(r => r.json()),
        fetch(`${API_BASE}/api/analytics/revenue-diagnosis`).then(r => r.json())
      ]);

      // Populate KPIs
      document.getElementById("kpiGmv").innerText = `₹${overviewRes.total_gmv.toLocaleString('en-IN')}`;
      document.getElementById("kpiTxCount").innerText = overviewRes.captured_count.toLocaleString('en-IN');
      document.getElementById("kpiSuccessRate").innerText = `${overviewRes.success_rate}%`;
      document.getElementById("successProgress").style.width = `${overviewRes.success_rate}%`;
      document.getElementById("kpiPrevented").innerText = `₹${overviewRes.fraud_prevented_gmv.toLocaleString('en-IN')}`;
      document.getElementById("kpiFraudCount").innerText = overviewRes.fraud_count;
      document.getElementById("kpiFailedGmv").innerText = `₹${overviewRes.failed_gmv.toLocaleString('en-IN')}`;
      document.getElementById("kpiFailedCount").innerText = overviewRes.failed_count;

      // Render Charts
      renderTrendChart(trendsRes);
      renderPaymentMethodChart(methodsRes);
      renderBankHealth(banksRes);
      renderRootCause(diagnosisRes);

    } catch (err) {
      console.error("Error loading overview metrics:", err);
    }
  }

  function renderTrendChart(trends) {
    const ctx = document.getElementById("revenueTrendChart").getContext("2d");
    const labels = trends.map(t => t.tx_date.slice(5));
    const gmvData = trends.map(t => t.captured_revenue);
    const successData = trends.map(t => t.success_rate);

    if (trendChartInstance) trendChartInstance.destroy();

    trendChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Processed GMV (₹)",
            data: gmvData,
            borderColor: "#0c8ce9",
            backgroundColor: "rgba(12, 140, 233, 0.1)",
            fill: true,
            tension: 0.35,
            yAxisID: "y"
          },
          {
            label: "Success Rate (%)",
            data: successData,
            borderColor: "#10b981",
            borderDash: [5, 5],
            tension: 0.2,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } } }
        },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#64748b", callback: v => "₹" + (v/1000) + "k" }
          },
          y1: {
            position: "right",
            grid: { display: false },
            ticks: { color: "#10b981", callback: v => v + "%" },
            min: 50,
            max: 100
          }
        }
      }
    });
  }

  function renderPaymentMethodChart(methods) {
    const ctx = document.getElementById("paymentMethodChart").getContext("2d");
    const labels = methods.map(m => m.payment_method.toUpperCase().replace("_", " "));
    const data = methods.map(m => m.volume_inr);

    if (methodChartInstance) methodChartInstance.destroy();

    methodChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: ["#0c8ce9", "#3b82f6", "#60a5fa", "#8b5cf6", "#10b981"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 } } }
        },
        cutout: "68%"
      }
    });
  }

  function renderBankHealth(banks) {
    const container = document.getElementById("bankList");
    container.innerHTML = "";

    banks.forEach(b => {
      const rateClass = b.success_rate >= 85 ? "high" : b.success_rate >= 70 ? "mid" : "low";
      const div = document.createElement("div");
      div.className = "bank-item";
      div.innerHTML = `
        <div class="bank-meta">
          <span class="bank-badge">${b.bank_code}</span>
          <span style="font-size: 13px; color: var(--text-secondary);">${b.total_tx} txns</span>
        </div>
        <div style="text-align: right;">
          <div class="bank-success-val ${rateClass}">${b.success_rate}% Success</div>
          <div style="font-size: 11px; color: var(--text-muted);">${b.downtime_incidents} outages</div>
        </div>
      `;
      container.appendChild(div);
    });
  }

  function renderRootCause(diagnosis) {
    const container = document.getElementById("rootCauseBox");
    const rootCauses = diagnosis.root_causes || [];
    const loss = diagnosis.loss_summary || {};

    if (rootCauses.length === 0) {
      container.innerHTML = `<div class="rc-desc">Network running with nominal latency. No anomalous gateway failure spikes detected.</div>`;
      return;
    }

    const top = rootCauses[0];
    container.innerHTML = `
      <div class="root-cause-item">
        <div class="rc-title">🚨 ${top.bank_code} (${top.payment_method.toUpperCase()}) Gateway Surge</div>
        <div class="rc-desc">
          Failure rate reached <strong>${top.failure_rate}%</strong>, accounting for 
          <strong>₹${Number(top.lost_revenue).toLocaleString('en-IN')}</strong> in lost merchant GMV.
        </div>
      </div>
      <div style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
        Total failed revenue across all causes: ₹${Number(loss.total_lost_revenue || 0).toLocaleString('en-IN')}
      </div>
    `;
  }

  // ================= 2. REAL-TIME FRAUD SIMULATOR =================
  const fraudForm = document.getElementById("fraudSimForm");
  const gaugeScore = document.getElementById("gaugeScore");
  const riskGauge = document.getElementById("riskGauge");
  const decisionBanner = document.getElementById("decisionBanner");
  const decisionTier = document.getElementById("decisionTier");
  const decisionAction = document.getElementById("decisionAction");
  const factorsList = document.getElementById("factorsList");
  const simTimestamp = document.getElementById("simTimestamp");

  // Presets
  document.getElementById("btnPresetFraud").addEventListener("click", () => {
    document.getElementById("simAmount").value = 48500;
    document.getElementById("simMethod").value = "card_credit";
    document.getElementById("simBank").value = "HDFC";
    document.getElementById("simVelocity1h").value = 5;
    document.getElementById("simRatio").value = 4.8;
    document.getElementById("simGeoDistance").value = 1450;
    document.getElementById("simHour").value = 2;
    document.getElementById("simVpn").checked = true;
    fraudForm.dispatchEvent(new Event("submit"));
  });

  document.getElementById("btnPresetNormal").addEventListener("click", () => {
    document.getElementById("simAmount").value = 1200;
    document.getElementById("simMethod").value = "upi";
    document.getElementById("simBank").value = "ICICI";
    document.getElementById("simVelocity1h").value = 0;
    document.getElementById("simRatio").value = 1.0;
    document.getElementById("simGeoDistance").value = 0;
    document.getElementById("simHour").value = 15;
    document.getElementById("simVpn").checked = false;
    fraudForm.dispatchEvent(new Event("submit"));
  });

  fraudForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      amount: parseFloat(document.getElementById("simAmount").value),
      payment_method: document.getElementById("simMethod").value,
      bank_code: document.getElementById("simBank").value,
      device_type: document.getElementById("simDevice").value,
      velocity_1h: parseInt(document.getElementById("simVelocity1h").value),
      velocity_24h: parseInt(document.getElementById("simVelocity1h").value) + 2,
      amount_to_avg_ratio: parseFloat(document.getElementById("simRatio").value),
      geo_distance_km: parseFloat(document.getElementById("simGeoDistance").value),
      is_vpn_or_proxy: document.getElementById("simVpn").checked ? 1 : 0,
      hour_of_day: parseInt(document.getElementById("simHour").value),
      day_of_week: new Date().getDay()
    };

    try {
      const res = await fetch(`${API_BASE}/api/fraud/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      gaugeScore.innerText = data.risk_score;
      simTimestamp.innerText = `Evaluated in 14ms`;

      // Update Gauge Glow & Tier
      decisionBanner.className = `decision-banner ${data.risk_tier}`;
      decisionTier.innerText = `${data.risk_tier} RISK TIER`;
      decisionAction.innerText = `Recommended Policy: ${data.decision}`;

      // Update Factor List
      factorsList.innerHTML = "";
      data.top_risk_factors.forEach(factor => {
        const li = document.createElement("li");
        li.innerText = factor;
        factorsList.appendChild(li);
      });

    } catch (err) {
      console.error("Fraud eval error:", err);
    }
  });

  // ================= 3. PAYMENT SUCCESS & SMART ROUTER =================
  const btnTestRoute = document.getElementById("btnTestRoute");
  const nodeOriginalName = document.getElementById("nodeOriginalName");
  const nodeOriginalHealth = document.getElementById("nodeOriginalHealth");
  const nodeFallbackName = document.getElementById("nodeFallbackName");
  const nodeFallbackHealth = document.getElementById("nodeFallbackHealth");
  const switchArrow = document.getElementById("switchArrow");
  const routeHeadline = document.getElementById("routeHeadline");
  const altTbody = document.getElementById("alternativesTableBody");

  btnTestRoute.addEventListener("click", async () => {
    const bank = document.getElementById("routerBank").value;
    const method = document.getElementById("routerMethod").value;
    const amount = parseFloat(document.getElementById("routerAmount").value);

    try {
      const res = await fetch(`${API_BASE}/api/predict/success`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bank_code: bank,
          payment_method: method,
          amount: amount,
          hour_of_day: 14,
          day_of_week: 2
        })
      });
      const data = await res.json();

      nodeOriginalName.innerText = `${data.current_route.bank_code} (${data.current_route.payment_method.toUpperCase()})`;
      nodeOriginalHealth.innerText = `Success: ${data.current_route.predicted_success_rate}%`;
      nodeOriginalHealth.className = `node-health ${data.current_route.predicted_success_rate < 75 ? 'danger' : 'success'}`;

      if (data.smart_route_recommended && data.recommended_fallback) {
        nodeFallbackName.innerText = data.recommended_fallback;
        nodeFallbackHealth.innerText = `Success: ${data.expected_success_rate}%`;
        switchArrow.style.opacity = "1";
        routeHeadline.innerHTML = `<strong>Optimizer Action:</strong> ${data.recommendation_reason}`;
      } else {
        nodeFallbackName.innerText = "Direct Routing";
        nodeFallbackHealth.innerText = "Nominal Gateway";
        switchArrow.style.opacity = "0.4";
        routeHeadline.innerText = data.recommendation_reason;
      }

      // Populate Alternatives Table
      altTbody.innerHTML = "";
      data.evaluated_alternatives.forEach(alt => {
        const tr = document.createElement("tr");
        const isOptimal = alt.route === data.recommended_fallback;
        tr.innerHTML = `
          <td><strong>${alt.route}</strong></td>
          <td style="color: var(--emerald); font-weight: 700;">${alt.predicted_success_rate}%</td>
          <td style="color: var(--text-secondary);">${alt.failure_rate}%</td>
          <td>
            <span class="badge-tag ${isOptimal ? 'pulse' : ''}">
              ${isOptimal ? 'Recommended Route' : 'Backup'}
            </span>
          </td>
        `;
        altTbody.appendChild(tr);
      });

    } catch (err) {
      console.error("Router error:", err);
    }
  });

  // ================= 4. AI MERCHANT ASSISTANT CHAT =================
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatLog = document.getElementById("chatLog");
  const chips = document.querySelectorAll(".prompt-chips .chip");

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      const text = chip.getAttribute("data-prompt");
      chatInput.value = text;
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Append User Message
    appendChatMessage("user", query);
    chatInput.value = "";

    // Show Bot Typing Indicator
    const typingIndicator = appendChatMessage("bot", "Analyzing platform risk data and financial trends...");

    try {
      const res = await fetch(`${API_BASE}/api/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query })
      });
      const data = await res.json();
      typingIndicator.remove();

      // Format Bot Message
      let formattedHtml = `<p>${formatMarkdown(data.direct_answer)}</p>`;

      // Callout Metrics
      if (data.key_metrics && Object.keys(data.key_metrics).length > 0) {
        formattedHtml += `<div class="chat-callout"><div class="callout-title">KEY FINANCIAL METRICS</div><div class="callout-metrics">`;
        for (const [k, v] of Object.entries(data.key_metrics)) {
          const cleanKey = k.replace(/_/g, " ").toUpperCase();
          formattedHtml += `<div class="metric-pill"><span>${cleanKey}:</span> <strong>${v}</strong></div>`;
        }
        formattedHtml += `</div></div>`;
      }

      // Recommendations
      if (data.actionable_recommendations && data.actionable_recommendations.length > 0) {
        formattedHtml += `<p style="margin-top: 8px; font-weight: 600; color: var(--emerald);">Actionable Recommendations:</p><ul>`;
        data.actionable_recommendations.forEach(rec => {
          formattedHtml += `<li>${rec}</li>`;
        });
        formattedHtml += `</ul>`;
      }

      appendChatMessage("bot", formattedHtml, true);

    } catch (err) {
      typingIndicator.remove();
      appendChatMessage("bot", "Sorry, an error occurred while generating intelligence insights.");
    }
  });

  function appendChatMessage(sender, content, isHtml = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}`;
    const icon = sender === "bot" ? "bot" : "user";
    
    msgDiv.innerHTML = `
      <div class="msg-avatar"><i data-feather="${icon}"></i></div>
      <div class="msg-content">${isHtml ? content : `<p>${content}</p>`}</div>
    `;
    chatLog.appendChild(msgDiv);
    if (window.feather) feather.replace();
    chatLog.scrollTop = chatLog.scrollHeight;
    return msgDiv;
  }

  function formatMarkdown(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\*(.*?)\*/g, '<em>$1</em>');
  }

  // ================= 5. TRANSACTION AUDIT STREAM =================
  async function loadTransactions() {
    const status = document.getElementById("filterStatus").value;
    const fraud = document.getElementById("filterFraud").value;
    const tbody = document.getElementById("txTableBody");

    let url = `${API_BASE}/api/transactions?limit=30`;
    if (status) url += `&status=${status}`;
    if (fraud) url += `&is_fraud=${fraud}`;

    try {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center">Loading transactions...</td></tr>`;
      const res = await fetch(url);
      const data = await res.json();

      tbody.innerHTML = "";
      if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center">No transactions matching filter</td></tr>`;
        return;
      }

      data.forEach(tx => {
        const tr = document.createElement("tr");
        const statusClass = tx.status;
        const riskTier = tx.risk_score >= 75 ? "high" : tx.risk_score >= 40 ? "mid" : "low";
        
        tr.innerHTML = `
          <td><code style="color: var(--razor-blue); font-weight: 600;">${tx.transaction_id}</code></td>
          <td><strong>₹${tx.amount.toLocaleString('en-IN')}</strong></td>
          <td>${tx.payment_method.toUpperCase()}</td>
          <td><span class="bank-badge">${tx.bank_code}</span></td>
          <td><span class="status-badge ${statusClass}">${tx.status.toUpperCase()}</span></td>
          <td><span style="font-size: 12px; color: var(--text-muted);">${tx.failure_reason || '—'}</span></td>
          <td><span class="risk-pill ${riskTier}">${tx.risk_score}</span></td>
          <td>${tx.is_fraud ? '<span class="status-badge failed">FRAUD</span>' : '<span style="color: var(--text-muted);">0</span>'}</td>
          <td><span style="font-size: 11px; color: var(--text-muted);">${tx.created_at.slice(0, 19).replace('T', ' ')}</span></td>
        `;
        tbody.appendChild(tr);
      });

    } catch (err) {
      console.error("Tx load error:", err);
    }
  }

  document.getElementById("btnRefreshTx").addEventListener("click", loadTransactions);
  document.getElementById("filterStatus").addEventListener("change", loadTransactions);
  document.getElementById("filterFraud").addEventListener("change", loadTransactions);

  // Relink & Refresh Dashboard
  async function relinkDashboard() {
    if (btnRelink) {
      btnRelink.innerHTML = `<i data-feather="loader"></i> Relinking...`;
      if (window.feather) feather.replace();
    }
    await checkBackendHealth();
    await Promise.all([loadOverviewData(), loadTransactions()]);
    if (btnRelink) {
      setTimeout(() => {
        btnRelink.innerHTML = `<i data-feather="check"></i> Linked`;
        if (window.feather) feather.replace();
        setTimeout(() => {
          btnRelink.innerHTML = `<i data-feather="refresh-cw"></i> Relink`;
          if (window.feather) feather.replace();
        }, 1200);
      }, 400);
    }
  }

  if (btnRelink) {
    btnRelink.addEventListener("click", (e) => {
      e.stopPropagation();
      relinkDashboard();
    });
  }

  const navStatusBadge = document.getElementById("navStatusBadge");
  if (navStatusBadge) {
    navStatusBadge.addEventListener("click", () => {
      relinkDashboard();
    });
  }

  // Periodic heartbeat every 10 seconds to keep dashboard linked
  setInterval(checkBackendHealth, 10000);

  // Initial Load & Health Check
  checkBackendHealth();
  loadOverviewData();
  loadTransactions();
});
