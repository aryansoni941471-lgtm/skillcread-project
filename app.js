/**
 * नगर Drishti (Civic Incident Intelligence Platform)
 * Frontend Interactive Controller & AI Intelligence Hub
 */

// Global State
const State = {
  currentTab: 'officer-dashboard', // 'officer-dashboard' | 'citizen-portal' | 'briefing-studio'
  complaints: [],
  spikes: [],
  clusters: [],
  summaryMetrics: {},
  trendsData: null,
  mapInstance: null,
  mapMarkers: [],
  mapHeatLayer: null,
  charts: {
    trends: null,
    categories: null,
    localities: null
  },
  currentUser: JSON.parse(localStorage.getItem('nagar_user')) || {
    full_name: 'Superintendent V. Sharma',
    role: 'officer',
    department: 'Municipal Operations Command'
  },
  filters: {
    category: 'All',
    department: 'All',
    status: 'All',
    locality: 'All',
    severity: 'All',
    search: ''
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initAuthUI();
  initMap();
  initCharts();
  bindEvents();
  fetchDashboardData();
  
  // Auto refresh every 30 seconds
  setInterval(() => {
    fetchDashboardData(true);
  }, 30000);
});

// ====================================================================
// Authentication & User Profile UI
// ====================================================================
function initAuthUI() {
  const profileName = document.getElementById('userProfileName');
  const roleBadge = document.getElementById('userRoleBadge');
  const officerNavBtn = document.getElementById('tabBtnOfficer');
  const citizenNavBtn = document.getElementById('tabBtnCitizen');

  if (profileName) profileName.textContent = State.currentUser.full_name;
  if (roleBadge) roleBadge.textContent = State.currentUser.role.toUpperCase();

  // If citizen, default to Citizen Portal
  if (State.currentUser.role === 'citizen') {
    switchTab('citizen-portal');
  }
}

function toggleRole() {
  if (State.currentUser.role === 'officer') {
    State.currentUser = {
      full_name: 'Aarav Sharma (Citizen)',
      role: 'citizen',
      department: 'Ward 12 Resident'
    };
    switchTab('citizen-portal');
  } else {
    State.currentUser = {
      full_name: 'Superintendent V. Sharma',
      role: 'officer',
      department: 'Municipal Operations Command'
    };
    switchTab('officer-dashboard');
  }
  localStorage.setItem('nagar_user', JSON.stringify(State.currentUser));
  initAuthUI();
  showToast(`Switched mode to ${State.currentUser.role.toUpperCase()}`, 'info');
}

// ====================================================================
// Map Initialization (Leaflet with Light Emerald & Voyager Styling)
// ====================================================================
function initMap() {
  const mapElem = document.getElementById('civicMap');
  if (!mapElem) return;

  // Center on Capital Metropolitan Area
  State.mapInstance = L.map('civicMap', {
    zoomControl: true,
    attributionControl: false
  }).setView([28.6250, 77.2150], 12);

  // Modern Clean Light CartoDB Voyager Tiles matching emerald/teal aesthetics
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(State.mapInstance);

  // Invalidate map size on window resize
  window.addEventListener('resize', () => {
    if (State.mapInstance) State.mapInstance.invalidateSize();
  });
}

function updateMapMarkers(complaints, spikes) {
  if (!State.mapInstance) return;

  // Clear existing markers
  State.mapMarkers.forEach(m => State.mapInstance.removeLayer(m));
  State.mapMarkers = [];

  // Severity color mapper
  const getSevColor = (sev) => {
    switch (sev) {
      case 5: return '#dc2626';
      case 4: return '#d97706';
      case 3: return '#0284c7';
      default: return '#059669';
    }
  };

  // Add Spike Circles (Pulsing Area Hotspots)
  spikes.forEach(spike => {
    const pulseCircle = L.circleMarker([spike.latitude, spike.longitude], {
      radius: 28,
      color: '#dc2626',
      fillColor: '#fee2e2',
      fillOpacity: 0.45,
      weight: 2.5,
      dashArray: '5, 5'
    }).addTo(State.mapInstance);

    pulseCircle.bindPopup(`
      <div class="custom-popup-title">🚨 CRITICAL SPIKE: ${spike.locality}</div>
      <div class="custom-popup-body">
        <strong>${spike.category}</strong><br>
        📈 Volume Surge: <strong>+${spike.surge_percentage}%</strong> (Z-Score: +${spike.z_score})<br>
        📋 Incidents Reported: <strong>${spike.current_count}</strong><br>
        <span style="color:#dc2626; font-size:11px; font-weight:600;">Supporting Evidence: ${spike.evidence_rows.join(', ')}</span>
      </div>
    `);
    State.mapMarkers.push(pulseCircle);
  });

  // Add Individual Incident Markers
  complaints.forEach(c => {
    const color = getSevColor(c.severity);
    const marker = L.circleMarker([c.latitude, c.longitude], {
      radius: c.severity >= 4 ? 8 : 6,
      fillColor: color,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(State.mapInstance);

    marker.bindPopup(`
      <div class="custom-popup-title">${c.id}: ${c.category}</div>
      <div class="custom-popup-body">
        <strong>${c.title}</strong><br>
        📍 Locality: ${c.locality}<br>
        ⚠️ Severity: <strong>${c.severity}/5</strong> | Status: <span class="status-badge status-${c.status.replace(' ', '-')}">${c.status}</span><br>
        ⏱️ SLA: ${c.sla_hours} hrs | 👍 Upvotes: ${c.upvotes}<br>
        <p style="margin-top:4px; font-size:11px; color:#475569;">${c.description}</p>
      </div>
    `);
    State.mapMarkers.push(marker);
  });
}

// ====================================================================
// Charts Initialization (Chart.js - Light Theme)
// ====================================================================
function initCharts() {
  const trendsCtx = document.getElementById('chartTrends');
  const catCtx = document.getElementById('chartCategories');

  Chart.defaults.color = '#475569';
  Chart.defaults.font.family = "'Outfit', sans-serif";

  // 1. Time-Series Trends Chart (Current 24h vs Historical Baseline)
  if (trendsCtx) {
    State.charts.trends = new Chart(trendsCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Current 24h Volume',
            data: [],
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.12)',
            fill: true,
            tension: 0.4,
            borderWidth: 2.5,
            pointBackgroundColor: '#059669',
            pointRadius: 3.5
          },
          {
            label: '7-Day Baseline Avg',
            data: [],
            borderColor: '#d97706',
            borderDash: [5, 5],
            backgroundColor: 'transparent',
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11, weight: 600 } } },
          tooltip: {
            backgroundColor: '#ffffff',
            titleColor: '#047857',
            bodyColor: '#0f172a',
            borderColor: '#059669',
            borderWidth: 1.5,
            boxPadding: 4
          }
        },
        scales: {
          x: { grid: { color: '#f1f5f9' } },
          y: { grid: { color: '#f1f5f9' }, beginAtZero: true }
        }
      }
    });
  }

  // 2. Category Distribution Donut Chart
  if (catCtx) {
    State.charts.categories = new Chart(catCtx, {
      type: 'doughnut',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: [
            '#059669', '#0284c7', '#d97706', '#dc2626', 
            '#7c3aed', '#db2777', '#2563eb', '#0d9488'
          ],
          borderColor: '#ffffff',
          borderWidth: 2.5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 10, font: { size: 11, weight: 600 } } }
        },
        cutout: '68%'
      }
    });
  }
}

// ====================================================================
// Data Fetching & Sync Engine
// ====================================================================
async function fetchDashboardData(isBackground = false) {
  try {
    const [summaryRes, complaintsRes, spikesRes, clustersRes, trendsRes, catRes] = await Promise.all([
      fetch('/api/analytics/summary').then(r => r.json()),
      fetch(buildComplaintsUrl()).then(r => r.json()),
      fetch('/api/analytics/spikes').then(r => r.json()),
      fetch('/api/analytics/clusters').then(r => r.json()),
      fetch('/api/analytics/trends').then(r => r.json()),
      fetch('/api/analytics/categories').then(r => r.json())
    ]);

    State.summaryMetrics = summaryRes.metrics || {};
    State.complaints = complaintsRes.complaints || [];
    State.spikes = spikesRes.spikes || [];
    State.clusters = clustersRes.clusters || [];

    // Update UI Components
    renderKPICards(State.summaryMetrics);
    renderSpikeAlertBanner(State.spikes);
    renderComplaintsTable(State.complaints);
    renderClustersList(State.clusters);
    renderCitizenFeed(State.complaints);
    updateMapMarkers(State.complaints, State.spikes);
    updateLocalityFilterDropdown(State.complaints);

    // Update Charts
    if (trendsRes.success && State.charts.trends) {
      State.charts.trends.data.labels = trendsRes.labels;
      State.charts.trends.data.datasets[0].data = trendsRes.current_24h;
      State.charts.trends.data.datasets[1].data = trendsRes.historical_baseline;
      State.charts.trends.update();
    }

    if (catRes.success && State.charts.categories) {
      State.charts.categories.data.labels = catRes.categories;
      State.charts.categories.data.datasets[0].data = catRes.counts;
      State.charts.categories.update();
    }

    if (!isBackground) {
      loadOperationsBriefing();
    }
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
  }
}

function buildComplaintsUrl() {
  const params = new URLSearchParams();
  if (State.filters.category !== 'All') params.append('category', State.filters.category);
  if (State.filters.department !== 'All') params.append('department', State.filters.department);
  if (State.filters.status !== 'All') params.append('status', State.filters.status);
  if (State.filters.locality !== 'All') params.append('locality', State.filters.locality);
  if (State.filters.severity !== 'All') params.append('severity', State.filters.severity);
  if (State.filters.search) params.append('search', State.filters.search);
  return `/api/complaints?${params.toString()}`;
}

// ====================================================================
// Render UI Components
// ====================================================================

function renderKPICards(m) {
  document.getElementById('kpiTotalComplaints').textContent = m.total_complaints || 0;
  document.getElementById('kpiActiveSpikes').textContent = m.active_spikes || 0;
  document.getElementById('kpiDuplicateClusters').textContent = m.duplicate_clusters || 0;
  document.getElementById('kpiAvgSla').textContent = `${m.avg_sla_hours || 0} hrs`;
}

function renderSpikeAlertBanner(spikes) {
  const banner = document.getElementById('spikeAlertBanner');
  if (!banner) return;

  if (spikes.length === 0) {
    banner.style.display = 'none';
    return;
  }

  banner.style.display = 'flex';
  const topSpike = spikes[0];
  document.getElementById('bannerSpikeLocality').textContent = `${topSpike.category} Surge in ${topSpike.locality}`;
  document.getElementById('bannerZScore').textContent = `Z-Score: +${topSpike.z_score}`;
  document.getElementById('bannerSpikeDesc').textContent = 
    `Detected ${topSpike.current_count} reports in 24h (+${topSpike.surge_percentage}% over baseline). High incident density logged across ${topSpike.evidence_rows.length} verified rows.`;
}

function renderComplaintsTable(complaints) {
  const tbody = document.getElementById('complaintsTableBody');
  const countBadge = document.getElementById('tableCountBadge');
  if (!tbody) return;

  if (countBadge) countBadge.textContent = `${complaints.length} Records`;

  if (complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 2rem; color: #94a3b8;">No complaints matching current filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = complaints.map(c => {
    const timeFormatted = new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `
      <tr>
        <td><strong style="color:#047857; font-weight:700;">${c.id}</strong></td>
        <td>
          <div style="font-weight:700; color:#0f172a;">${c.title}</div>
          <div style="font-size:12px; color:#475569; max-width:340px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${c.description}</div>
        </td>
        <td><span class="panel-badge" style="font-size:11px;">${c.category}</span></td>
        <td style="font-weight:600; color:#334155;">${c.locality}</td>
        <td>
          <span class="severity-pill sev-${c.severity}">${c.severity}</span>
        </td>
        <td>
          <select class="custom-select" style="padding:0.25rem 0.6rem; font-size:11px; font-weight:600;" onchange="updateComplaintStatus('${c.id}', this.value)">
            <option value="Pending" ${c.status === 'Pending' ? 'selected' : ''}>Pending</option>
            <option value="In Progress" ${c.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
            <option value="Escalated" ${c.status === 'Escalated' ? 'selected' : ''}>Escalated</option>
            <option value="Resolved" ${c.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
          </select>
        </td>
        <td style="color:#475569; font-size:12px; font-weight:500;">${timeFormatted}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="zoomToComplaint(${c.latitude}, ${c.longitude}, '${c.id}')" title="Locate on Map">
            📍 Locate
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function renderClustersList(clusters) {
  const container = document.getElementById('clustersList');
  if (!container) return;

  if (clusters.length === 0) {
    container.innerHTML = `<div style="color:#94a3b8; font-size:12px; text-align:center; padding:1.5rem;">No active duplicate clusters detected.</div>`;
    return;
  }

  container.innerHTML = clusters.map(c => `
    <div class="cluster-card">
      <div class="cluster-card-header">
        <span class="cluster-title">${c.incident_title}</span>
        <span class="cluster-count-badge">🔗 ${c.complaint_count} Clustered</span>
      </div>
      <div class="cluster-meta">
        <span>📍 ${c.locality}</span>
        <span>🏢 ${c.department}</span>
        <span>⚠️ Avg Severity: <strong>${c.avg_severity}/5</strong></span>
        <span>👍 ${c.total_upvotes} Upvotes</span>
      </div>
      <div style="font-size:11px; color:#94a3b8;">Linked Evidence Complaints:</div>
      <div class="cluster-evidence-list">
        ${c.evidence_rows.map(id => `<span class="evidence-tag" onclick="filterByEvidence('${id}')">${id}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

function renderCitizenFeed(complaints) {
  const feed = document.getElementById('citizenFeedContainer');
  if (!feed) return;

  feed.innerHTML = complaints.slice(0, 10).map(c => `
    <div class="kpi-card" style="margin-bottom:0.85rem; padding:1.1rem; border: 1px solid #e2e8f0;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.45rem;">
        <span class="panel-badge" style="font-size:11px;">${c.category}</span>
        <span class="status-badge status-${c.status.replace(' ', '-')}">${c.status}</span>
      </div>
      <h4 style="font-size:0.96rem; font-weight:700; color:#0f172a; margin-bottom:0.35rem;">${c.title}</h4>
      <p style="font-size:0.84rem; color:#475569; margin-bottom:0.65rem; line-height:1.45;">${c.description}</p>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; color:#64748b;">
        <span style="font-weight:600;">📍 ${c.locality} • 👤 ${c.citizen_name}</span>
        <button class="btn btn-secondary btn-sm" onclick="upvoteComplaint('${c.id}', this)">
          👍 <span class="upvote-num">${c.upvotes}</span>
        </button>
      </div>
    </div>
  `).join('');
}

// ====================================================================
// Daily Operations AI Briefing Generator (Strict Evidence Guardrail)
// ====================================================================
async function loadOperationsBriefing() {
  const container = document.getElementById('briefingContentContainer');
  if (!container) return;

  try {
    container.innerHTML = `<div style="text-align:center; padding:2rem; color:#10b981;">Synthesizing evidence-backed operations briefing...</div>`;
    const res = await fetch('/api/briefing/generate').then(r => r.json());
    if (!res.success) throw new Error('Briefing generation failed');

    const b = res.briefing;
    document.getElementById('briefingTimestamp').textContent = `Generated: ${b.generated_at}`;

    let itemsHtml = b.briefing_items.map((item, idx) => {
      const priorityClass = item.priority === 'CRITICAL' || item.priority === 'HIGH' ? 'priority-high' : 
                            item.priority === 'MEDIUM' ? 'priority-medium' : '';
      const pBadgeClass = item.priority === 'CRITICAL' || item.priority === 'HIGH' ? 'p-high' : 
                          item.priority === 'MEDIUM' ? 'p-med' : 'p-low';

      return `
        <div class="briefing-item ${priorityClass}">
          <div class="briefing-item-header">
            <span class="briefing-item-title">${idx + 1}. ${item.headline}</span>
            <span class="briefing-priority-badge ${pBadgeClass}">${item.priority}</span>
          </div>
          <div class="briefing-item-desc">${item.detail}</div>
          <div class="briefing-action-box">
            <span>⚡ <strong>Mandated Action:</strong> ${item.action_item}</span>
          </div>
          ${item.evidence_rows && item.evidence_rows.length > 0 ? `
            <div class="briefing-evidence-row">
              <span>Verified Row Citations:</span>
              ${item.evidence_rows.map(id => `<span class="evidence-tag" onclick="filterByEvidence('${id}')">${id}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="briefing-items-container">
        ${itemsHtml}
      </div>
      <div style="margin-top:1.25rem; padding-top:1rem; border-top:1px solid rgba(16,185,129,0.15); display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:11px; color:#64748b;">Grounded in ${b.total_analyzed_complaints} total records across municipal database.</span>
        <button class="btn btn-primary btn-sm" onclick="window.print()">
          🖨️ Export Briefing (PDF)
        </button>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div style="color:#ef4444; padding:1rem;">Failed to compute daily briefing. Please try again.</div>`;
  }
}

// ====================================================================
// Citizen Real-Time NLP Preview & Form Submission
// ====================================================================
let nlpDebounceTimer = null;

function onComplaintInput() {
  clearTimeout(nlpDebounceTimer);
  nlpDebounceTimer = setTimeout(async () => {
    const title = document.getElementById('citizenTitle').value.trim();
    const desc = document.getElementById('citizenDesc').value.trim();
    if (title.length + desc.length < 5) return;

    try {
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: `${title} ${desc}` })
      }).then(r => r.json());

      document.getElementById('predCategory').textContent = res.category;
      document.getElementById('predDepartment').textContent = res.department;
      document.getElementById('predSeverity').textContent = `${res.severity} / 5`;
      document.getElementById('predSla').textContent = `${res.sla_hours} hrs`;
      document.getElementById('predConfidence').textContent = `${Math.round(res.confidence * 100)}%`;

      // Check for nearby duplicates in state
      const locality = document.getElementById('citizenLocality').value;
      const dupCount = State.complaints.filter(c => c.locality === locality && c.category === res.category).length;
      const dupBox = document.getElementById('duplicateWarningAlert');
      if (dupBox) {
        if (dupCount >= 2) {
          dupBox.style.display = 'flex';
          dupBox.innerHTML = `⚠️ <strong>Notice:</strong> ${dupCount} similar reports in ${locality} recently reported. Your report will be automatically linked to this cluster!`;
        } else {
          dupBox.style.display = 'none';
        }
      }
    } catch (e) {
      console.error(e);
    }
  }, 350);
}

// ====================================================================
// Browser Live Geolocation & Reverse Geocoding Detection
// ====================================================================
function detectLiveLocation() {
  const btn = document.getElementById('btnDetectGps');
  const badge = document.getElementById('gpsStatusBadge');
  const text = document.getElementById('gpsCoordText');
  const addressText = document.getElementById('gpsAddressText');

  if (!navigator.geolocation) {
    showToast('Geolocation is not supported by your browser', 'warning');
    return;
  }

  if (btn) btn.textContent = '⏳ Locating GPS...';

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      const acc = Math.round(position.coords.accuracy || 10);

      document.getElementById('customLat').value = lat;
      document.getElementById('customLon').value = lon;

      if (badge && text) {
        badge.style.display = 'flex';
        text.textContent = `📍 Live GPS Locked: Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)} (±${acc}m accuracy)`;
      }
      if (btn) btn.textContent = '✅ GPS Locked';

      showToast(`📍 GPS Coordinates Locked: ${lat.toFixed(4)}, ${lon.toFixed(4)}`, 'success');

      // Reverse Geocoding via OpenStreetMap Nominatim API
      try {
        if (addressText) addressText.textContent = '🔍 Resolving local area name...';
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`).then(r => r.json());
        
        if (geoRes && geoRes.address) {
          const addr = geoRes.address;
          const detectedArea = addr.suburb || addr.neighbourhood || addr.residential || addr.city_district || addr.city || addr.town || addr.village || addr.county || 'Local Ward';
          const cityOrDistrict = addr.city || addr.town || addr.state_district || '';
          
          let displayLocality = detectedArea;
          if (cityOrDistrict && cityOrDistrict !== detectedArea) {
            displayLocality += ` (${cityOrDistrict})`;
          }

          document.getElementById('citizenLocality').value = displayLocality;
          if (addressText) {
            addressText.textContent = `📍 Auto-detected: ${geoRes.display_name.split(',').slice(0, 3).join(',')}`;
          }
          showToast(`📍 Detected Area: ${displayLocality}`, 'info');
        }
      } catch (err) {
        console.warn('Reverse geocoding offline, using coordinates:', err);
        if (addressText) addressText.textContent = `📍 Live Coordinates Area (${lat.toFixed(3)}, ${lon.toFixed(3)})`;
      }
      
      // Pan/Zoom map to exact citizen GPS location
      if (State.mapInstance) {
        State.mapInstance.flyTo([lat, lon], 14, { animate: true, duration: 1.5 });
      }
    },
    (error) => {
      if (btn) btn.textContent = '📍 Detect My Live GPS';
      let msg = 'Unable to retrieve location';
      if (error.code === 1) msg = 'Location access permission denied. You can manually enter area name & coordinates.';
      else if (error.code === 2) msg = 'Location unavailable on device.';
      else if (error.code === 3) msg = 'Location request timed out.';
      showToast(`⚠️ ${msg}`, 'warning');
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  );
}

function clearLiveGps() {
  document.getElementById('customLat').value = '28.6328';
  document.getElementById('customLon').value = '77.2195';
  document.getElementById('citizenLocality').value = 'Sector 4';
  const badge = document.getElementById('gpsStatusBadge');
  const btn = document.getElementById('btnDetectGps');
  if (badge) badge.style.display = 'none';
  if (btn) btn.textContent = '📍 Detect My Live GPS';
  showToast('Reset location to Sector 4 preset', 'info');
}

async function submitCitizenComplaint(e) {
  e.preventDefault();
  const title = document.getElementById('citizenTitle').value.trim();
  const desc = document.getElementById('citizenDesc').value.trim();
  const locality = document.getElementById('citizenLocality').value.trim() || 'Central Zone';
  const citizenName = document.getElementById('citizenName').value.trim() || 'Anonymous Citizen';
  
  const customLatVal = document.getElementById('customLat').value;
  const customLonVal = document.getElementById('customLon').value;

  if (!title || !desc) {
    showToast('Please enter both title and description', 'warning');
    return;
  }

  // Predefined Ward Coordinates
  const locCoords = {
    'Sector 4': [28.6328, 77.2195],
    'Civil Lines': [28.6750, 77.2280],
    'South Extension': [28.5720, 77.2215],
    'Hauz Khas': [28.5450, 77.2090],
    'Karol Bagh': [28.6520, 77.1850],
    'Tilak Marg': [28.6180, 77.2340],
    'Lajpat Nagar': [28.5800, 77.2020]
  };

  let finalLat, finalLon;
  if (customLatVal && customLonVal && !isNaN(parseFloat(customLatVal)) && !isNaN(parseFloat(customLonVal))) {
    finalLat = parseFloat(customLatVal);
    finalLon = parseFloat(customLonVal);
  } else {
    const baseCoords = locCoords[locality] || [28.6250, 77.2150];
    finalLat = baseCoords[0] + (Math.random() - 0.5) * 0.005;
    finalLon = baseCoords[1] + (Math.random() - 0.5) * 0.005;
  }

  try {
    const res = await fetch('/api/complaints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description: desc,
        locality,
        citizen_name: citizenName,
        latitude: finalLat,
        longitude: finalLon
      })
    }).then(r => r.json());

    if (res.success) {
      showToast(`🎉 Complaint registered in ${locality} with GPS [${finalLat.toFixed(4)}, ${finalLon.toFixed(4)}]!`, 'success');
      document.getElementById('complaintForm').reset();
      clearLiveGps();
      document.getElementById('duplicateWarningAlert').style.display = 'none';
      fetchDashboardData();
    }
  } catch (err) {
    showToast('Failed to submit complaint', 'error');
  }
}

// ====================================================================
// Interactive Simulation Controls (Hackathon Demo Triggers)
// ====================================================================
async function triggerSpikeSimulation(type) {
  try {
    showToast(`Injecting real-time ${type.replace('_', ' ')} crisis stream...`, 'info');
    const res = await fetch('/api/simulate/spike', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type })
    }).then(r => r.json());

    if (res.success) {
      showToast(`🔥 ${res.injected_count} new spike complaints injected! Anomaly detection updating...`, 'warning');
      fetchDashboardData();
    }
  } catch (e) {
    showToast('Simulation failed', 'error');
  }
}

// ====================================================================
// Helper Functions & Event Handlers
// ====================================================================
function switchTab(tabId) {
  State.currentTab = tabId;

  // Toggle Tab Buttons
  document.querySelectorAll('.nav-tab-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`tabBtn${tabId.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('')}`);
  if (activeBtn) activeBtn.classList.add('active');

  // Toggle View Containers
  document.querySelectorAll('.view-section').forEach(sec => sec.style.display = 'none');
  const targetView = document.getElementById(`view-${tabId}`);
  if (targetView) targetView.style.display = 'block';

  // Invalidate map if switching to officer dashboard
  if (tabId === 'officer-dashboard' && State.mapInstance) {
    setTimeout(() => State.mapInstance.invalidateSize(), 200);
  }
}

async function updateComplaintStatus(id, newStatus) {
  try {
    const res = await fetch(`/api/complaints/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    }).then(r => r.json());

    if (res.success) {
      showToast(`Complaint ${id} marked as ${newStatus}`, 'success');
      fetchDashboardData(true);
    }
  } catch (e) {
    showToast('Failed to update status', 'error');
  }
}

async function upvoteComplaint(id, btnElem) {
  try {
    const res = await fetch(`/api/complaints/${id}/upvote`, { method: 'POST' }).then(r => r.json());
    if (res.success) {
      const upvoteSpan = btnElem.querySelector('.upvote-num');
      if (upvoteSpan) upvoteSpan.textContent = res.upvotes;
      btnElem.classList.add('btn-primary');
      showToast('Upvoted!', 'success');
    }
  } catch (e) {
    console.error(e);
  }
}

function zoomToComplaint(lat, lon, id) {
  switchTab('officer-dashboard');
  if (State.mapInstance) {
    State.mapInstance.flyTo([lat, lon], 15, { animate: true, duration: 1.2 });
    showToast(`Focused on incident ${id}`, 'info');
  }
}

function filterByEvidence(id) {
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.value = id;
    State.filters.search = id;
    fetchDashboardData(true);
    // Scroll to table
    document.getElementById('complaintsTablePanel').scrollIntoView({ behavior: 'smooth' });
  }
}

function bindEvents() {
  // Search Input
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      State.filters.search = e.target.value.trim();
      fetchDashboardData(true);
    });
  }

  // Filters
  const filterCat = document.getElementById('filterCategory');
  if (filterCat) {
    filterCat.addEventListener('change', (e) => {
      State.filters.category = e.target.value;
      fetchDashboardData(true);
    });
  }

  const filterStatus = document.getElementById('filterStatus');
  if (filterStatus) {
    filterStatus.addEventListener('change', (e) => {
      State.filters.status = e.target.value;
      fetchDashboardData(true);
    });
  }

  const filterLoc = document.getElementById('filterLocality');
  if (filterLoc) {
    filterLoc.addEventListener('change', (e) => {
      State.filters.locality = e.target.value;
      fetchDashboardData(true);
    });
  }
}

function updateLocalityFilterDropdown(complaints) {
  const filterLoc = document.getElementById('filterLocality');
  if (!filterLoc) return;

  const currentVal = State.filters.locality;
  const uniqueLocalities = Array.from(new Set(complaints.map(c => c.locality).filter(Boolean))).sort();

  filterLoc.innerHTML = `
    <option value="All" ${currentVal === 'All' ? 'selected' : ''}>All Wards / Localities</option>
    ${uniqueLocalities.map(loc => `<option value="${loc}" ${currentVal === loc ? 'selected' : ''}>${loc}</option>`).join('')}
  `;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'warning') icon = '⚠️';
  if (type === 'error') icon = '❌';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
