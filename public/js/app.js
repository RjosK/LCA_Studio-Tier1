// econode_studio/web/js/app.js - Lógica Frontend Completa para ECONODE Studio (Tier 1)
// Cero dependencias externas. Totalmente reactivo e integrado con los endpoints REST del backend.

(function () {
  'use strict';

  // =========================================================================
  // 1. ESTADO GLOBAL REACTIVO
  // =========================================================================
  const state = {
    activeUser: null,
    isAuthenticated: false,
    allAccounts: [],
    activeSystem: null,
    systems: [],
    canvasNodes: [],
    canvasEdges: [],
    selectedNode: null,
    comments: [],
    checklist: [],
    checklistMeta: null,
    availableStandards: [],
    activeStandard: "nom070",
    paletteProcesses: [],
    editingProcess: null,
    editingInputs: [],
    editingOutputs: [],
    pendingHighlightText: "",
    catalogProcesses: [],
    selectedCatalogProcess: null,
    documents: [],
    currentView: "home", // VISTA POR DEFECTO: Home Landing Page
    systemFilter: "all",
    catalogFilter: "ALL",
    sankeyMode: "none", // "none" | "mass" | "energy"
    connectingFromNode: null, // ID del nodo origen al conectar flujos
    connectingToNode: null, // ID del nodo destino al conectar flujos
    showCanvasStickyNotes: true, // Visualización de sticky notes en lienzo
    canvasViewMode: "visual", // "visual" (diagrama) | "table" (hoja de cálculo)
    tableFilterText: "",
    tableFlowFilter: "ALL", // "ALL" | "INPUTS" | "OUTPUTS" | "CONNECTIONS"
    activeSheetTab: "lci", // "lci" | "connections"
    selectedSpreadsheetCell: null, // { row, col, address, val, meta }
    leftPanelVisible: true, // Visibilidad del catálogo (panel izquierdo)
    rightPanelVisible: true, // Visibilidad del inspector (panel derecho en diagrama)
    canvasZoom: 1.0 // Nivel de zoom del lienzo (0.5 a 1.75, 1.0 por defecto)
  };

  // =========================================================================
  // 2. CLIENTE DE API REST
  // =========================================================================
  const api = {
    async get(endpoint) {
      try {
        const headers = {};
        const token = sessionStorage.getItem("econode_token");
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(endpoint, { headers });
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return await res.json();
      } catch (err) {
        console.error(`API GET error on ${endpoint}:`, err);
        throw err;
      }
    },

    async post(endpoint, data = {}) {
      try {
        const headers = { "Content-Type": "application/json" };
        const token = sessionStorage.getItem("econode_token");
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(endpoint, {
          method: "POST",
          headers,
          body: JSON.stringify(data)
        });
        const json = await res.json();
        if (!res.ok || json.status === "error") {
          throw new Error(json.message || `HTTP ${res.status}`);
        }
        return json;
      } catch (err) {
        console.error(`API POST error on ${endpoint}:`, err);
        throw err;
      }
    },

    // Auth
    getAuthConfig: () => api.get("/api/auth/config"),
    loginWithCredentials: (emailOrUser, password) => api.post("/api/auth/login", { email: emailOrUser, password }),
    loginDemo: (userId) => api.post("/api/auth/login", { user_id: userId }),
    loginGoogle: (credential, email) => api.post("/api/auth/google", { credential, email }),
    signup: (data) => api.post("/api/auth/signup", data),
    logout: () => api.post("/api/auth/logout"),

    // Systems & Canvas
    getSystems: () => {
      const u = state.activeUser;
      let url = "/api/systems";
      if (u) {
        const email = encodeURIComponent(u.email || "");
        const uid = encodeURIComponent(u.id || "");
        url += `?email=${email}&user_id=${uid}`;
      }
      return api.get(url);
    },
    getSystemCanvas: (sysId) => api.get(`/api/systems/${sysId}/canvas`),
    saveSystemCanvas: (sysId, payload) => api.post(`/api/systems/${sysId}/save`, payload),
    createSystem: (data) => {
      const u = state.activeUser;
      const payload = {
        ...data,
        owner_id: u ? u.id : undefined,
        owner_email: u ? u.email : undefined,
        owner_name: u ? u.display_name : undefined,
        owner_role: u ? u.role : undefined,
        owner_org: u ? u.organization : undefined
      };
      return api.post("/api/systems/create", payload);
    },
    importCsv: (csvStr) => api.post("/api/systems/import-csv", { csv: csvStr }),

    // Catalog LCI
    searchCatalog: (q = "", categoryId = null, limit = 50) => {
      let url = `/api/processes?q=${encodeURIComponent(q)}&limit=${limit}`;
      if (categoryId && categoryId !== "ALL") url += `&category_id=${categoryId}`;
      return api.get(url);
    },
    getCategories: (limit = 100) => api.get(`/api/categories?limit=${limit}`),
    getProcessSheet: (procId) => api.get(`/api/processes/${procId}/sheet`),
    getDbFlows: (q = "", type = "ALL", limit = 40, category = null) => {
      let url = `/api/flows?q=${encodeURIComponent(q)}&limit=${limit}`;
      if (type && type !== "ALL") url += `&type=${type}`;
      if (category && category !== "ALL") url += `&category=${category}`;
      return api.get(url);
    },
    getDbProviders: (flowName = "", limit = 15) => api.get(`/api/providers?flow=${encodeURIComponent(flowName)}&limit=${limit}`),
    createCustomProcess: (data) => api.post("/api/processes/create", data),
    createCustomFlow: (data) => api.post("/api/flows/create", data),
    deleteCustomProcess: (procId) => api.post("/api/processes/delete", { process_id: procId }),
    deleteCustomFlow: (flowId) => api.post("/api/flows/delete", { flow_id: flowId }),

    // Comments & Audit
    getComments: (sysId = 21) => api.get(`/api/comments?system_id=${sysId}`),
    addComment: (sysId, content, authorName, authorRole, nodeId = null, x = null, y = null) =>
      api.post("/api/comments", {
        system_id: sysId,
        content,
        author_name: authorName,
        author_role: authorRole,
        node_id: nodeId,
        x,
        y
      }),
    resolveComment: (commentId, reply, resolvedBy) =>
      api.post("/api/comments/resolve", {
        comment_id: commentId,
        reply,
        resolved_by: resolvedBy
      }),
    deleteComment: (commentId, userName = null, userRole = null) =>
      api.post("/api/comments/delete", {
        comment_id: commentId,
        user_name: userName || (state.activeUser ? state.activeUser.display_name : "Carla Méndez"),
        user_role: userRole || (state.activeUser ? state.activeUser.role : "analyst")
      }),
    getStandards: () => api.get("/api/checklists"),
    getChecklist: (sysId = 21, checklistId = "nom070") =>
      api.get(`/api/checklist?system_id=${sysId}&checklist_id=${encodeURIComponent(checklistId)}`),
    toggleClause: (sysId, clauseId, isCompliant, checklistId = "nom070") =>
      api.post("/api/checklist/toggle", {
        system_id: sysId,
        clause_id: clauseId,
        is_compliant: isCompliant,
        checklist_id: checklistId
      }),
    signAudit: (sysId, checklistId = "nom070") =>
      api.post("/api/checklist/sign", { system_id: sysId, checklist_id: checklistId }),
    importChecklist: (csvContent, metadata = {}) =>
      api.post("/api/checklists/import", { csv_content: csvContent, metadata: metadata }),
    updateClauseEvidence: (sysId, clauseId, evidence, checklistId = "nom070") =>
      api.post("/api/checklist/evidence", { system_id: sysId, clause_id: clauseId, evidence: evidence, checklist_id: checklistId }),

    // Document Vault
    getDocuments: (sysId = null) => api.get(sysId ? `/api/documents?system_id=${sysId}` : "/api/documents"),
    uploadDocument: (data) => api.post("/api/documents/upload", data),
    deleteDocument: (docId) => api.post("/api/documents/delete", { document_id: docId }),

    // System management
    deleteSystem: (sysId) => api.post("/api/systems/delete", { system_id: sysId }),
    inviteCollaborator: (sysId, name, email, role) =>
      api.post("/api/systems/collaborators/invite", { system_id: sysId, name, email, role })
  };

  // =========================================================================
  // 3. ENRUTADOR & GESTIÓN DE VISTAS (Home Landing vs Studio)
  // =========================================================================
  const views = {
    home: document.getElementById("viewHome"),
    login: document.getElementById("viewLogin"),
    signup: document.getElementById("viewSignup"),
    dashboard: document.getElementById("viewDashboard"),
    canvas: document.getElementById("viewCanvas"),
    catalog: document.getElementById("viewCatalog"),
    report: document.getElementById("viewReport"),
    audit: document.getElementById("viewAudit")
  };

  function showView(viewName) {
    if (!views[viewName]) return;

    // Protección de rutas: si intenta entrar a Studio sin autenticación, enviar a login
    const isStudioRoute = ["dashboard", "canvas", "catalog", "report", "audit"].includes(viewName);
    if (isStudioRoute && !state.isAuthenticated) {
      showNotification("Por favor inicia sesión con tu perfil para ingresar al Studio.");
      viewName = "login";
    }

    // Protección de proyecto: Si no hay un sistema producto abierto, no permitir entrar a lienzo, reporte o checklist
    const requiresOpenSystem = ["canvas", "report", "audit"].includes(viewName);
    if (requiresOpenSystem && !state.activeSystem) {
      showNotification("Primero debes abrir un sistema producto desde el Dashboard de Proyectos.");
      viewName = "dashboard";
    }

    state.currentView = viewName;
    if (state.isAuthenticated && ["dashboard", "canvas", "catalog", "report", "audit"].includes(viewName)) {
      try { localStorage.setItem("econode_active_view", viewName); } catch (e) {}
    }

    // Alternar contenedores de vista
    Object.keys(views).forEach((name) => {
      if (views[name]) {
        views[name].classList.toggle("active", name === viewName);
      }
    });

    // Actualizar botones del top nav en modo Studio
    document.querySelectorAll(".nav-btn[data-view]").forEach((btn) => {
      const target = btn.getAttribute("data-view");
      btn.classList.toggle("active", target === viewName);
    });

    // Adaptar Top Navbar entre Landing y Studio
    const isLandingOrAuth = ["home", "login", "signup"].includes(viewName);
    const studioNav = document.getElementById("studioNavLinks");
    const landingNav = document.getElementById("landingNavLinks");
    const studioActions = document.getElementById("studioActionsGroup");
    const landingActions = document.getElementById("landingActionsGroup");
    const userGroup = document.getElementById("navUserGroup");
    const btnSettings = document.getElementById("btnOpenSettingsModal");
    const navTitle = document.getElementById("navProjectTitle");

    if (isLandingOrAuth) {
      if (studioNav) studioNav.style.display = "none";
      if (landingNav) landingNav.style.display = "flex";
      if (studioActions) studioActions.style.display = "none";
      if (landingActions) landingActions.style.display = "flex";
      if (userGroup) userGroup.style.display = "none";
      if (btnSettings) btnSettings.style.display = "none";
      if (navTitle) navTitle.textContent = "Professional Life Cycle Assessment Platform";
    } else {
      if (studioNav) studioNav.style.display = "flex";
      if (landingNav) landingNav.style.display = "none";
      if (studioActions) studioActions.style.display = "none";
      if (landingActions) landingActions.style.display = "none";
      if (userGroup) userGroup.style.display = "flex";
      if (btnSettings) btnSettings.style.display = "none";
      if (navTitle && state.activeSystem) {
        navTitle.textContent = `Reporte: ${state.activeSystem.name}`;
      }
    }

    // Aplicar restricciones de perfil de usuario (RBAC)
    applyRolePermissions();

    // Inicializaciones específicas por vista
    if (viewName === "dashboard") loadDashboard();
    if (viewName === "canvas") {
      switchCanvasViewMode(state.canvasViewMode || "visual");
    }
    if (viewName === "catalog") loadCatalog();
    if (viewName === "report") loadReport();
    if (viewName === "audit") loadAuditChecklist();

    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // =========================================================================
  // 4. AUTENTICACIÓN & RBAC (3 PERFILES: ANALISTA, AUDITOR, CLIENTE)
  // =========================================================================
  function applyRolePermissions() {
    const user = state.activeUser;
    const role = user ? user.role : "analyst";

    const navCatalog = document.getElementById("navBtnCatalog");
    const navImport = document.getElementById("btnOpenImportModal");
    const navNewSys = document.getElementById("btnOpenWizardModal");
    const dashNewBtn = document.getElementById("btnDashNewSystem");
    const dashImportBtn = document.getElementById("btnDashImport");
    const canvasPalettePanel = document.querySelector("#viewCanvas .canvas-wrapper > .canvas-panel:first-child");
    const canvasWrapper = document.querySelector("#viewCanvas .canvas-wrapper");
    const reportCommentsCol = document.getElementById("viewReportCommentsCol");
    const reportMainCard = document.getElementById("reportMainCard");
    const vaultUploadBox = document.getElementById("vaultUploadBox");
    const btnSignAudit = document.getElementById("btnSignAuditDictamen");
    const btnToggleSticky = document.getElementById("btnToggleCanvasStickyNotes");
    const stickyNotesLayer = document.getElementById("canvasStickyNotesLayer");
    const reportFormattingToolbar = document.getElementById("reportFormattingToolbar");
    const reportBubbleToolbar = document.getElementById("reportBubbleToolbar");
    const reportHighlightTooltip = document.getElementById("reportHighlightTooltip");
    const reportDocBody = document.getElementById("reportDocumentBody");

    if (role === "auditor") {
      // PERFIL AUDITOR LÍDER:
      document.body.classList.remove("role-client");
      if (navCatalog) navCatalog.style.display = "none";
      if (navImport) navImport.style.display = "none";
      if (navNewSys) navNewSys.style.display = "none";
      if (dashNewBtn) dashNewBtn.style.display = "none";
      if (dashImportBtn) dashImportBtn.style.display = "none";
      if (canvasPalettePanel) canvasPalettePanel.style.display = "none";
      if (canvasWrapper) canvasWrapper.style.gridTemplateColumns = "1fr 320px";
      if (vaultUploadBox) vaultUploadBox.style.display = "none";
      if (reportCommentsCol) reportCommentsCol.style.display = "block";
      if (reportMainCard && reportMainCard.parentElement) {
        reportMainCard.parentElement.style.gridTemplateColumns = "1fr 360px";
      }
      if (btnSignAudit) {
        btnSignAudit.style.display = "inline-flex";
        btnSignAudit.removeAttribute("disabled");
      }
      if (btnToggleSticky) btnToggleSticky.style.display = "inline-flex";
      if (reportFormattingToolbar) reportFormattingToolbar.style.display = "flex";
      if (reportDocBody) reportDocBody.setAttribute("contenteditable", "true");
    } else if (role === "client") {
      // PERFIL CLIENTE PRODUCTOR:
      document.body.classList.add("role-client");
      if (navCatalog) navCatalog.style.display = "none";
      if (navImport) navImport.style.display = "none";
      if (navNewSys) navNewSys.style.display = "none";
      if (dashNewBtn) dashNewBtn.style.display = "none";
      if (dashImportBtn) dashImportBtn.style.display = "none";
      if (canvasPalettePanel) canvasPalettePanel.style.display = "none";
      if (canvasWrapper) canvasWrapper.style.gridTemplateColumns = "1fr 320px";
      if (vaultUploadBox) vaultUploadBox.style.display = "block";
      if (reportCommentsCol) reportCommentsCol.style.display = "none";
      if (reportMainCard && reportMainCard.parentElement) {
        reportMainCard.parentElement.style.gridTemplateColumns = "1fr";
      }
      if (btnSignAudit) btnSignAudit.style.display = "none";

      // Ocultar completamente notas y comentarios en el lienzo para el Cliente
      if (btnToggleSticky) btnToggleSticky.style.display = "none";
      if (stickyNotesLayer) stickyNotesLayer.innerHTML = "";

      // Modo solo lectura en el reporte: ocultar herramientas de edición y deshabilitar edición directa
      if (reportFormattingToolbar) reportFormattingToolbar.style.display = "none";
      if (reportBubbleToolbar) reportBubbleToolbar.style.display = "none";
      if (reportHighlightTooltip) reportHighlightTooltip.style.display = "none";
      if (reportDocBody) reportDocBody.setAttribute("contenteditable", "false");
    } else {
      // PERFIL ANALISTA DE ACV (CREADOR):
      document.body.classList.remove("role-client");
      if (navCatalog) navCatalog.style.display = "inline-flex";
      if (navImport) navImport.style.display = "inline-flex";
      if (navNewSys) navNewSys.style.display = "inline-flex";
      if (dashNewBtn) dashNewBtn.style.display = "inline-flex";
      if (dashImportBtn) dashImportBtn.style.display = "inline-flex";
      if (canvasPalettePanel) canvasPalettePanel.style.display = "flex";
      if (canvasWrapper) canvasWrapper.style.gridTemplateColumns = "280px 1fr 320px";
      if (vaultUploadBox) vaultUploadBox.style.display = "block";
      if (reportCommentsCol) reportCommentsCol.style.display = "block";
      if (reportMainCard && reportMainCard.parentElement) {
        reportMainCard.parentElement.style.gridTemplateColumns = "1fr 360px";
      }
      if (btnSignAudit) btnSignAudit.style.display = "inline-flex";
      if (btnToggleSticky) btnToggleSticky.style.display = "inline-flex";
      if (reportFormattingToolbar) reportFormattingToolbar.style.display = "flex";
      if (reportDocBody) reportDocBody.setAttribute("contenteditable", "true");
    }
  }

  async function initAuth() {
    try {
      const cfg = await api.getAuthConfig();
      if (cfg.accounts) {
        state.allAccounts = cfg.accounts;
      }

      // Solo restaurar sesión si el usuario ya inició sesión explícitamente en esta sesión del navegador
      const storedToken = sessionStorage.getItem("econode_token");
      const storedUserId = sessionStorage.getItem("econode_user_id");

      if (storedToken && storedUserId && cfg.accounts) {
        const found = cfg.accounts.find(a => a.id === storedUserId || a.username === storedUserId || a.email === storedUserId);
        if (found) {
          state.activeUser = found;
          state.isAuthenticated = true;
          updateUserUI();
          return;
        }
      }

      // Si no hay token en sessionStorage, el usuario arranca como NO autenticado
      state.activeUser = null;
      state.isAuthenticated = false;
      sessionStorage.removeItem("econode_token");
      sessionStorage.removeItem("econode_user_id");
    } catch (err) {
      console.warn("Inicialización de auth:", err);
      state.activeUser = null;
      state.isAuthenticated = false;
    }
  }

  function updateUserUI() {
    const user = state.activeUser;
    if (!user) return;

    const navAvatar = document.getElementById("navUserAvatar");
    const navName = document.getElementById("navUserName");
    const navRole = document.getElementById("navUserRole");
    const commentAs = document.getElementById("commentPostingAsLabel");

    if (navAvatar) {
      const initials = (user.display_name || "CM")
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();
      navAvatar.textContent = initials || "CM";
      navAvatar.className = "user-avatar";
      if (user.role === "client") navAvatar.classList.add("client");
      else if (user.role === "analyst") navAvatar.style.background = "#0284C7";
      else navAvatar.style.background = "#0F172A";
    }

    if (navName) {
      navName.textContent = user.display_name || user.email;
    }

    if (navRole) {
      if (user.role === "analyst") navRole.textContent = window.I18n.t("roles.analyst", "Analista de ACV (Creador)");
      else if (user.role === "auditor") navRole.textContent = window.I18n.t("roles.auditor", "Auditor Líder NOM-070");
      else navRole.textContent = window.I18n.t("roles.client", "Cliente / Productor");
    }

    if (commentAs) {
      const roleStr = user.role === "analyst" ? "Analista" : user.role === "auditor" ? "Auditor Líder" : "Cliente";
      const postingAsPrefix = window.I18n.t("app.posting_as", "Publicando como:");
      commentAs.textContent = `${postingAsPrefix} ${user.display_name} (${roleStr})`;
    }

    applyRolePermissions();
  }

  // Login para los 3 Perfiles
  async function handleDemoLogin(roleId) {
    try {
      const res = await api.loginDemo(roleId);
      if (res.user) {
        state.activeUser = res.user;
        state.isAuthenticated = true;
        updateUserUI();

        const roleLabels = {
          analyst: "Analista de ACV (Creador del Sistema Producto)",
          auditor: "Auditor Líder NOM-070 (Verificador Oficial)",
          client: "Cliente / Productor (Empresa Auditada)"
        };
        const label = roleLabels[res.user.role] || res.user.role;
        showNotification(`Sesión iniciada: ${res.user.display_name} · ${label}`);
        applyRolePermissions();
        showView("dashboard");
      }
    } catch (err) {
      alert("Error al iniciar sesión: " + err.message);
    }
  }

  async function handleLogout() {
    try {
      await api.logout();
    } catch (e) {
      // Ignorar error de red si ocurre
    }
    sessionStorage.removeItem("econode_token");
    sessionStorage.removeItem("econode_user_id");
    try {
      localStorage.removeItem("econode_active_system_id");
      localStorage.removeItem("econode_active_view");
    } catch (e) {}
    state.activeUser = null;
    state.isAuthenticated = false;
    state.activeSystem = null;
    state.canvasNodes = [];
    state.canvasEdges = [];
    state.selectedNode = null;
    inspectNode(null);

    const navTitle = document.getElementById("navProjectTitle");
    if (navTitle) {
      navTitle.textContent = "Professional Life Cycle Assessment Platform";
    }

    applyRolePermissions();
    showNotification("Sesión cerrada correctamente. Volviendo al inicio.");
    showView("home");
  }

  // Callback Google GSI
  window.handleGoogleCredentialResponse = async function (response) {
    try {
      const res = await api.loginGoogle(response.credential);
      if (res.user) {
        state.activeUser = res.user;
        state.isAuthenticated = true;
        updateUserUI();
        applyRolePermissions();
        showNotification(`Sesión iniciada con Google Workspace: ${res.user.display_name}`);
        showView("dashboard");
      }
    } catch (err) {
      alert("Error al validar token de Google: " + err.message);
    }
  };

  // =========================================================================
  // 5. DASHBOARD DE PROYECTOS & SISTEMAS
  // =========================================================================
  async function loadDashboard() {
    try {
      const res = await api.getSystems();
      state.systems = res.items || [];

      // Si no hay un sistema activo seleccionado explícitamente, mantener el título neutral
      const navTitle = document.getElementById("navProjectTitle");
      if (navTitle && !state.activeSystem) {
        navTitle.textContent = "Portafolio de Sistemas Producto";
      }

      renderDashboardTable();
      renderDashboardKpis();
      loadDocsCount();
    } catch (err) {
      console.error("Error al cargar dashboard:", err);
    }
  }

  async function loadDocsCount() {
    try {
      if (!state.systems || state.systems.length === 0) {
        state.documents = [];
        const kpiDocs = document.getElementById("kpiDocCount");
        if (kpiDocs) kpiDocs.textContent = "0 Archivos";
        return;
      }
      const sysId = state.activeSystem ? state.activeSystem.id : state.systems[0].id;
      const docsRes = await api.getDocuments(sysId);
      state.documents = docsRes.items || [];
      const kpiDocs = document.getElementById("kpiDocCount");
      if (kpiDocs) kpiDocs.textContent = `${state.documents.length} Archivos`;
    } catch (e) {
      console.warn("Docs count:", e);
    }
  }

  function renderDashboardKpis() {
    const total = state.systems.length;
    const inAudit = state.systems.filter((s) => s.status === "in_audit").length;
    const certified = state.systems.filter((s) => s.status === "certified").length;
    const draft = state.systems.filter((s) => s.status === "draft" || !s.status).length;

    // 1. Contador principal de sistemas activos
    const kpiCount = document.getElementById("kpiActiveSystems");
    if (kpiCount) {
      kpiCount.textContent = `${total} ${total === 1 ? "Modelo" : "Modelos"}`;
    }

    // 2. Subtexto dinámico con desglose real de estados
    const kpiSub = document.getElementById("kpiSystemsSub");
    if (kpiSub) {
      if (total === 0) {
        kpiSub.textContent = window.I18n.t("dash.kpi_no_systems_sub", "0 en auditoría · 0 certificados · 0 borradores");
      } else {
        const parts = [];
        if (inAudit > 0) parts.push(`${inAudit} en auditoría`);
        if (certified > 0) parts.push(`${certified} certificados`);
        if (draft > 0) parts.push(`${draft} borradores`);
        kpiSub.textContent = parts.length > 0 ? parts.join(" · ") : `${total} en catálogo`;
      }
    }

    // 3. Conteo de pestañas filtradas
    const countAll = document.getElementById("countAllSystems");
    if (countAll) {
      countAll.textContent = total;
    }

    // 4. Tarjeta de conformidad según los modelos del usuario
    const kpiComplianceVal = document.getElementById("kpiComplianceValue");
    const kpiComplianceSub = document.getElementById("kpiComplianceSub");
    if (kpiComplianceVal && kpiComplianceSub) {
      if (total === 0) {
        kpiComplianceVal.textContent = "Sin proyectos";
        kpiComplianceVal.style.color = "var(--text-muted)";
        kpiComplianceSub.textContent = "Crea un modelo para auditar";
      } else if (certified > 0) {
        kpiComplianceVal.textContent = "● 100% Conforme";
        kpiComplianceVal.style.color = "var(--accent-emerald)";
        kpiComplianceSub.textContent = "18 de 18 cláusulas validadas";
      } else if (inAudit > 0) {
        kpiComplianceVal.textContent = "● En Auditoría";
        kpiComplianceVal.style.color = "var(--accent-emerald)";
        kpiComplianceSub.textContent = "Revisión técnica NOM-070";
      } else {
        kpiComplianceVal.textContent = "● Borrador";
        kpiComplianceVal.style.color = "var(--text-secondary)";
        kpiComplianceSub.textContent = "Pendiente de verificación";
      }
    }
  }

  function renderDashboardTable() {
    const tbody = document.getElementById("tableSystemsBody");
    if (!tbody) return;

    const filter = state.systemFilter;
    const search = (
      document.getElementById("inputSearchSystems")?.value || ""
    ).toLowerCase();

    const filtered = state.systems.filter((sys) => {
      if (filter === "in_audit" && sys.status !== "in_audit") return false;
      if (filter === "certified" && sys.status !== "certified") return false;
      if (filter === "draft" && sys.status !== "draft") return false;

      if (search) {
        const matchesName = (sys.name || "").toLowerCase().includes(search);
        const matchesCode = (sys.code || "").toLowerCase().includes(search);
        if (!matchesName && !matchesCode) return false;
      }
      return true;
    });

    if (state.systems.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 48px 20px; background: rgba(255, 255, 255, 0.02); border-radius: 8px;">
            <div style="font-size: 36px; margin-bottom: 10px;">📦</div>
            <div style="font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
              ${window.I18n.t("app.no_user_systems_title", "No tienes sistemas producto creados aún")}
            </div>
            <div style="font-size: 12px; color: var(--text-muted); max-width: 440px; margin: 0 auto 18px auto; line-height: 1.45;">
              ${window.I18n.t("app.no_user_systems_desc", "Tu portafolio está completamente limpio. Comienza creando tu primer modelo de ciclo de vida con el asistente interactivo.")}
            </div>
            <div style="display: flex; gap: 10px; justify-content: center;">
              <button class="btn btn-primary btn-sm" id="btnEmptyStateNewSys" onclick="window.EconodeApp.openWizardModal()">
                + ${window.I18n.t("app.new_system_btn", "Nuevo Sistema Producto")}
              </button>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-muted);">${window.I18n.t("app.no_systems_found", "No se encontraron sistemas producto que coincidan con el filtro.")}</td></tr>`;
      return;
    }

    const isAuditor = state.activeUser && state.activeUser.role === "auditor";
    const isClient = state.activeUser && state.activeUser.role === "client";

    tbody.innerHTML = filtered
      .map((sys) => {
        let badgeClass = "badge-slate";
        let statusText = window.I18n.t("app.status_draft", "Borrador Técnico");
        if (sys.status === "in_audit") {
          badgeClass = "badge-emerald";
          statusText = window.I18n.t("app.status_in_audit", "En Auditoría NOM-070");
        } else if (sys.status === "certified") {
          badgeClass = "badge-emerald";
          statusText = window.I18n.t("app.status_certified", "✓ Certificado NOM-070");
        }

        const isOfficial = sys.code === "SYS-PET-CIRCULAR-01" || sys.id === 21;

        let ownerNotice = "";
        const currentUser = state.activeUser;
        const currentUserName = currentUser ? (currentUser.display_name || currentUser.username) : "";
        const isOwner = sys.owner_name && (sys.owner_name.toLowerCase() === currentUserName.toLowerCase() || sys.owner_name.toLowerCase() === (currentUser?.email || "").toLowerCase());

        if (isOwner) {
          ownerNotice = `<div style="font-size: 9.5px; color: var(--accent-emerald); margin-top: 2px;">${window.I18n.t("app.creator_you", "Creador:")} ${currentUserName} ${window.I18n.t("app.you_tag", "(Tú)")}</div>`;
        } else if (isAuditor) {
          ownerNotice = `<div style="font-size: 10px; color: var(--accent-emerald); font-weight: 600; margin-top: 3px;">${window.I18n.t("app.created_by", "👤 Creado por:")} ${sys.owner_name || "Carla Méndez"} · ${sys.owner_org || "BioPack Industrial S.A. de C.V."}</div>`;
        } else if (isClient) {
          ownerNotice = `<div style="font-size: 10px; color: var(--accent-blue); font-weight: 600; margin-top: 3px;">${window.I18n.t("app.shared_by", "🔗 Compartido por:")} ${sys.owner_name || "Carla Méndez"} (BioPack Lab)</div>`;
        } else {
          ownerNotice = `<div style="font-size: 9.5px; color: var(--text-dim); margin-top: 2px;">${window.I18n.t("app.creator_you", "Creador:")} ${sys.owner_name || "Carla Méndez"}</div>`;
        }

        const ownerShortName = sys.owner_name ? (sys.owner_name.split(" ")[0] + (sys.owner_name.split(" ")[1] ? " " + sys.owner_name.split(" ")[1][0] + "." : "")) : "Creador";
        const collabsList = sys.collaborators || [];
        const extraCollabsHtml = collabsList.map(c => {
          const cRole = c.role === "auditor" ? "🔍" : c.role === "client" ? "🏢" : "👤";
          const cShort = c.display_name ? (c.display_name.split(" ")[0] + (c.display_name.split(" ")[1] ? " " + c.display_name.split(" ")[1][0] + "." : "")) : "Colab";
          const colorBg = c.role === "auditor" ? "rgba(16, 185, 129, 0.12)" : c.role === "client" ? "rgba(139, 92, 246, 0.12)" : "rgba(14, 165, 233, 0.12)";
          const colorText = c.role === "auditor" ? "#059669" : c.role === "client" ? "#7C3AED" : "#0284C7";
          return `<span class="user-chip-mini" style="background: ${colorBg}; color: ${colorText}; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="${c.display_name} (${c.role})">${cRole} ${cShort}</span>`;
        }).join("");

        const teamHtml = isOfficial ? `
          <div style="display: flex; gap: 4px; flex-wrap: wrap; align-items: center;" title="Equipo de trabajo asignado al proyecto">
            <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Carla Méndez (Analista de ACV)">👤 Carla M.</span>
            <span class="user-chip-mini" style="background: rgba(16, 185, 129, 0.12); color: #059669; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Josué Arentería (Auditor Líder)">🔍 Josué A.</span>
            <span class="user-chip-mini" style="background: rgba(139, 92, 246, 0.12); color: #7C3AED; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Elena Ramírez (Cliente / Productor)">🏢 Elena R.</span>
          </div>
        ` : `
          <div style="display: flex; gap: 4px; flex-wrap: wrap; align-items: center;" title="Equipo del proyecto">
            <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">👤 ${ownerShortName}</span>
            ${extraCollabsHtml}
            <button class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9px; border-radius: 4px;" onclick="window.EconodeApp.openInviteModal(${sys.id}, '${escape(sys.name)}')" title="Invitar auditor o cliente a este proyecto">+ Invitar</button>
          </div>
        `;

        return `
        <tr style="${isOfficial ? 'background: rgba(5, 150, 105, 0.03);' : ''}">
          <td>
            <strong style="color: var(--text-primary); cursor: pointer;" onclick="window.EconodeApp.openSystem(${sys.id})">${sys.name}</strong>
            <div style="font-size: 10px; color: var(--text-muted);">${sys.category || "Polímeros"} · ${sys.geography || "[MX]"} ${isOfficial ? `<span class="badge-pill badge-emerald" style="font-size: 8px;">${window.I18n.t("app.official_3_proc", "OFICIAL 3 PROCESOS")}</span>` : ''}</div>
            ${ownerNotice}
          </td>
          <td><span class="mono">${sys.code || "SKU-N/A"}</span></td>
          <td><span class="mono">${sys.target_amount || 1.0} ${sys.unit || "u"}</span></td>
          <td><span class="badge-pill badge-slate">${sys.nodes_count || 0} ${window.I18n.t("app.processes_count", "procesos")}</span></td>
          <td>${teamHtml}</td>
          <td><span class="badge-pill ${badgeClass}">${statusText}</span></td>
          <td>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openDocsModal(${sys.id})">
                ${window.I18n.t("app.vault_btn", "📁 Bóveda")}
              </button>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openSystem(${sys.id})">
                ${window.I18n.t("app.open_canvas_btn", "Abrir Lienzo ➔")}
              </button>
              ${!isOfficial ? `<button class="btn btn-secondary btn-sm" style="padding: 4px 7px; color: #EF4444;" onclick="window.EconodeApp.deleteSystem(${sys.id}, '${escape(sys.name)}')" title="Eliminar este sistema producto">🗑️</button>` : ''}
            </div>
          </td>
        </tr>
      `;
      })
      .join("");
  }

  async function openSystem(sysId, navigateToCanvas = true) {
    try {
      const res = await api.getSystemCanvas(sysId);
      if (res && res.system) {
        try { localStorage.setItem("econode_active_system_id", String(sysId)); } catch (e) {}
        state.activeSystem = res.system;
        state.canvasNodes = (res.system.nodes || []).map(n => {
          const nx = (n.x !== undefined && n.x !== null) ? Number(n.x) : ((n.pos_x !== undefined && n.pos_x !== null) ? Number(n.pos_x) : 60);
          const ny = (n.y !== undefined && n.y !== null) ? Number(n.y) : ((n.pos_y !== undefined && n.pos_y !== null) ? Number(n.pos_y) : 140);
          return {
            ...n,
            x: nx,
            y: ny,
            pos_x: nx,
            pos_y: ny
          };
        });
        state.canvasEdges = res.system.edges || [];

        // Actualizar títulos
        const navTitle = document.getElementById("navProjectTitle");
        if (navTitle) {
          navTitle.textContent = `Reporte: ${res.system.name}`;
        }
        const canvasTitle = document.getElementById("canvasSystemTitle");
        if (canvasTitle) {
          canvasTitle.textContent = `${res.system.name} (${res.system.code})`;
        }
        const isOfficial = res.system.id === 21 || res.system.code === "SYS-PET-CIRCULAR-01";
        const canvasTeam = document.getElementById("canvasProjectTeam");
        if (canvasTeam) {
          if (isOfficial) {
            canvasTeam.innerHTML = `
              <span style="font-weight: 600; color: var(--text-secondary);">${window.I18n.t("dash.col_team", "Equipo")}:</span>
              <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">👤 Carla M. (Analista)</span>
              <span class="user-chip-mini" style="background: rgba(16, 185, 129, 0.12); color: #059669; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">🔍 Josué A. (Auditor)</span>
              <span class="user-chip-mini" style="background: rgba(139, 92, 246, 0.12); color: #7C3AED; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">🏢 Elena R. (Cliente)</span>
            `;
          } else {
            const rawOwner = res.system.owner_name || (state.activeUser ? state.activeUser.display_name : "Creador");
            const ownerShort = rawOwner.split(" ")[0] + (rawOwner.split(" ")[1] ? " " + rawOwner.split(" ")[1][0] + "." : "");
            const collabs = res.system.collaborators || [];
            const collabsChips = collabs.map(c => {
              const icon = c.role === "auditor" ? "🔍" : c.role === "client" ? "🏢" : "👤";
              const roleTitle = c.role === "auditor" ? "Auditor" : c.role === "client" ? "Cliente" : "Colab";
              const cName = c.display_name || c.name || "Colab";
              const cShort = cName.split(" ")[0] + (cName.split(" ")[1] ? " " + cName.split(" ")[1][0] + "." : "");
              const colorBg = c.role === "auditor" ? "rgba(16, 185, 129, 0.12)" : c.role === "client" ? "rgba(139, 92, 246, 0.12)" : "rgba(14, 165, 233, 0.12)";
              const colorText = c.role === "auditor" ? "#059669" : c.role === "client" ? "#7C3AED" : "#0284C7";
              return `<span class="user-chip-mini" style="background: ${colorBg}; color: ${colorText}; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">${icon} ${cShort} (${roleTitle})</span>`;
            }).join("");
            const inviteBtn = `<button class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9px; border-radius: 4px; margin-left: 2px;" onclick="window.EconodeApp.openInviteModal(${res.system.id}, '${escape(res.system.name)}')" title="Invitar auditor o cliente a este proyecto">+ Invitar</button>`;
            canvasTeam.innerHTML = `
              <span style="font-weight: 600; color: var(--text-secondary);">${window.I18n.t("dash.col_team", "Equipo")}:</span>
              <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">👤 ${ownerShort} (Analista)</span>
              ${collabsChips}
              ${inviteBtn}
            `;
          }
        }

        // Paleta y selección de nodo: no precargar procesos PET en sistemas nuevos
        if (isOfficial) {
          initDefaultPalette();
          if (state.canvasNodes && state.canvasNodes.length > 0) {
            inspectNode(state.canvasNodes[0]);
          }
        } else {
          state.paletteProcesses = [];
          state.selectedNode = null;
          inspectNode(null);
        }
        renderPaletteProcesses();
        const reportTitle = document.getElementById("reportMainTitle");
        if (reportTitle) {
          reportTitle.textContent = res.system.name;
        }

        // Cargar comentarios estrictamente pertenecientes a este sistema producto
        await loadSystemComments();

        if (navigateToCanvas) {
          showView("canvas");
        }
      }
    } catch (err) {
      console.error("Error al abrir sistema:", err);
    }
  }

  // =========================================================================
  // 6. LIENZO INTERACTIVO DE MODELADO (CANVAS, PUERTOS, SANKEY Y DRAG & DROP)
  // =========================================================================
  function findNodeById(id) {
    if (!id || !state.canvasNodes) return null;
    const strId = String(id).trim();
    const cleanNum = strId.replace(/\D/g, "");
    return state.canvasNodes.find((n) => {
      if (n.id === id || String(n.id) === strId) return true;
      if (n.process_id !== undefined && (n.process_id === id || String(n.process_id) === strId)) return true;
      if (cleanNum && n.process_id !== undefined && String(n.process_id) === cleanNum) return true;
      if (cleanNum && n.id && String(n.id).replace(/\D/g, "") === cleanNum) return true;
      return false;
    });
  }

  function getNodeDirectEnergy(node) {
    if (!node) return 0;
    let sumEnergyKwh = 0;
    let foundExplicit = false;

    if (Array.isArray(node.inputs) && node.inputs.length > 0) {
      node.inputs.forEach((inp) => {
        // Ignorar flujos unitarios intermedios conectados de procesos aguas arriba
        const isConnectedUnit = inp.is_unit || 
          inp.type === "UNIT_PROCESS_FLOW" || 
          inp.exchange_type === "technosphere_connected" || 
          (inp.name && inp.name.toLowerCase().includes("connected flow")) ||
          (inp.flow_name && inp.flow_name.toLowerCase().includes("connected flow"));
        if (isConnectedUnit) return;

        const u = (inp.unit || inp.unit_symbol || "").trim().toLowerCase();
        const amt = parseFloat(inp.amount) || 0;
        if (amt <= 0) return;

        const nm = (inp.name || inp.flow_name || "").toLowerCase();

        if (u === "kwh") {
          sumEnergyKwh += amt;
          foundExplicit = true;
        } else if (u === "mwh") {
          sumEnergyKwh += amt * 1000;
          foundExplicit = true;
        } else if (u === "mj") {
          sumEnergyKwh += amt / 3.6;
          foundExplicit = true;
        } else if (u === "gj") {
          sumEnergyKwh += (amt * 1000) / 3.6;
          foundExplicit = true;
        } else if (u === "l" || u === "liter" || u === "litro") {
          // Equivalente térmico de diesel / combustible automotriz (aprox. 9.96 kWh / L)
          if (nm.includes("diesel") || nm.includes("combust") || nm.includes("fuel") || nm.includes("gasol")) {
            sumEnergyKwh += amt * 9.96;
            foundExplicit = true;
          }
        } else if (u.includes("t·km") || u.includes("tkm") || u.includes("t*km")) {
          // Energía directa de transporte pesado de carga (aprox. 0.70 kWh / t·km)
          sumEnergyKwh += amt * 0.70;
          foundExplicit = true;
        }
      });
    }

    if (foundExplicit && sumEnergyKwh > 0) {
      return Number(sumEnergyKwh.toFixed(3));
    }

    // Valores canónicos calculados de referencia para la cadena PET
    const pId = Number(node.process_id);
    const nm = (node.name || "").toLowerCase();
    if (pId === 100001 || nm.includes("inyecc") || nm.includes("injection")) {
      return 0.280;
    }
    if (pId === 100002 || nm.includes("soplado") || nm.includes("blow")) {
      return 0.140;
    }
    if (pId === 100003 || nm.includes("distrib") || nm.includes("logis") || nm.includes("transp")) {
      return 0.080;
    }

    return Number(((parseFloat(node.amount) || 1.0) * 0.25).toFixed(3));
  }

  function getNodeMass(node) {
    if (!node) return 1.0;
    const pId = Number(node.process_id);
    if (node.reference_flow) {
      const u = (node.reference_flow.unit || "").trim().toLowerCase();
      const amt = parseFloat(node.reference_flow.amount) || 1.0;
      if (u === "kg") return amt;
      if (u === "g") return amt / 1000;
      if (u === "t" || u === "ton") return amt * 1000;
      if (u === "u" || u === "pza") {
        if (pId === 100002 || pId === 100003) return 0.998;
        return amt;
      }
      return amt;
    }
    const u = (node.unit || "").trim().toLowerCase();
    const amt = parseFloat(node.amount) || 1.0;
    if (u === "kg") return amt;
    if (u === "g") return amt / 1000;
    if (u === "t" || u === "ton") return amt * 1000;
    if (u === "u" || u === "pza") {
      if (pId === 100002 || pId === 100003) return 0.998;
    }
    return amt;
  }

  function getNodeCumulativeEnergy(targetId, visited = new Set()) {
    if (!targetId) return 0;
    const node = findNodeById(targetId);
    if (!node) return 0;

    const nodeKey = String(node.process_id || node.id);
    if (visited.has(nodeKey)) return 0;
    visited.add(nodeKey);

    const directE = getNodeDirectEnergy(node);

    // Encontrar aristas que entran a este nodo
    const incomingEdges = (state.canvasEdges || []).filter((e) => {
      const edgeTarget = e.to || e.target_process_id;
      const targetNode = findNodeById(edgeTarget);
      return targetNode && (targetNode === node || String(targetNode.process_id) === String(node.process_id) || String(targetNode.id) === String(node.id));
    });

    if (incomingEdges.length === 0) {
      return directE;
    }

    let upstreamCumulative = 0;
    incomingEdges.forEach((e) => {
      const srcId = e.from || e.source_process_id;
      upstreamCumulative += getNodeCumulativeEnergy(srcId, visited);
    });

    return Number((upstreamCumulative + directE).toFixed(3));
  }

  function getEdgeEnergy(edge, fromNode) {
    if (!edge) return 0.28;
    const srcNode = fromNode || findNodeById(edge.from || edge.source_process_id);
    if (!srcNode) return 0.28;
    // La energía transportada por un flujo saliente es la energía acumulada embebida del nodo origen
    const cumEnergy = getNodeCumulativeEnergy(srcNode.id || srcNode.process_id);
    return Math.max(0.01, Number(cumEnergy.toFixed(2)));
  }

  function getEdgeMass(edge, fromNode) {
    if (!edge) return 1.0;
    const u = (edge.unit || "").trim().toLowerCase();
    const amt = parseFloat(edge.amount) || 1.0;
    if (u === "kg") return amt;
    if (u === "g") return amt / 1000;
    if (u === "t" || u === "ton") return amt * 1000;
    if (u === "u" || u === "pza") {
      const pId = fromNode ? Number(fromNode.process_id) : 0;
      if (pId === 100002 || (edge.flow && edge.flow.toLowerCase().includes("bottle"))) {
        return 0.998;
      }
      return amt;
    }
    return amt;
  }

  function renderCanvasStage() {
    const stage = document.getElementById("canvasStage");
    if (!stage) return;

    // Solo sembrar la estructura de 3 procesos en el modelo oficial de referencia PET
    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");
    if ((!state.canvasNodes || state.canvasNodes.length === 0) && isOfficialSys) {
      loadOfficial3ProcessModel();
    }

    // Si el lienzo está vacío o el nodo inspeccionado ya no existe, limpiar incondicionalmente el inspector
    if (!state.canvasNodes || state.canvasNodes.length === 0) {
      inspectNode(null);
    } else if (state.selectedNode && !state.canvasNodes.some(n => String(n.id) === String(state.selectedNode.id))) {
      inspectNode(null);
    }

    const emptyGuideHtml = (!state.canvasNodes || state.canvasNodes.length === 0) ? `
      <div class="empty-canvas-guide" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none; z-index: 5; opacity: 0.85;">
        <div style="font-size: 38px; margin-bottom: 10px;">🎨</div>
        <h4 style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">Lienzo de Modelado Vacío</h4>
        <p style="font-size: 12px; color: var(--text-muted); max-width: 360px; line-height: 1.45; margin: 0 auto;">
          Arrastra procesos desde la paleta izquierda o haz clic en <strong>"+ Buscar en Catálogo LCI"</strong> para comenzar a modelar este sistema producto.
        </p>
      </div>
    ` : '';

    stage.innerHTML = `
      <div id="canvasZoomContainer" style="position: absolute; top:0; left:0; width: 100%; height: 100%; min-width: 2400px; min-height: 1600px; transform-origin: 0 0; transform: scale(${state.canvasZoom || 1}); transition: transform 0.12s ease-out;">
        <svg id="canvasSvgOverlay" style="position: absolute; top:0; left:0; width: 100%; height: 100%; pointer-events: none; z-index: 2;">
        </svg>
        <div id="canvasNodesLayer" style="position: absolute; top:0; left:0; width: 100%; height: 100%; pointer-events: none; z-index: 4;"></div>
        <div id="canvasStickyNotesLayer" style="position: absolute; top:0; left:0; width: 100%; height: 100%; pointer-events: none; z-index: 10;"></div>
        ${emptyGuideHtml}
      </div>
    `;

    // Configurar paneo arrastrando sobre el fondo del lienzo y zoom con rueda (Ctrl + Rueda)
    let didPan = false;
    let isPanning = false;
    let panStartX = 0;
    let panStartY = 0;
    let scrollStartX = 0;
    let scrollStartY = 0;

    if (!stage.dataset.panBound) {
      stage.dataset.panBound = "true";

      stage.addEventListener("mousedown", (e) => {
        if (e.target.closest(".process-node-card") || 
            e.target.closest(".btn-node-comment") || 
            e.target.closest(".node-port") || 
            e.target.closest(".canvas-floating-zoom") ||
            e.target.closest(".canvas-bottom-dock") ||
            e.target.closest(".canvas-edge-group") ||
            e.target.closest(".canvas-sticky-note") ||
            (e.button !== 0 && e.button !== 1)) {
          return;
        }
        isPanning = true;
        didPan = false;
        panStartX = e.clientX;
        panStartY = e.clientY;
        scrollStartX = stage.scrollLeft;
        scrollStartY = stage.scrollTop;
      });

      window.addEventListener("mousemove", (e) => {
        if (!isPanning) return;
        const dx = e.clientX - panStartX;
        const dy = e.clientY - panStartY;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
          didPan = true;
          stage.style.cursor = "grabbing";
          stage.scrollLeft = scrollStartX - dx;
          stage.scrollTop = scrollStartY - dy;
        }
      });

      window.addEventListener("mouseup", () => {
        if (isPanning) {
          isPanning = false;
          stage.style.cursor = "";
          setTimeout(() => { didPan = false; }, 50);
        }
      });

      // Zoom con Ctrl + Rueda o gesto pinch en trackpad
      stage.addEventListener("wheel", (e) => {
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
          applyCanvasZoom((state.canvasZoom || 1.0) * zoomFactor, e.clientX, e.clientY);
        }
      }, { passive: false });
    }

    // Deseleccionar al hacer clic sobre el fondo del lienzo (solo si no se estaba paneando)
    if (!stage.dataset.bgClickBound) {
      stage.dataset.bgClickBound = "true";
      stage.addEventListener("click", (e) => {
        if (didPan) return;
        if (!e.target.closest(".process-node-card") && 
            !e.target.closest(".btn-node-comment") && 
            !e.target.closest(".node-port") && 
            !e.target.closest(".canvas-top-bar") &&
            !e.target.closest(".canvas-floating-zoom") &&
            !e.target.closest(".canvas-bottom-dock") &&
            !e.target.closest(".canvas-edge-group") &&
            !e.target.closest(".canvas-edge-badge")) {
          inspectNode(null);
          document.querySelectorAll(".process-node-card").forEach(c => c.style.border = "");
        }
      });
    }

    // Configurar stage para Drag & Drop desde la paleta (una sola vez)
    if (!stage.dataset.dragBound) {
      stage.dataset.dragBound = "true";
      stage.addEventListener("dragover", (e) => {
        e.preventDefault();
        stage.style.background = "rgba(5, 150, 105, 0.04)";
      });
      stage.addEventListener("dragleave", () => {
        stage.style.background = "transparent";
      });
      stage.addEventListener("drop", (e) => {
        e.preventDefault();
        stage.style.background = "transparent";
        const rawData = e.dataTransfer.getData("application/json");
        if (rawData) {
          try {
            const item = JSON.parse(rawData);
            const rect = stage.getBoundingClientRect();
            const zoom = state.canvasZoom || 1;
            const dropX = Math.max(20, Math.round((e.clientX - rect.left + stage.scrollLeft) / zoom - 100));
            const dropY = Math.max(20, Math.round((e.clientY - rect.top + stage.scrollTop) / zoom - 40));
            addNodeToCanvas(item.name, item.category || item.cat, item.unit, dropX, dropY, item.inputs, item.outputs, item.process_id || item.id);
            if (state.paletteProcesses && (item.id || item.process_id)) {
              const pIdx = state.paletteProcesses.findIndex(p => String(p.id) === String(item.id) || String(p.process_id) === String(item.process_id || item.id));
              if (pIdx >= 0) {
                state.paletteProcesses.splice(pIdx, 1);
                renderPaletteProcesses();
              }
            }
          } catch (err) {
            console.warn("Drop error:", err);
          }
        }
      });
    }

    const nodesLayer = document.getElementById("canvasNodesLayer");
    state.canvasNodes.forEach((node) => {
      const nx = (node.x !== undefined && node.x !== null) ? Number(node.x) : ((node.pos_x !== undefined && node.pos_x !== null) ? Number(node.pos_x) : 60);
      const ny = (node.y !== undefined && node.y !== null) ? Number(node.y) : ((node.pos_y !== undefined && node.pos_y !== null) ? Number(node.pos_y) : 140);
      node.x = nx;
      node.y = ny;
      node.pos_x = nx;
      node.pos_y = ny;
      const el = document.createElement("div");
      el.className = "process-node-card";
      el.id = `canvas_node_${node.id}`;
      el.style.left = `${nx}px`;
      el.style.top = `${ny}px`;
      el.style.width = "220px";
      el.style.position = "absolute";

      if (state.selectedNode && state.selectedNode.id === node.id) {
        el.style.border = "2px solid var(--accent-emerald)";
      }

      // Preparar etiquetas según modo Sankey con cálculo dinámico y físico
      let sankeyBadgeHtml = "";
      if (state.sankeyMode === "mass") {
        const massVal = getNodeMass(node);
        sankeyBadgeHtml = `<span class="node-sankey-badge mass">Mass: ${Number(massVal).toFixed(3)} kg</span>`;
      } else if (state.sankeyMode === "energy") {
        const energyVal = getNodeDirectEnergy(node);
        sankeyBadgeHtml = `<span class="node-sankey-badge energy">Energy: ${Number(energyVal).toFixed(2)} kWh</span>`;
      }

      // Conteo de entradas y salidas
      const inCount = node.inputs ? node.inputs.length : 3;
      const outCount = node.outputs ? node.outputs.length : 3;

      el.innerHTML = `
        <div class="node-header-row" style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 4px;">
            <span class="mono" style="font-size: 8.5px; font-weight: 700; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 1px 4px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25);">ID: #${node.process_id || node.id}</span>
            <span class="badge-pill badge-slate" style="font-size: 8px;">${node.category || "Process"}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 4px;">
            ${(state.activeUser && state.activeUser.role === 'client') ? '' : `<button type="button" class="btn-node-comment" title="Add technical note to this process" style="background: none; border: 1px solid var(--border-color); border-radius: 3px; font-size: 9.5px; padding: 1px 4px; cursor: pointer; color: var(--text-secondary); background: #FFFFFF;">💬 +</button>`}
            ${(state.activeUser && state.activeUser.role === 'client') ? '' : `<button type="button" class="btn-node-delete" title="Remove process from model" style="background: none; border: 1px solid var(--border-color); border-radius: 3px; font-size: 9.5px; padding: 1px 5px; cursor: pointer; color: #EF4444; background: #FFFFFF;" onclick="event.stopPropagation(); window.EconodeApp.removeNode('${node.id}');">✕</button>`}
            <span class="node-val mono" style="font-size: 10px; font-weight: 700; color: var(--accent-emerald);">${node.reference_flow ? `${node.reference_flow.amount} ${node.reference_flow.unit}` : `${node.amount || 1.0} ${node.unit || 'kg'}`}</span>
          </div>
        </div>
        <div class="node-title" style="font-size: 11.5px; font-weight: 700; margin: 4px 0 2px;">${node.name}</div>
        <div style="font-size: 9.5px; color: var(--text-dim);">● ${inCount} Inputs (1 Unit) · ${outCount} Outputs (1 Waste)</div>
        ${sankeyBadgeHtml}

        <div class="node-ports-row" style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
          <span class="node-port port-in" data-node-id="${node.id}" title="Inlet Port (Click to connect)">🡇</span>
          <span style="font-size: 9px; color: var(--text-muted);">Connectors</span>
          <span class="node-port port-out" data-node-id="${node.id}" title="Outlet Port (Click to connect)">🡆</span>
        </div>
      `;

      // Evento de botón de comentario específico en la tarjeta del proceso
      const btnComment = el.querySelector(".btn-node-comment");
      if (btnComment) {
        btnComment.addEventListener("click", (e) => {
          e.stopPropagation();
          openNodeCommentModal(node);
        });
      }

      // Eventos de arrastre y selección
      el.addEventListener("mousedown", (e) => {
        // Evitar arrastrar si se hizo clic en los puertos o en el botón de comentario
        if (e.target.classList.contains("node-port") || e.target.classList.contains("btn-node-comment")) return;
        startDragNode(e, node, el);
      });
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        if (state.connectingFromNode) {
          if (state.connectingFromNode.id !== node.id && String(state.connectingFromNode.process_id) !== String(node.process_id)) {
            completeConnection(node);
            return;
          }
        }
        inspectNode(node);
        document.querySelectorAll(".process-node-card").forEach(c => c.style.border = "");
        el.style.border = "2px solid var(--accent-emerald)";
      });

      // Eventos de conexión de puertos
      const portOut = el.querySelector(".port-out");
      const portIn = el.querySelector(".port-in");

      if (portOut) {
        portOut.addEventListener("click", (e) => {
          e.stopPropagation();
          startConnection(node);
        });
      }

      if (portIn) {
        portIn.addEventListener("click", (e) => {
          e.stopPropagation();
          completeConnection(node);
        });
      }

      nodesLayer.appendChild(el);
    });

    renderCanvasEdges();
    renderPaletteProcesses();
    updateSankeyLegend();
    renderCanvasStickyNotes();
    updateZoomLabels();
  }

  function loadOfficial3ProcessModel() {
    state.canvasNodes = [
      {
        id: "node_inyeccion",
        process_id: 100001,
        name: "PET Preform Injection Molding",
        category: "Polymer Transformation",
        x: 60,
        y: 140,
        reference_flow: { name: "Clear PET preform", amount: 1.000, unit: "kg" },
        inputs: [
          { name: "Virgin PET granulate [GLO]", amount: 1.050, unit: "kg", is_unit: true },
          { name: "CFE electricity grid mix 230kV [MX]", amount: 0.280, unit: "kWh", is_unit: false },
          { name: "Demineralized process cooling water [MX]", amount: 0.015, unit: "m3", is_unit: false }
        ],
        outputs: [
          { name: "Clear PET preform", amount: 1.000, unit: "kg", is_reference: true },
          { name: "Purge PET plastic scrap (Waste)", amount: 0.050, unit: "kg", is_waste: true },
          { name: "Fossil CO2 emissions [Air]", amount: 0.012, unit: "kg", is_elementary: true }
        ]
      },
      {
        id: "node_soplado",
        process_id: 100002,
        name: "PET Bottle Stretch Blow Molding",
        category: "Thermoforming & Blow Molding",
        x: 420,
        y: 140,
        reference_flow: { name: "Finished PET bottle 500ml", amount: 1.000, unit: "u" },
        inputs: [
          { name: "Clear PET preform (Connected Flow)", amount: 1.000, unit: "kg", is_unit: true },
          { name: "High-pressure compressed air (40 bar)", amount: 0.450, unit: "m3", is_unit: false },
          { name: "Thermoforming electricity CFE", amount: 0.140, unit: "kWh", is_unit: false }
        ],
        outputs: [
          { name: "Finished PET bottle 500ml", amount: 1.000, unit: "u", is_reference: true },
          { name: "Plastic trimming scrap (Waste)", amount: 0.002, unit: "kg", is_waste: true },
          { name: "Dissipated waste heat [Air]", amount: 0.005, unit: "MJ", is_elementary: true }
        ]
      },
      {
        id: "node_transporte",
        process_id: 100003,
        name: "PET Bottle Distribution & Logistics",
        category: "Distribution & Transport",
        x: 780,
        y: 140,
        reference_flow: { name: "Bottle distributed at distribution center", amount: 1.000, unit: "u" },
        inputs: [
          { name: "Finished PET bottle 500ml (Connected Flow)", amount: 1.000, unit: "u", is_unit: true },
          { name: "Automotive diesel fuel", amount: 0.008, unit: "l", is_unit: false },
          { name: "Freight lorry transport 16-32t [MX]", amount: 0.0084, unit: "t·km", is_unit: false }
        ],
        outputs: [
          { name: "Bottle distributed at distribution center", amount: 1.000, unit: "u", is_reference: true },
          { name: "Used lubricant oil (Waste)", amount: 0.0001, unit: "kg", is_waste: true },
          { name: "Diesel combustion emissions CO2 / NOx [Air]", amount: 0.021, unit: "kg", is_elementary: true }
        ]
      }
    ];

    state.canvasEdges = [
      { id: "edge_1_2", from: "node_inyeccion", to: "node_soplado", flow: "Clear PET preform", amount: 1.000, unit: "kg" },
      { id: "edge_2_3", from: "node_soplado", to: "node_transporte", flow: "Finished PET bottle 500ml", amount: 1.000, unit: "u" }
    ];
  }

  function renderCanvasEdges() {
    const svg = document.getElementById("canvasSvgOverlay");
    if (!svg) return;
    svg.innerHTML = "";

    const isSankeyMass = state.sankeyMode === "mass";
    const isSankeyEnergy = state.sankeyMode === "energy";

    state.canvasEdges.forEach((edge) => {
      const fromNode = state.canvasNodes.find((n) => 
        n.id === edge.from || 
        String(n.id) === String(edge.from) || 
        String(n.process_id) === String(edge.from) || 
        String(n.process_id) === String(edge.source_process_id) ||
        (n.id && edge.from && String(n.id).replace(/\D/g, "") === String(edge.from).replace(/\D/g, "") && String(edge.from).replace(/\D/g, "") !== "")
      );
      const toNode = state.canvasNodes.find((n) => 
        n.id === edge.to || 
        String(n.id) === String(edge.to) || 
        String(n.process_id) === String(edge.to) || 
        String(n.process_id) === String(edge.target_process_id) ||
        (n.id && edge.to && String(n.id).replace(/\D/g, "") === String(edge.to).replace(/\D/g, "") && String(edge.to).replace(/\D/g, "") !== "")
      );
      if (!fromNode || !toNode) return;

      const nodeWidth = 220;
      const fnX = (fromNode.x !== undefined && fromNode.x !== null) ? Number(fromNode.x) : Number(fromNode.pos_x || 60);
      const fnY = (fromNode.y !== undefined && fromNode.y !== null) ? Number(fromNode.y) : Number(fromNode.pos_y || 140);
      const tnX = (toNode.x !== undefined && toNode.x !== null) ? Number(toNode.x) : Number(toNode.pos_x || 420);
      const tnY = (toNode.y !== undefined && toNode.y !== null) ? Number(toNode.y) : Number(toNode.pos_y || 140);

      // Distribuir verticalmente si hay múltiples conexiones salientes desde fromNode
      const outgoingList = state.canvasEdges.filter(ed => ed.from === fromNode.id || String(ed.source_process_id) === String(fromNode.process_id));
      const outIdx = Math.max(0, outgoingList.indexOf(edge));
      const totalOut = outgoingList.length;
      const y1Offset = totalOut > 1 ? (outIdx - (totalOut - 1) / 2) * 16 : 0;

      // Distribuir verticalmente si hay múltiples conexiones entrantes a toNode
      const incomingList = state.canvasEdges.filter(ed => ed.to === toNode.id || String(ed.target_process_id) === String(toNode.process_id));
      const inIdx = Math.max(0, incomingList.indexOf(edge));
      const totalIn = incomingList.length;
      const y2Offset = totalIn > 1 ? (inIdx - (totalIn - 1) / 2) * 16 : 0;

      const x1 = fnX + nodeWidth;
      const y1 = fnY + 60 + y1Offset;
      const x2 = tnX;
      const y2 = tnY + 60 + y2Offset;

      const dx = Math.max(35, Math.abs(x2 - x1) * 0.5);
      const pathD = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

      // Configuración de estilo según Sankey con alto contraste óptico dinámico y física real
      let strokeWidth = 2.5;
      let strokeColor = "#CBD5E1";
      let strokeOpacity = "0.7";
      let edgeLabelStr = "";

      if (isSankeyMass) {
        const massVal = getEdgeMass(edge, fromNode);
        strokeWidth = Math.min(22, Math.max(3, Math.round(massVal * 18)));
        strokeColor = "#059669";
        strokeOpacity = "0.85";
        edgeLabelStr = `${edge.flow || 'Mass Flow'} (${massVal.toFixed(3)} kg)`;
      } else if (isSankeyEnergy) {
        const energyVal = getEdgeEnergy(edge, fromNode);
        // Ribbon proporcional al flujo energético acumulado: 0.28 kWh -> ~9px, 0.42 kWh -> ~13px
        strokeWidth = Math.min(22, Math.max(4, Math.round(energyVal * 32)));
        strokeColor = "#0284C7";
        strokeOpacity = "0.88";
        edgeLabelStr = `${edge.flow || 'Energy Flow'} (${energyVal.toFixed(2)} kWh)`;
      } else {
        edgeLabelStr = `${edge.flow || 'Flow'} (${Number(edge.amount || 1.0).toFixed(2)} ${edge.unit || 'kg'})`;
      }

      const edgeGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      edgeGroup.setAttribute("class", "canvas-edge-group");
      edgeGroup.setAttribute("data-edge-id", edge.id || "");

      // 1. Hit-path invisible ancho (28px) para captura táctil y de cursor sin esfuerzo
      const hitPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
      hitPath.setAttribute("class", "canvas-edge-hitpath");
      hitPath.setAttribute("d", pathD);
      hitPath.setAttribute("stroke", "transparent");
      hitPath.setAttribute("stroke-width", "28");
      hitPath.setAttribute("fill", "none");
      hitPath.setAttribute("stroke-linecap", "round");
      hitPath.style.cursor = "pointer";
      hitPath.style.pointerEvents = "stroke";
      hitPath.setAttribute("title", `Flujo: ${edge.flow}. Haz clic para desconectar este enlace.`);
      edgeGroup.appendChild(hitPath);

      // 2. Trazo visible de la conexión
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", "canvas-edge-path");
      path.setAttribute("d", pathD);
      path.setAttribute("stroke", strokeColor);
      path.setAttribute("stroke-width", String(strokeWidth));
      path.setAttribute("stroke-opacity", strokeOpacity);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke-linecap", "round");
      path.style.cursor = "pointer";
      path.style.pointerEvents = "stroke";
      path.setAttribute("title", `Flujo: ${edge.flow}. Haz clic para desconectar este enlace.`);
      edgeGroup.appendChild(path);

      // 3. Círculo decorativo en el punto de destino
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x2);
      circle.setAttribute("cy", y2);
      const circleR = isSankeyMass ? (strokeWidth > 12 ? "7" : "5") : isSankeyEnergy ? "5" : "4";
      circle.setAttribute("r", circleR);
      circle.setAttribute("fill", isSankeyMass ? "#059669" : (isSankeyEnergy ? "#0284C7" : "#64748B"));
      circle.style.pointerEvents = "none";
      edgeGroup.appendChild(circle);

      // 4. Insignia interactiva con botón ✕ en el punto medio sin truncamiento anti-HIG
      const midX = (x1 + x2) / 2;
      const midY = (y1 + y2) / 2;
      const labelStr = edgeLabelStr;
      const maxLen = 46;
      const displayTxt = labelStr.length > maxLen ? (labelStr.slice(0, maxLen - 2) + '…') : labelStr;
      const pillWidth = Math.max(100, Math.min(295, displayTxt.length * 6.8 + 34));
      const pillHeight = 22;
      const pillHalfW = pillWidth / 2;
      const pillHalfH = pillHeight / 2;

      const badgeGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      badgeGroup.setAttribute("class", "canvas-edge-badge");
      badgeGroup.setAttribute("transform", `translate(${midX}, ${midY})`);
      badgeGroup.style.cursor = "pointer";
      badgeGroup.style.pointerEvents = "all";
      badgeGroup.setAttribute("title", `Flujo: ${labelStr}. Haz clic para desconectar.`);

      const pillRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      pillRect.setAttribute("x", String(-pillHalfW));
      pillRect.setAttribute("y", String(-pillHalfH));
      pillRect.setAttribute("width", String(pillWidth));
      pillRect.setAttribute("height", String(pillHeight));
      pillRect.setAttribute("rx", "11");
      pillRect.setAttribute("ry", "11");
      pillRect.setAttribute("fill", "#FFFFFF");
      pillRect.setAttribute("stroke", isSankeyMass ? "#059669" : (isSankeyEnergy ? "#0284C7" : "#CBD5E1"));
      pillRect.setAttribute("stroke-width", "1.2");
      pillRect.style.filter = "drop-shadow(0 1px 3px rgba(0,0,0,0.12))";
      badgeGroup.appendChild(pillRect);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("class", "edge-label-text");
      text.setAttribute("x", String(-pillHalfW + 12));
      text.setAttribute("y", "3.5");
      text.setAttribute("font-size", "9");
      text.setAttribute("font-family", "Roboto Mono, monospace");
      text.setAttribute("font-weight", "600");
      text.setAttribute("fill", isSankeyMass ? "#059669" : (isSankeyEnergy ? "#0284C7" : "#475569"));
      text.style.pointerEvents = "none";
      text.textContent = displayTxt;
      badgeGroup.appendChild(text);

      const closeIcon = document.createElementNS("http://www.w3.org/2000/svg", "text");
      closeIcon.setAttribute("class", "edge-close-icon");
      closeIcon.setAttribute("x", String(pillHalfW - 12));
      closeIcon.setAttribute("y", "3.5");
      closeIcon.setAttribute("font-size", "10");
      closeIcon.setAttribute("font-weight", "bold");
      closeIcon.setAttribute("fill", "#94A3B8");
      closeIcon.setAttribute("text-anchor", "middle");
      closeIcon.style.pointerEvents = "none";
      closeIcon.textContent = "✕";
      badgeGroup.appendChild(closeIcon);

      edgeGroup.appendChild(badgeGroup);

      // Manejador centralizado de desconexión
      const handleDisconnect = (e) => {
        if (e) {
          e.stopPropagation();
          e.preventDefault();
        }
        if (state.connectingFromNode) {
          cancelConnection();
          return;
        }
        const flowDesc = edge.flow || "este flujo";
        const fromName = fromNode.name || "Origen";
        const toName = toNode.name || "Destino";
        if (confirm(`¿Deseas desconectar el flujo "${flowDesc}" entre "${fromName}" y "${toName}"?`)) {
          state.canvasEdges = (state.canvasEdges || []).filter(ed => {
            if (edge.id && ed.id) return ed.id !== edge.id;
            if (ed === edge) return false;
            const sameFrom = (ed.from === edge.from || String(ed.source_process_id) === String(edge.source_process_id));
            const sameTo = (ed.to === edge.to || String(ed.target_process_id) === String(edge.target_process_id));
            const sameFlow = (ed.flow === edge.flow);
            return !(sameFrom && sameTo && sameFlow);
          });
          renderCanvasEdges();
          scheduleAutoSaveCanvas();
          showNotification(`Flujo "${flowDesc}" desconectado.`);
        }
      };

      hitPath.addEventListener("click", handleDisconnect);
      path.addEventListener("click", handleDisconnect);
      badgeGroup.addEventListener("click", handleDisconnect);

      svg.appendChild(edgeGroup);
    });

    // Render dashed connector lines for canvas sticky notes if visible (except for client role)
    const isClientRole = state.activeUser && state.activeUser.role === "client";
    if (state.showCanvasStickyNotes && !isClientRole && state.comments && state.comments.length > 0) {
      renderStickyConnectorLines(svg);
    }
  }

  function renderStickyConnectorLines(svg) {
    const defaultCoords = [
      { x: 320, y: 30, targetNodeId: "node_inyeccion" },
      { x: 580, y: 20, targetNodeId: "node_soplado" },
      { x: 800, y: 160, targetNodeId: "node_transporte" }
    ];

    state.comments.forEach((c, idx) => {
      const coord = defaultCoords[idx % defaultCoords.length];
      const targetNode = state.canvasNodes.find(n => n.id === (c.node_id || coord.targetNodeId));
      if (!targetNode) return;

      const noteX = c.x || coord.x;
      const noteY = c.y || coord.y;
      const nodeX = (targetNode.x || 60) + 110;
      const nodeY = (targetNode.y || 140) + 30;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const d = `M ${noteX + 90} ${noteY + 70} Q ${(noteX + nodeX) / 2} ${(noteY + nodeY) / 2 + 20} ${nodeX} ${nodeY}`;
      path.setAttribute("d", d);
      path.setAttribute("stroke", c.author_role === "auditor" ? "#EAB308" : c.author_role === "analyst" ? "#3B82F6" : "#10B981");
      path.setAttribute("stroke-width", "1.5");
      path.setAttribute("stroke-dasharray", "4 4");
      path.setAttribute("stroke-opacity", "0.6");
      path.setAttribute("fill", "none");
      svg.appendChild(path);
    });
  }

  function renderCanvasStickyNotes() {
    const layer = document.getElementById("canvasStickyNotesLayer");
    if (!layer) return;

    // En el perfil de cliente nunca se deben mostrar las notas u observaciones en el lienzo
    const isClientRole = state.activeUser && state.activeUser.role === "client";
    if (!state.showCanvasStickyNotes || isClientRole) {
      layer.innerHTML = "";
      return;
    }

    const defaultCoords = [
      { x: 320, y: 30, targetNodeId: "node_inyeccion" },
      { x: 580, y: 20, targetNodeId: "node_soplado" },
      { x: 800, y: 160, targetNodeId: "node_transporte" }
    ];

    const activeSysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = (activeSysId === 21 || activeSysId === 1);
    const rawComments = (state.comments && state.comments.length > 0) ? state.comments : [];
    const seenNotes = new Set();
    const commentsToRender = [];
    for (const c of rawComments) {
      const belongs = isOfficialSys ? (c.system_id === 21 || c.system_id === 1) : (c.system_id === activeSysId);
      if (!belongs) continue;

      const key = `${c.system_id}_${(c.content || "").trim().toLowerCase()}`;
      if (!seenNotes.has(key)) {
        seenNotes.add(key);
        commentsToRender.push(c);
      }
    }
    if (commentsToRender.length === 0) {
      layer.innerHTML = "";
      return;
    }

    layer.innerHTML = commentsToRender.map((c, idx) => {
      const coord = defaultCoords[idx % defaultCoords.length];
      const posX = c.x || coord.x;
      const posY = c.y || coord.y;
      const roleCls = c.author_role === "auditor" ? "role-auditor" : c.author_role === "analyst" ? "role-analyst" : "role-client";
      const roleLabel = c.author_role === "auditor" ? "AUDITOR" : c.author_role === "analyst" ? "ANALISTA" : "CLIENTE";
      const isResolved = c.status === "resolved";

      const currentUserName = state.activeUser ? state.activeUser.display_name : "Carla Méndez";
      const currentUserRole = state.activeUser ? state.activeUser.role : "analyst";
      const canDelete = (c.author_name === currentUserName || c.author_role === currentUserRole || currentUserRole === "auditor");

      return `
        <div class="canvas-sticky-note ${roleCls}" id="sticky_note_${c.id}" style="left: ${posX}px; top: ${posY}px;">
          <div class="sticky-header-row">
            <span>● ${roleLabel}: ${c.author_name ? c.author_name.split(' ')[0] : 'Nota'}</span>
            <span style="font-size: 8.5px; opacity: 0.8;">${isResolved ? '✓ Resuelto' : '⚠️ Pendiente'}</span>
          </div>
          <div class="sticky-content-body">${c.content}</div>
          <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center; gap: 4px;">
            ${canDelete ? `<button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px; color: #EF4444;" onclick="window.EconodeApp.deleteComment(${c.id})" title="Eliminar observación">🗑 Eliminar</button>` : '<span></span>'}
            <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px;" onclick="window.EconodeApp.showView('report')">Ver en Reporte ➔</button>
          </div>
        </div>
      `;
    }).join('');

    // Enable dragging of sticky notes
    layer.querySelectorAll(".canvas-sticky-note").forEach((noteEl) => {
      noteEl.addEventListener("mousedown", (e) => {
        if (e.target.tagName === "BUTTON") return;
        e.stopPropagation();
        const noteId = parseInt(noteEl.id.replace("sticky_note_", ""), 10);
        const commentObj = commentsToRender.find(c => c.id === noteId);

        const startX = e.clientX;
        const startY = e.clientY;
        const initialLeft = parseFloat(noteEl.style.left) || 0;
        const initialTop = parseFloat(noteEl.style.top) || 0;

        function onMouseMove(moveEvent) {
          const dx = moveEvent.clientX - startX;
          const dy = moveEvent.clientY - startY;
          const newLeft = Math.max(10, initialLeft + dx);
          const newTop = Math.max(10, initialTop + dy);
          noteEl.style.left = `${newLeft}px`;
          noteEl.style.top = `${newTop}px`;
          if (commentObj) {
            commentObj.x = newLeft;
            commentObj.y = newTop;
          }
          renderCanvasEdges();
        }

        function onMouseUp() {
          document.removeEventListener("mousemove", onMouseMove);
          document.removeEventListener("mouseup", onMouseUp);
        }

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
      });
    });
  }

  function startDragNode(e, node, el) {
    if (e.button !== 0) return;
    e.stopPropagation();

    const startX = e.clientX;
    const startY = e.clientY;
    const initialLeft = node.x || 60;
    const initialTop = node.y || 140;
    const zoom = state.canvasZoom || 1.0;

    function onMouseMove(moveEvent) {
      const dx = (moveEvent.clientX - startX) / zoom;
      const dy = (moveEvent.clientY - startY) / zoom;
      node.x = Math.max(10, Math.round(initialLeft + dx));
      node.y = Math.max(10, Math.round(initialTop + dy));
      el.style.left = `${node.x}px`;
      el.style.top = `${node.y}px`;
      renderCanvasEdges();
    }

    function onMouseUp() {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      node.pos_x = node.x;
      node.pos_y = node.y;
      scheduleAutoSaveCanvas();
    }

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }

  // Conectar Nodos
  function startConnection(sourceNode) {
    state.connectingFromNode = sourceNode;
    state.connectingToNode = null;
    const banner = document.getElementById("connectHelpBanner");
    if (banner) {
      banner.style.display = "block";
      banner.innerHTML = `⚡ Connecting output of: <strong>${sourceNode.name}</strong>. Click destination process to complete link. <button id="btnCancelConnect" style="background: transparent; border: none; color: #FCA5A5; margin-left: 8px; cursor: pointer; text-decoration: underline;">Cancel</button>`;
      const btnCancel = document.getElementById("btnCancelConnect");
      if (btnCancel) {
        btnCancel.addEventListener("click", cancelConnection);
      }
    }
    document.querySelectorAll(".process-node-card").forEach(c => {
      const cid = c.id.replace("canvas_node_", "");
      if (cid !== String(sourceNode.id) && cid !== `node_${sourceNode.process_id}`) {
        c.classList.add("connect-target-candidate");
      }
    });
    showNotification(`Source: ${sourceNode.name}. Click destination process.`);
  }

  function completeConnection(targetNode) {
    if (!state.connectingFromNode) {
      showNotification("Please click the outlet port [🡆] on the source node first.");
      return;
    }
    const source = state.connectingFromNode;
    const target = targetNode;
    if (source.id === target.id || String(source.process_id) === String(target.process_id)) {
      showNotification("A node cannot be connected to itself.");
      return;
    }

    state.connectingToNode = target;

    // Quitar resaltado de candidatos
    document.querySelectorAll(".process-node-card").forEach(c => {
      c.classList.remove("connect-target-candidate");
    });

    // Abrir Modal de Conexión
    const modal = document.getElementById("modalConnectNodes");
    const staticBox = document.getElementById("connectNodesStaticBox");
    const selectBox = document.getElementById("connectNodesSelectBox");
    if (staticBox) staticBox.style.display = "block";
    if (selectBox) selectBox.style.display = "none";

    const srcLbl = document.getElementById("connectSourceLabel");
    const tgtLbl = document.getElementById("connectTargetLabel");
    const flowInput = document.getElementById("inputConnectFlowName");
    const amtInput = document.getElementById("inputConnectAmount");
    const unitInput = document.getElementById("inputConnectUnit");

    if (srcLbl) srcLbl.textContent = `${source.name} (ID #${source.process_id || source.id})`;
    if (tgtLbl) tgtLbl.textContent = `${target.name} (ID #${target.process_id || target.id})`;

    const refFlow = source.reference_flow || {};
    const defaultFlowName = refFlow.name || source.name || "Connected Flow";
    const defaultAmt = refFlow.amount !== undefined ? refFlow.amount : (source.amount || 1.0);
    const defaultUnit = refFlow.unit || source.unit || "kg";

    if (flowInput) flowInput.value = defaultFlowName;
    if (amtInput) amtInput.value = Number(defaultAmt).toFixed(3);
    if (unitInput) unitInput.value = defaultUnit;

    const selectSourceFlow = document.getElementById("selectConnectSourceFlow");
    if (selectSourceFlow) {
      let opts = `<option value="">-- Main flow: ${defaultFlowName} (${defaultAmt} ${defaultUnit}) --</option>`;
      if (source.outputs && Array.isArray(source.outputs) && source.outputs.length > 0) {
        source.outputs.forEach((out, oIdx) => {
          const typeBadge = out.is_reference ? '⭐ [Reference]' : out.is_waste ? '♻️ [Waste]' : '⚡ [Emission/Output]';
          opts += `<option value="${oIdx}">${typeBadge} ${out.name} (${Number(out.amount || 1.0).toFixed(3)} ${out.unit || 'kg'})</option>`;
        });
      }
      selectSourceFlow.innerHTML = opts;
      selectSourceFlow.onchange = () => {
        const selVal = selectSourceFlow.value;
        if (selVal !== "" && source.outputs && source.outputs[selVal]) {
          const chosen = source.outputs[selVal];
          flowInput.value = chosen.name;
          amtInput.value = Number(chosen.amount || 1.0).toFixed(3);
          unitInput.value = chosen.unit || "kg";
        } else {
          flowInput.value = defaultFlowName;
          amtInput.value = Number(defaultAmt).toFixed(3);
          unitInput.value = defaultUnit;
        }
      };
    }

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
    }
  }

  function cancelConnection() {
    state.connectingFromNode = null;
    state.connectingToNode = null;
    const banner = document.getElementById("connectHelpBanner");
    if (banner) banner.style.display = "none";
    document.querySelectorAll(".process-node-card").forEach(c => {
      c.classList.remove("connect-target-candidate");
    });
  }

  function inspectNode(node) {
    state.selectedNode = node;
    const inspCategory = document.getElementById("inspCategoryBadge");
    const inspDetails = document.getElementById("inspectorDetails");

    if (!node) {
      if (inspCategory) {
        inspCategory.textContent = window.I18n ? window.I18n.t("canvas.inspector_none", "No process selected") : "No process selected";
        inspCategory.className = "badge-pill badge-slate";
      }
      if (inspDetails) {
        inspDetails.innerHTML = `
          <div style="padding: 24px 12px; text-align: center; color: var(--text-muted);">
            <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
            <div style="font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">${window.I18n ? window.I18n.t("canvas.inspector_title", "Process Inspector") : "Process Inspector"}</div>
            <div style="font-size: 11px; line-height: 1.45;">${window.I18n ? window.I18n.t("canvas.inspector_empty", "Select a canvas node or add a process from the palette to inspect technosphere exchanges, unit inputs, and waste flows.") : "Select a canvas node or add a process from the palette to inspect technosphere exchanges, unit inputs, and waste flows."}</div>
          </div>
        `;
      }
      return;
    }

    if (inspCategory) {
      inspCategory.textContent = node.category || "Process";
      inspCategory.className = "badge-pill badge-emerald";
    }
    if (inspDetails) {
      const inputs = node.inputs || [
        { name: "Input 1 (Unit Flow)", amount: 1.0, unit: "kg", is_unit: true },
        { name: "Input 2 (Energy)", amount: 0.35, unit: "kWh", is_unit: false },
        { name: "Input 3 (Auxiliary)", amount: 0.02, unit: "kg", is_unit: false }
      ];

      const outputs = node.outputs || [
        { name: node.reference_flow ? node.reference_flow.name : "Main Product", amount: 1.0, unit: "kg", is_reference: true },
        { name: "Technical Scrap (Waste)", amount: 0.05, unit: "kg", is_waste: true },
        { name: "Fossil CO2 Emissions [Air]", amount: 0.012, unit: "kg", is_elementary: true }
      ];

      const isAuditor = state.activeUser && state.activeUser.role === "auditor";
      const isClient = state.activeUser && state.activeUser.role === "client";

      let actionButtonsHtml = "";
      if (!isAuditor && !isClient) {
        actionButtonsHtml = `
          <button class="btn btn-primary btn-sm" style="width: 100%; margin-bottom: 6px;" onclick="window.EconodeApp.openProcessEditor('${node.id}')">
            ${window.I18n.t("app.edit_proc_btn", "✏️ Edit Process (Inputs & Outputs)")}
          </button>
          <button class="btn btn-secondary btn-sm" style="width: 100%; color: #EF4444;" onclick="window.EconodeApp.removeNode('${node.id}')">
            ${window.I18n.t("app.delete_node_btn", "Remove Node from Model")}
          </button>
        `;
      } else if (isAuditor) {
        actionButtonsHtml = `
          <button class="btn btn-secondary btn-sm" style="width: 100%;;" onclick="window.EconodeApp.commentOnNode('${node.name}')">
            ${window.I18n.t("app.comment_proc_btn", "💬 Add Observation to Process")}
          </button>
        `;
      } else {
        actionButtonsHtml = `
          <div style="font-size: 10px; color: var(--text-dim); text-align: center; padding: 4px;">${window.I18n.t("app.readonly_client", "Read Only Mode (Client)")}</div>
        `;
      }

      inspDetails.innerHTML = `
        <div style="margin-bottom: 14px;">
          <h3 style="font-size: 13.5px; font-weight: 700;">${node.name}</h3>
          <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">ID: <span class="mono">${node.id}</span> · ecoinvent 3.12 Cutoff</div>
        </div>

        <div style="background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px; margin-bottom: 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">${window.I18n.t("app.ref_flow_badge", "QUANTITATIVE REFERENCE FLOW (UF)")}</div>
          <div class="mono" style="font-size: 16px; font-weight: 700; color: var(--accent-emerald);">
            ${node.reference_flow ? `${Number(node.reference_flow.amount).toFixed(3)} ${node.reference_flow.unit} ${node.reference_flow.name}` : `${Number(node.amount || 1).toFixed(3)} ${node.unit || 'kg'}`}
          </div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); margin-bottom: 6px;">${window.I18n.t("app.tech_inputs_badge", "3 TECHNOSPHERE INPUTS (WITH UNIT FLOW):")}</div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${inputs.map(inp => `
              <div style="font-size: 10px; padding: 4px 6px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between;">
                <span>${inp.name} ${inp.is_unit ? '<span class="badge-pill badge-emerald" style="font-size: 7.5px;">UNIT</span>' : ''}</span>
                <span class="mono" style="font-weight: 700;">${Number(inp.amount).toFixed(3)} ${inp.unit}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div style="margin-bottom: 14px;">
          <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); margin-bottom: 6px;">${window.I18n.t("app.outputs_badge", "3 OUTPUTS (PRODUCT, WASTE & EMISSIONS):")}</div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${outputs.map(out => `
              <div style="font-size: 10px; padding: 4px 6px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between;">
                <span>${out.name} ${out.is_waste ? '<span class="badge-pill badge-slate" style="font-size: 7.5px;">WASTE</span>' : out.is_elementary ? '<span class="badge-pill badge-slate" style="font-size: 7.5px;">EMISSION</span>' : '<span class="badge-pill badge-emerald" style="font-size: 7.5px;">REF</span>'}</span>
                <span class="mono" style="font-weight: 700;">${Number(out.amount).toFixed(4)} ${out.unit}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div style="margin-top: 14px;">
          ${actionButtonsHtml}
        </div>
      `;
    }
  }

  function initDefaultPalette() {
    if (state.paletteProcesses && state.paletteProcesses.length > 0) return;
    state.paletteProcesses = [
      {
        id: "palette_inyeccion",
        process_id: 100001,
        name: "PET Preform Injection Molding",
        category: "Polymer Processing",
        location: "MX",
        unit: "kg",
        amount: 1.0,
        reference_flow: { name: "Standard clear PET preform 500ml", amount: 1.0, unit: "kg" },
        inputs: [
          { name: "Virgin PET granulate [GLO]", amount: 1.05, unit: "kg", is_unit: true },
          { name: "CFE electricity grid mix 230kV [MX]", amount: 0.28, unit: "kWh", is_unit: false },
          { name: "Demineralized process cooling water [MX]", amount: 0.015, unit: "m3", is_unit: false }
        ],
        outputs: [
          { name: "Standard clear PET preform 500ml", amount: 1.0, unit: "kg", is_reference: true },
          { name: "Purge PET plastic scrap (Waste)", amount: 0.05, unit: "kg", is_waste: true },
          { name: "Fossil CO2 emissions [Air]", amount: 0.012, unit: "kg", is_elementary: true }
        ]
      },
      {
        id: "palette_soplado",
        process_id: 100002,
        name: "PET Bottle Stretch Blow Molding",
        category: "Thermoforming & Blow Molding",
        location: "MX",
        unit: "u",
        amount: 1.0,
        reference_flow: { name: "Finished PET bottle 500ml", amount: 1.0, unit: "u" },
        inputs: [
          { name: "Clear PET preform (Connected Flow)", amount: 1.0, unit: "kg", is_unit: true },
          { name: "High-pressure compressed air (40 bar)", amount: 0.45, unit: "m3", is_unit: false },
          { name: "Thermoforming electricity CFE", amount: 0.14, unit: "kWh", is_unit: false }
        ],
        outputs: [
          { name: "Finished PET bottle 500ml", amount: 1.0, unit: "u", is_reference: true },
          { name: "Plastic trimming scrap (Waste)", amount: 0.002, unit: "kg", is_waste: true },
          { name: "Dissipated waste heat [Air]", amount: 0.005, unit: "MJ", is_elementary: true }
        ]
      },
      {
        id: "palette_distribucion",
        process_id: 100003,
        name: "PET Bottle Distribution & Logistics",
        category: "Distribution & Transport",
        location: "MX",
        unit: "u",
        amount: 1.0,
        reference_flow: { name: "Bottle distributed at distribution center", amount: 1.0, unit: "u" },
        inputs: [
          { name: "Finished PET bottle 500ml (Connected Flow)", amount: 1.0, unit: "u", is_unit: true },
          { name: "Automotive diesel fuel", amount: 0.008, unit: "l", is_unit: false },
          { name: "Freight lorry transport 16-32t [MX]", amount: 0.0084, unit: "t·km", is_unit: false }
        ],
        outputs: [
          { name: "Bottle distributed at distribution center", amount: 1.0, unit: "u", is_reference: true },
          { name: "Used lubricant oil (Waste)", amount: 0.0001, unit: "kg", is_waste: true },
          { name: "Diesel combustion emissions CO2 / NOx [Air]", amount: 0.022, unit: "kg", is_elementary: true }
        ]
      },
      {
        id: "palette_hdpe",
        process_id: 100004,
        name: "High-Density Polyethylene [HDPE] Granulate",
        category: "Polymers",
        location: "GLO",
        unit: "kg",
        amount: 1.0,
        reference_flow: { name: "High-Density Polyethylene [HDPE] Granulate", amount: 1.0, unit: "kg" },
        inputs: [
          { name: "Petrochemical ethylene monomer [GLO]", amount: 1.02, unit: "kg", is_unit: true },
          { name: "Polymerization electricity [GLO]", amount: 0.35, unit: "kWh", is_unit: false },
          { name: "Medium-pressure process steam", amount: 0.85, unit: "MJ", is_unit: false }
        ],
        outputs: [
          { name: "High-Density Polyethylene [HDPE] Granulate", amount: 1.0, unit: "kg", is_reference: true },
          { name: "Purge polymer scrap (Waste)", amount: 0.02, unit: "kg", is_waste: true },
          { name: "VOC emissions to air [Air]", amount: 0.001, unit: "kg", is_elementary: true }
        ]
      },
      {
        id: "palette_pp",
        process_id: 100005,
        name: "Polypropylene Homopolymer Resin [PP]",
        category: "Polymers",
        location: "GLO",
        unit: "kg",
        amount: 1.0,
        reference_flow: { name: "Polypropylene Homopolymer Resin [PP]", amount: 1.0, unit: "kg" },
        inputs: [
          { name: "Polymer-grade propylene [GLO]", amount: 1.03, unit: "kg", is_unit: true },
          { name: "CFE electricity grid mix 230kV [MX]", amount: 0.40, unit: "kWh", is_unit: false },
          { name: "Ziegler-Natta catalyst", amount: 0.0005, unit: "kg", is_unit: false }
        ],
        outputs: [
          { name: "Polypropylene Homopolymer Resin [PP]", amount: 1.0, unit: "kg", is_reference: true },
          { name: "Extrusion plastic scrap (Waste)", amount: 0.03, unit: "kg", is_waste: true },
          { name: "Process CO2 emissions [Air]", amount: 0.008, unit: "kg", is_elementary: true }
        ]
      },
      {
        id: "palette_cfe",
        process_id: 100006,
        name: "CFE Grid Electricity 230kV [MX]",
        category: "Energy",
        location: "MX",
        unit: "kWh",
        amount: 1.0,
        reference_flow: { name: "Medium-voltage electricity", amount: 1.0, unit: "kWh" },
        inputs: [
          { name: "Natural gas in combined cycle turbine [MX]", amount: 1.85, unit: "MJ", is_unit: true },
          { name: "Imported hard coal [MX]", amount: 0.08, unit: "kg", is_unit: false },
          { name: "Hydropower electricity from reservoir [MX]", amount: 0.15, unit: "kWh", is_unit: false }
        ],
        outputs: [
          { name: "Medium-voltage electricity", amount: 1.0, unit: "kWh", is_reference: true },
          { name: "Fly ash from coal combustion (Waste)", amount: 0.004, unit: "kg", is_waste: true },
          { name: "Fossil CO2 emissions [Air]", amount: 0.435, unit: "kg", is_elementary: true }
        ]
      }
    ];
  }

  function renderPaletteProcesses() {
    const list = document.getElementById("paletteProcessList");
    if (!list) return;

    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");
    if ((!state.paletteProcesses || state.paletteProcesses.length === 0) && isOfficialSys) {
      initDefaultPalette();
    }

    const search = (document.getElementById("inputPaletteSearch")?.value || "").toLowerCase();
    const filtered = (state.paletteProcesses || []).filter(p => {
      if (!search) return true;
      return (p.name || "").toLowerCase().includes(search) || (p.category || "").toLowerCase().includes(search);
    });

    if (filtered.length === 0) {
      list.innerHTML = `
        <div style="padding: 24px 14px; font-size: 11px; color: var(--text-muted); text-align: center;">
          <div style="font-size: 26px; margin-bottom: 6px;">📂</div>
          <div style="font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Process Palette Empty</div>
          <div style="font-size: 10px; line-height: 1.4; margin-bottom: 12px;">Search unit processes in the 26,533 ecoinvent catalog or create a blank process using the button above.</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            <button class="btn btn-secondary btn-sm" style="font-size: 10.5px;" onclick="window.EconodeApp.showView('catalog')">🔍 Explore LCI Catalog</button>
          </div>
        </div>
      `;
      return;
    }

    list.innerHTML = filtered
      .map(
        (p) => `
      <div class="palette-item" draggable="true" style="padding: 8px 10px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;" data-json='${JSON.stringify(p)}' data-id="${p.id}">
        <div style="flex: 1; cursor: pointer;" onclick="window.EconodeApp.openProcessEditor('${p.id}')">
          <div style="display: flex; align-items: center; gap: 4px;">
            <span class="mono" style="font-size: 8px; font-weight: 700; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 1px 3px; border-radius: 2px;">ID: #${p.process_id || p.id}</span>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-primary);">${p.name}</div>
          </div>
          <div style="font-size: 9.5px; color: var(--text-muted); margin-top: 2px;">${p.category || "Polymers"} · 1.00 ${p.unit || "kg"} · <span style="color: var(--accent-emerald);">${(p.inputs || []).length} In / ${(p.outputs || []).length} Out</span></div>
        </div>
        <div style="display: flex; gap: 4px; align-items: center;">
          <button class="btn btn-secondary btn-sm" title="Edit inputs and outputs" style="padding: 2px 6px; font-size: 10px;" onclick="window.EconodeApp.openProcessEditor('${p.id}')">✏️</button>
          <button class="btn btn-secondary btn-sm" title="Add to canvas" style="padding: 2px 6px; font-size: 10px;" onclick="window.EconodeApp.addPaletteNode('${p.id}')">+</button>
          <button class="btn btn-secondary btn-sm" title="Remove from palette" style="padding: 2px 6px; font-size: 10px; color: #EF4444;" onclick="window.EconodeApp.removePaletteProcess('${p.id}')">✕</button>
        </div>
      </div>
    `
      )
      .join("");

    // Habilitar dragstart
    list.querySelectorAll(".palette-item").forEach((el) => {
      el.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("application/json", el.getAttribute("data-json"));
      });
    });
  }

  function addNodeToCanvas(name, cat, unit, x = null, y = null, initialInputs = null, initialOutputs = null, processId = null) {
    const defaultInputs = [
      { name: "Primary Material [GLO]", amount: 1.05, unit: unit, is_unit: true },
      { name: "CFE Grid Electricity [MX]", amount: 0.25, unit: "kWh", is_unit: false },
      { name: "Industrial Process Water", amount: 0.01, unit: "m3", is_unit: false }
    ];
    const defaultOutputs = [
      { name: name, amount: 1.0, unit: unit, is_reference: true },
      { name: "Plastic Scrap (Waste)", amount: 0.05, unit: unit, is_waste: true },
      { name: "CO2 Emissions [Air]", amount: 0.01, unit: "kg", is_elementary: true }
    ];

    let numericProcessId = (processId && !isNaN(parseInt(processId, 10)))
      ? parseInt(processId, 10)
      : (100000 + (state.canvasNodes ? state.canvasNodes.length : 0) + 1);

    if (state.canvasNodes && state.canvasNodes.some(n => n.process_id === numericProcessId || n.id === `node_${numericProcessId}`)) {
      numericProcessId = 100000 + state.canvasNodes.length + 1;
      while (state.canvasNodes.some(n => n.process_id === numericProcessId || n.id === `node_${numericProcessId}`)) {
        numericProcessId++;
      }
    }

    const newNode = {
      id: `node_${numericProcessId}`,
      process_id: numericProcessId,
      name: name,
      category: cat || "Custom processes & flows",
      amount: 1.0,
      unit: unit || "kg",
      x: x || (60 + Math.random() * 80),
      y: y || (80 + Math.random() * 180),
      pos_x: x || (60 + Math.random() * 80),
      pos_y: y || (80 + Math.random() * 180),
      reference_flow: { name: name, amount: 1.0, unit: unit || "kg" },
      inputs: Array.isArray(initialInputs) ? JSON.parse(JSON.stringify(initialInputs)) : defaultInputs,
      outputs: Array.isArray(initialOutputs) ? JSON.parse(JSON.stringify(initialOutputs)) : defaultOutputs
    };
    state.canvasNodes.push(newNode);
    renderCanvasStage();
    scheduleAutoSaveCanvas();
    showNotification(`Process "${name}" added to canvas.`);
  }

  // =========================================================================
  // GESTIÓN DEL EDITOR VISUAL DE PROCESO (#modalProcessEditor)
  // =========================================================================
  function openProcessEditor(targetId) {
    let target = null;
    let isCanvasNode = false;
    let isNewProcess = false;

    if (!targetId) {
      isNewProcess = true;
      const newNum = 1000000 + Math.floor(Math.random() * 90000) + 1;
      target = {
        id: `custom_${newNum}`,
        process_id: newNum,
        name: "",
        code: `PR_CUSTOM_${newNum}`,
        category: "Custom processes & flows",
        category_id: 999999,
        location: "GLO",
        amount: 1.0,
        unit: "kg",
        reference_flow: { name: "", amount: 1.0, unit: "kg" },
        inputs: [],
        outputs: []
      };
    } else {
      const searchStr = String(targetId);
      target = state.canvasNodes.find(n => String(n.id) === searchStr || String(n.process_id) === searchStr);
      if (target) {
        isCanvasNode = true;
      } else {
        target = (state.paletteProcesses || []).find(p => String(p.id) === searchStr || String(p.process_id) === searchStr);
        isCanvasNode = false;
      }
      if (!target && typeof targetId === "object" && targetId !== null) {
        target = targetId;
        isCanvasNode = false;
      }
    }
    if (!target) return;

    state.editingProcess = { target, isCanvasNode, isNewProcess };

    const modal = document.getElementById("modalProcessEditor");
    const nameInput = document.getElementById("procEditName");
    const codeInput = document.getElementById("procEditCode");
    const catInput = document.getElementById("procEditCategory");
    const locInput = document.getElementById("procEditLocation");
    const refNameInput = document.getElementById("procEditRefFlowName");
    const refAmountInput = document.getElementById("procEditRefAmount");
    const refUnitInput = document.getElementById("procEditRefUnit");

    if (nameInput) {
      nameInput.value = target.name || "";
      nameInput.placeholder = "e.g. PET Preform Injection Molding...";
    }
    if (codeInput) codeInput.value = target.code || target.id || "";
    if (catInput) catInput.value = target.category || target.category_name || "Custom processes & flows";
    if (locInput) locInput.value = target.location || "GLO";

    const ref = target.reference_flow || { name: target.name || "", amount: target.amount || 1.0, unit: target.unit || "kg" };
    if (refNameInput) {
      refNameInput.value = ref.name || target.name || "";
      refNameInput.placeholder = "Name of primary output product...";
    }
    if (refAmountInput) refAmountInput.value = ref.amount || 1.0;
    if (refUnitInput) refUnitInput.value = ref.unit || target.unit || "kg";

    if (isNewProcess) {
      state.editingInputs = [];
      state.editingOutputs = [];
    } else {
      state.editingInputs = Array.isArray(target.inputs)
        ? JSON.parse(JSON.stringify(target.inputs))
        : [];

      state.editingOutputs = Array.isArray(target.outputs)
        ? JSON.parse(JSON.stringify(target.outputs))
        : (ref.name ? [{ name: ref.name, amount: ref.amount || 1.0, unit: ref.unit || "kg", is_reference: true }] : []);
    }

    const masterTitle = document.getElementById("procEditMasterTitle");
    const masterGeo = document.getElementById("procEditMasterGeo");
    const idBadge = document.getElementById("procEditIdBadge");
    if (masterTitle) masterTitle.textContent = target.name || (isNewProcess ? "New Blank Process" : "Unit Process");
    if (masterGeo) masterGeo.textContent = `[${target.location || 'GLO'}] ${target.category || 'Custom processes & flows'}`;
    if (idBadge) idBadge.textContent = `ID: #${target.process_id || target.id}`;

    renderProcessEditorCards();
    updateProcessMassBalance();

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      if (nameInput && isNewProcess) {
        setTimeout(() => nameInput.focus(), 50);
      }
    }
  }

  function updateProcessMassBalance() {
    const totalIn = (state.editingInputs || []).reduce((acc, i) => acc + (parseFloat(i.amount) || 0), 0);
    const refAmount = parseFloat(document.getElementById("procEditRefAmount")?.value || "1.0");
    const totalOutWaste = (state.editingOutputs || []).reduce((acc, o) => acc + (parseFloat(o.amount) || 0), 0);
    const totalOut = totalOutWaste; // Total sum of outputs (including reference flow)

    const inEl = document.getElementById("procBalanceInVal");
    const outEl = document.getElementById("procBalanceOutVal");
    const deltaEl = document.getElementById("procBalanceDeltaBadge");

    if (inEl) inEl.textContent = `${totalIn.toFixed(3)} kg`;
    if (outEl) outEl.textContent = `${totalOut.toFixed(3)} kg`;

    const delta = Math.abs(totalIn - totalOut);
    if (deltaEl) {
      if (delta < 0.005) {
        deltaEl.className = "badge-pill badge-emerald";
        deltaEl.textContent = `${delta.toFixed(3)} kg (100% Balanced)`;
      } else {
        deltaEl.className = "badge-pill badge-slate";
        deltaEl.style.color = "#D97706";
        deltaEl.textContent = `Δ ${delta.toFixed(3)} kg (Unbalanced)`;
      }
    }
  }

  function renderProcessEditorCards() {
    const inputsContainer = document.getElementById("procEditorInputsContainer");
    const outputsContainer = document.getElementById("procEditorOutputsContainer");
    const inCount = document.getElementById("procEditorInputCount");
    const outCount = document.getElementById("procEditorOutputCount");

    if (inCount) inCount.textContent = (state.editingInputs || []).length;
    if (outCount) outCount.textContent = (state.editingOutputs || []).length;

    if (inputsContainer) {
      if ((state.editingInputs || []).length === 0) {
        inputsContainer.innerHTML = `
          <div style="text-align: center; padding: 32px 14px; color: var(--text-muted); border: 1px dashed var(--border-color); border-radius: var(--radius-sm);">
            <div style="font-size: 20px; margin-bottom: 6px;">⚙️</div>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-secondary);">No input flows (Inputs)</div>
            <div style="font-size: 10px; margin-top: 2px;">Click <strong>+ Add Flow</strong> to add consumed products or resources.</div>
          </div>
        `;
      } else {
        inputsContainer.innerHTML = (state.editingInputs || []).map((inp, idx) => `
          <div class="proc-flow-card" draggable="true" data-idx="${idx}" data-type="input" style="border-left: 3px solid var(--accent-blue);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="badge-pill ${inp.is_unit ? 'badge-emerald' : 'badge-slate'}" style="font-size: 8.5px;">
                ⚙️ Technosphere Flow (Input)
              </span>
              <button type="button" style="background: none; border: none; color: #EF4444; font-size: 11px; cursor: pointer;" onclick="window.EconodeApp.removeEditInput(${idx})" title="Remove Input">✕</button>
            </div>

            <!-- Nombre del flujo de base de datos (openLCA Flow) -->
            <div style="display: flex; align-items: center; justify-content: space-between; margin: 3px 0;">
              <strong style="font-size: 11px; color: var(--text-primary); line-height: 1.2;">⚙️ ${inp.name}</strong>
              <span class="badge-pill badge-slate" style="font-size: 8px; margin-left: 4px;">Flow ID: ${inp.flow_id || 'ecoinvent'}</span>
            </div>

            <!-- Proveedor asignado (Provider - Proceso que produce este flujo) -->
            <div style="margin: 4px 0;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">PROVIDER (SUPPLYING PROCESS):</label>
                <button type="button" style="background: none; border: none; color: var(--accent-blue); font-size: 9.5px; font-weight: 600; cursor: pointer; text-decoration: underline;" onclick="window.EconodeApp.openSelectProviderModal(${idx})">🔍 Search Process</button>
              </div>
              <input type="text" class="form-input" style="height: 24px; font-size: 10px; margin-top: 2px;" value="${inp.provider || inp.supplier || 'Market ecoinvent 3.12 [GLO]'}" placeholder="Supplying unit process..." oninput="window.EconodeApp.updateEditInput(${idx}, 'provider', this.value)">
            </div>

            <!-- Cantidad y Unidad -->
            <div style="display: grid; grid-template-columns: 1fr 65px; gap: 6px; margin-top: 4px;">
              <div>
                <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">AMOUNT:</label>
                <input type="number" step="0.001" class="form-input mono" style="height: 26px; font-size: 10.5px; font-weight: 700; color: var(--accent-blue);" value="${inp.amount}" oninput="window.EconodeApp.updateEditInput(${idx}, 'amount', parseFloat(this.value) || 0); window.EconodeApp.updateMassBalance();">
              </div>
              <div>
                <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">UNIT:</label>
                <input type="text" class="form-input mono" style="height: 26px; font-size: 10px; background: var(--bg-muted);" value="${inp.unit || 'kg'}" readonly>
              </div>
            </div>
          </div>
        `).join('');

        // Enable drag & drop reordering for inputs
        inputsContainer.querySelectorAll(".proc-flow-card").forEach(card => {
          card.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("text/plain", card.dataset.idx);
            card.classList.add("dragging");
          });
          card.addEventListener("dragend", () => card.classList.remove("dragging"));
        });
      }
    }

    if (outputsContainer) {
      if ((state.editingOutputs || []).length === 0) {
        outputsContainer.innerHTML = `
          <div style="text-align: center; padding: 32px 14px; color: var(--text-muted); border: 1px dashed var(--border-color); border-radius: var(--radius-sm);">
            <div style="font-size: 20px; margin-bottom: 6px;">★</div>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-secondary);">No output flows (Outputs)</div>
            <div style="font-size: 10px; margin-top: 2px;">Click <strong>+ Add Flow</strong> to add reference product, waste or emissions.</div>
          </div>
        `;
      } else {
        outputsContainer.innerHTML = (state.editingOutputs || []).map((out, idx) => {
          const isRef = Boolean(out.is_reference);
          const flowIcon = isRef ? '★' : out.is_waste ? '🗑️' : out.is_elementary ? '🍃' : '⚙️';
          const badgeClass = isRef ? 'badge-emerald' : 'badge-slate';
          const badgeLabel = isRef 
            ? '★ Quantitative Reference' 
            : out.is_waste 
              ? '🗑️ Waste Flow' 
              : out.is_elementary 
                ? '🍃 Elementary Emission' 
                : '⚙️ Product Output';
          const borderStyle = isRef ? 'border-left: 3px solid var(--accent-emerald);' : out.is_waste ? 'border-left: 3px solid #D97706;' : 'border-left: 3px solid var(--border-color);';

          return `
            <div class="proc-flow-card" draggable="true" data-idx="${idx}" data-type="output" style="${borderStyle}">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px;">
                <div>
                  ${isRef ? `
                    <span class="badge-pill badge-emerald" style="font-size: 8.5px;">
                      ★ Quantitative Reference
                    </span>
                  ` : out.is_waste ? `
                    <span class="badge-pill badge-slate" style="font-size: 8.5px;">
                      🗑️ Waste Flow
                    </span>
                  ` : out.is_elementary ? `
                    <span class="badge-pill badge-slate" style="font-size: 8.5px;">
                      🍃 Elementary Emission
                    </span>
                  ` : ''}
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  ${!isRef ? `
                    <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 9px; height: 20px; color: var(--accent-emerald); font-weight: 600; border-color: rgba(5, 150, 105, 0.4);" onclick="window.EconodeApp.setAsQuantitativeReference(${idx})" title="Set as quantitative reference">
                      ★ Set as Ref
                    </button>
                  ` : ''}
                  <button type="button" style="background: none; border: none; color: #EF4444; font-size: 11px; cursor: pointer; padding: 2px;" onclick="window.EconodeApp.removeEditOutput(${idx})" title="Remove Output">✕</button>
                </div>
              </div>

              <!-- Nombre del flujo de salida -->
              <div style="display: flex; align-items: center; justify-content: space-between; margin: 3px 0;">
                <strong style="font-size: 11px; color: var(--text-primary); line-height: 1.2;">${flowIcon} ${out.name}</strong>
                <span class="badge-pill badge-slate" style="font-size: 8px; margin-left: 4px;">Flow ID: ${out.flow_id || 'ecoinvent'}</span>
              </div>

              <!-- Destino / Tratamiento (solo para residuos o salidas secundarias) -->
              <div style="margin: 4px 0;">
                <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">${out.is_waste ? 'WASTE TREATMENT / RECOVERY:' : out.is_elementary ? 'ENVIRONMENTAL COMPARTMENT:' : 'ROLE IN PRODUCT SYSTEM:'}</label>
                <input type="text" class="form-input" style="height: 24px; font-size: 10px; margin-top: 2px;" value="${out.provider || out.destination || (out.is_reference ? 'Main reference flow' : 'Municipal disposal / recycling')}" placeholder="Destination or treatment..." oninput="window.EconodeApp.updateEditOutput(${idx}, 'provider', this.value)">
              </div>

              <!-- Cantidad y Unidad -->
              <div style="display: grid; grid-template-columns: 1fr 65px; gap: 6px; margin-top: 4px;">
                <div>
                  <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">AMOUNT:</label>
                  <input type="number" step="0.001" class="form-input mono" style="height: 26px; font-size: 10.5px; font-weight: 700; color: var(--accent-emerald);" value="${out.amount}" oninput="window.EconodeApp.updateEditOutput(${idx}, 'amount', parseFloat(this.value) || 0); window.EconodeApp.updateMassBalance();">
                </div>
                <div>
                  <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">UNIT:</label>
                  <input type="text" class="form-input mono" style="height: 26px; font-size: 10px; background: var(--bg-muted);" value="${out.unit || 'kg'}" readonly>
                </div>
              </div>
            </div>
          `;
        }).join('');

        // Enable drag & drop reordering for outputs
        outputsContainer.querySelectorAll(".proc-flow-card").forEach(card => {
          card.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("text/plain", card.dataset.idx);
            card.classList.add("dragging");
          });
          card.addEventListener("dragend", () => card.classList.remove("dragging"));
        });
      }
    }

    updateProcessMassBalance();
  }

  // =========================================================================
  // SELECTOR MODAL DE FLUJOS EXISTENTES EN LA BASE DE DATOS LCI
  // =========================================================================
  let currentFlowSelectTarget = "input"; // "input" | "output"

  function openSelectDbFlowModal(targetType = "input") {
    currentFlowSelectTarget = targetType;
    const modal = document.getElementById("modalSelectDbFlow");
    const titleEl = document.getElementById("selectFlowTitle");
    const typeSelect = document.getElementById("selectDbFlowType");

    if (titleEl) {
      titleEl.textContent = targetType === "input"
        ? "Select Input from Database (ecoinvent)"
        : "Select Waste / Emission from Database";
    }
    if (typeSelect) {
      typeSelect.value = targetType === "input" ? "PRODUCT_FLOW" : "WASTE_FLOW";
    }

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
    }
    loadDbFlowsList();
  }

  async function loadDbFlowsList() {
    const container = document.getElementById("dbFlowsListContainer");
    const searchInput = document.getElementById("inputSearchDbFlows");
    const typeSelect = document.getElementById("selectDbFlowType");

    if (!container) return;
    const q = searchInput ? searchInput.value.trim() : "";
    const type = typeSelect ? typeSelect.value : "ALL";

    container.innerHTML = `<div style="text-align: center; padding: 20px; font-size: 11px; color: var(--text-muted);">Querying flows in ecoinvent 3.12...</div>`;

    try {
      const res = await api.getDbFlows(q, type, 30);
      const items = res.items || [];
      if (items.length === 0) {
        container.innerHTML = `<div style="text-align: center; padding: 20px; font-size: 11px; color: var(--text-muted);">No flows found with that term in the database.</div>`;
        return;
      }

      container.innerHTML = items.map(f => `
        <div style="padding: 8px 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.15s ease;"
             onmouseover="this.style.background='var(--bg-subtle)'"
             onmouseout="this.style.background='var(--bg-card)'"
             onclick="window.EconodeApp.confirmInsertDbFlow('${f.id}', '${escape(f.name)}', '${f.unit_symbol || 'kg'}', '${f.flow_type}')">
          <div>
            <strong style="font-size: 11.5px; color: var(--text-primary);">${f.name}</strong>
            <div style="font-size: 9.5px; color: var(--text-muted);">${f.flow_type === 'PRODUCT_FLOW' ? 'Product / Technosphere Flow' : f.flow_type === 'WASTE_FLOW' ? 'Waste Flow' : 'Elementary Biospheric Emission'} · Unit: <span class="mono" style="font-weight: 700; color: var(--accent-emerald);">${f.unit_symbol || 'kg'}</span></div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 2px 8px;">+ Select</button>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div style="text-align: center; padding: 20px; font-size: 11px; color: #EF4444;">Error loading flows: ${err.message}</div>`;
    }
  }

  function confirmInsertDbFlow(flowId, escapedName, unitSymbol, flowType) {
    const flowName = unescape(escapedName);
    const modal = document.getElementById("modalSelectDbFlow");
    if (modal) {
      modal.classList.remove("active");
      modal.style.display = "none";
    }

    if (currentFlowSelectTarget === "input") {
      state.editingInputs.push({
        flow_id: flowId,
        name: flowName,
        amount: 1.0,
        unit: unitSymbol || "kg",
        provider: "Market ecoinvent 3.12 [GLO]",
        is_unit: flowType === "PRODUCT_FLOW"
      });
      showNotification(`Official input "${flowName}" added. Adjust quantity and provider.`);
    } else {
      state.editingOutputs.push({
        flow_id: flowId,
        name: flowName,
        amount: 0.05,
        unit: unitSymbol || "kg",
        provider: "Municipal Manager / Recycling",
        is_waste: flowType === "WASTE_FLOW",
        is_elementary: flowType === "ELEMENTARY_FLOW",
        is_reference: false,
        compartment: flowType === "ELEMENTARY_FLOW" ? "Air" : "N/A"
      });
      showNotification(`Official output "${flowName}" added. Adjust quantity and destination.`);
    }

    renderProcessEditorCards();
  }

  function setupSelectDbFlowModal() {
    const modal = document.getElementById("modalSelectDbFlow");
    const btnClose = document.getElementById("btnCloseSelectFlowModal");
    const btnCancel = document.getElementById("btnCancelSelectFlowModal");
    const searchInput = document.getElementById("inputSearchDbFlows");
    const typeSelect = document.getElementById("selectDbFlowType");
    const btnOpenCustomFlow = document.getElementById("btnOpenCreateCustomFlowModal");

    const close = () => {
      if (modal) {
        modal.classList.remove("active");
        modal.style.display = "none";
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (btnOpenCustomFlow) {
      btnOpenCustomFlow.addEventListener("click", () => {
        openCreateCustomFlowModal();
      });
    }

    if (searchInput) {
      let debounce = null;
      searchInput.addEventListener("input", () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => loadDbFlowsList(), 300);
      });
    }

    if (typeSelect) {
      typeSelect.addEventListener("change", loadDbFlowsList);
    }
  }

  // =========================================================================
  // MODAL CREACIÓN DE FLUJO PROPIO EN BLANCO (ESTILO OPENLCA)
  // =========================================================================
  function openCreateCustomFlowModal() {
    const modal = document.getElementById("modalCreateCustomFlow");
    const nameInput = document.getElementById("inputNewFlowName");
    const typeSelect = document.getElementById("selectNewFlowType");
    const propSelect = document.getElementById("selectNewFlowProperty");
    const unitInput = document.getElementById("inputNewFlowUnit");
    const descInput = document.getElementById("inputNewFlowDesc");

    if (nameInput) nameInput.value = "";
    if (typeSelect) {
      typeSelect.value = (currentFlowSelectTarget === "input") ? "PRODUCT_FLOW" : "WASTE_FLOW";
    }
    if (propSelect) propSelect.value = "Mass";
    if (unitInput) unitInput.value = "kg";
    if (descInput) descInput.value = "";

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      if (nameInput) nameInput.focus();
    }
  }

  function setupCreateCustomFlowModal() {
    const modal = document.getElementById("modalCreateCustomFlow");
    const btnClose = document.getElementById("btnCloseCreateCustomFlowModal");
    const btnCancel = document.getElementById("btnCancelCreateCustomFlow");
    const btnSave = document.getElementById("btnSaveCreateCustomFlow");
    const propSelect = document.getElementById("selectNewFlowProperty");
    const unitInput = document.getElementById("inputNewFlowUnit");

    if (propSelect && unitInput) {
      propSelect.addEventListener("change", (e) => {
        const selectedOption = e.target.options[e.target.selectedIndex];
        const defaultUnit = selectedOption.getAttribute("data-unit") || "kg";
        unitInput.value = defaultUnit;
      });
    }

    const close = () => {
      if (modal) {
        modal.classList.remove("active");
        modal.style.display = "none";
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (btnSave) {
      btnSave.addEventListener("click", async () => {
        const nameInput = document.getElementById("inputNewFlowName");
        const typeSelect = document.getElementById("selectNewFlowType");
        const propSel = document.getElementById("selectNewFlowProperty");
        const unitInp = document.getElementById("inputNewFlowUnit");
        const descInput = document.getElementById("inputNewFlowDesc");

        const name = (nameInput?.value || "").trim();
        if (!name) {
          showNotification("Por favor ingresa un nombre para el flujo.");
          if (nameInput) nameInput.focus();
          return;
        }

        const flowType = typeSelect?.value || "PRODUCT_FLOW";
        const refProperty = propSel?.value || "Mass";
        const unitSymbol = (unitInp?.value || "kg").trim();
        const description = (descInput?.value || "").trim();

        try {
          btnSave.disabled = true;
          btnSave.textContent = "Saving...";

          const res = await api.createCustomFlow({
            name: name,
            flow_type: flowType,
            reference_flow_property: refProperty,
            unit_symbol: unitSymbol,
            description: description,
            category_name: "Custom processes & flows"
          });

          if (res && res.flow) {
            close();
            confirmInsertDbFlow(res.flow.code || res.flow.id, escape(res.flow.name), res.flow.unit_symbol, res.flow.flow_type);
            showNotification(`Custom flow "${name}" created successfully.`);
            if (state.currentView === "catalog") {
              loadCatalog();
            }
          } else {
            throw new Error(res?.message || "Error creating flow");
          }
        } catch (err) {
          console.error("Error creating custom flow:", err);
          showNotification(`Error creating flow: ${err.message}`);
        } finally {
          btnSave.disabled = false;
          btnSave.textContent = "Save Flow ➔";
        }
      });
    }
  }

  // =========================================================================
  // SELECTOR DE PROCESO PROVEEDOR EN LA BASE DE DATOS (ESTILO OPENLCA)
  // =========================================================================
  let currentProviderInputIndex = null;

  async function openSelectProviderModal(inputIndex) {
    currentProviderInputIndex = inputIndex;
    const inp = (state.editingInputs || [])[inputIndex];
    if (!inp) return;

    const modal = document.getElementById("modalSelectProvider");
    const title = document.getElementById("selectProviderTitle");
    const sub = document.getElementById("selectProviderSubtitle");
    const search = document.getElementById("inputSearchProvider");

    if (title) title.textContent = `Provider for "${inp.name}"`;
    if (sub) sub.textContent = `Select the ecoinvent 3.12 unit process supplying this input.`;
    if (search) search.value = "";

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
    }

    await loadProviderList(inp.name);
  }

  async function loadProviderList(flowName = "") {
    const container = document.getElementById("providerListContainer");
    const searchInput = document.getElementById("inputSearchProvider");
    if (!container) return;

    const filterText = searchInput ? searchInput.value.trim().toLowerCase() : "";
    container.innerHTML = `<div style="text-align: center; padding: 18px; font-size: 11px; color: var(--text-muted);">Searching provider processes in ecoinvent 3.12...</div>`;

    try {
      const res = await api.getDbProviders(flowName, 25);
      let items = res.items || [];

      if (filterText) {
        items = items.filter(p => (p.name || "").toLowerCase().includes(filterText) || (p.location || "").toLowerCase().includes(filterText));
      }

      if (items.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 18px; font-size: 11px; color: var(--text-muted);">
            No direct processes found for "${flowName}". You can assign a global market:
            <div style="margin-top: 10px;">
              <button type="button" class="btn btn-secondary btn-sm" onclick="window.EconodeApp.selectProviderForInput('market for ${escape(flowName)} [GLO]')">Assign Global Market [GLO]</button>
            </div>
          </div>
        `;
        return;
      }

      container.innerHTML = items.map(p => `
        <div style="padding: 10px 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.15s ease;"
             onmouseover="this.style.background='var(--bg-subtle)'"
             onmouseout="this.style.background='var(--bg-card)'"
             onclick="window.EconodeApp.selectProviderForInput('${escape(p.name)} [${p.location || 'GLO'}]')">
          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <strong style="font-size: 11.5px; color: var(--text-primary);">${p.name}</strong>
              <span class="badge-pill badge-emerald" style="font-size: 8.5px;">${p.location || 'GLO'}</span>
            </div>
            <div style="font-size: 9.5px; color: var(--text-muted); margin-top: 2px;">
              Process ID: <span class="mono">${p.id}</span> · Reference Output: ${p.ref_flow_name || flowName} (${p.unit || 'kg'})
            </div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 2px 8px;">Connect ➔</button>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div style="text-align: center; padding: 18px; font-size: 11px; color: #EF4444;">Error querying providers: ${err.message}</div>`;
    }
  }

  function selectProviderForInput(escapedProviderName) {
    const providerName = unescape(escapedProviderName);
    if (currentProviderInputIndex !== null && state.editingInputs[currentProviderInputIndex]) {
      state.editingInputs[currentProviderInputIndex].provider = providerName;
      showNotification(`Provider assigned: "${providerName}"`);
      renderProcessEditorCards();
    }
    const modal = document.getElementById("modalSelectProvider");
    if (modal) {
      modal.classList.remove("active");
      modal.style.display = "none";
    }
  }

  function setupSelectProviderModal() {
    const modal = document.getElementById("modalSelectProvider");
    const btnClose = document.getElementById("btnCloseSelectProviderModal");
    const btnCancel = document.getElementById("btnCancelSelectProviderModal");
    const searchInput = document.getElementById("inputSearchProvider");

    const close = () => {
      if (modal) {
        modal.classList.remove("active");
        modal.style.display = "none";
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (searchInput) {
      let debounce = null;
      searchInput.addEventListener("input", () => {
        clearTimeout(debounce);
        const inp = (state.editingInputs || [])[currentProviderInputIndex];
        const baseName = inp ? inp.name : "";
        debounce = setTimeout(() => loadProviderList(baseName), 250);
      });
    }
  }

  // =========================================================================
  // COMENTARIOS ESPECÍFICOS POR PROCESO EN EL LIENZO
  // =========================================================================
  let targetCommentNode = null;

  function openNodeCommentModal(node) {
    targetCommentNode = node;
    const modal = document.getElementById("modalAddProcessComment");
    const subTitle = document.getElementById("subAddProcessComment");
    const authorSpan = document.getElementById("commentAuthorDisplay");
    const textarea = document.getElementById("inputProcessCommentText");

    const author = state.activeUser ? state.activeUser.display_name : "Carla Méndez";
    const role = state.activeUser ? state.activeUser.role : "analyst";
    const roleTitle = role === "auditor" ? "Auditor Líder" : role === "analyst" ? "Analista" : "Cliente";

    if (subTitle) {
      subTitle.textContent = `Proceso: ${node.name} (ID: #${node.process_id || node.id})`;
    }
    if (authorSpan) {
      authorSpan.textContent = `👤 Publicando como: ${author} (${roleTitle})`;
    }
    if (textarea) {
      textarea.value = "";
    }

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      if (textarea) textarea.focus();
    }
  }

  function setupAddProcessCommentModal() {
    const modal = document.getElementById("modalAddProcessComment");
    const btnClose = document.getElementById("btnCloseAddProcessComment");
    const btnCancel = document.getElementById("btnCancelAddProcessComment");
    const btnSave = document.getElementById("btnSaveAddProcessComment");

    const close = () => {
      if (modal) {
        modal.classList.remove("active");
        modal.style.display = "none";
      }
      targetCommentNode = null;
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (btnSave) {
      btnSave.addEventListener("click", async () => {
        if (!targetCommentNode) return;
        const textarea = document.getElementById("inputProcessCommentText");
        const typeSelect = document.getElementById("selectProcessCommentType");
        const content = textarea ? textarea.value.trim() : "";
        const obsType = typeSelect ? typeSelect.value : "Observación Técnica";

        if (!content) {
          alert("Por favor escribe el contenido de la observación técnica.");
          return;
        }

        const author = state.activeUser ? state.activeUser.display_name : "Carla Méndez";
        const role = state.activeUser ? state.activeUser.role : "analyst";
        const sysId = state.activeSystem ? state.activeSystem.id : 21;
        const noteX = Math.min(window.innerWidth - 300, Math.max(20, (targetCommentNode.x || 100) + 120));
        const noteY = Math.max(20, (targetCommentNode.y || 100) - 60);

        try {
          await api.addComment(
            sysId,
            `[${obsType} · "${targetCommentNode.name}"]: ${content}`,
            author,
            role,
            targetCommentNode.id,
            noteX,
            noteY
          );
          state.showCanvasStickyNotes = true;
          showNotification(`Observación técnica vinculada al proceso "${targetCommentNode.name}".`);
          close();
          await loadSystemComments();
          renderCanvasStage();
        } catch (err) {
          alert("Error al agregar comentario: " + err.message);
        }
      });
    }
  }

  async function deleteComment(commentId) {
    if (!confirm(window.I18n.t("comments.delete_confirm", "¿Deseas eliminar este comentario / nota técnica?"))) {
      return;
    }
    const user = state.activeUser ? state.activeUser.display_name : "Carla Méndez";
    const role = state.activeUser ? state.activeUser.role : "analyst";
    try {
      await api.deleteComment(commentId, user, role);
      showNotification(window.I18n.t("comments.deleted_ok", "Comentario eliminado correctamente."));
      await loadSystemComments();
      renderCanvasStickyNotes();
      renderCommentsThread();
    } catch (err) {
      alert("Error al eliminar comentario: " + err.message);
    }
  }

  async function loadSystemComments() {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = (sysId === 21 || sysId === 1);
    try {
      const res = await api.getComments(sysId);
      state.comments = (res.items || []).filter(c => {
        if (isOfficialSys) {
          return c.system_id === 21 || c.system_id === 1;
        }
        return c.system_id === sysId;
      });
    } catch (e) {
      console.warn("loadSystemComments:", e);
      state.comments = [];
    }
  }

  function setupProcessEditorModal() {
    const modal = document.getElementById("modalProcessEditor");
    const btnClose = document.getElementById("btnCloseProcessEditor");
    const btnCancel = document.getElementById("btnCancelProcessEditor");
    const btnSave = document.getElementById("btnSaveProcessEditor");
    const btnAddIn = document.getElementById("btnAddProcInput");
    const btnAddOut = document.getElementById("btnAddProcOutput");
    const tabIn = document.getElementById("tabProcEditorInputs");
    const tabOut = document.getElementById("tabProcEditorOutputs");

    const close = () => {
      if (modal) {
        modal.classList.remove("active");
        modal.style.display = "none";
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (tabIn) tabIn.addEventListener("click", () => switchProcessEditorTab("inputs"));
    if (tabOut) tabOut.addEventListener("click", () => switchProcessEditorTab("outputs"));

    if (btnAddIn) {
      btnAddIn.addEventListener("click", () => {
        openSelectDbFlowModal("input");
      });
    }

    if (btnAddOut) {
      btnAddOut.addEventListener("click", () => {
        openSelectDbFlowModal("output");
      });
    }

    const nameInput = document.getElementById("procEditName");
    if (nameInput) {
      nameInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        const masterTitle = document.getElementById("procEditMasterTitle");
        if (masterTitle) {
          masterTitle.textContent = val || "New Blank Process";
        }

        // En openLCA, al nombrar un proceso nuevo, se auto-crea y sincroniza el Quantitative Reference Flow
        if (state.editingProcess && state.editingProcess.isNewProcess) {
          const refNameInput = document.getElementById("procEditRefFlowName");
          const refAmtInput = document.getElementById("procEditRefAmount");
          const refUnitInput = document.getElementById("procEditRefUnit");

          if (refNameInput) {
            refNameInput.value = val;
          }

          if (val) {
            const refAmt = parseFloat(refAmtInput?.value || "1.0");
            const refUnit = (refUnitInput?.value || "kg").trim();
            const refIdx = (state.editingOutputs || []).findIndex(o => o.is_reference);
            if (refIdx >= 0) {
              state.editingOutputs[refIdx].name = val;
              state.editingOutputs[refIdx].amount = refAmt;
              state.editingOutputs[refIdx].unit = refUnit;
            } else {
              if (!state.editingOutputs) state.editingOutputs = [];
              state.editingOutputs.unshift({
                name: val,
                amount: refAmt,
                unit: refUnit,
                is_reference: true,
                is_waste: false,
                is_elementary: false,
                provider: "Main quantitative reference flow"
              });
            }
          } else {
            // Si el nombre está vacío, quitar la referencia vacía
            state.editingOutputs = (state.editingOutputs || []).filter(o => !o.is_reference);
          }
          renderProcessEditorCards();
        }
      });
    }

    // Permitir cambiar manualmente el flujo de referencia, su cantidad y su unidad
    const refNameInput = document.getElementById("procEditRefFlowName");
    const refAmtInput = document.getElementById("procEditRefAmount");
    const refUnitInput = document.getElementById("procEditRefUnit");

    if (refNameInput) {
      refNameInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        const refIdx = (state.editingOutputs || []).findIndex(o => o.is_reference);
        if (refIdx >= 0) {
          state.editingOutputs[refIdx].name = val || (document.getElementById("procEditName")?.value || "Reference Flow");
          renderProcessEditorCards();
        }
      });
    }

    if (refAmtInput) {
      refAmtInput.addEventListener("input", (e) => {
        const amt = parseFloat(e.target.value) || 0;
        const refIdx = (state.editingOutputs || []).findIndex(o => o.is_reference);
        if (refIdx >= 0) {
          state.editingOutputs[refIdx].amount = amt;
          renderProcessEditorCards();
        }
        updateProcessMassBalance();
      });
    }

    if (refUnitInput) {
      refUnitInput.addEventListener("input", (e) => {
        const unit = e.target.value.trim() || "kg";
        const refIdx = (state.editingOutputs || []).findIndex(o => o.is_reference);
        if (refIdx >= 0) {
          state.editingOutputs[refIdx].unit = unit;
          renderProcessEditorCards();
        }
      });
    }

    if (btnSave) {
      btnSave.addEventListener("click", async () => {
        if (!state.editingProcess || !state.editingProcess.target) return;
        const target = state.editingProcess.target;
        const nameVal = (document.getElementById("procEditName")?.value || target.name || "").trim() || "Unit Process";
        const codeVal = (document.getElementById("procEditCode")?.value || target.code || target.id || "").trim();
        const catVal = (document.getElementById("procEditCategory")?.value || target.category || "Custom processes & flows").trim();
        const locVal = (document.getElementById("procEditLocation")?.value || target.location || "GLO").trim();
        const refName = (document.getElementById("procEditRefFlowName")?.value || nameVal).trim();
        const refAmt = parseFloat(document.getElementById("procEditRefAmount")?.value || "1.0");
        const refUnit = (document.getElementById("procEditRefUnit")?.value || "kg").trim();

        target.name = nameVal;
        target.code = codeVal;
        target.category = catVal;
        target.category_name = catVal;
        target.location = locVal;
        target.reference_flow = { name: refName, amount: refAmt, unit: refUnit };
        target.inputs = JSON.parse(JSON.stringify(state.editingInputs || []));
        target.outputs = JSON.parse(JSON.stringify(state.editingOutputs || []));

        if (state.editingProcess.isNewProcess) {
          try {
            // Guardar en la base de datos de LCI bajo la categoría "Custom processes & flows"
            const res = await api.createCustomProcess({
              name: nameVal,
              code: codeVal,
              category_id: 999999,
              location: locVal,
              reference_flow_name: refName,
              reference_amount: refAmt,
              reference_unit: refUnit,
              description: "User custom process created from canvas",
              inputs: target.inputs,
              outputs: target.outputs
            });

            if (res && res.process) {
              target.id = res.process.id;
              target.process_id = res.process.id;
              target.name = res.process.name || nameVal;
            }

            // Agregar a la paleta de procesos del lienzo sin duplicar
            if (!state.paletteProcesses) state.paletteProcesses = [];
            const existingIdx = state.paletteProcesses.findIndex(p => String(p.id) === String(target.id) || String(p.process_id) === String(target.process_id));
            if (existingIdx >= 0) {
              state.paletteProcesses[existingIdx] = target;
            } else {
              state.paletteProcesses.unshift(target);
            }
            renderPaletteProcesses();

            // Refrescar catálogo LCI si está abierto o cargado
            loadCatalog();

            showNotification(`Process "${nameVal}" saved to "Custom processes & flows" section of the LCI explorer.`);
          } catch (err) {
            console.error("Error al persistir proceso propio:", err);
            if (!state.paletteProcesses) state.paletteProcesses = [];
            state.paletteProcesses.unshift(target);
            renderPaletteProcesses();
            showNotification(`Process "${nameVal}" added to the local palette.`);
          }
        } else {
          // Si es un proceso que ya existe en la paleta, sincronizar sus datos
          if (state.paletteProcesses) {
            const pIdx = state.paletteProcesses.findIndex(p => String(p.id) === String(target.id) || String(p.process_id) === String(target.process_id));
            if (pIdx >= 0) {
              state.paletteProcesses[pIdx] = Object.assign({}, state.paletteProcesses[pIdx], target);
            }
          }
          if (state.editingProcess.isCanvasNode) {
            renderCanvasStage();
            if (state.selectedNode && (String(state.selectedNode.id) === String(target.id) || String(state.selectedNode.process_id) === String(target.process_id))) {
              inspectNode(target);
            }
            scheduleAutoSaveCanvas();
          } else {
            renderPaletteProcesses();
          }
          showNotification(`Process "${nameVal}" updated successfully.`);
        }

        close();
      });
    }
  }

  function updateEditInput(idx, field, val) {
    if (state.editingInputs && state.editingInputs[idx]) {
      state.editingInputs[idx][field] = val;
    }
  }

  function removeEditInput(idx) {
    if (state.editingInputs) {
      state.editingInputs.splice(idx, 1);
      renderProcessEditorCards();
    }
  }

  function updateEditOutput(idx, field, val) {
    if (state.editingOutputs && state.editingOutputs[idx]) {
      state.editingOutputs[idx][field] = val;
    }
  }

  function updateEditOutputClass(idx, cls) {
    if (state.editingOutputs && state.editingOutputs[idx]) {
      const out = state.editingOutputs[idx];
      out.is_waste = cls === "waste";
      out.is_elementary = cls === "elementary";
      out.is_reference = cls === "ref";
      if (out.is_waste && (!out.compartment || out.compartment === "Aire" || out.compartment === "Air")) out.compartment = "N/A";
    }
  }

  function setAsQuantitativeReference(idx) {
    if (!state.editingOutputs || !state.editingOutputs[idx]) return;
    const selectedFlow = state.editingOutputs[idx];

    // Marcar solo el seleccionado como referencia
    state.editingOutputs.forEach((out, i) => {
      out.is_reference = (i === idx);
      if (out.is_reference) {
        out.is_waste = false;
        out.is_elementary = false;
        out.provider = "Main quantitative reference flow";
      }
    });

    // Sincronizar la caja maestra central
    const refNameInput = document.getElementById("procEditRefFlowName");
    const refAmtInput = document.getElementById("procEditRefAmount");
    const refUnitInput = document.getElementById("procEditRefUnit");

    if (refNameInput) refNameInput.value = selectedFlow.name || "";
    if (refAmtInput) refAmtInput.value = selectedFlow.amount || 1.0;
    if (refUnitInput) refUnitInput.value = selectedFlow.unit || "kg";

    renderProcessEditorCards();
    updateProcessMassBalance();
    showNotification(`"${selectedFlow.name}" set as Quantitative Reference.`);
  }

  function removeEditOutput(idx) {
    if (state.editingOutputs) {
      const removed = state.editingOutputs[idx];
      state.editingOutputs.splice(idx, 1);
      // Si eliminamos la referencia y quedan salidas, asignar la primera
      if (removed && removed.is_reference && state.editingOutputs.length > 0) {
        setAsQuantitativeReference(0);
      } else {
        renderProcessEditorCards();
      }
    }
  }

  function updateSankeyLegend() {
    const legend = document.getElementById("canvasSankeyLegend");
    const title = document.getElementById("sankeyLegendTitle");
    const statTotal = document.getElementById("sankeyStatTotal");
    const statMax = document.getElementById("sankeyStatMax");
    const labelTotal = document.getElementById("sankeyLabelTotal");
    const labelMax = document.getElementById("sankeyLabelMax");

    if (!legend) return;

    // Si el modo Sankey está apagado O el lienzo está vacío, ocultar la leyenda por completo
    if (state.sankeyMode === "none" || !state.canvasNodes || state.canvasNodes.length === 0) {
      legend.style.display = "none";
      return;
    }

    legend.style.display = "block";
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";

    if (state.sankeyMode === "mass") {
      if (title) title.textContent = isEn ? "Sankey Flow: Mass Balance (kg)" : "Diagrama Sankey por Masa (kg)";
      if (labelTotal) labelTotal.textContent = isEn ? "Total Flow in Chain" : "Flujo Total en Cadena";
      if (labelMax) labelMax.textContent = isEn ? "Maximum Flow" : "Flujo Máximo";

      let totalMass = 0;
      let maxMass = 0;
      let maxNodeName = "";

      state.canvasNodes.forEach(node => {
        const mVal = getNodeMass(node);
        if (mVal > maxMass) {
          maxMass = mVal;
          maxNodeName = node.reference_flow ? (node.reference_flow.name || node.name) : node.name;
        }
      });
      totalMass = maxMass > 0 ? maxMass : 1.0;

      if (statTotal) statTotal.textContent = `${totalMass.toFixed(3)} kg`;
      if (statMax) statMax.textContent = `${maxMass.toFixed(3)} kg (${maxNodeName || "N/A"})`;
    } else if (state.sankeyMode === "energy") {
      if (title) title.textContent = isEn ? "Sankey Flow: Cumulative Energy (kWh)" : "Diagrama Sankey por Energía Acumulada (kWh)";
      if (labelTotal) labelTotal.textContent = isEn ? "Total Direct Energy in Chain" : "Energía Directa Total en Cadena";
      if (labelMax) labelMax.textContent = isEn ? "Highest Consumer Process" : "Mayor Proceso Consumidor";

      let totalEnergy = 0;
      let maxEnergy = 0;
      let maxEnergyNode = "";

      state.canvasNodes.forEach(node => {
        const eVal = getNodeDirectEnergy(node);
        totalEnergy += eVal;
        if (eVal > maxEnergy) {
          maxEnergy = eVal;
          maxEnergyNode = node.name;
        }
      });

      if (statTotal) statTotal.textContent = `${totalEnergy.toFixed(3)} kWh`;
      if (statMax) statMax.textContent = `${maxEnergy.toFixed(3)} kWh (${maxEnergyNode || "N/A"})`;
    }
  }

  function updateCanvasHeaderToolbar() {
    const labelStickyToggle = document.getElementById("labelStickyNotesToggle");
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    if (labelStickyToggle) {
      if (state.showCanvasStickyNotes) {
        labelStickyToggle.textContent = isEn ? "Notes (On)" : "Notas (On)";
        labelStickyToggle.setAttribute("data-i18n", "canvas.sticky_notes_on");
      } else {
        labelStickyToggle.textContent = isEn ? "Notes (Off)" : "Notas (Off)";
        labelStickyToggle.setAttribute("data-i18n", "canvas.sticky_notes_off");
      }
    }
  }

  async function saveCanvas(isAuto = false) {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    try {
      (state.canvasNodes || []).forEach(n => {
        if (n.x !== undefined) n.pos_x = n.x;
        if (n.y !== undefined) n.pos_y = n.y;
      });
      await api.saveSystemCanvas(sysId, {
        nodes: state.canvasNodes,
        edges: state.canvasEdges
      });
      if (!isAuto) {
        showNotification("Lienzo guardado exitosamente en base de datos.");
      }
    } catch (err) {
      if (!isAuto) {
        alert("Error al guardar lienzo: " + err.message);
      } else {
        console.warn("Auto-save canvas warning:", err);
      }
    }
  }

  let autoSaveCanvasTimer = null;
  function scheduleAutoSaveCanvas() {
    if (autoSaveCanvasTimer) clearTimeout(autoSaveCanvasTimer);
    autoSaveCanvasTimer = setTimeout(() => {
      saveCanvas(true);
    }, 400);
  }

  // =========================================================================
  // 6.5. VISTA HOJA DE CÁLCULO / MATRIZ LCI (SPREADSHEET VIEW & CONNECTION MATRIX)
  // =========================================================================

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function updateCanvasPanelLayout() {
    const canvasWrapper = document.getElementById("canvasWrapper");
    if (!canvasWrapper) return;

    const isTable = state.canvasViewMode === "table";
    const hideLeft = state.leftPanelVisible === false;
    // En modo tabla, el inspector está estrictamente deshabilitado y cerrado
    const hideRight = isTable ? true : (state.rightPanelVisible === false);

    canvasWrapper.classList.toggle("table-mode", isTable);
    canvasWrapper.classList.toggle("hide-left", hideLeft);
    canvasWrapper.classList.toggle("hide-right", hideRight);

    const btnLeft = document.getElementById("btnToggleLeftSidebar");
    const btnRight = document.getElementById("btnToggleRightSidebar");
    const btnFull = document.getElementById("btnToggleFullCanvas");

    if (btnLeft) {
      btnLeft.classList.toggle("active", !hideLeft);
      btnLeft.setAttribute("aria-pressed", !hideLeft ? "true" : "false");
    }
    if (btnRight) {
      if (isTable) {
        btnRight.style.display = "none";
      } else {
        btnRight.style.display = "";
        btnRight.classList.toggle("active", !hideRight);
        btnRight.setAttribute("aria-pressed", !hideRight ? "true" : "false");
      }
    }
    if (btnFull) {
      const isFull = isTable ? hideLeft : (hideLeft && hideRight);
      btnFull.classList.toggle("active", isFull);
      btnFull.setAttribute("aria-pressed", isFull ? "true" : "false");
    }

    // Notificar redimensionamiento y refrescar conexiones SVG
    setTimeout(() => {
      if (!isTable) {
        renderCanvasEdges();
      }
      window.dispatchEvent(new Event("resize"));
    }, 60);
  }

  function toggleLeftPanel(forceState) {
    if (forceState !== undefined) {
      state.leftPanelVisible = forceState;
    } else {
      state.leftPanelVisible = (state.leftPanelVisible === false);
    }
    updateCanvasPanelLayout();
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    showNotification(state.leftPanelVisible ? 
      (isEn ? "Process catalog expanded." : "Catálogo de procesos visible.") : 
      (isEn ? "Process catalog hidden (more space for canvas)." : "Catálogo ocultado para ampliar el espacio de trabajo."));
  }

  function toggleRightPanel(forceState) {
    // En la vista 2 de hoja de cálculo no se puede abrir el inspector
    if (state.canvasViewMode === "table") {
      return;
    }
    if (forceState !== undefined) {
      state.rightPanelVisible = forceState;
    } else {
      state.rightPanelVisible = (state.rightPanelVisible === false);
    }
    updateCanvasPanelLayout();
    const isVisible = state.rightPanelVisible;
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    showNotification(isVisible ? 
      (isEn ? "Process inspector expanded." : "Inspector de proceso visible.") : 
      (isEn ? "Process inspector hidden (more space for canvas)." : "Inspector ocultado para ampliar el espacio de trabajo."));
  }

  function toggleFullCanvas() {
    const isTable = state.canvasViewMode === "table";
    if (isTable) {
      // En modo tabla, maximizar oculta o muestra el catálogo izquierdo (100% de amplitud para la hoja)
      state.leftPanelVisible = !state.leftPanelVisible;
      updateCanvasPanelLayout();
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      showNotification(state.leftPanelVisible ? 
        (isEn ? "Process catalog shown." : "Catálogo de procesos visible.") : 
        (isEn ? "Spreadsheet maximized (100% width)." : "Hoja de cálculo maximizada al 100% de amplitud."));
      return;
    }

    const hideLeft = state.leftPanelVisible === false;
    const hideRight = state.rightPanelVisible === false;

    if (hideLeft && hideRight) {
      state.leftPanelVisible = true;
      state.rightPanelVisible = true;
      updateCanvasPanelLayout();
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      showNotification(isEn ? "Side panels restored." : "Paneles laterales restaurados.");
    } else {
      state.leftPanelVisible = false;
      state.rightPanelVisible = false;
      updateCanvasPanelLayout();
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      showNotification(isEn ? "Canvas maximized (100% width)." : "Lienzo maximizado al 100% de amplitud.");
    }
  }

  function updateZoomLabels() {
    const pct = Math.round((state.canvasZoom || 1.0) * 100);
    const labelFloat = document.getElementById("canvasZoomPercentLabel");
    const labelTb = document.getElementById("canvasTbZoomPercentLabel");
    if (labelFloat) labelFloat.textContent = `${pct}%`;
    if (labelTb) labelTb.textContent = `${pct}%`;
  }

  function applyCanvasZoom(newZoom, mouseClientX, mouseClientY) {
    const stage = document.getElementById("canvasStage");
    const zoomContainer = document.getElementById("canvasZoomContainer");
    if (!stage || !zoomContainer) return;

    const oldZoom = state.canvasZoom || 1.0;
    // Acotar el zoom entre 50% (0.50) y 175% (1.75) para un rango ergonómico suave
    const clampedZoom = Math.max(0.5, Math.min(1.75, Math.round(newZoom * 100) / 100));
    state.canvasZoom = clampedZoom;

    // Calcular punto focal (cursor del ratón o centro de la vista visible)
    const rect = stage.getBoundingClientRect();
    const targetX = (mouseClientX !== undefined && mouseClientX !== null) ? mouseClientX : (rect.left + rect.width / 2);
    const targetY = (mouseClientY !== undefined && mouseClientY !== null) ? mouseClientY : (rect.top + rect.height / 2);

    const viewX = targetX - rect.left + stage.scrollLeft;
    const viewY = targetY - rect.top + stage.scrollTop;

    const canvasX = viewX / oldZoom;
    const canvasY = viewY / oldZoom;

    zoomContainer.style.transform = `scale(${clampedZoom})`;

    // Ajustar scroll para mantener el punto focal
    const newViewX = canvasX * clampedZoom;
    const newViewY = canvasY * clampedZoom;
    stage.scrollLeft = newViewX - (targetX - rect.left);
    stage.scrollTop = newViewY - (targetY - rect.top);

    updateZoomLabels();
  }

  function switchCanvasViewMode(mode) {
    state.canvasViewMode = mode;
    const visualContainer = document.getElementById("canvasVisualStageContainer");
    const tableContainer = document.getElementById("canvasTableStageContainer");
    const btnVisual = document.getElementById("btnCanvasViewVisual");
    const btnTable = document.getElementById("btnCanvasViewTable");
    const zoomTbGroup = document.getElementById("canvasZoomToolbarGroup");
    const sankeyTbGroup = document.getElementById("canvasSankeyToolbarGroup");

    updateCanvasPanelLayout();

    if (btnVisual) btnVisual.classList.toggle("active", mode === "visual");
    if (btnTable) btnTable.classList.toggle("active", mode === "table");
    if (zoomTbGroup) zoomTbGroup.style.display = mode === "table" ? "none" : "flex";
    if (sankeyTbGroup) sankeyTbGroup.style.display = mode === "table" ? "none" : "flex";

    if (mode === "table") {
      if (visualContainer) {
        visualContainer.style.display = "none";
        visualContainer.classList.remove("active");
      }
      if (tableContainer) {
        tableContainer.style.display = "flex";
        tableContainer.classList.add("active");
      }
      renderCanvasTableView();
    } else {
      if (tableContainer) {
        tableContainer.style.display = "none";
        tableContainer.classList.remove("active");
      }
      if (visualContainer) {
        visualContainer.style.display = "flex";
        visualContainer.classList.add("active");
      }
      renderCanvasStage();
    }
  }

    function selectSpreadsheetCell(cellEl, rowNum, colLetter, cellVal, meta) {
    document.querySelectorAll(".excel-cell.excel-active-cell").forEach(el => el.classList.remove("excel-active-cell"));
    document.querySelectorAll(".excel-col-letter.active-header").forEach(el => el.classList.remove("active-header"));
    document.querySelectorAll(".excel-row-num.active-header").forEach(el => el.classList.remove("active-header"));

    if (cellEl) {
      cellEl.classList.add("excel-active-cell");
    }

    const colHeader = document.querySelector(`.excel-col-letter[data-col="${colLetter}"]`);
    if (colHeader) colHeader.classList.add("active-header");

    const rowHeader = document.querySelector(`.excel-row-num[data-row="${rowNum}"]`);
    if (rowHeader) rowHeader.classList.add("active-header");

    const nameBox = document.getElementById("spreadsheetActiveCellName");
    const formulaInput = document.getElementById("spreadsheetFormulaInput");

    if (nameBox) nameBox.textContent = `${colLetter}${rowNum}`;
    if (formulaInput) {
      formulaInput.value = (cellVal !== undefined && cellVal !== null) ? String(cellVal) : "";
    }

    state.selectedSpreadsheetCell = {
      cellEl,
      row: rowNum,
      col: colLetter,
      val: cellVal,
      meta: meta || {}
    };
  }

  function applyFormulaBarChange(newVal) {
    if (!state.selectedSpreadsheetCell || !state.selectedSpreadsheetCell.meta) return;
    const meta = state.selectedSpreadsheetCell.meta;
    const trimmed = String(newVal !== undefined ? newVal : "").trim();

    if (meta.type === "amount" && meta.nodeId) {
      tableUpdateAmount(meta.nodeId, meta.flowKind, meta.idx, trimmed);
    } else if (meta.type === "name" && meta.nodeId) {
      tableUpdateFlowName(meta.nodeId, meta.flowKind, meta.idx, trimmed);
    } else if (meta.type === "unit" && meta.nodeId) {
      tableUpdateUnit(meta.nodeId, meta.flowKind, meta.idx, trimmed);
    } else if (meta.type === "processName" && meta.nodeId) {
      tableUpdateProcessName(meta.nodeId, trimmed);
    } else if (meta.type === "edgeAmount" && meta.edgeId) {
      tableUpdateEdgeAmount(meta.edgeId, trimmed);
    }

    if (state.selectedSpreadsheetCell.cellEl) {
      const input = state.selectedSpreadsheetCell.cellEl.querySelector(".excel-inline-input");
      if (input) input.value = trimmed;
      else state.selectedSpreadsheetCell.cellEl.textContent = trimmed;
    }
  }

  function renderCanvasTableView() {
    const container = document.getElementById("canvasTableScrollArea");
    if (!container) return;

    const t = (k, fallback) => (window.I18n && window.I18n.t ? window.I18n.t(k, fallback) : fallback);

    const fileNameEl = document.getElementById("spreadsheetFileName");
    if (fileNameEl) {
      const sys = state.activeSystem;
      const baseName = (sys && sys.name) ? sys.name.replace(/[^a-zA-Z0-9_\-\s]/g, "").trim().replace(/\s+/g, "_") : "LCI_Inventario_Cadena";
      fileNameEl.textContent = `${baseName}.xlsx`;
    }

    const tabLci = document.getElementById("tabSheetLci");
    const tabConn = document.getElementById("tabSheetConnections");
    const activeTab = state.activeSheetTab || "lci";

    if (tabLci) {
      tabLci.classList.toggle("active", activeTab === "lci");
      tabLci.setAttribute("aria-selected", activeTab === "lci" ? "true" : "false");
      tabLci.onclick = () => {
        state.activeSheetTab = "lci";
        renderCanvasTableView();
      };
    }
    if (tabConn) {
      tabConn.classList.toggle("active", activeTab === "connections");
      tabConn.setAttribute("aria-selected", activeTab === "connections" ? "true" : "false");
      tabConn.onclick = () => {
        state.activeSheetTab = "connections";
        renderCanvasTableView();
      };
    }

    const formulaInput = document.getElementById("spreadsheetFormulaInput");
    if (formulaInput && !formulaInput._boundEvents) {
      formulaInput._boundEvents = true;
      formulaInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          applyFormulaBarChange(formulaInput.value);
          formulaInput.blur();
        }
      });
      formulaInput.addEventListener("blur", () => {
        applyFormulaBarChange(formulaInput.value);
      });
    }

    const filterText = (state.tableFilterText || "").toLowerCase().trim();
    const flowFilter = state.tableFlowFilter || "ALL";

    const inputSearch = document.getElementById("inputTableFilter");
    if (inputSearch && inputSearch.value !== state.tableFilterText) {
      inputSearch.value = state.tableFilterText;
    }
    const selectFilter = document.getElementById("selectTableFlowFilter");
    if (selectFilter && selectFilter.value !== state.tableFlowFilter) {
      selectFilter.value = state.tableFlowFilter;
    }

    if (!state.canvasNodes || state.canvasNodes.length === 0) {
      container.innerHTML = `
        <div style="padding: 48px 16px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 40px; margin-bottom: 12px;">📊</div>
          <h3 style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
            ${t("canvas.table_title", "Hoja de Cálculo LCI: Balance e Intercambios")}
          </h3>
          <p style="font-size: 12px; max-width: 440px; margin: 0 auto 16px; line-height: 1.5;">
            No hay procesos en este sistema producto. Agrega procesos desde el catálogo lateral o crea uno nuevo para comenzar a estructurar la matriz LCI.
          </p>
          <button type="button" class="btn btn-primary btn-sm" onclick="window.EconodeApp.openProcessEditor(null)">
            + ${t("canvas.table_add_process", "Agregar Proceso")}
          </button>
        </div>
      `;
      return;
    }

    let html = "";
    let totalRows = 0;
    let totalInputsKg = 0;

    if (activeTab === "lci") {
      let currentRowNum = 1;

      html += `
        <table class="lci-excel-grid">
          <thead>
            <tr class="excel-header-row-letters">
              <th class="excel-corner-cell"></th>
              <th class="excel-col-letter" data-col="A" style="width: 230px;">A</th>
              <th class="excel-col-letter" data-col="B" style="width: 135px;">B</th>
              <th class="excel-col-letter" data-col="C" style="min-width: 220px;">C</th>
              <th class="excel-col-letter" data-col="D" style="width: 260px;">D</th>
              <th class="excel-col-letter" data-col="E" style="width: 105px; text-align: right;">E</th>
              <th class="excel-col-letter" data-col="F" style="width: 70px; text-align: center;">F</th>
              <th class="excel-col-letter" data-col="G" style="width: 85px; text-align: center;">G</th>
            </tr>
            <tr>
              <th class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</th>
              <th class="excel-col-label-th">${t("canvas.col_process", "Proceso")}</th>
              <th class="excel-col-label-th">${t("canvas.col_type", "Tipo")}</th>
              <th class="excel-col-label-th">Material / Flujo</th>
              <th class="excel-col-label-th">${t("canvas.col_provider", "Proveedor / Destino")}</th>
              <th class="excel-col-label-th" style="text-align: right;">${t("canvas.col_value", "Valor")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_unit", "Unidad")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_actions", "Acciones")}</th>
            </tr>
          </thead>
          <tbody>
      `;

      state.canvasNodes.forEach((node) => {
        const nodeNameLower = (node.name || "").toLowerCase();
        const nodeCatLower = (node.category || "").toLowerCase();

        const showInputs = flowFilter === "ALL" || flowFilter === "INPUTS";
        const showOutputs = flowFilter === "ALL" || flowFilter === "OUTPUTS";

        const filteredInputs = (node.inputs || []).map((inp, idx) => ({ ...inp, originalIdx: idx })).filter(inp => {
          if (!filterText) return true;
          return nodeNameLower.includes(filterText) ||
                 nodeCatLower.includes(filterText) ||
                 (inp.name && inp.name.toLowerCase().includes(filterText)) ||
                 (inp.origin && inp.origin.toLowerCase().includes(filterText));
        });

        const filteredOutputs = (node.outputs || []).map((out, idx) => ({ ...out, originalIdx: idx })).filter(out => {
          if (!filterText) return true;
          return nodeNameLower.includes(filterText) ||
                 nodeCatLower.includes(filterText) ||
                 (out.name && out.name.toLowerCase().includes(filterText));
        });

        if (filterText && !nodeNameLower.includes(filterText) && !nodeCatLower.includes(filterText) && filteredInputs.length === 0 && filteredOutputs.length === 0) {
          return;
        }

        const processRows = [];

        if (showInputs) {
          filteredInputs.forEach((inp) => {
            const connectedEdge = (state.canvasEdges || []).find(e => 
              (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id) || String(e.to) === String(node.process_id)) &&
              (e.flow === inp.name || (inp.name && inp.name.includes(e.flow)))
            );

            let typeBadge = '';
            let providerText = '';
            if (connectedEdge) {
              const srcNode = state.canvasNodes.find(n => String(n.id) === String(connectedEdge.from) || String(n.process_id) === String(connectedEdge.source_process_id));
              const srcName = srcNode ? srcNode.name : (connectedEdge.from || "Upstream");
              typeBadge = `<span class="excel-badge-connected">🔗 ${t("canvas.tag_connected", "Conectado")}</span>`;
              providerText = `<span style="color: #6D28D9; font-weight: 600;">🔗 ${escapeHtml(srcName)}</span>`;
            } else if (inp.is_unit) {
              typeBadge = `<span class="excel-badge-techno">⚙️ Tecnosfera</span>`;
              providerText = escapeHtml(inp.origin || "Mercado ecoinvent 3.12");
            } else {
              typeBadge = `<span class="excel-badge-techno">⚡ Auxiliar</span>`;
              providerText = escapeHtml(inp.origin || "Suministro Industrial / CFE");
            }

            const amt = inp.amount !== undefined ? Number(inp.amount) : 1.0;
            if (inp.unit === "kg") totalInputsKg += amt;

            processRows.push({
              flowKind: "input",
              idx: inp.originalIdx,
              typeBadge,
              flowName: inp.name || "Insumo",
              provider: providerText,
              amount: amt,
              unit: inp.unit || "kg",
              isReference: false,
              isWaste: false,
              isElementary: false,
              canDelete: true
            });
          });
        }

        if (showOutputs) {
          filteredOutputs.forEach((out) => {
            const outgoingEdges = (state.canvasEdges || []).filter(e => 
              (String(e.from) === String(node.id) || String(e.source_process_id) === String(node.process_id) || String(e.from) === String(node.process_id)) &&
              (e.flow === out.name || (out.name && out.name.includes(e.flow)))
            );

            let typeBadge = '';
            let destText = '';

            if (out.is_reference) {
              typeBadge = `<span class="excel-badge-ref">⭐ Referencia</span>`;
              destText = `[Flujo de Referencia Principal]`;
            } else if (out.is_waste) {
              typeBadge = `<span class="excel-badge-techno" style="background:#FEF2F2; color:#991B1B; border-color:#FECACA;">♻️ Residuo</span>`;
              destText = `Tratamiento / Relleno Sanitario`;
            } else if (out.is_elementary) {
              typeBadge = `<span class="excel-badge-techno" style="background:#FFFBEB; color:#92400E; border-color:#FDE68A;">🌿 Biosfera</span>`;
              destText = `Emisión Ambiental [Aire/Agua]`;
            } else {
              typeBadge = `<span class="excel-badge-techno">📦 Coproducto</span>`;
              destText = `Salida intermedia del sistema`;
            }

            if (outgoingEdges.length > 0) {
              const targetNames = outgoingEdges.map(e => {
                const tgt = state.canvasNodes.find(n => String(n.id) === String(e.to) || String(n.process_id) === String(e.target_process_id));
                return tgt ? tgt.name : e.to;
              }).join(", ");
              destText = `➔ Alimenta: ${escapeHtml(targetNames)}`;
            }

            processRows.push({
              flowKind: "output",
              idx: out.originalIdx,
              typeBadge,
              flowName: out.name || "Producto / Salida",
              provider: destText,
              amount: out.amount !== undefined ? Number(out.amount) : 1.0,
              unit: out.unit || "kg",
              isReference: out.is_reference === true,
              isWaste: out.is_waste === true,
              isElementary: out.is_elementary === true,
              canDelete: !out.is_reference
            });
          });
        }

        if (processRows.length === 0) {
          processRows.push({
            flowKind: "none",
            idx: -1,
            typeBadge: '<span style="color:var(--text-muted); font-style:italic;">—</span>',
            flowName: "Sin flujos registrados",
            provider: "—",
            amount: 0,
            unit: "—",
            isReference: false,
            canDelete: false
          });
        }

        processRows.forEach((rowItem, rIdx) => {
          currentRowNum++;
          totalRows++;

          const isFirstRowOfProcess = (rIdx === 0);
          const rowClass = rowItem.isReference ? "excel-row-reference" : (rowItem.isWaste ? "excel-row-waste" : (rowItem.isElementary ? "excel-row-emission" : ""));
          const processStartClass = isFirstRowOfProcess ? "excel-row-process-start" : "";

          html += `
            <tr class="${processStartClass} ${rowClass}">
              <td class="excel-row-num" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(null, ${currentRowNum}, 'A', '${escapeHtml(node.name)}')">
                ${currentRowNum}
              </td>
              <td class="excel-cell" data-col="A" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'A', '${escapeHtml(node.name)}', { type: 'processName', nodeId: '${node.id}' })">
                ${isFirstRowOfProcess ? `
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
                    <span style="font-weight: 700; color: var(--text-primary);">${escapeHtml(node.name)}</span>
                    <span class="mono" style="font-size: 8.5px; font-weight: 700; color: #059669; background: rgba(5, 150, 105, 0.08); padding: 1px 4px; border-radius: 3px;">#${node.process_id || node.id}</span>
                  </div>
                ` : `
                  <span style="color: var(--text-muted); opacity: 0.35;">↳</span>
                `}
              </td>
              <td class="excel-cell" data-col="B" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'B', '${rowItem.flowKind}')">
                ${rowItem.typeBadge}
              </td>
              <td class="excel-cell" data-col="C" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'C', '${escapeHtml(rowItem.flowName)}', { type: 'name', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" value="${escapeHtml(rowItem.flowName)}" 
                  onchange="window.EconodeApp.tableUpdateFlowName('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)">
              </td>
              <td class="excel-cell" data-col="D" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'D', '${escapeHtml(rowItem.provider)}')">
                ${rowItem.provider}
              </td>
              <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: right;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'E', '${rowItem.amount}', { type: 'amount', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="number" step="any" class="excel-inline-input" style="text-align: right;" value="${rowItem.amount}" 
                  onchange="window.EconodeApp.tableUpdateAmount('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                  oninput="window.EconodeApp.tableUpdateAmount('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value, true)">
              </td>
              <td class="excel-cell mono" data-col="F" data-row="${currentRowNum}" style="text-align: center;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'F', '${escapeHtml(rowItem.unit)}', { type: 'unit', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" style="text-align: center;" value="${escapeHtml(rowItem.unit)}" 
                  onchange="window.EconodeApp.tableUpdateUnit('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)">
              </td>
              <td class="excel-cell" data-col="G" data-row="${currentRowNum}" style="text-align: center;">
                ${rowItem.canDelete ? `
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9.5px; color: #EF4444;" 
                    onclick="window.EconodeApp.tableDeleteFlow('${node.id}', '${rowItem.flowKind}', ${rowItem.idx})" title="Eliminar fila">✕</button>
                ` : (isFirstRowOfProcess ? `
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 4px; font-size: 9px;" onclick="window.EconodeApp.tableAddFlow('${node.id}', 'input')" title="Agregar insumo">+</button>
                ` : `
                  <span style="color: var(--text-muted); font-size: 9px;">—</span>
                `)}
              </td>
            </tr>
          `;
        });
      });

      html += `
          </tbody>
        </table>
      `;
    }

    if (activeTab === "connections") {
      let currentRowNum = 1;
      const edges = state.canvasEdges || [];

      html += `
        <table class="lci-excel-grid">
          <thead>
            <tr class="excel-header-row-letters">
              <th class="excel-corner-cell"></th>
              <th class="excel-col-letter" data-col="A" style="width: 250px;">A</th>
              <th class="excel-col-letter" data-col="B" style="width: 200px;">B</th>
              <th class="excel-col-letter" data-col="C" style="width: 250px;">C</th>
              <th class="excel-col-letter" data-col="D" style="width: 110px; text-align: right;">D</th>
              <th class="excel-col-letter" data-col="E" style="width: 80px; text-align: center;">E</th>
              <th class="excel-col-letter" data-col="F" style="width: 90px; text-align: center;">F</th>
            </tr>
            <tr>
              <th class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</th>
              <th class="excel-col-label-th">${t("canvas.conn_source", "Proceso Origen (Salida)")}</th>
              <th class="excel-col-label-th">${t("canvas.conn_flow", "Flujo Transferido")}</th>
              <th class="excel-col-label-th">${t("canvas.conn_target", "Proceso Destino (Entrada)")}</th>
              <th class="excel-col-label-th" style="text-align: right;">${t("canvas.col_value", "Cantidad")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_unit", "Unidad")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_actions", "Acción")}</th>
            </tr>
          </thead>
          <tbody>
      `;

      if (edges.length === 0) {
        currentRowNum++;
        html += `
          <tr>
            <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
            <td class="excel-cell" colspan="6" style="text-align: center; color: var(--text-muted); padding: 18px; font-style: italic;">
              ${t("canvas.no_connections", "No hay conexiones internas definidas en este sistema producto.")}
            </td>
          </tr>
        `;
      } else {
        edges.forEach((edge) => {
          currentRowNum++;
          totalRows++;

          const srcNode = state.canvasNodes.find(n => String(n.id) === String(edge.from) || String(n.process_id) === String(edge.source_process_id));
          const tgtNode = state.canvasNodes.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id));

          const srcLabel = srcNode ? `${srcNode.name} (#${srcNode.process_id || srcNode.id})` : (edge.from || "Origen");
          const tgtLabel = tgtNode ? `${tgtNode.name} (#${tgtNode.process_id || tgtNode.id})` : (edge.to || "Destino");

          html += `
            <tr>
              <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
              <td class="excel-cell" data-col="A" data-row="${currentRowNum}" style="font-weight: 600; color: #059669;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'A', '${escapeHtml(srcLabel)}')">
                ➔ ${escapeHtml(srcLabel)}
              </td>
              <td class="excel-cell" data-col="B" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'B', '${escapeHtml(edge.flow)}')">
                <span class="excel-badge-connected">${escapeHtml(edge.flow || "Flujo Conectado")}</span>
              </td>
              <td class="excel-cell" data-col="C" data-row="${currentRowNum}" style="font-weight: 600; color: #7C3AED;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'C', '${escapeHtml(tgtLabel)}')">
                🡇 ${escapeHtml(tgtLabel)}
              </td>
              <td class="excel-cell mono" data-col="D" data-row="${currentRowNum}" style="text-align: right;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'D', '${edge.amount || 1.0}', { type: 'edgeAmount', edgeId: '${edge.id}' })">
                <input type="number" step="any" class="excel-inline-input" style="text-align: right;" 
                  value="${edge.amount !== undefined ? edge.amount : 1.0}" 
                  onchange="window.EconodeApp.tableUpdateEdgeAmount('${edge.id}', this.value)">
              </td>
              <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: center;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'E', '${escapeHtml(edge.unit || 'kg')}')">
                ${escapeHtml(edge.unit || 'kg')}
              </td>
              <td class="excel-cell" data-col="F" data-row="${currentRowNum}" style="text-align: center;">
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9.5px; color: #EF4444;" 
                  onclick="window.EconodeApp.tableDeleteEdge('${edge.id}')" title="Desconectar vínculo">
                  ✕ ${t("canvas.conn_disconnect", "Desconectar")}
                </button>
              </td>
            </tr>
          `;
        });
      }

      html += `
          </tbody>
        </table>
      `;
    }

    container.innerHTML = html;

    const statRows = document.getElementById("statRowCount");
    const statProcs = document.getElementById("statProcessCount");
    const statInputs = document.getElementById("statTotalInputs");

    if (statRows) statRows.textContent = `Filas: ${totalRows}`;
    if (statProcs) statProcs.textContent = `Procesos: ${state.canvasNodes ? state.canvasNodes.length : 0}`;
    if (statInputs) statInputs.textContent = `Total Insumos: ${totalInputsKg.toFixed(3)} kg`;

    setTimeout(() => {
      const firstDataCell = container.querySelector('.excel-cell[data-col="C"][data-row="2"]');
      if (firstDataCell && !state.selectedSpreadsheetCell) {
        firstDataCell.click();
      }
    }, 40);
  }

  function exportLciTableToCsv() {
    const sys = state.activeSystem;
    const sysName = (sys && sys.name) ? sys.name : "Sistema_Producto";
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `LCI_${sysName.replace(/[^a-zA-Z0-9_\-]/g, "_")}_${dateStr}.csv`;

    let csv = "\uFEFF"; // BOM UTF-8 for Excel compatibility
    csv += "========================================================================\n";
    csv += `ECONODE STUDIO - MATRIZ DE INVENTARIO DE CICLO DE VIDA (LCI)\n`;
    csv += `Sistema Producto: ${sysName}\n`;
    csv += `Código: ${(sys && sys.code) ? sys.code : "N/A"}\n`;
    csv += `Fecha: ${new Date().toLocaleString()}\n`;
    csv += "========================================================================\n\n";

    // 1. Procesos y Flujos
    csv += "ID Proceso,Nombre Proceso,Categoría,Tipo de Flujo,Nombre del Flujo,Proveedor / Destino en Cadena,Cantidad,Unidad\n";

    (state.canvasNodes || []).forEach(node => {
      const pid = node.process_id || node.id;
      const pName = `"${(node.name || "").replace(/"/g, '""')}"`;
      const pCat = `"${(node.category || "Process").replace(/"/g, '""')}"`;

      // Inputs
      (node.inputs || []).forEach(inp => {
        const connectedEdge = (state.canvasEdges || []).find(e => 
          (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id) || String(e.to) === String(node.process_id)) &&
          (e.flow === inp.name || (inp.name && inp.name.includes(e.flow)))
        );
        let flowType = connectedEdge ? "Flujo Conectado" : (inp.is_unit ? "Insumo Tecnosfera" : "Insumo Auxiliar");
        let provider = connectedEdge ? `Proceso upstream (#${connectedEdge.from})` : (inp.origin || "Mercado global");
        csv += `${pid},${pName},${pCat},"${flowType}","${(inp.name || "").replace(/"/g, '""')}","${provider.replace(/"/g, '""')}",${inp.amount !== undefined ? inp.amount : 1.0},"${(inp.unit || "kg").replace(/"/g, '""')}"\n`;
      });

      // Outputs
      (node.outputs || []).forEach(out => {
        let flowType = out.is_reference ? "Producto de Referencia" : (out.is_waste ? "Residuo / Salida" : (out.is_elementary ? "Emisión Biosférica" : "Salida Técnica"));
        let dest = out.is_reference ? "Producto principal" : (out.is_waste ? "Tratamiento de residuos" : "Medio ambiente");
        csv += `${pid},${pName},${pCat},"${flowType}","${(out.name || "").replace(/"/g, '""')}","${dest.replace(/"/g, '""')}",${out.amount !== undefined ? out.amount : 1.0},"${(out.unit || "kg").replace(/"/g, '""')}"\n`;
      });
    });

    csv += "\n";
    csv += "========================================================================\n";
    csv += "SISTEMA PRODUCTO: MATRIZ DE CONEXIONES DIRECTAS (CADENA DE SUMINISTRO)\n";
    csv += "========================================================================\n";
    csv += "ID Vínculo,Proceso Origen (Salida),Flujo Transferido,Proceso Destino (Entrada),Cantidad,Unidad\n";

    (state.canvasEdges || []).forEach(edge => {
      const srcNode = state.canvasNodes.find(n => String(n.id) === String(edge.from) || String(n.process_id) === String(edge.source_process_id));
      const tgtNode = state.canvasNodes.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id));
      const srcName = srcNode ? srcNode.name : edge.from;
      const tgtName = tgtNode ? tgtNode.name : edge.to;
      csv += `"${edge.id}","${srcName.replace(/"/g, '""')}","${(edge.flow || "").replace(/"/g, '""')}","${tgtName.replace(/"/g, '""')}",${edge.amount !== undefined ? edge.amount : 1.0},"${(edge.unit || "kg").replace(/"/g, '""')}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification(window.I18n ? window.I18n.t("canvas.csv_exported_ok", "Hoja de cálculo exportada en CSV compatible con Excel.") : "Hoja de cálculo exportada en CSV.");
  }

  function openTableConnectModal() {
    if (!state.canvasNodes || state.canvasNodes.length < 2) {
      alert("Debes tener al menos 2 procesos en el sistema para conectar flujos.");
      return;
    }

    const modal = document.getElementById("modalConnectNodes");
    const staticBox = document.getElementById("connectNodesStaticBox");
    const selectBox = document.getElementById("connectNodesSelectBox");
    const selectSrc = document.getElementById("selectConnectSourceNode");
    const selectTgt = document.getElementById("selectConnectTargetNode");
    const selectFlow = document.getElementById("selectConnectSourceFlow");
    const flowInput = document.getElementById("inputConnectFlowName");
    const amtInput = document.getElementById("inputConnectAmount");
    const unitInput = document.getElementById("inputConnectUnit");

    if (staticBox) staticBox.style.display = "none";
    if (selectBox) selectBox.style.display = "block";

    if (selectSrc && selectTgt) {
      let srcOpts = "";
      let tgtOpts = "";
      state.canvasNodes.forEach((node, i) => {
        srcOpts += `<option value="${node.id}" ${i === 0 ? 'selected' : ''}>${escapeHtml(node.name)} (#${node.process_id || node.id})</option>`;
        tgtOpts += `<option value="${node.id}" ${i === 1 ? 'selected' : ''}>${escapeHtml(node.name)} (#${node.process_id || node.id})</option>`;
      });
      selectSrc.innerHTML = srcOpts;
      selectTgt.innerHTML = tgtOpts;

      const updateFlowsFromChosenSource = () => {
        const srcId = selectSrc.value;
        const srcNode = state.canvasNodes.find(n => String(n.id) === String(srcId) || String(n.process_id) === String(srcId));
        if (!srcNode) return;

        state.connectingFromNode = srcNode;

        const refFlow = srcNode.reference_flow || {};
        const defaultFlowName = refFlow.name || srcNode.name || "Flujo Conectado";
        const defaultAmt = refFlow.amount !== undefined ? refFlow.amount : (srcNode.amount || 1.0);
        const defaultUnit = refFlow.unit || srcNode.unit || "kg";

        if (flowInput) flowInput.value = defaultFlowName;
        if (amtInput) amtInput.value = Number(defaultAmt).toFixed(3);
        if (unitInput) unitInput.value = defaultUnit;

        if (selectFlow) {
          let opts = `<option value="">-- Flujo principal: ${escapeHtml(defaultFlowName)} (${defaultAmt} ${defaultUnit}) --</option>`;
          if (srcNode.outputs && Array.isArray(srcNode.outputs) && srcNode.outputs.length > 0) {
            srcNode.outputs.forEach((out, oIdx) => {
              const typeBadge = out.is_reference ? '⭐ [Referencia]' : out.is_waste ? '♻️ [Residuo]' : '📦 [Coproducto]';
              opts += `<option value="${oIdx}">${typeBadge} ${escapeHtml(out.name)} (${Number(out.amount || 1.0).toFixed(3)} ${out.unit || 'kg'})</option>`;
            });
          }
          selectFlow.innerHTML = opts;
          selectFlow.onchange = () => {
            const selVal = selectFlow.value;
            if (selVal !== "" && srcNode.outputs && srcNode.outputs[selVal]) {
              const chosen = srcNode.outputs[selVal];
              flowInput.value = chosen.name;
              amtInput.value = Number(chosen.amount || 1.0).toFixed(3);
              unitInput.value = chosen.unit || "kg";
            } else {
              flowInput.value = defaultFlowName;
              amtInput.value = Number(defaultAmt).toFixed(3);
              unitInput.value = defaultUnit;
            }
          };
        }
      };

      selectSrc.onchange = updateFlowsFromChosenSource;
      selectTgt.onchange = () => {
        const tgtId = selectTgt.value;
        state.connectingToNode = state.canvasNodes.find(n => String(n.id) === String(tgtId) || String(n.process_id) === String(tgtId));
      };

      updateFlowsFromChosenSource();
      const firstTgt = state.canvasNodes.find(n => String(n.id) === String(selectTgt.value) || String(n.process_id) === String(selectTgt.value));
      state.connectingToNode = firstTgt || state.canvasNodes[1] || null;
    }

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
    }
  }

  // Modificaciones directas desde la tabla
  function tableUpdateAmount(nodeId, type, idx, value, isInputEvent = false) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const num = parseFloat(value) || 0;

    if (type === "input" && node.inputs && node.inputs[idx]) {
      node.inputs[idx].amount = num;
      // Actualizar también arista conectada si existe
      const edge = (state.canvasEdges || []).find(e => 
        (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id) || String(e.to) === String(node.process_id)) &&
        (e.flow === node.inputs[idx].name || (node.inputs[idx].name && node.inputs[idx].name.includes(e.flow)))
      );
      if (edge) edge.amount = num;
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      node.outputs[idx].amount = num;
      if (node.outputs[idx].is_reference) {
        if (!node.reference_flow) node.reference_flow = {};
        node.reference_flow.amount = num;
        node.amount = num;
      }
      // Actualizar aristas salientes
      (state.canvasEdges || []).filter(e => 
        (String(e.from) === String(node.id) || String(e.source_process_id) === String(node.process_id) || String(e.from) === String(node.process_id)) &&
        (e.flow === node.outputs[idx].name || (node.outputs[idx].name && node.outputs[idx].name.includes(e.flow)))
      ).forEach(e => e.amount = num);
    }

    scheduleAutoSaveCanvas();
    if (!isInputEvent) {
      if (state.selectedNode && String(state.selectedNode.id) === String(node.id)) {
        inspectNode(node);
      }
    }
  }

  function tableUpdateFlowName(nodeId, type, idx, newName) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (newName || "").trim();
    if (!trimmed) return;

    if (type === "input" && node.inputs && node.inputs[idx]) {
      const oldName = node.inputs[idx].name;
      node.inputs[idx].name = trimmed;
      (state.canvasEdges || []).filter(e => 
        (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id)) &&
        (e.flow === oldName || (oldName && oldName.includes(e.flow)))
      ).forEach(e => e.flow = trimmed);
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      const oldName = node.outputs[idx].name;
      node.outputs[idx].name = trimmed;
      if (node.outputs[idx].is_reference) {
        if (!node.reference_flow) node.reference_flow = {};
        node.reference_flow.name = trimmed;
      }
      (state.canvasEdges || []).filter(e => 
        (String(e.from) === String(node.id) || String(e.source_process_id) === String(node.process_id)) &&
        (e.flow === oldName || (oldName && oldName.includes(e.flow)))
      ).forEach(e => e.flow = trimmed);
    }

    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableUpdateUnit(nodeId, type, idx, newUnit) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (newUnit || "kg").trim();

    if (type === "input" && node.inputs && node.inputs[idx]) {
      node.inputs[idx].unit = trimmed;
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      node.outputs[idx].unit = trimmed;
      if (node.outputs[idx].is_reference) {
        if (!node.reference_flow) node.reference_flow = {};
        node.reference_flow.unit = trimmed;
        node.unit = trimmed;
      }
    }

    scheduleAutoSaveCanvas();
  }

  function tableUpdateProcessName(nodeId, newName) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (newName || "").trim();
    if (!trimmed) return;
    node.name = trimmed;
    scheduleAutoSaveCanvas();
  }

  function tableDeleteFlow(nodeId, type, idx) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;

    if (type === "input" && node.inputs && node.inputs[idx]) {
      const flowName = node.inputs[idx].name;
      node.inputs.splice(idx, 1);
      state.canvasEdges = (state.canvasEdges || []).filter(e => 
        !(String(e.to) === String(node.id) && (e.flow === flowName || flowName.includes(e.flow)))
      );
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      if (node.outputs[idx].is_reference) {
        alert("El flujo de referencia del proceso no puede ser eliminado.");
        return;
      }
      const flowName = node.outputs[idx].name;
      node.outputs.splice(idx, 1);
      state.canvasEdges = (state.canvasEdges || []).filter(e => 
        !(String(e.from) === String(node.id) && (e.flow === flowName || flowName.includes(e.flow)))
      );
    }

    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableAddFlow(nodeId, type) {
    const node = state.canvasNodes.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;

    const defaultTitle = type === "input" ? "Nuevo Insumo Técnico" : "Nuevo Subproducto / Residuo";
    const name = prompt(type === "input" ? "Nombre del insumo técnico o energía (Entrada):" : "Nombre del producto, subproducto o emisión (Salida):", defaultTitle);
    if (!name || !name.trim()) return;

    if (type === "input") {
      if (!node.inputs) node.inputs = [];
      node.inputs.push({
        name: name.trim(),
        amount: 1.000,
        unit: "kg",
        is_unit: true,
        origin: "Catálogo / Suministro"
      });
    } else {
      if (!node.outputs) node.outputs = [];
      node.outputs.push({
        name: name.trim(),
        amount: 1.000,
        unit: "kg",
        is_waste: false,
        is_reference: false,
        is_elementary: false
      });
    }

    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableUpdateEdgeAmount(edgeId, value) {
    const edge = (state.canvasEdges || []).find(e => String(e.id) === String(edgeId));
    if (!edge) return;
    const num = parseFloat(value) || 0;
    edge.amount = num;
    scheduleAutoSaveCanvas();
  }

  function tableDeleteEdge(edgeId) {
    state.canvasEdges = (state.canvasEdges || []).filter(e => String(e.id) !== String(edgeId));
    scheduleAutoSaveCanvas();
    renderCanvasTableView();
    showNotification("Conexión eliminada.");
  }

  // =========================================================================
  // 7. EXPLORADOR & CATÁLOGO LCI (ecoinvent 3.12)
  // =========================================================================
  async function loadCatalogCategories() {
    try {
      const select = document.getElementById("selectCatalogCategory");
      if (!select || select.dataset.loaded === "true") return;
      const res = await api.getCategories(100);
      const catList = res.items || res.categories || [];
      if (catList.length > 0) {
        const ownCat = catList.find(c => c.id === 999999 || (c.name && c.name.toLowerCase().includes("propio")));
        const otherCats = catList.filter(c => c !== ownCat);

        let html = `<option value="ALL">All Categories (26,533 processes)</option>`;
        if (ownCat) {
          html += `<option value="${ownCat.id}" style="font-weight: 700; color: var(--accent-emerald);">⭐ ${ownCat.name} (${ownCat.process_count || 0})</option>`;
        } else {
          html += `<option value="999999" style="font-weight: 700; color: var(--accent-emerald);">⭐ Custom processes & flows</option>`;
        }
        html += otherCats.map(c => `
          <option value="${c.id || c.category_id}">${c.name || c.category_name} (${c.process_count || 0})</option>
        `).join('');
        select.innerHTML = html;
        select.dataset.loaded = "true";
      }
    } catch (e) {
      console.warn("Could not load categories:", e);
    }
  }

  async function loadCatalog() {
    try {
      await loadCatalogCategories();
      const q = document.getElementById("inputCatalogSearch")?.value || "";
      const catSelect = document.getElementById("selectCatalogCategory");
      const catVal = catSelect ? catSelect.value : state.catalogFilter;
      const res = await api.searchCatalog(q, catVal, 40);
      state.catalogProcesses = res.items || [];

      // Si la categoría seleccionada es "Custom processes & flows", cargamos solo los flujos creados por el usuario
      if (String(catVal) === "999999") {
        try {
          const flowRes = await api.getDbFlows(q, "ALL", 100, "999999");
          state.catalogCustomFlows = (flowRes.items || []).filter(f => {
            const fid = String(f.id || f.code || "");
            // Solo flujos explícitamente creados por el usuario (FL_CUSTOM_)
            return fid.startsWith("FL_CUSTOM_");
          });
        } catch (fErr) {
          console.warn("Error fetching custom flows for catalog:", fErr);
          state.catalogCustomFlows = [];
        }
      } else {
        state.catalogCustomFlows = [];
      }

      renderCatalogList();

      if (state.catalogProcesses.length > 0 && !state.selectedCatalogProcess) {
        selectCatalogProcess(state.catalogProcesses[0].id);
      }
    } catch (err) {
      console.error("Error al cargar catálogo:", err);
    }
  }

  function renderCatalogList() {
    const container = document.getElementById("catalogProcessList");
    if (!container) return;

    const catSelect = document.getElementById("selectCatalogCategory");
    const isCustomCat = catSelect && String(catSelect.value) === "999999";

    if (state.catalogProcesses.length === 0 && (!state.catalogCustomFlows || state.catalogCustomFlows.length === 0)) {
      container.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 11px;">${isCustomCat ? 'You have not created any custom processes or flows yet. Use the "+ Create Blank Process" button on the canvas to create them.' : 'No processes found in ecoinvent 3.12.'}</div>`;
      return;
    }

    let html = "";
    if (state.catalogProcesses.length > 0) {
      if (isCustomCat) {
        html += `<div style="font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase;">● Custom Unit Processes (${state.catalogProcesses.length})</div>`;
      }
      html += state.catalogProcesses
        .map((proc) => {
          const isCustom = isCustomCat || proc.category_id === 999999 || String(proc.category_name || proc.category || "").toLowerCase().includes("propio") || String(proc.category_name || proc.category || "").toLowerCase().includes("custom");
          return `
        <div class="catalog-proc-item" style="padding: 10px 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s ease;" onclick="window.EconodeApp.selectCatalogProcess(${proc.id})">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0;">
              <span class="mono" style="font-size: 8.5px; font-weight: 700; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 1px 4px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25);">ID: #${proc.id}</span>
              <div style="font-size: 11.5px; font-weight: 700; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${proc.name}</div>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
              <span class="badge-pill badge-slate">${proc.location || proc.geography || "GLO"}</span>
              ${isCustom ? `
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 10px; color: #EF4444; border-color: rgba(239, 68, 68, 0.3);"
                        title="${window.I18n.t('catalog.delete_process_btn', 'Delete Process')}"
                        onclick="event.stopPropagation(); window.EconodeApp.deleteCatalogProcess(${proc.id}, '${escape(proc.name)}')">
                  🗑️
                </button>
              ` : ''}
            </div>
          </div>
          <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: var(--text-muted);">
            <span>${proc.category_name || proc.category || "Custom processes & flows"}</span>
            <span class="mono">${Number(proc.reference_amount || 1).toFixed(2)} ${proc.reference_unit || "kg"}</span>
          </div>
        </div>
      `;
        })
        .join("");
    } else if (isCustomCat) {
      html += `<div style="padding: 10px; text-align: center; color: var(--text-muted); font-size: 10.5px;">No unit processes registered in this section.</div>`;
    }

    if (isCustomCat && state.catalogCustomFlows && state.catalogCustomFlows.length > 0) {
      html += `
        <div style="margin-top: 16px; padding-top: 12px; border-top: 2px dashed var(--border-color);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 10px; font-weight: 700; color: var(--accent-emerald); text-transform: uppercase;">● Registered Custom Flows (${state.catalogCustomFlows.length})</span>
            <button type="button" class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openCreateCustomFlowModal()" style="font-size: 9.5px; padding: 2px 6px;">+ New Flow</button>
          </div>
          ${state.catalogCustomFlows.map(flow => `
            <div style="padding: 8px 10px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 6px; cursor: pointer; transition: background 0.15s ease;"
                 onmouseover="this.style.background='var(--bg-subtle)'"
                 onmouseout="this.style.background='var(--bg-card)'"
                 onclick="window.EconodeApp.selectCatalogFlow('${escape(JSON.stringify(flow))}')">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0;">
                  <strong style="font-size: 11px; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${flow.name}</strong>
                  <span class="mono badge-pill badge-emerald" style="font-size: 8.5px;">${flow.unit_symbol || 'kg'}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 10px; color: #EF4444; border-color: rgba(239, 68, 68, 0.3);"
                          title="${window.I18n.t('catalog.delete_flow_btn', 'Delete Flow')}"
                          onclick="event.stopPropagation(); window.EconodeApp.deleteCatalogFlow('${flow.id || flow.code}', '${escape(flow.name)}')">
                    🗑️
                  </button>
                </div>
              </div>
              <div style="display: flex; justify-content: space-between; margin-top: 2px; font-size: 9px; color: var(--text-muted);">
                <span>${flow.flow_type === 'PRODUCT_FLOW' ? 'Product Flow (Input)' : flow.flow_type === 'WASTE_FLOW' ? 'Waste Flow' : 'Biospheric Emission'}</span>
                <span class="mono">ID: ${flow.id}</span>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    container.innerHTML = html;
  }

  function selectCatalogFlow(escapedJson) {
    try {
      const flow = JSON.parse(unescape(escapedJson));
      state.selectedCatalogFlow = flow;
      state.selectedCatalogProcess = null;

      const titleEl = document.getElementById("catalogDetailTitle");
      const subEl = document.getElementById("catalogDetailSub");
      const inputsTable = document.getElementById("catalogInputsTable");
      const outputsTable = document.getElementById("catalogOutputsTable");
      const btnInsert = document.getElementById("btnInsertToActiveCanvas");
      const btnDelete = document.getElementById("btnDeleteCatalogItem");

      if (btnInsert) btnInsert.style.display = "none";
      if (btnDelete) {
        btnDelete.style.display = "inline-flex";
        btnDelete.onclick = () => deleteCatalogFlow(flow.id || flow.code, flow.name);
      }

      if (titleEl) {
        titleEl.innerHTML = `<span class="mono" style="font-size: 11px; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25); margin-right: 6px;">DB FLOW: #${flow.id}</span>${flow.name}`;
      }
      if (subEl) {
        const typeLabel = flow.flow_type === 'PRODUCT_FLOW' ? 'Product / Technosphere Flow' : flow.flow_type === 'WASTE_FLOW' ? 'Waste Flow' : 'Elementary Biospheric Emission';
        subEl.textContent = `Category: Custom processes & flows · Classification: ${typeLabel} · FU: 1.000 ${flow.unit_symbol || 'kg'}`;
      }
      if (inputsTable) {
        inputsTable.innerHTML = `
          <tr>
            <td><strong>Código / Identificador</strong></td>
            <td class="mono" colspan="2">${flow.id}</td>
          </tr>
          <tr>
            <td><strong>Tipo de Flujo en openLCA</strong></td>
            <td class="mono" colspan="2">${flow.flow_type}</td>
          </tr>
          <tr>
            <td><strong>Unidad de Referencia</strong></td>
            <td class="mono" colspan="2">${flow.unit_symbol || 'kg'}</td>
          </tr>
        `;
      }
      if (outputsTable) {
        outputsTable.innerHTML = `
          <tr>
            <td><strong>Descripción / Procedencia Técnica</strong></td>
            <td class="mono" colspan="2">${flow.description || 'Custom flow created by analyst in ECONODE Studio'}</td>
          </tr>
        `;
      }
    } catch (e) {
      console.error("Error displaying catalog flow:", e);
    }
  }

  async function selectCatalogProcess(procId) {
    try {
      const res = await api.getProcessSheet(procId);
      if (res && res.sheet) {
        state.selectedCatalogProcess = res.sheet;
        state.selectedCatalogFlow = null;
        renderProcessSheet(res.sheet);
      }
    } catch (err) {
      console.error("Error al obtener ficha de proceso:", err);
    }
  }

  function renderProcessSheet(sheet) {
    const titleEl = document.getElementById("catalogDetailTitle");
    const subEl = document.getElementById("catalogDetailSub");
    const inputsTable = document.getElementById("catalogInputsTable");
    const outputsTable = document.getElementById("catalogOutputsTable");
    const btnInsert = document.getElementById("btnInsertToActiveCanvas");
    const btnDelete = document.getElementById("btnDeleteCatalogItem");

    if (btnInsert) btnInsert.style.display = "inline-flex";

    const p = sheet.process || sheet;
    const isCustom = p.category_id === 999999 || String(p.category_name || "").toLowerCase().includes("propio");

    if (btnDelete) {
      if (isCustom) {
        btnDelete.style.display = "inline-flex";
        btnDelete.onclick = () => deleteCatalogProcess(p.id, p.name);
      } else {
        btnDelete.style.display = "none";
      }
    }

    if (titleEl) titleEl.innerHTML = `<span class="mono" style="font-size: 11px; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25); margin-right: 6px;">ID: #${p.id}</span>${p.name} [${p.location || "GLO"}]`;
    if (subEl) {
      subEl.textContent = `ecoinvent 3.12 Cutoff · Categoría: ${p.category_name || "Polímeros"} · UF: ${p.reference_amount || 1.0} ${p.ref_unit || "kg"}`;
    }

    // Tabla Insumos
    if (inputsTable) {
      const inputs = sheet.technosphere_inputs || [];
      if (inputs.length === 0) {
        inputsTable.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">Sin intercambios tecnosféricos registrados.</td></tr>`;
      } else {
        inputsTable.innerHTML = inputs
          .map(
            (inp) => `
          <tr>
            <td><strong>${inp.flow_name || inp.name}</strong></td>
            <td class="mono">${Number(inp.amount || 0).toFixed(4)}</td>
            <td class="mono">${inp.unit_symbol || inp.unit || "kg"}</td>
          </tr>
        `
          )
          .join("");
      }
    }

    // Tabla Emisiones
    if (outputsTable) {
      const outputs = sheet.biosphere_emissions || [];
      if (outputs.length === 0) {
        outputsTable.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">Sin emisiones biosféricas elementales.</td></tr>`;
      } else {
        outputsTable.innerHTML = outputs
          .map(
            (out) => `
          <tr>
            <td><strong>${out.flow_name || out.name}</strong></td>
            <td class="mono">${Number(out.amount || 0).toFixed(4)}</td>
            <td class="mono">${out.unit_symbol || out.unit || "kg"}</td>
          </tr>
        `
          )
          .join("");
      }
    }
  }

  async function deleteCatalogProcess(procId, procName = "") {
    const displayName = procName ? unescape(procName) : `ID #${procId}`;
    const confirmMsg = window.I18n.t("catalog.delete_process_confirm", `¿Deseas eliminar permanentemente el proceso unitario '${displayName}' de tu base de datos?`).replace("{name}", displayName);
    if (!window.confirm(confirmMsg)) return;

    try {
      const res = await api.deleteCustomProcess(procId);
      if (res && res.status === "success") {
        showNotification(window.I18n.t("catalog.process_deleted", "Proceso eliminado permanentemente de la base de datos."));
        state.selectedCatalogProcess = null;
        await loadCatalog();
      } else {
        showNotification(res?.message || "No se pudo eliminar el proceso.", "error");
      }
    } catch (err) {
      console.error("Error al eliminar proceso propio:", err);
      showNotification("Error al eliminar proceso: " + (err.message || err), "error");
    }
  }

  async function deleteCatalogFlow(flowId, flowName = "") {
    const displayName = flowName ? unescape(flowName) : `ID #${flowId}`;
    const confirmMsg = window.I18n.t("catalog.delete_flow_confirm", `¿Deseas eliminar permanentemente el flujo '${displayName}' de tu base de datos?`).replace("{name}", displayName);
    if (!window.confirm(confirmMsg)) return;

    try {
      const res = await api.deleteCustomFlow(flowId);
      if (res && res.status === "success") {
        showNotification(window.I18n.t("catalog.flow_deleted", "Flujo eliminado permanentemente de la base de datos."));
        state.selectedCatalogFlow = null;
        await loadCatalog();
      } else {
        showNotification(res?.message || "No se pudo eliminar el flujo.", "error");
      }
    } catch (err) {
      console.error("Error al eliminar flujo propio:", err);
      showNotification("Error al eliminar flujo: " + (err.message || err), "error");
    }
  }

  function insertSelectedProcessToCanvas() {
    if (!state.selectedCatalogProcess) return;
    const sheet = state.selectedCatalogProcess;
    const p = sheet.process || sheet;
    const isCustom = p.category_id === 999999 || String(p.category_name || "").toLowerCase().includes("propio") || String(p.category_name || "").toLowerCase().includes("custom");

    const formattedInputs = (sheet.technosphere_inputs && sheet.technosphere_inputs.length > 0)
      ? sheet.technosphere_inputs.slice(0, 5).map(i => ({
          name: i.flow_name || i.name || "Technosphere input",
          amount: parseFloat(i.amount) || 1.0,
          unit: i.unit_symbol || i.unit || "kg",
          is_unit: true
        }))
      : (isCustom ? [] : [
          { name: "Primary Material [GLO]", amount: 1.05, unit: "kg", is_unit: true },
          { name: "CFE electricity grid mix", amount: 0.28, unit: "kWh", is_unit: false },
          { name: "Process Cooling Water", amount: 0.015, unit: "m3", is_unit: false }
        ]);

    const formattedOutputs = isCustom && Array.isArray(sheet.outputs) && sheet.outputs.length > 0
      ? sheet.outputs.map(o => ({
          name: o.flow_name || o.name || p.ref_flow_name || p.name,
          amount: parseFloat(o.amount) || 1.0,
          unit: o.unit_symbol || o.unit || "kg",
          is_reference: o.is_reference || false,
          is_waste: o.is_waste || false,
          is_elementary: o.is_elementary || false
        }))
      : [
          {
            name: p.ref_flow_name || p.name,
            amount: parseFloat(p.reference_amount || 1.0),
            unit: p.ref_unit || p.reference_unit || "kg",
            is_reference: true
          },
          ...(isCustom ? [] : [
            {
              name: (sheet.waste_outputs && sheet.waste_outputs[0]?.flow_name) || "Plastic Scrap (Waste)",
              amount: sheet.waste_outputs && sheet.waste_outputs[0]?.amount ? parseFloat(sheet.waste_outputs[0].amount) : 0.05,
              unit: p.ref_unit || "kg",
              is_waste: true
            },
            {
              name: (sheet.biosphere_emissions && sheet.biosphere_emissions[0]?.flow_name) || "Carbon Dioxide [Air]",
              amount: sheet.biosphere_emissions && sheet.biosphere_emissions[0]?.amount ? parseFloat(sheet.biosphere_emissions[0].amount) : 0.012,
              unit: "kg",
              is_elementary: true,
              compartment: "Air"
            }
          ])
        ];

    const newPaletteItem = {
      id: `proc_lci_${p.id || Date.now()}`,
      process_id: p.id,
      name: p.name,
      category: p.category_name || p.category || "Polymers",
      unit: p.ref_unit || p.reference_unit || "kg",
      amount: parseFloat(p.reference_amount || 1.0),
      location: p.location || "GLO",
      reference_flow: {
        name: p.ref_flow_name || p.name,
        amount: parseFloat(p.reference_amount || 1.0),
        unit: p.ref_unit || p.reference_unit || "kg"
      },
      inputs: formattedInputs,
      outputs: formattedOutputs
    };

    if (!state.paletteProcesses) state.paletteProcesses = [];
    state.paletteProcesses.unshift(newPaletteItem);
    renderPaletteProcesses();
    showNotification(`Process "${p.name}" inserted into Process Catalog (palette).`);
    showView("canvas");
  }

  // =========================================================================
  // 8. REPORTE DINÁMICO & HILOS COLABORATIVOS (3 ROLES) & EXPORTACIONES
  // =========================================================================
  async function loadReport() {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = (sysId === 21 || sysId === 1);
    try {
      const res = await api.getComments(sysId);
      state.comments = (res.items || []).filter(c => {
        if (isOfficialSys) {
          return c.system_id === 21 || c.system_id === 1;
        }
        return c.system_id === sysId;
      });
      renderCommentsThread();
      renderReportProcessesTable();
      applyRolePermissions();
    } catch (err) {
      console.error("Error al cargar reporte:", err);
      state.comments = [];
      applyRolePermissions();
    }
  }

  function renderReportProcessesTable() {
    const tbody = document.getElementById("reportBodyProcesses");
    const lciBody = document.getElementById("reportBodyLciConsolidated");
    if (!tbody) return;

    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");

    if (!state.canvasNodes || state.canvasNodes.length === 0) {
      if (isOfficialSys) {
        // En el sistema oficial se conservan los 3 procesos demo
        const defaultNodes = [
          { name: "PET Preform Injection Molding", ref: "1.000 kg Preform", in: "Virgin PET granulate (1.05 kg), CFE 230kV, Cooling Water", waste: "0.050 kg Scrap", em: "0.012 kg CO2" },
          { name: "PET Bottle Stretch Blow Molding", ref: "1.000 u Bottle", in: "Connected preform (1.00 kg), 40bar Air, Electricity", waste: "0.002 kg Scrap", em: "0.005 MJ Heat" },
          { name: "PET Bottle Distribution & Logistics", ref: "1.000 u Distributed", in: "Connected bottle (1.00 u), Diesel, Truck 350km", waste: "0.0001 kg Used Oil", em: "0.021 kg CO2" }
        ];
        tbody.innerHTML = defaultNodes.map(n => `
          <tr>
            <td><strong style="color: var(--text-primary);">${n.name}</strong></td>
            <td><span class="mono" style="font-weight: 700; color: var(--accent-emerald);">${n.ref}</span></td>
            <td style="font-size: 10px; color: var(--text-secondary); line-height: 1.4;">${n.in}</td>
            <td><span class="badge-pill badge-slate">${n.waste}</span></td>
            <td style="font-size: 10px; color: var(--text-muted);">${n.em}</td>
          </tr>
        `).join('');
      } else {
        // En sistemas creados por el usuario sin nodos, mostrar estado limpio
        tbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">
              <div style="font-size: 20px; margin-bottom: 4px;">🎨</div>
              <div style="font-weight: 600; color: var(--text-secondary);">No modeled processes on canvas</div>
              <div style="font-size: 10.5px; margin-top: 4px;">Model processes on the canvas to automatically generate report stages and balances.</div>
            </td>
          </tr>
        `;
        if (lciBody) {
          lciBody.innerHTML = `
            <tr>
              <td colspan="4" style="text-align: center; padding: 18px; color: var(--text-muted); font-size: 11px;">
                The life cycle inventory (LCI) will be consolidated automatically once you add inputs and processes on the canvas.
              </td>
            </tr>
          `;
        }
        return;
      }
    } else {
      tbody.innerHTML = state.canvasNodes.map(n => {
        const refText = n.reference_flow ? `${n.reference_flow.amount} ${n.reference_flow.unit} ${n.reference_flow.name}` : `${n.amount || 1.0} ${n.unit || 'u'}`;
        const inText = (n.inputs && n.inputs.length > 0) ? n.inputs.map(i => `${i.name} (${i.amount} ${i.unit})`).join("<br>") : "<span style='color:var(--text-dim);'>No inputs</span>";
        const wasteText = (n.outputs && n.outputs.find(o => o.is_waste)) ? n.outputs.find(o => o.is_waste).name : "No waste";
        const emText = (n.outputs && n.outputs.find(o => o.is_elementary)) ? n.outputs.find(o => o.is_elementary).name : "No direct emissions";

        return `
          <tr>
            <td><strong style="color: var(--text-primary);">${n.name}</strong></td>
            <td><span class="mono" style="font-weight: 700; color: var(--accent-emerald);">${refText}</span></td>
            <td style="font-size: 10px; color: var(--text-secondary); line-height: 1.4;">${inText}</td>
            <td><span class="badge-pill badge-slate">${wasteText}</span></td>
            <td style="font-size: 10px; color: var(--text-muted);">${emText}</td>
          </tr>
        `;
      }).join('');
    }

    // Poblar la tabla de LCI Consolidado dinámicamente a partir de los inputs de los nodos
    if (lciBody) {
      const consolidatedInputs = [];
      state.canvasNodes.forEach(node => {
        (node.inputs || []).forEach(inp => {
          consolidatedInputs.push({
            name: inp.name,
            amount: inp.amount,
            unit: inp.unit,
            verified: inp.is_unit ? "✓ Connected Unit Flow" : "✓ Technosphere Input"
          });
        });
        (node.outputs || []).filter(o => o.is_waste || o.is_elementary).forEach(out => {
          consolidatedInputs.push({
            name: out.name,
            amount: out.amount,
            unit: out.unit,
            verified: out.is_waste ? "Waste (Closed Loop)" : "Biospheric Emission"
          });
        });
      });

      if (consolidatedInputs.length === 0 && isOfficialSys) {
        lciBody.innerHTML = `
          <tr>
            <td>Virgin PET granulate [GLO] (ecoinvent)</td>
            <td class="mono">1.050</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-emerald">✓ Validated Plant/CFE Invoice</span></td>
          </tr>
          <tr>
            <td>CFE electricity grid mix 230kV [MX]</td>
            <td class="mono">0.420</td>
            <td class="mono">kWh</td>
            <td><span class="badge-pill badge-emerald">✓ Verified CFE Utility Bill</span></td>
          </tr>
          <tr>
            <td>Diesel freight truck transport 16-32t [MX]</td>
            <td class="mono">0.0084</td>
            <td class="mono">t·km</td>
            <td><span class="badge-pill badge-emerald">✓ Compliant 350 km Freight</span></td>
          </tr>
          <tr>
            <td>Purge PET plastic scrap (Waste)</td>
            <td class="mono">0.052</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-slate">Closed Loop Recycling</span></td>
          </tr>
        `;
      } else if (consolidatedInputs.length > 0) {
        lciBody.innerHTML = consolidatedInputs.map(item => `
          <tr>
            <td>${item.name}</td>
            <td class="mono">${Number(item.amount).toFixed(3)}</td>
            <td class="mono">${item.unit}</td>
            <td><span class="badge-pill badge-emerald">${item.verified}</span></td>
          </tr>
        `).join('');
      } else {
        lciBody.innerHTML = `
          <tr>
            <td colspan="4" style="text-align: center; padding: 18px; color: var(--text-muted); font-size: 11px;">
              No inventory flows recorded in current processes.
            </td>
          </tr>
        `;
      }
    }
  }

  function renderCommentsThread() {
    const container = document.getElementById("commentsThreadContainer");
    if (!container) return;

    const seenComments = new Set();
    const uniqueComments = [];
    for (const c of (state.comments || [])) {
      const key = `${c.system_id}_${(c.content || "").trim().toLowerCase()}`;
      if (!seenComments.has(key)) {
        seenComments.add(key);
        uniqueComments.push(c);
      }
    }

    if (uniqueComments.length === 0) {
      container.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 14px;">${window.I18n.t("app.no_comments", "No hay notas u observaciones abiertas.")}</div>`;
      return;
    }

    container.innerHTML = uniqueComments
      .map((c) => {
        const isAuditor = c.author_role === "auditor";
        const isAnalyst = c.author_role === "analyst";
        const isResolved = c.status === "resolved";

        let roleBadge = window.I18n.t("roles.auditor", "Auditor Líder");
        let avatarBg = "#0F172A";
        let initials = "JA";

        if (isAnalyst) {
          roleBadge = window.I18n.t("roles.analyst", "Analista");
          avatarBg = "#0284C7";
          initials = "CM";
        } else if (!isAuditor) {
          roleBadge = window.I18n.t("roles.client", "Cliente");
          avatarBg = "var(--accent-emerald)";
          initials = "ER";
        }

        const statusLabel = isResolved ? window.I18n.t("app.resolved", "Resuelto ✓") : window.I18n.t("app.pending", "Pendiente");
        const replyPrefix = window.I18n.t("app.reply_label", "Respuesta");

        return `
        <div style="background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px; margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <div class="user-avatar" style="width: 20px; height: 20px; font-size: 8.5px; background: ${avatarBg};">
                ${initials}
              </div>
              <strong style="font-size: 11px;">${c.author_name}</strong>
              <span style="font-size: 9px; color: var(--text-muted);">(${roleBadge})</span>
            </div>
            <span class="badge-pill ${isResolved ? "badge-emerald" : "badge-slate"}">${statusLabel}</span>
          </div>

          <p style="font-size: 11.5px; color: var(--text-primary); line-height: 1.4; margin-bottom: 6px;">
            ${c.content}
          </p>

          ${
            c.reply
              ? `
            <div style="background: #FFFFFF; border-left: 2px solid var(--accent-emerald); padding: 6px 10px; margin-top: 6px; font-size: 10.5px; border-radius: 2px;">
              <strong style="color: var(--accent-emerald);">${replyPrefix} (${c.resolved_by || "Cliente"}):</strong>
              <div>${c.reply}</div>
            </div>
          `
              : ""
          }

          ${
            !isResolved
              ? `
            <div style="display: flex; gap: 6px; margin-top: 8px;">
              <input type="text" class="form-input" id="replyInput_${c.id}" placeholder="Escribir aclaración técnica..." style="height: 28px; font-size: 10.5px;">
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.resolveComment(${c.id})">${window.I18n.t("app.resolved", "Resolver ✓")}</button>
            </div>
          `
              : ""
          }

          ${
            (c.author_name === (state.activeUser ? state.activeUser.display_name : "Carla Méndez") || (state.activeUser && state.activeUser.role === "auditor"))
              ? `
            <div style="display: flex; justify-content: flex-end; margin-top: 6px;">
              <button class="btn btn-secondary btn-sm" style="font-size: 9.5px; color: #EF4444; padding: 1px 6px;" onclick="window.EconodeApp.deleteComment(${c.id})">🗑 Eliminar Nota</button>
            </div>
          `
              : ""
          }
        </div>
      `;
      })
      .join("");
  }

  async function postNewComment() {
    const input = document.getElementById("inputNewComment");
    if (!input || !input.value.trim()) return;

    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const author = state.activeUser ? state.activeUser.display_name : "Carla Méndez";
    const role = state.activeUser ? state.activeUser.role : "analyst";

    try {
      await api.addComment(sysId, input.value.trim(), author, role);
      input.value = "";
      showNotification("Observación publicada en el hilo colaborativo.");
      loadReport();
    } catch (err) {
      alert("Error al publicar comentario: " + err.message);
    }
  }

  async function resolveComment(commentId) {
    const replyInput = document.getElementById(`replyInput_${commentId}`);
    const replyText = replyInput && replyInput.value.trim() ? replyInput.value.trim() : "Aclaración técnica y evidencia documental adjuntada.";
    const resolvedBy = state.activeUser ? state.activeUser.display_name : "Elena Ramírez (Cliente)";

    try {
      await api.resolveComment(commentId, replyText, resolvedBy);
      showNotification("Observación marcada como resuelta.");
      loadReport();
    } catch (err) {
      alert("Error al resolver comentario: " + err.message);
    }
  }

  // =========================================================================
  // 9. CHECKLIST NORMATIVO MULTI-NORMA (NOM-070, ISO 14044, ISO 14067, GHG Protocol & Custom)
  // =========================================================================
  async function loadAvailableStandards() {
    try {
      const res = await api.getStandards();
      state.availableStandards = res.standards || [];
      const select = document.getElementById("selectAuditStandard");
      if (select && state.availableStandards.length > 0) {
        const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");
        const currentVal = state.activeStandard || (isOfficialSys ? "nom070" : "");
        const placeholderOption = `<option value="" ${!currentVal ? 'selected' : ''}>-- Seleccionar Norma de Auditoría --</option>`;
        select.innerHTML = placeholderOption + state.availableStandards
          .map((std) => `<option value="${std.id}" ${std.id === currentVal ? 'selected' : ''}>${std.name} (${std.clauses_count || std.clauses?.length || 0} cl.)</option>`)
          .join("");
        select.value = currentVal;
      }
    } catch (err) {
      console.warn("No se pudieron cargar estándares dinámicos:", err);
    }
  }

  async function loadAuditChecklist(selectedStandard = null) {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");

    if (selectedStandard !== null) {
      state.activeStandard = selectedStandard;
    } else if (!state.activeStandard) {
      state.activeStandard = isOfficialSys ? "nom070" : "";
    }
    const standardId = state.activeStandard;

    // Asegurar que la lista de estándares en el select esté al día
    await loadAvailableStandards();

    const badge = document.getElementById("auditActiveStandardBadge");
    const label = document.getElementById("auditComplianceLabel");
    const bar = document.getElementById("auditProgressBar");
    const tbody = document.getElementById("auditClausesTableBody");

    if (!standardId) {
      state.checklist = [];
      state.checklistMeta = null;
      if (badge) badge.textContent = "Ninguna Norma Seleccionada";
      if (label) label.textContent = "● Pendiente de Selección de Norma por el Auditor";
      if (bar) bar.style.width = "0%";
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; padding: 36px 20px; color: var(--text-muted);">
              <div style="font-size: 28px; margin-bottom: 8px;">📋</div>
              <div style="font-size: 13.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Selecciona una Norma de Auditoría</div>
              <div style="font-size: 11px; max-width: 440px; margin: 0 auto 12px auto; line-height: 1.45;">
                Elige en el selector superior la norma oficial (NOM-070, ISO 14044, ISO 14067, GHG Protocol) o sube un checklist propio desde CSV para comenzar la auditoría técnica.
              </div>
            </td>
          </tr>
        `;
      }
      return;
    }

    try {
      const res = await api.getChecklist(sysId, standardId);
      const data = res.checklist || {};
      state.checklist = Array.isArray(data) ? data : (data.clauses || []);
      state.checklistMeta = typeof data === "object" && !Array.isArray(data) ? data : null;

      // Actualizar badge superior de norma activa
      if (badge) {
        const currentStd = (state.availableStandards || []).find((s) => s.id === standardId);
        badge.textContent = currentStd ? currentStd.name : standardId.toUpperCase();
      }

      renderChecklistTable();
      renderChecklistProgress();
    } catch (err) {
      console.error("Error al cargar checklist:", err);
    }
  }

  function renderChecklistProgress() {
    const total = state.checklist.length || 0;
    const compliantCount = state.checklist.filter((c) => c.is_compliant === true || c.status === "COMPLIANT").length;
    const pct = total > 0 ? ((compliantCount / total) * 100).toFixed(1) : "0.0";

    const label = document.getElementById("auditComplianceLabel");
    const bar = document.getElementById("auditProgressBar");

    if (label) {
      if (compliantCount === 0) {
        label.textContent = `● 0.0% Conforme (Todas las ${total} Cláusulas Pendientes de Verificación)`;
      } else {
        label.textContent = `● ${pct}% Conforme (${compliantCount} de ${total} Cláusulas Verificadas)`;
      }
    }
    if (bar) {
      bar.style.width = `${pct}%`;
    }
  }

  function renderChecklistTable() {
    const tbody = document.getElementById("auditClausesTableBody");
    if (!tbody) return;

    const isClient = state.activeUser && state.activeUser.role === "client";
    const currentStd = state.activeStandard || "";

    if (!currentStd) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 32px; color: var(--text-muted);">
            Selecciona una norma en el menú superior para desplegar las cláusulas de auditoría.
          </td>
        </tr>
      `;
      return;
    }

    if (!state.checklist || state.checklist.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No hay cláusulas registradas para esta norma.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.checklist
      .map((item) => {
        const isOk = item.is_compliant === true || item.status === "COMPLIANT";
        const compliantLabel = window.I18n.t("app.compliant_btn", "✓ Conforme");
        const pendingLabel = window.I18n.t("app.pending_btn", "⚠️ Pendiente");
        const readOnlyLabel = window.I18n.t("app.readonly_mode", "Solo lectura");

        return `
        <tr>
          <td><strong class="mono" style="font-size: 11px;">${item.clause_id}</strong></td>
          <td>
            <div style="font-weight: 600;">${item.title}</div>
            <div style="font-size: 10px; color: var(--text-muted);">${item.criterion}</div>
          </td>
          <td>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 6px;">
              <span style="font-size: 10.5px; color: var(--text-secondary); line-height: 1.35;" id="clause_evidence_text_${item.clause_id}">${item.evidence || "Evidencia técnica requerida por la norma."}</span>
              ${!isClient ? `
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9.5px;" onclick="window.EconodeApp.editClauseEvidence('${item.clause_id}', '${escape(item.evidence || '')}')" title="Editar requerimiento de evidencia">
                  ✏️
                </button>
              ` : ''}
            </div>
          </td>
          <td>
            <span class="badge-pill ${isOk ? "badge-emerald" : "badge-slate"}">
              ${isOk ? compliantLabel : "○ " + pendingLabel.replace("⚠️ ", "")}
            </span>
          </td>
          <td><span style="font-size: 10.5px; color: var(--text-muted);">${item.verified_by || item.verifier || "Josué Arentería (Auditor Líder)"}</span></td>
          <td>
            ${isClient ? `<span style="font-size: 10px; color: var(--text-muted);">${readOnlyLabel}</span>` : `
            <div style="display: flex; gap: 4px;">
              <button class="btn btn-sm ${isOk ? 'btn-emerald' : 'btn-secondary'}" style="padding: 2px 7px; font-size: 10px;" onclick="window.EconodeApp.toggleClause('${item.clause_id}', true)" title="Validar conforme">
                ${compliantLabel}
              </button>
              <button class="btn btn-sm ${!isOk ? 'btn-primary' : 'btn-secondary'}" style="padding: 2px 7px; font-size: 10px; ${!isOk ? 'background: #EF4444; border-color: #DC2626;' : ''}" onclick="window.EconodeApp.toggleClause('${item.clause_id}', false)" title="Marcar pendiente de subsanar">
                ${pendingLabel}
              </button>
            </div>`}
          </td>
        </tr>
      `;
      })
      .join("");
  }

  async function toggleClause(clauseId, isCompliant) {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const stdId = state.activeStandard || "nom070";
    try {
      const res = await api.toggleClause(sysId, clauseId, isCompliant, stdId);
      const data = res.checklist || {};
      state.checklist = Array.isArray(data) ? data : (data.clauses || []);
      state.checklistMeta = typeof data === "object" && !Array.isArray(data) ? data : null;
      renderChecklistTable();
      renderChecklistProgress();
      showNotification(`Cláusula ${clauseId} (${stdId.toUpperCase()}) actualizada.`);
    } catch (err) {
      alert("Error al actualizar cláusula: " + err.message);
    }
  }

  async function signAuditDictamen() {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const stdId = state.activeStandard || "nom070";
    try {
      const res = await api.signAudit(sysId, stdId);
      if (res && res.receipt) {
        const sealEl = document.getElementById("auditDigitalSeal");
        if (sealEl) {
          sealEl.textContent = `Sello SHA-256: ${res.receipt.digital_seal}`;
        }
        alert(
          `✓ DICTAMEN DE CONFORMIDAD NORMATIVA EMITIDO CON ÉXITO\n\n` +
          `• Sistema Producto: ${state.activeSystem ? state.activeSystem.name : 'Envase PET Circular 500ml'}\n` +
          `• Norma / Estándar: ${stdId.toUpperCase()}\n` +
          `• Auditor Verificador: ${res.receipt.auditor}\n` +
          `• Cláusulas Validadas: ${res.receipt.compliant_clauses} de ${res.receipt.total_clauses}\n` +
          `• Sello HMAC-SHA256: ${res.receipt.digital_seal}\n` +
          `• Marca de Tiempo: ${res.receipt.timestamp}`
        );
      }
    } catch (err) {
      alert("Error al emitir dictamen: " + err.message);
    }
  }

  // =========================================================================
  // 10. BÓVEDA DE DOCUMENTOS (SQL, EXCEL, PDF, JSON, ZIP)
  // =========================================================================
  async function loadDocumentsList() {
    const tbody = document.getElementById("docsTableBody");
    if (!tbody) return;

    try {
      const sysId = state.activeSystem ? state.activeSystem.id : 21;
      const res = await api.getDocuments(sysId);
      state.documents = res.items || [];
      renderDocumentsTable();
      loadDocsCount();
    } catch (err) {
      console.error("Error al cargar documentos:", err);
    }
  }

  function renderDocumentsTable() {
    const tbody = document.getElementById("docsTableBody");
    if (!tbody) return;

    if (state.documents.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No hay archivos custodiados en la bóveda aún.</td></tr>`;
      return;
    }

    const typeIcons = {
      sql: "🗄️",
      xlsx: "📊",
      xls: "📊",
      csv: "📑",
      pdf: "📄",
      json: "⚙️",
      zip: "📦"
    };

    tbody.innerHTML = state.documents
      .map((doc) => {
        const ext = (doc.file_type || "bin").toLowerCase();
        const icon = typeIcons[ext] || "📁";
        const sizeKb = (doc.file_size_bytes / 1024).toFixed(1);
        const hashShort = doc.sha256_hash ? doc.sha256_hash.slice(0, 12) + "..." : "SHA-256 OK";

        return `
        <tr>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 16px;">${icon}</span>
              <div>
                <strong style="color: var(--text-primary);">${doc.title}</strong>
                <div style="font-size: 9.5px; color: var(--text-muted);">${doc.original_filename}</div>
              </div>
            </div>
          </td>
          <td><span class="badge-pill badge-slate">.${ext.toUpperCase()}</span></td>
          <td><span class="mono">${sizeKb} KB</span></td>
          <td>
            <span style="font-size: 11px; font-weight: 600;">${doc.uploaded_by}</span>
            <div style="font-size: 9px; color: var(--text-muted);">${doc.user_role}</div>
          </td>
          <td>
            <div style="font-size: 10px; color: var(--text-muted);">${doc.created_at || "2026-10-07"}</div>
            <span class="mono" style="font-size: 8.5px; color: var(--accent-emerald);" title="${doc.sha256_hash}">SHA: ${hashShort}</span>
          </td>
          <td>
            <div style="display: flex; gap: 4px; align-items: center;">
              <a href="/api/documents/${doc.id}/download" class="btn btn-secondary btn-sm" download="${doc.original_filename}" title="Descargar archivo">
                🡇 Descargar
              </a>
              <button type="button" class="btn btn-secondary btn-sm" style="padding: 3px 7px; color: #EF4444;" onclick="window.EconodeApp.deleteVaultDocument(${doc.id}, '${escape(doc.title)}')" title="Eliminar este archivo de la bóveda">
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `;
      })
      .join("");
  }

  function setupDocumentsModal() {
    const modal = document.getElementById("modalDocuments");
    const btnOpen1 = document.getElementById("btnOpenDocsModal");
    const btnOpen2 = document.getElementById("btnDashOpenDocs");
    const btnClose = document.getElementById("btnCloseDocsModal");
    const btnDone = document.getElementById("btnDoneDocsModal");
    const formUpload = document.getElementById("formUploadDocument");

    const kpiDoc = document.getElementById("kpiDocCard");

    const open = () => {
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
        loadDocumentsList();
      }
    };
    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnDone) btnDone.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (formUpload) {
      formUpload.addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = document.getElementById("inputDocTitle")?.value || "";
        const fileInput = document.getElementById("inputFileDocument");

        if (!title || !fileInput || !fileInput.files || !fileInput.files[0]) {
          alert("Por favor selecciona un archivo y escribe un título.");
          return;
        }

        const file = fileInput.files[0];
        const reader = new FileReader();

        reader.onload = async function () {
          try {
            const base64Content = reader.result.split(",")[1];
            const sysId = state.activeSystem ? state.activeSystem.id : 21;
            const uploader = state.activeUser ? state.activeUser.display_name : "Usuario";
            const role = state.activeUser ? state.activeUser.role : "client";

            await api.uploadDocument({
              title: title,
              original_filename: file.name,
              content_base64: base64Content,
              system_id: sysId,
              uploaded_by: uploader,
              user_role: role,
              description: `Archivo ${file.name} custodiado en base de datos.`
            });

            showNotification(`Archivo "${file.name}" subido exitosamente a la bóveda.`);
            formUpload.reset();
            loadDocumentsList();
          } catch (err) {
            alert("Error al subir archivo: " + err.message);
          }
        };

        reader.readAsDataURL(file);
      });
    }
  }

  // =========================================================================
  // 11. MODALES: CONEXIÓN DE NODOS, WIZARD, IMPORT CENTER & AJUSTES
  // =========================================================================

  // Modal Conectar Nodos
  function setupConnectNodesModal() {
    const modal = document.getElementById("modalConnectNodes");
    const btnClose = document.getElementById("btnCloseConnectModal");
    const form = document.getElementById("formConnectNodes");

    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
      cancelConnection();
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();

        let source = state.connectingFromNode;
        let target = state.connectingToNode;

        const selectSrc = document.getElementById("selectConnectSourceNode");
        const selectTgt = document.getElementById("selectConnectTargetNode");
        if ((!source || !target) && selectSrc && selectTgt) {
          const sId = selectSrc.value;
          const tId = selectTgt.value;
          source = state.canvasNodes.find(n => String(n.id) === String(sId) || String(n.process_id) === String(sId));
          target = state.canvasNodes.find(n => String(n.id) === String(tId) || String(n.process_id) === String(tId));
        }

        if (!source || !target) {
          close();
          return;
        }

        if (source.id === target.id || String(source.process_id) === String(target.process_id)) {
          alert("No se puede conectar un proceso consigo mismo.");
          return;
        }

        const flowName = (document.getElementById("inputConnectFlowName")?.value || source.reference_flow?.name || "Connected Flow").trim();
        const amount = parseFloat(document.getElementById("inputConnectAmount")?.value || "1.0");
        const unit = (document.getElementById("inputConnectUnit")?.value || "kg").trim();

        if (!state.canvasEdges) state.canvasEdges = [];
        const existingIdx = state.canvasEdges.findIndex(ed => 
          (ed.from === source.id || String(ed.source_process_id) === String(source.process_id)) &&
          (ed.to === target.id || String(ed.target_process_id) === String(target.process_id)) &&
          ed.flow === flowName
        );

        if (existingIdx >= 0) {
          state.canvasEdges[existingIdx].amount = amount;
          state.canvasEdges[existingIdx].unit = unit;
        } else {
          const newEdge = {
            id: `edge_${Date.now()}`,
            from: source.id,
            to: target.id,
            source_process_id: source.process_id || source.id,
            target_process_id: target.process_id || target.id,
            flow: flowName,
            amount: amount,
            unit: unit
          };
          state.canvasEdges.push(newEdge);
        }

        // Registrar en entradas del destino si no existe
        if (target.inputs && Array.isArray(target.inputs)) {
          const hasInp = target.inputs.some(i => (i.name || "").toLowerCase().includes(flowName.toLowerCase()));
          if (!hasInp) {
            target.inputs.push({
              name: `${flowName} (Connected Flow)`,
              amount: amount,
              unit: unit,
              is_unit: true,
              origin: source.name
            });
            if (state.selectedNode && state.selectedNode.id === target.id) {
              inspectNode(target);
            }
          }
        }

        renderCanvasEdges();
        if (state.canvasViewMode === "table") {
          renderCanvasTableView();
        }
        close();
        scheduleAutoSaveCanvas();
        showNotification(`Connection created: "${source.name}" ➔ "${target.name}" (${amount} ${unit}).`);
      });
    }
  }

  // Wizard Nuevo Sistema
  function setupWizardModal() {
    const modal = document.getElementById("modalWizard");
    const btnOpen1 = document.getElementById("btnOpenWizardModal");
    const btnOpen2 = document.getElementById("btnDashNewSystem");
    const btnClose = document.getElementById("btnCloseWizardModal");
    const btnCancel = document.getElementById("btnCancelWizard");
    const btnSubmit = document.getElementById("btnSubmitWizard");

    const open = () => {
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    };
    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnOpen1) btnOpen1.addEventListener("click", open);
    if (btnOpen2) btnOpen2.addEventListener("click", open);
    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }
    const inputName = document.getElementById("wizSystemName");
    const inputCode = document.getElementById("wizSystemCode");

    const generateSkuFromName = (name) => {
      if (!name || !name.trim()) return "";
      const clean = name
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-zA-Z0-9\s]/g, "")
        .trim();
      const words = clean.split(/\s+/).filter(Boolean);
      const prefix = words.slice(0, 3).map(w => w.slice(0, 3).toUpperCase()).join("-");
      const hash = Math.floor(100 + Math.random() * 900);
      return `SKU-${prefix || "SYS"}-${hash}`;
    };

    if (inputName && inputCode) {
      inputName.addEventListener("input", () => {
        const val = inputName.value.trim();
        if (val) {
          inputCode.value = generateSkuFromName(val);
        } else {
          inputCode.value = "";
        }
      });
    }

    if (btnSubmit) {
      btnSubmit.addEventListener("click", async () => {
        const name = document.getElementById("wizSystemName")?.value || "";
        let code = document.getElementById("wizSystemCode")?.value || "";
        const category = document.getElementById("wizSystemCategory")?.value || "";
        const geography = document.getElementById("wizSystemGeo")?.value || "";
        const amount = parseFloat(document.getElementById("wizSystemAmount")?.value || "1.0");
        const unit = document.getElementById("wizSystemUnit")?.value || "u";

        if (!name.trim()) {
          alert("Por favor escribe el nombre del sistema producto.");
          return;
        }

        if (!code) {
          code = generateSkuFromName(name);
        }

        try {
          const res = await api.createSystem({
            name,
            code,
            category,
            geography,
            reference_amount: amount,
            reference_unit: unit
          });
          close();
          showNotification(`Sistema "${name}" creado exitosamente.`);
          await loadDashboard();
          if (res.system_id) {
            openSystem(res.system_id);
          }
        } catch (err) {
          alert("Error al crear sistema: " + err.message);
        }
      });
    }
  }

  // Modal para Invitar Auditor / Cliente Colaborador
  function setupInviteCollaboratorModal() {
    const modal = document.getElementById("modalInviteCollaborator");
    const btnClose = document.getElementById("btnCloseInviteModal");
    const btnCancel = document.getElementById("btnCancelInvite");
    const btnSubmit = document.getElementById("btnSubmitInvite");

    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (btnSubmit) {
      btnSubmit.addEventListener("click", async () => {
        const sysId = parseInt(document.getElementById("inviteSystemId")?.value || "0", 10);
        const name = (document.getElementById("inviteCollaboratorName")?.value || "").trim();
        const email = (document.getElementById("inviteCollaboratorEmail")?.value || "").trim();
        const role = document.getElementById("inviteCollaboratorRole")?.value || "auditor";

        if (!sysId) {
          alert("Error: No se identificó el sistema producto.");
          return;
        }
        if (!name || !email) {
          alert("Por favor indica el nombre y correo del colaborador.");
          return;
        }

        try {
          const res = await api.inviteCollaborator(sysId, name, email, role);
          close();
          showNotification(res.message || `Colaborador ${name} asignado al proyecto.`);
          await loadDashboard();
          if (state.activeSystem && state.activeSystem.id === sysId) {
            openSystem(sysId, false);
          }
        } catch (err) {
          alert("Error al invitar colaborador: " + err.message);
        }
      });
    }
  }

  // Centro de Importación
  function setupImportModal() {
    const modal = document.getElementById("modalImport");
    const btnOpen1 = document.getElementById("btnOpenImportModal");
    const btnOpen2 = document.getElementById("btnDashImport");
    const btnClose = document.getElementById("btnCloseImportModal");
    const btnCancel = document.getElementById("btnCancelImport");
    const btnDownload = document.getElementById("btnDownloadTemplateCsv");
    const btnChoose = document.getElementById("btnChooseImportFile");
    const inputCsv = document.getElementById("inputImportFile");
    const dropzone = document.getElementById("dropzoneBox");
    const btnExecute = document.getElementById("btnExecuteImport");

    const open = () => {
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    };
    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnOpen1) btnOpen1.addEventListener("click", open);
    if (btnOpen2) btnOpen2.addEventListener("click", open);
    if (btnClose) btnClose.addEventListener("click", close);
    if (btnCancel) btnCancel.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    if (btnDownload) {
      btnDownload.addEventListener("click", () => {
        window.location.href = "/api/systems/template-csv";
      });
    }

    // Selector de tipo de importación (CSV, openLCA, Evidencias)
    const tabCsv = document.getElementById("tabImportCsv");
    const tabOpenLca = document.getElementById("tabImportOpenLca");
    const tabEvidence = document.getElementById("tabImportEvidence");

    const setImportTab = (selectedTab, acceptExt, notice) => {
      [tabCsv, tabOpenLca, tabEvidence].forEach((t) => {
        if (t) t.classList.toggle("active", t === selectedTab);
      });
      if (inputCsv) inputCsv.accept = acceptExt;
      const label = document.getElementById("importLoadedFileName");
      if (label) label.textContent = notice;
    };

    if (tabCsv) {
      tabCsv.addEventListener("click", () =>
        setImportTab(tabCsv, ".csv", "● plantilla_sistemas_parametrizados.csv (Listo)")
      );
    }
    if (tabOpenLca) {
      tabOpenLca.addEventListener("click", () =>
        setImportTab(tabOpenLca, ".json,.zip", "● Archivo openLCA JSON-LD / ZIP (Listo)")
      );
    }
    if (tabEvidence) {
      tabEvidence.addEventListener("click", () =>
        setImportTab(tabEvidence, ".pdf,.xlsx,.sql,.zip", "● Expediente técnico de auditoría NOM-070")
      );
    }

    if (btnChoose && inputCsv) {
      btnChoose.addEventListener("click", () => inputCsv.click());
      inputCsv.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
          const fileName = e.target.files[0].name;
          const label = document.getElementById("importLoadedFileName");
          if (label) label.textContent = `● ${fileName} (Cargado)`;
        }
      });
    }

    if (dropzone && inputCsv) {
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--accent-emerald)";
      });
      dropzone.addEventListener("dragleave", () => {
        dropzone.style.borderColor = "var(--border-strong)";
      });
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--border-strong)";
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          inputCsv.files = e.dataTransfer.files;
          const label = document.getElementById("importLoadedFileName");
          if (label) label.textContent = `● ${e.dataTransfer.files[0].name} (Cargado)`;
        }
      });
    }

    if (btnExecute) {
      btnExecute.addEventListener("click", async () => {
        let fileContent = "";
        if (inputCsv && inputCsv.files && inputCsv.files[0]) {
          const file = inputCsv.files[0];
          fileContent = await file.text();
        }

        try {
          const res = await api.importCsv(fileContent);
          close();
          showNotification(`Importación completada: ${res.systems_imported || 1} sistemas creados.`);
          await loadDashboard();
          showView("dashboard");
        } catch (err) {
          alert("Error al importar archivos: " + err.message);
        }
      });
    }
  }

  // Ajustes & Facturación Modal
  function setupSettingsModal() {
    const modal = document.getElementById("modalSettings");
    const btnOpen = document.getElementById("btnOpenSettingsModal");
    const btnClose = document.getElementById("btnCloseSettingsModal");
    const btnDone = document.getElementById("btnDoneSettings");
    const userMenu = document.getElementById("btnUserMenu");

    const open = () => {
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    };
    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnOpen) btnOpen.addEventListener("click", open);
    if (userMenu) {
      userMenu.addEventListener("click", () => {
        open();
        switchSettingsTab("profile");
      });
    }
    if (btnClose) btnClose.addEventListener("click", close);
    if (btnDone) btnDone.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }

    const tabs = ["billing", "profile", "workspace", "databases", "crypto"];
    tabs.forEach((tab) => {
      const btn = document.getElementById(`tabSettings${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
      if (btn) {
        btn.addEventListener("click", () => switchSettingsTab(tab));
      }
    });
  }

  function switchSettingsTab(tabName) {
    const tabs = ["billing", "profile", "workspace", "databases", "crypto"];
    tabs.forEach((tab) => {
      const btn = document.getElementById(`tabSettings${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
      if (btn) btn.classList.toggle("active", tab === tabName);
    });

    const contentArea = document.getElementById("settingsContentArea");
    if (!contentArea) return;

    if (tabName === "billing") {
      contentArea.innerHTML = `
        <div style="margin-bottom: 16px;">
          <span class="badge-pill badge-emerald">● SUSCRIPCIÓN ACTIVA · TIER 1</span>
          <h3 style="font-size: 16px; font-weight: 700; margin-top: 6px;">ECONODE Studio & Auditoría ACV</h3>
          <p style="font-size: 11px; color: var(--text-muted);">$2,400.00 USD / año · Licencia corporativa institucional</p>
          <div style="margin-top: 8px; font-size: 11px; color: var(--text-secondary);">
            ✓ Sistemas producto ilimitados &nbsp;|&nbsp; ✓ ecoinvent 3.12 y Sphera oficiales &nbsp;|&nbsp; ✓ Sellos SHA-256
          </div>
        </div>

        <div style="background: var(--accent-emerald-light); border: 1px solid var(--accent-emerald-border); border-radius: var(--radius-lg); padding: 16px; margin-top: 18px;">
          <span class="badge-pill badge-emerald">MÓDULO OPCIONAL · TIER 2 ADD-ON</span>
          <h4 style="font-size: 14px; font-weight: 700; margin-top: 6px; color: var(--text-primary);">Motor de Cálculo Matricial & Simulación Monte Carlo</h4>
          <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.5; margin-top: 4px;">
            Desbloquea el motor de cómputo matricial directo (s = A⁻¹f), árboles de corte con bucles de reciclaje y 1,000 iteraciones estocásticas de incertidumbre con matriz Pedigree.
          </p>
          <button class="btn btn-primary btn-sm" style="margin-top: 10px;" onclick="alert('El módulo de cálculo matricial Tier 2 es una suscripción add-on. Contacta a ventas institucionales.')">
            Desbloquear Motor Matricial (Tier 2) ➔
          </button>
        </div>
      `;
    } else if (tabName === "profile") {
      const user = state.activeUser || { display_name: "Carla Méndez", email: "carla.mendez@econode.io", role: "analyst" };
      contentArea.innerHTML = `
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 12px;">Perfil de Usuario & Sesión Activa</h3>
          <div class="form-group">
            <label class="form-label">Nombre del Titular</label>
            <input type="text" class="form-input" value="${user.display_name || ''}" readonly>
          </div>
          <div class="form-group">
            <label class="form-label">Correo Electrónico</label>
            <input type="text" class="form-input" value="${user.email || ''}" readonly>
          </div>
          <div class="form-group">
            <label class="form-label">Rol Activo en la Plataforma</label>
            <input type="text" class="form-input" value="${user.role === 'analyst' ? 'Analista de ACV (Creador)' : user.role === 'auditor' ? 'Auditor Líder NOM-070' : 'Cliente Productor'}" readonly>
          </div>
          <div style="margin-top: 14px; padding: 10px 14px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: 10px; color: var(--text-muted);">
            Token de Sesión Cifrado: <span class="mono">eco_sec_••••••••44b8</span> (TLS 1.3 HMAC-SHA256)
          </div>
        </div>
      `;
    } else if (tabName === "workspace") {
      contentArea.innerHTML = `
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 12px;">Espacio de Trabajo Corporativo</h3>
          <p style="font-size: 11px; color: var(--text-secondary); margin-bottom: 14px;">Configuración regional y nomenclatura para expedientes de verificación.</p>
          <div class="form-group">
            <label class="form-label">Organización Titular</label>
            <input type="text" class="form-input" value="ECONODE Verification Bureau S.A. de C.V." readonly>
          </div>
          <div class="form-group">
            <label class="form-label">Jurisdicción Normativa</label>
            <input type="text" class="form-input" value="México · NOM-070-SE-2024 / ISO 14044:2006" readonly>
          </div>
        </div>
      `;
    } else if (tabName === "databases") {
      contentArea.innerHTML = `
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 12px;">Bases de Datos LCI Conectadas</h3>
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="padding: 12px; background: var(--accent-emerald-light); border: 1px solid var(--accent-emerald-border); border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--accent-emerald); font-size: 12px;">● ecoinvent 3.12 (Cutoff Unit)</div>
              <div style="font-size: 10px; color: var(--text-secondary); margin-top: 2px;">26,533 procesos unitarios oficiales conectados vía SQLite WAL local.</div>
            </div>
            <div style="padding: 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--text-primary); font-size: 12px;">○ openLCA JSON-LD & Sphera Adapter</div>
              <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">Adaptador de importación de paquetes ILCD y flujos elementales.</div>
            </div>
          </div>
        </div>
      `;
    } else if (tabName === "crypto") {
      contentArea.innerHTML = `
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 12px;">Sello Criptográfico & Auditoría</h3>
          <p style="font-size: 11px; color: var(--text-secondary); margin-bottom: 14px;">
            Todos los balances de masa, modelos de procesos y firmas de dictamen se sellan mediante algoritmo HMAC-SHA256 con llave institucional.
          </p>
          <div style="padding: 12px; background: var(--bg-muted); border: 1px solid var(--border-strong); border-radius: var(--radius-md); font-family: var(--font-mono); font-size: 10.5px;">
            Algoritmo: HMAC-SHA256<br>
            Llave: eco_cert_2026_994a37b8...<br>
            Acreditación: EMA / NOM-070-SE-2024
          </div>
        </div>
      `;
    }
  }

  // Modal de Planes de Suscripción (Analista)
  function setupSubscriptionModal() {
    const modal = document.getElementById("modalSubscription");
    const btnClose = document.getElementById("btnCloseSubModal");
    const btnSkip = document.getElementById("btnSkipSubscription");

    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    if (btnClose) btnClose.addEventListener("click", close);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) close();
      });
    }
    if (btnSkip) {
      btnSkip.addEventListener("click", () => {
        close();
        showNotification("Espacio de Analista activado en Periodo de Prueba.");
        showView("dashboard");
      });
    }
  }

  function activateSubscription(plan) {
    const modal = document.getElementById("modalSubscription");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
    const planNames = {
      starter: "Starter ACV ($99/mes)",
      pro: "Profesional Bureau ($240/mes)",
      enterprise: "Enterprise Corporate ($590/mes)"
    };
    showNotification(`Plan ${planNames[plan] || plan} activado exitosamente.`);
    showView("dashboard");
  }

  // Comentar sobre un nodo específico
  function commentOnNode(nodeName) {
    showView("report");
    const input = document.getElementById("inputNewComment");
    if (input) {
      input.value = `[Observación sobre proceso "${nodeName}"]: `;
      input.focus();
      showNotification(`Enfocado para comentar sobre "${nodeName}".`);
    }
  }

  // Subrayado & Selección Contextual en el Reporte Dinámico (Estilo Notion/Medium flotante)
  function setupReportHighlighting() {
    const reportBody = document.getElementById("reportDocumentBody");
    const bubble = document.getElementById("reportBubbleToolbar");
    if (!reportBody || !bubble) return;

    document.addEventListener("selectionchange", () => {
      if (state.currentView !== "report" || (state.activeUser && state.activeUser.role === "client")) {
        bubble.style.display = "none";
        return;
      }
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !sel.rangeCount) {
        // Ocultar barra flotante si no hay texto seleccionado
        if (!state.pendingHighlightText) bubble.style.display = "none";
        return;
      }
      const range = sel.getRangeAt(0);
      if (!reportBody.contains(range.commonAncestorContainer)) {
        bubble.style.display = "none";
        return;
      }
      const selectedText = sel.toString().trim();
      if (selectedText.length < 2) {
        bubble.style.display = "none";
        return;
      }

      state.pendingHighlightText = selectedText;
      const rect = range.getBoundingClientRect();
      const bubbleWidth = 260;
      const leftPos = Math.max(10, Math.min(window.innerWidth - bubbleWidth - 20, rect.left + rect.width / 2 - bubbleWidth / 2 + window.scrollX));
      const topPos = Math.max(10, rect.top + window.scrollY - 44);

      bubble.style.left = `${leftPos}px`;
      bubble.style.top = `${topPos}px`;
      bubble.style.display = "flex";
    });

    // Botones de la barra flotante estilo Notion
    const bBold = document.getElementById("bubbleBold");
    const bItalic = document.getElementById("bubbleItalic");
    const bUnderline = document.getElementById("bubbleUnderline");
    const bYellow = document.getElementById("bubbleYellow");
    const bGreen = document.getElementById("bubbleGreen");
    const bClear = document.getElementById("bubbleClear");
    const bQuote = document.getElementById("bubbleQuote");

    if (bBold) bBold.addEventListener("click", () => document.execCommand("bold", false, null));
    if (bItalic) bItalic.addEventListener("click", () => document.execCommand("italic", false, null));
    if (bUnderline) bUnderline.addEventListener("click", () => document.execCommand("underline", false, null));
    if (bYellow) bYellow.addEventListener("click", () => document.execCommand("hiliteColor", false, "#FEF08A"));
    if (bGreen) bGreen.addEventListener("click", () => document.execCommand("hiliteColor", false, "#BBF7D0"));
    if (bClear) bClear.addEventListener("click", () => document.execCommand("removeFormat", false, null));
    if (bQuote) {
      bQuote.addEventListener("click", () => {
        if (!state.pendingHighlightText) return;
        const input = document.getElementById("inputNewComment");
        if (input) {
          input.value = `[Sobre texto: "${state.pendingHighlightText}"]: `;
          input.focus();
          showNotification("Cita agregada al panel de auditoría.");
        }
        bubble.style.display = "none";
      });
    }

    setupReportEditorToolbar();
  }

  function setupReportEditorToolbar() {
    const btnBold = document.getElementById("btnFmtBold");
    const btnItalic = document.getElementById("btnFmtItalic");
    const btnUnderline = document.getElementById("btnFmtUnderline");
    const btnHiYellow = document.getElementById("btnFmtHighlightYellow");
    const btnHiGreen = document.getElementById("btnFmtHighlightGreen");
    const btnClearHi = document.getElementById("btnFmtClearHighlight");
    const btnInsertNote = document.getElementById("btnFmtInsertNote");
    const btnSaveEdits = document.getElementById("btnSaveReportEdits");

    if (btnBold) btnBold.addEventListener("click", () => document.execCommand("bold", false, null));
    if (btnItalic) btnItalic.addEventListener("click", () => document.execCommand("italic", false, null));
    if (btnUnderline) btnUnderline.addEventListener("click", () => document.execCommand("underline", false, null));

    if (btnHiYellow) {
      btnHiYellow.addEventListener("click", () => {
        document.execCommand("hiliteColor", false, "#FEF08A");
      });
    }

    if (btnHiGreen) {
      btnHiGreen.addEventListener("click", () => {
        document.execCommand("hiliteColor", false, "#BBF7D0");
      });
    }

    if (btnClearHi) {
      btnClearHi.addEventListener("click", () => {
        document.execCommand("removeFormat", false, null);
      });
    }

    if (btnInsertNote) {
      btnInsertNote.addEventListener("click", () => {
        const sel = window.getSelection();
        if (!sel || !sel.rangeCount) return;
        const noteHtml = `<span style="background: #FEFCE8; border: 1px solid #FEF08A; border-radius: 4px; padding: 2px 6px; font-size: 10.5px; color: #854D0E; font-weight: 600; margin: 0 4px;">[Nota: Revisión técnica NOM-070]</span>&nbsp;`;
        document.execCommand("insertHTML", false, noteHtml);
      });
    }

    if (btnSaveEdits) {
      btnSaveEdits.addEventListener("click", () => {
        const bodyEl = document.getElementById("reportDocumentBody");
        if (bodyEl) {
          const sysId = state.activeSystem ? state.activeSystem.id : 21;
          localStorage.setItem(`econode_report_${sysId}`, bodyEl.innerHTML);
          showNotification("Reporte técnico guardado localmente exitosamente.");
        }
      });
    }

    // Cargar contenido guardado previamente si existe
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const saved = localStorage.getItem(`econode_report_${sysId}`);
    const bodyEl = document.getElementById("reportDocumentBody");
    if (saved && bodyEl && saved.length > 50) {
      bodyEl.innerHTML = saved;
    }
  }

  // =========================================================================
  // 12. NOTIFICACIONES FLOTANTES (TOAST)
  // =========================================================================
  function showNotification(msg) {
    let toast = document.getElementById("econodeToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "econodeToast";
      toast.style.position = "fixed";
      toast.style.bottom = "24px";
      toast.style.right = "24px";
      toast.style.backgroundColor = "var(--accent-slate)";
      toast.style.color = "#FFFFFF";
      toast.style.padding = "10px 18px";
      toast.style.borderRadius = "var(--radius-md)";
      toast.style.boxShadow = "var(--shadow-lg)";
      toast.style.fontSize = "11.5px";
      toast.style.fontWeight = "600";
      toast.style.zIndex = "9999";
      toast.style.transition = "all 0.2s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
    }, 3200);
  }

  // =========================================================================
  // 13. INICIALIZACIÓN GLOBAL & EVENT LISTENERS
  // =========================================================================
  async function initApp() {
    // 1. Configurar Auth
    await initAuth();

    // 2. Navegación Top Navbar
    document.querySelectorAll(".nav-btn[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.getAttribute("data-view");
        showView(view);
      });
    });

    const btnHomeLogo = document.getElementById("btnNavHome");
    if (btnHomeLogo) btnHomeLogo.addEventListener("click", () => showView("home"));

    // Botones de Navegación del Landing
    const btnNavLogin = document.getElementById("btnNavLogin");
    const btnNavSignup = document.getElementById("btnNavSignup");
    const btnNavEnter = document.getElementById("btnNavEnterStudio");
    const btnHomeEnter = document.getElementById("btnHomeEnterStudio");
    const btnHomeEx = document.getElementById("btnHomeViewExamples");

    if (btnNavLogin) btnNavLogin.addEventListener("click", () => showView("login"));
    if (btnNavSignup) btnNavSignup.addEventListener("click", () => showView("signup"));
    if (btnNavEnter) btnNavEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"));
    if (btnHomeEnter) btnHomeEnter.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"));
    if (btnHomeEx) btnHomeEx.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"));

    // Botón Cerrar Sesión
    const btnLogout = document.getElementById("btnNavbarLogout");
    if (btnLogout) btnLogout.addEventListener("click", handleLogout);

    // Idioma
    const btnEs = document.getElementById("btnLangEs");
    const btnEn = document.getElementById("btnLangEn");
    if (btnEs) btnEs.addEventListener("click", () => window.I18n.setLanguage("es"));
    if (btnEn) btnEn.addEventListener("click", () => window.I18n.setLanguage("en"));

    // Enlaces Login <-> Signup
    const linkGoSignup = document.getElementById("linkGoSignup");
    const linkGoLogin = document.getElementById("linkGoLogin");
    if (linkGoSignup) linkGoSignup.addEventListener("click", (e) => { e.preventDefault(); showView("signup"); });
    if (linkGoLogin) linkGoLogin.addEventListener("click", (e) => { e.preventDefault(); showView("login"); });

    // Botones de los 3 Perfiles en Login
    const btnAnalyst = document.getElementById("btnLoginAnalyst");
    const btnAuditor = document.getElementById("btnLoginAuditor");
    const btnClient = document.getElementById("btnLoginClient");

    if (btnAnalyst) btnAnalyst.addEventListener("click", () => handleDemoLogin("analyst_carla"));
    if (btnAuditor) btnAuditor.addEventListener("click", () => handleDemoLogin("auditor_lead"));
    if (btnClient) btnClient.addEventListener("click", () => handleDemoLogin("client_elena"));

    // Formulario de Acceso Profesional con Usuario y Contraseña
    const formLogin = document.getElementById("formLogin");
    const loginErrorBox = document.getElementById("loginErrorMessage");

    if (formLogin) {
      formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userInput = document.getElementById("inputLoginEmail")?.value || "";
        const passInput = document.getElementById("inputLoginPassword")?.value || "";
        const btnSubmit = document.getElementById("btnSubmitLogin");

        if (loginErrorBox) {
          loginErrorBox.style.display = "none";
          loginErrorBox.textContent = "";
        }

        if (btnSubmit) {
          btnSubmit.disabled = true;
          btnSubmit.textContent = "Verificando...";
        }

        try {
          const res = await api.loginWithCredentials(userInput, passInput);
          if (res && res.user) {
            state.activeUser = res.user;
            state.isAuthenticated = true;
            if (res.token) {
              sessionStorage.setItem("econode_token", res.token);
              sessionStorage.setItem("econode_user_id", res.user.id || res.user.username);
            }
            updateUserUI();
            showNotification(`Bienvenido(a), ${res.user.display_name}`);
            applyRolePermissions();
            showView("dashboard");
          }
        } catch (err) {
          const msg = err.message || "Usuario o contraseña incorrectos.";
          if (loginErrorBox) {
            loginErrorBox.style.display = "block";
            loginErrorBox.textContent = `Error de autenticación: ${msg}`;
          } else {
            alert("Error: " + msg);
          }
        } finally {
          if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.textContent = "Iniciar Sesión ➔";
          }
        }
      });
    }

    // Formulario Signup (Registro de Nuevas Cuentas)
    const formSignup = document.getElementById("formSignup");
    const btnRoleAnalyst = document.getElementById("btnSignupRoleAnalyst");
    const btnRoleAuditor = document.getElementById("btnSignupRoleAuditor");
    const btnRoleClient = document.getElementById("btnSignupRoleClient");
    const inputRoleHidden = document.getElementById("inputSignupSelectedRole");

    const setSignupRole = (role) => {
      [btnRoleAnalyst, btnRoleAuditor, btnRoleClient].forEach(b => b && b.classList.remove("active"));
      if (role === "analyst" && btnRoleAnalyst) btnRoleAnalyst.classList.add("active");
      if (role === "auditor" && btnRoleAuditor) btnRoleAuditor.classList.add("active");
      if (role === "client" && btnRoleClient) btnRoleClient.classList.add("active");
      if (inputRoleHidden) inputRoleHidden.value = role;
    };

    if (btnRoleAnalyst) btnRoleAnalyst.addEventListener("click", () => setSignupRole("analyst"));
    if (btnRoleAuditor) btnRoleAuditor.addEventListener("click", () => setSignupRole("auditor"));
    if (btnRoleClient) btnRoleClient.addEventListener("click", () => setSignupRole("client"));

    if (formSignup) {
      formSignup.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("inputSignupName")?.value || "";
        const email = document.getElementById("inputSignupEmail")?.value || "";
        const org = document.getElementById("inputSignupOrg")?.value || "";
        const password = document.getElementById("inputSignupPassword")?.value || "";
        const role = inputRoleHidden ? inputRoleHidden.value : "analyst";
        const btnSubmit = document.getElementById("btnSubmitSignup");
        const signupErrorBox = document.getElementById("signupErrorMessage");

        if (signupErrorBox) {
          signupErrorBox.style.display = "none";
          signupErrorBox.textContent = "";
        }

        if (password.length < 6) {
          if (signupErrorBox) {
            signupErrorBox.style.display = "block";
            signupErrorBox.textContent = "La contraseña debe tener un mínimo de 6 caracteres.";
          } else {
            alert("La contraseña debe tener un mínimo de 6 caracteres.");
          }
          return;
        }

        if (btnSubmit) {
          btnSubmit.disabled = true;
          btnSubmit.textContent = "Creando cuenta...";
        }

        try {
          const res = await api.signup({
            full_name: name,
            email: email,
            organization: org,
            role: role,
            password: password
          });
          if (res.user) {
            state.activeUser = res.user;
            state.isAuthenticated = true;
            if (res.token) {
              sessionStorage.setItem("econode_token", res.token);
              sessionStorage.setItem("econode_user_id", res.user.id || res.user.username);
            }
            updateUserUI();
            showNotification(`Cuenta creada exitosamente para ${res.user.display_name}.`);
            if (role === "analyst") {
              const subModal = document.getElementById("modalSubscription");
              if (subModal) {
                subModal.style.display = "flex";
                subModal.classList.add("active");
              } else {
                showView("dashboard");
              }
            } else {
              showView("dashboard");
            }
          }
        } catch (err) {
          const msg = err.message || "Error al registrar la cuenta.";
          if (signupErrorBox) {
            signupErrorBox.style.display = "block";
            signupErrorBox.textContent = `Aviso de Registro: ${msg}`;
          } else {
            alert("Error: " + msg);
          }
        } finally {
          if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.textContent = "Crear Cuenta & Activar Espacio de Trabajo ➔";
          }
        }
      });
    }

    // Google Sign-In Action
    const btnGoogle = document.getElementById("btnGoogleSignInAction");
    if (btnGoogle) {
      btnGoogle.addEventListener("click", () => {
        if (window.google && window.google.accounts && window.google.accounts.id) {
          window.google.accounts.id.prompt();
        } else {
          handleDemoLogin("auditor_lead");
        }
      });
    }

    // Dashboard Filtros & Búsqueda
    document.querySelectorAll(".table-filters .segmented-btn[data-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".table-filters .segmented-btn[data-filter]").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.systemFilter = btn.getAttribute("data-filter");
        renderDashboardTable();
      });
    });

    const inputSearch = document.getElementById("inputSearchSystems");
    if (inputSearch) {
      inputSearch.addEventListener("input", () => renderDashboardTable());
    }

    // Canvas Botones & Modos Sankey
    const btnBack = document.getElementById("btnBackToDashboard");
    if (btnBack) btnBack.addEventListener("click", () => showView("dashboard"));

    const btnCanvasReport = document.getElementById("btnCanvasOpenReport");
    if (btnCanvasReport) btnCanvasReport.addEventListener("click", () => showView("report"));

    const btnSaveCanvas = document.getElementById("btnSaveCanvas");
    if (btnSaveCanvas) btnSaveCanvas.addEventListener("click", saveCanvas);

    // Sub-vistas del Lienzo: Diagrama vs Hoja de Cálculo
    const btnViewVisual = document.getElementById("btnCanvasViewVisual");
    const btnViewTable = document.getElementById("btnCanvasViewTable");
    const btnSlideToTable = document.getElementById("btnSlideToTableView");
    const btnSlideToVisual = document.getElementById("btnSlideToVisualView");

    if (btnViewVisual) btnViewVisual.addEventListener("click", () => switchCanvasViewMode("visual"));
    if (btnViewTable) btnViewTable.addEventListener("click", () => switchCanvasViewMode("table"));
    if (btnSlideToTable) btnSlideToTable.addEventListener("click", () => switchCanvasViewMode("table"));
    if (btnSlideToVisual) btnSlideToVisual.addEventListener("click", () => switchCanvasViewMode("visual"));

    // Controles de Visibilidad de Paneles Laterales (Expandir/Maximizar Lienzo)
    const btnToggleLeft = document.getElementById("btnToggleLeftSidebar");
    const btnToggleRight = document.getElementById("btnToggleRightSidebar");
    const btnToggleFull = document.getElementById("btnToggleFullCanvas");
    const btnCollapseCat = document.getElementById("btnCollapseCatalog");
    const btnCollapseInsp = document.getElementById("btnCollapseInspector");

    if (btnToggleLeft) btnToggleLeft.addEventListener("click", () => toggleLeftPanel());
    if (btnToggleRight) btnToggleRight.addEventListener("click", () => toggleRightPanel());
    if (btnToggleFull) btnToggleFull.addEventListener("click", () => toggleFullCanvas());
    if (btnCollapseCat) btnCollapseCat.addEventListener("click", () => toggleLeftPanel(false));
    if (btnCollapseInsp) btnCollapseInsp.addEventListener("click", () => toggleRightPanel(false));

    // Controles de Zoom del Lienzo (Toolbar & Floating Dock)
    const btnZIn = document.getElementById("btnZoomIn");
    const btnZOut = document.getElementById("btnZoomOut");
    const btnZReset = document.getElementById("btnZoomReset");
    const btnTbZIn = document.getElementById("btnTbZoomIn");
    const btnTbZOut = document.getElementById("btnTbZoomOut");
    const btnTbZReset = document.getElementById("btnTbZoomReset");

    const doZoomIn = () => applyCanvasZoom((state.canvasZoom || 1.0) + 0.1);
    const doZoomOut = () => applyCanvasZoom((state.canvasZoom || 1.0) - 0.1);
    const doZoomReset = () => applyCanvasZoom(1.0);

    if (btnZIn) btnZIn.addEventListener("click", doZoomIn);
    if (btnTbZIn) btnTbZIn.addEventListener("click", doZoomIn);
    if (btnZOut) btnZOut.addEventListener("click", doZoomOut);
    if (btnTbZOut) btnTbZOut.addEventListener("click", doZoomOut);
    if (btnZReset) btnZReset.addEventListener("click", doZoomReset);
    if (btnTbZReset) btnTbZReset.addEventListener("click", doZoomReset);

    // Filtros de la Hoja de Cálculo LCI
    const inputTableSearch = document.getElementById("inputTableFilter");
    if (inputTableSearch) {
      inputTableSearch.addEventListener("input", (e) => {
        state.tableFilterText = e.target.value;
        renderCanvasTableView();
      });
    }

    const selectFlowFilter = document.getElementById("selectTableFlowFilter");
    if (selectFlowFilter) {
      selectFlowFilter.addEventListener("change", (e) => {
        state.tableFlowFilter = e.target.value;
        renderCanvasTableView();
      });
    }

    const btnTableAddProc = document.getElementById("btnTableAddProcess");
    if (btnTableAddProc) {
      btnTableAddProc.addEventListener("click", () => openProcessEditor(null));
    }

    const btnTableAddConn = document.getElementById("btnTableAddConnection");
    if (btnTableAddConn) {
      btnTableAddConn.addEventListener("click", openTableConnectModal);
    }

    const btnTableCsv = document.getElementById("btnTableExportCsv");
    if (btnTableCsv) {
      btnTableCsv.addEventListener("click", exportLciTableToCsv);
    }

    // Sankey Toggle Buttons
    const btnSankeyNone = document.getElementById("btnSankeyModeNone");
    const btnSankeyMass = document.getElementById("btnSankeyModeMass");
    const btnSankeyEnergy = document.getElementById("btnSankeyModeEnergy");

    const setSankeyMode = (mode) => {
      [btnSankeyNone, btnSankeyMass, btnSankeyEnergy].forEach(b => b && b.classList.remove("active"));
      if (mode === "none" && btnSankeyNone) btnSankeyNone.classList.add("active");
      if (mode === "mass" && btnSankeyMass) btnSankeyMass.classList.add("active");
      if (mode === "energy" && btnSankeyEnergy) btnSankeyEnergy.classList.add("active");
      state.sankeyMode = mode;
      renderCanvasStage();
    };

    if (btnSankeyNone) btnSankeyNone.addEventListener("click", () => setSankeyMode("none"));
    if (btnSankeyMass) btnSankeyMass.addEventListener("click", () => setSankeyMode("mass"));
    if (btnSankeyEnergy) btnSankeyEnergy.addEventListener("click", () => setSankeyMode("energy"));

    // Sticky Notes Controls on Canvas
    const btnToggleSticky = document.getElementById("btnToggleCanvasStickyNotes");
    const labelStickyToggle = document.getElementById("labelStickyNotesToggle");

    if (btnToggleSticky) {
      btnToggleSticky.addEventListener("click", () => {
        state.showCanvasStickyNotes = !state.showCanvasStickyNotes;
        updateCanvasHeaderToolbar();
        renderCanvasStage();
        const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
        showNotification(state.showCanvasStickyNotes ? 
          (isEn ? "Sticky notes visible on canvas." : "Notas adhesivas visibles en lienzo.") : 
          (isEn ? "Sticky notes hidden on canvas." : "Notas adhesivas ocultadas en lienzo."));
      });
    }

    // Catálogo Filtros & Búsqueda
    const selectCat = document.getElementById("selectCatalogCategory");
    if (selectCat) {
      selectCat.addEventListener("change", () => {
        state.catalogFilter = selectCat.value;
        loadCatalog();
      });
    }

    const inputCatSearch = document.getElementById("inputCatalogSearch");
    if (inputCatSearch) {
      let debounceTimer = null;
      inputCatSearch.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => loadCatalog(), 300);
      });
    }

    const btnInsertCanvas = document.getElementById("btnInsertToActiveCanvas");
    if (btnInsertCanvas) btnInsertCanvas.addEventListener("click", insertSelectedProcessToCanvas);

    // Reporte: Comentarios y Exportaciones
    const btnPostComment = document.getElementById("btnPostComment");
    if (btnPostComment) btnPostComment.addEventListener("click", postNewComment);

    const btnExpOpenLca = document.getElementById("btnExportOpenLca");
    const btnReportExpOpenLca = document.getElementById("btnReportExportOpenLca");
    const btnExpIlcd = document.getElementById("btnExportIlcd");
    const btnExpSimaPro = document.getElementById("btnExportSimaPro");
    const btnExpLciCsv = document.getElementById("btnExportLciCsv");
    const btnExpPdf = document.getElementById("btnExportReportPdf");

    const getSysId = () => state.activeSystem ? state.activeSystem.id : 21;

    // Dropdown Global de Exportación en el Lienzo
    const btnExportDropdown = document.getElementById("btnCanvasExportDropdown");
    const exportMenu = document.getElementById("canvasExportMenu");
    if (btnExportDropdown && exportMenu) {
      btnExportDropdown.addEventListener("click", (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle("show");
      });
      document.addEventListener("click", (e) => {
        if (!e.target.closest(".canvas-export-dropdown-wrapper")) {
          exportMenu.classList.remove("show");
        }
      });
    }

    if (btnExpOpenLca) {
      btnExpOpenLca.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/openlca`;
      });
    }
    if (btnReportExpOpenLca) {
      btnReportExpOpenLca.addEventListener("click", () => {
        window.location.href = `/api/systems/${getSysId()}/export/openlca`;
      });
    }
    if (btnExpIlcd) {
      btnExpIlcd.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/ilcd`;
      });
    }
    if (btnExpSimaPro) {
      btnExpSimaPro.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/simapro`;
      });
    }
    if (btnExpLciCsv) {
      btnExpLciCsv.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/csv`;
      });
    }
    if (btnExpPdf) {
      btnExpPdf.addEventListener("click", () => {
        window.location.href = `/api/systems/${getSysId()}/export/pdf`;
      });
    }

    // Checklist Botones & Multi-Norma
    const btnSign = document.getElementById("btnSignAuditDictamen");
    if (btnSign) btnSign.addEventListener("click", signAuditDictamen);

    const btnExpAuditZip = document.getElementById("btnExportAuditZip");
    if (btnExpAuditZip) {
      btnExpAuditZip.addEventListener("click", () => {
        window.location.href = `/api/systems/${getSysId()}/export/expediente`;
      });
    }

    const selectAuditStd = document.getElementById("selectAuditStandard");
    if (selectAuditStd) {
      selectAuditStd.addEventListener("change", (e) => {
        const chosenStd = e.target.value;
        loadAuditChecklist(chosenStd);
      });
    }

    const btnDlTemplate = document.getElementById("btnDownloadChecklistTemplate");
    if (btnDlTemplate) {
      btnDlTemplate.addEventListener("click", () => {
        window.location.href = "/api/checklists/template-csv";
      });
    }

    const btnImportChecklist = document.getElementById("btnImportChecklistCsv");
    const inputImportChecklist = document.getElementById("inputImportChecklistFile");
    if (btnImportChecklist && inputImportChecklist) {
      btnImportChecklist.addEventListener("click", () => {
        inputImportChecklist.click();
      });

      inputImportChecklist.addEventListener("change", async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async function () {
          try {
            const csvText = reader.result;
            const stdName = prompt("Ingresa el nombre o clave de la norma a importar:", file.name.replace(".csv", ""));
            if (!stdName) return;

            const res = await api.importChecklist(csvText, {
              standard_name: stdName,
              organization: state.activeUser ? state.activeUser.organization : "ECONODE"
            });

            showNotification(res.message || "Checklist importado exitosamente.");
            await loadAuditChecklist(res.standard_id || "nom070");
          } catch (err) {
            alert("Error al importar checklist: " + err.message);
          } finally {
            inputImportChecklist.value = "";
          }
        };
        reader.readAsText(file, "UTF-8");
      });
    }

    // Configurar Modales & Listeners
    setupWizardModal();
    setupInviteCollaboratorModal();
    setupImportModal();
    setupSettingsModal();
    setupDocumentsModal();
    setupConnectNodesModal();
    setupProcessEditorModal();
    setupAddProcessCommentModal();
    setupSelectDbFlowModal();
    setupCreateCustomFlowModal();
    setupSelectProviderModal();
    setupSubscriptionModal();
    setupReportHighlighting();

    const inputPalSearch = document.getElementById("inputPaletteSearch");
    if (inputPalSearch) {
      inputPalSearch.addEventListener("input", renderPaletteProcesses);
    }

    const btnPaletteBlank = document.getElementById("btnPaletteCreateBlank");
    if (btnPaletteBlank) {
      btnPaletteBlank.addEventListener("click", () => openProcessEditor(null));
    }

    // Cierre de modales con tecla Escape y eliminación de nodo seleccionado con Delete/Backspace
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.active, .modal-overlay[style*='display: flex']").forEach((m) => {
          m.style.display = "none";
          m.classList.remove("active");
        });
      } else if ((e.key === "Delete" || e.key === "Backspace") && state.currentView === "canvas" && state.selectedNode) {
        const tag = (document.activeElement && document.activeElement.tagName) || "";
        if (tag !== "INPUT" && tag !== "TEXTAREA" && !document.activeElement.isContentEditable) {
          e.preventDefault();
          window.EconodeApp.removeNode(state.selectedNode.id);
        }
      } else if ((e.ctrlKey || e.metaKey) && state.currentView === "canvas" && state.canvasViewMode === "visual") {
        if (e.key === "+" || e.key === "=") {
          e.preventDefault();
          applyCanvasZoom((state.canvasZoom || 1.0) + 0.1);
        } else if (e.key === "-" || e.key === "_") {
          e.preventDefault();
          applyCanvasZoom((state.canvasZoom || 1.0) - 0.1);
        } else if (e.key === "0") {
          e.preventDefault();
          applyCanvasZoom(1.0);
        }
      }
    });

    // Auto-ajustar conexiones SVG del lienzo cuando la ventana del navegador cambia de tamaño
    window.addEventListener("resize", () => {
      if (state.currentView === "canvas" && state.canvasViewMode === "visual") {
        renderCanvasEdges();
      }
    });

    // 14. VISTA INICIAL: Si está autenticado, restaurar sistema producto y vista previa guardada
    if (state.isAuthenticated) {
      let savedSystemId = null;
      let savedView = null;
      try {
        savedSystemId = localStorage.getItem("econode_active_system_id");
        savedView = localStorage.getItem("econode_active_view");
      } catch (e) {}

      if (savedSystemId && (savedView === "canvas" || savedView === "report" || savedView === "audit")) {
        await openSystem(parseInt(savedSystemId, 10), savedView === "canvas");
        if (savedView !== "canvas") {
          showView(savedView);
        }
      } else {
        showView(savedView && views[savedView] ? savedView : "dashboard");
      }
    } else {
      showView("home");
    }
    updateCanvasHeaderToolbar();
  }

  // Métodos globales de acceso rápido
  window.showView = showView;
  window.openSystem = openSystem;

  // API Pública para llamadas inline desde HTML y pruebas
  window.EconodeApp = {
    showView,
    openSystem,
    selectCatalogProcess,
    deleteCatalogProcess,
    deleteCatalogFlow,
    resolveComment,
    deleteComment,
    toggleClause,
    openProcessEditor,
    openCreateCustomFlowModal,
    selectCatalogFlow,
    openSelectProviderModal,
    selectProviderForInput,
    openNodeCommentModal,
    updateEditInput,
    removeEditInput,
    updateEditOutput,
    updateEditOutputClass,
    removeEditOutput,
    setAsQuantitativeReference,
    activateSubscription,
    commentOnNode,
    confirmInsertDbFlow,
    handleDirectLogin: (roleId) => handleDemoLogin(roleId),
    openWizardModal: () => {
      const modal = document.getElementById("modalWizard");
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    },
    closeWizardModal: () => {
      const modal = document.getElementById("modalWizard");
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    },
    openInviteModal: (systemId, systemName) => {
      const modal = document.getElementById("modalInviteCollaborator");
      const idInput = document.getElementById("inviteSystemId");
      const nameInput = document.getElementById("inviteSystemNameDisplay");
      const personName = document.getElementById("inviteCollaboratorName");
      const personEmail = document.getElementById("inviteCollaboratorEmail");
      if (idInput) idInput.value = systemId;
      if (nameInput) nameInput.value = unescape(systemName || `Sistema #${systemId}`);
      if (personName) personName.value = "";
      if (personEmail) personEmail.value = "";
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    },
    closeInviteModal: () => {
      const modal = document.getElementById("modalInviteCollaborator");
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    },
    deleteSystem: async (systemId, systemName) => {
      const displayName = systemName ? unescape(systemName) : `ID #${systemId}`;
      if (!confirm(`¿Estás seguro de que deseas eliminar permanentemente el sistema producto "${displayName}"?\nEsta acción borrará sus procesos, lienzo y comentarios asociados.`)) {
        return;
      }
      try {
        await api.deleteSystem(systemId);
        showNotification(`Sistema "${displayName}" eliminado correctamente.`);
        if (state.activeSystem && state.activeSystem.id === systemId) {
          state.activeSystem = null;
          state.canvasNodes = [];
          state.canvasEdges = [];
          state.selectedNode = null;
          inspectNode(null);
          showView("dashboard");
        }
        await loadDashboard();
      } catch (err) {
        alert("Error al eliminar sistema: " + err.message);
      }
    },
    openImportModal: () => {
      const modal = document.getElementById("modalImport");
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
    },
    closeImportModal: () => {
      const modal = document.getElementById("modalImport");
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    },
    closeAllModals: () => {
      document.querySelectorAll(".modal-overlay").forEach((m) => {
        m.style.display = "none";
        m.classList.remove("active");
      });
    },
    openDocsModal: (systemId = null) => {
      if (systemId) {
        const found = state.systems.find(s => s.id === systemId);
        if (found) {
          state.activeSystem = found;
          const modalTitle = document.getElementById("modalDocsTitle");
          if (modalTitle) {
            modalTitle.textContent = `Bóveda de Documentos: ${found.name}`;
          }
        }
      }
      const modal = document.getElementById("modalDocuments");
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
        loadDocumentsList();
      }
    },
    deleteVaultDocument: async (docId, title) => {
      const displayTitle = title ? unescape(title) : `Documento #${docId}`;
      if (!confirm(`¿Deseas eliminar permanentemente el archivo "${displayTitle}" de la bóveda?`)) {
        return;
      }
      try {
        await api.deleteDocument(docId);
        showNotification(`Archivo "${displayTitle}" eliminado de la bóveda.`);
        await loadDocumentsList();
        await loadDocsCount();
      } catch (err) {
        alert("Error al eliminar documento: " + err.message);
      }
    },
    editClauseEvidence: async (clauseId, currentEvidence) => {
      const decodedEvidence = currentEvidence ? unescape(currentEvidence) : "";
      const newEvidence = prompt(`Editar evidencia requerida para la cláusula ${clauseId}:`, decodedEvidence);
      if (newEvidence === null || newEvidence.trim() === decodedEvidence.trim()) {
        return;
      }
      const sysId = state.activeSystem ? state.activeSystem.id : 21;
      const stdId = state.activeStandard || "nom070";
      try {
        const res = await api.updateClauseEvidence(sysId, clauseId, newEvidence.trim(), stdId);
        const data = res.checklist || {};
        state.checklist = Array.isArray(data) ? data : (data.clauses || []);
        state.checklistMeta = typeof data === "object" && !Array.isArray(data) ? data : null;
        renderChecklistTable();
        showNotification(`Evidencia de cláusula ${clauseId} actualizada exitosamente.`);
      } catch (err) {
        alert("Error al actualizar evidencia: " + err.message);
      }
    },
    removePaletteProcess: (procId) => {
      const targetId = String(procId);
      state.paletteProcesses = (state.paletteProcesses || []).filter(p => String(p.id) !== targetId && String(p.process_id) !== targetId);
      renderPaletteProcesses();
      showNotification("Proceso retirado del catálogo. Si lo necesitas de nuevo, puedes buscarlo en el Explorador LCI.");
    },
    updateMassBalance: () => {
      updateProcessMassBalance();
    },
    removeNode: (nodeId) => {
      const targetId = String(nodeId);
      const cleanNumeric = targetId.replace(/\D/g, "");

      // 1. Localizar el nodo en el lienzo antes de eliminarlo
      const removedNode = (state.canvasNodes || []).find((n) => {
        const nid = String(n.id);
        const npid = String(n.process_id || "");
        return nid === targetId || npid === targetId || (cleanNumeric && (nid === `node_${cleanNumeric}` || npid === cleanNumeric));
      });

      // 2. Filtrar y quitar del lienzo
      state.canvasNodes = (state.canvasNodes || []).filter((n) => {
        const nid = String(n.id);
        const npid = String(n.process_id || "");
        return nid !== targetId && npid !== targetId && (!cleanNumeric || (nid !== `node_${cleanNumeric}` && npid !== cleanNumeric));
      });

      // 3. Quitar conexiones conectadas a este nodo
      state.canvasEdges = (state.canvasEdges || []).filter((e) => {
        const ef = String(e.from);
        const et = String(e.to);
        const esrc = String(e.source_process_id || "");
        const etgt = String(e.target_process_id || "");
        return ef !== targetId && et !== targetId && esrc !== targetId && etgt !== targetId &&
               (!cleanNumeric || (ef !== `node_${cleanNumeric}` && et !== `node_${cleanNumeric}` && esrc !== cleanNumeric && etgt !== cleanNumeric));
      });

      // 4. Regresar el proceso al catálogo de procesos (paleta lateral)
      if (removedNode) {
        if (!state.paletteProcesses) state.paletteProcesses = [];
        const existsInPalette = state.paletteProcesses.some(p => 
          String(p.id) === String(removedNode.id) || 
          String(p.process_id) === String(removedNode.process_id) ||
          (cleanNumeric && String(p.process_id || p.id).includes(cleanNumeric))
        );
        if (!existsInPalette) {
          state.paletteProcesses.unshift({
            id: removedNode.id || `palette_${removedNode.process_id || Date.now()}`,
            process_id: removedNode.process_id,
            code: removedNode.code || `PR-${removedNode.process_id || removedNode.id}`,
            name: removedNode.name,
            category: removedNode.category || "Custom processes & flows",
            location: removedNode.location || "GLO",
            unit: removedNode.unit || (removedNode.reference_flow ? removedNode.reference_flow.unit : "kg"),
            amount: removedNode.amount || 1.0,
            reference_flow: removedNode.reference_flow || { name: removedNode.name, amount: 1.0, unit: removedNode.unit || "kg" },
            inputs: Array.isArray(removedNode.inputs) ? JSON.parse(JSON.stringify(removedNode.inputs)) : [],
            outputs: Array.isArray(removedNode.outputs) ? JSON.parse(JSON.stringify(removedNode.outputs)) : []
          });
        }
        renderPaletteProcesses();
      }

      if (!state.selectedNode || String(state.selectedNode.id) === targetId || String(state.selectedNode.process_id) === targetId || (cleanNumeric && (String(state.selectedNode.id).includes(cleanNumeric) || String(state.selectedNode.process_id) === cleanNumeric)) || state.canvasNodes.length === 0) {
        inspectNode(null);
      }
      renderCanvasStage();
      if (state.canvasViewMode === "table") {
        renderCanvasTableView();
      }
      scheduleAutoSaveCanvas();
      showNotification(removedNode ? `Process "${removedNode.name}" returned to process catalog.` : "Node removed from canvas.");
    },
    addPaletteNode: (param1, cat, unit) => {
      const searchStr = String(param1);
      const foundIdx = (state.paletteProcesses || []).findIndex(p => String(p.id) === searchStr || String(p.process_id) === searchStr);
      if (foundIdx >= 0) {
        const found = state.paletteProcesses[foundIdx];
        addNodeToCanvas(
          found.name,
          found.category || found.category_name || "Custom processes & flows",
          found.unit || "kg",
          null,
          null,
          Array.isArray(found.inputs) ? found.inputs : [],
          Array.isArray(found.outputs) ? found.outputs : [],
          found.process_id || found.id
        );
        state.paletteProcesses.splice(foundIdx, 1);
        renderPaletteProcesses();
        if (state.canvasViewMode === "table") {
          renderCanvasTableView();
        }
      } else {
        addNodeToCanvas(param1, cat || "Polymers", unit || "kg");
      }
    },
    switchCanvasViewMode: (mode) => switchCanvasViewMode(mode),
    renderCanvasTableView: () => renderCanvasTableView(),
    exportLciTableToCsv: () => exportLciTableToCsv(),
    selectSpreadsheetCell: (el, r, c, v, m) => selectSpreadsheetCell(el, r, c, v, m),
    applyFormulaBarChange: (v) => applyFormulaBarChange(v),
    openConnectModal: () => openTableConnectModal(),
    openProcessEditor: (targetId) => openProcessEditor(targetId),
    tableUpdateAmount: (nodeId, type, idx, val, isInput) => tableUpdateAmount(nodeId, type, idx, val, isInput),
    tableUpdateFlowName: (nodeId, type, idx, val) => tableUpdateFlowName(nodeId, type, idx, val),
    tableUpdateUnit: (nodeId, type, idx, val) => tableUpdateUnit(nodeId, type, idx, val),
    tableUpdateProcessName: (nodeId, val) => tableUpdateProcessName(nodeId, val),
    tableDeleteFlow: (nodeId, type, idx) => tableDeleteFlow(nodeId, type, idx),
    tableAddFlow: (nodeId, type) => tableAddFlow(nodeId, type),
    tableUpdateEdgeAmount: (edgeId, val) => tableUpdateEdgeAmount(edgeId, val),
    tableDeleteEdge: (edgeId) => tableDeleteEdge(edgeId),
    toggleLeftPanel: (force) => toggleLeftPanel(force),
    toggleRightPanel: (force) => toggleRightPanel(force),
    toggleFullCanvas: () => toggleFullCanvas(),
    updateCanvasPanelLayout: () => updateCanvasPanelLayout(),
    applyCanvasZoom: (z, x, y) => applyCanvasZoom(z, x, y),
    getZoom: () => state.canvasZoom || 1.0,
    onLanguageChange: (lang) => {
      renderDashboardTable();
      renderDashboardKpis();
      renderChecklistTable();
      renderCommentsThread();
      renderReportProcessesTable();
      renderPaletteProcesses();
      renderCanvasStage();
      if (state.canvasViewMode === "table") {
        renderCanvasTableView();
      }
      updateCanvasHeaderToolbar();
      if (state.selectedNode) {
        inspectNode(state.selectedNode);
      }
      updateUserUI();
    }
  };

  // Arranque al cargar el DOM
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
  } else {
    initApp();
  }
})();
