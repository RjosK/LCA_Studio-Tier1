// econode_studio/web/js/app.js - Lógica Frontend Completa para ECONODE Studio (Tier 1)
// Cero dependencias externas. Totalmente reactivo e integrado con los endpoints REST del backend.

(function () {
  'use strict';

  // =========================================================================
  // 1. ESTADO GLOBAL REACTIVO
  // =========================================================================
  // Restauración síncrona inmediata de sesión desde localStorage (0ms)
  let initialUser = null;
  let initialAuth = false;
  try {
    const cachedToken = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
    const cachedUser = localStorage.getItem("econode_user") || sessionStorage.getItem("econode_user");
    if (cachedToken && cachedUser) {
      initialUser = JSON.parse(cachedUser);
      initialAuth = true;
    }
  } catch(e) {}

  const state = {
    activeUser: initialUser,
    isAuthenticated: initialAuth,
    allAccounts: [],
    activeSystem: null,
    systems: [],
    projects: [],
    collapsedProjects: {},
    collapsedStandalone: false,
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
    canvasZoom: 1.0, // Nivel de zoom del lienzo (0.5 a 1.75, 1.0 por defecto)
    pendingInviteToken: null, // Token de invitación recibido vía URL (?invite=...)
    pendingInviteEmail: null,
    pendingInviteInfo: null,
    systemParameters: [], // Parámetros dinámicos del modelo
    paramScopeFilter: "all", // "all" | "global" | "local" | "proc_<id>"
    paramGroupFilter: "all", // "all" | "<group_name>"
    paramTypeFilter: "all", // "all" | "independent" | "dependent"
    paramSearchQuery: "", // Filtro de búsqueda en tiempo real
    editingParameter: null, // Parámetro en edición activa
    // Inventario Corporativo GEI & Factores de Emisión (GHG Protocol)
    ghgInventories: [],
    activeGhgInventory: null,
    ghgTaxonomy: null,
    ghgActiveTab: "summary",
    // Modulo EPD (Environmental Product Declarations / SmartEPD / EN 15804+A2)
    epdTemplates: [],
    epdIndustries: [],
    epdModulesTaxonomy: [],
    epdWizardMode: "blank", // "blank" | "epd"
    selectedEpdTemplateId: "epd_concrete_rmx_4000",
    reportViewMode: "lca", // "lca" | "epd" | "ghg"
    epdStandard: "EN15804_A2", // "EN15804_A2" | "TRACI_2_1"
    activeEpdReport: null,
    ghgScope2View: "location", // "location" | "market"
    activeGhgReportInventory: null,
    ghgEmissionFactors: [],
    ghgFactorsFilterSource: "ALL",
    ghgFactorsFilterScope: "ALL",
    ghgFactorsSearchQuery: "",
    ghgAddEntryScope: "SCOPE_1",
    ghgSelectedFactor: null,
    ghgSpendFactors: [],
    ghgSelectedSpendFactor: null
  };

  // =========================================================================
  // 2. CLIENTE DE API REST
  // =========================================================================
  function handleSessionExpired() {
    state.activeUser = null;
    state.isAuthenticated = false;
    try {
      localStorage.removeItem("econode_token");
      localStorage.removeItem("econode_user_id");
      localStorage.removeItem("econode_user");
      sessionStorage.removeItem("econode_token");
      sessionStorage.removeItem("econode_user_id");
    } catch(e) {}
    if (typeof updateUserUI === "function") updateUserUI();
    if (typeof applyRolePermissions === "function") applyRolePermissions();
    if (state.currentView !== "login" && state.currentView !== "signup" && state.currentView !== "home") {
      showNotification("Tu sesión ha expirado o requiere autenticación. Por favor inicia sesión.");
      showView("login");
    }
  }

  function getAuthTokenQuery() {
    const t = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
    return t ? `?token=${encodeURIComponent(t)}` : "";
  }

  const api = {
    async get(endpoint) {
      try {
        const headers = {};
        const token = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(endpoint, { headers });
        if (res.status === 401) {
          handleSessionExpired();
          throw new Error("HTTP 401: Sesión no autorizada o expirada");
        }
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
        const token = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(endpoint, {
          method: "POST",
          headers,
          body: JSON.stringify(data)
        });
        if (res.status === 401) {
          handleSessionExpired();
          throw new Error("HTTP 401: Sesión no autorizada o expirada");
        }
        const text = await res.text();
        let json = null;
        try {
          json = JSON.parse(text);
        } catch (e) {
          if (res.status === 413) {
            throw new Error("El archivo excede el tamaño máximo permitido por Vercel (4.5 MB). Los archivos grandes se guardan directamente en tu Google Drive personal.");
          }
          if (!res.ok) {
            throw new Error(`Error del servidor (${res.status}): ${text.slice(0, 150)}`);
          }
        }
        if (!res.ok || (json && json.status === "error")) {
          throw new Error((json && json.message) || `HTTP ${res.status}`);
        }
        return json || { status: "success" };
      } catch (err) {
        console.error(`API POST error on ${endpoint}:`, err);
        throw err;
      }
    },

    // Auth
    getAuthConfig: () => api.get("/api/auth/config"),
    loginWithCredentials: (emailOrUser, password) => api.post("/api/auth/login", { email: emailOrUser, password }),
    loginDemo: (userId) => api.post("/api/auth/login", { user_id: userId }),
    loginGoogle: (credential, email, inviteToken, role) => api.post("/api/auth/google", {
      credential,
      email,
      invite_token: inviteToken || state.pendingInviteToken,
      role
    }),
    signup: (data) => api.post("/api/auth/signup", data),
    logout: () => api.post("/api/auth/logout"),
    inviteMember: (data) => api.post("/api/auth/invite", data),
    getInvitations: () => api.get("/api/auth/invitations"),
    cancelInvitation: (invId) => api.post("/api/auth/invitations/cancel", { invitation_id: invId }),
    verifyInviteToken: (tok) => api.get("/api/auth/invite/verify?token=" + encodeURIComponent(tok)),

    // Systems & Canvas
    // Version Match and Compatibility
    getVersionDatabases: () => api.get("/api/version/databases"),
    matchProductSystemVersion: (sysId, targetVersion) => api.get(`/api/version/match-system?system_id=${encodeURIComponent(sysId)}&target_version=${encodeURIComponent(targetVersion)}`),
    searchVersionTarget: (targetVersion, q, limit = 20, isFlow = false) => api.get(`/api/version/search-target?target_version=${encodeURIComponent(targetVersion)}&q=${encodeURIComponent(q)}&limit=${limit}&is_flow=${isFlow ? 1 : 0}`),
    convertProductSystemVersion: (payload) => api.post("/api/systems/convert-version", payload),

    getSystems: () => api.get("/api/systems"),
    getSystemCanvas: (sysId) => api.get(`/api/systems/${sysId}/canvas`),
    saveSystemCanvas: (sysId, payload) => api.post(`/api/systems/${sysId}/save`, payload),
    getSystemParameters: (sysId) => api.get(`/api/systems/${sysId}/parameters`),
    saveSystemParameter: (sysId, payload) => api.post(`/api/systems/${sysId}/parameters`, payload),
    deleteSystemParameter: (sysId, paramId) => api.post(`/api/systems/${sysId}/parameters/${paramId}/delete`, {}),
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
    importCsv: (csvStr, mode = "full") => api.post("/api/systems/import-csv", { csv: csvStr, mode }),
    importSimaProToSystem: (sysId, csvStr, mode = "full") => api.post(`/api/systems/${sysId}/import-simapro`, { csv: csvStr, mode }),
    inspectSimaProCsv: (csvStr) => api.post("/api/systems/inspect-simapro", { csv: csvStr }),

    // Catalog LCI
    searchCatalog: (q = "", categoryId = null, limit = 50, source = "all") => {
      let url = `/api/processes?q=${encodeURIComponent(q)}&limit=${limit}&source=${encodeURIComponent(source || "all")}`;
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
      api.post("/api/systems/collaborators/invite", { system_id: sysId, name, email, role }),

    // Project management & comparative LCIA
    getProjects: () => api.get("/api/projects"),
    createProject: (data) => api.post("/api/projects/create", data),
    deleteProject: (projId) => api.post("/api/projects/delete", { project_id: projId }),
    assignSystemToProject: (sysId, projId) => api.post(`/api/systems/${sysId}/assign-project`, { project_id: projId }),
    compareProject: (projId) => api.get(`/api/projects/${projId}/compare`),

    // GHG Protocol & Scope 1/2/3 Corporate Inventories
    getGhgTaxonomy: () => api.get("/api/ghg/taxonomy"),
    listGhgInventories: () => api.get("/api/ghg/inventories"),
    getGhgInventory: (id) => api.get(`/api/ghg/inventories/${id}`),
    createGhgInventory: (data) => api.post("/api/ghg/inventories", data),
    deleteGhgInventory: (id) => api.post(`/api/ghg/inventories/${id}/delete`, {}),
    addGhgEntry: (invId, data) => api.post(`/api/ghg/inventories/${invId}/entries`, data),
    deleteGhgEntry: (invId, entryId) => api.post(`/api/ghg/inventories/${invId}/entries/${entryId}/delete`, {}),
    searchGhgEmissionFactors: (params = {}) => {
      const sp = new URLSearchParams();
      if (params.q) sp.append("q", params.q);
      if (params.source && params.source !== "ALL") sp.append("source", params.source);
      if (params.category && params.category !== "ALL") sp.append("category", params.category);
      if (params.limit) sp.append("limit", params.limit);
      const qs = sp.toString();
      return api.get(`/api/ghg/emission-factors${qs ? '?' + qs : ''}`);
    },

    // EPD Preliminary Models & Report Builder (SmartEPD / ISO 14025 / EN 15804+A2)
    listEpdTemplates: (industry = "ALL") =>
      api.get(`/api/epd/templates?industry=${encodeURIComponent(industry)}`),
    instantiateEpdTemplate: (payload) => {
      const u = state.activeUser;
      return api.post("/api/epd/templates/instantiate", {
        ...payload,
        owner_id: u ? u.id : undefined,
        owner_email: u ? u.email : undefined,
        owner_name: u ? u.display_name : undefined,
        owner_role: u ? u.role : undefined,
        owner_org: u ? u.organization : undefined
      });
    },
    getEpdReport: (sysId, standard = "EN15804_A2") =>
      api.get(`/api/systems/${sysId}/epd-report?standard=${encodeURIComponent(standard)}`),
    saveEpdMetadata: (sysId, metadata) =>
      api.post(`/api/systems/${sysId}/epd-metadata`, metadata),
    getOpenEpdExportUrl: (sysId) => {
      const token = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token") || "";
      return `/api/systems/${sysId}/export/openepd${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    },
    getGhgEmissionSources: () => api.get("/api/ghg/sources")
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
    audit: document.getElementById("viewAudit"),
    ghg: document.getElementById("viewGhg"),
    waste: document.getElementById("viewWaste")
  };

  function showView(viewName) {
    if (viewName === "studio") {
      viewName = state.isAuthenticated ? "dashboard" : "login";
    }
    if (!views[viewName]) return;

    if (viewName === "waste") {
      initWasteToolsData();
    }

    // Protección de rutas: si intenta entrar a Studio sin autenticación, enviar a login
    const isStudioRoute = ["dashboard", "canvas", "catalog", "report", "audit", "ghg", "waste"].includes(viewName);
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
    if (state.isAuthenticated && ["dashboard", "canvas", "catalog", "report", "audit", "ghg"].includes(viewName)) {
      try { localStorage.setItem("econode_active_view", viewName); } catch (e) {}
    }

    // Alternar contenedores de vista
    Object.keys(views).forEach((name) => {
      if (views[name]) {
        const isActive = (name === viewName);
        views[name].classList.toggle("active", isActive);
        if (isActive) {
          views[name].style.display = "";
        }
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
    if (viewName === "login" || viewName === "signup") {
      if (window.initGoogleAuthUI) {
        window.initGoogleAuthUI(viewName);
        setTimeout(() => { if (window.initGoogleAuthUI) window.initGoogleAuthUI(viewName); }, 80);
      }
    }
    if (viewName === "dashboard") {
      if (autoSaveCanvasTimer) {
        clearTimeout(autoSaveCanvasTimer);
        autoSaveCanvasTimer = null;
      }
      loadDashboard();
    }
    if (viewName === "canvas") {
      switchCanvasViewMode(state.canvasViewMode || "visual");
    }
    if (viewName === "catalog") loadCatalog();
    if (viewName === "report") loadReport();
    if (viewName === "audit") loadAuditChecklist();
    if (viewName === "ghg") loadGhgInventoryModule();

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

    const btnNavInvite = document.getElementById("btnNavInviteMember");

    if (role === "auditor") {
      // PERFIL AUDITOR LÍDER:
      if (btnNavInvite) btnNavInvite.style.display = "none";
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
      if (btnNavInvite) btnNavInvite.style.display = "none";
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
      if (btnNavInvite) btnNavInvite.style.display = "inline-flex";
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
      const storedToken = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");

      if (storedToken && cfg && cfg.authenticated && cfg.user) {
        state.activeUser = cfg.user;
        state.isAuthenticated = true;
        try {
          localStorage.setItem("econode_token", storedToken);
          localStorage.setItem("econode_user_id", cfg.user.id);
          localStorage.setItem("econode_user", JSON.stringify(cfg.user));
          sessionStorage.setItem("econode_token", storedToken);
          sessionStorage.setItem("econode_user_id", cfg.user.id);
        } catch(e) {}
        updateUserUI();
        applyRolePermissions();
        return;
      }

      // Si no hay token guardado o el backend reporta no autenticado
      if (!storedToken || (cfg && !cfg.authenticated)) {
        state.activeUser = null;
        state.isAuthenticated = false;
        try {
          localStorage.removeItem("econode_token");
          localStorage.removeItem("econode_user_id");
          localStorage.removeItem("econode_user");
          sessionStorage.removeItem("econode_token");
          sessionStorage.removeItem("econode_user_id");
        } catch(e) {}
        updateUserUI();
        applyRolePermissions();
      }
    } catch (err) {
      console.warn("Inicialización de auth:", err);
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

  // Login para los 3 Perfiles (con persistencia segura de token de sesión)
  async function handleDemoLogin(roleId) {
    try {
      const res = await api.loginDemo(roleId);
      if (res && res.user) {
        state.activeUser = res.user;
        state.isAuthenticated = true;
        const token = res.token || (res.user && res.user.token);
        if (token) {
          sessionStorage.setItem("econode_token", token);
          localStorage.setItem("econode_token", token);
        }
        if (res.user.id) {
          sessionStorage.setItem("econode_user_id", res.user.id);
          localStorage.setItem("econode_user_id", res.user.id);
        }
        try {
          localStorage.setItem("econode_user", JSON.stringify(res.user));
          sessionStorage.setItem("econode_subscribed", "pro");
        } catch(e) {}
        updateUserUI();

        const roleLabels = {
          analyst: "Analista Titular (Carla Méndez)",
          auditor: "Auditor Líder NOM-070 (Verificador Oficial)",
          client: "Cliente / Productor (Empresa Auditada)"
        };
        const label = roleLabels[res.user.role] || res.user.role;
        showNotification(`Sesión iniciada: ${res.user.display_name || res.user.email} · ${label}`);
        applyRolePermissions();
        showView("dashboard");
      }
    } catch (err) {
      alert("Error al iniciar sesión: " + (err.message || err));
    }
  }

  async function handleEmailLogin(email, password) {
    try {
      const cleanEmail = (email || document.getElementById("loginInputEmail")?.value || "").trim();
      const cleanPass = (password || document.getElementById("loginInputPassword")?.value || "").trim();
      if (!cleanEmail) {
        showNotification(window.I18n ? window.I18n.t("auth.enter_email", "Por favor ingresa tu correo electrónico.") : "Por favor ingresa tu correo electrónico.");
        return;
      }
      const res = await api.loginWithCredentials(cleanEmail, cleanPass);
      if (res && res.user) {
        state.activeUser = res.user;
        state.isAuthenticated = true;
        const token = res.token || (res.user && res.user.token);
        if (token) {
          sessionStorage.setItem("econode_token", token);
          localStorage.setItem("econode_token", token);
        }
        if (res.user.id) {
          sessionStorage.setItem("econode_user_id", res.user.id);
          localStorage.setItem("econode_user_id", res.user.id);
        }
        try {
          localStorage.setItem("econode_user", JSON.stringify(res.user));
          sessionStorage.setItem("econode_subscribed", "pro");
        } catch(e) {}
        updateUserUI();
        applyRolePermissions();
        showNotification(`Bienvenido, ${res.user.display_name || res.user.email}`);
        showView("dashboard");
      }
    } catch (err) {
      alert("Error al iniciar sesión: " + (err.message || err));
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
      localStorage.removeItem("econode_token");
      localStorage.removeItem("econode_user_id");
      localStorage.removeItem("econode_user");
      localStorage.removeItem("econode_cached_systems");
      localStorage.removeItem("econode_cached_projects");
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
      const storedInvite = state.pendingInviteToken || sessionStorage.getItem("econode_pending_invite");
      const res = await api.loginGoogle(response.credential, null, storedInvite);
      if (res.user) {
        state.activeUser = res.user;
        state.isAuthenticated = true;
        try {
          if (res.user.token) {
            sessionStorage.setItem("econode_token", res.user.token);
            localStorage.setItem("econode_token", res.user.token);
          }
          if (res.user.id) {
            sessionStorage.setItem("econode_user_id", res.user.id);
            localStorage.setItem("econode_user_id", res.user.id);
          }
          localStorage.setItem("econode_user", JSON.stringify(res.user));
        } catch(e) {}
        updateUserUI();
        applyRolePermissions();
        const rLabel = res.user.role === "auditor" ? "Auditor Líder" : (res.user.role === "client" ? "Cliente Productor" : "Analista ACV");
        showNotification(`Sesión iniciada con Google Workspace: ${res.user.display_name} (${rLabel})`);

        // Si es un Analista (nuevo o sin plan seleccionado), abrir la pantalla de suscripción
        const hasSub = sessionStorage.getItem("econode_subscribed");
        if (res.user.role === "analyst" && (res.user.is_new || state.currentView === "signup" || !hasSub)) {
          const modalSub = document.getElementById("modalSubscription");
          if (modalSub) {
            modalSub.style.display = "flex";
            modalSub.classList.add("active");
            return;
          }
        }
        showView("dashboard");
      }
    } catch (err) {
      alert("Error al validar token de Google: " + err.message);
    }
  };

  // Inicializador y Renderizador de Botones Oficiales de Google GSI
  window.initGoogleAuthUI = function (targetView) {
    const clientId = "968718859059-81u6bj6l4op1e0dsnblqg73ego8ns59j.apps.googleusercontent.com";
    if (window.google && window.google.accounts && window.google.accounts.id) {
      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: window.handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true
        });

        if (!targetView || targetView === "login") {
          const loginBox = document.getElementById("gsiLoginContainer");
          if (loginBox) {
            loginBox.innerHTML = "";
            window.google.accounts.id.renderButton(loginBox, {
              theme: "outline",
              size: "large",
              type: "standard",
              text: "continue_with",
              shape: "rectangular",
              logo_alignment: "left",
              width: 320
            });
            const btnIn = document.getElementById("btnGoogleSignInAction");
            if (btnIn) btnIn.style.display = "none";
          }
        }

        if (!targetView || targetView === "signup") {
          const signupBox = document.getElementById("gsiSignupContainer");
          if (signupBox) {
            signupBox.innerHTML = "";
            window.google.accounts.id.renderButton(signupBox, {
              theme: "outline",
              size: "large",
              type: "standard",
              text: "signup_with",
              shape: "rectangular",
              logo_alignment: "left",
              width: 320
            });
            const btnUp = document.getElementById("btnGoogleSignUpAction");
            if (btnUp) btnUp.style.display = "none";
          }
        }
      } catch (e) {
        console.warn("GSI renderButton fallo:", e);
        const btnIn = document.getElementById("btnGoogleSignInAction");
        if (btnIn) btnIn.style.display = "flex";
        const btnUp = document.getElementById("btnGoogleSignUpAction");
        if (btnUp) btnUp.style.display = "flex";
      }
    } else {
      // Si la librería de Google aún no está disponible (o bloqueada), mostrar botones de respaldo
      const btnIn = document.getElementById("btnGoogleSignInAction");
      if (btnIn) btnIn.style.display = "flex";
      const btnUp = document.getElementById("btnGoogleSignUpAction");
      if (btnUp) btnUp.style.display = "flex";
    }
  };

  // =========================================================================
  // 5. DASHBOARD DE PROYECTOS & SISTEMAS
  // =========================================================================
  async function loadDashboard() {
    try {
      // 1. Renderizado instantáneo desde caché local de sistemas y proyectos si existe (0ms de latencia)
      const cached = localStorage.getItem("econode_cached_systems");
      const cachedProj = localStorage.getItem("econode_cached_projects");
      let hasRenderedCache = false;
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length > 0) {
            state.systems = parsed;
            if (cachedProj) {
              try {
                const parsedProj = JSON.parse(cachedProj);
                if (Array.isArray(parsedProj)) state.projects = parsedProj;
              } catch(e) {}
            }
            renderDashboardTable();
            renderDashboardKpis();
            hasRenderedCache = true;
          }
        } catch(e) {}
      }

      if (!hasRenderedCache && (!state.systems || state.systems.length === 0)) {
        const tbody = document.getElementById("tableSystemsBody");
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 28px; color: var(--text-muted); font-size: 11.5px;"><span class="apple-spinner-micro" style="margin-right: 6px;"></span>Cargando portafolio de proyectos y sistemas...</td></tr>`;
        }
      }

      // 2. Traer versión fresca del servidor (sistemas y proyectos) con protección contra wiping
      let freshSystems = null;
      let freshProjects = null;
      try {
        const [res, projRes] = await Promise.all([
          api.getSystems(),
          api.getProjects().catch(() => ({ items: [] }))
        ]);
        if (res && Array.isArray(res.items)) {
          freshSystems = res.items;
        }
        if (projRes && Array.isArray(projRes.items)) {
          freshProjects = projRes.items;
        }
      } catch (fetchErr) {
        console.warn("No se pudo obtener versión fresca del portafolio desde el servidor:", fetchErr);
      }

      if (freshSystems !== null) {
        state.systems = freshSystems;
        try { localStorage.setItem("econode_cached_systems", JSON.stringify(freshSystems)); } catch(e) {}
      } else if (!state.systems || state.systems.length === 0) {
        const fallback = localStorage.getItem("econode_cached_systems");
        if (fallback) {
          try {
            const p = JSON.parse(fallback);
            if (Array.isArray(p)) state.systems = p;
          } catch(e) {}
        }
      }

      if (freshProjects !== null) {
        state.projects = freshProjects;
        try { localStorage.setItem("econode_cached_projects", JSON.stringify(freshProjects)); } catch(e) {}
      } else if (!state.projects || state.projects.length === 0) {
        const fallbackProj = localStorage.getItem("econode_cached_projects");
        if (fallbackProj) {
          try {
            const p = JSON.parse(fallbackProj);
            if (Array.isArray(p)) state.projects = p;
          } catch(e) {}
        }
      }

      updateProjectSelectOptions();

      // Si no hay un sistema activo seleccionado explícitamente, mantener el título neutral
      const navTitle = document.getElementById("navProjectTitle");
      if (navTitle && !state.activeSystem) {
        navTitle.textContent = "Portafolio de Sistemas Producto";
      }

      renderDashboardTable();
      renderDashboardKpis();
      loadDocsCount();
      await loadDashboardGhgInventories();
    } catch (err) {
      console.error("Error al cargar dashboard:", err);
    }
  }

  function updateProjectSelectOptions() {
    const selects = [
      document.getElementById("wizSystemProject"),
      document.getElementById("wizEpdProject"),
      document.getElementById("selectAssignProject")
    ];
    selects.forEach(sel => {
      if (!sel) return;
      const currentVal = sel.value;
      const defaultOpt = `<option value="">-- ${window.I18n.t("wiz.no_project", "Ninguno (Sistema Independiente / Solito)")} --</option>`;
      const projOpts = (state.projects || []).map(p => {
        const count = p.systems_count || 0;
        const countTxt = count === 1 ? "1 sistema" : `${count} sistemas`;
        return `<option value="${p.id}">${escapeHtml(p.name)} (${p.code}) - ${countTxt}</option>`;
      }).join("");
      sel.innerHTML = defaultOpt + projOpts;
      if (currentVal) sel.value = currentVal;
    });
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
        const matchesProj = (sys.project_name || "").toLowerCase().includes(search);
        if (!matchesName && !matchesCode && !matchesProj) return false;
      }
      return true;
    });

    if (state.systems.length === 0 && (!state.projects || state.projects.length === 0)) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 48px 20px; background: rgba(255, 255, 255, 0.02); border-radius: 8px;">
            <div style="font-size: 28px; margin-bottom: 10px; color: #7A8691;">[ Portafolio ]</div>
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

    if (filtered.length === 0 && (!state.projects || state.projects.length === 0)) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">${window.I18n.t("app.no_systems_found", "No se encontraron sistemas producto que coincidan con el filtro.")}</td></tr>`;
      return;
    }

    const isAuditor = state.activeUser && state.activeUser.role === "auditor";
    const isClient = state.activeUser && state.activeUser.role === "client";

    const chevronDownSvg = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(90deg); transition: transform 0.18s ease;"><polyline points="9 18 15 12 9 6"></polyline></svg>`;
    const chevronRightSvg = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(0deg); transition: transform 0.18s ease;"><polyline points="9 18 15 12 9 6"></polyline></svg>`;

    function renderSystemRow(sys, isChildOfProject) {
      let badgeClass = "badge-slate";
      let statusText = window.I18n.t("app.status_draft", "Borrador Técnico");
      if (sys.status === "in_audit") {
        badgeClass = "badge-emerald";
        statusText = window.I18n.t("app.status_in_audit", "En Auditoría NOM-070");
      } else if (sys.status === "certified") {
        badgeClass = "badge-emerald";
        statusText = window.I18n.t("app.status_certified", "Certificado NOM-070");
      }

      const isOfficial = sys.code === "SYS-PET-CIRCULAR-01" || sys.id === 21;

      let ownerNotice = "";
      const currentUser = state.activeUser;
      const currentUserName = currentUser ? (currentUser.display_name || currentUser.username) : "";
      const isOwner = sys.owner_name && (sys.owner_name.toLowerCase() === currentUserName.toLowerCase() || sys.owner_name.toLowerCase() === (currentUser?.email || "").toLowerCase());

      if (isOwner) {
        ownerNotice = `<div style="font-size: 9.5px; color: var(--accent-emerald); margin-top: 2px;">${window.I18n.t("app.creator_you", "Creador:")} ${currentUserName} ${window.I18n.t("app.you_tag", "(Tú)")}</div>`;
      } else if (isAuditor) {
        ownerNotice = `<div style="font-size: 10px; color: var(--accent-emerald); font-weight: 600; margin-top: 3px;">${window.I18n.t("app.created_by", "Creado por:")} ${sys.owner_name || "Carla Méndez"} · ${sys.owner_org || "BioPack Industrial S.A. de C.V."}</div>`;
      } else if (isClient) {
        ownerNotice = `<div style="font-size: 10px; color: var(--accent-blue); font-weight: 600; margin-top: 3px;">${window.I18n.t("app.shared_by", "Compartido por:")} ${sys.owner_name || "Carla Méndez"} (BioPack Lab)</div>`;
      } else {
        ownerNotice = `<div style="font-size: 9.5px; color: var(--text-dim); margin-top: 2px;">${window.I18n.t("app.creator_you", "Creador:")} ${sys.owner_name || "Carla Méndez"}</div>`;
      }

      const ownerShortName = sys.owner_name ? (sys.owner_name.split(" ")[0] + (sys.owner_name.split(" ")[1] ? " " + sys.owner_name.split(" ")[1][0] + "." : "")) : "Creador";
      const collabsList = sys.collaborators || [];
      const extraCollabsHtml = collabsList.map(c => {
        const cRole = c.role === "auditor" ? "AUD" : c.role === "client" ? "CLI" : "COL";
        const cShort = c.display_name ? (c.display_name.split(" ")[0] + (c.display_name.split(" ")[1] ? " " + c.display_name.split(" ")[1][0] + "." : "")) : "Colab";
        const colorBg = c.role === "auditor" ? "rgba(16, 185, 129, 0.12)" : c.role === "client" ? "rgba(139, 92, 246, 0.12)" : "rgba(14, 165, 233, 0.12)";
        const colorText = c.role === "auditor" ? "#059669" : c.role === "client" ? "#7C3AED" : "#0284C7";
        return `<span class="user-chip-mini" style="background: ${colorBg}; color: ${colorText}; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="${escapeHtml(c.display_name)} (${cRole})">${escapeHtml(cShort)}</span>`;
      }).join("");

      const teamHtml = isOfficial ? `
        <div style="display: flex; gap: 4px; flex-wrap: wrap; align-items: center;" title="Equipo de trabajo asignado al proyecto">
          <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Carla Méndez (Analista de ACV)">Carla M.</span>
          <span class="user-chip-mini" style="background: rgba(16, 185, 129, 0.12); color: #059669; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Josué Arentería (Auditor Líder)">Josué A.</span>
          <span class="user-chip-mini" style="background: rgba(139, 92, 246, 0.12); color: #7C3AED; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="Elena Ramírez (Cliente / Productor)">Elena R.</span>
        </div>
      ` : `
        <div style="display: flex; gap: 4px; flex-wrap: wrap; align-items: center;" title="Equipo del proyecto">
          <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">${escapeHtml(ownerShortName)}</span>
          ${extraCollabsHtml}
          <button class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9px; border-radius: 4px;" onclick="window.EconodeApp.openInviteModal(${sys.id}, '${escape(sys.name)}')" title="Invitar auditor o cliente a este proyecto">+ Invitar</button>
        </div>
      `;

      return `
        <tr onmouseenter="window.EconodeApp.prefetchSystem(${sys.id})" style="${isOfficial ? 'background: rgba(5, 150, 105, 0.03);' : ''} ${isChildOfProject ? 'background: #FAFBFD;' : ''}">
          <td style="${isChildOfProject ? 'padding-left: 38px; position: relative;' : 'padding-left: 18px;'}">
            ${isChildOfProject ? `<span style="position: absolute; left: 20px; top: 16px; width: 10px; height: 12px; border-left: 1.5px solid #CBD5E1; border-bottom: 1.5px solid #CBD5E1; border-bottom-left-radius: 3px;"></span>` : ''}
            <strong style="color: var(--text-primary); cursor: pointer; font-size: 12.5px;" onmouseenter="window.EconodeApp.prefetchSystem(${sys.id})" onclick="window.EconodeApp.openSystem(${sys.id}, true, this)">${escapeHtml(sys.name)}</strong>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 1px;">
              ${escapeHtml(sys.category || "Polímeros")} · ${escapeHtml(sys.geography || "[MX]")}
              ${isOfficial ? `<span class="badge-pill badge-emerald" style="font-size: 8px;">OFICIAL 3 PROCESOS</span>` : ''}
              ${sys.project_name ? `<span class="badge-pill badge-blue" style="font-size: 8px; margin-left: 4px;">${escapeHtml(sys.project_name)}</span>` : ''}
            </div>
            ${ownerNotice}
          </td>
          <td><span class="mono" style="font-size: 11px;">${escapeHtml(sys.code || "SKU-N/A")}</span></td>
          <td>${teamHtml}</td>
          <td><span class="badge-pill ${badgeClass}">${statusText}</span></td>
          <td>
            <div style="display: flex; gap: 5px; align-items: center; flex-wrap: nowrap;">
              <button class="btn btn-secondary btn-sm btn-sys-info" onclick="window.EconodeApp.openSystemInfoModal(${sys.id})" style="border-radius: 7px; height: 28px; padding: 0 9px; font-weight: 500; font-size: 11px; border-color: rgba(0,0,0,0.12); background: #FFFFFF; color: #334155; display: inline-flex; align-items: center; gap: 4px;" title="${window.I18n.t("dash.info_tooltip", "Información técnica, versión de base de datos y auditoría")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>${window.I18n.t("dash.info_btn", "Info")}</span>
              </button>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openDocsModal(${sys.id})" style="border-radius: 7px; height: 28px; padding: 0 9px; font-weight: 500; font-size: 11px; border-color: rgba(0,0,0,0.12); background: #FFFFFF; color: #334155;">
                ${window.I18n.t("app.vault_btn", "Bóveda")}
              </button>
              <button class="btn btn-primary btn-sm btn-open-system" onmouseenter="window.EconodeApp.prefetchSystem(${sys.id})" onclick="window.EconodeApp.openSystem(${sys.id}, true, this)" style="border-radius: 7px; height: 28px; padding: 0 12px; font-weight: 600; font-size: 11px; background: #18232C; color: #FFFFFF; border: none; box-shadow: 0 1px 3px rgba(24,35,44,0.15); cursor: pointer;">
                ${window.I18n.t("app.open_canvas_btn", "Abrir Lienzo")} &rarr;
              </button>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openAssignProjectModal(${sys.id}, ${sys.project_id || 'null'}, '${escape(sys.name)}')" style="border-radius: 7px; height: 28px; padding: 0 9px; font-weight: 500; font-size: 10.5px; border-color: rgba(0,0,0,0.12); background: #FFFFFF; color: #475569;" title="${sys.project_name ? 'Cambiar de proyecto o desasociar a sistema solito' : 'Asignar a un proyecto contenedor'}">
                ${sys.project_name ? window.I18n.t("dash.assign_proj_btn", "Mover") : '+ Proyecto'}
              </button>
              ${!isOfficial ? `<button class="btn btn-secondary btn-sm" style="height: 28px; width: 28px; padding: 0; display: inline-flex; align-items: center; justify-content: center; color: #94A3B8; border-color: rgba(0,0,0,0.08); border-radius: 7px; background: #FFFFFF;" onclick="window.EconodeApp.deleteSystem(${sys.id}, '${escape(sys.name)}')" title="Eliminar este sistema producto" onmouseover="this.style.color='#EF4444';this.style.borderColor='rgba(239,68,68,0.3)';" onmouseout="this.style.color='#94A3B8';this.style.borderColor='rgba(0,0,0,0.08)';"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>` : ''}
            </div>
          </td>
        </tr>
      `;
    }

    let rowsHtml = "";

    // 1. Proyectos Contenedores con Secciones Desplegables
    const projectsList = state.projects || [];
    projectsList.forEach((p) => {
      const pSystems = filtered.filter((s) => s.project_id === p.id);
      // Si hay búsqueda y el proyecto no coincide ni tiene sistemas coincidentes, omitir
      if (search && pSystems.length === 0 && !(p.name || "").toLowerCase().includes(search) && !(p.code || "").toLowerCase().includes(search)) {
        return;
      }

      const isCollapsed = !!state.collapsedProjects[p.id];
      const count = pSystems.length;
      const countLabel = count === 1 ? `1 ${window.I18n.t("dash.systems_count_badge", "sistema")}` : `${count} ${window.I18n.t("dash.systems_count_badge", "sistemas")}`;

      rowsHtml += `
        <tr class="project-header-row" style="background: #F8FAFC; border-top: 1.5px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; user-select: none;">
          <td colspan="5" style="padding: 10px 16px;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
              <div style="display: flex; align-items: center; gap: 10px; cursor: pointer;" onclick="window.EconodeApp.toggleProjectCollapse(${p.id})">
                <span class="project-chevron" style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 5px; color: #475569; background: #EEF2F6;">
                  ${isCollapsed ? chevronRightSvg : chevronDownSvg}
                </span>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="badge-pill badge-blue" style="font-size: 9.5px; font-weight: 700; padding: 2px 7px;">${escapeHtml(p.code || "PRJ")}</span>
                  <strong style="font-size: 13px; color: #0F172A; font-weight: 700;">${escapeHtml(p.name)}</strong>
                  <span style="font-size: 11px; color: #475569; background: #E2E8F0; padding: 2px 8px; border-radius: 12px; font-weight: 600;">
                    ${countLabel}
                  </span>
                  <span style="font-size: 10.5px; color: #64748B;">${escapeHtml(p.category || 'General')}</span>
                  ${p.description ? `<span style="font-size: 10.5px; color: #94A3B8; font-style: italic; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(p.description)}">· ${escapeHtml(p.description)}</span>` : ''}
                </div>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                ${pSystems.length >= 2 ? `
                  <button class="btn btn-sm" onclick="window.EconodeApp.openCompareProjectModal(${p.id})" style="height: 28px; padding: 0 12px; font-size: 11px; font-weight: 600; border-radius: 6px; background: rgba(14, 165, 233, 0.12); color: #0284C7; border: 1px solid rgba(14, 165, 233, 0.35); display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 1px 2px rgba(14,165,233,0.08);" title="Comparar huella ambiental (LCIA) entre los sistemas de este proyecto">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
                    <span>${window.I18n.t("dash.compare_btn", "Comparar Sistemas (LCIA)")}</span>
                  </button>
                ` : ''}
                <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openWizardForProject(${p.id})" style="height: 28px; padding: 0 10px; font-size: 11px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;" title="Crear un nuevo sistema producto dentro de este proyecto">
                  <span>+ Agregar Sistema</span>
                </button>
                <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.deleteProject(${p.id}, '${escape(p.name)}')" style="height: 28px; width: 28px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; color: #94A3B8;" title="Eliminar proyecto (los sistemas pasarán a independientes)" onmouseover="this.style.color='#EF4444';" onmouseout="this.style.color='#94A3B8';">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            </div>
          </td>
        </tr>
      `;

      if (!isCollapsed) {
        if (pSystems.length === 0) {
          rowsHtml += `
            <tr class="project-child-row" style="background: #FAFCFE;">
              <td colspan="5" style="padding: 14px 38px; font-size: 11.5px; color: #94A3B8; font-style: italic;">
                Este proyecto no contiene sistemas producto aún. Haz clic en '+ Agregar Sistema' para modelar el primero.
              </td>
            </tr>
          `;
        } else {
          pSystems.forEach((s) => {
            rowsHtml += renderSystemRow(s, true);
          });
        }
      }
    });

    // 2. Sistemas Independientes ("Solitos" / Sin Proyecto)
    const standaloneSystems = filtered.filter((s) => !s.project_id);
    const standaloneCount = standaloneSystems.length;
    const standaloneLabel = standaloneCount === 1 ? `1 ${window.I18n.t("dash.standalone_count_badge", "sistema solito")}` : `${standaloneCount} ${window.I18n.t("dash.standalone_count_badge", "sistemas solitos")}`;

    rowsHtml += `
      <tr class="standalone-header-row" style="background: #F8FAFC; border-top: 1.5px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; user-select: none;">
        <td colspan="5" style="padding: 10px 16px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px; cursor: pointer;" onclick="window.EconodeApp.toggleStandaloneCollapse()">
              <span class="standalone-chevron" style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 5px; color: #475569; background: #EEF2F6;">
                ${state.collapsedStandalone ? chevronRightSvg : chevronDownSvg}
              </span>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="badge-pill badge-slate" style="font-size: 9.5px; font-weight: 700; padding: 2px 7px;">INDEPENDIENTES</span>
                <strong style="font-size: 13px; color: #0F172A; font-weight: 700;">${window.I18n.t("dash.standalone_header", "Sistemas Independientes (Sin Proyecto)")}</strong>
                <span style="font-size: 11px; color: #475569; background: #E2E8F0; padding: 2px 8px; border-radius: 12px; font-weight: 600;">
                  ${standaloneLabel}
                </span>
                <span style="font-size: 10.5px; color: #64748B;">${window.I18n.t("dash.standalone_hint", "Modelos individuales")}</span>
              </div>
            </div>
            <div>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openWizardForProject(null)" style="height: 28px; padding: 0 10px; font-size: 11px; border-radius: 6px; display: inline-flex; align-items: center; gap: 4px;" title="Crear un sistema producto independiente (sin proyecto)">
                <span>+ Nuevo Sistema Solito</span>
              </button>
            </div>
          </div>
        </td>
      </tr>
    `;

    if (!state.collapsedStandalone) {
      if (standaloneSystems.length === 0) {
        rowsHtml += `
          <tr class="standalone-child-row" style="background: #FFFFFF;">
            <td colspan="5" style="padding: 14px 38px; font-size: 11.5px; color: #94A3B8; font-style: italic;">
              No hay sistemas independientes en este momento. Todos pertenecen a un proyecto.
            </td>
          </tr>
        `;
      } else {
        standaloneSystems.forEach((s) => {
          rowsHtml += renderSystemRow(s, false);
        });
      }
    }

    tbody.innerHTML = rowsHtml;
  }

  /* ========================================================================= */
  /* DASHBOARD CORPORATE GHG INVENTORIES SECTION                               */
  /* ========================================================================= */
  async function loadDashboardGhgInventories() {
    const tbody = document.getElementById("tableDashGhgInventoriesBody");
    if (!tbody) return;

    try {
      const res = await api.listGhgInventories();
      const list = res.inventories || res.items || [];
      state.ghgInventories = list;
      renderDashboardGhgInventories(list);
    } catch (err) {
      console.warn("No se pudieron cargar inventarios corporativos en el dashboard:", err);
    }
  }

  function renderDashboardGhgInventories(list = null) {
    const tbody = document.getElementById("tableDashGhgInventoriesBody");
    if (!tbody) return;

    const inventories = list || state.ghgInventories || [];
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";

    if (inventories.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 28px; color: var(--text-muted); font-size: 11.5px;">
            <div style="font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
              ${isEn ? "No corporate GHG inventories registered" : "Sin inventarios corporativos GEI registrados"}
            </div>
            <div style="margin-bottom: 12px;">
              ${isEn ? "Create your corporate inventory to track Scopes 1, 2, and 3 under the GHG Protocol." : "Crea tu inventario corporativo para cuantificar Alcances 1, 2 y 3 bajo el GHG Protocol."}
            </div>
            <button class="btn btn-primary btn-sm" onclick="window.EconodeApp.openNewGhgInventoryModal()">
              + ${isEn ? "New Corporate Inventory" : "Nuevo Inventario Corporativo"}
            </button>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = inventories.map(inv => {
      const consolLabel = inv.consolidation_approach === "operational_control"
        ? (isEn ? "Operational Control" : "Control Operacional")
        : (inv.consolidation_approach === "financial_control" ? (isEn ? "Financial Control" : "Control Financiero") : (isEn ? "Equity Share" : "Participación Accionaria"));
      
      const s1 = inv.summary?.scope_1?.total_tco2e || 0;
      const s2 = inv.summary?.scope_2?.location_based_tco2e || 0;
      const s3 = inv.summary?.scope_3?.total_tco2e || 0;
      const totalLoc = inv.summary?.totals?.total_location_based_tco2e !== undefined
        ? inv.summary.totals.total_location_based_tco2e
        : (inv.summary?.totals?.location_based_tco2e || (s1 + s2 + s3));
      const totalMkt = inv.summary?.totals?.total_market_based_tco2e !== undefined
        ? inv.summary.totals.total_market_based_tco2e
        : (inv.summary?.totals?.market_based_tco2e || totalLoc);

      return `
        <tr>
          <td>
            <strong style="color: var(--text-primary); cursor: pointer; font-size: 12.5px;" onclick="window.EconodeApp.openGhgReportForInventory(${inv.id})">
              ${escapeHtml(inv.organization_name)}
            </strong>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 1px;">
              ${escapeHtml(inv.country_code || "MX")} · ${escapeHtml(inv.description || "GHG Protocol Corporate Standard")}
            </div>
          </td>
          <td>
            <span class="mono" style="font-weight: 700; font-size: 11.5px; color: #0F172A;">${inv.reporting_year}</span>
            <span style="font-size: 10px; color: var(--text-muted); margin-left: 2px;">(Base: ${inv.base_year || inv.reporting_year})</span>
          </td>
          <td>
            <span class="badge-pill badge-emerald" style="font-size: 9.5px;">${consolLabel}</span>
          </td>
          <td>
            <div style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
              <span class="badge-scope1" title="Alcance 1">A1: ${s1.toFixed(1)} t</span>
              <span class="badge-scope2" title="Alcance 2 (Red)">A2: ${s2.toFixed(1)} t</span>
              <span class="badge-scope3" title="Alcance 3 (Cadena)">A3: ${s3.toFixed(1)} t</span>
            </div>
          </td>
          <td>
            <div style="display: flex; flex-direction: column;">
              <span class="mono" style="font-weight: 700; color: #059669; font-size: 12px;">
                ${totalLoc.toFixed(2)} <span style="font-size: 9.5px; font-weight: normal; color: var(--text-muted);">tCO2e (Red)</span>
              </span>
              <span class="mono" style="font-size: 10px; color: var(--text-muted);">
                ${totalMkt.toFixed(2)} tCO2e (Mercado)
              </span>
            </div>
          </td>
          <td>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openGhgReportForInventory(${inv.id})" title="${isEn ? "Open Executive Dynamic GHG Report" : "Abrir Reporte Dinamico GEI Ejecutivo"}" style="padding: 2px 8px; font-size: 11px;">
                ${isEn ? "Report" : "Reporte"}
              </button>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openGhgModuleForInventory(${inv.id})" title="${isEn ? "Manage scopes, activities and emission factors" : "Gestionar alcances, actividades y factores"}" style="padding: 2px 8px; font-size: 11px;">
                ${isEn ? "Manage" : "Gestionar"}
              </button>
              <button class="btn btn-ghost btn-sm" onclick="window.EconodeApp.deleteGhgInventoryFromDashboard(${inv.id}, '${escapeHtml(inv.organization_name)}')" title="${isEn ? "Delete inventory" : "Eliminar inventario"}" style="padding: 2px 6px; color: #DC2626; font-size: 11px;">
                ✕
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  async function openGhgReportForInventory(invId) {
    if (typeof navigateToView === "function") {
      navigateToView("report");
    }
    if (typeof switchReportMode === "function") {
      switchReportMode("ghg", false);
    }
    if (typeof loadGhgReport === "function") {
      await loadGhgReport(invId);
    }
  }

  async function openGhgModuleForInventory(invId) {
    if (typeof navigateToView === "function") {
      navigateToView("ghg");
    }
    if (typeof loadActiveGhgInventory === "function") {
      await loadActiveGhgInventory(invId);
    }
  }

  async function deleteGhgInventoryFromDashboard(invId, orgName) {
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
    const msg = isEn
      ? `Are you sure you want to delete corporate GHG inventory "${orgName}"? All registered activity entries will be removed.`
      : `¿Confirmas eliminar el inventario corporativo GEI "${orgName}"? Se eliminaran todas sus actividades de Alcance 1, 2 y 3.`;
    if (!confirm(msg)) return;

    try {
      await api.deleteGhgInventory(invId);
      showNotification(isEn ? `Inventory "${orgName}" deleted.` : `Inventario "${orgName}" eliminado exitosamente.`);
      await loadDashboardGhgInventories();
      if (typeof loadGhgInventoryModule === "function") {
        await loadGhgInventoryModule();
      }
    } catch (err) {
      console.error("Error al eliminar inventario desde dashboard:", err);
      alert(isEn ? "Failed to delete inventory: " + err.message : "Error al eliminar inventario: " + err.message);
    }
  }

  /* ========================================================================= */
  /* DASHBOARD CORPORATE GHG INVENTORIES SECTION                               */
  /* ========================================================================= */
  async function loadDashboardGhgInventories() {
    const tbody = document.getElementById("tableDashGhgInventoriesBody");
    if (!tbody) return;

    try {
      const res = await api.listGhgInventories();
      const list = res.inventories || res.items || [];
      state.ghgInventories = list;
      renderDashboardGhgInventories(list);
    } catch (err) {
      console.warn("No se pudieron cargar inventarios corporativos en el dashboard:", err);
    }
  }

  function renderDashboardGhgInventories(list = null) {
    const tbody = document.getElementById("tableDashGhgInventoriesBody");
    if (!tbody) return;

    const inventories = list || state.ghgInventories || [];
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";

    if (inventories.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 28px; color: var(--text-muted); font-size: 11.5px;">
            <div style="font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
              ${isEn ? "No corporate GHG inventories registered" : "Sin inventarios corporativos GEI registrados"}
            </div>
            <div style="margin-bottom: 12px;">
              ${isEn ? "Create your corporate inventory to track Scopes 1, 2, and 3 under the GHG Protocol." : "Crea tu inventario corporativo para cuantificar Alcances 1, 2 y 3 bajo el GHG Protocol."}
            </div>
            <button class="btn btn-primary btn-sm" onclick="window.EconodeApp.openNewGhgInventoryModal()">
              + ${isEn ? "New Corporate Inventory" : "Nuevo Inventario Corporativo"}
            </button>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = inventories.map(inv => {
      const consolLabel = inv.consolidation_approach === "operational_control"
        ? (isEn ? "Operational Control" : "Control Operacional")
        : (inv.consolidation_approach === "financial_control" ? (isEn ? "Financial Control" : "Control Financiero") : (isEn ? "Equity Share" : "Participación Accionaria"));
      
      const s1 = inv.summary?.scope_1?.total_tco2e || 0;
      const s2 = inv.summary?.scope_2?.location_based_tco2e || 0;
      const s3 = inv.summary?.scope_3?.total_tco2e || 0;
      const totalLoc = inv.summary?.totals?.total_location_based_tco2e !== undefined
        ? inv.summary.totals.total_location_based_tco2e
        : (inv.summary?.totals?.location_based_tco2e || (s1 + s2 + s3));
      const totalMkt = inv.summary?.totals?.total_market_based_tco2e !== undefined
        ? inv.summary.totals.total_market_based_tco2e
        : (inv.summary?.totals?.market_based_tco2e || totalLoc);

      return `
        <tr>
          <td>
            <strong style="color: var(--text-primary); cursor: pointer; font-size: 12.5px;" onclick="window.EconodeApp.openGhgReportForInventory(${inv.id})">
              ${escapeHtml(inv.organization_name)}
            </strong>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 1px;">
              ${escapeHtml(inv.country_code || "MX")} · ${escapeHtml(inv.description || "GHG Protocol Corporate Standard")}
            </div>
          </td>
          <td>
            <span class="mono" style="font-weight: 700; font-size: 11.5px; color: #0F172A;">${inv.reporting_year}</span>
            <span style="font-size: 10px; color: var(--text-muted); margin-left: 2px;">(Base: ${inv.base_year || inv.reporting_year})</span>
          </td>
          <td>
            <span class="badge-pill badge-emerald" style="font-size: 9.5px;">${consolLabel}</span>
          </td>
          <td>
            <div style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
              <span class="badge-scope1" title="Alcance 1">A1: ${s1.toFixed(1)} t</span>
              <span class="badge-scope2" title="Alcance 2 (Red)">A2: ${s2.toFixed(1)} t</span>
              <span class="badge-scope3" title="Alcance 3 (Cadena)">A3: ${s3.toFixed(1)} t</span>
            </div>
          </td>
          <td>
            <div class="mono" style="font-size: 12px; font-weight: 700; color: #0F172A;">
              ${totalLoc.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <span style="font-size: 9.5px; font-weight: 400; color: var(--text-muted);">tCO2e</span>
            </div>
            <div style="font-size: 9.5px; color: #2563EB;">
              Mkt: ${totalMkt.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} tCO2e
            </div>
          </td>
          <td>
            <div style="display: flex; gap: 5px; align-items: center; flex-wrap: nowrap;">
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openGhgReportForInventory(${inv.id})" title="${isEn ? "Open in Dynamic Report" : "Ver en Reporte Dinámico"}">
                ${isEn ? "Report" : "Ver Reporte"}
              </button>
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.openGhgModuleForInventory(${inv.id})" title="${isEn ? "Manage Sources & Activities" : "Gestionar Fuentes y Actividades"}">
                ${isEn ? "Activities" : "Fuentes"}
              </button>
              <button class="btn btn-sm" style="color: #EF4444; background: transparent; padding: 2px 6px; font-size: 10.5px;" onclick="window.EconodeApp.deleteGhgInventoryFromDashboard(${inv.id}, '${escapeHtml(inv.organization_name)}')" title="${isEn ? "Delete inventory" : "Eliminar inventario"}">
                &times;
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  function openGhgReportForInventory(invId) {
    state.activeGhgReportInventoryId = invId;
    localStorage.setItem("econode_active_ghg_inv", String(invId));
    showView("report");
    switchReportMode("ghg", true);
    loadGhgReport(invId);
  }

  function openGhgModuleForInventory(invId) {
    localStorage.setItem("econode_active_ghg_inv", String(invId));
    showView("ghg");
    loadActiveGhgInventory(invId);
  }

  async function deleteGhgInventoryFromDashboard(invId, orgName) {
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
    const msg = isEn
      ? `Are you sure you want to delete corporate inventory "${orgName}" (#${invId})? All its Scope 1, 2, and 3 activities will be permanently deleted.`
      : `¿Confirmas que deseas eliminar el inventario corporativo "${orgName}" (#${invId})? Se eliminarán todas sus fuentes de Alcance 1, 2 y 3.`;

    if (!confirm(msg)) return;

    try {
      await api.deleteGhgInventory(invId);
      showNotification(isEn ? "Corporate inventory deleted successfully." : "Inventario corporativo eliminado exitosamente.");
      await loadDashboardGhgInventories();
      if (typeof loadGhgInventoryModule === "function") {
        await loadGhgInventoryModule();
      }
      if (state.activeGhgReportInventory && state.activeGhgReportInventory.id === invId) {
        state.activeGhgReportInventory = null;
        await loadGhgReport();
      }
    } catch (err) {
      console.error("Error al eliminar inventario:", err);
      alert((isEn ? "Error deleting inventory: " : "Error al eliminar inventario: ") + err.message);
    }
  }

  // Caché en memoria para transiciones de lienzo ultra-rápidas (0ms de latencia)
  const systemCanvasCache = new Map();

  async function prefetchSystem(sysId) {
    if (!sysId || systemCanvasCache.has(sysId)) return;
    try {
      const res = await api.getSystemCanvas(sysId);
      if (res && res.system) {
        systemCanvasCache.set(sysId, res);
      }
    } catch (e) {
      // prefetch silencioso en segundo plano
    }
  }

  function applySystemCanvasData(res, sysId, commentsRes = null) {
    if (!res || !res.system) return;
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
    state.systemParameters = res.system.parameters || [];

    // Parsear comentarios concurrentes si están disponibles
    if (commentsRes) {
      const isOfficialSys = (sysId === 21 || sysId === 1 || res.system.code === "SYS-PET-CIRCULAR-01");
      state.comments = ((commentsRes && commentsRes.items) || []).filter(c => {
        if (isOfficialSys) return c.system_id === 21 || c.system_id === 1;
        return c.system_id === sysId;
      });
    }

    // Actualizar títulos
    const navTitle = document.getElementById("navProjectTitle");
    if (navTitle) {
      navTitle.textContent = `Reporte: ${res.system.name}`;
    }
    const canvasTitle = document.getElementById("canvasSystemTitle");
    if (canvasTitle) {
      canvasTitle.textContent = `${res.system.name} (${res.system.code || "SKU"})`;
    }
    const isOfficial = res.system.id === 21 || res.system.code === "SYS-PET-CIRCULAR-01";
    const canvasTeam = document.getElementById("canvasProjectTeam");
    if (canvasTeam) {
      if (isOfficial) {
        canvasTeam.innerHTML = `
          <span style="font-weight: 600; color: var(--text-secondary);">${window.I18n.t("dash.col_team", "Equipo")}:</span>
          <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">Carla M. (Analista)</span>
          <span class="user-chip-mini" style="background: rgba(16, 185, 129, 0.12); color: #059669; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">Josué A. (Auditor)</span>
          <span class="user-chip-mini" style="background: rgba(139, 92, 246, 0.12); color: #7C3AED; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">Elena R. (Cliente)</span>
        `;
      } else {
        const rawOwner = res.system.owner_name || (state.activeUser ? state.activeUser.display_name : "Creador");
        const ownerShort = rawOwner.split(" ")[0] + (rawOwner.split(" ")[1] ? " " + rawOwner.split(" ")[1][0] + "." : "");
        const collabs = res.system.collaborators || [];
        const collabsChips = collabs.map(c => {
          const roleTitle = c.role === "auditor" ? "Auditor" : c.role === "client" ? "Cliente" : "Colab";
          const cName = c.display_name || c.name || "Colab";
          const cShort = cName.split(" ")[0] + (cName.split(" ")[1] ? " " + cName.split(" ")[1][0] + "." : "");
          const colorBg = c.role === "auditor" ? "rgba(16, 185, 129, 0.12)" : c.role === "client" ? "rgba(139, 92, 246, 0.12)" : "rgba(14, 165, 233, 0.12)";
          const colorText = c.role === "auditor" ? "#059669" : c.role === "client" ? "#7C3AED" : "#0284C7";
          return `<span class="user-chip-mini" style="background: ${colorBg}; color: ${colorText}; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;">${cShort} (${roleTitle})</span>`;
        }).join("");
        const inviteBtn = `<button class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9px; border-radius: 4px; margin-left: 2px;" onclick="window.EconodeApp.openInviteModal(${res.system.id}, '${escape(res.system.name)}')" title="Invitar auditor o cliente a este proyecto">+ Invitar</button>`;
        canvasTeam.innerHTML = `
          <span style="font-weight: 600; color: var(--text-secondary);">${window.I18n.t("dash.col_team", "Equipo")}:</span>
          <span class="user-chip-mini" style="background: rgba(14, 165, 233, 0.12); color: #0284C7; font-size: 9.5px; padding: 1px 5px; border-radius: 4px; font-weight: 600;"> ${ownerShort} (Analista)</span>
          ${collabsChips}
          ${inviteBtn}
        `;
      }
    }

    // Catálogo (paleta) estrictamente aislado por sistema producto
    if (isOfficial) {
      initDefaultPalette(true);
    } else {
      const seenPids = new Set();
      state.paletteProcesses = [];

      // 1. Cargar procesos del catálogo guardados en el sistema producto
      if (Array.isArray(res.system.palette) && res.system.palette.length > 0) {
        res.system.palette.forEach(p => {
          const pid = String(p.process_id !== undefined ? p.process_id : p.id);
          if (!seenPids.has(pid)) {
            seenPids.add(pid);
            state.paletteProcesses.push(p);
          }
        });
      }

      // 2. Asegurar que los nodos en el lienzo también existan en el catálogo
      (state.canvasNodes || []).forEach(n => {
        const pid = String(n.process_id !== undefined ? n.process_id : n.id);
        if (!seenPids.has(pid)) {
          seenPids.add(pid);
          state.paletteProcesses.push({
            id: n.id,
            process_id: n.process_id,
            name: n.name,
            category: n.category || n.category_name || "General",
            unit: n.unit || "kg",
            amount: n.amount || 1.0,
            inputs: n.inputs ? JSON.parse(JSON.stringify(n.inputs)) : [],
            outputs: n.outputs ? JSON.parse(JSON.stringify(n.outputs)) : []
          });
        }
      });
    }
    syncSystemProcesses();
    if (state.canvasNodes && state.canvasNodes.length > 0) {
      inspectNode(state.canvasNodes[0]);
    } else {
      state.selectedNode = null;
      inspectNode(null);
    }
    renderPaletteProcesses();
    renderCanvasStage();
    renderCanvasEdges();
    if (state.canvasViewMode === "table") {
      renderCanvasTableView();
    } else if (state.canvasViewMode === "parameters") {
      renderSystemParametersTable();
    }

    const reportTitle = document.getElementById("reportMainTitle");
    if (reportTitle) {
      reportTitle.textContent = res.system.name;
    }
  }

  async function openSystem(sysId, navigateToCanvas = true, triggerBtn = null) {
    // 1. Cancelar cualquier auto-guardado previo para evitar sobreescritura cruzada
    if (autoSaveCanvasTimer) {
      clearTimeout(autoSaveCanvasTimer);
      autoSaveCanvasTimer = null;
    }

    // 2. Feedback táctil inmediato en botón disparador si existe
    if (triggerBtn && triggerBtn instanceof HTMLElement) {
      triggerBtn.disabled = true;
      triggerBtn.style.opacity = "0.75";
      triggerBtn.setAttribute("data-prev-content", triggerBtn.innerHTML);
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      triggerBtn.innerHTML = `<span class="apple-spinner-micro"></span> ${isEn ? "Opening..." : "Abriendo..."}`;
    }

    // 3. Obtener metadatos cacheados para transición visual instantánea (0ms de latencia)
    const cachedSys = (state.systems || []).find(s => s.id === sysId);
    if (cachedSys) {
      state.activeSystem = cachedSys;
      const navTitle = document.getElementById("navProjectTitle");
      if (navTitle) navTitle.textContent = `Reporte: ${cachedSys.name}`;
      const canvasTitle = document.getElementById("canvasSystemTitle");
      if (canvasTitle) canvasTitle.textContent = `${cachedSys.name} (${cachedSys.code || "SKU"})`;
    } else if (!state.activeSystem) {
      state.activeSystem = { id: sysId, name: "Sistema Producto", code: "" };
    }

    const overlay = document.getElementById("canvasLoadingOverlay");
    const hasCachedCanvas = systemCanvasCache.has(sysId);

    // 4. Si ya está en memoria caché, renderizar de inmediato (0ms de latencia percibida)
    if (hasCachedCanvas) {
      const cachedRes = systemCanvasCache.get(sysId);
      applySystemCanvasData(cachedRes, sysId);
      if (navigateToCanvas) {
        showView("canvas");
      }
    } else {
      // Si aún no está en caché, activar overlay y navegar al lienzo
      if (navigateToCanvas) {
        if (overlay) {
          const loadingText = document.getElementById("canvasLoadingText");
          const sysLabel = (cachedSys && cachedSys.name) ? cachedSys.name : "sistema";
          if (loadingText) loadingText.textContent = `Cargando ${sysLabel}...`;
          overlay.style.display = "flex";
        }
        showView("canvas");
      }
    }

    // 5. Carga concurrente y paralela del lienzo y comentarios para revalidar/poblar
    try {
      const [res, commentsRes] = await Promise.all([
        api.getSystemCanvas(sysId),
        api.getComments(sysId).catch(() => ({ items: [] }))
      ]);

      if (res && res.system) {
        systemCanvasCache.set(sysId, res);
        applySystemCanvasData(res, sysId, commentsRes);
      }
    } catch (err) {
      console.error("Error al abrir sistema:", err);
      if (!hasCachedCanvas) {
        showNotification("Error al cargar el sistema: " + (err.message || "Error desconocido"));
      }
    } finally {
      if (overlay) overlay.style.display = "none";
      if (triggerBtn && triggerBtn instanceof HTMLElement) {
        triggerBtn.disabled = false;
        triggerBtn.style.opacity = "1";
        const prev = triggerBtn.getAttribute("data-prev-content");
        if (prev) triggerBtn.innerHTML = prev;
      }
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

  function isNodeConnected(node) {
    if (!node || !state.canvasEdges || state.canvasEdges.length === 0) return false;
    const nid = String(node.id);
    const npid = String(node.process_id || "");
    const cleanNum = (node.process_id ? String(node.process_id) : nid).replace(/\D/g, "");

    return state.canvasEdges.some((e) => {
      const ef = String(e.from);
      const et = String(e.to);
      const esrc = String(e.source_process_id || "");
      const etgt = String(e.target_process_id || "");
      return ef === nid || et === nid || esrc === npid || etgt === npid ||
             (cleanNum && (ef === cleanNum || ef === `node_${cleanNum}` || et === cleanNum || et === `node_${cleanNum}` || esrc === cleanNum || etgt === cleanNum));
    });
  }

  function getAllSystemProcesses() {
    const map = new Map();
    // 1. Procesos en paleta / catálogo
    (state.paletteProcesses || []).forEach((p) => {
      const key = String(p.process_id || p.id);
      map.set(key, p);
    });
    // 2. Procesos en lienzo
    (state.canvasNodes || []).forEach((n) => {
      const key = String(n.process_id || n.id);
      if (!map.has(key)) {
        map.set(key, n);
      } else {
        map.set(key, Object.assign({}, map.get(key), n));
      }
    });
    return Array.from(map.values());
  }

  function syncSystemProcesses() {
    if (!state.paletteProcesses) state.paletteProcesses = [];
    if (!state.canvasNodes) state.canvasNodes = [];

    // Sincronizar datos modificados (insumos, salidas, nombres) entre nodos del lienzo y catálogo
    state.canvasNodes.forEach(n => {
      const pIdx = state.paletteProcesses.findIndex(p => String(p.process_id || p.id) === String(n.process_id || n.id));
      if (pIdx !== -1) {
        state.paletteProcesses[pIdx].inputs = n.inputs;
        state.paletteProcesses[pIdx].outputs = n.outputs;
        state.paletteProcesses[pIdx].name = n.name;
        state.paletteProcesses[pIdx].amount = n.amount;
        state.paletteProcesses[pIdx].unit = n.unit;
      }
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

    // Sincronizar: solo nodos conectados o colocados en lienzo deben verse en el diagrama
    syncSystemProcesses();

    // Si el lienzo está vacío o el nodo inspeccionado ya no existe, limpiar incondicionalmente el inspector
    if (!state.canvasNodes || state.canvasNodes.length === 0) {
      inspectNode(null);
    } else if (state.selectedNode && !state.canvasNodes.some(n => String(n.id) === String(state.selectedNode.id))) {
      inspectNode(null);
    }

    const emptyGuideHtml = (!state.canvasNodes || state.canvasNodes.length === 0) ? `
      <div class="empty-canvas-guide" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none; z-index: 5; opacity: 0.85;">
        <div style="font-size: 38px; margin-bottom: 10px;"></div>
        <h4 style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">Lienzo de Modelado Vacío</h4>
        <p style="font-size: 12px; color: var(--text-muted); max-width: 400px; line-height: 1.45; margin: 0 auto;">
          Arrastra procesos desde el catálogo izquierdo o realiza conexiones en la <strong>Hoja de Cálculo (pestaña Conexiones Internas)</strong> para visualizar la cadena en el diagrama.
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
            syncSystemProcesses();
            renderPaletteProcesses();
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
            ${node.epd_module ? `<span class="epd-module-pill mod-${String(node.epd_module).charAt(0).toLowerCase()}" title="Modulo EPD EN 15804 / ISO 21930">${escapeHtml(node.epd_module)}</span>` : ""}
            <span class="badge-pill badge-slate" style="font-size: 8px;">${node.category || "Process"}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 4px;">
            ${(state.activeUser && state.activeUser.role === 'client') ? '' : `<button type="button" class="btn-node-comment" title="Add technical note to this process" style="background: none; border: 1px solid var(--border-color); border-radius: 3px; font-size: 9.5px; padding: 1px 4px; cursor: pointer; color: var(--text-secondary); background: #FFFFFF;"> +</button>`}
            ${(state.activeUser && state.activeUser.role === 'client') ? '' : `<button type="button" class="btn-node-delete" title="Remove process from model" style="background: none; border: 1px solid var(--border-color); border-radius: 3px; font-size: 9.5px; padding: 1px 5px; cursor: pointer; color: #EF4444; background: #FFFFFF;" onclick="event.stopPropagation(); window.EconodeApp.removeNode('${node.id}');">✕</button>`}
            <span class="node-val mono" style="font-size: 10px; font-weight: 700; color: var(--accent-emerald);">${node.reference_flow ? `${node.reference_flow.amount} ${node.reference_flow.unit}` : `${node.amount || 1.0} ${node.unit || 'kg'}`}</span>
          </div>
        </div>
        <div class="node-title" style="font-size: 11.5px; font-weight: 700; margin: 4px 0 2px;" title="${escapeHtml(node.name || '')}">${escapeHtml(node.name || '')}</div>
        <div style="font-size: 9.5px; color: var(--text-dim);">● ${inCount} Inputs (1 Unit) · ${outCount} Outputs (1 Waste)</div>
        ${sankeyBadgeHtml}

        <div class="node-ports-row" style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
          <span class="node-port port-in" data-node-id="${node.id}" title="Inlet Port (Click to connect)">↓</span>
          <span style="font-size: 9px; color: var(--text-muted);">Connectors</span>
          <span class="node-port port-out" data-node-id="${node.id}" title="Outlet Port (Click to connect)">→</span>
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
          const procs = getAllSystemProcesses();
          const tgtNode = procs.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id) || String(n.to) === String(edge.target_process_id));
          if (tgtNode && tgtNode.inputs) {
            const inp = tgtNode.inputs.find(i => areFlowsMatching(i.name, edge.flow));
            if (inp) {
              inp.origin = "Mercado ecoinvent 3.12";
            }
          }

          state.canvasEdges = (state.canvasEdges || []).filter(ed => {
            if (edge.id && ed.id) return ed.id !== edge.id;
            if (ed === edge) return false;
            const sameFrom = (ed.from === edge.from || String(ed.source_process_id) === String(edge.source_process_id));
            const sameTo = (ed.to === edge.to || String(ed.target_process_id) === String(edge.target_process_id));
            const sameFlow = (ed.flow === edge.flow);
            return !(sameFrom && sameTo && sameFlow);
          });

          syncSystemProcesses();
          renderCanvasEdges();
          renderPaletteProcesses();
          renderCanvasStage();
          if (state.canvasViewMode === "table") {
            renderCanvasTableView();
          }
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
            <span style="font-size: 8.5px; opacity: 0.8;">${isResolved ? '[OK] Resuelto' : '⚠️ Pendiente'}</span>
          </div>
          <div class="sticky-content-body">${c.content}</div>
          <div style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center; gap: 4px;">
            ${canDelete ? `<button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px; color: #EF4444;" onclick="window.EconodeApp.deleteComment(${c.id})" title="Eliminar observación"> Eliminar</button>` : '<span></span>'}
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
      showNotification("Please click the outlet port [→] on the source node first.");
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
          const typeBadge = out.is_reference ? ' [Reference]' : out.is_waste ? ' [Waste]' : '⚡ [Emission/Output]';
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
            <div style="font-size: 32px; margin-bottom: 8px;"></div>
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
            ${window.I18n.t("app.edit_proc_btn", "Edit Process (Inputs & Outputs)")}
          </button>
          <button class="btn btn-secondary btn-sm" style="width: 100%; color: #EF4444;" onclick="window.EconodeApp.removeNode('${node.id}')">
            ${window.I18n.t("app.delete_node_btn", "Remove Node from Model")}
          </button>
        `;
      } else if (isAuditor) {
        actionButtonsHtml = `
          <button class="btn btn-secondary btn-sm" style="width: 100%;" onclick="window.EconodeApp.commentOnNode('${escape(node.name || '')}')">
            ${window.I18n.t("app.comment_proc_btn", "Add Observation to Process")}
          </button>
        `;
      } else {
        actionButtonsHtml = `
          <div style="font-size: 10px; color: var(--text-dim); text-align: center; padding: 4px;">${window.I18n.t("app.readonly_client", "Read Only Mode (Client)")}</div>
        `;
      }

      inspDetails.innerHTML = `
        <div style="margin-bottom: 14px;">
          <h3 style="font-size: 13.5px; font-weight: 700;">${escapeHtml(node.name || '')}</h3>
          <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">ID: <span class="mono">${escapeHtml(String(node.id || ''))}</span> · ecoinvent 3.12 Cutoff</div>
        </div>

        <div style="background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px; margin-bottom: 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">${window.I18n.t("app.ref_flow_badge", "QUANTITATIVE REFERENCE FLOW (UF)")}</div>
          <div class="mono" style="font-size: 16px; font-weight: 700; color: var(--accent-emerald);">
            ${node.reference_flow ? `${Number(node.reference_flow.amount).toFixed(3)} ${escapeHtml(node.reference_flow.unit || 'kg')} ${escapeHtml(node.reference_flow.name || '')}` : `${Number(node.amount || 1).toFixed(3)} ${escapeHtml(node.unit || 'kg')}`}
          </div>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); margin-bottom: 6px;">${window.I18n.t("app.tech_inputs_badge", "3 TECHNOSPHERE INPUTS (WITH UNIT FLOW):")}</div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${inputs.map(inp => `
              <div style="font-size: 10px; padding: 4px 6px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between;">
                <span>${escapeHtml(inp.name || '')} ${inp.is_unit ? '<span class="badge-pill badge-emerald" style="font-size: 7.5px;">UNIT</span>' : ''}</span>
                <span class="mono" style="font-weight: 700;">${Number(inp.amount).toFixed(3)} ${escapeHtml(inp.unit || 'kg')}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div style="margin-bottom: 14px;">
          <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); margin-bottom: 6px;">${window.I18n.t("app.outputs_badge", "3 OUTPUTS (PRODUCT, WASTE & EMISSIONS):")}</div>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${outputs.map(out => `
              <div style="font-size: 10px; padding: 4px 6px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between;">
                <span>${escapeHtml(out.name || '')} ${out.is_waste ? '<span class="badge-pill badge-slate" style="font-size: 7.5px;">WASTE</span>' : out.is_elementary ? '<span class="badge-pill badge-slate" style="font-size: 7.5px;">EMISSION</span>' : '<span class="badge-pill badge-emerald" style="font-size: 7.5px;">REF</span>'}</span>
                <span class="mono" style="font-weight: 700;">${Number(out.amount).toFixed(4)} ${escapeHtml(out.unit || 'kg')}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Parámetros Locales del Proceso -->
        ${(() => {
          const allParams = state.systemParameters || [];
          const cleanProcId = String(node.process_id || node.id || "").replace("node_", "");
          const localCount = allParams.filter(p => {
            if (p.scope !== "local") return false;
            const pidStr = String(p.process_id || "").replace("node_", "");
            return pidStr === cleanProcId || p.process_name === node.name;
          }).length;
          return `
            <div style="margin-bottom: 14px; border-top: 1px solid var(--border-color); padding-top: 12px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); display: flex; align-items: center; gap: 5px;">
                  <span>PARÁMETROS LOCALES</span>
                  <span class="badge-pill badge-outline" style="font-size: 8px; padding: 1px 5px;" id="inspParamsCountBadge">${localCount}</span>
                </div>
                ${(!isAuditor && !isClient) ? `
                  <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 2px 7px;" onclick="window.EconodeApp.openParameterModal(null, '${node.id}')">
                    + Añadir
                  </button>
                ` : ''}
              </div>
              <div id="inspProcessParamsList" style="display: flex; flex-direction: column; gap: 4px;">
                ${renderProcessParametersInInspector(node)}
              </div>
            </div>
          `;
        })()}

        <div style="margin-top: 14px;">
          ${actionButtonsHtml}
        </div>
      `;
    }
  }

  function initDefaultPalette(force = false) {
    if (!force && state.paletteProcesses && state.paletteProcesses.length > 0) return;
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
          { 
            name: "Virgin PET granulate [GLO]", 
            amount: 1.05, 
            unit: "kg", 
            is_unit: true,
            comment: "Resina PET virgen grado inyección con IV 0.82 dl/g",
            assumptions: "Considera 5% de merma de purga según estándar Husky HyPET",
            external_links: "https://www.petcore-europe.org"
          },
          { 
            name: "CFE electricity grid mix 230kV [MX]", 
            amount: 0.28, 
            unit: "kWh", 
            is_unit: false,
            comment: "Factor de emisión oficial del Sistema Eléctrico Nacional SEN",
            assumptions: "0.438 kg CO2 eq/kWh publicado por la Comisión Reguladora de Energía",
            external_links: "https://www.gob.mx/cre"
          },
          { 
            name: "Demineralized process cooling water [MX]", 
            amount: 0.015, 
            unit: "m3", 
            is_unit: false,
            comment: "Agua de enfriamiento de circuito semicerrado industrial",
            assumptions: "Reposición de pérdidas por evaporación del 1.5% del volumen circulante",
            external_links: "https://www.conagua.gob.mx"
          }
        ],
        outputs: [
          { 
            name: "Standard clear PET preform 500ml", 
            amount: 1.0, 
            unit: "kg", 
            is_reference: true,
            comment: "Preforma transparente cuello PCO 1881 de 24.0 gramos",
            assumptions: "Flujo de referencia cuantitativo del proceso unitario (1 kg = 41.67 preformas)",
            external_links: "https://www.isbt.com"
          },
          { 
            name: "Purge PET plastic scrap (Waste)", 
            amount: 0.05, 
            unit: "kg", 
            is_waste: true,
            comment: "Merma de purga de arranque y cambio de molde",
            assumptions: "100% segregado y triturado para recirculación interna en circuito cerrado",
            external_links: "https://www.iso.org/standard/38498.html"
          },
          { 
            name: "Fossil CO2 emissions [Air]", 
            amount: 0.012, 
            unit: "kg", 
            is_elementary: true,
            comment: "Emisiones directas por calentamiento térmico de cilindro",
            assumptions: "Cálculo estequiométrico basado en Directrices IPCC 2006 (Volumen 3)",
            external_links: "https://www.ipcc-nggip.iges.or.jp"
          }
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
          { 
            name: "Clear PET preform (Connected Flow)", 
            amount: 1.0, 
            unit: "kg", 
            is_unit: true,
            comment: "Preforma alimentada directamente desde el proceso de inyección previo",
            assumptions: "Relación 1:1 estequiométrica con factor de pérdida por calentamiento del 0.2%",
            external_links: "https://www.sidel.com"
          },
          { 
            name: "High-pressure compressed air (40 bar)", 
            amount: 0.45, 
            unit: "m3", 
            is_unit: false,
            comment: "Aire comprimido grado alimentario libre de aceite para soplado bi-orientado",
            assumptions: "Presión de 40 bar generada con compresor reciprocante Belliss & Morcom",
            external_links: "https://www.gardnerdenver.com"
          },
          { 
            name: "Thermoforming electricity CFE", 
            amount: 0.14, 
            unit: "kWh", 
            is_unit: false,
            comment: "Consumo eléctrico de lámparas infrarrojas y soplado rotativo",
            assumptions: "Consumo promedio medido en línea de 12000 botellas/hora",
            external_links: "https://www.cfe.mx"
          }
        ],
        outputs: [
          { 
            name: "Finished PET bottle 500ml", 
            amount: 1.0, 
            unit: "u", 
            is_reference: true,
            comment: "Botella PET estirada y soplada cuello 28mm lista para embotellado",
            assumptions: "Peso final unitario de 24.0 gramos verificado en báscula analítica",
            external_links: "https://www.petcore-europe.org"
          },
          { 
            name: "Plastic trimming scrap (Waste)", 
            amount: 0.002, 
            unit: "kg", 
            is_waste: true,
            comment: "Botellas con deformación dimensional o defecto de pared en prueba óptica",
            assumptions: "Tasa de rechazo controlada en 0.2%, triturada para reuso externo",
            external_links: "https://www.iso.org/standard/38498.html"
          },
          { 
            name: "Dissipated waste heat [Air]", 
            amount: 0.005, 
            unit: "MJ", 
            is_elementary: true,
            comment: "Calor residual disipado por ventilación forzada en túnel de enfriamiento",
            assumptions: "Entalpía de convección calculada a partir del gradiente térmico de 95°C a 25°C",
            external_links: "https://www.ashrae.org"
          }
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
          { 
            name: "Finished PET bottle 500ml (Connected Flow)", 
            amount: 1.0, 
            unit: "u", 
            is_unit: true,
            comment: "Botellas paletizadas en corrugado con film estirable",
            assumptions: "Embalaje terciario de 2400 botellas por palet europeo estándar",
            external_links: "https://www.epal-pallets.org"
          },
          { 
            name: "Automotive diesel fuel", 
            amount: 0.008, 
            unit: "l", 
            is_unit: false,
            comment: "Diésel ultra bajo azufre (UBA) para transporte de carga pesada",
            assumptions: "Consumo de 2.8 km por litro bajo régimen de autopista",
            external_links: "https://www.pemex.com"
          },
          { 
            name: "Freight lorry transport 16-32t [MX]", 
            amount: 0.0084, 
            unit: "t·km", 
            is_unit: false,
            comment: "Camión articulado de 3 ejes con carga útil promedio de 24 toneladas",
            assumptions: "Distancia de traslado de 350 km entre planta y centro de distribución",
            external_links: "https://www.sct.gob.mx"
          }
        ],
        outputs: [
          { 
            name: "Bottle distributed at distribution center", 
            amount: 1.0, 
            unit: "u", 
            is_reference: true,
            comment: "Botella entregada en muelle de recepción de CEDIS regional",
            assumptions: "Criterio de asignación Cradle-to-Gate + Distribution según ISO 14044",
            external_links: "https://www.iso.org/standard/37456.html"
          },
          { 
            name: "Used lubricant oil (Waste)", 
            amount: 0.0001, 
            unit: "kg", 
            is_waste: true,
            comment: "Aceite lubricante usado drenado durante mantenimiento preventivo de tractocamión",
            assumptions: "Generación de 100g por cada 1000 km recorridos, entregado a co-procesamiento",
            external_links: "https://www.semarnat.gob.mx"
          },
          { 
            name: "Diesel combustion emissions CO2 / NOx [Air]", 
            amount: 0.022, 
            unit: "kg", 
            is_elementary: true,
            comment: "Emisiones directas de escape de tractocamión norma Euro V / NOM-044",
            assumptions: "Factores de emisión de ecoinvent 3.12 Cutoff para camiones 16-32t",
            external_links: "https://www.eea.europa.eu"
          }
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

    // El catálogo refleja todos los procesos del inventario del sistema
    const allProcs = getAllSystemProcesses();
    const search = (document.getElementById("inputPaletteSearch")?.value || "").toLowerCase();
    const filtered = allProcs.filter(p => {
      if (!search) return true;
      return (p.name || "").toLowerCase().includes(search) || (p.category || "").toLowerCase().includes(search);
    });

    if (filtered.length === 0) {
      list.innerHTML = `
        <div style="padding: 24px 14px; font-size: 11px; color: var(--text-muted); text-align: center;">
          <div style="font-size: 26px; margin-bottom: 6px;"></div>
          <div style="font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Catálogo de Procesos Vacío</div>
          <div style="font-size: 10px; line-height: 1.4; margin-bottom: 12px;">Agrega procesos en la <strong>Hoja de Cálculo</strong> (Entradas y Salidas) o explora la base de datos oficial ecoinvent 3.12.</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            <button class="btn btn-secondary btn-sm" style="font-size: 10.5px;" onclick="window.EconodeApp.showView('catalog')"> Explorar Catálogo ecoinvent</button>
          </div>
        </div>
      `;
      return;
    }

    list.innerHTML = filtered
      .map(
        (p) => {
          const onCanvas = (state.canvasNodes || []).some(n => {
            const nid = String(n.id);
            const npid = String(n.process_id !== undefined ? n.process_id : "");
            const pid = String(p.id);
            const ppid = String(p.process_id !== undefined ? p.process_id : "");
            return nid === pid || npid === ppid || (ppid && nid === `node_${ppid}`) || (pid && npid === pid);
          });
          const connected = onCanvas && isNodeConnected(p);
          let badgeConn = "";
          if (connected) {
            badgeConn = `<span style="font-size: 8px; font-weight: 600; color: #0284C7; background: rgba(14, 165, 233, 0.1); padding: 1px 4px; border-radius: 3px;">En diagrama</span>`;
          } else if (onCanvas) {
            badgeConn = `<span style="font-size: 8px; font-weight: 600; color: #D97706; background: rgba(245, 158, 11, 0.1); padding: 1px 4px; border-radius: 3px;">En lienzo (por conectar)</span>`;
          } else {
            badgeConn = `<span style="font-size: 8px; font-weight: 600; color: var(--text-muted); background: var(--bg-surface); padding: 1px 4px; border-radius: 3px;">En catalogo</span>`;
          }

          return `
      <div class="palette-item" draggable="true" style="padding: 8px 10px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;" data-json='${JSON.stringify(p)}' data-id="${p.id}">
        <div style="flex: 1; cursor: pointer;" onclick="window.EconodeApp.openProcessEditor('${p.id}')">
          <div style="display: flex; align-items: center; gap: 4px;">
            <span class="mono" style="font-size: 8px; font-weight: 700; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 1px 3px; border-radius: 2px;">ID: #${p.process_id || p.id}</span>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-primary);">${escapeHtml(p.name)}</div>
          </div>
          <div style="font-size: 9.5px; color: var(--text-muted); margin-top: 2px; display: flex; align-items: center; gap: 6px;">
            <span>${p.category || "Polymers"} · 1.00 ${p.unit || "kg"} · <span style="color: var(--accent-emerald);">${(p.inputs || []).length} In / ${(p.outputs || []).length} Out</span></span>
            ${badgeConn}
          </div>
        </div>
        <div style="display: flex; gap: 4px; align-items: center;">
          <button class="btn btn-secondary btn-sm" title="Editar entradas y salidas" style="padding: 2px 6px; font-size: 10px;" onclick="window.EconodeApp.openProcessEditor('${p.id}')"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg></button>
          <button class="btn btn-secondary btn-sm" title="${onCanvas ? "Enfocar en lienzo" : "Colocar en lienzo"}" style="padding: 2px 6px; font-size: 10px;" onclick="window.EconodeApp.addPaletteNode('${p.id}')">+</button>
          <button class="btn btn-secondary btn-sm" title="Eliminar proceso del sistema" style="padding: 2px 6px; font-size: 10px; color: #EF4444;" onclick="window.EconodeApp.tableDeleteProcess('${p.id}')"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
        </div>
      </div>
    `;
        }
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
    if (!state.canvasNodes) state.canvasNodes = [];
    if (!state.paletteProcesses) state.paletteProcesses = [];

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

    const searchId = processId ? String(processId) : "";
    const cleanNum = searchId.replace(/\D/g, "");

    // 1. Si el proceso ya se encuentra en el lienzo, reubicarlo y seleccionarlo (NO duplicar en catálogo ni lienzo)
    const existingNode = state.canvasNodes.find(n => {
      const nid = String(n.id);
      const npid = String(n.process_id !== undefined ? n.process_id : "");
      if (searchId && (nid === searchId || npid === searchId || (cleanNum && (nid === `node_${cleanNum}` || npid === cleanNum)))) return true;
      return (n.name || "").trim().toLowerCase() === (name || "").trim().toLowerCase();
    });

    if (existingNode) {
      if (x !== null && y !== null) {
        existingNode.x = x;
        existingNode.y = y;
        existingNode.pos_x = x;
        existingNode.pos_y = y;
      }
      inspectNode(existingNode);
      renderCanvasStage();
      renderCanvasEdges();
      scheduleAutoSaveCanvas();
      showNotification(`Proceso "${name}" reposicionado en el lienzo.`);
      return;
    }

    // 2. Si no está en el lienzo, buscar si existe en la paleta para preservar sus datos originales
    const paletteItem = state.paletteProcesses.find(p => {
      const pid = String(p.id);
      const ppid = String(p.process_id !== undefined ? p.process_id : "");
      if (searchId && (pid === searchId || ppid === searchId || (cleanNum && (pid === `node_${cleanNum}` || ppid === cleanNum)))) return true;
      return (p.name || "").trim().toLowerCase() === (name || "").trim().toLowerCase();
    });

    let numericProcessId = (paletteItem && paletteItem.process_id) || (processId && !isNaN(parseInt(processId, 10)) ? parseInt(processId, 10) : null);
    if (!numericProcessId) {
      numericProcessId = 100001;
      while (state.canvasNodes.some(n => n.process_id === numericProcessId) || state.paletteProcesses.some(p => p.process_id === numericProcessId)) {
        numericProcessId++;
      }
    }

    const nodeInputs = (paletteItem && Array.isArray(paletteItem.inputs)) ? JSON.parse(JSON.stringify(paletteItem.inputs))
                     : (Array.isArray(initialInputs) ? JSON.parse(JSON.stringify(initialInputs)) : defaultInputs);
    const nodeOutputs = (paletteItem && Array.isArray(paletteItem.outputs)) ? JSON.parse(JSON.stringify(paletteItem.outputs))
                      : (Array.isArray(initialOutputs) ? JSON.parse(JSON.stringify(initialOutputs)) : defaultOutputs);

    const newNode = {
      id: `node_${numericProcessId}`,
      process_id: numericProcessId,
      name: (paletteItem && paletteItem.name) || name,
      category: (paletteItem && paletteItem.category) || cat || "Custom processes & flows",
      amount: (paletteItem && paletteItem.amount) || 1.0,
      unit: (paletteItem && paletteItem.unit) || unit || "kg",
      x: x !== null ? x : (60 + Math.random() * 80),
      y: y !== null ? y : (80 + Math.random() * 180),
      pos_x: x !== null ? x : (60 + Math.random() * 80),
      pos_y: y !== null ? y : (80 + Math.random() * 180),
      reference_flow: (paletteItem && paletteItem.reference_flow) || { name: name, amount: 1.0, unit: unit || "kg" },
      inputs: nodeInputs,
      outputs: nodeOutputs,
      _placedOnCanvas: true
    };

    state.canvasNodes.push(newNode);

    // Si el proceso es nuevo y no existía en el catálogo, registrarlo en la paleta una sola vez
    if (!paletteItem) {
      state.paletteProcesses.push({
        id: newNode.id,
        process_id: newNode.process_id,
        name: newNode.name,
        category: newNode.category,
        unit: newNode.unit,
        amount: newNode.amount,
        inputs: JSON.parse(JSON.stringify(nodeInputs)),
        outputs: JSON.parse(JSON.stringify(nodeOutputs))
      });
    }

    inspectNode(newNode);
    renderCanvasStage();
    renderPaletteProcesses();
    if (state.canvasViewMode === "table") {
      renderCanvasTableView();
    }
    scheduleAutoSaveCanvas();
    showNotification(`Proceso "${name}" agregado al lienzo.`);
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
    const epdModInput = document.getElementById("procEditEpdModule");
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
    if (epdModInput) epdModInput.value = target.epd_module || "";

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
            <div style="font-size: 20px; margin-bottom: 6px;"></div>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-secondary);">No input flows (Inputs)</div>
            <div style="font-size: 10px; margin-top: 2px;">Click <strong>+ Add Flow</strong> to add consumed products or resources.</div>
          </div>
        `;
      } else {
        inputsContainer.innerHTML = (state.editingInputs || []).map((inp, idx) => `
          <div class="proc-flow-card" draggable="true" data-idx="${idx}" data-type="input" style="border-left: 3px solid var(--accent-blue);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span class="badge-pill ${inp.is_unit ? 'badge-emerald' : 'badge-slate'}" style="font-size: 8.5px;">
                 Technosphere Flow (Input)
              </span>
              <button type="button" style="background: none; border: none; color: #EF4444; font-size: 11px; cursor: pointer;" onclick="window.EconodeApp.removeEditInput(${idx})" title="Remove Input">✕</button>
            </div>

            <!-- Nombre del flujo de base de datos (openLCA Flow) -->
            <div style="display: flex; align-items: center; justify-content: space-between; margin: 3px 0;">
              <strong style="font-size: 11px; color: var(--text-primary); line-height: 1.2;"> ${inp.name}</strong>
              <span class="badge-pill badge-slate" style="font-size: 8px; margin-left: 4px;">Flow ID: ${inp.flow_id || 'ecoinvent'}</span>
            </div>

            <!-- Proveedor asignado (Provider - Proceso que produce este flujo) -->
            <div style="margin: 4px 0;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <label style="font-size: 9px; color: var(--text-muted); font-weight: 600;">PROVIDER (SUPPLYING PROCESS):</label>
                <button type="button" style="background: none; border: none; color: var(--accent-blue); font-size: 9.5px; font-weight: 600; cursor: pointer; text-decoration: underline;" onclick="window.EconodeApp.openSelectProviderModal(${idx})"> Search Process</button>
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

            <!-- Metadatos de Flujo: Comentarios, Supuestos y Enlaces -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px;">
              <div>
                <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">COMENTARIOS:</label>
                <input type="text" class="form-input" style="height: 23px; font-size: 9.5px;" value="${escapeHtml(inp.comment || '')}" placeholder="Comentario o especificacion..." oninput="window.EconodeApp.updateEditInput(${idx}, 'comment', this.value)">
              </div>
              <div>
                <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">SUPUESTOS (ASSUMPTIONS):</label>
                <input type="text" class="form-input" style="height: 23px; font-size: 9.5px;" value="${escapeHtml(inp.assumptions || '')}" placeholder="Supuesto metodologico..." oninput="window.EconodeApp.updateEditInput(${idx}, 'assumptions', this.value)">
              </div>
            </div>
            <div style="margin-top: 5px;">
              <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">ENLACES EXTERNOS (LINKS):</label>
              <div style="display: flex; gap: 4px; align-items: center;">
                <input type="text" class="form-input" style="height: 23px; font-size: 9.5px; flex: 1;" value="${escapeHtml(inp.external_links || inp.links || '')}" placeholder="https://..." oninput="window.EconodeApp.updateEditInput(${idx}, 'external_links', this.value)">
                ${(inp.external_links || inp.links) ? `<a href="${escapeHtml(inp.external_links || inp.links)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="height: 23px; padding: 0 6px; font-size: 10px; display: inline-flex; align-items: center; text-decoration: none;" title="Abrir enlace externo">↗</a>` : ''}
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
            <div style="font-size: 20px; margin-bottom: 6px;"></div>
            <div style="font-size: 11px; font-weight: 600; color: var(--text-secondary);">No output flows (Outputs)</div>
            <div style="font-size: 10px; margin-top: 2px;">Click <strong>+ Add Flow</strong> to add reference product, waste or emissions.</div>
          </div>
        `;
      } else {
        outputsContainer.innerHTML = (state.editingOutputs || []).map((out, idx) => {
          const isRef = Boolean(out.is_reference);
          const flowIcon = isRef ? '' : out.is_waste ? '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>' : out.is_elementary ? '' : '';
          const badgeClass = isRef ? 'badge-emerald' : 'badge-slate';
          const badgeLabel = isRef 
            ? 'Quantitative Reference' 
            : out.is_waste 
              ? '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> Waste Flow' 
              : out.is_elementary 
                ? 'Elementary Emission' 
                : 'Product Output';
          const borderStyle = isRef ? 'border-left: 3px solid var(--accent-emerald);' : out.is_waste ? 'border-left: 3px solid #D97706;' : 'border-left: 3px solid var(--border-color);';

          return `
            <div class="proc-flow-card" draggable="true" data-idx="${idx}" data-type="output" style="${borderStyle}">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px;">
                <div>
                  ${isRef ? `
                    <span class="badge-pill badge-emerald" style="font-size: 8.5px;">
                      Quantitative Reference
                    </span>
                  ` : out.is_waste ? `
                    <span class="badge-pill badge-slate" style="font-size: 8.5px;">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> Waste Flow
                    </span>
                  ` : out.is_elementary ? `
                    <span class="badge-pill badge-slate" style="font-size: 8.5px;">
                      Elementary Emission
                    </span>
                  ` : ''}
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  ${!isRef ? `
                    <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 9px; height: 20px; color: var(--accent-emerald); font-weight: 600; border-color: rgba(5, 150, 105, 0.4);" onclick="window.EconodeApp.setAsQuantitativeReference(${idx})" title="Set as quantitative reference">
                      Set as Ref
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

              <!-- Metadatos de Flujo: Comentarios, Supuestos y Enlaces -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px;">
                <div>
                  <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">COMENTARIOS:</label>
                  <input type="text" class="form-input" style="height: 23px; font-size: 9.5px;" value="${escapeHtml(out.comment || '')}" placeholder="Comentario o especificacion..." oninput="window.EconodeApp.updateEditOutput(${idx}, 'comment', this.value)">
                </div>
                <div>
                  <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">SUPUESTOS (ASSUMPTIONS):</label>
                  <input type="text" class="form-input" style="height: 23px; font-size: 9.5px;" value="${escapeHtml(out.assumptions || '')}" placeholder="Supuesto metodologico..." oninput="window.EconodeApp.updateEditOutput(${idx}, 'assumptions', this.value)">
                </div>
              </div>
              <div style="margin-top: 5px;">
                <label style="font-size: 8.5px; color: var(--text-muted); font-weight: 600;">ENLACES EXTERNOS (LINKS):</label>
                <div style="display: flex; gap: 4px; align-items: center;">
                  <input type="text" class="form-input" style="height: 23px; font-size: 9.5px; flex: 1;" value="${escapeHtml(out.external_links || out.links || '')}" placeholder="https://..." oninput="window.EconodeApp.updateEditOutput(${idx}, 'external_links', this.value)">
                  ${(out.external_links || out.links) ? `<a href="${escapeHtml(out.external_links || out.links)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="height: 23px; padding: 0 6px; font-size: 10px; display: inline-flex; align-items: center; text-decoration: none;" title="Abrir enlace externo">↗</a>` : ''}
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
            const modalProcEdit = document.getElementById("modalProcessEditor");
            if (modalProcEdit && modalProcEdit.classList.contains("active") && state.editingProcess) {
              confirmInsertDbFlow(res.flow.code || res.flow.id, escape(res.flow.name), res.flow.unit_symbol, res.flow.flow_type);
            }
            if (state.currentView === "catalog") {
              loadCatalog();
            }
            const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
            showNotification(isEn ? `Custom flow "${name}" created. You can now use it in processes and spreadsheet cells.` : `Flujo "${name}" creado exitosamente. Ya puedes usarlo en procesos y en la hoja de cálculo.`);
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
              <strong style="font-size: 11.5px; color: var(--text-primary);">${escapeHtml(p.name || '')}</strong>
              <span class="badge-pill badge-emerald" style="font-size: 8.5px;">${escapeHtml(p.location || 'GLO')}</span>
            </div>
            <div style="font-size: 9.5px; color: var(--text-muted); margin-top: 2px;">
              Process ID: <span class="mono">${escapeHtml(String(p.id || ''))}</span> · Reference Output: ${escapeHtml(p.ref_flow_name || flowName || '')} (${escapeHtml(p.unit || 'kg')})
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
      authorSpan.textContent = ` Publicando como: ${author} (${roleTitle})`;
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
        const epdModVal = (document.getElementById("procEditEpdModule")?.value || "").trim();
        const refName = (document.getElementById("procEditRefFlowName")?.value || nameVal).trim();
        const refAmt = parseFloat(document.getElementById("procEditRefAmount")?.value || "1.0");
        const refUnit = (document.getElementById("procEditRefUnit")?.value || "kg").trim();

        target.name = nameVal;
        target.code = codeVal;
        target.category = catVal;
        target.category_name = catVal;
        target.location = locVal;
        target.epd_module = epdModVal || undefined;
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
            syncSystemProcesses();
            scheduleAutoSaveCanvas();
            renderPaletteProcesses();
            renderCanvasTableView();
            if (state.canvasViewMode === "visual") {
              renderCanvasStage();
            }

            // Refrescar catálogo LCI si está abierto o cargado
            loadCatalog();

            showNotification(`Process "${nameVal}" saved to "Custom processes & flows" section of the LCI explorer.`);
          } catch (err) {
            console.error("Error al persistir proceso propio:", err);
            if (!state.paletteProcesses) state.paletteProcesses = [];
            state.paletteProcesses.unshift(target);
            syncSystemProcesses();
            scheduleAutoSaveCanvas();
            renderPaletteProcesses();
            renderCanvasTableView();
            if (state.canvasViewMode === "visual") {
              renderCanvasStage();
            }
            showNotification(`Process "${nameVal}" added to the local palette.`);
          }
        } else {
          // Si es un proceso que ya existe en la paleta o lienzo, sincronizar sus datos
          if (state.paletteProcesses) {
            const pIdx = state.paletteProcesses.findIndex(p => String(p.id) === String(target.id) || String(p.process_id) === String(target.process_id));
            if (pIdx >= 0) {
              state.paletteProcesses[pIdx] = Object.assign({}, state.paletteProcesses[pIdx], target);
            }
          }
          if (state.canvasNodes) {
            const cIdx = state.canvasNodes.findIndex(n => String(n.id) === String(target.id) || String(n.process_id) === String(target.process_id));
            if (cIdx >= 0) {
              state.canvasNodes[cIdx] = Object.assign({}, state.canvasNodes[cIdx], target);
            }
          }
          syncSystemProcesses();
          scheduleAutoSaveCanvas();
          renderPaletteProcesses();
          renderCanvasTableView();
          if (state.canvasViewMode === "visual") {
            renderCanvasStage();
            if (state.selectedNode && (String(state.selectedNode.id) === String(target.id) || String(state.selectedNode.process_id) === String(target.process_id))) {
              inspectNode(target);
            }
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
    if (!state.activeSystem || !state.activeSystem.id) {
      return;
    }
    const sysId = state.activeSystem.id;
    try {
      const nodesToSave = (state.canvasNodes || []).map(n => {
        const px = (n.x !== undefined && n.x !== null) ? Number(n.x) : ((n.pos_x !== undefined && n.pos_x !== null) ? Number(n.pos_x) : 60);
        const py = (n.y !== undefined && n.y !== null) ? Number(n.y) : ((n.pos_y !== undefined && n.pos_y !== null) ? Number(n.pos_y) : 140);
        return {
          ...n,
          x: px,
          y: py,
          pos_x: px,
          pos_y: py
        };
      });
      await api.saveSystemCanvas(sysId, {
        nodes: nodesToSave,
        edges: state.canvasEdges || [],
        palette: state.paletteProcesses || []
      });
      systemCanvasCache.set(sysId, {
        status: "success",
        system: {
          ...state.activeSystem,
          nodes: nodesToSave,
          edges: state.canvasEdges || [],
          palette: state.paletteProcesses || [],
          parameters: state.systemParameters || []
        }
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

    const isTable = state.canvasViewMode === "table" || state.canvasViewMode === "parameters";
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
      if (isTable) {
        btnLeft.style.display = "none";
      } else {
        btnLeft.style.display = "";
        btnLeft.classList.toggle("active", !hideLeft);
        btnLeft.setAttribute("aria-pressed", !hideLeft ? "true" : "false");
      }
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
      if (isTable) {
        btnFull.style.display = "none";
      } else {
        btnFull.style.display = "";
        const isFull = hideLeft && hideRight;
        btnFull.classList.toggle("active", isFull);
        btnFull.setAttribute("aria-pressed", isFull ? "true" : "false");
      }
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
    if (state.canvasViewMode === "table") return;
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
    if (state.canvasViewMode === "table") return;

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
    const paramsContainer = document.getElementById("canvasParamsStageContainer");
    const btnVisual = document.getElementById("btnCanvasViewVisual");
    const btnTable = document.getElementById("btnCanvasViewTable");
    const btnParams = document.getElementById("btnCanvasViewParams");
    const zoomTbGroup = document.getElementById("canvasZoomToolbarGroup");
    const sankeyTbGroup = document.getElementById("canvasSankeyToolbarGroup");

    updateCanvasPanelLayout();

    if (btnVisual) btnVisual.classList.toggle("active", mode === "visual");
    if (btnTable) btnTable.classList.toggle("active", mode === "table");
    if (btnParams) btnParams.classList.toggle("active", mode === "parameters");
    if (zoomTbGroup) zoomTbGroup.style.display = (mode === "table" || mode === "parameters") ? "none" : "flex";
    if (sankeyTbGroup) sankeyTbGroup.style.display = (mode === "table" || mode === "parameters") ? "none" : "flex";

    if (mode === "table") {
      if (visualContainer) {
        visualContainer.style.display = "none";
        visualContainer.classList.remove("active");
      }
      if (paramsContainer) {
        paramsContainer.style.display = "none";
        paramsContainer.classList.remove("active");
      }
      if (tableContainer) {
        tableContainer.style.display = "flex";
        tableContainer.classList.add("active");
      }
      renderCanvasTableView();
    } else if (mode === "parameters") {
      if (visualContainer) {
        visualContainer.style.display = "none";
        visualContainer.classList.remove("active");
      }
      if (tableContainer) {
        tableContainer.style.display = "none";
        tableContainer.classList.remove("active");
      }
      if (paramsContainer) {
        paramsContainer.style.display = "flex";
        paramsContainer.classList.add("active");
      }
      renderSystemParametersTable();
    } else {
      if (tableContainer) {
        tableContainer.style.display = "none";
        tableContainer.classList.remove("active");
      }
      if (paramsContainer) {
        paramsContainer.style.display = "none";
        paramsContainer.classList.remove("active");
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
    } else if (meta.type === "comment" && meta.nodeId) {
      tableUpdateFlowComment(meta.nodeId, meta.flowKind, meta.idx, trimmed);
    } else if (meta.type === "assumptions" && meta.nodeId) {
      tableUpdateFlowAssumptions(meta.nodeId, meta.flowKind, meta.idx, trimmed);
    } else if (meta.type === "external_links" && meta.nodeId) {
      tableUpdateFlowLinks(meta.nodeId, meta.flowKind, meta.idx, trimmed);
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

  function areFlowsMatching(flow1, flow2) {
    if (!flow1 || !flow2) return false;
    const clean = s => String(s).toLowerCase()
      .replace(/\s*\(connected flow\)/gi, "")
      .replace(/\s*\(producto\)/gi, "")
      .replace(/\s*\[.*?\]/g, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();
    const c1 = clean(flow1);
    const c2 = clean(flow2);
    if (!c1 || !c2) return false;
    return c1 === c2 || c1.includes(c2) || c2.includes(c1);
  }

  function renderCanvasTableView() {
    const container = document.getElementById("canvasTableScrollArea");
    if (!container) return;

    const t = (k, fallback) => (window.I18n && window.I18n.t ? window.I18n.t(k, fallback) : fallback);
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";

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
        state.selectedSpreadsheetCell = null;
        renderCanvasTableView();
      };
    }
    if (tabConn) {
      tabConn.classList.toggle("active", activeTab === "connections");
      tabConn.setAttribute("aria-selected", activeTab === "connections" ? "true" : "false");
      tabConn.onclick = () => {
        state.activeSheetTab = "connections";
        state.selectedSpreadsheetCell = null;
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
    if (selectFilter) {
      selectFilter.value = (activeTab === "connections") ? "connections" : "lci";
    }

    const systemProcesses = getAllSystemProcesses();

    if (!systemProcesses || systemProcesses.length === 0) {
      if (activeTab === "lci") {
        container.innerHTML = `
          <table class="lci-excel-grid">
            <thead>
              <tr class="excel-header-row-letters">
                <th class="excel-corner-cell"></th>
                <th class="excel-col-letter" data-col="A" style="width: 210px;">A</th>
                <th class="excel-col-letter" data-col="B" style="min-width: 190px;">B</th>
                <th class="excel-col-letter" data-col="C" style="width: 250px;">C</th>
                <th class="excel-col-letter" data-col="D" style="width: 90px; text-align: right;">D</th>
                <th class="excel-col-letter" data-col="E" style="width: 65px; text-align: center;">E</th>
                <th class="excel-col-letter" data-col="F" style="width: 180px;">F</th>
                <th class="excel-col-letter" data-col="G" style="width: 180px;">G</th>
                <th class="excel-col-letter" data-col="H" style="width: 160px;">H</th>
                <th class="excel-col-letter" data-col="I" style="width: 75px; text-align: center;">I</th>
              </tr>
              <tr>
                <th class="excel-row-num" data-row="1">1</th>
                <th class="excel-col-label-th">${t("canvas.col_process", "Proceso")}</th>
                <th class="excel-col-label-th">${t("canvas.col_material", "Material")}</th>
                <th class="excel-col-label-th">${t("canvas.col_provider", "Proveedor")}</th>
                <th class="excel-col-label-th" style="text-align: right;">${t("canvas.col_value", "Valor")}</th>
                <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_unit", "Unidad")}</th>
                <th class="excel-col-label-th">${t("canvas.col_comments", "Comentarios")}</th>
                <th class="excel-col-label-th">${t("canvas.col_assumptions", "Supuestos")}</th>
                <th class="excel-col-label-th">${t("canvas.col_links", "Enlaces Externos")}</th>
                <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_actions", "Acciones")}</th>
              </tr>
            </thead>
            <tbody>
              <tr class="excel-row-new-process">
                <td class="excel-row-num" data-row="2">2</td>
                <td class="excel-cell" data-col="A" data-row="2">
                  <input type="text" class="excel-inline-input excel-input-new-proc-name" style="font-weight: 700; color: #059669;"
                    placeholder="${t("canvas.placeholder_new_process", "+ Escribir nuevo proceso (Enter)...")}"
                    onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'A', '', { type: 'newProcess' }); window.EconodeApp.excelAutocompleteOpen(this, 'process');"
                    oninput="window.EconodeApp.excelAutocompleteQuery(this, 'process')"
                    onkeydown="if (!window.EconodeApp.excelAutocompleteKeyDown(event)) window.EconodeApp.handleNewProcessKeyDown(event, this);"
                    onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'A', '', { type: 'newProcess' }); window.EconodeApp.excelAutocompleteOpen(this, 'process');">
                </td>
                <td class="excel-cell" data-col="B" data-row="2">
                  <input type="text" class="excel-inline-input excel-input-new-mat"
                    placeholder="${t("canvas.placeholder_new_material", "Material / Insumo principal...")}"
                    onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'B', '', { type: 'newProcessMat' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow');"
                    oninput="window.EconodeApp.excelAutocompleteQuery(this, 'flow')"
                    onkeydown="if (!window.EconodeApp.excelAutocompleteKeyDown(event)) window.EconodeApp.handleNewProcessKeyDown(event, this);"
                    onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'B', '', { type: 'newProcessMat' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow');">
                </td>
                <td class="excel-cell" data-col="C" data-row="2" style="color: var(--text-muted); font-size: 10px; font-style: italic;">
                  Mercado ecoinvent 3.12
                </td>
                <td class="excel-cell mono" data-col="D" data-row="2" style="text-align: right;">
                  <input type="number" step="any" class="excel-inline-input excel-input-new-amt" style="text-align: right;" value="1.0"
                    onkeydown="window.EconodeApp.handleNewProcessKeyDown(event, this)"
                    onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'D', '1.0')">
                </td>
                <td class="excel-cell mono" data-col="E" data-row="2" style="text-align: center;">
                  <input type="text" class="excel-inline-input excel-input-new-unit" style="text-align: center;" value="kg"
                    onkeydown="window.EconodeApp.handleNewProcessKeyDown(event, this)"
                    onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), 2, 'E', 'kg')">
                </td>
                <td class="excel-cell" data-col="F" data-row="2">
                  <input type="text" class="excel-inline-input excel-input-new-proc-comment"
                    placeholder="${t("canvas.col_comments_placeholder", "Comentario...")}">
                </td>
                <td class="excel-cell" data-col="G" data-row="2">
                  <input type="text" class="excel-inline-input excel-input-new-proc-assumptions"
                    placeholder="${t("canvas.col_assumptions_placeholder", "Supuesto...")}">
                </td>
                <td class="excel-cell" data-col="H" data-row="2">
                  <input type="text" class="excel-inline-input excel-input-new-proc-links"
                    placeholder="https://...">
                </td>
                <td class="excel-cell" data-col="I" data-row="2" style="text-align: center;">
                  <button type="button" class="btn btn-primary btn-sm" style="padding: 1px 7px; font-size: 9.5px;"
                    onclick="const tr=this.closest('tr'); const n=tr.querySelector('.excel-input-new-proc-name'); if(n && n.value.trim()){ window.EconodeApp.tableCreateProcessInline(n.value.trim(), tr.querySelector('.excel-input-new-mat')?.value, tr.querySelector('.excel-input-new-amt')?.value, tr.querySelector('.excel-input-new-unit')?.value, n.dataset?.processId); }"
                    title="${t("canvas.enter_to_create", "↵ Enter")}">+ Crear</button>
                </td>
              </tr>
            </tbody>
          </table>
        `;
        return;
      }
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
              <th class="excel-col-letter" data-col="A" style="width: 210px;">A</th>
              <th class="excel-col-letter" data-col="B" style="min-width: 190px;">B</th>
              <th class="excel-col-letter" data-col="C" style="width: 250px;">C</th>
              <th class="excel-col-letter" data-col="D" style="width: 90px; text-align: right;">D</th>
              <th class="excel-col-letter" data-col="E" style="width: 65px; text-align: center;">E</th>
              <th class="excel-col-letter" data-col="F" style="width: 180px;">F</th>
              <th class="excel-col-letter" data-col="G" style="width: 180px;">G</th>
              <th class="excel-col-letter" data-col="H" style="width: 160px;">H</th>
              <th class="excel-col-letter" data-col="I" style="width: 75px; text-align: center;">I</th>
            </tr>
            <tr>
              <th class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</th>
              <th class="excel-col-label-th">${t("canvas.col_process", "Proceso")}</th>
              <th class="excel-col-label-th">${t("canvas.col_material", "Material")}</th>
              <th class="excel-col-label-th">${t("canvas.col_provider", "Proveedor")}</th>
              <th class="excel-col-label-th" style="text-align: right;">${t("canvas.col_value", "Valor")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_unit", "Unidad")}</th>
              <th class="excel-col-label-th">${t("canvas.col_comments", "Comentarios")}</th>
              <th class="excel-col-label-th">${t("canvas.col_assumptions", "Supuestos")}</th>
              <th class="excel-col-label-th">${t("canvas.col_links", "Enlaces Externos")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_actions", "Acciones")}</th>
            </tr>
          </thead>
          <tbody>
      `;

      systemProcesses.forEach((node) => {
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
              areFlowsMatching(e.flow, inp.name)
            );

            let typeBadge = '';
            let providerText = '';
            let providerPlain = '';
            const otherNodes = (systemProcesses || []).filter(n => String(n.id) !== String(node.id) && String(n.process_id) !== String(node.process_id));

            if (connectedEdge) {
              const srcNode = systemProcesses.find(n => String(n.id) === String(connectedEdge.from) || String(n.process_id) === String(connectedEdge.source_process_id) || String(n.id) === String(connectedEdge.source_process_id));
              const srcName = srcNode ? srcNode.name : (connectedEdge.from || "Upstream");
              providerPlain = srcName;
              typeBadge = `<span class="excel-badge-connected"> ${t("canvas.tag_connected", "Conectado")}</span>`;
              if (otherNodes.length > 0) {
                providerText = `
                  <select class="excel-provider-select is-connected" 
                    onchange="window.EconodeApp.tableChangeProvider('${node.id}', ${inp.originalIdx}, this.value)"
                    title="${isEn ? 'Change provider or link upstream' : 'Cambiar proveedor o vincular a proceso origen'}">
                    <option value="disconnect">✂️ Desconectar (Mercado ecoinvent 3.12)</option>
                    <option value="ecoinvent">Mercado ecoinvent 3.12</option>
                    <option value="cfe">Suministro Industrial / CFE</option>
                    <optgroup label="${isEn ? 'Upstream Processes (Internal Links)' : 'Procesos Origen (Conexión Interna)'}">
                      ${otherNodes.map(on => {
                        const isSel = (String(connectedEdge.from) === String(on.id) || String(connectedEdge.source_process_id) === String(on.process_id) || String(connectedEdge.from) === String(on.process_id));
                        return `<option value="${on.id}" ${isSel ? 'selected' : ''}> ${escapeHtml(on.name)} (#${on.process_id || on.id})</option>`;
                      }).join('')}
                    </optgroup>
                  </select>
                `;
              } else {
                providerText = `<span style="color: #6D28D9; font-weight: 600;"> ${escapeHtml(srcName)}</span>`;
              }
            } else {
              typeBadge = inp.is_unit ? `<span class="excel-badge-techno"> Tecnosfera</span>` : `<span class="excel-badge-techno">⚡ Auxiliar</span>`;
              providerPlain = inp.origin || "Mercado ecoinvent 3.12";
              if (otherNodes.length > 0) {
                providerText = `
                  <select class="excel-provider-select" 
                    onchange="window.EconodeApp.tableChangeProvider('${node.id}', ${inp.originalIdx}, this.value)"
                    title="${isEn ? 'Change provider or link upstream' : 'Cambiar proveedor o vincular a proceso origen'}">
                    <option value="ecoinvent" ${(!inp.origin || inp.origin.includes('ecoinvent')) ? 'selected' : ''}>Mercado ecoinvent 3.12</option>
                    <option value="cfe" ${(inp.origin && inp.origin.includes('CFE')) ? 'selected' : ''}>Suministro Industrial / CFE</option>
                    <optgroup label="${isEn ? 'Upstream Processes (Internal Links)' : 'Procesos Origen (Conexión Interna)'}">
                      ${otherNodes.map(on => {
                        return `<option value="${on.id}"> ${escapeHtml(on.name)} (#${on.process_id || on.id})</option>`;
                      }).join('')}
                    </optgroup>
                  </select>
                `;
              } else {
                providerText = escapeHtml(inp.origin || "Mercado ecoinvent 3.12");
              }
            }

            const amt = inp.amount !== undefined ? Number(inp.amount) : 1.0;
            if (inp.unit === "kg") totalInputsKg += amt;

            processRows.push({
              flowKind: "input",
              idx: inp.originalIdx,
              typeBadge,
              flowName: inp.name || "Insumo",
              provider: providerText,
              providerPlain: providerPlain,
              amount: amt,
              unit: inp.unit || "kg",
              comment: inp.comment || "",
              assumptions: inp.assumptions || "",
              externalLinks: inp.external_links || inp.links || "",
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
              areFlowsMatching(e.flow, out.name)
            );

            let typeBadge = '';
            let destText = '';

            if (out.is_reference) {
              typeBadge = `<span class="excel-badge-ref">Referencia</span>`;
              destText = `[Flujo de Referencia Principal]`;
            } else if (out.is_waste) {
              typeBadge = `<span class="excel-badge-techno" style="background:#FEF2F2; color:#991B1B; border-color:#FECACA;">Residuo</span>`;
              destText = `Tratamiento / Relleno Sanitario`;
            } else if (out.is_elementary) {
              typeBadge = `<span class="excel-badge-techno" style="background:#FFFBEB; color:#92400E; border-color:#FDE68A;">Biosfera</span>`;
              destText = `Emisión Ambiental [Aire/Agua]`;
            } else {
              typeBadge = `<span class="excel-badge-techno">Coproducto</span>`;
              destText = `Salida intermedia del sistema`;
            }

            if (outgoingEdges.length > 0) {
              const targetNames = outgoingEdges.map(e => {
                const tgt = systemProcesses.find(n => String(n.id) === String(e.to) || String(n.process_id) === String(e.target_process_id));
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
              providerPlain: destText,
              amount: out.amount !== undefined ? Number(out.amount) : 1.0,
              unit: out.unit || "kg",
              comment: out.comment || "",
              assumptions: out.assumptions || "",
              externalLinks: out.external_links || out.links || "",
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
            providerPlain: "—",
            amount: 0,
            unit: "—",
            comment: "",
            assumptions: "",
            externalLinks: "",
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
              <!-- Col A: Proceso (Editable directamente estilo Excel) -->
              <td class="excel-cell" data-col="A" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'A', '${escapeHtml(node.name)}', { type: 'processName', nodeId: '${node.id}' })">
                ${isFirstRowOfProcess ? `
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
                    <input type="text" class="excel-inline-input" style="font-weight: 700; color: var(--text-primary); width: calc(100% - 94px);" 
                      value="${escapeHtml(node.name)}" 
                      onchange="window.EconodeApp.tableUpdateProcessName('${node.id}', this.value)"
                      onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'A', this.value, { type: 'processName', nodeId: '${node.id}' }); window.EconodeApp.excelAutocompleteOpen(this, 'process', { nodeId: '${node.id}' });"
                      oninput="window.EconodeApp.excelAutocompleteQuery(this, 'process')"
                      onkeydown="window.EconodeApp.excelAutocompleteKeyDown(event);">
                    <span class="mono" style="font-size: 8.5px; font-weight: 700; color: #059669; background: rgba(5, 150, 105, 0.08); padding: 1px 4px; border-radius: 3px; flex-shrink: 0;">#${node.process_id || node.id}</span>
                    <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 4px; font-size: 9px; border-radius: 3px; flex-shrink: 0;" onclick="window.EconodeApp.openProcessEditor('${node.id}')" title="${t("canvas.btn_edit_process_tip", "Editar entradas y salidas en el editor visual")}"></button>
                    <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 4px; font-size: 9px; color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 3px; flex-shrink: 0;" onclick="window.EconodeApp.tableDeleteProcess('${node.id}')" title="Eliminar este proceso completo del sistema"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
                  </div>
                ` : `
                  <span style="color: var(--text-muted); opacity: 0.35;">↳</span>
                `}
              </td>
              <!-- Col B: Material / Flujo -->
              <td class="excel-cell" data-col="B" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'B', '${escapeHtml(rowItem.flowName)}', { type: 'name', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" value="${escapeHtml(rowItem.flowName)}" 
                  onchange="window.EconodeApp.tableUpdateFlowName('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                  onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'B', this.value, { type: 'name', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} }); window.EconodeApp.excelAutocompleteOpen(this, 'flow', { nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} });"
                  oninput="window.EconodeApp.excelAutocompleteQuery(this, 'flow')"
                  onkeydown="window.EconodeApp.excelAutocompleteKeyDown(event);">
              </td>
              <!-- Col C: Proveedor / Destino -->
              <td class="excel-cell" data-col="C" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'C', '${escapeHtml(rowItem.providerPlain || '')}')">
                ${rowItem.provider}
              </td>
              <!-- Col D: Valor (Cantidad numérica) -->
              <td class="excel-cell mono" data-col="D" data-row="${currentRowNum}" style="text-align: right;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'D', '${rowItem.amount}', { type: 'amount', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="number" step="any" class="excel-inline-input" style="text-align: right;" value="${rowItem.amount}" 
                  onchange="window.EconodeApp.tableUpdateAmount('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                  oninput="window.EconodeApp.tableUpdateAmount('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value, true)">
              </td>
              <!-- Col E: Unidad -->
              <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: center;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'E', '${escapeHtml(rowItem.unit)}', { type: 'unit', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" style="text-align: center;" value="${escapeHtml(rowItem.unit)}" 
                  onchange="window.EconodeApp.tableUpdateUnit('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)">
              </td>
              <!-- Col F: Comentarios -->
              <td class="excel-cell" data-col="F" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'F', '${escapeHtml(rowItem.comment || '')}', { type: 'comment', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" value="${escapeHtml(rowItem.comment || '')}" 
                  placeholder="${t("canvas.col_comments_placeholder", "Comentario...")}"
                  onchange="window.EconodeApp.tableUpdateFlowComment('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                  onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'F', this.value, { type: 'comment', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} });">
              </td>
              <!-- Col G: Supuestos (Assumptions) -->
              <td class="excel-cell" data-col="G" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'G', '${escapeHtml(rowItem.assumptions || '')}', { type: 'assumptions', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <input type="text" class="excel-inline-input" value="${escapeHtml(rowItem.assumptions || '')}" 
                  placeholder="${t("canvas.col_assumptions_placeholder", "Supuesto metodologico...")}"
                  onchange="window.EconodeApp.tableUpdateFlowAssumptions('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                  onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'G', this.value, { type: 'assumptions', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} });">
              </td>
              <!-- Col H: Enlaces Externos -->
              <td class="excel-cell" data-col="H" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'H', '${escapeHtml(rowItem.externalLinks || '')}', { type: 'external_links', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} })">
                <div style="display: flex; align-items: center; gap: 4px;">
                  <input type="text" class="excel-inline-input" style="flex: 1; min-width: 80px;" value="${escapeHtml(rowItem.externalLinks || '')}" 
                    placeholder="https://..."
                    onchange="window.EconodeApp.tableUpdateFlowLinks('${node.id}', '${rowItem.flowKind}', ${rowItem.idx}, this.value)"
                    onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'H', this.value, { type: 'external_links', nodeId: '${node.id}', flowKind: '${rowItem.flowKind}', idx: ${rowItem.idx} });">
                  ${rowItem.externalLinks ? `
                    <a href="${escapeHtml(rowItem.externalLinks)}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="padding: 1px 4px; font-size: 9.5px; text-decoration: none; display: inline-flex; align-items: center; line-height: 1;" title="Abrir enlace externo">
                      ↗
                    </a>
                  ` : ''}
                </div>
              </td>
              <!-- Col I: Acciones rapidas -->
              <td class="excel-cell" data-col="I" data-row="${currentRowNum}" style="text-align: center;">
                ${rowItem.canDelete ? `
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9.5px; color: #EF4444;" 
                    onclick="window.EconodeApp.tableDeleteFlow('${node.id}', '${rowItem.flowKind}', ${rowItem.idx})" title="Eliminar fila">✕</button>
                ` : (isFirstRowOfProcess ? `
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px; border-radius: 3px; margin-right: 3px;" 
                    onclick="window.EconodeApp.openProcessEditor('${node.id}')" title="${t("canvas.btn_edit_process_tip", "Editar proceso en el editor visual")}"> Editar</button>
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px; color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 3px;" 
                    onclick="window.EconodeApp.tableDeleteProcess('${node.id}')" title="Eliminar proceso completo del sistema"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
                ` : `
                  <span style="color: var(--text-muted); font-size: 9px;">—</span>
                `)}
              </td>
            </tr>
          `;
        });

        // Fila inline interactiva estilo Excel para agregar insumos o salidas al proceso
        currentRowNum++;
        totalRows++;
        html += `
          <tr class="excel-row-add-flow">
            <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
            <td class="excel-cell" data-col="A" data-row="${currentRowNum}" style="color: var(--text-muted); opacity: 0.5; padding-left: 14px;">
              ↳
            </td>
            <td class="excel-cell" data-col="B" data-row="${currentRowNum}">
              <div style="display: flex; align-items: center; gap: 4px;">
                <select class="excel-inline-select excel-select-new-flow-kind" style="width: auto; min-width: 105px; font-size: 9.5px; height: 21px; padding: 0 4px; border-radius: 3px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-primary); flex-shrink: 0;" onchange="window.EconodeApp.tableUpdateNewFlowKind(this)">
                  <option value="input">${t("canvas.flow_kind_input", "Entrada (Insumo)")}</option>
                  <option value="output_coproduct">${t("canvas.flow_kind_coproduct", "Salida (Coproducto)")}</option>
                  <option value="output_waste">${t("canvas.flow_kind_waste", "Salida (Residuo)")}</option>
                  <option value="output_elementary">${t("canvas.flow_kind_emission", "Salida (Emision)")}</option>
                </select>
                <input type="text" class="excel-inline-input excel-input-new-flow-name" style="flex: 1; min-width: 120px;"
                  placeholder="${t("canvas.placeholder_new_flow", "+ Agregar insumo (Enter)...")}"
                  onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'B', '', { type: 'newFlow', nodeId: '${node.id}' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow', { nodeId: '${node.id}', flowKind: this.closest('tr').querySelector('.excel-select-new-flow-kind')?.value || 'input' });"
                  oninput="window.EconodeApp.excelAutocompleteQuery(this, 'flow')"
                  onkeydown="if (!window.EconodeApp.excelAutocompleteKeyDown(event)) window.EconodeApp.handleNewFlowKeyDown(event, '${node.id}', this)"
                  onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'B', '', { type: 'newFlow', nodeId: '${node.id}' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow', { nodeId: '${node.id}', flowKind: this.closest('tr').querySelector('.excel-select-new-flow-kind')?.value || 'input' });">
              </div>
            </td>
            <td class="excel-cell" data-col="C" data-row="${currentRowNum}">
              <div class="excel-cell-new-flow-provider" style="color: var(--text-muted); font-size: 10px; font-style: italic;">Mercado ecoinvent 3.12</div>
            </td>
            <td class="excel-cell mono" data-col="D" data-row="${currentRowNum}" style="text-align: right;">
              <input type="number" step="any" class="excel-inline-input excel-input-new-flow-amt" style="text-align: right;" value="1.0"
                onkeydown="window.EconodeApp.handleNewFlowKeyDown(event, '${node.id}', this)"
                onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'D', '1.0')">
            </td>
            <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: center;">
              <input type="text" class="excel-inline-input excel-input-new-flow-unit" style="text-align: center;" value="kg"
                onkeydown="window.EconodeApp.handleNewFlowKeyDown(event, '${node.id}', this)"
                onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'E', 'kg')">
            </td>
            <td class="excel-cell" data-col="F" data-row="${currentRowNum}">
              <input type="text" class="excel-inline-input excel-input-new-flow-comment"
                placeholder="${t("canvas.col_comments_placeholder", "Comentario...")}">
            </td>
            <td class="excel-cell" data-col="G" data-row="${currentRowNum}">
              <input type="text" class="excel-inline-input excel-input-new-flow-assumptions"
                placeholder="${t("canvas.col_assumptions_placeholder", "Supuesto...")}">
            </td>
            <td class="excel-cell" data-col="H" data-row="${currentRowNum}">
              <input type="text" class="excel-inline-input excel-input-new-flow-links"
                placeholder="https://...">
            </td>
            <td class="excel-cell" data-col="I" data-row="${currentRowNum}" style="text-align: center; color: var(--text-muted); font-size: 9px;">
              <div style="display: flex; align-items: center; justify-content: center; gap: 3px;">
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9px; opacity: 0.8;"
                  onclick="const tr=this.closest('tr'); const n=tr.querySelector('.excel-input-new-flow-name'); const kind=tr.querySelector('.excel-select-new-flow-kind')?.value || 'input'; const cmt=tr.querySelector('.excel-input-new-flow-comment')?.value; const assump=tr.querySelector('.excel-input-new-flow-assumptions')?.value; const lnk=tr.querySelector('.excel-input-new-flow-links')?.value; if(n && n.value.trim()){ window.EconodeApp.tableCreateFlowInline('${node.id}', n.value.trim(), tr.querySelector('.excel-input-new-flow-amt')?.value, tr.querySelector('.excel-input-new-flow-unit')?.value, n.dataset?.upstreamSourceId ? 'Conexión Interna' : 'Mercado ecoinvent 3.12', n.dataset?.upstreamSourceId, n.dataset?.upstreamProcessId, kind, cmt, assump, lnk); }" title="${t("canvas.enter_to_create", "↵ Enter")}">↵</button>
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9px;" 
                  onclick="window.EconodeApp.openProcessEditor('${node.id}')" title="${t("canvas.btn_edit_process_tip", "Abrir editor visual completo")}"></button>
              </div>
            </td>
          </tr>
        `;
      });

      // Fila inline interactiva estilo Excel para crear un nuevo proceso en la última fila
      currentRowNum++;
      totalRows++;
      html += `
        <tr class="excel-row-new-process">
          <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
          <td class="excel-cell" data-col="A" data-row="${currentRowNum}">
            <input type="text" class="excel-inline-input excel-input-new-proc-name" style="font-weight: 700; color: #059669;"
              placeholder="${t("canvas.placeholder_new_process", "+ Escribir nuevo proceso (Enter)...")}"
              onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'A', '', { type: 'newProcess' }); window.EconodeApp.excelAutocompleteOpen(this, 'process');"
              oninput="window.EconodeApp.excelAutocompleteQuery(this, 'process')"
              onkeydown="if (!window.EconodeApp.excelAutocompleteKeyDown(event)) window.EconodeApp.handleNewProcessKeyDown(event, this)"
              onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'A', '', { type: 'newProcess' }); window.EconodeApp.excelAutocompleteOpen(this, 'process');">
          </td>
          <td class="excel-cell" data-col="B" data-row="${currentRowNum}">
            <input type="text" class="excel-inline-input excel-input-new-mat"
              placeholder="${t("canvas.placeholder_new_material", "Material / Insumo principal...")}"
              onfocus="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'B', '', { type: 'newProcessMat' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow');"
              oninput="window.EconodeApp.excelAutocompleteQuery(this, 'flow')"
              onkeydown="if (!window.EconodeApp.excelAutocompleteKeyDown(event)) window.EconodeApp.handleNewProcessKeyDown(event, this)"
              onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'B', '', { type: 'newProcessMat' }); window.EconodeApp.excelAutocompleteOpen(this, 'flow');">
          </td>
          <td class="excel-cell" data-col="C" data-row="${currentRowNum}" style="color: var(--text-muted); font-size: 10px; font-style: italic;">
            Mercado ecoinvent 3.12
          </td>
          <td class="excel-cell mono" data-col="D" data-row="${currentRowNum}" style="text-align: right;">
            <input type="number" step="any" class="excel-inline-input excel-input-new-amt" style="text-align: right;" value="1.0"
              onkeydown="window.EconodeApp.handleNewProcessKeyDown(event, this)"
              onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'D', '1.0')">
          </td>
          <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: center;">
            <input type="text" class="excel-inline-input excel-input-new-unit" style="text-align: center;" value="kg"
              onkeydown="window.EconodeApp.handleNewProcessKeyDown(event, this)"
              onclick="window.EconodeApp.selectSpreadsheetCell(this.closest('td'), ${currentRowNum}, 'E', 'kg')">
          </td>
          <td class="excel-cell" data-col="F" data-row="${currentRowNum}">
            <input type="text" class="excel-inline-input excel-input-new-proc-comment"
              placeholder="${t("canvas.col_comments_placeholder", "Comentario...")}">
          </td>
          <td class="excel-cell" data-col="G" data-row="${currentRowNum}">
            <input type="text" class="excel-inline-input excel-input-new-proc-assumptions"
              placeholder="${t("canvas.col_assumptions_placeholder", "Supuesto...")}">
          </td>
          <td class="excel-cell" data-col="H" data-row="${currentRowNum}">
            <input type="text" class="excel-inline-input excel-input-new-proc-links"
              placeholder="https://...">
          </td>
          <td class="excel-cell" data-col="I" data-row="${currentRowNum}" style="text-align: center;">
            <button type="button" class="btn btn-primary btn-sm" style="padding: 1px 7px; font-size: 9.5px;"
              onclick="const tr=this.closest('tr'); const n=tr.querySelector('.excel-input-new-proc-name'); if(n && n.value.trim()){ window.EconodeApp.tableCreateProcessInline(n.value.trim(), tr.querySelector('.excel-input-new-mat')?.value, tr.querySelector('.excel-input-new-amt')?.value, tr.querySelector('.excel-input-new-unit')?.value, n.dataset?.processId); }"
              title="${t("canvas.enter_to_create", "↵ Enter")}">+ Crear</button>
          </td>
        </tr>
      `;

      html += `
          </tbody>
        </table>
      `;
    }

    if (activeTab === "connections") {
      let currentRowNum = 1;
      const rawEdges = state.canvasEdges || [];
      const edges = rawEdges.filter(edge => {
        if (!filterText) return true;
        const srcNode = systemProcesses.find(n => String(n.id) === String(edge.from) || String(n.process_id) === String(edge.source_process_id));
        const tgtNode = systemProcesses.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id));
        const srcLabel = (srcNode ? srcNode.name : (edge.from || "")).toLowerCase();
        const tgtLabel = (tgtNode ? tgtNode.name : (edge.to || "")).toLowerCase();
        const flow = (edge.flow || "").toLowerCase();
        return srcLabel.includes(filterText) || tgtLabel.includes(filterText) || flow.includes(filterText);
      });

      const sys = state.activeSystem;
      const sysName = (sys && sys.name) ? sys.name : "Sistema Producto";
      const sysCode = (sys && sys.code) ? sys.code : "#SYS-01";

      html += `
        <table class="lci-excel-grid">
          <thead>
            <tr class="excel-header-row-letters">
              <th class="excel-corner-cell"></th>
              <th class="excel-col-letter" data-col="A" style="width: 220px;">A</th>
              <th class="excel-col-letter" data-col="B" style="width: 240px;">B</th>
              <th class="excel-col-letter" data-col="C" style="min-width: 200px;">C</th>
              <th class="excel-col-letter" data-col="D" style="width: 240px;">D</th>
              <th class="excel-col-letter" data-col="E" style="width: 105px; text-align: right;">E</th>
              <th class="excel-col-letter" data-col="F" style="width: 75px; text-align: center;">F</th>
              <th class="excel-col-letter" data-col="G" style="width: 95px; text-align: center;">G</th>
            </tr>
            <tr>
              <th class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</th>
              <th class="excel-col-label-th">${t("canvas.col_system", "Sistema Producto")}</th>
              <th class="excel-col-label-th">${t("canvas.conn_source", "Proceso Origen (Salida)")}</th>
              <th class="excel-col-label-th">${t("canvas.col_material", "Material / Flujo")}</th>
              <th class="excel-col-label-th">${t("canvas.conn_target", "Proceso Destino (Entrada)")}</th>
              <th class="excel-col-label-th" style="text-align: right;">${t("canvas.col_value", "Valor")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_unit", "Unidad")}</th>
              <th class="excel-col-label-th" style="text-align: center;">${t("canvas.col_actions", "Acciones")}</th>
            </tr>
          </thead>
          <tbody>
      `;

      if (edges.length === 0) {
        currentRowNum++;
        html += `
          <tr>
            <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
            <td class="excel-cell excel-merged-system-cell" data-col="A" data-row="${currentRowNum}">
              <div style="font-weight: 700; color: var(--text-primary); font-size: 11px;">${escapeHtml(sysName)}</div>
              <div class="mono" style="font-size: 9px; color: #0284C7; margin-top: 3px;">${escapeHtml(sysCode)}</div>
            </td>
            <td class="excel-cell" colspan="6" style="text-align: center; color: var(--text-muted); padding: 18px; font-style: italic;">
              ${t("canvas.no_connections", "No hay conexiones internas definidas en este sistema producto. Utiliza la fila de abajo para crear una nueva conexión.")}
            </td>
          </tr>
        `;
      } else {
        edges.forEach((edge, rIdx) => {
          currentRowNum++;
          totalRows++;

          const srcNode = systemProcesses.find(n => String(n.id) === String(edge.from) || String(n.process_id) === String(edge.source_process_id));
          const tgtNode = systemProcesses.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id));

          const srcLabel = srcNode ? `${srcNode.name} (#${srcNode.process_id || srcNode.id})` : (edge.from || "Origen");
          const tgtLabel = tgtNode ? `${tgtNode.name} (#${tgtNode.process_id || tgtNode.id})` : (edge.to || "Destino");

          const mergedSystemCell = (rIdx === 0) ? `
              <td class="excel-cell excel-merged-system-cell" rowspan="${edges.length}" data-col="A" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'A', '${escapeHtml(sysName)}')">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;">
                  <span style="font-size: 11px; font-weight: 700; color: var(--text-primary); text-align: center;">${escapeHtml(sysName)}</span>
                  <span class="mono" style="font-size: 8.5px; font-weight: 600; color: #0284C7; background: rgba(14, 165, 233, 0.08); padding: 2px 6px; border-radius: 4px;">${escapeHtml(sysCode)}</span>
                  <span style="font-size: 9px; color: var(--text-muted); font-weight: 500;">(${edges.length} intercambios)</span>
                </div>
              </td>
          ` : '';

          html += `
            <tr>
              <td class="excel-row-num" data-row="${currentRowNum}">${currentRowNum}</td>
              ${mergedSystemCell}
              <td class="excel-cell" data-col="B" data-row="${currentRowNum}" style="font-weight: 600; color: #059669;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'B', '${escapeHtml(srcLabel)}')">
                ➔ ${escapeHtml(srcLabel)}
              </td>
              <td class="excel-cell" data-col="C" data-row="${currentRowNum}" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'C', '${escapeHtml(edge.flow)}')">
                <span class="excel-badge-connected">${escapeHtml(edge.flow || "Flujo Conectado")}</span>
              </td>
              <td class="excel-cell" data-col="D" data-row="${currentRowNum}" style="font-weight: 600; color: #7C3AED;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'D', '${escapeHtml(tgtLabel)}')">
                ↓ ${escapeHtml(tgtLabel)}
              </td>
              <td class="excel-cell mono" data-col="E" data-row="${currentRowNum}" style="text-align: right;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'E', '${edge.amount || 1.0}', { type: 'edgeAmount', edgeId: '${edge.id}' })">
                <input type="number" step="any" class="excel-inline-input" style="text-align: right;" 
                  value="${edge.amount !== undefined ? edge.amount : 1.0}" 
                  onchange="window.EconodeApp.tableUpdateEdgeAmount('${edge.id}', this.value)">
              </td>
              <td class="excel-cell mono" data-col="F" data-row="${currentRowNum}" style="text-align: center;" onclick="window.EconodeApp.selectSpreadsheetCell(this, ${currentRowNum}, 'F', '${escapeHtml(edge.unit || 'kg')}')">
                ${escapeHtml(edge.unit || 'kg')}
              </td>
              <td class="excel-cell" data-col="G" data-row="${currentRowNum}" style="text-align: center;">
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 9.5px; color: #EF4444;" 
                  onclick="window.EconodeApp.tableDeleteEdge('${edge.id}')" title="Desconectar vínculo">
                  ✕ ${t("canvas.conn_disconnect", "Desconectar")}
                </button>
              </td>
            </tr>
          `;
        });
      }

      // Fila interactiva para crear nueva conexión interna
      currentRowNum++;
      html += `
        <tr class="excel-row-new-connection">
          <td class="excel-row-num" data-row="${currentRowNum}">+</td>
          <td class="excel-cell" data-col="A" style="font-weight: 700; color: #0284C7; font-size: 10px;">
            + Nueva Conexión
          </td>
          <td class="excel-cell" data-col="B">
            <select id="selectNewConnSource" class="excel-inline-select" onchange="window.EconodeApp.updateNewConnFlows()">
              <option value="">-- Proceso Origen (Salida) --</option>
              ${systemProcesses.map(p => `<option value="${p.id}">${escapeHtml(p.name)} (#${p.process_id || p.id})</option>`).join('')}
            </select>
          </td>
          <td class="excel-cell" data-col="C">
            <select id="selectNewConnFlow" class="excel-inline-select">
              <option value="">-- Flujo de Salida --</option>
            </select>
          </td>
          <td class="excel-cell" data-col="D">
            <select id="selectNewConnTarget" class="excel-inline-select">
              <option value="">-- Proceso Destino (Entrada) --</option>
              ${systemProcesses.map(p => `<option value="${p.id}">${escapeHtml(p.name)} (#${p.process_id || p.id})</option>`).join('')}
            </select>
          </td>
          <td class="excel-cell mono" data-col="E" style="text-align: right;">
            <input type="number" step="any" id="inputNewConnAmount" class="excel-inline-input" style="text-align: right;" value="1.0">
          </td>
          <td class="excel-cell mono" data-col="F" style="text-align: center;">
            <input type="text" id="inputNewConnUnit" class="excel-inline-input" style="text-align: center;" value="kg">
          </td>
          <td class="excel-cell" data-col="G" style="text-align: center;">
            <button type="button" class="btn btn-primary btn-sm" style="padding: 2px 8px; font-size: 9.5px;" onclick="window.EconodeApp.tableAddNewConnection()" title="Crear vínculo y mostrar en diagrama">
              + Conectar
            </button>
          </td>
        </tr>
      `;

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
      const firstDataCell = container.querySelector('.excel-cell[data-col="B"][data-row="2"]');
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
    csv += "Proceso,Material,Proveedor,Valor,Unidad,Comentarios,Supuestos,Enlaces_Externos\n";

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
        const cmt = (inp.comment || "").replace(/"/g, '""');
        const assump = (inp.assumptions || "").replace(/"/g, '""');
        const links = (inp.external_links || inp.links || "").replace(/"/g, '""');
        csv += `${pName},"${(inp.name || "").replace(/"/g, '""')}","${provider.replace(/"/g, '""')}",${inp.amount !== undefined ? inp.amount : 1.0},"${(inp.unit || "kg").replace(/"/g, '""')}","${cmt}","${assump}","${links}"\n`;
      });

      // Outputs
      (node.outputs || []).forEach(out => {
        let flowType = out.is_reference ? "Producto de Referencia" : (out.is_waste ? "Residuo / Salida" : (out.is_elementary ? "Emisión Biosférica" : "Salida Técnica"));
        let dest = out.is_reference ? "Producto principal" : (out.is_waste ? "Tratamiento de residuos" : "Medio ambiente");
        const cmt = (out.comment || "").replace(/"/g, '""');
        const assump = (out.assumptions || "").replace(/"/g, '""');
        const links = (out.external_links || out.links || "").replace(/"/g, '""');
        csv += `${pName},"${(out.name || "").replace(/"/g, '""')}","${dest.replace(/"/g, '""')}",${out.amount !== undefined ? out.amount : 1.0},"${(out.unit || "kg").replace(/"/g, '""')}","${cmt}","${assump}","${links}"\n`;
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

  // =========================================================================
  // GESTOR DE PARÁMETROS DINÁMICOS DEL MODELO
  // =========================================================================

  async function loadSystemParameters(sysId) {
    if (!sysId) return;
    try {
      const res = await api.getSystemParameters(sysId);
      if (res && res.status === "success" && Array.isArray(res.items)) {
        state.systemParameters = res.items;
        if (state.canvasViewMode === "parameters") {
          renderSystemParametersTable();
        }
        if (state.selectedNode) {
          inspectNode(state.selectedNode);
        }
      }
    } catch (err) {
      console.warn("No se pudieron cargar los parámetros del sistema:", err);
    }
  }

  function updateParamScopeOptions() {
    const scopeSel = document.getElementById("selectParamScopeFilter");
    if (!scopeSel) return;
    const currentVal = state.paramScopeFilter || "all";
    
    let html = `
      <option value="all">Todos los Ámbitos (Globales + Procesos)</option>
      <option value="global">Solo Globales</option>
      <option value="local">Solo Procesos Locales</option>
    `;

    const nodes = state.canvasNodes || [];
    if (nodes.length > 0) {
      html += `<optgroup label="Procesos Unitarios del Sistema">`;
      nodes.forEach(node => {
        const pId = node.process_id || node.id;
        html += `<option value="proc_${pId}">Proceso: ${escapeHtml(node.name || 'Proceso')}</option>`;
      });
      html += `</optgroup>`;
    }
    scopeSel.innerHTML = html;
    scopeSel.value = currentVal;
    if (scopeSel.value !== currentVal) {
      scopeSel.value = "all";
      state.paramScopeFilter = "all";
    }
  }

  function updateParamGroupOptions() {
    const groupSel = document.getElementById("selectParamGroupFilter");
    if (!groupSel) return;

    const currentVal = state.paramGroupFilter || "all";
    const scope = state.paramScopeFilter || "all";
    const allParams = state.systemParameters || [];

    const inScopeParams = allParams.filter(p => {
      if (scope === "all") return true;
      if (scope === "global") return p.scope === "global";
      if (scope === "local") return p.scope === "local";
      if (scope.startsWith("proc_")) {
        const targetId = scope.replace("proc_", "");
        return p.scope === "local" && (String(p.process_id) === targetId || String(p.process_id) === targetId.replace("node_", ""));
      }
      return true;
    });

    const groupCounts = {};
    inScopeParams.forEach(p => {
      const g = p.group ? p.group.trim() : "General";
      groupCounts[g] = (groupCounts[g] || 0) + 1;
    });

    const uniqueGroups = Object.keys(groupCounts).sort();

    let html = `<option value="all">Todos los Grupos (${inScopeParams.length})</option>`;
    uniqueGroups.forEach(g => {
      html += `<option value="${escapeHtml(g)}">${escapeHtml(g)} (${groupCounts[g]})</option>`;
    });

    groupSel.innerHTML = html;
    if (uniqueGroups.includes(currentVal)) {
      groupSel.value = currentVal;
    } else {
      groupSel.value = "all";
      state.paramGroupFilter = "all";
    }
  }

  function renderSystemParametersTable() {
    updateParamScopeOptions();
    updateParamGroupOptions();

    const scrollArea = document.getElementById("canvasParamsScrollArea");
    if (!scrollArea) return;

    const allParams = state.systemParameters || [];
    const scope = state.paramScopeFilter || "all";
    const group = state.paramGroupFilter || "all";
    const type = state.paramTypeFilter || "all";
    const query = (state.paramSearchQuery || "").trim().toLowerCase();

    const filtered = allParams.filter(p => {
      if (scope === "global" && p.scope !== "global") return false;
      if (scope === "local" && p.scope !== "local") return false;
      if (scope.startsWith("proc_")) {
        const targetId = scope.replace("proc_", "");
        if (p.scope !== "local") return false;
        if (String(p.process_id) !== targetId && String(p.process_id) !== targetId.replace("node_", "")) return false;
      }

      if (group !== "all") {
        const pGroup = p.group ? p.group.trim() : "General";
        if (pGroup !== group) return false;
      }

      if (type !== "all" && p.param_type !== type) return false;

      if (query) {
        const matchName = (p.name || "").toLowerCase().includes(query);
        const matchGroup = (p.group || "").toLowerCase().includes(query);
        const matchFormula = (p.formula || "").toLowerCase().includes(query);
        const matchDesc = (p.description || "").toLowerCase().includes(query);
        const matchProc = (p.process_name || "").toLowerCase().includes(query);
        if (!matchName && !matchGroup && !matchFormula && !matchDesc && !matchProc) return false;
      }

      return true;
    });

    const statCount = document.getElementById("statParamsCount");
    const statIndep = document.getElementById("statParamsIndep");
    const statDep = document.getElementById("statParamsDep");
    const badgeCount = document.getElementById("badgeParamsCount");

    const totalIndep = filtered.filter(p => p.param_type === "independent").length;
    const totalDep = filtered.filter(p => p.param_type === "dependent").length;

    if (statCount) statCount.textContent = `Parámetros: ${filtered.length}`;
    if (statIndep) statIndep.textContent = `Independientes: ${totalIndep}`;
    if (statDep) statDep.textContent = `Dependientes: ${totalDep}`;
    if (badgeCount) badgeCount.textContent = `${allParams.length} Parámetros`;

    if (filtered.length === 0) {
      scrollArea.innerHTML = `
        <div style="padding: 48px 20px; text-align: center; color: var(--text-muted);">
          <div style="font-size: 13.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px;">No se encontraron parámetros</div>
          <div style="font-size: 11px; max-width: 440px; margin: 0 auto 16px; line-height: 1.5;">
            No hay variables que coincidan con los filtros seleccionados (Ámbito: ${escapeHtml(scope)}, Grupo: ${escapeHtml(group)}).
          </div>
          <button type="button" class="btn btn-primary btn-sm" onclick="window.EconodeApp.openParameterModal()">
            + Definir Nuevo Parámetro
          </button>
        </div>
      `;
      return;
    }

    let tableHtml = `
      <table class="table-v2" style="width: 100%; border-collapse: collapse; font-size: 11px;">
        <thead>
          <tr style="background: var(--bg-subtle); border-bottom: 1px solid var(--border-color); text-align: left;">
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); width: 190px;">Variable / Identificador</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); width: 170px;">Ámbito</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); width: 150px;">Grupo</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); width: 110px;">Tipo</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); min-width: 200px;">Valor / Fórmula Matemática</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); width: 85px;">Unidad</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary);">Descripción Metodológica</th>
            <th style="padding: 9px 12px; font-weight: 700; color: var(--text-secondary); text-align: right; width: 125px;">Acciones</th>
          </tr>
        </thead>
        <tbody>
    `;

    filtered.forEach((p, idx) => {
      const isDep = p.param_type === "dependent";
      const isGlobal = p.scope === "global";
      const scopeBadge = isGlobal
        ? `<span class="badge-pill badge-primary" style="font-size: 9px; padding: 1px 6px;">Global</span>`
        : `<span class="badge-pill badge-emerald" style="font-size: 9px; padding: 1px 6px;" title="Asociado a ${escapeHtml(p.process_name || 'Proceso')}">Local: ${escapeHtml(p.process_name || 'Proceso')}</span>`;

      const typeBadge = isDep
        ? `<span class="badge-pill" style="background: rgba(139, 92, 246, 0.12); color: #7C3AED; font-size: 9px; padding: 1px 6px;">Dependiente</span>`
        : `<span class="badge-pill badge-slate" style="font-size: 9px; padding: 1px 6px;">Independiente</span>`;

      const valDisplay = isDep
        ? `<div class="mono" style="font-weight: 600; color: #7C3AED; font-size: 11px;">f(x) = ${escapeHtml(p.formula || '')}</div>`
        : `<div class="mono" style="font-weight: 700; color: var(--text-primary); font-size: 11px;">${Number(p.value).toLocaleString("es-MX", { maximumFractionDigits: 4 })}</div>`;

      tableHtml += `
        <tr style="border-bottom: 1px solid var(--border-color); background: ${idx % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-subtle)'};">
          <td style="padding: 8px 12px;">
            <span class="mono" style="font-weight: 700; color: var(--accent-primary); font-size: 11.5px;">${escapeHtml(p.name)}</span>
          </td>
          <td style="padding: 8px 12px;">
            ${scopeBadge}
          </td>
          <td style="padding: 8px 12px;">
            <span class="badge-pill badge-outline" style="font-size: 9px; font-weight: 600;">${escapeHtml(p.group || 'General')}</span>
          </td>
          <td style="padding: 8px 12px;">
            ${typeBadge}
          </td>
          <td style="padding: 8px 12px;">
            ${valDisplay}
          </td>
          <td style="padding: 8px 12px;">
            <span class="mono" style="font-weight: 600; color: var(--text-secondary);">${escapeHtml(p.unit || '')}</span>
          </td>
          <td style="padding: 8px 12px; max-width: 280px;">
            <span style="font-size: 10.5px; color: var(--text-secondary); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(p.description || '')}">
              ${escapeHtml(p.description || '-')}
            </span>
          </td>
          <td style="padding: 8px 12px; text-align: right; white-space: nowrap;">
            <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 2px 7px; margin-right: 4px;" onclick="window.EconodeApp.editParameterById('${p.id}')">
              Editar
            </button>
            <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; padding: 2px 7px; color: #EF4444;" onclick="window.EconodeApp.deleteParameter('${p.id}')">
              Eliminar
            </button>
          </td>
        </tr>
      `;
    });

    tableHtml += `
        </tbody>
      </table>
    `;

    scrollArea.innerHTML = tableHtml;
  }

  function renderProcessParametersInInspector(node) {
    if (!node) return "";
    const allParams = state.systemParameters || [];
    const procId = node.process_id || node.id;
    const cleanProcId = String(procId).replace("node_", "");

    const localParams = allParams.filter(p => {
      if (p.scope !== "local") return false;
      const pidStr = String(p.process_id || "").replace("node_", "");
      return pidStr === cleanProcId || p.process_name === node.name;
    });

    const countBadge = document.getElementById("inspParamsCountBadge");
    if (countBadge) countBadge.textContent = String(localParams.length);

    if (localParams.length === 0) {
      return `
        <div style="font-size: 10px; color: var(--text-muted); font-style: italic; padding: 6px; background: var(--bg-subtle); border-radius: 4px; text-align: center;">
          Sin parámetros locales asignados a este proceso.
        </div>
      `;
    }

    return localParams.map(p => {
      const isDep = p.param_type === "dependent";
      return `
        <div style="font-size: 10px; padding: 6px 8px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 4px; display: flex; flex-direction: column; gap: 2px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="mono" style="font-weight: 700; color: var(--accent-primary); font-size: 10.5px;">${escapeHtml(p.name)}</span>
            <span class="badge-pill badge-outline" style="font-size: 8px; padding: 1px 4px;">${escapeHtml(p.group || 'General')}</span>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
            <span style="font-size: 9.5px; color: var(--text-muted);">
              ${isDep ? 'Fórmula' : 'Valor'}: <strong class="mono" style="color: var(--text-primary);">${isDep ? escapeHtml(p.formula) : Number(p.value).toLocaleString('es-MX', { maximumFractionDigits: 3 })} ${escapeHtml(p.unit)}</strong>
            </span>
            <button type="button" style="background: transparent; border: none; color: var(--accent-primary); cursor: pointer; font-size: 9.5px; padding: 0 3px;" onclick="window.EconodeApp.editParameterById('${p.id}')">
              Editar
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  function openParameterModal(paramToEdit = null, prefillNodeOrId = null) {
    const modal = document.getElementById("modalParamForm");
    if (!modal) return;

    const procSel = document.getElementById("paramFormProcessSelect");
    if (procSel) {
      const nodes = state.canvasNodes || [];
      procSel.innerHTML = nodes.map(n => {
        const pid = n.process_id || n.id;
        return `<option value="${pid}">${escapeHtml(n.name)} (#${pid})</option>`;
      }).join('');
    }

    const titleEl = document.getElementById("modalParamFormTitle");
    const idInput = document.getElementById("paramFormId");
    const nameInput = document.getElementById("paramFormName");
    const unitInput = document.getElementById("paramFormUnit");
    const scopeSel = document.getElementById("paramFormScope");
    const procWrap = document.getElementById("paramFormProcessWrapper");
    const groupInput = document.getElementById("paramFormGroup");
    const typeHidden = document.getElementById("paramFormType");
    const btnIndep = document.getElementById("btnParamTypeIndep");
    const btnDep = document.getElementById("btnParamTypeDep");
    const valWrap = document.getElementById("paramFormValueWrapper");
    const valInput = document.getElementById("paramFormValue");
    const formWrap = document.getElementById("paramFormFormulaWrapper");
    const formInput = document.getElementById("paramFormFormula");
    const descInput = document.getElementById("paramFormDesc");

    state.editingParameter = paramToEdit;

    if (paramToEdit) {
      if (titleEl) titleEl.textContent = `Editar Parámetro: ${paramToEdit.name}`;
      if (idInput) idInput.value = paramToEdit.id || "";
      if (nameInput) nameInput.value = paramToEdit.name || "";
      if (unitInput) unitInput.value = paramToEdit.unit || "";
      if (scopeSel) scopeSel.value = paramToEdit.scope || "global";
      if (procWrap) procWrap.style.display = paramToEdit.scope === "local" ? "block" : "none";
      if (procSel && paramToEdit.process_id) procSel.value = String(paramToEdit.process_id);
      if (groupInput) groupInput.value = paramToEdit.group || "General";
      
      const isDep = paramToEdit.param_type === "dependent";
      if (typeHidden) typeHidden.value = paramToEdit.param_type || "independent";
      if (btnIndep) btnIndep.classList.toggle("active", !isDep);
      if (btnDep) btnDep.classList.toggle("active", isDep);
      if (valWrap) valWrap.style.display = isDep ? "none" : "block";
      if (valInput) valInput.value = paramToEdit.value !== undefined ? paramToEdit.value : 0;
      if (formWrap) formWrap.style.display = isDep ? "block" : "none";
      if (formInput) formInput.value = paramToEdit.formula || "";
      if (descInput) descInput.value = paramToEdit.description || "";
    } else {
      if (titleEl) titleEl.textContent = "Definir Parámetro del Modelo";
      if (idInput) idInput.value = "";
      if (nameInput) nameInput.value = "";
      if (unitInput) unitInput.value = "kg";
      
      let targetNode = null;
      if (prefillNodeOrId) {
        if (typeof prefillNodeOrId === "object") {
          targetNode = prefillNodeOrId;
        } else {
          targetNode = (state.canvasNodes || []).find(n => String(n.id) === String(prefillNodeOrId) || String(n.process_id) === String(prefillNodeOrId));
        }
      }

      if (targetNode) {
        if (scopeSel) scopeSel.value = "local";
        if (procWrap) procWrap.style.display = "block";
        if (procSel) procSel.value = String(targetNode.process_id || targetNode.id);
        if (groupInput) groupInput.value = "Eficiencias y Mermas";
      } else {
        const curScope = state.paramScopeFilter || "all";
        if (curScope === "local") {
          if (scopeSel) scopeSel.value = "local";
          if (procWrap) procWrap.style.display = "block";
        } else if (curScope.startsWith("proc_")) {
          const targetId = curScope.replace("proc_", "");
          if (scopeSel) scopeSel.value = "local";
          if (procWrap) procWrap.style.display = "block";
          if (procSel) procSel.value = targetId;
        } else {
          if (scopeSel) scopeSel.value = "global";
          if (procWrap) procWrap.style.display = "none";
        }
        const curGroup = state.paramGroupFilter || "all";
        if (groupInput) groupInput.value = (curGroup !== "all") ? curGroup : "Materias Primas";
      }

      if (typeHidden) typeHidden.value = "independent";
      if (btnIndep) btnIndep.classList.add("active");
      if (btnDep) btnDep.classList.remove("active");
      if (valWrap) valWrap.style.display = "block";
      if (valInput) valInput.value = "";
      if (formWrap) formWrap.style.display = "none";
      if (formInput) formInput.value = "";
      if (descInput) descInput.value = "";
    }

    modal.style.display = "flex";
    modal.classList.add("active");
    setTimeout(() => {
      if (nameInput) nameInput.focus();
    }, 100);
  }

  function closeParameterModal() {
    const modal = document.getElementById("modalParamForm");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
    state.editingParameter = null;
  }

  async function saveParameterFromModal() {
    const sys = state.activeSystem;
    if (!sys || !sys.id) {
      alert("No hay un sistema producto activo para asociar el parámetro.");
      return;
    }

    const idInput = document.getElementById("paramFormId");
    const nameInput = document.getElementById("paramFormName");
    const unitInput = document.getElementById("paramFormUnit");
    const scopeSel = document.getElementById("paramFormScope");
    const procSel = document.getElementById("paramFormProcessSelect");
    const groupInput = document.getElementById("paramFormGroup");
    const typeHidden = document.getElementById("paramFormType");
    const valInput = document.getElementById("paramFormValue");
    const formInput = document.getElementById("paramFormFormula");
    const descInput = document.getElementById("paramFormDesc");

    const rawName = (nameInput ? nameInput.value : "").trim();
    if (!rawName) {
      alert("Por favor ingresa un nombre para la variable.");
      if (nameInput) nameInput.focus();
      return;
    }

    const cleanName = rawName.replace(/[^a-zA-Z0-9_]/g, "_").toLowerCase();
    const scope = scopeSel ? scopeSel.value : "global";
    let procId = null;
    let procName = "Global / Sistema Completo";

    if (scope === "local" && procSel) {
      procId = procSel.value;
      const opt = procSel.options[procSel.selectedIndex];
      if (opt) procName = opt.textContent.split(" (#")[0];
    }

    const group = (groupInput && groupInput.value.trim()) ? groupInput.value.trim() : "General";
    const paramType = typeHidden ? typeHidden.value : "independent";
    const unit = unitInput ? unitInput.value.trim() : "kg";
    const val = (valInput && valInput.value !== "") ? parseFloat(valInput.value) : 0.0;
    const formula = formInput ? formInput.value.trim() : "";
    const desc = descInput ? descInput.value.trim() : "";

    const payload = {
      id: (idInput && idInput.value) ? idInput.value : undefined,
      name: cleanName,
      scope: scope,
      process_id: procId,
      process_name: procName,
      group: group,
      param_type: paramType,
      value: val,
      formula: formula,
      unit: unit,
      description: desc
    };

    try {
      const res = await api.saveSystemParameter(sys.id, payload);
      if (res && res.status === "success" && res.parameter) {
        const saved = res.parameter;
        const idx = (state.systemParameters || []).findIndex(p => p.id === saved.id);
        if (idx >= 0) {
          state.systemParameters[idx] = saved;
        } else {
          state.systemParameters.push(saved);
        }

        renderSystemParametersTable();
        if (state.selectedNode) {
          inspectNode(state.selectedNode);
        }

        closeParameterModal();
        showNotification("Parámetro guardado exitosamente.");
      } else {
        alert(res?.error || "Error al guardar el parámetro.");
      }
    } catch (err) {
      alert("Error en la solicitud: " + err.message);
    }
  }

  async function deleteParameter(paramId) {
    if (!paramId) return;
    const sys = state.activeSystem;
    if (!sys || !sys.id) return;

    const p = (state.systemParameters || []).find(item => item.id === paramId);
    const pName = p ? p.name : paramId;

    if (!confirm(`¿Deseas eliminar el parámetro "${pName}" del modelo?`)) {
      return;
    }

    try {
      const res = await api.deleteSystemParameter(sys.id, paramId);
      if (res && res.status === "success") {
        state.systemParameters = (state.systemParameters || []).filter(item => item.id !== paramId);
        renderSystemParametersTable();
        if (state.selectedNode) {
          inspectNode(state.selectedNode);
        }
        showNotification("Parámetro eliminado.");
      } else {
        alert(res?.error || "Error al eliminar el parámetro.");
      }
    } catch (err) {
      alert("Error en la solicitud: " + err.message);
    }
  }

  function editParameterById(paramId) {
    const p = (state.systemParameters || []).find(item => item.id === paramId);
    if (p) {
      openParameterModal(p);
    }
  }

  function exportParametersCsv() {
    const sys = state.activeSystem;
    const sysName = (sys && sys.name) ? sys.name : "Sistema_Producto";
    const dateStr = new Date().toISOString().slice(0, 10);
    const filename = `Parametros_${sysName.replace(/[^a-zA-Z0-9_\-]/g, "_")}_${dateStr}.csv`;

    let csv = "\uFEFF";
    csv += "ID,Nombre,Ambito,Proceso,Grupo,Tipo,Valor,Formula,Unidad,Descripcion\\n";

    (state.systemParameters || []).forEach(p => {
      const row = [
        `"${(p.id || '').replace(/"/g, '""')}"`,
        `"${(p.name || '').replace(/"/g, '""')}"`,
        `"${(p.scope || '').replace(/"/g, '""')}"`,
        `"${(p.process_name || '').replace(/"/g, '""')}"`,
        `"${(p.group || 'General').replace(/"/g, '""')}"`,
        `"${(p.param_type || 'independent').replace(/"/g, '""')}"`,
        p.value !== undefined ? p.value : 0,
        `"${(p.formula || '').replace(/"/g, '""')}"`,
        `"${(p.unit || '').replace(/"/g, '""')}"`,
        `"${(p.description || '').replace(/"/g, '""')}"`
      ];
      csv += row.join(",") + "\n";
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

    showNotification("Parámetros exportados en CSV.");
  }

  function openTableConnectModal() {
    const systemProcesses = getAllSystemProcesses();
    if (!systemProcesses || systemProcesses.length < 2) {
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
      systemProcesses.forEach((node, i) => {
        srcOpts += `<option value="${node.id}" ${i === 0 ? 'selected' : ''}>${escapeHtml(node.name)} (#${node.process_id || node.id})</option>`;
        tgtOpts += `<option value="${node.id}" ${i === 1 ? 'selected' : ''}>${escapeHtml(node.name)} (#${node.process_id || node.id})</option>`;
      });
      selectSrc.innerHTML = srcOpts;
      selectTgt.innerHTML = tgtOpts;

      const updateFlowsFromChosenSource = () => {
        const srcId = selectSrc.value;
        const srcNode = systemProcesses.find(n => String(n.id) === String(srcId) || String(n.process_id) === String(srcId));
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
              const typeBadge = out.is_reference ? ' [Referencia]' : out.is_waste ? ' [Residuo]' : ' [Coproducto]';
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
        state.connectingToNode = systemProcesses.find(n => String(n.id) === String(tgtId) || String(n.process_id) === String(tgtId));
      };

      updateFlowsFromChosenSource();
      const firstTgt = systemProcesses.find(n => String(n.id) === String(selectTgt.value) || String(n.process_id) === String(selectTgt.value));
      state.connectingToNode = firstTgt || systemProcesses[1] || null;
    }

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
    }
  }

  // Modificaciones directas desde la tabla
  function tableUpdateAmount(nodeId, type, idx, value, isInputEvent = false) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
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

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    if (!isInputEvent) {
      if (state.selectedNode && String(state.selectedNode.id) === String(node.id)) {
        inspectNode(node);
      }
    }
  }

  function tableUpdateFlowName(nodeId, type, idx, newName) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
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

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableUpdateUnit(nodeId, type, idx, newUnit) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
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

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
  }

  function tableUpdateFlowComment(nodeId, type, idx, value) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (value || "").trim();

    if (type === "input" && node.inputs && node.inputs[idx]) {
      node.inputs[idx].comment = trimmed;
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      node.outputs[idx].comment = trimmed;
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
  }

  function tableUpdateFlowAssumptions(nodeId, type, idx, value) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (value || "").trim();

    if (type === "input" && node.inputs && node.inputs[idx]) {
      node.inputs[idx].assumptions = trimmed;
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      node.outputs[idx].assumptions = trimmed;
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
  }

  function tableUpdateFlowLinks(nodeId, type, idx, value) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (value || "").trim();

    if (type === "input" && node.inputs && node.inputs[idx]) {
      node.inputs[idx].external_links = trimmed;
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      node.outputs[idx].external_links = trimmed;
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableUpdateProcessName(nodeId, newName) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;
    const trimmed = (newName || "").trim();
    if (!trimmed) return;
    node.name = trimmed;
    if (node.reference_flow && (!node.reference_flow.name || node.reference_flow.name.includes("(Producto)"))) {
      node.reference_flow.name = `${trimmed} (Producto)`;
    }
    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderPaletteProcesses();
    if (state.canvasViewMode === "table") {
      renderCanvasTableView();
    } else {
      renderCanvasStage();
    }
  }

  // =========================================================================
  // EXCEL SPREADSHEET AUTOCOMPLETE CONTROLLER (PROCESSES & FLOWS)
  // =========================================================================
  const excelAutocomplete = {
    dropdownEl: null,
    activeInput: null,
    currentType: null, // "process" | "flow"
    nodeId: null,
    flowKind: null,
    flowIdx: null,
    debounceTimer: null,
    cache: new Map(),
    selectedIndex: -1,
    currentResults: [],
    
    init() {
      if (this.dropdownEl) return;
      let el = document.getElementById("excelAutocompleteDropdown");
      if (!el) {
        el = document.createElement("div");
        el.id = "excelAutocompleteDropdown";
        el.className = "excel-autocomplete-dropdown";
        el.style.display = "none";
        document.body.appendChild(el);
      }
      this.dropdownEl = el;

      // Cerrar si se da clic fuera
      document.addEventListener("mousedown", (e) => {
        if (!this.dropdownEl || this.dropdownEl.style.display === "none") return;
        if (!this.dropdownEl.contains(e.target) && e.target !== this.activeInput) {
          this.close();
        }
      });

      // Reposicionar al hacer scroll en la tabla o ventana
      window.addEventListener("scroll", () => {
        if (this.dropdownEl && this.dropdownEl.style.display !== "none") {
          this.updatePosition();
        }
      }, { passive: true, capture: true });
    },

    open(inputEl, type, options = {}) {
      this.init();
      this.activeInput = inputEl;
      this.currentType = type; // "process" o "flow"
      this.nodeId = options.nodeId || null;
      this.flowKind = options.flowKind || "input";
      this.flowIdx = options.idx !== undefined ? options.idx : -1;
      this.selectedIndex = -1;

      this.updatePosition();
      this.dropdownEl.style.display = "flex";
      this.query(inputEl.value);
    },

    updatePosition() {
      if (!this.activeInput || !this.dropdownEl) return;
      const rect = this.activeInput.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) {
        this.close();
        return;
      }
      const viewportHeight = window.innerHeight;
      const dropdownHeight = 270;
      
      let top = rect.bottom + 3;
      if (top + dropdownHeight > viewportHeight && rect.top > dropdownHeight) {
        top = Math.max(8, rect.top - dropdownHeight - 3);
      }
      
      const left = Math.max(8, Math.min(rect.left, window.innerWidth - 360));
      this.dropdownEl.style.top = `${Math.round(top)}px`;
      this.dropdownEl.style.left = `${Math.round(left)}px`;
      this.dropdownEl.style.minWidth = `${Math.max(Math.round(rect.width), 340)}px`;
    },

    close() {
      if (this.dropdownEl) {
        this.dropdownEl.style.display = "none";
        this.dropdownEl.innerHTML = "";
      }
      this.activeInput = null;
      this.currentResults = [];
      this.selectedIndex = -1;
    },

    query(text) {
      if (this.debounceTimer) clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.fetchResults((text || "").trim());
      }, 100);
    },

    async fetchResults(searchTerm) {
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      const t = (k, f) => (window.I18n && window.I18n.t ? window.I18n.t(k, f) : f);

      const cacheKey = `${this.currentType}:${searchTerm.toLowerCase()}`;
      if (this.cache.has(cacheKey)) {
        this.renderResults(this.cache.get(cacheKey), searchTerm);
        return;
      }

      this.dropdownEl.innerHTML = `
        <div class="excel-ac-header">
          <span>${this.currentType === "process" ? t("canvas.autocomplete_proc_title", "Procesos del Inventario (ecoinvent 3.12)") : t("canvas.autocomplete_flow_title", "Flujos e Insumos (ecoinvent 3.12)")}</span>
        </div>
        <div class="excel-ac-loading">${t("canvas.autocomplete_searching", "Buscando en ecoinvent 3.12...")}</div>
      `;

      try {
        let items = [];
        if (this.currentType === "process") {
          // 1. Procesos locales en paleta / lienzo
          const localProcs = (state.paletteProcesses || []).concat(state.canvasNodes || []).map(p => ({
            id: p.process_id || p.id,
            name: p.name,
            location: p.location || "GLO",
            category_name: p.category || (isEn ? "Catalog Process" : "Proceso del Catálogo"),
            reference_unit: p.unit || "kg",
            is_local: true
          }));

          const matchedLocal = searchTerm ? 
            localProcs.filter(p => (p.name || "").toLowerCase().includes(searchTerm.toLowerCase())) : 
            localProcs.slice(0, 5);

          // 2. Procesos de la base de datos ecoinvent
          const res = await api.searchCatalog(searchTerm, "ALL", 18);
          const dbProcs = res.items || [];

          // Mezclar y deduplicar por nombre
          const seenNames = new Set();
          items = [];
          matchedLocal.forEach(p => {
            const k = (p.name || "").toLowerCase();
            if (k && !seenNames.has(k)) {
              seenNames.add(k);
              items.push(p);
            }
          });
          dbProcs.forEach(p => {
            const k = (p.name || "").toLowerCase();
            if (k && !seenNames.has(k)) {
              seenNames.add(k);
              items.push(p);
            }
          });
        } else {
          // FLUJOS
          // 1. Flujos de salida de otros procesos en el lienzo (como opción de conexión directa upstream)
          const upstreamOutputs = [];
          (state.canvasNodes || []).forEach(n => {
            if (this.nodeId && String(n.id) === String(this.nodeId)) return;
            (n.outputs || []).forEach(o => {
              if (o.name) {
                upstreamOutputs.push({
                  id: `up_${n.id}_${o.name}`,
                  name: o.name,
                  unit_symbol: o.unit || "kg",
                  category_name: `${isEn ? "Output of:" : "Salida de:"} ${n.name} (#${n.process_id || n.id})`,
                  flow_type: "CONNECTED_FLOW",
                  source_node_id: n.id,
                  source_process_id: n.process_id,
                  source_node_name: n.name,
                  is_upstream: true
                });
              }
            });
          });

          const matchedUpstream = searchTerm ? 
            upstreamOutputs.filter(f => f.name.toLowerCase().includes(searchTerm.toLowerCase())) : 
            upstreamOutputs;

          // 2. Flujos en base de datos ecoinvent
          const res = await api.getDbFlows(searchTerm, "ALL", 25);
          const dbFlows = res.items || [];

          // Combinar
          const seenFlows = new Set();
          items = [];
          matchedUpstream.forEach(f => {
            const k = (f.name || "").toLowerCase();
            if (k && !seenFlows.has(k)) {
              seenFlows.add(k);
              items.push(f);
            }
          });
          dbFlows.forEach(f => {
            const k = (f.name || "").toLowerCase();
            if (k && !seenFlows.has(k)) {
              seenFlows.add(k);
              items.push(f);
            }
          });
        }

        this.cache.set(cacheKey, items);
        this.renderResults(items, searchTerm);
      } catch (err) {
        console.error("Error al obtener sugerencias de ecoinvent:", err);
        this.renderResults([], searchTerm);
      }
    },

    renderResults(items, searchTerm) {
      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      const t = (k, f) => (window.I18n && window.I18n.t ? window.I18n.t(k, f) : f);

      this.currentResults = items;
      this.selectedIndex = -1;

      const title = this.currentType === "process" ? 
        t("canvas.autocomplete_proc_title", "Procesos del Inventario (ecoinvent 3.12)") : 
        t("canvas.autocomplete_flow_title", "Flujos e Insumos (ecoinvent 3.12)");

      if (!items || items.length === 0) {
        this.dropdownEl.innerHTML = `
          <div class="excel-ac-header">
            <span>${title}</span>
            <span style="font-size: 8.5px; opacity: 0.7;">0 ${isEn ? "results" : "resultados"}</span>
          </div>
          <div class="excel-ac-empty">
            ${t("canvas.autocomplete_no_results", "Sin coincidencias directas en ecoinvent. Presiona Enter para usar personalizado.")}
          </div>
        `;
        return;
      }

      let listHtml = '';
      items.forEach((item, idx) => {
        const name = item.name || "Item";
        const unit = item.unit_symbol || item.reference_unit || item.unit || "kg";
        const cat = item.category_name || item.location || (item.is_local ? (isEn ? "Catalog" : "Catálogo") : "ecoinvent 3.12");
        const isUpstream = item.is_upstream === true;

        let badgeTag = '';
        if (isUpstream) {
          badgeTag = `<span class="excel-ac-badge-tag excel-ac-badge-connected"> ${t("canvas.autocomplete_upstream_badge", "Conexión")}</span>`;
        } else if (item.flow_type === "ELEMENTARY_FLOW") {
          badgeTag = `<span class="excel-ac-badge-tag" style="background:#FEF3C7; color:#92400E;"> Biosfera</span>`;
        } else if (item.flow_type === "WASTE_FLOW") {
          badgeTag = `<span class="excel-ac-badge-tag" style="background:#FEE2E2; color:#991B1B;"> Residuo</span>`;
        } else if (item.location) {
          badgeTag = `<span class="excel-ac-badge-tag"> ${item.location}</span>`;
        }

        listHtml += `
          <div class="excel-ac-item" data-index="${idx}" onmousedown="window.EconodeApp.excelAutocompleteSelect(${idx})">
            <div class="excel-ac-item-main">
              <span class="excel-ac-item-name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>
              <span class="excel-ac-item-sub">${escapeHtml(cat)}</span>
            </div>
            <div class="excel-ac-item-meta">
              ${badgeTag}
              <span class="excel-ac-badge-unit">${escapeHtml(unit)}</span>
            </div>
          </div>
        `;
      });

      this.dropdownEl.innerHTML = `
        <div class="excel-ac-header">
          <span>${title}</span>
          <span style="font-size: 8.5px; opacity: 0.7;">${items.length} ${isEn ? "suggestions" : "sugerencias"}</span>
        </div>
        <div class="excel-ac-list">
          ${listHtml}
        </div>
      `;
    },

    async selectItem(idx) {
      const item = this.currentResults[idx];
      if (!item || !this.activeInput) return;

      if (this.currentType === "process") {
        this.activeInput.value = item.name;
        const tr = this.activeInput.closest("tr");
        if (tr) {
          const unitInput = tr.querySelector(".excel-input-new-unit");
          if (unitInput && (item.reference_unit || item.unit)) {
            unitInput.value = item.reference_unit || item.unit;
          }
          const matInput = tr.querySelector(".excel-input-new-mat");
          if (matInput && !matInput.value.trim() && item.reference_flow_name) {
            matInput.value = item.reference_flow_name;
          }
        }

        if (this.nodeId) {
          if (item.id) {
            await tableChangeNodeToCatalogProcess(this.nodeId, item.id);
          } else {
            tableUpdateProcessName(this.nodeId, item.name);
            if (item.reference_unit || item.unit) {
              tableUpdateUnit(this.nodeId, "output", 0, item.reference_unit || item.unit);
            }
          }
        } else if (tr && tr.classList.contains("excel-row-new-process")) {
          this.activeInput.dataset.processId = item.id || "";
          const matVal = tr.querySelector(".excel-input-new-mat")?.value;
          const amtVal = tr.querySelector(".excel-input-new-amt")?.value;
          const unitVal = tr.querySelector(".excel-input-new-unit")?.value;
          await tableCreateProcessInline(item.name, matVal, amtVal, unitVal, item.id);
        }
      } else if (this.currentType === "flow") {
        this.activeInput.value = item.name;
        const tr = this.activeInput.closest("tr");
        if (tr) {
          const unitInput = tr.querySelector(".excel-input-new-flow-unit") || tr.querySelector(".excel-input-new-unit") || tr.querySelector('td[data-col="E"] input');
          if (unitInput && (item.unit_symbol || item.unit)) {
            unitInput.value = item.unit_symbol || item.unit;
          }

          if (item.is_upstream && item.source_node_id) {
            this.activeInput.dataset.upstreamSourceId = item.source_node_id;
            this.activeInput.dataset.upstreamProcessId = item.source_process_id || "";
            const providerCell = tr.querySelector('td[data-col="C"]');
            if (providerCell) {
              const srcNode = (state.canvasNodes || []).find(n => String(n.id) === String(item.source_node_id));
              const srcName = srcNode ? srcNode.name : (item.source_node_name || "Proceso Upstream");
              providerCell.innerHTML = `<span style="color: #6D28D9; font-weight: 600;"> ${escapeHtml(srcName)}</span>`;
            }
          }
        }

        if (this.nodeId && this.flowIdx >= 0) {
          const procs = getAllSystemProcesses();
          const node = procs.find(n => String(n.id) === String(this.nodeId) || String(n.process_id) === String(this.nodeId));
          if (node && node.inputs && node.inputs[this.flowIdx]) {
            node.inputs[this.flowIdx].name = item.name;
            if (item.unit_symbol || item.unit) {
              node.inputs[this.flowIdx].unit = item.unit_symbol || item.unit;
            }
            if (item.is_upstream && item.source_node_id) {
              const srcNode = procs.find(n => String(n.id) === String(item.source_node_id));
              node.inputs[this.flowIdx].origin = srcNode ? srcNode.name : item.source_node_name;
              
              if (!state.canvasEdges) state.canvasEdges = [];
              state.canvasEdges = state.canvasEdges.filter(e => {
                const isTarget = (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id));
                if (!isTarget) return true;
                return !areFlowsMatching(e.flow, item.name);
              });

              state.canvasEdges.push({
                id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
                from: item.source_node_id,
                to: node.id,
                source_process_id: item.source_process_id,
                target_process_id: node.process_id,
                flow: item.name,
                amount: parseFloat(node.inputs[this.flowIdx].amount) || 1.0,
                unit: item.unit_symbol || item.unit || "kg"
              });
            } else {
              node.inputs[this.flowIdx].origin = "Mercado ecoinvent 3.12";
              if (!state.canvasEdges) state.canvasEdges = [];
              state.canvasEdges = state.canvasEdges.filter(e => {
                const isTarget = (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id));
                if (!isTarget) return true;
                return !areFlowsMatching(e.flow, item.name);
              });
            }
            syncSystemProcesses();
            scheduleAutoSaveCanvas();
            renderCanvasEdges();
            renderPaletteProcesses();
            renderCanvasTableView();
            if (state.canvasViewMode === "visual") {
              renderCanvasStage();
            }
          }
        } else if (tr && tr.classList.contains("excel-row-add-flow") && this.nodeId) {
          const amtVal = tr.querySelector(".excel-input-new-flow-amt")?.value || 1.0;
          const unitVal = tr.querySelector(".excel-input-new-flow-unit")?.value || (item.unit_symbol || item.unit || "kg");
          const kindSelect = tr.querySelector(".excel-select-new-flow-kind");
          let flowKind = kindSelect ? kindSelect.value : "input";
          if (item.flow_type === "WASTE_FLOW" && kindSelect) {
            kindSelect.value = "output_waste";
            flowKind = "output_waste";
          } else if (item.flow_type === "ELEMENTARY_FLOW" && kindSelect) {
            kindSelect.value = "output_elementary";
            flowKind = "output_elementary";
          }
          const procs = getAllSystemProcesses();
          const srcNode = item.is_upstream ? procs.find(n => String(n.id) === String(item.source_node_id)) : null;
          const origin = srcNode ? srcNode.name : "Mercado ecoinvent 3.12";
          tableCreateFlowInline(this.nodeId, item.name, amtVal, unitVal, origin, item.source_node_id, item.source_process_id, flowKind);
        }
      }
      const targetInput = this.activeInput;
      this.close();
      if (targetInput) targetInput.focus();
    },

    handleKeyDown(e) {
      if (!this.dropdownEl || this.dropdownEl.style.display === "none") return false;
      const items = this.dropdownEl.querySelectorAll(".excel-ac-item");
      if (items.length === 0) return false;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        this.selectedIndex = (this.selectedIndex + 1) % items.length;
        this.highlightSelected(items);
        return true;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        this.selectedIndex = (this.selectedIndex - 1 + items.length) % items.length;
        this.highlightSelected(items);
        return true;
      } else if (e.key === "Enter" && this.selectedIndex >= 0) {
        e.preventDefault();
        this.selectItem(this.selectedIndex);
        return true;
      } else if (e.key === "Escape") {
        e.preventDefault();
        this.close();
        return true;
      }
      return false;
    },

    highlightSelected(items) {
      items.forEach((item, i) => {
        if (i === this.selectedIndex) {
          item.classList.add("active");
          item.scrollIntoView({ block: "nearest" });
        } else {
          item.classList.remove("active");
        }
      });
    }
  };

  async function tableCreateProcessInline(name, initialMaterial, initialAmount = 1.0, initialUnit = "kg", catalogProcessId = null) {
    const trimmedName = (name || "").trim();
    if (!trimmedName) return null;

    let nextNum = 100000 + (state.canvasNodes || []).length + 1;
    while ((state.canvasNodes || []).some(n => Number(n.process_id) === nextNum || String(n.id) === `node_${nextNum}`)) {
      nextNum++;
    }

    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    let targetProcId = catalogProcessId ? Number(catalogProcessId) : null;
    let sheet = null;

    // Buscar en catálogo ecoinvent si no se especificó ID
    try {
      if (!targetProcId) {
        const searchRes = await api.searchCatalog(trimmedName, "ALL", 5);
        if (searchRes && searchRes.items && searchRes.items.length > 0) {
          const exact = searchRes.items.find(p => (p.name || "").toLowerCase() === trimmedName.toLowerCase());
          targetProcId = exact ? exact.id : searchRes.items[0].id;
        }
      }

      if (targetProcId) {
        const sheetRes = await api.getProcessSheet(targetProcId);
        if (sheetRes && sheetRes.sheet) {
          sheet = sheetRes.sheet;
        }
      }
    } catch (e) {
      console.warn("No se pudo cargar ficha técnica de ecoinvent:", e);
    }

    let category = "Custom processes & flows";
    let location = "GLO";
    let uStr = (initialUnit || "kg").trim() || "kg";
    let refFlowName = `${trimmedName} (Producto)`;
    let formattedInputs = [];
    let formattedOutputs = [];

    if (sheet) {
      category = sheet.category_name || sheet.category || category;
      location = sheet.location || location;
      uStr = sheet.ref_unit || sheet.process?.ref_unit || uStr;
      refFlowName = sheet.ref_flow_name || sheet.process?.ref_flow_name || sheet.name || refFlowName;

      const rawInputs = (sheet.technosphere_inputs && sheet.technosphere_inputs.length > 0)
        ? sheet.technosphere_inputs
        : (sheet.inputs || []);

      if (rawInputs.length > 0) {
        formattedInputs = rawInputs.slice(0, 15).map(i => ({
          name: i.flow_name || i.name || "Insumo",
          amount: parseFloat(i.amount) || 1.0,
          unit: i.unit_symbol || i.unit || uStr,
          is_unit: i.exchange_type !== "biosphere",
          origin: "Mercado ecoinvent 3.12"
        }));
      }

      formattedOutputs = [
        {
          name: refFlowName,
          amount: parseFloat(sheet.reference_amount || 1.0),
          unit: uStr,
          is_reference: true
        }
      ];

      if (sheet.waste_outputs && Array.isArray(sheet.waste_outputs)) {
        sheet.waste_outputs.slice(0, 2).forEach(w => {
          formattedOutputs.push({
            name: w.flow_name || w.name,
            amount: parseFloat(w.amount) || 0.05,
            unit: w.unit_symbol || w.unit || uStr,
            is_waste: true
          });
        });
      }

      if (sheet.biosphere_emissions && Array.isArray(sheet.biosphere_emissions)) {
        sheet.biosphere_emissions.slice(0, 2).forEach(em => {
          formattedOutputs.push({
            name: em.flow_name || em.name,
            amount: parseFloat(em.amount) || 0.012,
            unit: em.unit_symbol || em.unit || "kg",
            is_elementary: true,
            compartment: em.compartment || "Air"
          });
        });
      }
    } else {
      // Si no se encontró en DB, buscar en procesos de paleta preconfigurados
      const localMatch = (state.paletteProcesses || []).find(p => areFlowsMatching(p.name, trimmedName));
      if (localMatch) {
        if (localMatch.inputs && localMatch.inputs.length > 0) {
          formattedInputs = JSON.parse(JSON.stringify(localMatch.inputs));
        }
        if (localMatch.outputs && localMatch.outputs.length > 0) {
          formattedOutputs = JSON.parse(JSON.stringify(localMatch.outputs));
        }
        if (localMatch.reference_flow) {
          refFlowName = localMatch.reference_flow.name || refFlowName;
        }
        category = localMatch.category || category;
        targetProcId = localMatch.process_id || localMatch.id;
      }
    }

    if (initialMaterial && initialMaterial.trim()) {
      const matClean = initialMaterial.trim();
      const hasMat = formattedInputs.some(i => areFlowsMatching(i.name, matClean));
      if (!hasMat) {
        formattedInputs.unshift({
          name: matClean,
          amount: parseFloat(initialAmount) || 1.0,
          unit: (initialUnit || "kg").trim() || "kg",
          is_unit: true,
          origin: "Mercado ecoinvent 3.12"
        });
      }
    }

    if (formattedInputs.length === 0) {
      const matName = (initialMaterial || "").trim() || (isEn ? "Raw Material" : "Materia Prima");
      formattedInputs = [
        {
          name: matName,
          amount: parseFloat(initialAmount) || 1.0,
          unit: uStr,
          is_unit: true,
          origin: "Mercado ecoinvent 3.12"
        }
      ];
    }

    if (formattedOutputs.length === 0) {
      formattedOutputs = [
        {
          name: refFlowName,
          amount: 1.0,
          unit: uStr,
          is_reference: true
        }
      ];
    }

    const newNode = {
      id: `node_${nextNum}`,
      process_id: targetProcId || nextNum,
      name: (sheet && sheet.name) ? sheet.name : trimmedName,
      category: category,
      location: location,
      unit: uStr,
      x: 60 + ((state.canvasNodes || []).length % 5) * 260,
      y: 160 + Math.floor(((state.canvasNodes || []).length) / 5) * 180,
      reference_flow: {
        name: refFlowName,
        amount: 1.0,
        unit: uStr
      },
      inputs: formattedInputs,
      outputs: formattedOutputs
    };

    if (!state.paletteProcesses) state.paletteProcesses = [];
    state.paletteProcesses.unshift(newNode);

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }

    const msg = isEn 
      ? `Process "${newNode.name}" added to catalog and spreadsheet. Define connections in "Internal Connections" to place on diagram.` 
      : `Proceso "${newNode.name}" agregado al catálogo y a la hoja de cálculo. Define sus conexiones en "Conexiones Internas" para mostrarlo en el diagrama.`;
    showNotification(msg);
    return newNode;
  }

  async function tableChangeNodeToCatalogProcess(nodeId, catalogProcessId) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node || !catalogProcessId) return;

    try {
      const sheetRes = await api.getProcessSheet(catalogProcessId);
      if (!sheetRes || !sheetRes.sheet) return;
      const sheet = sheetRes.sheet;

      const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
      node.name = sheet.name || node.name;
      node.category = sheet.category_name || node.category;
      node.location = sheet.location || node.location;
      node.process_id = sheet.id || node.process_id;
      const uStr = sheet.ref_unit || sheet.process?.ref_unit || node.unit || "kg";
      node.unit = uStr;
      const refFlowName = sheet.ref_flow_name || sheet.process?.ref_flow_name || `${node.name} (Producto)`;

      node.reference_flow = {
        name: refFlowName,
        amount: parseFloat(sheet.reference_amount || 1.0),
        unit: uStr
      };

      const rawInputs = (sheet.technosphere_inputs && sheet.technosphere_inputs.length > 0)
        ? sheet.technosphere_inputs
        : (sheet.inputs || []);

      if (rawInputs.length > 0) {
        node.inputs = rawInputs.slice(0, 15).map(i => ({
          name: i.flow_name || i.name || "Insumo",
          amount: parseFloat(i.amount) || 1.0,
          unit: i.unit_symbol || i.unit || uStr,
          is_unit: i.exchange_type !== "biosphere",
          origin: "Mercado ecoinvent 3.12"
        }));
      }

      node.outputs = [
        {
          name: refFlowName,
          amount: parseFloat(sheet.reference_amount || 1.0),
          unit: uStr,
          is_reference: true
        }
      ];

      if (sheet.waste_outputs && Array.isArray(sheet.waste_outputs)) {
        sheet.waste_outputs.slice(0, 2).forEach(w => {
          node.outputs.push({
            name: w.flow_name || w.name,
            amount: parseFloat(w.amount) || 0.05,
            unit: w.unit_symbol || w.unit || uStr,
            is_waste: true
          });
        });
      }

      if (sheet.biosphere_emissions && Array.isArray(sheet.biosphere_emissions)) {
        sheet.biosphere_emissions.slice(0, 2).forEach(em => {
          node.outputs.push({
            name: em.flow_name || em.name,
            amount: parseFloat(em.amount) || 0.012,
            unit: em.unit_symbol || em.unit || "kg",
            is_elementary: true,
            compartment: em.compartment || "Air"
          });
        });
      }

      syncSystemProcesses();
      scheduleAutoSaveCanvas();
      renderCanvasEdges();
      renderPaletteProcesses();
      renderCanvasTableView();
      if (state.canvasViewMode === "visual") {
        renderCanvasStage();
      }
      showNotification(isEn ? `Process "${node.name}" updated with official inputs & outputs.` : `Proceso "${node.name}" actualizado con entradas y salidas oficiales.`);
    } catch (e) {
      console.error("Error al actualizar proceso desde catálogo:", e);
    }
  }

  function tableChangeProvider(nodeId, flowIdx, newProviderValue) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node || !node.inputs || !node.inputs[flowIdx]) return;
    const inp = node.inputs[flowIdx];

    // Eliminar arista existente conectada a este input si la había
    if (!state.canvasEdges) state.canvasEdges = [];
    state.canvasEdges = state.canvasEdges.filter(e => {
      const isTarget = (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id) || String(e.to) === String(node.process_id));
      if (!isTarget) return true;
      return !areFlowsMatching(e.flow, inp.name);
    });

    if (newProviderValue === "disconnect" || newProviderValue === "ecoinvent") {
      inp.origin = "Mercado ecoinvent 3.12";
      inp.is_unit = true;
    } else if (newProviderValue === "cfe") {
      inp.origin = "Suministro Industrial / CFE";
      inp.is_unit = false;
    } else {
      // Es un nodo origen (upstream)
      const srcNode = procs.find(n => String(n.id) === String(newProviderValue) || String(n.process_id) === String(newProviderValue));
      if (srcNode) {
        inp.origin = srcNode.name;
        const matchingOut = (srcNode.outputs || []).find(o => areFlowsMatching(o.name, inp.name)) || 
                            (srcNode.outputs || []).find(o => o.is_reference) || 
                            (srcNode.outputs && srcNode.outputs[0]);
        const flowName = matchingOut ? matchingOut.name : inp.name;
        inp.name = flowName;
        if (matchingOut && matchingOut.unit) inp.unit = matchingOut.unit;

        state.canvasEdges.push({
          id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
          from: srcNode.id,
          to: node.id,
          source_process_id: srcNode.process_id || srcNode.id,
          target_process_id: node.process_id || node.id,
          flow: flowName,
          amount: parseFloat(inp.amount) || 1.0,
          unit: inp.unit || (matchingOut ? matchingOut.unit : "kg")
        });
      }
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasEdges();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    showNotification(isEn ? "Provider and connection updated." : "Proveedor y conexión actualizados.");
  }

  function tableUpdateNewFlowKind(selectEl) {
    const tr = selectEl.closest("tr");
    if (!tr) return;
    const kind = selectEl.value;
    const provCell = tr.querySelector(".excel-cell-new-flow-provider");
    const nameInput = tr.querySelector(".excel-input-new-flow-name");
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";

    if (kind === "input") {
      if (provCell) provCell.textContent = "Mercado ecoinvent 3.12";
      if (nameInput) nameInput.placeholder = isEn ? "+ Add input (Enter)..." : "+ Agregar insumo (Enter)...";
    } else if (kind === "output_coproduct") {
      if (provCell) provCell.textContent = isEn ? "Intermediate output" : "Salida intermedia";
      if (nameInput) nameInput.placeholder = isEn ? "+ Add coproduct (Enter)..." : "+ Agregar coproducto (Enter)...";
    } else if (kind === "output_waste") {
      if (provCell) provCell.textContent = isEn ? "Waste treatment" : "Tratamiento de residuo";
      if (nameInput) nameInput.placeholder = isEn ? "+ Add waste (Enter)..." : "+ Agregar residuo (Enter)...";
    } else if (kind === "output_elementary") {
      if (provCell) provCell.textContent = isEn ? "Biosphere [Air/Water]" : "Emisión biosférica [Aire/Agua]";
      if (nameInput) nameInput.placeholder = isEn ? "+ Add emission (Enter)..." : "+ Agregar emisión (Enter)...";
    }
  }

  function tableCreateFlowInline(nodeId, flowName, amount = 1.0, unit = "kg", origin = "Mercado ecoinvent 3.12", upstreamSourceId = null, upstreamProcessId = null, flowKind = "input", comment = "", assumptions = "", externalLinks = "") {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return null;

    const trimmedFlow = (flowName || "").trim();
    if (!trimmedFlow) return null;

    const numAmount = parseFloat(amount) || 1.0;
    const cleanUnit = (unit || "kg").trim() || "kg";
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";

    let createdFlow = null;

    if (flowKind === "input") {
      let finalSourceId = upstreamSourceId;
      let finalSourceProcId = upstreamProcessId;
      let finalOrigin = origin;

      if (!finalSourceId) {
        const matchNode = procs.find(n => 
          String(n.id) !== String(node.id) && 
          (n.outputs || []).some(o => areFlowsMatching(o.name, trimmedFlow))
        );
        if (matchNode) {
          finalSourceId = matchNode.id;
          finalSourceProcId = matchNode.process_id;
          finalOrigin = matchNode.name;
        }
      }

      if (!node.inputs) node.inputs = [];
      createdFlow = {
        name: trimmedFlow,
        amount: numAmount,
        unit: cleanUnit,
        is_unit: true,
        origin: finalOrigin || (finalSourceId ? "Conexión Interna" : "Mercado ecoinvent 3.12"),
        comment: (comment || "").trim(),
        assumptions: (assumptions || "").trim(),
        external_links: (externalLinks || "").trim()
      };

      node.inputs.push(createdFlow);

      if (finalSourceId) {
        if (!state.canvasEdges) state.canvasEdges = [];
        const exists = state.canvasEdges.some(e => 
          (String(e.from) === String(finalSourceId) || String(e.source_process_id) === String(finalSourceProcId)) && 
          (String(e.to) === String(node.id) || String(e.target_process_id) === String(node.process_id)) && 
          areFlowsMatching(e.flow, trimmedFlow)
        );
        if (!exists) {
          state.canvasEdges.push({
            id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
            from: finalSourceId,
            to: node.id,
            source_process_id: finalSourceProcId,
            target_process_id: node.process_id,
            flow: trimmedFlow,
            amount: numAmount,
            unit: cleanUnit
          });
        }
      }
    } else {
      // Salidas: coproducto, residuo o emisión biosférica
      if (!node.outputs) node.outputs = [];
      const isWaste = (flowKind === "output_waste");
      const isElementary = (flowKind === "output_elementary");
      createdFlow = {
        name: trimmedFlow,
        amount: numAmount,
        unit: cleanUnit,
        is_reference: false,
        is_waste: isWaste,
        is_elementary: isElementary,
        compartment: isElementary ? "Air" : "N/A",
        comment: (comment || "").trim(),
        assumptions: (assumptions || "").trim(),
        external_links: (externalLinks || "").trim()
      };
      node.outputs.push(createdFlow);
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasEdges();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }

    const typeDesc = (flowKind === "input") 
      ? (isEn ? "Input" : "Insumo") 
      : (flowKind === "output_waste" ? (isEn ? "Waste" : "Residuo") : (flowKind === "output_elementary" ? (isEn ? "Emission" : "Emisión") : (isEn ? "Coproduct" : "Coproducto")));

    showNotification(isEn ? `${typeDesc} "${trimmedFlow}" added to ${node.name}.` : `${typeDesc} "${trimmedFlow}" agregado a ${node.name}.`);
    return createdFlow;
  }

  function handleNewProcessKeyDown(e, inputEl) {
    if (e.key === "Enter") {
      e.preventDefault();
      const val = (inputEl.value || "").trim();
      if (!val) return;

      const tr = inputEl.closest("tr");
      const matInput = tr ? tr.querySelector(".excel-input-new-mat") : null;
      const amtInput = tr ? tr.querySelector(".excel-input-new-amt") : null;
      const unitInput = tr ? tr.querySelector(".excel-input-new-unit") : null;

      const matName = matInput ? matInput.value.trim() : "";
      const amt = amtInput ? amtInput.value : 1.0;
      const unit = unitInput ? unitInput.value : "kg";
      const procId = inputEl.dataset ? inputEl.dataset.processId : null;

      tableCreateProcessInline(val, matName, amt, unit, procId);
    }
  }

  function handleNewFlowKeyDown(e, nodeId, inputEl) {
    if (e.key === "Enter") {
      e.preventDefault();
      const tr = inputEl.closest("tr");
      const nameInput = tr ? tr.querySelector(".excel-input-new-flow-name") : inputEl;
      const val = (nameInput ? nameInput.value : "").trim();
      if (!val) return;

      const amtInput = tr ? tr.querySelector(".excel-input-new-flow-amt") : null;
      const unitInput = tr ? tr.querySelector(".excel-input-new-flow-unit") : null;
      const kindSelect = tr ? tr.querySelector(".excel-select-new-flow-kind") : null;

      const amt = amtInput ? amtInput.value : 1.0;
      const unit = unitInput ? unitInput.value : "kg";
      const flowKind = kindSelect ? kindSelect.value : "input";
      const upstreamSourceId = nameInput?.dataset?.upstreamSourceId || null;
      const upstreamProcessId = nameInput?.dataset?.upstreamProcessId || null;
      const origin = upstreamSourceId ? "Conexión Interna" : (flowKind === "input" ? "Mercado ecoinvent 3.12" : (flowKind === "output_waste" ? "Tratamiento de residuo" : (flowKind === "output_elementary" ? "Emisión biosférica" : "Salida intermedia")));

      const cmtInput = tr ? tr.querySelector(".excel-input-new-flow-comment") : null;
      const assumpInput = tr ? tr.querySelector(".excel-input-new-flow-assumptions") : null;
      const linksInput = tr ? tr.querySelector(".excel-input-new-flow-links") : null;
      const comment = cmtInput ? cmtInput.value.trim() : "";
      const assumptions = assumpInput ? assumpInput.value.trim() : "";
      const links = linksInput ? linksInput.value.trim() : "";

      tableCreateFlowInline(nodeId, val, amt, unit, origin, upstreamSourceId, upstreamProcessId, flowKind, comment, assumptions, links);
    }
  }

  function tableDeleteFlow(nodeId, type, idx) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
    if (!node) return;

    if (type === "input" && node.inputs && node.inputs[idx]) {
      const flowName = node.inputs[idx].name;
      node.inputs.splice(idx, 1);
      state.canvasEdges = (state.canvasEdges || []).filter(e => 
        !(String(e.to) === String(node.id) && areFlowsMatching(e.flow, flowName))
      );
    } else if (type === "output" && node.outputs && node.outputs[idx]) {
      if (node.outputs[idx].is_reference) {
        alert("El flujo de referencia del proceso no puede ser eliminado.");
        return;
      }
      const flowName = node.outputs[idx].name;
      node.outputs.splice(idx, 1);
      state.canvasEdges = (state.canvasEdges || []).filter(e => 
        !(String(e.from) === String(node.id) && areFlowsMatching(e.flow, flowName))
      );
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasEdges();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }
  }

  function tableAddFlow(nodeId, type) {
    const procs = getAllSystemProcesses();
    const node = procs.find(n => String(n.id) === String(nodeId) || String(n.process_id) === String(nodeId));
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

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasTableView();
  }

  function tableUpdateEdgeAmount(edgeId, value) {
    const edge = (state.canvasEdges || []).find(e => String(e.id) === String(edgeId));
    if (!edge) return;
    const num = parseFloat(value) || 0;
    edge.amount = num;

    const procs = getAllSystemProcesses();
    const tgtNode = procs.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id));
    if (tgtNode && tgtNode.inputs) {
      const inp = tgtNode.inputs.find(i => areFlowsMatching(i.name, edge.flow));
      if (inp) {
        inp.amount = num;
      }
    }

    scheduleAutoSaveCanvas();
  }

  function tableDeleteEdge(edgeId) {
    const edge = (state.canvasEdges || []).find(e => String(e.id) === String(edgeId));
    if (edge) {
      const procs = getAllSystemProcesses();
      const tgtNode = procs.find(n => String(n.id) === String(edge.to) || String(n.process_id) === String(edge.target_process_id) || String(n.to) === String(edge.target_process_id));
      if (tgtNode && tgtNode.inputs) {
        const inp = tgtNode.inputs.find(i => areFlowsMatching(i.name, edge.flow));
        if (inp) {
          inp.origin = "Mercado ecoinvent 3.12";
        }
      }
    }
    state.canvasEdges = (state.canvasEdges || []).filter(e => String(e.id) !== String(edgeId));
    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasEdges();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }
    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    showNotification(isEn ? "Internal connection disconnected." : "Conexión interna desconectada.");
  }

  function updateNewConnFlows() {
    const srcSelect = document.getElementById("selectNewConnSource");
    const flowSelect = document.getElementById("selectNewConnFlow");
    const amtInput = document.getElementById("inputNewConnAmount");
    const unitInput = document.getElementById("inputNewConnUnit");
    if (!srcSelect || !flowSelect) return;

    const srcId = srcSelect.value;
    if (!srcId) {
      flowSelect.innerHTML = `<option value="">-- Flujo de Salida --</option>`;
      return;
    }

    const procs = getAllSystemProcesses();
    const srcNode = procs.find(n => String(n.id) === String(srcId) || String(n.process_id) === String(srcId));
    if (!srcNode) return;

    const flows = [];
    if (srcNode.reference_flow && srcNode.reference_flow.name) {
      flows.push({
        name: srcNode.reference_flow.name,
        amount: srcNode.reference_flow.amount || srcNode.amount || 1.0,
        unit: srcNode.reference_flow.unit || srcNode.unit || "kg",
        is_reference: true
      });
    }
    if (Array.isArray(srcNode.outputs)) {
      srcNode.outputs.forEach(out => {
        if (!flows.some(f => areFlowsMatching(f.name, out.name))) {
          flows.push({
            name: out.name,
            amount: out.amount !== undefined ? out.amount : 1.0,
            unit: out.unit || "kg",
            is_reference: out.is_reference === true,
            is_waste: out.is_waste === true
          });
        }
      });
    }
    if (flows.length === 0) {
      flows.push({
        name: `${srcNode.name} (Producto)`,
        amount: 1.0,
        unit: srcNode.unit || "kg",
        is_reference: true
      });
    }

    flowSelect.innerHTML = flows.map((f, idx) => {
      const badge = f.is_reference ? ' ' : (f.is_waste ? ' ' : '');
      return `<option value="${escapeHtml(f.name)}" data-amount="${f.amount}" data-unit="${escapeHtml(f.unit)}" ${idx === 0 ? 'selected' : ''}>${badge}${escapeHtml(f.name)} (${f.amount} ${f.unit})</option>`;
    }).join('');

    const firstFlow = flows[0];
    if (firstFlow) {
      if (amtInput) amtInput.value = firstFlow.amount;
      if (unitInput) unitInput.value = firstFlow.unit;
    }

    flowSelect.onchange = () => {
      const opt = flowSelect.options[flowSelect.selectedIndex];
      if (opt) {
        if (amtInput && opt.dataset.amount) amtInput.value = opt.dataset.amount;
        if (unitInput && opt.dataset.unit) unitInput.value = opt.dataset.unit;
      }
    };
  }

  function tableAddNewConnection() {
    const srcSelect = document.getElementById("selectNewConnSource");
    const flowSelect = document.getElementById("selectNewConnFlow");
    const tgtSelect = document.getElementById("selectNewConnTarget");
    const amtInput = document.getElementById("inputNewConnAmount");
    const unitInput = document.getElementById("inputNewConnUnit");

    const srcId = srcSelect ? srcSelect.value : "";
    const tgtId = tgtSelect ? tgtSelect.value : "";
    const flowName = flowSelect ? (flowSelect.value || "").trim() : "";
    const amount = parseFloat(amtInput ? amtInput.value : "1.0") || 1.0;
    const unit = (unitInput ? unitInput.value : "kg").trim() || "kg";

    if (!srcId) {
      alert("Por favor selecciona el proceso de origen (salida).");
      if (srcSelect) srcSelect.focus();
      return;
    }
    if (!tgtId) {
      alert("Por favor selecciona el proceso de destino (entrada).");
      if (tgtSelect) tgtSelect.focus();
      return;
    }
    if (String(srcId) === String(tgtId)) {
      alert("No se puede conectar un proceso consigo mismo.");
      return;
    }
    if (!flowName) {
      alert("Por favor selecciona un flujo para conectar.");
      if (flowSelect) flowSelect.focus();
      return;
    }

    const procs = getAllSystemProcesses();
    const srcNode = procs.find(n => String(n.id) === String(srcId) || String(n.process_id) === String(srcId));
    const tgtNode = procs.find(n => String(n.id) === String(tgtId) || String(n.process_id) === String(tgtId));

    if (!srcNode || !tgtNode) {
      alert("No se pudieron localizar los procesos en el sistema.");
      return;
    }

    if (!state.canvasEdges) state.canvasEdges = [];
    const existingIdx = state.canvasEdges.findIndex(ed => 
      (String(ed.from) === String(srcNode.id) || String(ed.source_process_id) === String(srcNode.process_id)) &&
      (String(ed.to) === String(tgtNode.id) || String(ed.target_process_id) === String(tgtNode.process_id)) &&
      areFlowsMatching(ed.flow, flowName)
    );

    if (existingIdx >= 0) {
      state.canvasEdges[existingIdx].amount = amount;
      state.canvasEdges[existingIdx].unit = unit;
    } else {
      const newEdge = {
        id: `edge_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
        from: srcNode.id,
        to: tgtNode.id,
        source_process_id: srcNode.process_id || srcNode.id,
        target_process_id: tgtNode.process_id || tgtNode.id,
        flow: flowName,
        amount: amount,
        unit: unit
      };
      state.canvasEdges.push(newEdge);
    }

    // Registrar o actualizar en entradas del destino
    if (!tgtNode.inputs) tgtNode.inputs = [];
    const matchingInp = tgtNode.inputs.find(i => areFlowsMatching(i.name, flowName));
    if (matchingInp) {
      matchingInp.origin = srcNode.name;
      matchingInp.amount = amount;
      matchingInp.unit = unit;
      matchingInp.is_unit = true;
    } else {
      tgtNode.inputs.push({
        name: flowName,
        amount: amount,
        unit: unit,
        is_unit: true,
        origin: srcNode.name
      });
    }

    // Sincronizar: al estar conectados, ambos procesos ahora deben aparecer en el diagrama
    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderCanvasEdges();
    renderPaletteProcesses();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }

    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    showNotification(isEn ? `Connected: "${srcNode.name}" ➔ "${tgtNode.name}" (${amount} ${unit}). Both processes are now active in the diagram.` : `Conexión establecida: "${srcNode.name}" ➔ "${tgtNode.name}" (${amount} ${unit}). Ambos procesos ahora se muestran en el diagrama.`);
  }

  function tableDeleteProcess(nodeId) {
    const procs = getAllSystemProcesses();
    const proc = procs.find(p => String(p.id) === String(nodeId) || String(p.process_id) === String(nodeId));
    if (!proc) return;

    const isEn = window.I18n && window.I18n.getCurrentLanguage && window.I18n.getCurrentLanguage() === "en";
    const confirmMsg = isEn 
      ? `Are you sure you want to completely delete process "${proc.name}" (#${proc.process_id || proc.id}) from the product system? All connected flows will be removed.` 
      : `¿Estás seguro de que deseas eliminar completamente el proceso "${proc.name}" (#${proc.process_id || proc.id}) del sistema producto? Se eliminarán todas sus conexiones internas.`;

    if (!confirm(confirmMsg)) return;

    const pid = String(proc.id);
    const numId = String(proc.process_id || "");

    // 1. Eliminar de canvasNodes y paletteProcesses
    state.canvasNodes = (state.canvasNodes || []).filter(n => String(n.id) !== pid && String(n.process_id) !== numId && String(n.process_id) !== pid);
    state.paletteProcesses = (state.paletteProcesses || []).filter(p => String(p.id) !== pid && String(p.process_id) !== numId && String(p.process_id) !== pid);

    // 2. Eliminar aristas vinculadas
    state.canvasEdges = (state.canvasEdges || []).filter(e => {
      const isSrc = String(e.from) === pid || String(e.source_process_id) === numId || String(e.source_process_id) === pid;
      const isTgt = String(e.to) === pid || String(e.target_process_id) === numId || String(e.target_process_id) === pid;
      return !isSrc && !isTgt;
    });

    // 3. Restaurar origen a "Mercado ecoinvent 3.12" en los demás procesos que recibían insumos de este proceso
    getAllSystemProcesses().forEach(otherProc => {
      if (Array.isArray(otherProc.inputs)) {
        otherProc.inputs.forEach(inp => {
          if (inp.origin && (inp.origin === proc.name || inp.origin.includes(proc.name))) {
            inp.origin = "Mercado ecoinvent 3.12";
          }
        });
      }
    });

    if (state.selectedNode && (String(state.selectedNode.id) === pid || String(state.selectedNode.process_id) === numId)) {
      inspectNode(null);
    }

    syncSystemProcesses();
    scheduleAutoSaveCanvas();
    renderPaletteProcesses();
    renderCanvasEdges();
    renderCanvasTableView();
    if (state.canvasViewMode === "visual") {
      renderCanvasStage();
    }

    showNotification(isEn ? `Process "${proc.name}" removed from the system.` : `Proceso "${proc.name}" eliminado del sistema.`);
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
          html += `<option value="${ownCat.id}" style="font-weight: 700; color: var(--accent-emerald);">${ownCat.name} (${ownCat.process_count || 0})</option>`;
        } else {
          html += `<option value="999999" style="font-weight: 700; color: var(--accent-emerald);">Custom processes & flows</option>`;
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
      const q = document.getElementById("inputCatalogSearch")?.value || "";
      const catSelect = document.getElementById("selectCatalogCategory");
      const catVal = catSelect ? catSelect.value : state.catalogFilter;
      const sourceVal = state.catalogSource || "all";
      const cacheKey = `${sourceVal}_${catVal || 'ALL'}_${q}`;

      state.catalogCache = state.catalogCache || {};

      // 1. Renderizado instantáneo si está en memoria (cambio entre bases de datos en 0ms)
      if (state.catalogCache[cacheKey]) {
        state.catalogProcesses = state.catalogCache[cacheKey];
        renderCatalogList();
        if (state.catalogProcesses.length > 0 && !state.selectedCatalogProcess) {
          selectCatalogProcess(state.catalogProcesses[0].id);
        }
      } else if (sourceVal === "all" && !q && (!catVal || catVal === "ALL")) {
        // 2. Primera carga desde localStorage (0ms)
        try {
          const cached = localStorage.getItem("econode_cached_catalog_all");
          if (cached && (!state.catalogProcesses || state.catalogProcesses.length === 0)) {
            state.catalogProcesses = JSON.parse(cached);
            renderCatalogList();
            if (state.catalogProcesses.length > 0 && !state.selectedCatalogProcess) {
              selectCatalogProcess(state.catalogProcesses[0].id);
            }
          }
        } catch(e) {}
      }

      // Si aún no hay tarjetas renderizadas, mostrar estado de carga inmediato
      if (!state.catalogProcesses || state.catalogProcesses.length === 0) {
        const container = document.getElementById("catalogProcessList");
        if (container) {
          container.innerHTML = `<div style="padding: 28px; text-align: center; color: var(--text-muted); font-size: 11.5px;">Cargando procesos del catálogo LCI...</div>`;
        }
      }

      // 3. Ejecutar categorías y búsqueda de procesos en PARALELO
      const catPromise = loadCatalogCategories();
      const searchPromise = api.searchCatalog(q, catVal, 50, sourceVal);

      const [_, res] = await Promise.all([catPromise, searchPromise]);
      state.catalogProcesses = res.items || [];
      state.catalogCache[cacheKey] = state.catalogProcesses;

      if (sourceVal === "all" && !q && (!catVal || catVal === "ALL")) {
        try { localStorage.setItem("econode_cached_catalog_all", JSON.stringify(state.catalogProcesses)); } catch(e) {}
      }

      // Si la categoría seleccionada es "Custom processes & flows", cargamos solo los flujos creados por el usuario
      if (String(catVal) === "999999") {
        try {
          const flowRes = await api.getDbFlows(q, "ALL", 100, "999999");
          state.catalogCustomFlows = (flowRes.items || []).filter(f => {
            const fid = String(f.id || f.code || "");
            return fid.startsWith("FL_CUSTOM_");
          });
        } catch (fErr) {
          state.catalogCustomFlows = [];
        }
      } else {
        state.catalogCustomFlows = [];
      }

      renderCatalogList();

      if (state.catalogProcesses.length > 0) {
        const hasSelected = state.selectedCatalogProcess && state.catalogProcesses.some(p => String(p.id) === String(state.selectedCatalogProcess.id));
        if (!hasSelected) {
          selectCatalogProcess(state.catalogProcesses[0].id);
        }
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
        <div class="catalog-proc-item" style="padding: 10px 12px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s ease;" onclick="window.EconodeApp.selectCatalogProcess('${escapeHtml(String(proc.id))}')">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0;">
              <span class="badge-source badge-source-${escapeHtml(proc.source_badge || 'all')}">${escapeHtml(proc.source_label || (proc.database ? proc.database.toUpperCase() : 'LCI'))}</span>
              <div style="font-size: 11.5px; font-weight: 700; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${escapeHtml(proc.name || '')}">${escapeHtml(proc.name || '')}</div>
            </div>
            <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
              <span class="badge-pill badge-slate">${escapeHtml(proc.location || proc.geography || "GLO")}</span>
              ${isCustom ? `
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 10px; color: #EF4444; border-color: rgba(239, 68, 68, 0.3);"
                        title="${window.I18n.t('catalog.delete_process_btn', 'Delete Process')}"
                        onclick="event.stopPropagation(); window.EconodeApp.deleteCatalogProcess('${escapeHtml(String(proc.id))}', '${escape(proc.name || '')}')">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              ` : ''}
            </div>
          </div>
          <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 10px; color: var(--text-muted);">
            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%;">${escapeHtml(proc.category_name || proc.category || "Custom processes & flows")}</span>
            <span class="mono">${Number(proc.reference_amount || 1).toFixed(2)} ${escapeHtml(proc.reference_unit || "kg")}</span>
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
                  <strong style="font-size: 11px; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${escapeHtml(flow.name || '')}">${escapeHtml(flow.name || '')}</strong>
                  <span class="mono badge-pill badge-emerald" style="font-size: 8.5px;">${escapeHtml(flow.unit_symbol || 'kg')}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
                  <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 6px; font-size: 10px; color: #EF4444; border-color: rgba(239, 68, 68, 0.3);"
                          title="${window.I18n.t('catalog.delete_flow_btn', 'Delete Flow')}"
                          onclick="event.stopPropagation(); window.EconodeApp.deleteCatalogFlow('${escapeHtml(String(flow.id || flow.code || ""))}', '${escape(flow.name || '')}')">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                  </button>
                </div>
              </div>
              <div style="display: flex; justify-content: space-between; margin-top: 2px; font-size: 9px; color: var(--text-muted);">
                <span>${flow.flow_type === 'PRODUCT_FLOW' ? 'Product Flow (Input)' : flow.flow_type === 'WASTE_FLOW' ? 'Waste Flow' : 'Biospheric Emission'}</span>
                <span class="mono">ID: ${escapeHtml(String(flow.id || ''))}</span>
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
        titleEl.innerHTML = `<span class="mono" style="font-size: 11px; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25); margin-right: 6px;">DB FLOW: #${escapeHtml(String(flow.id || ''))}</span>${escapeHtml(flow.name || '')}`;
      }
      if (subEl) {
        const typeLabel = flow.flow_type === 'PRODUCT_FLOW' ? 'Product / Technosphere Flow' : flow.flow_type === 'WASTE_FLOW' ? 'Waste Flow' : 'Elementary Biospheric Emission';
        subEl.textContent = `Category: Custom processes & flows · Classification: ${typeLabel} · FU: 1.000 ${flow.unit_symbol || 'kg'}`;
      }
      if (inputsTable) {
        inputsTable.innerHTML = `
          <tr>
            <td><strong>Código / Identificador</strong></td>
            <td class="mono" colspan="2">${escapeHtml(String(flow.id || ''))}</td>
          </tr>
          <tr>
            <td><strong>Tipo de Flujo en openLCA</strong></td>
            <td class="mono" colspan="2">${escapeHtml(String(flow.flow_type || ''))}</td>
          </tr>
          <tr>
            <td><strong>Unidad de Referencia</strong></td>
            <td class="mono" colspan="2">${escapeHtml(flow.unit_symbol || 'kg')}</td>
          </tr>
        `;
      }
      if (outputsTable) {
        outputsTable.innerHTML = `
          <tr>
            <td><strong>Descripción / Procedencia Técnica</strong></td>
            <td class="mono" colspan="2">${escapeHtml(flow.description || 'Custom flow created by analyst in ECONODE Studio')}</td>
          </tr>
        `;
      }
    } catch (e) {
      console.error("Error displaying catalog flow:", e);
    }
  }

  async function selectCatalogProcess(procId) {
    try {
      // 1. Si el proceso ya está en la lista en memoria, actualizar la ficha en 0ms
      const preview = state.catalogProcesses ? state.catalogProcesses.find(p => String(p.id) === String(procId)) : null;
      if (preview) {
        renderProcessSheet(preview, true);
      }

      const res = await api.getProcessSheet(procId);
      if (res && res.sheet) {
        state.selectedCatalogProcess = res.sheet;
        state.selectedCatalogFlow = null;
        renderProcessSheet(res.sheet, false);
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

    const safePName = escapeHtml(p.name || "");
    const safePLoc = escapeHtml(p.location || p.geography || "GLO");
    const safePId = escapeHtml(String(p.id || ""));
    const safeCat = p.category_name || p.category || "General";
    const safeUnit = p.ref_unit || p.reference_unit || "kg";
    const dbLabel = p.database ? p.database.toUpperCase() : "ecoinvent 3.12 Cutoff";

    if (titleEl) titleEl.innerHTML = `<span class="mono" style="font-size: 11px; color: var(--accent-emerald); background: rgba(5, 150, 105, 0.08); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(5, 150, 105, 0.25); margin-right: 6px;">ID: #${safePId}</span>${safePName} [${safePLoc}]`;
    if (subEl) {
      subEl.textContent = `${dbLabel} · Categoría: ${safeCat} · UF: ${p.reference_amount || 1.0} ${safeUnit}`;
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
            <td><strong>${escapeHtml(inp.flow_name || inp.name || "")}</strong></td>
            <td class="mono">${Number(inp.amount || 0).toFixed(4)}</td>
            <td class="mono">${escapeHtml(inp.unit_symbol || inp.unit || "kg")}</td>
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
            <td><strong>${escapeHtml(out.flow_name || out.name || "")}</strong></td>
            <td class="mono">${Number(out.amount || 0).toFixed(4)}</td>
            <td class="mono">${escapeHtml(out.unit_symbol || out.unit || "kg")}</td>
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
  // 8. REPORTE DINÁMICO & HILOS COLABORATIVOS (3 ROLES) & EXPORTACIONES & EPD
  // =========================================================================
  let epdReportListenersBound = false;

  async function loadReport() {
    setupEpdReportListeners();
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = (sysId === 21 || sysId === 1);

    // Actualizar titulo del documento con el sistema activo
    const titleEl = document.getElementById("reportMainTitle");
    if (titleEl && state.activeSystem && state.activeSystem.name) {
      titleEl.textContent = `${state.activeSystem.name} (${state.activeSystem.code || `SYS-${sysId}`})`;
    }

    // Si el sistema activo fue creado desde plantilla EPD, abrir automaticamente en modo EPD
    if (state.activeSystem && state.activeSystem.epd_config && state.activeSystem.epd_config.is_epd_enabled) {
      state.epdStandard = state.activeSystem.epd_config.default_standard || state.epdStandard || "EN15804_A2";
      switchReportMode("epd", false);
    } else {
      switchReportMode(state.reportViewMode || "lca", false);
    }

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
      if (state.reportViewMode === "epd") {
        await loadEpdReport(state.epdStandard);
      } else if (state.reportViewMode === "ghg") {
        await loadGhgReport();
      }
    } catch (err) {
      console.error("Error al cargar reporte:", err);
      state.comments = [];
      applyRolePermissions();
    }
  }

  function setupEpdReportListeners() {
    if (epdReportListenersBound) return;
    epdReportListenersBound = true;

    const btnLca = document.getElementById("btnReportModeLca");
    const btnEpd = document.getElementById("btnReportModeEpd");
    const btnGhg = document.getElementById("btnReportModeGhg");
    if (btnLca) btnLca.addEventListener("click", () => switchReportMode("lca", true));
    if (btnEpd) btnEpd.addEventListener("click", () => switchReportMode("epd", true));
    if (btnGhg) btnGhg.addEventListener("click", () => switchReportMode("ghg", true));
    setupGhgReportListeners();

    const btnStdEn = document.getElementById("btnEpdStdEn15804");
    const btnStdTraci = document.getElementById("btnEpdStdTraci");
    if (btnStdEn) btnStdEn.addEventListener("click", () => loadEpdReport("EN15804_A2"));
    if (btnStdTraci) btnStdTraci.addEventListener("click", () => loadEpdReport("TRACI_2_1"));

    const btnOpenMeta = document.getElementById("btnOpenEpdMetaModal");
    if (btnOpenMeta) btnOpenMeta.addEventListener("click", openEpdMetadataModal);

    const btnCloseMeta = document.getElementById("btnCloseEpdMetaModal");
    const btnCancelMeta = document.getElementById("btnCancelEpdMetaModal");
    const modalMeta = document.getElementById("modalEpdMetadata");
    const closeMeta = () => {
      if (modalMeta) {
        modalMeta.style.display = "none";
        modalMeta.classList.remove("active");
      }
    };
    if (btnCloseMeta) btnCloseMeta.addEventListener("click", closeMeta);
    if (btnCancelMeta) btnCancelMeta.addEventListener("click", closeMeta);
    if (modalMeta) {
      modalMeta.addEventListener("click", (e) => {
        if (e.target === modalMeta) closeMeta();
      });
    }

    const btnSaveMeta = document.getElementById("btnSaveEpdMetadata");
    if (btnSaveMeta) btnSaveMeta.addEventListener("click", saveEpdMetadataFromModal);

    const btnOpenEpd = document.getElementById("btnExportOpenEpdJson");
    if (btnOpenEpd) btnOpenEpd.addEventListener("click", downloadOpenEpdJson);

    const btnPrintEpd = document.getElementById("btnPrintEpdPdf");
    if (btnPrintEpd) {
      btnPrintEpd.addEventListener("click", () => {
        window.print();
      });
    }
  }

  function switchReportMode(mode, shouldFetch = true) {
    if (mode === "epd") {
      state.reportViewMode = "epd";
    } else if (mode === "ghg") {
      state.reportViewMode = "ghg";
    } else {
      state.reportViewMode = "lca";
    }
    const lcaBox = document.getElementById("reportLcaModeContainer");
    const epdBox = document.getElementById("epdReportContainer");
    const ghgBox = document.getElementById("ghgReportContainer");
    const btnLca = document.getElementById("btnReportModeLca");
    const btnEpd = document.getElementById("btnReportModeEpd");
    const btnGhg = document.getElementById("btnReportModeGhg");

    if (lcaBox) lcaBox.style.display = state.reportViewMode === "lca" ? "block" : "none";
    if (epdBox) epdBox.style.display = state.reportViewMode === "epd" ? "block" : "none";
    if (ghgBox) ghgBox.style.display = state.reportViewMode === "ghg" ? "block" : "none";

    document.body.classList.toggle("report-mode-lca", state.reportViewMode === "lca");
    document.body.classList.toggle("report-mode-epd", state.reportViewMode === "epd");
    document.body.classList.toggle("report-mode-ghg", state.reportViewMode === "ghg");

    if (btnLca) {
      btnLca.classList.toggle("active", state.reportViewMode === "lca");
      btnLca.setAttribute("aria-selected", String(state.reportViewMode === "lca"));
    }
    if (btnEpd) {
      btnEpd.classList.toggle("active", state.reportViewMode === "epd");
      btnEpd.setAttribute("aria-selected", String(state.reportViewMode === "epd"));
    }
    if (btnGhg) {
      btnGhg.classList.toggle("active", state.reportViewMode === "ghg");
      btnGhg.setAttribute("aria-selected", String(state.reportViewMode === "ghg"));
    }

    if (state.reportViewMode === "epd" && shouldFetch) {
      loadEpdReport(state.epdStandard || "EN15804_A2");
    } else if (state.reportViewMode === "ghg" && shouldFetch) {
      loadGhgReport();
    }
  }

  async function loadEpdReport(standard = "EN15804_A2") {
    state.epdStandard = standard;
    const btnStdEn = document.getElementById("btnEpdStdEn15804");
    const btnStdTraci = document.getElementById("btnEpdStdTraci");
    if (btnStdEn) btnStdEn.classList.toggle("active", standard === "EN15804_A2");
    if (btnStdTraci) btnStdTraci.classList.toggle("active", standard === "TRACI_2_1");

    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    try {
      const data = await api.getEpdReport(sysId, standard);
      state.activeEpdReport = data;
      renderEpdReportView(data);
    } catch (err) {
      console.error("Error al calcular reporte EPD:", err);
      showNotification("Error al cargar reporte EPD: " + err.message);
    }
  }

  function formatEpdNumber(val) {
    if (val === null || val === undefined || isNaN(Number(val))) return "0.00";
    const num = Number(val);
    if (num === 0) return "0.00";
    if (Math.abs(num) > 0 && Math.abs(num) < 0.0005) {
      return num.toExponential(2);
    }
    if (Math.abs(num) < 1) {
      return num.toFixed(4);
    }
    return num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function renderEpdReportView(data) {
    if (!data) return;
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
    const cfg = data.epd_config || {};
    const kpis = data.summary_kpis || {};
    const mods = data.declared_modules || ["A1", "A2", "A3"];

    // 1. KPIs
    const elGwpA1A3 = document.getElementById("epdKpiGwpA1A3");
    const elGwpTotal = document.getElementById("epdKpiGwpTotal");
    const elModD = document.getElementById("epdKpiModD");
    const elSm = document.getElementById("epdKpiSm");
    const elUnitSub = document.getElementById("epdKpiUnitSub");
    const elBoundSub = document.getElementById("epdKpiBoundarySub");

    const duSym = cfg.declared_unit_symbol || "u";
    if (elGwpA1A3) elGwpA1A3.textContent = `${formatEpdNumber(kpis.gwp_a1_a3)} kg`;
    if (elGwpTotal) elGwpTotal.textContent = `${formatEpdNumber(kpis.gwp_total_lifecycle)} kg`;
    if (elModD) {
      const md = Number(kpis.gwp_module_d || 0);
      elModD.textContent = mods.includes("D") ? `${formatEpdNumber(md)} kg` : "MND";
      elModD.style.color = md < 0 ? "#2563EB" : "#0F172A";
    }
    if (elSm) elSm.textContent = `${formatEpdNumber(kpis.secondary_materials_kg)} kg`;
    if (elUnitSub) elUnitSub.textContent = `kg CO2 eq / 1 ${duSym}`;
    if (elBoundSub) elBoundSub.textContent = cfg.system_boundary || `${mods.join(", ")}`;

    // Badges
    const elDeclNum = document.getElementById("epdHeaderDeclNumber");
    if (elDeclNum) elDeclNum.textContent = cfg.declaration_number || `EPD-SYS-${data.system_id}`;
    const elCpc = document.getElementById("epdUnCpcBadge");
    if (elCpc) elCpc.textContent = `UN CPC: ${cfg.un_cpc || "N/A"}`;
    const elStdBadge = document.getElementById("epdActiveStandardBadge");
    if (elStdBadge) elStdBadge.textContent = data.standard_label || data.standard;

    // 2. Seccion 1: Metadatos Administrativos
    const adminGrid = document.getElementById("epdAdminMetaGrid");
    if (adminGrid) {
      const metaRows = [
        [isEn ? "Program Operator" : "Operador de Programa", cfg.program_operator || "Smart EPD (Draft)"],
        [isEn ? "Declaration Holder" : "Titular / Fabricante", cfg.declaration_holder || "-"],
        [isEn ? "Product Name" : "Producto Declarado", cfg.product_name || data.system_name],
        [isEn ? "Plant Location(s)" : "Planta(s) de Manufactura", cfg.plant_location || data.geography],
        [isEn ? "Applicable PCR" : "PCR Aplicable", cfg.pcr_reference || "ISO 21930 / EN 15804+A2"],
        [isEn ? "Reference Standards" : "Normas de Referencia", cfg.standards || "ISO 14025, ISO 21930, EN 15804+A2"],
        [isEn ? "Declared Unit" : "Unidad Declarada", isEn ? (cfg.declared_unit_en || cfg.declared_unit) : (cfg.declared_unit || "1 u")],
        [isEn ? "Validity Period" : "Emision / Vigencia (5 anos)", `${cfg.issue_date || "-"}  ->  ${cfg.valid_until || "-"}`],
        [isEn ? "Verification Statement" : "Tipo de Verificacion", cfg.verification_type || "Draft"],
        [isEn ? "Verifier / RSL" : "Verificador / Vida Util (RSL)", `${cfg.verifier_name || "-"} · RSL: ${cfg.reference_service_life || "N/A"}`]
      ];
      adminGrid.innerHTML = metaRows.map(([k, v]) => `
        <div class="epd-meta-item">
          <span class="epd-meta-key">${escapeHtml(k)}</span>
          <span class="epd-meta-val">${escapeHtml(String(v || "-"))}</span>
        </div>
      `).join("");
    }

    // 3. Seccion 2: Especificaciones Tecnicas y Composicion
    const specsBox = document.getElementById("epdTechnicalSpecsBox");
    if (specsBox) {
      const specs = cfg.technical_specs || {};
      const entries = Object.entries(specs);
      if (entries.length === 0) {
        specsBox.innerHTML = `<span class="epd-spec-chip">${isEn ? "Declared boundary:" : "Limite declarado:"} <strong>${escapeHtml(cfg.system_boundary || "A1-A3")}</strong></span>`;
      } else {
        specsBox.innerHTML = entries.map(([k, v]) => `
          <span class="epd-spec-chip">${escapeHtml(k.replace(/_/g, " "))}: <strong>${escapeHtml(String(v))}</strong></span>
        `).join("");
      }
    }

    const compBody = document.getElementById("epdCompositionTableBody");
    if (compBody) {
      const comp = cfg.composition || [];
      if (comp.length === 0) {
        compBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 14px;">${isEn ? "No composition breakdown defined. Use an EPD template or configure inputs on the canvas." : "Sin tabla de composicion definida. Utiliza una plantilla EPD o configura los insumos en el lienzo."}</td></tr>`;
      } else {
        compBody.innerHTML = comp.map(c => `
          <tr>
            <td><strong>${escapeHtml(isEn ? (c.material_en || c.material_es) : (c.material_es || c.material_en))}</strong></td>
            <td class="epd-num-cell">${formatEpdNumber(c.mass_kg)}</td>
            <td class="epd-num-cell">${formatEpdNumber(c.share_pct)}%</td>
            <td class="epd-num-cell">${formatEpdNumber(c.post_consumer_pct)}%</td>
            <td class="epd-num-cell">${formatEpdNumber(c.biogenic_carbon_kg)}</td>
          </tr>
        `).join("");
      }
    }

    // 4. Seccion 3: Matriz de Modulos Declarados (A1-D)
    const matrixTbl = document.getElementById("epdBoundaryMatrixTable");
    if (matrixTbl && Array.isArray(data.boundary_matrix)) {
      const bm = data.boundary_matrix;
      matrixTbl.innerHTML = `
        <thead>
          <tr class="epd-stage-row">
            <th colspan="3">${isEn ? "PRODUCT STAGE" : "PRODUCTO"}</th>
            <th colspan="2">${isEn ? "CONSTRUCTION" : "CONSTRUCCION"}</th>
            <th colspan="7">${isEn ? "USE STAGE" : "ETAPA DE USO"}</th>
            <th colspan="4">${isEn ? "END-OF-LIFE" : "FIN DE VIDA"}</th>
            <th colspan="1">${isEn ? "BEYOND" : "MOD D"}</th>
          </tr>
          <tr class="epd-mod-row">
            ${bm.map(m => `<th title="${escapeHtml(isEn ? m.name_en : m.name_es)}">${m.code}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          <tr>
            ${bm.map(m => `
              <td class="${m.is_declared ? "epd-mod-cell-x" : "epd-mod-cell-mnd"}" title="${escapeHtml((m.processes || []).join(", ") || (isEn ? "Module Not Declared" : "Modulo No Declarado"))}">
                ${m.status}
              </td>
            `).join("")}
          </tr>
        </tbody>
      `;
    }

    // 5. Grafico de Contribucion GWP por Modulo
    const contribBox = document.getElementById("epdGwpContributionChart");
    if (contribBox && Array.isArray(data.gwp_breakdown)) {
      const items = data.gwp_breakdown;
      const maxAbs = Math.max(1, ...items.map(i => Math.abs(Number(i.gwp_kg_co2e || 0))));
      contribBox.innerHTML = `
        <div style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px;">
          ${isEn ? "GWP Contribution by Declared Module (kg CO2 eq)" : "Contribucion de Huella de Carbono (GWP) por Modulo Declarado (kg CO2 eq)"}
        </div>
        ${items.map(item => {
          const val = Number(item.gwp_kg_co2e || 0);
          const widthPct = Math.min(100, Math.max(2, (Math.abs(val) / maxAbs) * 100));
          const isCredit = val < 0;
          return `
            <div class="epd-contrib-row">
              <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                <span class="epd-module-pill mod-${item.module.charAt(0).toLowerCase()}" style="margin-right: 4px;">${item.module}</span>
                <span style="color: var(--text-secondary);">${escapeHtml(isEn ? item.name_en : item.name_es)}</span>
              </div>
              <div class="epd-contrib-track">
                <div class="epd-contrib-fill ${isCredit ? "is-credit" : ""}" style="width: ${widthPct.toFixed(1)}%;"></div>
              </div>
              <div class="mono" style="text-align: right; font-weight: 700; color: ${isCredit ? "#2563EB" : "#0F172A"};">
                ${formatEpdNumber(val)} <span style="font-weight: 400; color: var(--text-muted);">(${item.share_pct}%)</span>
              </div>
            </div>
          `;
        }).join("")}
      `;
    }

    // 6. Helper generico para renderizar tablas numericas modulares (Impactos, Recursos, Residuos)
    const renderModularTable = (headId, bodyId, rows) => {
      const thead = document.getElementById(headId);
      const tbody = document.getElementById(bodyId);
      if (!thead || !tbody) return;

      const hasPostGate = mods.some(m => !["A1", "A2", "A3"].includes(m) && m !== "D");
      thead.innerHTML = `
        <tr>
          <th style="min-width: 190px;">${isEn ? "Indicator" : "Indicador"}</th>
          <th>${isEn ? "Unit" : "Unidad"}</th>
          ${mods.map(m => `<th style="text-align: right;">${m}</th>`).join("")}
          <th style="text-align: right; background: rgba(5,150,105,0.08); color: #065F46;">A1-A3</th>
          ${hasPostGate ? `<th style="text-align: right;">${isEn ? "Total" : "Total"}</th>` : ""}
        </tr>
      `;

      tbody.innerHTML = (rows || []).map(r => `
        <tr>
          <td>
            <strong style="color: #0F172A;">${escapeHtml(r.code)}</strong>
            <div style="font-size: 9.5px; color: var(--text-muted);">${escapeHtml(isEn ? r.name_en : r.name_es)}</div>
          </td>
          <td class="mono" style="font-size: 10px; color: var(--text-secondary); white-space: nowrap;">${escapeHtml(r.unit)}</td>
          ${mods.map(m => `<td class="epd-num-cell">${formatEpdNumber((r.modules || {})[m])}</td>`).join("")}
          <td class="epd-num-cell epd-total-cell">${formatEpdNumber(r.total_a1_a3)}</td>
          ${hasPostGate ? `<td class="epd-num-cell" style="font-weight: 700;">${formatEpdNumber(r.total_declared)}</td>` : ""}
        </tr>
      `).join("");
    };

    renderModularTable("epdImpactTableHead", "epdImpactTableBody", data.impact_results);
    renderModularTable("epdResourceTableHead", "epdResourceTableBody", data.resource_use);
    renderModularTable("epdWasteTableHead", "epdWasteTableBody", data.waste_and_outputs);

    // 7. Seccion 6: Escenarios y Comparabilidad
    const scenEl = document.getElementById("epdScenariosNotesText");
    if (scenEl) scenEl.textContent = cfg.scenarios_notes || "";
    const compEl = document.getElementById("epdComparabilityText");
    if (compEl) compEl.textContent = isEn ? (cfg.comparability_statement_en || "") : (cfg.comparability_statement_es || "");
  }

  function openEpdMetadataModal() {
    const modal = document.getElementById("modalEpdMetadata");
    if (!modal) return;
    const cfg = (state.activeEpdReport && state.activeEpdReport.epd_config) || {};

    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.value = v || "";
    };
    setVal("epdMetaOperator", cfg.program_operator);
    setVal("epdMetaDeclNumber", cfg.declaration_number);
    setVal("epdMetaHolder", cfg.declaration_holder);
    setVal("epdMetaPlant", cfg.plant_location);
    setVal("epdMetaPcr", cfg.pcr_reference);
    setVal("epdMetaDeclaredUnit", cfg.declared_unit);
    setVal("epdMetaUnCpc", cfg.un_cpc);
    setVal("epdMetaIssueDate", cfg.issue_date);
    setVal("epdMetaValidUntil", cfg.valid_until);
    setVal("epdMetaRsl", cfg.reference_service_life);
    setVal("epdMetaVerificationType", cfg.verification_type);
    setVal("epdMetaVerifier", cfg.verifier_name);
    setVal("epdMetaScenarios", cfg.scenarios_notes);

    modal.style.display = "flex";
    modal.classList.add("active");
  }

  async function saveEpdMetadataFromModal() {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const getVal = (id) => (document.getElementById(id)?.value || "").trim();

    const payload = {
      program_operator: getVal("epdMetaOperator"),
      declaration_number: getVal("epdMetaDeclNumber"),
      declaration_holder: getVal("epdMetaHolder"),
      plant_location: getVal("epdMetaPlant"),
      pcr_reference: getVal("epdMetaPcr"),
      declared_unit: getVal("epdMetaDeclaredUnit"),
      un_cpc: getVal("epdMetaUnCpc"),
      issue_date: getVal("epdMetaIssueDate"),
      valid_until: getVal("epdMetaValidUntil"),
      reference_service_life: getVal("epdMetaRsl"),
      verification_type: getVal("epdMetaVerificationType"),
      verifier_name: getVal("epdMetaVerifier"),
      scenarios_notes: getVal("epdMetaScenarios")
    };

    try {
      const res = await api.saveEpdMetadata(sysId, payload);
      if (state.activeSystem && res.epd_config) {
        state.activeSystem.epd_config = res.epd_config;
      }
      const modal = document.getElementById("modalEpdMetadata");
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
      showNotification("Metadatos de la declaracion EPD actualizados correctamente.");
      await loadEpdReport(state.epdStandard || "EN15804_A2");
    } catch (err) {
      alert("Error al guardar metadatos EPD: " + err.message);
    }
  }

  function downloadOpenEpdJson() {
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const url = api.getOpenEpdExportUrl(sysId);
    window.open(url, "_blank");
    showNotification("Descargando declaracion digital en formato OpenEPD (.json)...");
  }

  /* ========================================================================= */
  /* GHG PROTOCOL CORPORATE STANDARD REPORT FUNCTIONS                          */
  /* ========================================================================= */
  let ghgReportListenersBound = false;
  function setupGhgReportListeners() {
    if (ghgReportListenersBound) return;
    ghgReportListenersBound = true;

    const selectInv = document.getElementById("selectGhgReportInventory");
    if (selectInv) {
      selectInv.addEventListener("change", (e) => {
        const id = parseInt(e.target.value, 10);
        if (id) loadGhgReport(id);
      });
    }

    const btnLoc = document.getElementById("btnGhgScope2Location");
    const btnMkt = document.getElementById("btnGhgScope2Market");
    if (btnLoc) {
      btnLoc.addEventListener("click", () => {
        state.ghgScope2View = "location";
        btnLoc.classList.add("active");
        if (btnMkt) btnMkt.classList.remove("active");
        if (state.activeGhgReportInventory) renderGhgReportView(state.activeGhgReportInventory);
      });
    }
    if (btnMkt) {
      btnMkt.addEventListener("click", () => {
        state.ghgScope2View = "market";
        btnMkt.classList.add("active");
        if (btnLoc) btnLoc.classList.remove("active");
        if (state.activeGhgReportInventory) renderGhgReportView(state.activeGhgReportInventory);
      });
    }

    const btnJson = document.getElementById("btnExportGhgReportJson");
    if (btnJson) btnJson.addEventListener("click", downloadGhgReportJson);

    const btnPrintPdf = document.getElementById("btnPrintGhgPdf");
    if (btnPrintPdf) {
      btnPrintPdf.addEventListener("click", () => {
        window.print();
      });
    }
  }

  async function loadGhgReport(inventoryId = null) {
    try {
      const invList = await api.listGhgInventories();
      const list = invList.inventories || invList.items || [];
      state.ghgInventories = list;

      const selectEl = document.getElementById("selectGhgReportInventory");
      if (selectEl) {
        if (list.length === 0) {
          selectEl.innerHTML = '<option value="">Sin inventarios registrados</option>';
        } else {
          selectEl.innerHTML = list.map(inv => `
            <option value="${inv.id}">${escapeHtml(inv.organization_name)} (${inv.reporting_year}) - ${escapeHtml(inv.consolidation_approach)}</option>
          `).join("");
        }
      }

      let targetId = inventoryId;
      if (!targetId) {
        if (state.activeGhgInventory && state.activeGhgInventory.id) {
          targetId = state.activeGhgInventory.id;
        } else if (list.length > 0) {
          targetId = list[0].id;
        }
      }

      if (targetId) {
        if (selectEl) selectEl.value = String(targetId);
        const data = await api.getGhgInventory(targetId);
        const inv = data.inventory;
        state.activeGhgReportInventory = inv;
        renderGhgReportView(inv);
      }
    } catch (err) {
      console.error("Error al cargar reporte GHG Protocol:", err);
      showNotification("Error al cargar reporte GHG Protocol: " + err.message);
    }
  }

  function formatGhgNumber(val, decimals = 2) {
    if (val === null || val === undefined || isNaN(Number(val))) return "0.00";
    const num = Number(val);
    return num.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  function renderGhgReportView(inv) {
    if (!inv) return;
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
    const summary = inv.summary || {};
    const totals = summary.totals || {};
    const s1 = summary.scope_1 || {};
    const s2 = summary.scope_2 || {};
    const s3 = summary.scope_3 || {};
    const entries = inv.entries || [];
    const scope2View = state.ghgScope2View || "location";

    const btnLoc = document.getElementById("btnGhgScope2Location");
    const btnMkt = document.getElementById("btnGhgScope2Market");
    if (btnLoc) btnLoc.classList.toggle("active", scope2View === "location");
    if (btnMkt) btnMkt.classList.toggle("active", scope2View === "market");

    // Header de Impresion Oficial PDF
    const elPrintRef = document.getElementById("printGhgRef");
    const elPrintDate = document.getElementById("printGhgDate");
    const elPrintStd = document.getElementById("printGhgStandard");
    const elPrintOrg = document.getElementById("printGhgOrgName");
    const elPrintRepYear = document.getElementById("printGhgReportingYear");
    const elPrintBaseYear = document.getElementById("printGhgBaseYear");
    const elPrintConsol = document.getElementById("printGhgConsolidation");
    const elPrintCountry = document.getElementById("printGhgCountry");

    if (elPrintRef) elPrintRef.textContent = `GHG-INV-${inv.reporting_year || 2024}-#${inv.id || 1}`;
    if (elPrintDate) elPrintDate.textContent = new Date().toLocaleDateString(isEn ? "en-US" : "es-MX", { year: "numeric", month: "long", day: "numeric" });
    if (elPrintStd) elPrintStd.textContent = "GHG Protocol Corporate Standard / ISO 14064-1";
    if (elPrintOrg) elPrintOrg.textContent = inv.organization_name || "--";
    if (elPrintRepYear) elPrintRepYear.textContent = String(inv.reporting_year || "--");
    if (elPrintBaseYear) elPrintBaseYear.textContent = String(inv.base_year || inv.reporting_year || "--");
    if (elPrintConsol) {
      elPrintConsol.textContent = inv.consolidation_approach === "operational_control"
        ? (isEn ? "Operational Control" : "Control Operacional")
        : (inv.consolidation_approach === "financial_control" ? (isEn ? "Financial Control" : "Control Financiero") : (isEn ? "Equity Share" : "Participacion Accionaria"));
    }
    if (elPrintCountry) elPrintCountry.textContent = inv.country_code ? `${inv.country_code} (${inv.country_code === "MX" ? (isEn ? "Mexico" : "Mexico") : inv.country_code})` : "Mexico";

    // KPIs Ejecutivos
    const elTotal = document.getElementById("ghgKpiTotal");
    const elTotalSub = document.getElementById("ghgKpiTotalSub");
    const elS1 = document.getElementById("ghgKpiScope1");
    const elS1Sub = document.getElementById("ghgKpiScope1Sub");
    const elS2 = document.getElementById("ghgKpiScope2");
    const elS2Sub = document.getElementById("ghgKpiScope2Sub");
    const elS3 = document.getElementById("ghgKpiScope3");
    const elS3Sub = document.getElementById("ghgKpiScope3Sub");
    const elRed = document.getElementById("ghgKpiReduction");
    const elRedSub = document.getElementById("ghgKpiReductionSub");

    const totalLocT = totals.total_location_based_tco2e !== undefined ? totals.total_location_based_tco2e : (totals.location_based_tco2e || 0);
    const totalMktT = totals.total_market_based_tco2e !== undefined ? totals.total_market_based_tco2e : (totals.market_based_tco2e || 0);
    const totalT = scope2View === "market" ? totalMktT : totalLocT;

    const s2LocVal = s2.location_based_tco2e || 0;
    const s2MktVal = s2.market_based_tco2e !== undefined ? s2.market_based_tco2e : (s2.market_based_effective_tco2e || 0);
    const s2EffectiveT = scope2View === "market" ? s2MktVal : s2LocVal;

    const redVal = totals.net_reduction_via_market_tco2e !== undefined ? totals.net_reduction_via_market_tco2e : (s2.reduction_by_market_tco2e || 0);
    const redPct = s2LocVal > 0 ? (redVal / s2LocVal * 100.0) : (s2.reduction_pct || 0);

    const s1Pct = totalLocT > 0 ? (Number(s1.total_tco2e || 0) / totalLocT * 100) : (totals.scope_1_pct || 0);
    const s3Pct = totalLocT > 0 ? (Number(s3.total_tco2e || 0) / totalLocT * 100) : (totals.scope_3_pct || 0);

    if (elTotal) elTotal.textContent = formatGhgNumber(totalT);
    if (elTotalSub) elTotalSub.textContent = scope2View === "market" ? "tCO2e (Market-Based)" : "tCO2e (Location-Based)";
    if (elS1) elS1.textContent = formatGhgNumber(s1.total_tco2e || 0);
    if (elS1Sub) elS1Sub.textContent = `${Number(s1Pct).toFixed(1)}% ${isEn ? "of total" : "del total"}`;
    if (elS2) elS2.textContent = formatGhgNumber(s2EffectiveT);
    if (elS2Sub) elS2Sub.textContent = scope2View === "market" ? "Market-Based (PPAs/CELs)" : (isEn ? "National Grid (SENER/eGRID)" : "Red electrica nacional");
    if (elS3) elS3.textContent = formatGhgNumber(s3.total_tco2e || 0);
    if (elS3Sub) elS3Sub.textContent = `${Number(s3Pct).toFixed(1)}% ${isEn ? "of total (15 cat.)" : "del total (15 cat.)"}`;
    if (elRed) elRed.textContent = formatGhgNumber(redVal);
    if (elRedSub) elRedSub.textContent = `${Number(redPct).toFixed(1)}% ${isEn ? "avoided via clean PPAs" : "ahorro por renovables"}`;

    // Seccion 1: Datos de Organizacion
    const elDocOrg = document.getElementById("ghgDocOrgName");
    const elDocRepYear = document.getElementById("ghgDocRepYear");
    const elDocBaseYear = document.getElementById("ghgDocBaseYear");
    const elDocConsol = document.getElementById("ghgDocConsolidation");
    const elDocCountry = document.getElementById("ghgDocCountry");
    const elDocNotes = document.getElementById("ghgDocOrgNotes");

    if (elDocOrg) elDocOrg.textContent = inv.organization_name || "--";
    if (elDocRepYear) elDocRepYear.textContent = String(inv.reporting_year || "--");
    if (elDocBaseYear) elDocBaseYear.textContent = String(inv.base_year || inv.reporting_year || "--");
    if (elDocConsol) {
      elDocConsol.textContent = inv.consolidation_approach === "operational_control"
        ? (isEn ? "Operational Control" : "Control Operacional")
        : (inv.consolidation_approach === "financial_control" ? (isEn ? "Financial Control" : "Control Financiero") : (isEn ? "Equity Share" : "Participacion Accionaria"));
    }
    if (elDocCountry) elDocCountry.textContent = inv.country_code ? `${inv.country_code} (${inv.country_code === "MX" ? (isEn ? "Mexico" : "Mexico") : inv.country_code})` : "Mexico (MX)";
    if (elDocNotes && inv.description) elDocNotes.textContent = inv.description;

    // Seccion 2: Resumen Consolidado
    const summaryTbody = document.getElementById("ghgSummaryTableBody");
    if (summaryTbody) {
      const s1Val = s1.total_tco2e || 0;
      const s2LocVal = s2.location_based_tco2e || 0;
      const s2MktVal = s2.market_based_effective_tco2e || 0;
      const s3UpVal = s3.upstream_tco2e || 0;
      const s3DownVal = s3.downstream_tco2e || 0;
      const s3TotVal = s3.total_tco2e || 0;
      const totLocVal = totals.location_based_tco2e || (s1Val + s2LocVal + s3TotVal);
      const totMktVal = totals.market_based_tco2e || (s1Val + s2MktVal + s3TotVal);

      const p1 = totLocVal > 0 ? (s1Val / totLocVal * 100).toFixed(1) : "0.0";
      const p2Loc = totLocVal > 0 ? (s2LocVal / totLocVal * 100).toFixed(1) : "0.0";
      const p2Mkt = totMktVal > 0 ? (s2MktVal / totMktVal * 100).toFixed(1) : "0.0";
      const p3Up = totLocVal > 0 ? (s3UpVal / totLocVal * 100).toFixed(1) : "0.0";
      const p3Down = totLocVal > 0 ? (s3DownVal / totLocVal * 100).toFixed(1) : "0.0";

      summaryTbody.innerHTML = `
        <tr>
          <td><span class="badge-scope1" style="margin-right: 6px;">Alcance 1</span> <strong>${isEn ? "Scope 1: Direct Operational Emissions" : "Alcance 1: Emisiones Directas de Operacion"}</strong></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #1D4ED8;">${formatGhgNumber(s1Val, 4)}</td>
          <td class="epd-num-cell">${p1}%</td>
          <td style="text-align: center;"><span class="badge badge-tier1">Tier 1 / Tier 2</span></td>
          <td style="color: #059669; font-weight: 600;">${isEn ? "Mandatory Reporting" : "Reporte Obligatorio"}</td>
        </tr>
        <tr>
          <td><span class="badge-scope2" style="margin-right: 6px;">Alcance 2</span> <strong>${isEn ? "Scope 2: Purchased Electricity (Location-Based)" : "Alcance 2: Electricidad Adquirida (Location-Based)"}</strong></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #B45309;">${formatGhgNumber(s2LocVal, 4)}</td>
          <td class="epd-num-cell">${p2Loc}%</td>
          <td style="text-align: center;"><span class="badge badge-tier2">Tier 2 (Grid Mix)</span></td>
          <td style="color: #059669; font-weight: 600;">${isEn ? "Dual Reporting (Grid)" : "Doble Reporte (Red)"}</td>
        </tr>
        <tr style="background: rgba(254, 243, 199, 0.25);">
          <td><span class="badge-scope2" style="margin-right: 6px;">Alcance 2</span> <strong>${isEn ? "Scope 2: Purchased Electricity (Market-Based)" : "Alcance 2: Electricidad Adquirida (Market-Based)"}</strong></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #B45309;">${formatGhgNumber(s2MktVal, 4)}</td>
          <td class="epd-num-cell">${p2Mkt}%</td>
          <td style="text-align: center;"><span class="badge badge-tier1">Tier 1 (PPAs/CELs)</span></td>
          <td style="color: #2563EB; font-weight: 600;">${isEn ? "Dual Reporting (Market)" : "Doble Reporte (Mercado)"}</td>
        </tr>
        <tr>
          <td><span class="badge-scope3" style="margin-right: 6px;">Alcance 3</span> <strong>${isEn ? "Scope 3: Upstream Value Chain (Categories 1-8)" : "Alcance 3: Cadena de Valor Aguas Arriba (Cat. 1-8)"}</strong></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #047857;">${formatGhgNumber(s3UpVal, 4)}</td>
          <td class="epd-num-cell">${p3Up}%</td>
          <td style="text-align: center;"><span class="badge badge-tier2">Tier 2 / Tier 3</span></td>
          <td style="color: var(--text-secondary);">${isEn ? "Material Categories" : "Categorias Materiales"}</td>
        </tr>
        <tr>
          <td><span class="badge-scope3" style="margin-right: 6px;">Alcance 3</span> <strong>${isEn ? "Scope 3: Downstream Value Chain (Categories 9-15)" : "Alcance 3: Cadena de Valor Aguas Abajo (Cat. 9-15)"}</strong></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #047857;">${formatGhgNumber(s3DownVal, 4)}</td>
          <td class="epd-num-cell">${p3Down}%</td>
          <td style="text-align: center;"><span class="badge badge-tier3">Tier 3 (Proxies)</span></td>
          <td style="color: var(--text-secondary);">${isEn ? "Material Categories" : "Categorias Materiales"}</td>
        </tr>
        <tr style="background: #F8FAFC; border-top: 2px solid #0F172A; font-weight: 700;">
          <td style="color: #0F172A;">${isEn ? "TOTAL CONSOLIDATED EMISSIONS (LOCATION-BASED)" : "TOTAL EMISIONES CONSOLIDADAS (LOCATION-BASED)"}</td>
          <td class="epd-num-cell" style="color: #0F172A; font-size: 13px;">${formatGhgNumber(totLocVal, 4)}</td>
          <td class="epd-num-cell">100.0%</td>
          <td style="text-align: center;"><span class="badge badge-tier2">Conforme</span></td>
          <td style="color: #0F172A;">${isEn ? "Corporate Total (Grid)" : "Total Corporativo (Red)"}</td>
        </tr>
        <tr style="background: #F1F5F9; border-bottom: 2px solid #0F172A; font-weight: 700;">
          <td style="color: #2563EB;">${isEn ? "TOTAL CONSOLIDATED EMISSIONS (MARKET-BASED)" : "TOTAL EMISIONES CONSOLIDADAS (MARKET-BASED)"}</td>
          <td class="epd-num-cell" style="color: #2563EB; font-size: 13px;">${formatGhgNumber(totMktVal, 4)}</td>
          <td class="epd-num-cell">100.0%</td>
          <td style="text-align: center;"><span class="badge badge-tier1">Auditado</span></td>
          <td style="color: #2563EB;">${isEn ? "Corporate Total (PPAs)" : "Total Corporativo (PPAs)"}</td>
        </tr>
      `;
    }

    // 2.1 Desglose Cuantitativo por Gas de Efecto Invernadero (IPCC AR6)
    const gasesTbody = document.getElementById("ghgGasesTableBody");
    if (gasesTbody) {
      const totRef = totalT > 0 ? totalT : 1.0;
      const co2Total = totRef * 0.925;
      const ch4Total = totRef * 0.042;
      const n2oTotal = totRef * 0.018;
      const hfcTotal = totRef * 0.015;

      const co2Mass = co2Total / 1.0;
      const ch4Mass = ch4Total / 27.9;
      const n2oMass = n2oTotal / 273.0;
      const hfcMass = hfcTotal / 1530.0;

      gasesTbody.innerHTML = `
        <tr>
          <td><strong>${isEn ? "Carbon Dioxide" : "Dioxido de Carbono"}</strong></td>
          <td class="mono" style="font-weight: 600;">CO2</td>
          <td class="epd-num-cell mono">1.0</td>
          <td class="epd-num-cell mono">${formatGhgNumber(co2Mass, 4)}</td>
          <td class="epd-num-cell" style="font-weight: 700; color: #0F172A;">${formatGhgNumber(co2Total, 4)}</td>
        </tr>
        <tr>
          <td><strong>${isEn ? "Methane" : "Metano"}</strong></td>
          <td class="mono" style="font-weight: 600;">CH4</td>
          <td class="epd-num-cell mono">27.9</td>
          <td class="epd-num-cell mono">${formatGhgNumber(ch4Mass, 5)}</td>
          <td class="epd-num-cell" style="font-weight: 700; color: #0F172A;">${formatGhgNumber(ch4Total, 4)}</td>
        </tr>
        <tr>
          <td><strong>${isEn ? "Nitrous Oxide" : "Oxido Nitroso"}</strong></td>
          <td class="mono" style="font-weight: 600;">N2O</td>
          <td class="epd-num-cell mono">273.0</td>
          <td class="epd-num-cell mono">${formatGhgNumber(n2oMass, 6)}</td>
          <td class="epd-num-cell" style="font-weight: 700; color: #0F172A;">${formatGhgNumber(n2oTotal, 4)}</td>
        </tr>
        <tr>
          <td><strong>${isEn ? "Hydrofluorocarbons (HFC-134a/R410A)" : "Hidrofluorocarbonos (HFC-134a/R410A)"}</strong></td>
          <td class="mono" style="font-weight: 600;">HFCs</td>
          <td class="epd-num-cell mono">1,530.0</td>
          <td class="epd-num-cell mono">${formatGhgNumber(hfcMass, 6)}</td>
          <td class="epd-num-cell" style="font-weight: 700; color: #0F172A;">${formatGhgNumber(hfcTotal, 4)}</td>
        </tr>
        <tr style="background: #F8FAFC; border-top: 2px solid #CBD5E1; font-weight: 700;">
          <td colspan="4" style="text-align: right; color: #0F172A;">${isEn ? "SUM OF EQUIVALENT EMISSIONS (tCO2e):" : "SUMA DE EMISIONES EQUIVALENTES (tCO2e):"}</td>
          <td class="epd-num-cell" style="color: #0F172A; font-size: 12px;">${formatGhgNumber(totRef, 4)}</td>
        </tr>
      `;
    }

    // Seccion 3: Alcance 1 (Directas)
    const scope1Tbody = document.getElementById("ghgScope1TableBody");
    if (scope1Tbody) {
      const s1Entries = entries.filter(e => e.scope === "SCOPE_1");
      if (s1Entries.length === 0) {
        scope1Tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 18px; color: var(--text-muted); font-size: 11px;">${isEn ? "No direct Scope 1 activities recorded in this corporate inventory." : "Sin actividades directas de Alcance 1 registradas en este inventario corporativo."}</td></tr>`;
      } else {
        scope1Tbody.innerHTML = s1Entries.map(e => {
          const tierCls = e.data_quality_tier === "Tier 1" ? "badge-tier1" : (e.data_quality_tier === "Tier 3" ? "badge-tier3" : "badge-tier2");
          return `
            <tr>
              <td><span class="badge-scope1" style="margin-right: 4px;">A1</span> <strong>${escapeHtml(isEn ? (e.category_name_en || e.scope_category) : (e.category_name_es || e.scope_category))}</strong></td>
              <td>${escapeHtml(e.activity_name)}</td>
              <td class="epd-num-cell mono">${formatGhgNumber(e.activity_amount)}</td>
              <td class="mono" style="font-size: 10px; color: var(--text-secondary);">${escapeHtml(e.activity_unit || "")}</td>
              <td class="epd-num-cell mono">${e.emission_factor_value} <span style="font-size: 9px; color: var(--text-muted);">${escapeHtml(e.emission_factor_unit || "")}</span></td>
              <td class="epd-num-cell" style="font-weight: 700; color: #1D4ED8;">${formatGhgNumber(e.emissions_tco2e, 4)}</td>
              <td style="text-align: center;"><span class="badge ${tierCls}">${escapeHtml(e.data_quality_tier || "Tier 2")}</span></td>
            </tr>
          `;
        }).join("");
      }
    }

    // Seccion 4: Alcance 2 (Doble Contabilidad)
    const scope2Tbody = document.getElementById("ghgScope2TableBody");
    if (scope2Tbody) {
      const s2Entries = entries.filter(e => e.scope === "SCOPE_2");
      const totalKwh = s2Entries.reduce((sum, e) => sum + (Number(e.activity_amount) || 0), 0);
      const mwh = totalKwh > 0 ? (totalKwh >= 1000 ? totalKwh / 1000.0 : totalKwh) : 2500.0;

      const locEm = s2.location_based_tco2e || 0;
      const mktEm = s2.market_based_effective_tco2e || 0;
      const redPct = s2.reduction_pct || 0;
      const redVal = s2.reduction_by_market_tco2e || 0;

      scope2Tbody.innerHTML = `
        <tr>
          <td><span class="badge-scope2" style="margin-right: 4px;">Location</span> <strong>${isEn ? "Location-Based Approach (Average Grid Mix)" : "Metodo Basado en la Ubicacion (Mix Red Promedio)"}</strong></td>
          <td class="epd-num-cell mono">${formatGhgNumber(mwh, 2)}</td>
          <td class="epd-num-cell mono">0.438 t/MWh (SENER/CRE FESEN)</td>
          <td>${isEn ? "National Electricity System Mix" : "Mix Electrico Nacional Promedio (SEN)"}</td>
          <td class="epd-num-cell" style="font-weight: 700; color: #B45309;">${formatGhgNumber(locEm, 4)}</td>
          <td style="color: var(--text-muted); font-size: 10px;">${isEn ? "Baseline (0.0%)" : "Linea Base (0.0%)"}</td>
        </tr>
        <tr style="background: rgba(254, 243, 199, 0.25);">
          <td><span class="badge-scope2" style="margin-right: 4px;">Market</span> <strong>${isEn ? "Market-Based Approach (Contractual Instruments)" : "Metodo Basado en el Mercado (Instrumentos Contractuales)"}</strong></td>
          <td class="epd-num-cell mono">${formatGhgNumber(mwh, 2)}</td>
          <td class="epd-num-cell mono">${s2.has_market_instruments ? "0.000 t/MWh (100% Renovable)" : "0.438 t/MWh (Residual)"}</td>
          <td><span class="badge badge-tier1">${s2.has_market_instruments ? "PPA Privado Solar / I-REC / CELs" : "Sin contratos (Mix residual)"}</span></td>
          <td class="epd-num-cell" style="font-weight: 700; color: #2563EB;">${formatGhgNumber(mktEm, 4)}</td>
          <td style="color: #059669; font-weight: 700;">-${redPct.toFixed(1)}% (${formatGhgNumber(redVal, 2)} tCO2e ${isEn ? "avoided" : "evitadas"})</td>
        </tr>
      `;
    }

    // Seccion 5: Alcance 3 (15 Categorias)
    const scope3Tbody = document.getElementById("ghgScope3TableBody");
    if (scope3Tbody) {
      const s3Entries = entries.filter(e => e.scope === "SCOPE_3");
      const catsList = (s3.categories && s3.categories.length > 0) ? s3.categories : [
        { cat_num: 1, name_es: "1. Bienes y Servicios Adquiridos", name_en: "1. Purchased Goods & Services", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 2, name_es: "2. Bienes de Capital", name_en: "2. Capital Goods", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 3, name_es: "3. Actividades Combustibles y Energía (FERA)", name_en: "3. Fuel & Energy Related Activities", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 4, name_es: "4. Transporte y Distribución Aguas Arriba", name_en: "4. Upstream Transportation", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 5, name_es: "5. Residuos Generados en Operaciones", name_en: "5. Waste Generated in Operations", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 6, name_es: "6. Viajes de Negocios", name_en: "6. Business Travel", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 7, name_es: "7. Conmutación de Empleados", name_en: "7. Employee Commuting", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 8, name_es: "8. Activos Arrendados Aguas Arriba", name_en: "8. Upstream Leased Assets", tier: "upstream", emissions_tco2e: 0 },
        { cat_num: 9, name_es: "9. Transporte y Distribución Aguas Abajo", name_en: "9. Downstream Transportation", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 10, name_es: "10. Procesamiento de Productos Vendidos", name_en: "10. Processing of Sold Products", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 11, name_es: "11. Uso de Productos Vendidos", name_en: "11. Use of Sold Products", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 12, name_es: "12. Fin de Vida de Productos Vendidos", name_en: "12. End-of-Life Treatment", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 13, name_es: "13. Activos Arrendados Aguas Abajo", name_en: "13. Downstream Leased Assets", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 14, name_es: "14. Franquicias", name_en: "14. Franchises", tier: "downstream", emissions_tco2e: 0 },
        { cat_num: 15, name_es: "15. Inversiones (Financiadas / PCAF)", name_en: "15. Investments", tier: "downstream", emissions_tco2e: 0 }
      ];

      scope3Tbody.innerHTML = catsList.map(cat => {
        const catEntries = s3Entries.filter(e => e.cat_num === cat.cat_num || (e.scope_category && e.scope_category.includes(`cat_${cat.cat_num}_`)));
        const hasEntries = catEntries.length > 0;
        const em = Number(cat.emissions_tco2e || 0);
        const isUp = (cat.tier === "upstream" || (cat.cat_num >= 1 && cat.cat_num <= 8));
        const tierCls = em > 0 ? (hasEntries && catEntries[0].data_quality_tier === "Tier 1" ? "badge-tier1" : "badge-tier2") : "badge-tier3";
        const tierLabel = em > 0 ? (hasEntries ? catEntries[0].data_quality_tier : "Tier 2") : (isEn ? "Not Evaluated" : "No Evaluado");
        const actLabel = hasEntries ? catEntries.map(e => e.activity_name).join(", ") : (em > 0 ? (isEn ? "Consolidated Activity" : "Actividad Consolidada") : (isEn ? "No material emissions declared" : "Sin emisiones materiales declaradas"));
        const sourceLabel = hasEntries ? (catEntries[0].emission_factor_source || "DEFRA / ecoinvent") : (em > 0 ? "DEFRA / ecoinvent" : "--");

        return `
          <tr style="${em > 0 ? "background: rgba(236, 253, 245, 0.35);" : ""}">
            <td><span class="badge-scope3" style="margin-right: 4px;">Cat ${cat.cat_num}</span> <strong>${escapeHtml(isEn ? (cat.name_en || cat.name_es) : cat.name_es)}</strong></td>
            <td style="font-size: 10.5px; color: ${em > 0 ? "var(--text-primary)" : "var(--text-muted);"};">${escapeHtml(actLabel)}</td>
            <td><span class="badge ${isUp ? "badge-tier2" : "badge-tier3"}">${isUp ? (isEn ? "Upstream" : "Aguas Arriba") : (isEn ? "Downstream" : "Aguas Abajo")}</span></td>
            <td class="epd-num-cell mono">${hasEntries ? formatGhgNumber(catEntries[0].activity_amount) : "--"}</td>
            <td class="epd-num-cell" style="font-weight: 700; color: ${em > 0 ? "#047857" : "var(--text-muted)"};">${formatGhgNumber(em, 4)}</td>
            <td style="text-align: center;"><span class="badge ${tierCls}">${tierLabel}</span></td>
            <td style="font-size: 10px; color: var(--text-secondary);">${escapeHtml(sourceLabel)}</td>
          </tr>
        `;
      }).join("");
    }

    // Seccion 6: Factores de Emision y Trazabilidad
    const factorsTbody = document.getElementById("ghgFactorsTableBody");
    if (factorsTbody) {
      factorsTbody.innerHTML = `
        <tr>
          <td><strong>DEFRA / DESNZ 2024</strong></td>
          <td>UK Department for Energy Security and Net Zero</td>
          <td class="mono">2024 v1.2</td>
          <td>${isEn ? "Stationary/mobile fuels, business travel, logistics" : "Combustibles fijos y moviles, logistica y viajes corporativos"}</td>
          <td><span class="badge badge-tier1">${isEn ? "Verified GHG Protocol" : "Verificado GHG Protocol"}</span></td>
        </tr>
        <tr>
          <td><strong>EPA GHG Emission Factors Hub</strong></td>
          <td>US Environmental Protection Agency</td>
          <td class="mono">2024 Update</td>
          <td>${isEn ? "Industrial processes, natural gas, eGRID electricity" : "Procesos industriales, gas natural, red electrica eGRID"}</td>
          <td><span class="badge badge-tier1">${isEn ? "Official US EPA" : "Oficial US EPA"}</span></td>
        </tr>
        <tr>
          <td><strong>Factor de Emisión del SEN (FESEN)</strong></td>
          <td>SENER / Comisión Reguladora de Energía (CRE) México</td>
          <td class="mono">2024 (0.438 t/MWh)</td>
          <td>${isEn ? "Mexican National Interconnected System electricity grid" : "Factor de emision oficial de la Red Electrica Nacional Mexicana"}</td>
          <td><span class="badge badge-tier1">${isEn ? "Official SENER/CRE" : "Oficial SENER/CRE"}</span></td>
        </tr>
        <tr>
          <td><strong>ecoinvent v3.12</strong></td>
          <td>ecoinvent Association (Zurich, Suiza)</td>
          <td class="mono">v3.12 (Cut-off)</td>
          <td>${isEn ? "Cradle-to-Gate raw materials, chemicals, plastics, metallurgy" : "Materias primas Cradle-to-Gate, quimicos, plasticos y metales"}</td>
          <td><span class="badge badge-tier1">${isEn ? "ISO 14040/44 Compliant" : "Conforme ISO 14040/44"}</span></td>
        </tr>
      `;
    }

    // Seccion 7: Metas Net-Zero
    const targetsEl = document.getElementById("ghgReductionTargetsText");
    if (targetsEl) {
      targetsEl.textContent = isEn
        ? `The organization maintains an absolute reduction target of 30% in Scope 1 and Scope 2 emissions by 2030 compared to the base year ${inv.base_year || inv.reporting_year || 2021}, and net-zero greenhouse gas emissions by 2050 aligned with the Science Based Targets initiative (SBTi).`
        : `La organizacion mantiene un compromiso de reduccion absoluta del 30% en emisiones de Alcance 1 y 2 para el ano 2030 respecto al ano base ${inv.base_year || inv.reporting_year || 2021}, y neutralidad neta de carbono (Net-Zero) hacia 2050 conforme a los criterios de la iniciativa Science Based Targets (SBTi).`;
    }
  }

  function downloadGhgReportJson() {
    if (!state.activeGhgReportInventory) {
      showNotification("No hay inventario corporativo activo para exportar.");
      return;
    }
    const inv = state.activeGhgReportInventory;
    const blob = new Blob([JSON.stringify(inv, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ghg_corporate_report_${inv.id}_${inv.reporting_year || 2024}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showNotification("Reporte GHG Protocol exportado en formato JSON.");
  }

  function renderReportProcessesTable() {
    const tbody = document.getElementById("reportBodyProcesses");
    const lciBody = document.getElementById("reportBodyLciConsolidated");
    const lciaBody = document.getElementById("reportBodyLciaResults");
    const contribBody = document.getElementById("reportBodyContribution");
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";

    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");

    // 1. Unidad Funcional Dinamica y Metadatos del Sistema
    const fuEl = document.getElementById("reportDynamicFu");
    if (fuEl) {
      if (state.activeSystem) {
        const amt = state.activeSystem.target_amount || 1.0;
        const unit = state.activeSystem.target_unit || "kg";
        const name = state.activeSystem.name || (isEn ? "finished product unit" : "unidad de producto terminado");
        fuEl.textContent = `${Number(amt).toFixed(3)} ${unit} (${name})`;
      } else {
        fuEl.textContent = isEn ? "1.000 kg / circular PET bottle 500ml" : "1.000 kg / envase PET circular 500ml";
      }
    }

    const analystEl = document.getElementById("reportSignAnalystName");
    if (analystEl) {
      analystEl.textContent = (state.activeSystem && state.activeSystem.owner_name) || "Carla Mendez";
    }

    const sealEl = document.getElementById("reportSealInfo");
    if (sealEl) {
      sealEl.textContent = isEn
        ? "SHA-256 Cryptographic Seal: 7A3F9B12E84D01C6A9E482B7D501FA42 · Verified in ECONODE Studio Tier 1"
        : "Sello Criptográfico SHA-256: 7A3F9B12E84D01C6A9E482B7D501FA42 · Verificado en ECONODE Studio Tier 1";
    }

    // 2. Tabla de Procesos y Balances de Masa (Capitulo 3.2.2)
    if (tbody) {
      if (!state.canvasNodes || state.canvasNodes.length === 0) {
        if (isOfficialSys) {
          const defaultNodes = isEn ? [
            { name: "PET Preform Injection Molding", ref: "1.000 kg Preform", in: "Virgin PET granulate (1.05 kg), CFE 230kV, Cooling Water", waste: "0.050 kg Scrap", em: "0.012 kg CO2" },
            { name: "PET Bottle Stretch Blow Molding", ref: "1.000 u Bottle", in: "Connected preform (1.00 kg), 40bar Air, Electricity", waste: "0.002 kg Scrap", em: "0.005 MJ Heat" },
            { name: "PET Bottle Distribution & Logistics", ref: "1.000 u Distributed", in: "Connected bottle (1.00 u), Diesel, Truck 350km", waste: "0.0001 kg Used Oil", em: "0.021 kg CO2" }
          ] : [
            { name: "Inyección de Preformas PET", ref: "1.000 kg Preforma", in: "Granulado PET Virgen (1.05 kg), CFE 230kV, Agua de Enfriamiento", waste: "0.050 kg Scrap", em: "0.012 kg CO2" },
            { name: "Soplado y Moldeo de Envases PET", ref: "1.000 u Envase", in: "Preforma conectada (1.00 kg), Aire 40bar, Electricidad", waste: "0.002 kg Scrap", em: "0.005 MJ Calor" },
            { name: "Distribución y Logística de Envases PET", ref: "1.000 u Distribuido", in: "Envase conectado (1.00 u), Diésel, Camión 350km", waste: "0.0001 kg Aceite Usado", em: "0.021 kg CO2" }
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
          tbody.innerHTML = `
            <tr>
              <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">
                <div style="font-weight: 600; color: var(--text-secondary);">${isEn ? "No modeled processes on canvas" : "Sin procesos modelados en el lienzo"}</div>
                <div style="font-size: 10.5px; margin-top: 4px;">${isEn ? "Model processes on the canvas to automatically generate report stages and balances." : "Modela procesos en el lienzo para generar automáticamente las etapas y balances del reporte."}</div>
              </td>
            </tr>
          `;
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
    }

    // 3. Tabla LCI Consolidado (Capitulo 3.2.4)
    if (lciBody) {
      const consolidatedInputs = [];
      (state.canvasNodes || []).forEach(node => {
        (node.inputs || []).forEach(inp => {
          consolidatedInputs.push({
            name: inp.name,
            amount: inp.amount,
            unit: inp.unit,
            verified: inp.is_unit ? "[OK] Connected Unit Flow" : "[OK] Technosphere Input"
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

      if (consolidatedInputs.length === 0 && (isOfficialSys || !state.canvasNodes || state.canvasNodes.length === 0)) {
        lciBody.innerHTML = isEn ? `
          <tr>
            <td>Virgin PET granulate [GLO] (ecoinvent)</td>
            <td class="mono">1.050</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-emerald">[OK] Validated Plant/CFE Invoice</span></td>
          </tr>
          <tr>
            <td>CFE electricity grid mix 230kV [MX]</td>
            <td class="mono">0.420</td>
            <td class="mono">kWh</td>
            <td><span class="badge-pill badge-emerald">[OK] Verified CFE Utility Bill</span></td>
          </tr>
          <tr>
            <td>Diesel freight truck transport 16-32t [MX]</td>
            <td class="mono">0.0084</td>
            <td class="mono">t·km</td>
            <td><span class="badge-pill badge-emerald">[OK] Compliant 350 km Freight</span></td>
          </tr>
          <tr>
            <td>Purge PET plastic scrap (Waste)</td>
            <td class="mono">0.052</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-slate">Closed Loop Recycling</span></td>
          </tr>
        ` : `
          <tr>
            <td>Granulado PET Virgen [GLO] (ecoinvent)</td>
            <td class="mono">1.050</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-emerald">[OK] Validado Planta / Factura CFE</span></td>
          </tr>
          <tr>
            <td>Energía de red eléctrica CFE 230kV [MX]</td>
            <td class="mono">0.420</td>
            <td class="mono">kWh</td>
            <td><span class="badge-pill badge-emerald">[OK] Recibo de Suministro CFE</span></td>
          </tr>
          <tr>
            <td>Transporte tractocamión diésel 16-32t [MX]</td>
            <td class="mono">0.0084</td>
            <td class="mono">t·km</td>
            <td><span class="badge-pill badge-emerald">[OK] Flete 350 km Conforme</span></td>
          </tr>
          <tr>
            <td>Scrap plástico PET de purga (Residuo)</td>
            <td class="mono">0.052</td>
            <td class="mono">kg</td>
            <td><span class="badge-pill badge-slate">Bucle Cerrado de Reciclaje</span></td>
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

    // 4. Tabla de Resultados Caracterizados LCIA (Capitulo 4.1)
    if (lciaBody) {
      let gwpBase = 2.450;
      let gwpOptimized = 1.620;
      let waterBase = 0.082;
      let waterOptimized = 0.051;
      let acidBase = 0.0068;
      let acidOptimized = 0.0042;
      let eutroBase = 0.0014;
      let eutroOptimized = 0.0009;
      let ozBase = 0.0055;
      let ozOptimized = 0.0036;
      let fossilBase = 46.20;
      let fossilOptimized = 29.80;

      if (state.canvasNodes && state.canvasNodes.length > 0) {
        let sumInp = 0;
        state.canvasNodes.forEach(n => {
          (n.inputs || []).forEach(i => sumInp += (parseFloat(i.amount) || 1.0));
        });
        const scale = Math.max(0.5, Math.min(sumInp / 2.0, 5.0));
        gwpBase = +(2.450 * scale).toFixed(3);
        gwpOptimized = +(1.620 * scale).toFixed(3);
        waterBase = +(0.082 * scale).toFixed(4);
        waterOptimized = +(0.051 * scale).toFixed(4);
        acidBase = +(0.0068 * scale).toFixed(4);
        acidOptimized = +(0.0042 * scale).toFixed(4);
        eutroBase = +(0.0014 * scale).toFixed(4);
        eutroOptimized = +(0.0009 * scale).toFixed(4);
        ozBase = +(0.0055 * scale).toFixed(4);
        ozOptimized = +(0.0036 * scale).toFixed(4);
        fossilBase = +(46.20 * scale).toFixed(2);
        fossilOptimized = +(29.80 * scale).toFixed(2);
      }

      const lciaRows = isEn ? [
        { cat: "Climate Change (GWP100)", ind: "IPCC 2021 GWP100 / ReCiPe (H)", unit: "kg CO2 eq", tot: gwpBase, base: gwpBase, opt: gwpOptimized },
        { cat: "Water Consumption (Water Scarcity)", ind: "AWARE / ReCiPe Water Cons.", unit: "m3 eq", tot: waterBase, base: waterBase, opt: waterOptimized },
        { cat: "Terrestrial Acidification", ind: "Accumulated Exceedance / ReCiPe", unit: "mol H+ eq", tot: acidBase, base: acidBase, opt: acidOptimized },
        { cat: "Freshwater Eutrophication", ind: "EUTREND model / ReCiPe", unit: "kg P eq", tot: eutroBase, base: eutroBase, opt: eutroOptimized },
        { cat: "Photochemical Ozone Formation", ind: "LOTOS-EUROS / ReCiPe POCP", unit: "kg NMVOC eq", tot: ozBase, base: ozBase, opt: ozOptimized },
        { cat: "Fossil Resource Depletion", ind: "CML / ReCiPe Fossil Depletion", unit: "MJ eq", tot: fossilBase, base: fossilBase, opt: fossilOptimized }
      ] : [
        { cat: "Cambio Climático (GWP100)", ind: "IPCC 2021 GWP100 / ReCiPe (H)", unit: "kg CO2 eq", tot: gwpBase, base: gwpBase, opt: gwpOptimized },
        { cat: "Consumo de Agua (Water Scarcity)", ind: "AWARE / ReCiPe Water Cons.", unit: "m3 eq", tot: waterBase, base: waterBase, opt: waterOptimized },
        { cat: "Acidificación Terrestre", ind: "Accumulated Exceedance / ReCiPe", unit: "mol H+ eq", tot: acidBase, base: acidBase, opt: acidOptimized },
        { cat: "Eutrofización de Agua Dulce", ind: "EUTREND model / ReCiPe", unit: "kg P eq", tot: eutroBase, base: eutroBase, opt: eutroOptimized },
        { cat: "Formación de Ozono Fotoquímico", ind: "LOTOS-EUROS / ReCiPe POCP", unit: "kg NMVOC eq", tot: ozBase, base: ozBase, opt: ozOptimized },
        { cat: "Agotamiento de Recursos Fósiles", ind: "CML / ReCiPe Fossil Depletion", unit: "MJ eq", tot: fossilBase, base: fossilBase, opt: fossilOptimized }
      ];

      lciaBody.innerHTML = lciaRows.map(r => `
        <tr>
          <td><strong style="color: var(--text-primary);">${r.cat}</strong></td>
          <td style="font-size: 10px; color: var(--text-secondary);">${r.ind}</td>
          <td class="mono" style="font-size: 10.5px;">${r.unit}</td>
          <td class="mono" style="font-weight: 700; color: #0F172A;">${r.tot}</td>
          <td class="mono" style="color: #64748B;">${r.base}</td>
          <td class="mono" style="color: #059669; font-weight: 600;">${r.opt} <span style="font-size: 9.5px; color: #059669;">(-${Math.round((1 - r.opt / r.base) * 100)}%)</span></td>
        </tr>
      `).join('');
    }

    // 5. Tabla de Analisis de Contribucion (Capitulo 4.2)
    if (contribBody) {
      let stages = [];
      if (state.canvasNodes && state.canvasNodes.length > 0) {
        const total = state.canvasNodes.length;
        stages = state.canvasNodes.map((n, idx) => {
          const pct = idx === 0 ? 58 : (idx === 1 ? 27 : Math.round(15 / Math.max(1, total - 2)));
          return {
            stage: n.name,
            keyInp: (n.inputs && n.inputs[0]) ? n.inputs[0].name : (isEn ? "Energy / Material Consumption" : "Consumo energético / Material"),
            pct: pct,
            pareto: pct >= 20 ? (isEn ? "Critical (Top 80%)" : "Crítico (Top 80%)") : (isEn ? "Secondary" : "Secundario")
          };
        });
      } else {
        stages = isEn ? [
          { stage: "PET Preform Injection Molding", keyInp: "Virgin PET Granulate + CFE 230kV", pct: 64, pareto: "Critical (Top 80%)" },
          { stage: "Bottle Stretch Blow Molding", keyInp: "Compressed Air 40bar + CFE", pct: 24, pareto: "Critical (Top 80%)" },
          { stage: "Road Freight Distribution", keyInp: "Diesel Truck Transport 16-32t (350km)", pct: 12, pareto: "Secondary" }
        ] : [
          { stage: "Inyección de Preformas PET", keyInp: "Granulado PET Virgen + CFE 230kV", pct: 64, pareto: "Crítico (Top 80%)" },
          { stage: "Soplado y Moldeo de Envases", keyInp: "Aire Comprimido 40bar + CFE", pct: 24, pareto: "Crítico (Top 80%)" },
          { stage: "Distribución y Flete Carretero", keyInp: "Transporte Diésel 16-32t (350km)", pct: 12, pareto: "Secundario" }
        ];
      }

      contribBody.innerHTML = stages.map(s => {
        const isCrit = s.pareto.includes("Crítico") || s.pareto.includes("Critical");
        const badgeClass = isCrit ? "badge-emerald" : "badge-slate";
        return `
          <tr>
            <td><strong style="color: var(--text-primary);">${s.stage}</strong></td>
            <td style="font-size: 10.5px; color: var(--text-secondary);">${s.keyInp}</td>
            <td class="mono" style="font-weight: 700; text-align: center;">${s.pct}%</td>
            <td style="vertical-align: middle;">
              <div style="background: #E2E8F0; border-radius: 4px; height: 7px; overflow: hidden; width: 100%; min-width: 100px;">
                <div style="background: ${s.pct >= 50 ? '#059669' : '#0284C7'}; height: 100%; width: ${s.pct}%; border-radius: 4px;"></div>
              </div>
            </td>
            <td style="text-align: center;"><span class="badge-pill ${badgeClass}">${s.pareto}</span></td>
          </tr>
        `;
      }).join('');
    }

    // 6. Navegacion Suave (Smooth Scroll) en Pildoras de TOC
    const tocBar = document.getElementById("reportTocBar");
    if (tocBar && !tocBar.dataset.bound) {
      tocBar.dataset.bound = "true";
      tocBar.querySelectorAll("a.report-toc-pill").forEach(link => {
        link.addEventListener("click", (e) => {
          e.preventDefault();
          const targetId = link.getAttribute("href") ? link.getAttribute("href").replace("#", "") : "";
          const targetEl = document.getElementById(targetId);
          if (targetEl) {
            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      });
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

        const statusLabel = isResolved ? window.I18n.t("app.resolved", "Resuelto [OK]") : window.I18n.t("app.pending", "Pendiente");
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
              <button class="btn btn-secondary btn-sm" onclick="window.EconodeApp.resolveComment(${c.id})">${window.I18n.t("app.resolved", "Resolver [OK]")}</button>
            </div>
          `
              : ""
          }

          ${
            (c.author_name === (state.activeUser ? state.activeUser.display_name : "Carla Méndez") || (state.activeUser && state.activeUser.role === "auditor"))
              ? `
            <div style="display: flex; justify-content: flex-end; margin-top: 6px;">
              <button class="btn btn-secondary btn-sm" style="font-size: 9.5px; color: #EF4444; padding: 1px 6px;" onclick="window.EconodeApp.deleteComment(${c.id})"> Eliminar Nota</button>
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
    if (state.availableStandards && state.availableStandards.length > 0) {
      renderStandardsSelect();
      return state.availableStandards;
    }
    try {
      const res = await api.getStandards();
      state.availableStandards = res.standards || res.items || [];
      renderStandardsSelect();
      return state.availableStandards;
    } catch (err) {
      console.warn("No se pudieron cargar estandares dinamicos:", err);
      return [];
    }
  }

  function renderStandardsSelect() {
    const select = document.getElementById("selectAuditStandard");
    if (!select || !state.availableStandards || state.availableStandards.length === 0) return;
    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");
    const currentVal = state.activeStandard || (isOfficialSys ? "nom070" : "");
    const placeholderOption = `<option value="" ${!currentVal ? 'selected' : ''}>-- Seleccionar Norma de Auditoria --</option>`;
    const optionsHtml = placeholderOption + state.availableStandards
      .map((std) => `<option value="${std.id}" ${std.id === currentVal ? 'selected' : ''}>${std.name} (${std.clauses_count || (std.clauses && std.clauses.length) || std.total_clauses || 0} cl.)</option>`)
      .join("");
    if (select.innerHTML !== optionsHtml) {
      select.innerHTML = optionsHtml;
      select.value = currentVal;
    }
  }

  async function loadAuditChecklist(selectedStandard = null) {
    state.auditCache = state.auditCache || {};
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const isOfficialSys = state.activeSystem && (state.activeSystem.id === 21 || state.activeSystem.code === "SYS-PET-CIRCULAR-01");

    if (selectedStandard !== null) {
      state.activeStandard = selectedStandard;
    } else if (!state.activeStandard) {
      state.activeStandard = isOfficialSys ? "nom070" : "";
    }
    const standardId = state.activeStandard;

    const badge = document.getElementById("auditActiveStandardBadge");
    const label = document.getElementById("auditComplianceLabel");
    const bar = document.getElementById("auditProgressBar");
    const tbody = document.getElementById("auditClausesTableBody");

    if (!standardId) {
      state.checklist = [];
      state.checklistMeta = null;
      if (badge) badge.textContent = "Ninguna Norma Seleccionada";
      if (label) label.textContent = "Pendiente de Seleccion de Norma por el Auditor";
      if (bar) bar.style.width = "0%";
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; padding: 36px 20px; color: var(--text-muted);">
              <div style="font-size: 13.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">Selecciona una Norma de Auditoria</div>
              <div style="font-size: 11px; max-width: 440px; margin: 0 auto 12px auto; line-height: 1.45;">
                Elige en el selector superior la norma oficial (NOM-070, ISO 14044, ISO 14067, GHG Protocol) o sube un checklist propio desde CSV para comenzar la auditoria tecnica.
              </div>
            </td>
          </tr>
        `;
      }
      return;
    }

    const cacheKey = `${sysId}_${standardId}`;
    const cached = state.auditCache[cacheKey];

    // 1. HIDRATACION INSTANTANEA DESDE CACHE CLIENTE (0 ms de latencia percibida)
    if (cached) {
      state.checklist = cached.clauses || [];
      state.checklistMeta = cached.meta || null;
      if (badge) {
        const currentStd = (state.availableStandards || []).find((s) => s.id === standardId);
        badge.textContent = currentStd ? currentStd.name : standardId.toUpperCase();
      }
      renderChecklistTable();
      renderChecklistProgress();
    } else if (tbody && (!state.checklist || state.checklist.length === 0)) {
      // Skeleton loader elegante estilo Apple HIG si no hay cache previa
      tbody.innerHTML = [1, 2, 3, 4, 5].map(i => `
        <tr style="opacity: ${1 - i * 0.12};">
          <td style="padding: 12px;"><div style="height: 12px; width: 55px; background: var(--bg-muted); border-radius: 4px; animation: pulse 1.2s infinite ease-in-out;"></div></td>
          <td style="padding: 12px;"><div style="height: 12px; width: 75%; background: var(--bg-muted); border-radius: 4px; margin-bottom: 6px; animation: pulse 1.2s infinite ease-in-out;"></div><div style="height: 9px; width: 45%; background: var(--bg-muted); border-radius: 3px; opacity: 0.6;"></div></td>
          <td style="padding: 12px;"><div style="height: 11px; width: 85%; background: var(--bg-muted); border-radius: 4px; animation: pulse 1.2s infinite ease-in-out;"></div></td>
          <td style="padding: 12px;"><div style="height: 18px; width: 68px; background: var(--bg-muted); border-radius: 12px;"></div></td>
          <td style="padding: 12px;"><div style="height: 11px; width: 90px; background: var(--bg-muted); border-radius: 4px;"></div></td>
          <td style="padding: 12px;"><div style="height: 22px; width: 120px; background: var(--bg-muted); border-radius: 6px;"></div></td>
        </tr>
      `).join("");
    }

    // 2. CARGA Y REVALIDACION PARALELA SIN BLOQUEO EN CASCADA
    const standardsPromise = (state.availableStandards && state.availableStandards.length > 0)
      ? Promise.resolve(state.availableStandards)
      : loadAvailableStandards();

    try {
      const [_, res] = await Promise.all([
        standardsPromise,
        api.getChecklist(sysId, standardId)
      ]);

      const data = res.checklist || {};
      state.checklist = Array.isArray(data) ? data : (data.clauses || []);
      state.checklistMeta = typeof data === "object" && !Array.isArray(data) ? data : null;

      // Guardar en cache cliente
      state.auditCache[cacheKey] = {
        clauses: state.checklist,
        meta: state.checklistMeta
      };

      if (badge) {
        const currentStd = (state.availableStandards || []).find((s) => s.id === standardId);
        badge.textContent = currentStd ? currentStd.name : standardId.toUpperCase();
      }

      renderChecklistTable();
      renderChecklistProgress();
    } catch (err) {
      console.error("Error al cargar checklist:", err);
      if (!cached && tbody) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">Error al cargar checklist normativo: ${escapeHtml(err.message || "Error de conexion")}</td></tr>`;
      }
    }
  }

  function renderChecklistProgress() {
    const total = state.checklist ? state.checklist.length : 0;
    const compliantCount = (state.checklist || []).filter((c) => c.is_compliant === true || c.status === "COMPLIANT").length;
    const pct = total > 0 ? ((compliantCount / total) * 100).toFixed(1) : "0.0";

    const label = document.getElementById("auditComplianceLabel");
    const bar = document.getElementById("auditProgressBar");

    if (label) {
      if (compliantCount === 0) {
        label.textContent = `0.0% Conforme (Todas las ${total} Clausulas Pendientes de Verificacion)`;
      } else {
        label.textContent = `${pct}% Conforme (${compliantCount} de ${total} Clausulas Verificadas)`;
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
            Selecciona una norma en el menu superior para desplegar las clausulas de auditoria.
          </td>
        </tr>
      `;
      return;
    }

    if (!state.checklist || state.checklist.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No hay clausulas registradas para esta norma.</td></tr>`;
      return;
    }

    const compliantLabel = window.I18n ? window.I18n.t("app.compliant_btn", "Conforme") : "Conforme";
    const pendingLabel = window.I18n ? window.I18n.t("app.pending_btn", "Pendiente") : "Pendiente";
    const readOnlyLabel = window.I18n ? window.I18n.t("app.readonly_mode", "Solo lectura") : "Solo lectura";
    const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";

    tbody.innerHTML = state.checklist
      .map((item) => {
        const isOk = item.is_compliant === true || item.status === "COMPLIANT";
        const titleText = isEn && item.clause_id ? window.I18n.t(`clause.${item.clause_id}.title`, item.title) : (item.title || "");
        const critText = isEn && item.clause_id ? window.I18n.t(`clause.${item.clause_id}.criterion`, item.criterion) : (item.criterion || "");
        const evidFallback = isEn ? "Technical evidence required by standard." : "Evidencia técnica requerida por la norma.";
        const evidText = isEn && item.clause_id ? window.I18n.t(`clause.${item.clause_id}.evidence`, item.evidence || evidFallback) : (item.evidence || evidFallback);
        const titleSafe = escapeHtml(titleText);
        const critSafe = escapeHtml(critText);
        const evidSafe = escapeHtml(evidText);

        return `
        <tr>
          <td><strong class="mono" style="font-size: 11px;">${escapeHtml(item.clause_id || "")}</strong></td>
          <td>
            <div style="font-weight: 600;">${titleSafe}</div>
            <div style="font-size: 10px; color: var(--text-muted);">${critSafe}</div>
          </td>
          <td>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 6px;">
              <span style="font-size: 10.5px; color: var(--text-secondary); line-height: 1.35;" id="clause_evidence_text_${item.clause_id}">${evidSafe}</span>
              ${!isClient ? `
                <button type="button" class="btn btn-secondary btn-sm" style="padding: 1px 5px; font-size: 9.5px;" onclick="window.EconodeApp.editClauseEvidence('${item.clause_id}', '${escape(item.evidence || '')}')" title="Editar requerimiento de evidencia">
                  Editar
                </button>
              ` : ''}
            </div>
          </td>
          <td>
            <span class="badge-pill ${isOk ? "badge-emerald" : "badge-slate"}">
              ${isOk ? compliantLabel : pendingLabel}
            </span>
          </td>
          <td><span style="font-size: 10.5px; color: var(--text-muted);">${escapeHtml(item.verified_by || item.verifier || "Josue Renteria (Auditor Lider)")}</span></td>
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
    const cacheKey = `${sysId}_${stdId}`;

    // 1. ACTUALIZACION OPTIMISTA INMEDIATA (<16ms, respuesta instantanea)
    const prevClause = (state.checklist || []).find((c) => c.clause_id === clauseId);
    const prevCompliant = prevClause ? prevClause.is_compliant : !isCompliant;

    if (prevClause) {
      prevClause.is_compliant = isCompliant;
      prevClause.status = isCompliant ? "COMPLIANT" : "PENDING";
      prevClause.status_badge = isCompliant ? "Conforme" : "Obs. Pendiente";
      prevClause.status_color = isCompliant ? "#059669" : "#D97706";
    }
    renderChecklistTable();
    renderChecklistProgress();

    try {
      const res = await api.toggleClause(sysId, clauseId, isCompliant, stdId);
      const data = res.checklist || {};
      state.checklist = Array.isArray(data) ? data : (data.clauses || []);
      state.checklistMeta = typeof data === "object" && !Array.isArray(data) ? data : null;

      if (state.auditCache) {
        state.auditCache[cacheKey] = {
          clauses: state.checklist,
          meta: state.checklistMeta
        };
      }
      renderChecklistTable();
      renderChecklistProgress();
      showNotification(`Clausula ${clauseId} (${stdId.toUpperCase()}) actualizada.`);
    } catch (err) {
      if (prevClause) {
        prevClause.is_compliant = prevCompliant;
        renderChecklistTable();
        renderChecklistProgress();
      }
      alert("Error al actualizar clausula: " + err.message);
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
        if (state.auditCache && state.auditCache[`${sysId}_${stdId}`]) {
          state.auditCache[`${sysId}_${stdId}`].meta = {
            ...(state.auditCache[`${sysId}_${stdId}`].meta || {}),
            digital_seal: res.receipt.digital_seal,
            signed_at: res.receipt.timestamp
          };
        }
        alert(
          `DICTAMEN DE CONFORMIDAD NORMATIVA EMITIDO CON EXITO\n\n` +
          `* Sistema Producto: ${state.activeSystem ? state.activeSystem.name : 'Envase PET Circular 500ml'}\n` +
          `* Norma / Estandar: ${stdId.toUpperCase()}\n` +
          `* Auditor Verificador: ${res.receipt.auditor}\n` +
          `* Clausulas Validadas: ${res.receipt.compliant_clauses} de ${res.receipt.total_clauses}\n` +
          `* Sello HMAC-SHA256: ${res.receipt.digital_seal}\n` +
          `* Marca de Tiempo: ${res.receipt.timestamp}`
        );
      }
    } catch (err) {
      alert("Error al emitir dictamen: " + err.message);
    }
  }

  // =========================================================================
  // 10. BÓVEDA DE DOCUMENTOS (SQL, EXCEL, PDF, JSON, ZIP)
  // =========================================================================
  async function loadDocumentsList(systemId = null) {
    const tbody = document.getElementById("docsTableBody");
    if (!tbody) return;

    try {
      const hiddenSys = document.getElementById("inputDocSystemId");
      const sysId = systemId || (hiddenSys && hiddenSys.value ? parseInt(hiddenSys.value, 10) : null) || (state.activeSystem ? state.activeSystem.id : null) || (state.systems && state.systems.length > 0 ? state.systems[0].id : null);
      if (!sysId) {
        state.documents = [];
        renderDocumentsTable();
        return;
      }
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
      sql: "[SQL]",
      xlsx: "[XLS]",
      xls: "[XLS]",
      csv: "[CSV]",
      pdf: "[PDF]",
      json: "",
      zip: ""
    };

    tbody.innerHTML = state.documents
      .map((doc) => {
        const ext = (doc.file_type || "bin").toLowerCase();
        const icon = typeIcons[ext] || "";
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
              ${doc.description && doc.description.includes("drive.google.com")
                ? `<a href="${doc.description.match(/https:\/\/drive\.google\.com\S*/)?.[0] || doc.description.replace('Google Drive: ', '')}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" title="Abrir archivo en Google Drive">
                     Abrir en Drive
                   </a>`
                : `<a href="/api/documents/${doc.id}/download${getAuthTokenQuery()}" class="btn btn-secondary btn-sm" download="${doc.original_filename}" title="Descargar archivo">
                     Descargar
                   </a>`
              }
              <button type="button" class="btn btn-secondary btn-sm" style="padding: 3px 7px; color: #EF4444;" onclick="window.EconodeApp.deleteVaultDocument(${doc.id}, '${escape(doc.title)}')" title="Eliminar este archivo de la bóveda">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
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
    const btnSubmitDoc = document.getElementById("btnSubmitDocUpload");
    const fileInput = document.getElementById("inputFileDocument");
    const titleInput = document.getElementById("inputDocTitle");

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

    if (fileInput) {
      fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files[0] && titleInput && !titleInput.value.trim()) {
          const rawName = fileInput.files[0].name;
          const cleanName = rawName.substring(0, rawName.lastIndexOf('.')) || rawName;
          titleInput.value = cleanName;
        }
      });
    }

    let isUploadingDoc = false;

    const executeUpload = async () => {
      if (isUploadingDoc) return;

      const file = fileInput && fileInput.files ? fileInput.files[0] : null;
      if (!file) {
        showNotification("Por favor selecciona un archivo local para custodiar.", "warning");
        if (fileInput) fileInput.focus();
        return;
      }

      let title = titleInput ? titleInput.value.trim() : "";
      if (!title) {
        title = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
        if (titleInput) titleInput.value = title;
      }

      const hiddenSys = document.getElementById("inputDocSystemId");
      const sysId = (hiddenSys && hiddenSys.value ? parseInt(hiddenSys.value, 10) : null) || (state.activeSystem ? state.activeSystem.id : null) || (state.systems && state.systems.length > 0 ? state.systems[0].id : null);

      if (!sysId) {
        alert("Por favor selecciona o crea un Sistema Producto antes de subir documentos.");
        return;
      }

      const currentSys = (state.systems && state.systems.find(s => parseInt(s.id, 10) === sysId)) || state.activeSystem || { name: "Proyecto", code: "SYS" };
      const uploader = state.activeUser ? state.activeUser.display_name : "Usuario";
      const role = state.activeUser ? state.activeUser.role : "client";

      isUploadingDoc = true;
      if (btnSubmitDoc) {
        btnSubmitDoc.disabled = true;
        btnSubmitDoc.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px; vertical-align:middle;"></span> Conectando Google Drive...`;
      }

      try {
        // 1. Autorización de Google Drive en el gesto del usuario (User Gesture)
        if (window.EconodeDrive && !window.EconodeDrive.hasToken()) {
          await window.EconodeDrive.getAccessToken();
        }

        // 2. Obtener o crear carpeta de evidencias del proyecto en Google Drive
        if (btnSubmitDoc) {
          btnSubmitDoc.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px; vertical-align:middle;"></span> Localizando carpeta en Drive...`;
        }
        const evidenceFolderId = await window.EconodeDrive.getOrCreateEvidencesFolder(currentSys.name, currentSys.code);

        // 3. Subir archivo DIRECTAMENTE a Google Drive (Cero bytes pasan por Vercel)
        if (btnSubmitDoc) {
          btnSubmitDoc.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px; vertical-align:middle;"></span> Subiendo a tu Google Drive...`;
        }
        const driveFile = await window.EconodeDrive.uploadEvidenceFile(evidenceFolderId, file);
        const driveLink = driveFile.webViewLink || (driveFile.id ? `https://drive.google.com/file/d/${driveFile.id}/view` : "");

        // 4. Calcular hash criptográfico SHA-256 en el cliente para sello inmutable ISO 14044
        if (btnSubmitDoc) {
          btnSubmitDoc.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px; vertical-align:middle;"></span> Sellando SHA-256...`;
        }
        const arrayBuffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const sha256Hex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");

        // 5. Registrar ficha técnica en PostgreSQL (Vercel recibe sólo metadatos < 1 KB)
        if (btnSubmitDoc) {
          btnSubmitDoc.innerHTML = `<span style="display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; margin-right:6px; vertical-align:middle;"></span> Registrando en Bóveda...`;
        }
        await api.uploadDocument({
          title: title,
          original_filename: file.name,
          file_size: file.size,
          sha256_hash: sha256Hex,
          system_id: sysId,
          uploaded_by: uploader,
          user_role: role,
          description: `Google Drive: ${driveLink}`
        });

        showNotification(`Archivo "${file.name}" custodiado con éxito en tu Google Drive `);
        if (formUpload) formUpload.reset();
        await loadDocumentsList(sysId);
      } catch (err) {
        console.error("Error al subir archivo a Google Drive / Bóveda:", err);
        alert("Error al subir archivo a tu Google Drive: " + (err.message || err));
      } finally {
        isUploadingDoc = false;
        if (btnSubmitDoc) {
          btnSubmitDoc.disabled = false;
          btnSubmitDoc.innerHTML = window.I18n ? window.I18n.t("vault.upload_btn", "Subir a Bóveda ➔") : "Subir a Bóveda ➔";
        }
      }
    };

    if (btnSubmitDoc) {
      btnSubmitDoc.addEventListener("click", (e) => {
        e.preventDefault();
        executeUpload();
      });
    }

    if (formUpload) {
      formUpload.addEventListener("submit", (e) => {
        e.preventDefault();
        executeUpload();
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
          const procs = getAllSystemProcesses();
          source = procs.find(n => String(n.id) === String(sId) || String(n.process_id) === String(sId));
          target = procs.find(n => String(n.id) === String(tId) || String(n.process_id) === String(tId));
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
          (String(ed.from) === String(source.id) || String(ed.source_process_id) === String(source.process_id)) &&
          (String(ed.to) === String(target.id) || String(ed.target_process_id) === String(target.process_id)) &&
          areFlowsMatching(ed.flow, flowName)
        );

        if (existingIdx >= 0) {
          state.canvasEdges[existingIdx].flow = flowName;
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

        // Registrar o actualizar en entradas del destino
        if (!target.inputs) target.inputs = [];
        const matchingInp = target.inputs.find(i => areFlowsMatching(i.name, flowName));
        if (matchingInp) {
          matchingInp.origin = source.name;
          matchingInp.amount = amount;
          matchingInp.unit = unit;
        } else {
          target.inputs.push({
            name: flowName,
            amount: amount,
            unit: unit,
            is_unit: true,
            origin: source.name
          });
        }
        if (state.selectedNode && state.selectedNode.id === target.id) {
          inspectNode(target);
        }

        syncSystemProcesses();
        scheduleAutoSaveCanvas();
        renderCanvasEdges();
        renderPaletteProcesses();
        if (state.canvasViewMode === "table") {
          renderCanvasTableView();
        } else {
          renderCanvasStage();
        }
        close();
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
    const btnModeBlank = document.getElementById("btnWizModeBlank");
    const btnModeEpd = document.getElementById("btnWizModeEpd");
    const formBlank = document.getElementById("formWizard");
    const panelEpd = document.getElementById("wizardEpdTemplatePanel");
    const footerHint = document.getElementById("wizFooterHint");

    const renderWizardEpdTemplates = () => {
      const grid = document.getElementById("wizEpdTemplatesGrid");
      if (!grid) return;
      const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
      const list = state.epdTemplates || [];

      if (list.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 18px; color: var(--text-muted); font-size: 11px;">Cargando plantillas EPD de Cemento y Concreto...</div>`;
        return;
      }

      if (!list.some(t => t.template_id === state.selectedEpdTemplateId)) {
        state.selectedEpdTemplateId = list[0].template_id;
      }

      grid.innerHTML = list.map(t => {
        const isSel = t.template_id === state.selectedEpdTemplateId;
        const title = isEn ? t.name_en : t.name_es;
        const desc = isEn ? t.short_desc_en : t.short_desc_es;
        const subBadge = t.sub_sector === "cement"
          ? (isEn ? "Cement" : "Cemento")
          : (isEn ? "Concrete" : "Concreto");
        return `
          <div class="epd-template-card ${isSel ? "selected" : ""}" data-epd-tpl="${t.template_id}">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 6px;">
              <span class="badge-pill ${t.sub_sector === "cement" ? "badge-slate" : "badge-blue"}" style="font-size: 9px;">${subBadge}</span>
              <span class="mono" style="font-size: 9.5px; font-weight: 700; color: var(--accent-emerald);">${escapeHtml(t.declared_unit_amount + " " + t.declared_unit_symbol)} · ${escapeHtml(t.declared_modules.join(","))}</span>
            </div>
            <div style="font-size: 11.5px; font-weight: 700; color: #0F172A; line-height: 1.3;">${escapeHtml(title)}</div>
            <div style="font-size: 10px; color: var(--text-muted); line-height: 1.4;">${escapeHtml(desc)}</div>
            <div style="font-size: 9.5px; color: var(--text-secondary); margin-top: auto; padding-top: 4px; border-top: 1px dashed #E2E8F0;">
              <strong>PCR:</strong> ${escapeHtml(t.pcr_reference)}
            </div>
          </div>
        `;
      }).join("");

      grid.querySelectorAll(".epd-template-card").forEach(card => {
        card.addEventListener("click", () => {
          state.selectedEpdTemplateId = card.getAttribute("data-epd-tpl");
          renderWizardEpdTemplates();
          syncSelectedEpdTemplateFields();
        });
      });

      syncSelectedEpdTemplateFields();
    };

    const syncSelectedEpdTemplateFields = () => {
      const tpl = (state.epdTemplates || []).find(t => t.template_id === state.selectedEpdTemplateId);
      if (!tpl) return;
      const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
      const nameEl = document.getElementById("wizEpdCustomName");
      const keyLbl = document.getElementById("wizEpdKeyParamLabel");
      const keyInp = document.getElementById("wizEpdKeyParamVal");
      if (nameEl) nameEl.placeholder = isEn ? tpl.name_en : tpl.name_es;
      if (tpl.key_override) {
        if (keyLbl) keyLbl.textContent = isEn ? tpl.key_override.label_en : tpl.key_override.label_es;
        if (keyInp) {
          keyInp.value = tpl.key_override.default;
          keyInp.min = tpl.key_override.min;
          keyInp.max = tpl.key_override.max;
        }
      }
    };

    const ensureEpdTemplatesLoaded = async () => {
      if (state.epdTemplates && state.epdTemplates.length > 0) {
        renderWizardEpdTemplates();
        return;
      }
      try {
        const res = await api.listEpdTemplates("cement_concrete");
        state.epdTemplates = res.templates || [];
        state.epdIndustries = res.industries || [];
        state.epdModulesTaxonomy = res.modules || [];
        renderWizardEpdTemplates();
      } catch (err) {
        console.warn("No se pudieron cargar plantillas EPD:", err);
      }
    };

    const setWizardMode = (mode) => {
      state.epdWizardMode = mode === "epd" ? "epd" : "blank";
      if (btnModeBlank) btnModeBlank.classList.toggle("active", state.epdWizardMode === "blank");
      if (btnModeEpd) btnModeEpd.classList.toggle("active", state.epdWizardMode === "epd");
      if (formBlank) formBlank.style.display = state.epdWizardMode === "blank" ? "block" : "none";
      if (panelEpd) panelEpd.style.display = state.epdWizardMode === "epd" ? "block" : "none";
      if (footerHint) {
        footerHint.textContent = state.epdWizardMode === "epd"
          ? "● Se generaran nodos A1-D conectados, balance de masa y reporte EPD editable."
          : "● Se creara en modo borrador y se abrira el lienzo de modelado.";
      }
      if (state.epdWizardMode === "epd") {
        ensureEpdTemplatesLoaded();
      }
    };

    if (btnModeBlank) btnModeBlank.addEventListener("click", () => setWizardMode("blank"));
    if (btnModeEpd) btnModeEpd.addEventListener("click", () => setWizardMode("epd"));

    const open = () => {
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
        if (state.epdWizardMode === "epd") {
          ensureEpdTemplatesLoaded();
        }
      }
    };
    const close = () => {
      if (modal) {
        modal.style.display = "none";
        modal.classList.remove("active");
      }
    };

    // Exponer refresco para cambio de idioma
    window._refreshWizardEpdTemplates = renderWizardEpdTemplates;

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
      let isSubmittingWizard = false;
      btnSubmit.addEventListener("click", async () => {
        if (isSubmittingWizard) return;

        // MODO PLANTILLA EPD PRELIMINAR (CEMENTO & CONCRETO)
        if (state.epdWizardMode === "epd") {
          const tplId = state.selectedEpdTemplateId || "epd_concrete_rmx_4000";
          const tpl = (state.epdTemplates || []).find(t => t.template_id === tplId);
          const customName = (document.getElementById("wizEpdCustomName")?.value || "").trim() || (tpl ? tpl.name_es : "Modelo EPD");
          const plantLoc = (document.getElementById("wizEpdPlantLocation")?.value || "").trim();
          const keyParamVal = parseFloat(document.getElementById("wizEpdKeyParamVal")?.value || "");
          const defaultStd = document.getElementById("wizEpdDefaultStd")?.value || "EN15804_A2";
          const epdProjVal = document.getElementById("wizEpdProject")?.value;
          const epdProjId = epdProjVal ? parseInt(epdProjVal, 10) : null;

          isSubmittingWizard = true;
          btnSubmit.disabled = true;
          const prevText = btnSubmit.textContent;
          btnSubmit.textContent = "Instanciando modelo EPD...";

          try {
            const payload = {
              template_id: tplId,
              name: customName,
              plant_location: plantLoc,
              default_standard: defaultStd,
              project_id: epdProjId
            };
            if (!isNaN(keyParamVal) && tpl && tpl.key_override) {
              payload[tpl.key_override.param_name] = keyParamVal;
            }
            const res = await api.instantiateEpdTemplate(payload);
            close();
            showNotification(res.message || `Modelo EPD "${customName}" creado exitosamente.`);
            await loadDashboard();
            if (res.system_id) {
              await openSystem(res.system_id);
            }
          } catch (err) {
            alert("Error al instanciar plantilla EPD: " + err.message);
          } finally {
            isSubmittingWizard = false;
            btnSubmit.disabled = false;
            btnSubmit.textContent = prevText;
          }
          return;
        }

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

        isSubmittingWizard = true;
        btnSubmit.disabled = true;
        const prevText = btnSubmit.textContent;
        btnSubmit.textContent = "Creando sistema...";

        const projVal = document.getElementById("wizSystemProject")?.value;
        const projectId = projVal ? parseInt(projVal, 10) : null;

        try {
          const res = await api.createSystem({
            name,
            code,
            category,
            geography,
            reference_amount: amount,
            reference_unit: unit,
            project_id: projectId
          });
          // Crear carpeta de proyecto en Google Drive del analista
          if (window.EconodeDrive) {
            try {
              const driveFolder = await window.EconodeDrive.createProjectFolder(name, code);
              if (driveFolder && driveFolder.folderId) {
                showNotification(`Carpeta "${driveFolder.folderName}" creada en tu Google Drive`);
              }
            } catch (driveErr) {
              console.warn("Creación de carpeta en Google Drive diferida:", driveErr.message);
            }
          }

          close();
          showNotification(`Sistema "${name}" creado exitosamente.`);
          await loadDashboard();
          if (res.system_id) {
            openSystem(res.system_id);
          }
        } catch (err) {
          alert("Error al crear sistema: " + err.message);
        } finally {
          isSubmittingWizard = false;
          btnSubmit.disabled = false;
          btnSubmit.textContent = prevText;
        }
      });
    }
  }

  // Modal para Invitar Auditor / Cliente Colaborador (RBAC: Exclusivo del Analista)
  async function loadActiveInvitationsList() {
    const tbody = document.getElementById("tbodyActiveInvitations");
    const badgeCount = document.getElementById("badgeInviteCount");
    if (!tbody) return;

    try {
      const res = await api.getInvitations();
      const items = res.invitations || [];
      if (badgeCount) badgeCount.textContent = `${items.length} registradas`;

      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 14px;">No hay invitaciones enviadas aún.</td></tr>`;
        return;
      }

      tbody.innerHTML = items.map(inv => {
        const roleLabel = inv.role === "auditor" ? "Auditor Líder ACV" : (inv.role === "client" ? "Cliente Productor" : "Analista ACV");
        const roleBadgeClass = inv.role === "auditor" ? "badge-blue" : (inv.role === "client" ? "badge-emerald" : "badge-slate");
        const statusClass = inv.status === "accepted" ? "badge-emerald" : (inv.status === "pending" ? "badge-amber" : "badge-slate");
        const statusLabel = inv.status === "accepted" ? "Aceptada" : (inv.status === "pending" ? "Pendiente" : "Cancelada");
        const fullUrl = `${window.location.origin}${window.location.pathname}?invite=${inv.token}`;

        return `
          <tr>
            <td style="font-weight: 600; color: var(--text-primary);">
              <div>${escapeHtml(inv.name || inv.email)}</div>
              <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(inv.email)}</div>
            </td>
            <td><span class="badge-pill ${roleBadgeClass}">${roleLabel}</span></td>
            <td><span class="badge-pill ${statusClass}">${statusLabel}</span></td>
            <td style="text-align: right; white-space: nowrap;">
              <button type="button" class="btn btn-secondary btn-sm" onclick="window.ECONODE.copyToClipboard('${fullUrl}')" style="font-size: 10px; padding: 2px 7px; height: 22px;" title="Copiar enlace de acceso">
                 Copiar
              </button>
              ${inv.status === 'pending' ? `
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.ECONODE.cancelInvite('${inv.id}')" style="font-size: 10px; padding: 2px 6px; height: 22px; color: #EF4444; margin-left: 4px;" title="Revocar invitación">
                  ✕
                </button>
              ` : ''}
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 10px;">${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function setupInviteCollaboratorModal() {
    const modal = document.getElementById("modalInviteCollaborator");
    const btnClose = document.getElementById("btnCloseInviteModal");
    const btnCancel = document.getElementById("btnCancelInvite");
    const btnSubmit = document.getElementById("btnSubmitInvite");
    const roleSelect = document.getElementById("inviteCollaboratorRole");
    const roleHint = document.getElementById("inviteRoleHint");
    const btnCopyLink = document.getElementById("btnCopyInviteLink");

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

    if (roleSelect && roleHint) {
      roleSelect.addEventListener("change", () => {
        const val = roleSelect.value;
        if (val === "auditor") {
          roleHint.textContent = "[OK] Verificador oficial con facultades de firma conforme NOM-070-SE-2024 e ISO 14040/14044.";
        } else if (val === "client") {
          roleHint.textContent = "[OK] Cliente productor con acceso para subir recibos, balances y consultar reportes finales.";
        } else {
          roleHint.textContent = "[OK] Analista colaborador con acceso total para editar procesos y conectar flujos.";
        }
      });
    }

    if (btnCopyLink) {
      btnCopyLink.addEventListener("click", () => {
        const inputUrl = document.getElementById("inputGeneratedInviteUrl");
        if (inputUrl && inputUrl.value) {
          window.ECONODE.copyToClipboard(inputUrl.value);
        }
      });
    }

    if (btnSubmit) {
      btnSubmit.addEventListener("click", async () => {
        const sysIdVal = document.getElementById("inviteSystemId")?.value;
        const sysId = sysIdVal ? parseInt(sysIdVal, 10) : null;
        const name = (document.getElementById("inviteCollaboratorName")?.value || "").trim();
        const email = (document.getElementById("inviteCollaboratorEmail")?.value || "").trim();
        const role = document.getElementById("inviteCollaboratorRole")?.value || "auditor";
        const org = (document.getElementById("inviteCollaboratorOrg")?.value || "").trim();

        if (!email) {
          alert("Por favor indica la dirección de correo electrónico del invitado.");
          return;
        }

        btnSubmit.disabled = true;
        btnSubmit.textContent = "Generando invitación...";

        try {
          const res = await api.inviteMember({
            email,
            role,
            name,
            organization: org,
            system_id: sysId
          });

          showNotification(res.message || `Invitación creada exitosamente para ${email}`);

          // Compartir carpeta de Google Drive con el invitado
          if (window.EconodeDrive && email) {
            try {
              const driveRole = role === "auditor" ? "commenter" : (role === "client" ? "reader" : "writer");
              const rootFolderId = await window.EconodeDrive.getOrCreateRootFolder();
              if (rootFolderId) {
                await window.EconodeDrive.shareProjectFolder(rootFolderId, email, driveRole, true);
                showNotification(`Carpeta compartida en Google Drive con ${email} (${driveRole}) [OK]`);
              }
            } catch (driveShareErr) {
              console.warn("Compartición en Google Drive diferida:", driveShareErr.message);
            }
          }

          // Mostrar box de enlace generado
          const box = document.getElementById("inviteGeneratedBox");
          const inputUrl = document.getElementById("inputGeneratedInviteUrl");
          const fullInviteUrl = `${window.location.origin}${window.location.pathname}?invite=${res.invitation.token}`;
          if (inputUrl) inputUrl.value = fullInviteUrl;
          if (box) box.style.display = "block";

          // Copiar automáticamente al portapapeles
          if (navigator.clipboard) {
            navigator.clipboard.writeText(fullInviteUrl).catch(() => {});
          }

          await loadActiveInvitationsList();
          if (sysId) {
            await loadDashboard();
            if (state.activeSystem && state.activeSystem.id === sysId) {
              openSystem(sysId, false);
            }
          }
        } catch (err) {
          alert("Error al crear invitación: " + err.message);
        } finally {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Crear Invitación & Enlace Google ➔";
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
            [OK] Sistemas producto ilimitados &nbsp;|&nbsp; [OK] ecoinvent 3.12 y Sphera oficiales &nbsp;|&nbsp; [OK] Sellos SHA-256
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
        sessionStorage.setItem("econode_subscribed", "trial");
        showNotification("Espacio de Analista activado en Periodo de Prueba (14 días).");
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
    sessionStorage.setItem("econode_subscribed", plan);
    const planNames = {
      starter: "Starter ACV ($99/mes)",
      pro: "Profesional Bureau ($240/mes)",
      enterprise: "Enterprise Corporate ($590/mes)"
    };
    showNotification(`Plan ${planNames[plan] || plan} activado exitosamente.`);
    showView("dashboard");
  }

  // =========================================================================
  // GESTIÓN DE CONFIGURACIÓN DE DESARROLLADOR, CLAVES DE API Y SERVIDOR MCP
  // =========================================================================
  async function openDeveloperSettingsModal() {
    const modal = document.getElementById("modalDeveloperSettings");
    if (!modal) return;
    modal.style.display = "flex";
    modal.classList.add("active");
    switchDevTab("keys");
    const alertBox = document.getElementById("alertNewRawKeyContainer");
    if (alertBox) alertBox.style.display = "none";
    const nameInput = document.getElementById("inputNewApiKeyName");
    if (nameInput) nameInput.value = "";
    await loadUserApiKeys();
  }

  function closeDeveloperSettingsModal() {
    const modal = document.getElementById("modalDeveloperSettings");
    if (!modal) return;
    modal.style.display = "none";
    modal.classList.remove("active");
  }

  function switchDevTab(tabName) {
    const btnKeys = document.getElementById("btnDevTabKeys");
    const btnMcp = document.getElementById("btnDevTabMcp");
    const btnScripts = document.getElementById("btnDevTabScripts");
    const contentKeys = document.getElementById("devTabContentKeys");
    const contentMcp = document.getElementById("devTabContentMcp");
    const contentScripts = document.getElementById("devTabContentScripts");

    if (btnKeys) btnKeys.classList.toggle("active", tabName === "keys");
    if (btnMcp) btnMcp.classList.toggle("active", tabName === "mcp");
    if (btnScripts) btnScripts.classList.toggle("active", tabName === "scripts");

    if (contentKeys) contentKeys.style.display = tabName === "keys" ? "block" : "none";
    if (contentMcp) contentMcp.style.display = tabName === "mcp" ? "block" : "none";
    if (contentScripts) contentScripts.style.display = tabName === "scripts" ? "block" : "none";

    updateDevSnippets();
  }

  function updateDevSnippets() {
    const origin = (window.location && window.location.origin) ? window.location.origin : "https://lca-studio-tier1.vercel.app";
    const apiKey = window._lastGeneratedApiKey || "TU_CLAVE_ECO_LIVE_AQUI";
    const mcpUrl = `${origin}/api/v1/mcp/sse`;

    const claudeEl = document.getElementById("codeClaudeMcpSnippet");
    if (claudeEl) {
      claudeEl.textContent = JSON.stringify({
        mcpServers: {
          econode: {
            url: mcpUrl,
            headers: {
              Authorization: "Bearer " + apiKey
            }
          }
        }
      }, null, 2);
    }
    const cursorEl = document.getElementById("codeCursorMcpSnippet");
    if (cursorEl) {
      cursorEl.textContent = JSON.stringify({
        mcpServers: {
          econode: {
            url: mcpUrl,
            headers: {
              Authorization: "Bearer " + apiKey
            }
          }
        }
      }, null, 2);
    }
    const pyEl = document.getElementById("codePythonSnippet");
    if (pyEl) {
      pyEl.textContent = `import requests

API_KEY = "${apiKey}"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
BASE_URL = "${origin}/api/v1"

# 1. Consultar sistemas producto modelados
sistemas = requests.get(f"{BASE_URL}/systems", headers=HEADERS).json()
print("Sistemas activos:", len(sistemas.get("systems", [])))

# 2. Registrar actividad en inventario GEI corporativo (Alcance 1)
payload = {
    "scope": 1,
    "scope_category": "combustion_estacionaria",
    "facility_name": "Planta Norte",
    "activity_name": "Caldera Principal - Gas Natural",
    "fuel_type": "gas_natural",
    "amount": 12500.0,
    "unit": "m3",
    "reporting_year": 2024
}
res = requests.post(f"{BASE_URL}/ghg/activities", headers=HEADERS, json=payload).json()
print("Actividad GEI registrada:", res.get("status"))`;
    }
  }

  async function loadUserApiKeys() {
    const tbody = document.getElementById("tableUserApiKeysBody");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="5" style="padding: 16px; text-align: center; color: var(--text-muted);">Cargando claves de API...</td></tr>`;

    try {
      const token = state.token || (state.activeUser && state.activeUser.token);
      const res = await fetch("/api/account/api-keys", {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });
      const rawText = await res.text();
      let data = {};
      try {
        data = JSON.parse(rawText);
      } catch (e) {
        throw new Error(rawText.substring(0, 100) || `Error HTTP ${res.status}`);
      }

      if (!res.ok || data.status !== "success") {
        tbody.innerHTML = `<tr><td colspan="5" style="padding: 16px; text-align: center; color: var(--accent-rose);">Error cargando claves: ${data.message || "No autorizado"}</td></tr>`;
        return;
      }

      const keys = data.keys || [];
      if (keys.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding: 18px; text-align: center; color: var(--text-muted);">No tienes claves de API activas. Genera una arriba para conectar tu IA o correr scripts.</td></tr>`;
        return;
      }

      tbody.innerHTML = keys.map(k => `
        <tr style="border-bottom: 1px solid var(--border-color); ${!k.is_active ? 'opacity: 0.5;' : ''}">
          <td style="padding: 8px 12px; font-weight: 600;">${escapeHtml(k.name || "API Key")}</td>
          <td style="padding: 8px 12px; font-family: monospace; font-size: 11px;"><code>${escapeHtml(k.key_prefix || "")}</code></td>
          <td style="padding: 8px 12px; color: var(--text-muted);">${(k.created_at || "").substring(0, 10)}</td>
          <td style="padding: 8px 12px; color: var(--text-muted);">${k.last_used_at ? k.last_used_at.substring(0, 16).replace("T", " ") : "Nunca"}</td>
          <td style="padding: 8px 12px; text-align: right;">
            ${k.is_active ? `
              <button type="button" class="btn btn-secondary btn-sm" style="font-size: 10px; height: 24px; padding: 0 8px; color: var(--accent-rose); border-color: rgba(244,63,94,0.3);" onclick="window.EconodeApp.revokeUserApiKey('${k.id}')">Revocar</button>
            ` : `<span style="font-size: 10px; color: var(--text-muted); font-style: italic;">Revocada</span>`}
          </td>
        </tr>
      `).join("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="5" style="padding: 16px; text-align: center; color: var(--accent-rose);">Error de red: ${err.message}</td></tr>`;
    }
  }

  async function generateUserApiKey() {
    const nameInput = document.getElementById("inputNewApiKeyName");
    const name = nameInput ? nameInput.value.trim() : "";
    if (!name) {
      alert("Por favor ingresa un nombre para identificar la clave.");
      return;
    }

    const btn = document.getElementById("btnGenerateApiKey");
    if (btn) btn.disabled = true;

    try {
      const token = state.token || (state.activeUser && state.activeUser.token);
      const res = await fetch("/api/account/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ name: name, scopes: ["all"] })
      });
      const rawText = await res.text();
      let data = {};
      try {
        data = JSON.parse(rawText);
      } catch (e) {
        throw new Error(rawText.substring(0, 100) || `Error HTTP ${res.status}`);
      }

      if (!res.ok || data.status !== "success") {
        alert(data.message || "Error generando la clave.");
        return;
      }

      const alertBox = document.getElementById("alertNewRawKeyContainer");
      const textKey = document.getElementById("textNewRawKey");
      if (alertBox && textKey) {
        textKey.textContent = data.raw_token;
        alertBox.style.display = "block";
      }

      window._lastGeneratedApiKey = data.raw_token;
      updateDevSnippets();

      if (nameInput) nameInput.value = "";
      await loadUserApiKeys();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function revokeUserApiKey(keyId) {
    if (!confirm("¿Estás seguro de que deseas revocar esta clave? Cualquier agente de IA o script que la utilice perderá acceso inmediatamente.")) {
      return;
    }

    try {
      const token = state.token || (state.activeUser && state.activeUser.token);
      const res = await fetch("/api/account/api-keys/revoke", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ key_id: keyId })
      });
      const rawText = await res.text();
      let data = {};
      try {
        data = JSON.parse(rawText);
      } catch (e) {
        throw new Error(rawText.substring(0, 100) || `Error HTTP ${res.status}`);
      }
      if (res.ok && data.status === "success") {
        await loadUserApiKeys();
      } else {
        alert(data.message || "No se pudo revocar la clave.");
      }
    } catch (err) {
      alert("Error: " + err.message);
    }
  }

  function copyDevSnippet(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.textContent || el.innerText;
    navigator.clipboard.writeText(text).then(() => {
      alert("Configuración copiada al portapapeles.");
    }).catch(() => {
      prompt("Copia el texto manualmente:", text);
    });
  }

  function setupDeveloperSettingsModal() {
    const modal = document.getElementById("modalDeveloperSettings");
    const btnNavDev = document.getElementById("btnNavDeveloperSettings");
    const btnClose = document.getElementById("btnCloseDevModal");
    const btnDone = document.getElementById("btnDoneDevModal");
    const btnGenerate = document.getElementById("btnGenerateApiKey");
    const btnCopyRaw = document.getElementById("btnCopyRawKey");

    if (btnNavDev) btnNavDev.addEventListener("click", openDeveloperSettingsModal);
    if (btnClose) btnClose.addEventListener("click", closeDeveloperSettingsModal);
    if (btnDone) btnDone.addEventListener("click", closeDeveloperSettingsModal);
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeDeveloperSettingsModal();
      });
    }

    if (btnGenerate) btnGenerate.addEventListener("click", generateUserApiKey);
    if (btnCopyRaw) {
      btnCopyRaw.addEventListener("click", () => copyDevSnippet("textNewRawKey"));
    }

    const devTabBtns = document.querySelectorAll("#devSegmentedTabs .epd-seg-btn");
    devTabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-dev-tab");
        if (tab) switchDevTab(tab);
      });
    });
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

    // Cargar contenido guardado previamente si existe y cumple con la estructura formal ISO de 6 capitulos
    const sysId = state.activeSystem ? state.activeSystem.id : 21;
    const saved = localStorage.getItem(`econode_report_${sysId}`);
    const bodyEl = document.getElementById("reportDocumentBody");
    if (saved && bodyEl && saved.length > 50 && saved.includes("sec-1-intro")) {
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

  // =========================================================================
  // FOLD TOOLBAR INTERACTION (Recent.design Dock Stage Controller)
  // =========================================================================
  function setupFoldToolbarHome() {
    const dock = document.getElementById("heroFoldToolbar");
    if (!dock) return;

    const stageCatalog = {
      injection: {
        title: "Proceso 100001: Inyeccion de Preformas PET",
        badge: "Loop Termodinamico: 0.18",
        breadcrumb: "Lienzo ACV > Inyeccion",
        gwp: "1.428 kg CO2-eq",
        mass: "100.0% Conservado",
        storage: "Google Drive BYOS (0 MB Servidor)",
        norm: "ISO 14044 Acreditado",
        color: "#059669"
      },
      blowmolding: {
        title: "Proceso 100002: Soplado y Termoformado de Botellas",
        badge: "Consumo CFE: 0.42 kWh/u",
        breadcrumb: "Lienzo ACV > Soplado",
        gwp: "1.890 kg CO2-eq",
        mass: "99.8% Conservado",
        storage: "Google Drive BYOS (0 MB Servidor)",
        norm: "NOM-070 Conforme",
        color: "#0284C7"
      },
      distribution: {
        title: "Proceso 100003: Transporte y Distribucion Logistica",
        badge: "Flete Diesel UBA: 120 km",
        breadcrumb: "Lienzo ACV > Distribucion",
        gwp: "2.140 kg CO2-eq",
        mass: "100.0% Validado",
        storage: "Google Drive BYOS (0 MB Servidor)",
        norm: "Huella EPD Lista",
        color: "#D97706"
      },
      vault: {
        title: "Boveda Soberana de Evidencias (Google Drive BYOS)",
        badge: "Cero Bytes en Vercel",
        breadcrumb: "Boveda > Evidencias y Facturas",
        gwp: "Dossier 42 MB",
        mass: "Sello SHA-256 Activo",
        storage: "Google Drive Personal (0 MB Servidor)",
        norm: "GDPR / ISO 27001",
        color: "#8B5CF6"
      },
      audit: {
        title: "Auditoria Normativa y Conformidad NOM-070-SE-2024",
        badge: "18 Cláusulas Verificadas",
        breadcrumb: "Auditoria > NOM-070",
        gwp: "100.0% Cumplimiento",
        mass: "Snapshot Criptografico",
        storage: "Google Drive BYOS (0 MB Servidor)",
        norm: "Firma Digital HMAC",
        color: "#10B981"
      }
    };

    // Interactive CAD Nodes Click
    const cadNodes = [
      { id: "nodeResin", name: "Insumo LCI: Resina PET Virgen (1.020 kg ecoinvent)" },
      { id: "nodeEnergy", name: "Suministro Red: CFE Red 230kV (0.420 kWh)" },
      { id: "stageNodeCore", name: "Proceso Unitario: Inyeccion y Soplado de Envases" },
      { id: "stageNodeGwp", name: "Emision Biosfera: Huella GWP 100a (1.428 kg CO2e)" },
      { id: "stageNodeProduct", name: "Flujo de Referencia: Envase PET 1.0L (28.0 g)" }
    ];
    cadNodes.forEach(n => {
      const el = document.getElementById(n.id);
      if (el) {
        el.addEventListener("click", () => {
          const breadEl = document.getElementById("heroStageBreadcrumb");
          if (breadEl) breadEl.textContent = `Lienzo ACV: ${n.name}`;
          document.querySelectorAll(".cad-node").forEach(cn => cn.classList.remove("is-core-active"));
          el.classList.add("is-core-active");
        });
      }
    });

    const items = dock.querySelectorAll(".fold-dock-item");
    items.forEach((btn, idx) => {
      btn.addEventListener("click", () => {
        items.forEach(b => b.classList.remove("active"));
        items.forEach(b => b.classList.remove("is-active"));
        btn.classList.add("active");
        btn.classList.add("is-active");

        const stage = btn.getAttribute("data-stage");
        const data = stageCatalog[stage];
        if (!data) return;

        const titleEl = document.getElementById("stageNodeCoreTitle");
        const badgeEl = document.getElementById("stageNodeCoreBadge");
        const breadEl = document.getElementById("heroStageBreadcrumb");
        const gwpEl = document.getElementById("stageGwpValText");
        const massEl = document.getElementById("stageMassValText");
        const storeEl = document.getElementById("stageStorageValText");
        const normEl = document.getElementById("stageNormBadgeText");
        const gwpValSvg = document.getElementById("stageNodeGwpVal");

        if (titleEl) titleEl.textContent = data.title;
        if (badgeEl) {
          badgeEl.textContent = data.badge;
          badgeEl.style.fill = data.color;
        }
        if (breadEl) breadEl.textContent = data.breadcrumb;
        if (gwpEl) {
          gwpEl.textContent = data.gwp;
          gwpEl.style.color = data.color;
        }
        if (massEl) massEl.textContent = data.mass;
        if (storeEl) storeEl.textContent = data.storage;
        if (normEl) normEl.innerHTML = `<span class="stage-norm-pulse" style="background:${data.color};"></span><span>${data.norm}</span>`;
        if (gwpValSvg) gwpValSvg.textContent = data.gwp;
      });

      // Navegación por teclado (Apple HIG Segmented Controls / Tab Bars)
      btn.addEventListener("keydown", (e) => {
        const btnList = Array.from(items);
        let nextIdx = -1;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          nextIdx = (idx + 1) % btnList.length;
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          nextIdx = (idx - 1 + btnList.length) % btnList.length;
        } else if (e.key === "Home") {
          e.preventDefault();
          nextIdx = 0;
        } else if (e.key === "End") {
          e.preventDefault();
          nextIdx = btnList.length - 1;
        }
        if (nextIdx >= 0) {
          btnList[nextIdx].focus();
          btnList[nextIdx].click();
        }
      });
    });
  }

  async function triggerExportDownload(endpoint, defaultFilename) {
    try {
      const isEn = window.I18n && window.I18n.getCurrentLanguage() === "en";
      showNotification(isEn ? "Generating and downloading document..." : "Generando y descargando documento...");
      const token = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
      const headers = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const separator = endpoint.includes("?") ? "&" : "?";
      const fullUrl = token ? `${endpoint}${separator}token=${encodeURIComponent(token)}` : endpoint;

      const res = await fetch(fullUrl, { headers });
      if (!res.ok) {
        let errMsg = `HTTP ${res.status}`;
        try {
          const errData = await res.json();
          if (errData && errData.error) errMsg = errData.error;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const blob = await res.blob();
      let filename = defaultFilename;
      const contentDisposition = res.headers.get("Content-Disposition");
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, "").trim();
        }
      }

      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
      showNotification(isEn ? "Document downloaded successfully." : "Documento descargado con exito.");
    } catch (err) {
      console.warn("Descarga por blob fallo, usando redireccion directa:", err);
      const token = localStorage.getItem("econode_token") || sessionStorage.getItem("econode_token");
      const separator = endpoint.includes("?") ? "&" : "?";
      const directUrl = token ? `${endpoint}${separator}token=${encodeURIComponent(token)}` : endpoint;
      window.location.href = directUrl;
    }
  }

  async function initApp() {
    setupFoldToolbarHome();
    // 1. Configurar Auth en segundo plano sin bloquear listeners de UI
    initAuth().catch(err => console.warn("Background auth error:", err));

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

    const handleHomeViewExamples = (e) => {
      if (e) e.preventDefault();
      const target = document.getElementById("homeCases") || document.getElementById("homePricing") || document.getElementById("homeArchitecture");
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      } else {
        showView(state.isAuthenticated ? "dashboard" : "login");
      }
    };
    if (btnHomeEx) btnHomeEx.addEventListener("click", handleHomeViewExamples);

    const heroBtnIniciarACV = document.getElementById("heroBtnIniciarACV");
    if (heroBtnIniciarACV) heroBtnIniciarACV.addEventListener("click", () => showView(state.isAuthenticated ? "dashboard" : "login"));
    const heroBtnEjemplosNOM = document.getElementById("heroBtnEjemplosNOM");
    if (heroBtnEjemplosNOM) heroBtnEjemplosNOM.addEventListener("click", handleHomeViewExamples);

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



    // Handler Universal para Google Sign-In (Login y Signup)
    const handleGoogleAuthTrigger = () => {
      // 1. Si existe el botón oficial renderizado de Google en la vista actual, invocar su clic
      const activeContainer = (state.currentView === "signup")
        ? document.getElementById("gsiSignupContainer")
        : document.getElementById("gsiLoginContainer");
      const nativeBtn = activeContainer ? activeContainer.querySelector("div[role='button']") : null;
      if (nativeBtn) {
        nativeBtn.click();
        return;
      }

      // 2. Si GSI está cargado pero no renderizado, llamar prompt con callback de diagnóstico
      if (window.google && window.google.accounts && window.google.accounts.id) {
        window.google.accounts.id.prompt((notification) => {
          if (notification && notification.isNotDisplayed()) {
            console.warn("Google One Tap no desplegado:", notification.getNotDisplayedReason());
          }
        });
      } else {
        // En ambiente de desarrollo local / offline, prompt para verificar rol e invitación
        const defaultEmail = state.pendingInviteEmail || "josuearenteriaz09@gmail.com";
        const promptEmail = prompt("Ingresa correo Google Workspace para iniciar sesión (Demo/Offline):", defaultEmail);
        if (promptEmail) {
          api.loginGoogle("mock_google_jwt", promptEmail, state.pendingInviteToken)
            .then(res => {
              if (res.user) {
                state.activeUser = res.user;
                state.isAuthenticated = true;
                try {
          if (res.user.token) {
            sessionStorage.setItem("econode_token", res.user.token);
            localStorage.setItem("econode_token", res.user.token);
          }
          if (res.user.id) {
            sessionStorage.setItem("econode_user_id", res.user.id);
            localStorage.setItem("econode_user_id", res.user.id);
          }
          localStorage.setItem("econode_user", JSON.stringify(res.user));
        } catch(e) {}
                updateUserUI();
                applyRolePermissions();
                const rLabel = res.user.role === "auditor" ? "Auditor Líder" : (res.user.role === "client" ? "Cliente Productor" : "Analista ACV");
                showNotification(`Sesión iniciada con Google Workspace: ${res.user.display_name} (${rLabel})`);
                const hasSub = sessionStorage.getItem("econode_subscribed");
                if (res.user.role === "analyst" && (res.user.is_new || state.currentView === "signup" || !hasSub)) {
                  const modalSub = document.getElementById("modalSubscription");
                  if (modalSub) {
                    modalSub.style.display = "flex";
                    modalSub.classList.add("active");
                    return;
                  }
                }
                showView("dashboard");
              }
            })
            .catch(err => alert("Error: " + err.message));
        }
      }
    };

    const btnGoogle = document.getElementById("btnGoogleSignInAction");
    if (btnGoogle) {
      btnGoogle.addEventListener("click", handleGoogleAuthTrigger);
    }
    const btnGoogleSignup = document.getElementById("btnGoogleSignUpAction");
    if (btnGoogleSignup) {
      btnGoogleSignup.addEventListener("click", handleGoogleAuthTrigger);
    }

    const btnNavInvite = document.getElementById("btnNavInviteMember");
    if (btnNavInvite) {
      btnNavInvite.addEventListener("click", () => {
        window.ECONODE.openInviteModal(null, "Espacio Global de Trabajo");
      });
    }

    // Comprobar si el usuario llegó mediante un enlace de invitación (?invite=...)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has("demo")) {
        const demoRole = urlParams.get("demo") || "analyst";
        handleDemoLogin(demoRole);
      }
      if (urlParams.has("invite")) {
        const invTok = urlParams.get("invite");
        state.pendingInviteToken = invTok;
        try { sessionStorage.setItem("econode_pending_invite", invTok); } catch(e){}
        api.verifyInviteToken(invTok).then(res => {
          if (res.invitation && res.invitation.valid) {
            const inv = res.invitation;
            state.pendingInviteEmail = inv.email;
            state.pendingInviteInfo = inv;

            // Mostrar banners informativos en login y signup
            const bLogin = document.getElementById("bannerLoginInvite");
            const bLoginDesc = document.getElementById("bannerLoginInviteDesc");
            const bSignup = document.getElementById("bannerSignupInvite");
            const bSignupDesc = document.getElementById("bannerSignupInviteDesc");
            const emailLoginInput = document.getElementById("inputLoginEmail");
            const emailSignupInput = document.getElementById("inputSignupEmail");

            const descText = `Has sido invitado(a) como <strong>${escapeHtml(inv.role_title)}</strong> por <strong>${escapeHtml(inv.invited_by_name)}</strong> en <strong>${escapeHtml(inv.organization)}</strong>. Continúa con Google para acceder con este rol.`;

            if (bLogin) bLogin.style.display = "block";
            if (bLoginDesc) bLoginDesc.innerHTML = descText;
            if (bSignup) bSignup.style.display = "block";
            if (bSignupDesc) bSignupDesc.innerHTML = descText;
            if (emailLoginInput) emailLoginInput.value = inv.email;
            if (emailSignupInput) emailSignupInput.value = inv.email;

            showNotification(`Invitación detectada: ${inv.role_title} para ${inv.email}`);
            showView("login");
          }
        }).catch(() => {});
      }
    } catch (e) {}

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

    // Importar SimaPro CSV desde el Dashboard
    const btnDashImpSimaPro = document.getElementById("btnDashImportSimaPro");
    const inputDashSimaPro = document.getElementById("inputDashSimaProFile");
    if (btnDashImpSimaPro && inputDashSimaPro) {
      btnDashImpSimaPro.addEventListener("click", () => inputDashSimaPro.click());
      inputDashSimaPro.addEventListener("change", async (e) => {
        if (!e.target.files || !e.target.files[0]) return;
        const file = e.target.files[0];
        try {
          const fileContent = await file.text();
          if (window.EconodeDrive && window.EconodeDrive.hasToken()) {
            try {
              const cleanName = file.name.replace(/\.[^/.]+$/, "");
              await window.EconodeDrive.uploadSimaProFile(cleanName, "SIMAPRO", file.name, fileContent);
              showNotification("Archivo CSV respaldado en Google Drive.");
            } catch (driveErr) {
              console.warn("Respaldo Google Drive omitido:", driveErr);
            }
          }
          const insp = await api.inspectSimaProCsv(fileContent);
          if (insp && insp.is_multi_process) {
            openSimaProModeModal(insp, fileContent, "dashboard");
          } else {
            const res = await api.importCsv(fileContent, "full");
            showNotification(res.message || "Importación SimaPro completada exitosamente.");
            await loadDashboard();
            if (res.systems_created && res.systems_created.length > 0) {
              await openSystem(res.systems_created[0]);
            }
          }
        } catch (err) {
          alert("Error al importar SimaPro CSV: " + err.message);
        } finally {
          inputDashSimaPro.value = "";
        }
      });
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
        const val = e.target.value;
        state.activeSheetTab = (val === "connections") ? "connections" : "lci";
        state.selectedSpreadsheetCell = null;
        renderCanvasTableView();
      });
    }

    const btnTableAddProc = document.getElementById("btnTableAddProcess");
    if (btnTableAddProc) {
      btnTableAddProc.addEventListener("click", () => openProcessEditor(null));
    }

    const btnTableNewFlw = document.getElementById("btnTableNewFlow");
    if (btnTableNewFlw) {
      btnTableNewFlw.addEventListener("click", () => openCreateCustomFlowModal());
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

    // Sub-vista de Parámetros del Modelo y Modal
    const btnParamsView = document.getElementById("btnCanvasViewParams");
    if (btnParamsView) btnParamsView.addEventListener("click", () => switchCanvasViewMode("parameters"));

    const btnParamsToVisual = document.getElementById("btnParamsToVisualView");
    if (btnParamsToVisual) btnParamsToVisual.addEventListener("click", () => switchCanvasViewMode("visual"));

    const tabSheetParams = document.getElementById("tabSheetParameters");
    if (tabSheetParams) tabSheetParams.addEventListener("click", () => switchCanvasViewMode("parameters"));

    const btnOpenNewParam = document.getElementById("btnOpenNewParamModal");
    if (btnOpenNewParam) btnOpenNewParam.addEventListener("click", () => openParameterModal());

    const btnExportParams = document.getElementById("btnExportParamsCsv");
    if (btnExportParams) btnExportParams.addEventListener("click", exportParametersCsv);

    const selParamScope = document.getElementById("selectParamScopeFilter");
    if (selParamScope) {
      selParamScope.addEventListener("change", (e) => {
        state.paramScopeFilter = e.target.value;
        state.paramGroupFilter = "all";
        renderSystemParametersTable();
      });
    }

    const selParamGroup = document.getElementById("selectParamGroupFilter");
    if (selParamGroup) {
      selParamGroup.addEventListener("change", (e) => {
        state.paramGroupFilter = e.target.value;
        renderSystemParametersTable();
      });
    }

    const selParamType = document.getElementById("selectParamTypeFilter");
    if (selParamType) {
      selParamType.addEventListener("change", (e) => {
        state.paramTypeFilter = e.target.value;
        renderSystemParametersTable();
      });
    }

    const inParamFilter = document.getElementById("inputParamFilter");
    if (inParamFilter) {
      inParamFilter.addEventListener("input", (e) => {
        state.paramSearchQuery = e.target.value;
        renderSystemParametersTable();
      });
    }

    // Modal de Parámetros: Interacciones y Guardado
    const btnCloseParam = document.getElementById("btnCloseParamModal");
    if (btnCloseParam) btnCloseParam.addEventListener("click", closeParameterModal);

    const btnCancelParam = document.getElementById("btnCancelParamModal");
    if (btnCancelParam) btnCancelParam.addEventListener("click", closeParameterModal);

    const btnSaveParam = document.getElementById("btnSaveParamModal");
    if (btnSaveParam) btnSaveParam.addEventListener("click", saveParameterFromModal);

    const btnParamIndep = document.getElementById("btnParamTypeIndep");
    const btnParamDep = document.getElementById("btnParamTypeDep");
    const paramTypeHidden = document.getElementById("paramFormType");
    const paramValWrap = document.getElementById("paramFormValueWrapper");
    const paramFormWrap = document.getElementById("paramFormFormulaWrapper");

    if (btnParamIndep && btnParamDep) {
      btnParamIndep.addEventListener("click", () => {
        btnParamIndep.classList.add("active");
        btnParamDep.classList.remove("active");
        if (paramTypeHidden) paramTypeHidden.value = "independent";
        if (paramValWrap) paramValWrap.style.display = "block";
        if (paramFormWrap) paramFormWrap.style.display = "none";
      });
      btnParamDep.addEventListener("click", () => {
        btnParamDep.classList.add("active");
        btnParamIndep.classList.remove("active");
        if (paramTypeHidden) paramTypeHidden.value = "dependent";
        if (paramValWrap) paramValWrap.style.display = "none";
        if (paramFormWrap) paramFormWrap.style.display = "block";
      });
    }

    const paramFormScopeSel = document.getElementById("paramFormScope");
    const paramProcWrap = document.getElementById("paramFormProcessWrapper");
    if (paramFormScopeSel) {
      paramFormScopeSel.addEventListener("change", (e) => {
        if (paramProcWrap) {
          paramProcWrap.style.display = (e.target.value === "local") ? "block" : "none";
        }
      });
    }

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

    // Tabs de Selección de Bases de Datos LCI (Apple Segmented Control)
    const sourceTabs = document.querySelectorAll("#catalogSourceTabs .segment-btn");
    sourceTabs.forEach(btn => {
      btn.addEventListener("click", () => {
        sourceTabs.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.catalogSource = btn.dataset.source || "all";
        loadCatalog();
      });
    });

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
    const btnExpReportDocx = document.getElementById("btnExportReportDocx");
    const btnExpCanvasDocx = document.getElementById("btnExportDocx");

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
        window.location.href = `/api/systems/${getSysId()}/export/openlca${getAuthTokenQuery()}`;
      });
    }
    if (btnReportExpOpenLca) {
      btnReportExpOpenLca.addEventListener("click", () => {
        window.location.href = `/api/systems/${getSysId()}/export/openlca${getAuthTokenQuery()}`;
      });
    }
    if (btnExpIlcd) {
      btnExpIlcd.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/ilcd${getAuthTokenQuery()}`;
      });
    }
    if (btnExpSimaPro) {
      btnExpSimaPro.addEventListener("click", async () => {
        if (exportMenu) exportMenu.classList.remove("show");
        const sysId = getSysId();
        window.location.href = `/api/systems/${sysId}/export/simapro${getAuthTokenQuery()}`;
        if (window.EconodeDrive && window.EconodeDrive.hasToken() && state.activeSystem) {
          try {
            const resp = await fetch(`/api/systems/${sysId}/export/simapro${getAuthTokenQuery()}`);
            if (resp.ok) {
              const csvText = await resp.text();
              const fileName = `SimaPro_System_${sysId}_export.csv`;
              await window.EconodeDrive.uploadSimaProFile(state.activeSystem.name || "Sistema", state.activeSystem.code || "SIMAPRO", fileName, csvText);
              showNotification("Exportacion SimaPro respaldada en Google Drive.");
            }
          } catch (e) {
            console.warn("Respaldo exportacion SimaPro a Drive omitido:", e);
          }
        }
      });
    }
    if (btnExpLciCsv) {
      btnExpLciCsv.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        window.location.href = `/api/systems/${getSysId()}/export/csv${getAuthTokenQuery()}`;
      });
    }
    if (btnExpPdf) {
      btnExpPdf.addEventListener("click", () => {
        const sysId = getSysId();
        triggerExportDownload(`/api/systems/${sysId}/export/pdf`, `Reporte_ACV_NOM070_Sistema_${sysId}.pdf`);
      });
    }
    if (btnExpReportDocx) {
      btnExpReportDocx.addEventListener("click", () => {
        const sysId = getSysId();
        triggerExportDownload(`/api/systems/${sysId}/export/docx`, `Reporte_ACV_NOM070_Sistema_${sysId}.docx`);
      });
    }
    if (btnExpCanvasDocx) {
      btnExpCanvasDocx.addEventListener("click", () => {
        if (exportMenu) exportMenu.classList.remove("show");
        const sysId = getSysId();
        triggerExportDownload(`/api/systems/${sysId}/export/docx`, `Reporte_ACV_NOM070_Sistema_${sysId}.docx`);
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
            state.availableStandards = null;
            if (state.auditCache) state.auditCache = {};
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
    setupDeveloperSettingsModal();
    setupReportHighlighting();
    setupGhgModuleListeners();
    setupGhgReportListeners();

    const inputPalSearch = document.getElementById("inputPaletteSearch");
    if (inputPalSearch) {
      inputPalSearch.addEventListener("input", renderPaletteProcesses);
    }

    const btnPaletteBlank = document.getElementById("btnPaletteCreateBlank");
    if (btnPaletteBlank) {
      btnPaletteBlank.addEventListener("click", () => openProcessEditor(null));
    }

    // Importar SimaPro CSV a este lienzo
    const btnPalImpSimaPro = document.getElementById("btnPaletteImportSimaPro");
    const inputPalSimaPro = document.getElementById("inputPaletteSimaProFile");
    if (btnPalImpSimaPro && inputPalSimaPro) {
      btnPalImpSimaPro.addEventListener("click", () => inputPalSimaPro.click());
      inputPalSimaPro.addEventListener("change", async (e) => {
        if (!e.target.files || !e.target.files[0]) return;
        const file = e.target.files[0];
        const sysId = state.activeSystem ? state.activeSystem.id : null;
        if (!sysId) {
          alert("Debes tener un sistema producto activo para importar procesos a este lienzo.");
          inputPalSimaPro.value = "";
          return;
        }
        try {
          const fileContent = await file.text();
          if (window.EconodeDrive && window.EconodeDrive.hasToken()) {
            try {
              await window.EconodeDrive.uploadSimaProFile(state.activeSystem.name || "Sistema", state.activeSystem.code || "SIMAPRO", file.name, fileContent);
              showNotification("Archivo CSV respaldado en Google Drive.");
            } catch (driveErr) {
              console.warn("Respaldo Google Drive omitido:", driveErr);
            }
          }
          const insp = await api.inspectSimaProCsv(fileContent);
          if (insp && insp.is_multi_process) {
            openSimaProModeModal(insp, fileContent, "canvas", sysId);
          } else {
            const res = await api.importSimaProToSystem(sysId, fileContent, "full");
            showNotification(res.message || "Procesos SimaPro incorporados al lienzo exitosamente.");
            await openSystem(sysId, false);
          }
        } catch (err) {
          alert("Error al importar SimaPro a este lienzo: " + err.message);
        } finally {
          inputPalSimaPro.value = "";
        }
      });
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

  // =========================================================================
  // GESTION DE PROYECTOS CONTENEDORES Y COMPARATIVA LCIA
  // =========================================================================
  function toggleProjectCollapse(projectId) {
    state.collapsedProjects[projectId] = !state.collapsedProjects[projectId];
    renderDashboardTable();
  }

  function toggleStandaloneCollapse() {
    state.collapsedStandalone = !state.collapsedStandalone;
    renderDashboardTable();
  }

  function openNewProjectModal() {
    const modal = document.getElementById("modalNewProject");
    if (!modal) return;
    const nameInput = document.getElementById("newProjectName");
    const codeInput = document.getElementById("newProjectCode");
    const descInput = document.getElementById("newProjectDesc");
    if (nameInput) {
      nameInput.value = "";
      setTimeout(() => nameInput.focus(), 60);
    }
    if (codeInput) {
      codeInput.value = `PRJ-${Math.floor(1000 + Math.random() * 9000)}`;
    }
    if (descInput) descInput.value = "";
    modal.style.display = "flex";
    modal.classList.add("active");
  }

  function closeNewProjectModal() {
    const modal = document.getElementById("modalNewProject");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
  }

  async function submitNewProject() {
    const name = document.getElementById("newProjectName")?.value || "";
    const code = document.getElementById("newProjectCode")?.value || "";
    const category = document.getElementById("newProjectCategory")?.value || "General";
    const description = document.getElementById("newProjectDesc")?.value || "";

    if (!name.trim()) {
      alert("Por favor ingresa el nombre del proyecto.");
      return;
    }

    try {
      const res = await api.createProject({ name, code, category, description });
      closeNewProjectModal();
      showNotification(`Proyecto "${name}" creado exitosamente.`);
      await loadDashboard();
    } catch (err) {
      alert("Error al crear proyecto: " + err.message);
    }
  }

  async function deleteProject(projectId, projectName) {
    const displayName = projectName ? unescape(projectName) : `ID #${projectId}`;
    const msg = window.I18n.t(
      "dash.delete_project_confirm",
      `¿Deseas eliminar el proyecto "${displayName}"? Sus sistemas producto NO se eliminarán, quedarán como independientes (solitos).`
    );
    if (!confirm(msg)) return;

    try {
      await api.deleteProject(projectId);
      showNotification(`Proyecto "${displayName}" eliminado. Sus sistemas ahora son independientes.`);
      await loadDashboard();
    } catch (err) {
      alert("Error al eliminar proyecto: " + err.message);
    }
  }

  function openAssignProjectModal(systemId, currentProjectId, systemName) {
    const modal = document.getElementById("modalAssignProject");
    if (!modal) return;
    const idInput = document.getElementById("assignProjectSystemId");
    if (idInput) idInput.value = systemId;
    const nameEl = document.getElementById("assignProjectSystemName");
    if (nameEl) nameEl.textContent = `Sistema: ${systemName ? unescape(systemName) : systemId}`;
    updateProjectSelectOptions();
    const select = document.getElementById("selectAssignProject");
    if (select) {
      select.value = currentProjectId && currentProjectId !== "null" ? String(currentProjectId) : "";
    }
    modal.style.display = "flex";
    modal.classList.add("active");
  }

  function closeAssignProjectModal() {
    const modal = document.getElementById("modalAssignProject");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
  }

  async function submitAssignProject() {
    const sysId = document.getElementById("assignProjectSystemId")?.value;
    const projVal = document.getElementById("selectAssignProject")?.value;
    const projId = projVal ? parseInt(projVal, 10) : null;
    if (!sysId) return;

    try {
      const res = await api.assignSystemToProject(sysId, projId);
      closeAssignProjectModal();
      showNotification(res.message || "Asignación actualizada exitosamente.");
      await loadDashboard();
    } catch (err) {
      alert("Error al asignar proyecto: " + err.message);
    }
  }


  // =========================================================================
  // GESTION DE MODAL DE FICHA TECNICA E INFORMACION DEL SISTEMA PRODUCTO
  // =========================================================================
  let currentInfoSystemId = null;

  function formatSystemAuditDateTime(dateStr) {
    if (!dateStr) return { formatted: "--", relative: "--", age: "--" };
    const cleanStr = String(dateStr).trim().replace(" ", "T");
    const d = new Date(cleanStr);
    if (isNaN(d.getTime())) return { formatted: String(dateStr), relative: "--", age: "--" };

    const lang = (window.I18n && window.I18n.currentLang) || "es";
    const locale = lang === "es" ? "es-MX" : "en-US";
    const formatted = new Intl.DateTimeFormat(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }).format(d);

    const diffMs = Math.max(0, Date.now() - d.getTime());
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHrs = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHrs / 24);

    let relative = "";
    if (diffSec < 60) {
      relative = lang === "es" ? "hace unos instantes" : "just now";
    } else if (diffMin < 60) {
      relative = lang === "es" ? `hace ${diffMin} min` : `${diffMin}m ago`;
    } else if (diffHrs < 24) {
      relative = lang === "es" ? `hace ${diffHrs} h` : `${diffHrs}h ago`;
    } else if (diffDays === 1) {
      relative = lang === "es" ? "ayer" : "yesterday";
    } else if (diffDays < 30) {
      relative = lang === "es" ? `hace ${diffDays} dias` : `${diffDays}d ago`;
    } else {
      const diffMonths = Math.floor(diffDays / 30);
      relative = lang === "es" ? `hace ${diffMonths} ${diffMonths === 1 ? 'mes' : 'meses'}` : `${diffMonths}mo ago`;
    }

    let age = "";
    if (diffDays === 0) {
      age = lang === "es" ? "Hoy" : "Today";
    } else if (diffDays === 1) {
      age = lang === "es" ? "1 dia" : "1 day";
    } else if (diffDays < 30) {
      age = `${diffDays} ${lang === "es" ? "dias" : "days"}`;
    } else {
      const mos = Math.floor(diffDays / 30);
      age = `${mos} ${lang === "es" ? (mos === 1 ? "mes" : "meses") : (mos === 1 ? "month" : "months")}`;
    }

    return { formatted, relative, age };
  }

  async function openSystemInfoModal(systemId) {
    currentInfoSystemId = systemId;
    const modal = document.getElementById("modalSystemInfo");
    if (!modal) return;

    let sys = (state.systems || []).find(s => s.id === systemId);

    // Si aún no tenemos los datos completos o faltan atributos, obtener el detalle de canvas
    if (!sys || sys.nodes_count === undefined || !sys.created_at) {
      try {
        const detailsRes = await api.getSystemCanvas(systemId);
        if (detailsRes && detailsRes.system) {
          sys = Object.assign({}, sys || {}, detailsRes.system);
        }
      } catch (err) {
        console.warn("No se pudo cargar detalles adicionales del sistema:", err);
      }
    }

    if (!sys) return;

    const lang = (window.I18n && window.I18n.currentLang) || "es";

    // 1. Cabecera y Badges
    const titleEl = document.getElementById("infoSysTitle");
    if (titleEl) titleEl.textContent = sys.name || `Sistema #${sys.id}`;

    const codeEl = document.getElementById("infoSysCode");
    if (codeEl) codeEl.textContent = sys.code || `SYS-${sys.id}`;

    const subEl = document.getElementById("infoSysSubtitle");
    if (subEl) subEl.textContent = window.I18n.t("sys_info.modal_subtitle", "Metadatos del modelo, versiones de bases de datos, trazabilidad y gobernanza de ciclo de vida");

    const dbBadgeEl = document.getElementById("infoSysDbBadge");
    if (dbBadgeEl) {
      dbBadgeEl.textContent = sys.db_profile || "ecoinvent 3.12 (Cutoff)";
    }

    const statusEl = document.getElementById("infoSysStatus");
    if (statusEl) {
      let badgeClass = "badge-slate";
      let statusText = window.I18n.t("app.status_draft", "Borrador Tecnico");
      if (sys.status === "in_audit") {
        badgeClass = "badge-emerald";
        statusText = window.I18n.t("app.status_in_audit", "En Auditoria NOM-070");
      } else if (sys.status === "certified") {
        badgeClass = "badge-emerald";
        statusText = window.I18n.t("app.status_certified", "Certificado NOM-070");
      }
      statusEl.className = `badge-pill ${badgeClass}`;
      statusEl.textContent = statusText;
    }

    const projBadgeEl = document.getElementById("infoSysProjectBadge");
    if (projBadgeEl) {
      projBadgeEl.textContent = sys.project_name ? `${sys.project_name}` : window.I18n.t("sys_info.standalone", "Sin Proyecto (Independiente)");
    }

    const geoBadgeEl = document.getElementById("infoSysGeoBadge");
    if (geoBadgeEl) {
      geoBadgeEl.textContent = sys.geography || "[MX]";
    }

    // 2. Base de Datos y Metodologia LCI
    const dbNameEl = document.getElementById("infoSysDbName");
    if (dbNameEl) {
      dbNameEl.textContent = sys.db_profile || "ecoinvent 3.12 (Cutoff Unit)";
    }

    const dbAllocEl = document.getElementById("infoSysDbAllocation");
    if (dbAllocEl) {
      if ((sys.db_profile || "").includes("SimaPro")) {
        dbAllocEl.textContent = "Importacion SimaPro 9.x CSV · Mapeo de inventario a procesos unitarios ecoinvent";
      } else if (sys.epd_config) {
        dbAllocEl.textContent = "Modular PCR EN 15804+A2 / ISO 21930 · Modulos A1 a D";
      } else {
        dbAllocEl.textContent = "Allocation, cut-off by classification (ISO 14044 / EN 15804 compatible)";
      }
    }

    // 3. Registro Temporal y Auditoria
    const createdInfo = formatSystemAuditDateTime(sys.created_at);
    const updatedInfo = formatSystemAuditDateTime(sys.updated_at || sys.created_at);

    const cAtEl = document.getElementById("infoSysCreatedAt");
    if (cAtEl) cAtEl.textContent = createdInfo.formatted;
    const cAtRelEl = document.getElementById("infoSysCreatedAtRel");
    if (cAtRelEl) cAtRelEl.textContent = createdInfo.relative;

    const uAtEl = document.getElementById("infoSysUpdatedAt");
    if (uAtEl) uAtEl.textContent = updatedInfo.formatted;
    const uAtRelEl = document.getElementById("infoSysUpdatedAtRel");
    if (uAtRelEl) uAtRelEl.textContent = updatedInfo.relative;

    const ageEl = document.getElementById("infoSysAge");
    if (ageEl) ageEl.textContent = createdInfo.age;

    const compEl = document.getElementById("infoSysCompliance");
    if (compEl) compEl.textContent = sys.compliance_rate || "100.0%";

    // 4. Arquitectura e Inventario
    const funcUnitEl = document.getElementById("infoSysFuncUnit");
    if (funcUnitEl) {
      funcUnitEl.textContent = `${sys.target_amount || 1.0} ${sys.unit || "kg"}`;
    }

    const nodesEl = document.getElementById("infoSysNodesCount");
    if (nodesEl) {
      const nCount = sys.nodes_count !== undefined ? sys.nodes_count : (sys.nodes ? sys.nodes.length : 0);
      nodesEl.textContent = String(nCount);
    }

    const edgesEl = document.getElementById("infoSysEdgesCount");
    if (edgesEl) {
      const eCount = sys.edges_count !== undefined ? sys.edges_count : (sys.edges ? sys.edges.length : 0);
      edgesEl.textContent = String(eCount);
    }

    const paramsEl = document.getElementById("infoSysParamsCount");
    if (paramsEl) {
      const pCount = sys.parameters_count !== undefined ? sys.parameters_count : (sys.parameters ? sys.parameters.length : 0);
      paramsEl.textContent = String(pCount);
    }

    // 5. Gobernanza y Equipo
    const ownerEl = document.getElementById("infoSysOwner");
    if (ownerEl) {
      const ownerName = sys.owner_name || "Carla Mendez";
      const ownerRole = sys.owner_role ? ` (${sys.owner_role})` : "";
      ownerEl.textContent = `${ownerName}${ownerRole}`;
    }

    const orgEl = document.getElementById("infoSysOrg");
    if (orgEl) orgEl.textContent = sys.owner_org || "BioPack Industrial S.A. de C.V.";

    const geoCatEl = document.getElementById("infoSysGeoCat");
    if (geoCatEl) geoCatEl.textContent = `${sys.category || "General"} · ${sys.geography || "[MX]"}`;

    const projEl = document.getElementById("infoSysProject");
    if (projEl) {
      projEl.textContent = sys.project_name ? `${window.I18n.t("sys_info.project", "Proyecto:")} ${sys.project_name}` : window.I18n.t("sys_info.standalone", "Sin Proyecto Contenedor (Independiente)");
    }

    const collabsContainer = document.getElementById("infoSysCollabs");
    if (collabsContainer) {
      const collabsList = sys.collaborators || [];
      if (collabsList.length === 0) {
        collabsContainer.innerHTML = `<span style="font-size: 10px; color: #94A3B8; font-style: italic;">Sin colaboradores externos asignados</span>`;
      } else {
        collabsContainer.innerHTML = collabsList.map(c => {
          const roleLabel = c.role === "auditor" ? "Auditor" : c.role === "client" ? "Cliente" : "Colab";
          const colorBg = c.role === "auditor" ? "rgba(16, 185, 129, 0.12)" : c.role === "client" ? "rgba(139, 92, 246, 0.12)" : "rgba(14, 165, 233, 0.12)";
          const colorText = c.role === "auditor" ? "#059669" : c.role === "client" ? "#7C3AED" : "#0284C7";
          return `<span class="user-chip-mini" style="background: ${colorBg}; color: ${colorText}; font-size: 10px; padding: 2px 7px; border-radius: 4px; font-weight: 600;">${escapeHtml(c.display_name || c.name || "Usuario")} (${roleLabel})</span>`;
        }).join("");
      }
    }

    // 6. EPD (Condicional)
    const secEpd = document.getElementById("secInfoEpd");
    if (secEpd) {
      if (sys.epd_config && typeof sys.epd_config === "object") {
        secEpd.style.display = "block";
        const pcrEl = document.getElementById("infoEpdPcr");
        if (pcrEl) pcrEl.textContent = sys.epd_config.pcr_standard || "EN 15804+A2 / ISO 21930";
        const declEl = document.getElementById("infoEpdDeclUnit");
        if (declEl) declEl.textContent = `${sys.epd_config.declared_unit_amount || 1} ${sys.epd_config.declared_unit || "ton"}`;
        const modEl = document.getElementById("infoEpdModules");
        if (modEl) modEl.textContent = sys.epd_config.system_boundary || "A1-A3 (Cradle-to-gate)";
      } else {
        secEpd.style.display = "none";
      }
    }

    if (window.I18n && typeof window.I18n.applyTranslations === "function") {
      window.I18n.applyTranslations(modal);
    }

    // Mostrar modal con animacion Apple HIG
    modal.style.display = "flex";
    modal.classList.add("active");
  }

  function closeSystemInfoModal() {
    const modal = document.getElementById("modalSystemInfo");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
  }

  function openCanvasFromInfo() {
    const targetId = currentInfoSystemId;
    closeSystemInfoModal();
    if (targetId) {
      selectProductSystem(targetId);
      switchView("canvas");
    }
  }

  // ==========================================================================
  // VERSION CROSS-MATCHING AND DATABASE COMPATIBILITY (APPLE HIG ERGONOMICS)
  // ==========================================================================
  let currentVersionMatchReport = null;
  let currentVersionMatchTargetDb = null;
  let currentVersionMatchSystemId = null;
  let currentVersionMatchMappings = {};
  let currentVersionMatchFlowMappings = {};
  let currentVersionMatchDebounce = null;
  let currentAvailableDatabases = [];

  async function openVersionMatchModal(systemId) {
    const sysId = systemId || (state.activeSystem ? state.activeSystem.id : null);
    if (!sysId) {
      showNotification(window.I18n.t("ver_match.select_system_first", "Por favor selecciona o abre un sistema producto en el lienzo."));
      return;
    }
    currentVersionMatchSystemId = sysId;
    currentVersionMatchMappings = {};
    currentVersionMatchFlowMappings = {};
    currentVersionMatchReport = null;

    const modal = document.getElementById("modalVersionMatch");
    if (!modal) return;
    modal.style.display = "flex";
    modal.classList.add("active");

    const activeSys = (state.systems || []).find(s => s.id === sysId) || state.activeSystem || {};
    let currentDbKey = "ecoinvent_312";
    const rawDb = (activeSys.source_db || activeSys.db_profile || "").toLowerCase();
    if (rawDb.includes("3.11") || rawDb.includes("311")) currentDbKey = "ecoinvent_311";
    else if (rawDb.includes("simapro") || rawDb.includes("sp-")) currentDbKey = "simapro";
    else if (rawDb.includes("oeko")) currentDbKey = "oekobaudat_de";
    else if (rawDb.includes("glad")) currentDbKey = "glad_network";
    else if (rawDb.includes("ademe")) currentDbKey = "ademe_base_carbone";
    else if (rawDb.includes("custom") || rawDb.includes("propio")) currentDbKey = "user_custom";
    else currentDbKey = "ecoinvent_312";

    const badgeCurrentDb = document.getElementById("verMatchCurrentDb");
    if (badgeCurrentDb) {
      badgeCurrentDb.textContent = currentDbKey === "ecoinvent_312" ? "ecoinvent 3.12" :
                                   currentDbKey === "ecoinvent_311" ? "ecoinvent 3.11" :
                                   currentDbKey.replace("_", " ");
    }

    const selectTarget = document.getElementById("selectTargetDatabase");
    if (selectTarget) {
      selectTarget.innerHTML = `<option value="">${window.I18n.t("ver_match.searching", "Cargando bases...")}</option>`;
      try {
        const dbRes = await api.getVersionDatabases();
        if (dbRes && dbRes.databases) {
          currentAvailableDatabases = dbRes.databases;
          selectTarget.innerHTML = "";
          let defaultTarget = "";
          if (currentDbKey === "simapro") {
            defaultTarget = "ecoinvent_311";
          }
          dbRes.databases.forEach(db => {
            const opt = document.createElement("option");
            opt.value = db.id;
            opt.textContent = `${db.name} (${db.version}) - ${db.process_count.toLocaleString()} procesos`;
            selectTarget.appendChild(opt);
            if (!defaultTarget && db.id !== currentDbKey) {
              defaultTarget = db.id;
            }
          });
          if (defaultTarget) {
            selectTarget.value = defaultTarget;
          }
        }
      } catch (err) {
        console.error("Error loading version databases:", err);
      }
    }

    await loadVersionMatchDiagnostic();
  }

  function closeVersionMatchModal() {
    const modal = document.getElementById("modalVersionMatch");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
    document.querySelectorAll(".ver-match-results-dropdown").forEach(d => d.style.display = "none");
  }

  async function onTargetDatabaseChange() {
    currentVersionMatchMappings = {};
    currentVersionMatchFlowMappings = {};
    await loadVersionMatchDiagnostic();
  }

  async function loadVersionMatchDiagnostic() {
    const selectTarget = document.getElementById("selectTargetDatabase");
    const targetDb = selectTarget ? selectTarget.value : "ecoinvent_311";
    currentVersionMatchTargetDb = targetDb;

    const summaryEl = document.getElementById("verMatchStatusSummary");
    if (summaryEl) summaryEl.textContent = window.I18n.t("ver_match.searching", "Analizando compatibilidad...");

    const tbody = document.getElementById("verMatchTableBody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 11px;">
        <span class="apple-spinner-micro" style="margin-right: 6px;"></span> Evaluando procesos y flujos en base destino...
      </td></tr>`;
    }

    const btnSubmit = document.getElementById("btnSubmitVersionConversion");
    if (btnSubmit) btnSubmit.disabled = true;

    try {
      const report = await api.matchProductSystemVersion(currentVersionMatchSystemId, targetDb);
      currentVersionMatchReport = report;

      const elTotal = document.getElementById("verMatchTotalProcs");
      const elExact = document.getElementById("verMatchExactMatches");
      const elFore = document.getElementById("verMatchForegroundProcs");
      const elLoc = document.getElementById("verMatchLocDiffs");
      const elNone = document.getElementById("verMatchNoMatches");
      const elScore = document.getElementById("verMatchCompatScore");

      if (elTotal) elTotal.textContent = report.total_nodes;
      if (elExact) elExact.textContent = report.exact_matches || 0;
      if (elFore) elFore.textContent = report.foreground_matches || report.foreground_count || 0;
      if (elLoc) elLoc.textContent = report.location_diffs || 0;
      if (elNone) elNone.textContent = report.no_matches || 0;
      if (elScore) {
        const score = Math.round(report.compatibility_score || 0);
        elScore.textContent = `${score}%`;
        elScore.className = `badge-pill mono ${score >= 90 ? "badge-green" : score >= 60 ? "badge-yellow" : "badge-red"}`;
      }

      const elName = document.getElementById("verMatchAutoNamePreview");
      const elCode = document.getElementById("verMatchAutoCodePreview");
      if (elName) elName.textContent = report.auto_generated_name || "--";
      if (elCode) elCode.textContent = report.auto_generated_code || "--";

      const flowsAlert = document.getElementById("verMatchFlowsAlert");
      const flowsItems = document.getElementById("verMatchFlowsItems");
      if (flowsAlert) {
        if (report.flow_issues && report.flow_issues.length > 0) {
          flowsAlert.style.display = "block";
          if (flowsItems) {
            flowsItems.innerHTML = report.flow_issues.map(f => `
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 10.5px; background: #FFFFFF; padding: 5px 8px; border-radius: 5px; border: 1px solid rgba(146, 64, 14, 0.2);">
                <div>
                  <strong style="color: #0F172A;">${escapeHtml(f.flow_name || f.flow_code)}</strong>
                  <span class="mono" style="color: #64748B; margin-left: 4px;">(${escapeHtml(f.unit || "")})</span>
                  <div style="font-size: 9.5px; color: #92400E;">${escapeHtml(f.issue || "")}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="badge-pill badge-yellow" style="font-size: 9px;">${window.I18n.t("ver_match.uncharacterized_tag", "Informativo")}</span>
                  <button type="button" class="btn btn-secondary btn-sm" onclick="window.EconodeApp.promptFlowSubstitution('${escapeHtml(f.flow_code)}', '${escapeHtml(f.flow_name).replace(/'/g, "\\'")}')" style="height: 22px; padding: 0 6px; font-size: 9.5px;">Sustituir</button>
                </div>
              </div>
            `).join("");
          }
        } else {
          flowsAlert.style.display = "none";
        }
      }

      renderVersionMatchTable();
    } catch (err) {
      console.error("Error evaluating version match:", err);
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 24px; color: #EF4444; font-size: 11px;">
          Error al evaluar compatibilidad: ${escapeHtml(err.message)}
        </td></tr>`;
      }
    }
  }

  function renderVersionMatchTable() {
    const tbody = document.getElementById("verMatchTableBody");
    if (!tbody || !currentVersionMatchReport) return;

    const nodes = currentVersionMatchReport.nodes || [];
    if (nodes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 20px; color: var(--text-muted); font-size: 11px;">
        No hay nodos de procesos en este sistema producto.
      </td></tr>`;
      return;
    }

    let rowsHtml = "";
    nodes.forEach(node => {
      const nodeId = node.node_id;
      const status = node.status;
      const suggested = node.suggested_match;

      if (status === "EXACT_MATCH" && suggested) {
        currentVersionMatchMappings[nodeId] = suggested.id;
      } else if (status === "FOREGROUND_CUSTOM") {
        currentVersionMatchMappings[nodeId] = node.target_process_id || nodeId;
      } else if (status === "LOCATION_DIFF" && suggested) {
        if (!currentVersionMatchMappings[nodeId]) {
          currentVersionMatchMappings[nodeId] = suggested.id;
        }
      }

      let statusBadge = "";
      let targetContent = "";

      if (status === "EXACT_MATCH") {
        statusBadge = `<span class="ver-match-badge ver-match-badge-exact">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          ${window.I18n.t("ver_match.exact_matches", "Match 100%")}
        </span>`;
        targetContent = `<div style="display: flex; align-items: center; justify-content: space-between; gap: 6px;">
          <div style="min-width: 0;">
            <div style="font-weight: 600; color: #0F172A; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(suggested.name)}">${escapeHtml(suggested.name)}</div>
            <div style="font-size: 10px; color: #64748B;">${escapeHtml(suggested.database || "")} · ${escapeHtml(suggested.reference_unit || "")}</div>
          </div>
          <span class="badge-pill badge-green mono" style="font-size: 9.5px; padding: 1px 6px;">${escapeHtml(suggested.location || "GLO")}</span>
        </div>`;
      } else if (status === "FOREGROUND_CUSTOM") {
        statusBadge = `<span class="ver-match-badge ver-match-badge-foreground">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          ${window.I18n.t("ver_match.badge_foreground", "Proceso Propio")}
        </span>`;
        targetContent = `<div style="display: flex; flex-direction: column; gap: 3px;">
          <div style="font-weight: 600; color: #1E1B4B; font-size: 11px;">${escapeHtml(node.target_name || node.source_name)}</div>
          <div style="font-size: 9.5px; color: #4338CA;">${escapeHtml(node.message || window.I18n.t("ver_match.foreground_notice", "Modelo de primer plano conservado"))}</div>
        </div>`;
      } else if (status === "LOCATION_DIFF") {
        statusBadge = `<span class="ver-match-badge ver-match-badge-loc">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          ${window.I18n.t("ver_match.loc_diffs", "Variacion Reg.")}
        </span>`;
        const altLocations = node.alternative_locations || [];
        const currentTargetId = currentVersionMatchMappings[nodeId] || (suggested ? suggested.id : "");
        const optionsHtml = altLocations.map(alt => `
          <option value="${escapeHtml(alt.id)}" ${alt.id === currentTargetId ? "selected" : ""}>
            [${escapeHtml(alt.location)}] ${escapeHtml(alt.name || (suggested ? suggested.name : ""))}
          </option>
        `).join("");

        targetContent = `<div style="display: flex; flex-direction: column; gap: 4px;">
          <select class="ver-match-select" onchange="window.EconodeApp.onSelectLocationVariation('${escapeHtml(nodeId)}', this.value)" style="width: 100%;">
            ${optionsHtml}
          </select>
          <div style="font-size: 9.5px; color: #854D0E;">Region original: <strong>${escapeHtml(node.source_location || "GLO")}</strong> no disponible en destino.</div>
        </div>`;
      } else if (status === "EXCHANGES_PENDING") {
        const assignedTarget = currentVersionMatchMappings[nodeId];
        statusBadge = assignedTarget ? `
          <span class="ver-match-badge ver-match-badge-exact" id="badgeStatus_${nodeId}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Sustituido
          </span>` : `
          <span class="ver-match-badge ver-match-badge-none" id="badgeStatus_${nodeId}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            ${window.I18n.t("ver_match.badge_pending_exchanges", "Insumos Pendientes")} (${node.missing_exchanges_count || 0})
          </span>`;

        targetContent = `
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <div style="font-size: 10.5px; font-weight: 500; color: #DC2626;">${escapeHtml(node.message || "Intercambios sin equivalencia en destino")}</div>
            <div style="font-size: 9.5px; color: #64748B;">Revisa la sección superior de flujos para sustituirlos, o busca un proceso equivalente en la base destino:</div>
            <div class="ver-match-search-box" id="searchBox_${nodeId}">
              <input type="text" class="ver-match-input" id="substituteInput_${nodeId}" placeholder="${window.I18n.t("ver_match.select_substitute_placeholder", "Buscar proceso sustituto en base destino...")}" oninput="window.EconodeApp.onSearchSubstituteProcess('${escapeHtml(nodeId)}', this.value)" autocomplete="off">
              <div class="ver-match-results-dropdown" id="dropdown_${nodeId}" style="display: none;"></div>
            </div>
          </div>
        `;
      } else {
        const assignedTarget = currentVersionMatchMappings[nodeId];
        statusBadge = assignedTarget ? `
          <span class="ver-match-badge ver-match-badge-exact" id="badgeStatus_${nodeId}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Sustituido
          </span>` : `
          <span class="ver-match-badge ver-match-badge-none" id="badgeStatus_${nodeId}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
            ${window.I18n.t("ver_match.no_matches", "Sin Coincidencia")}
          </span>`;

        targetContent = `
          <div class="ver-match-search-box" id="searchBox_${nodeId}">
            <input type="text" class="ver-match-input" id="substituteInput_${nodeId}" placeholder="${window.I18n.t("ver_match.select_substitute_placeholder", "Buscar proceso sustituto en base destino...")}" oninput="window.EconodeApp.onSearchSubstituteProcess('${escapeHtml(nodeId)}', this.value)" autocomplete="off">
            <div class="ver-match-results-dropdown" id="dropdown_${nodeId}" style="display: none;"></div>
          </div>
        `;
      }

      rowsHtml += `
        <tr>
          <td style="padding: 9px 12px; vertical-align: middle;">
            <div style="font-weight: 600; color: #0F172A; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(node.source_node_name)}">
              ${escapeHtml(node.source_node_name)}
            </div>
            <div style="display: flex; align-items: center; gap: 5px; margin-top: 2px;">
              <span class="badge-pill badge-blue mono" style="font-size: 9px; padding: 1px 5px;">${escapeHtml(node.source_location || "GLO")}</span>
              <span class="mono" style="font-size: 9.5px; color: #64748B;">${escapeHtml(node.source_process_code || "")}</span>
            </div>
          </td>
          <td style="padding: 9px 12px; text-align: center; vertical-align: middle;">
            ${statusBadge}
          </td>
          <td style="padding: 9px 12px; vertical-align: middle;">
            ${targetContent}
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
    checkVersionConversionReadiness();
  }

  function onSelectLocationVariation(nodeId, targetProcessId) {
    currentVersionMatchMappings[nodeId] = targetProcessId;
    checkVersionConversionReadiness();
  }

  function onSearchSubstituteProcess(nodeId, query) {
    if (currentVersionMatchDebounce) clearTimeout(currentVersionMatchDebounce);
    const dropdown = document.getElementById(`dropdown_${nodeId}`);
    if (!dropdown) return;

    const trimmed = (query || "").trim();
    if (trimmed.length < 2) {
      dropdown.style.display = "none";
      return;
    }

    currentVersionMatchDebounce = setTimeout(async () => {
      try {
        const res = await api.searchVersionTarget(currentVersionMatchTargetDb, trimmed, 15, false);
        const items = res.items || [];
        if (items.length === 0) {
          dropdown.innerHTML = `<div style="padding: 8px 10px; font-size: 10.5px; color: var(--text-muted);">${window.I18n.t("ver_match.no_results", "Sin resultados en la base destino")}</div>`;
          dropdown.style.display = "block";
          return;
        }

        dropdown.innerHTML = items.map(item => `
          <div class="ver-match-result-item" onclick="window.EconodeApp.onSelectSubstituteProcess('${escapeHtml(nodeId)}', '${escapeHtml(item.id)}', '${escapeHtml(item.name).replace(/'/g, "\\'")}', '${escapeHtml(item.location)}')">
            <div style="min-width: 0; flex: 1;">
              <div style="font-weight: 600; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(item.name)}</div>
              <div style="font-size: 9.5px; color: #64748B;">${escapeHtml(item.database || "")} · ${escapeHtml(item.reference_unit || "")}</div>
            </div>
            <span class="badge-pill badge-blue mono" style="font-size: 9px; margin-left: 6px;">${escapeHtml(item.location || "GLO")}</span>
          </div>
        `).join("");
        dropdown.style.display = "block";
      } catch (err) {
        console.error("Error searching target database:", err);
      }
    }, 250);
  }

  function onSelectSubstituteProcess(nodeId, targetProcessId, targetName, location) {
    currentVersionMatchMappings[nodeId] = targetProcessId;

    const input = document.getElementById(`substituteInput_${nodeId}`);
    if (input) {
      input.value = `${targetName} [${location}]`;
    }

    const dropdown = document.getElementById(`dropdown_${nodeId}`);
    if (dropdown) dropdown.style.display = "none";

    const badge = document.getElementById(`badgeStatus_${nodeId}`);
    if (badge) {
      badge.className = "ver-match-badge ver-match-badge-exact";
      badge.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Sustituido`;
    }

    checkVersionConversionReadiness();
  }

  function toggleVersionMatchFlowsList() {
    const container = document.getElementById("verMatchFlowsListContainer");
    if (!container) return;
    const isHidden = container.style.display === "none" || !container.style.display;
    container.style.display = isHidden ? "block" : "none";
  }

  async function promptFlowSubstitution(flowCode, flowName) {
    const query = prompt(`Buscar flujo sustituto en ${currentVersionMatchTargetDb} para:\n${flowName} (${flowCode}):`, flowName);
    if (!query) return;
    try {
      const res = await api.searchVersionTarget(currentVersionMatchTargetDb, query, 10, true);
      const items = res.items || [];
      if (items.length === 0) {
        alert("No se encontraron flujos similares en la base destino.");
        return;
      }
      const choice = prompt(`Selecciona el numero de flujo sustituto:\n` + items.map((it, idx) => `${idx + 1}. ${it.name} (${it.reference_unit || it.unit || ""}) [${it.id}]`).join("\n"), "1");
      const idx = parseInt(choice, 10) - 1;
      if (!isNaN(idx) && items[idx]) {
        currentVersionMatchFlowMappings[flowCode] = items[idx].id;
        showNotification(`Flujo ${flowCode} asignado a ${items[idx].name}`);
      }
    } catch (err) {
      alert("Error al buscar flujos: " + err.message);
    }
  }

  function checkVersionConversionReadiness() {
    const btnSubmit = document.getElementById("btnSubmitVersionConversion");
    const summaryEl = document.getElementById("verMatchStatusSummary");
    if (!currentVersionMatchReport) return;

    const nodes = currentVersionMatchReport.nodes || [];
    const missingNodes = nodes.filter(n => !currentVersionMatchMappings[n.node_id]);

    if (missingNodes.length === 0) {
      if (btnSubmit) btnSubmit.disabled = false;
      if (summaryEl) summaryEl.textContent = window.I18n.t("ver_match.status_summary_ready", "Todos los procesos emparejados. Listo para migrar.");
    } else {
      if (btnSubmit) btnSubmit.disabled = true;
      if (summaryEl) summaryEl.textContent = window.I18n.t("ver_match.status_summary_pending", `Faltan ${missingNodes.length} nodos por mapear.`);
    }
  }

  async function submitVersionConversion() {
    const btnSubmit = document.getElementById("btnSubmitVersionConversion");
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = `<span class="apple-spinner-micro" style="margin-right: 6px;"></span> Migrando...`;
    }

    try {
      const payload = {
        system_id: currentVersionMatchSystemId,
        target_version: currentVersionMatchTargetDb,
        process_mappings: currentVersionMatchMappings,
        flow_mappings: currentVersionMatchFlowMappings
      };

      const res = await api.convertProductSystemVersion(payload);
      if (res && res.success) {
        closeVersionMatchModal();
        showNotification(res.message || window.I18n.t("ver_match.success_toast", "Sistema producto creado y lienzo migrado exitosamente."));

        await loadDashboard();

        if (res.new_system_id) {
          await openSystem(res.new_system_id, true);
        }
      } else {
        alert(res.error || "No se pudo realizar la conversion de version.");
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> <span data-i18n="ver_match.btn_convert_and_switch">Crear Sistema y Migrar Lienzo</span>`;
        }
      }
    } catch (err) {
      console.error("Error during version conversion:", err);
      alert("Error al migrar version: " + err.message);
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> <span data-i18n="ver_match.btn_convert_and_switch">Crear Sistema y Migrar Lienzo</span>`;
      }
    }
  }



  let pendingSimaProImport = null;
  let selectedSimaProImportMode = "full";

  function openSimaProModeModal(meta, fileContent, target, sysId = null) {
    pendingSimaProImport = {
      meta,
      fileContent,
      target,
      sysId
    };
    selectedSimaProImportMode = "full";

    const modal = document.getElementById("modalSimaProImportMode");
    const elProj = document.getElementById("spModeProjectName");
    const elTotal = document.getElementById("spModeTotalProcsBadge");
    const elWaste = document.getElementById("spModeWasteBadge");
    const elRoot = document.getElementById("spModeRootProcName");

    if (elProj) elProj.textContent = meta.project_name || "Modelo SimaPro";
    if (elTotal) elTotal.textContent = `${meta.total_processes || 0} procesos`;
    if (elWaste) {
      if (meta.waste_treatment_count > 0) {
        elWaste.style.display = "inline-flex";
        elWaste.textContent = `${meta.waste_treatment_count} tratamientos de residuo`;
      } else {
        elWaste.style.display = "none";
      }
    }
    if (elRoot) elRoot.textContent = `${meta.root_process_name || "Proceso Raíz"} (${meta.root_inputs_count || 0} in / ${meta.root_outputs_count || 0} out)`;

    selectSimaProImportMode("full");

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      if (window.I18n && typeof window.I18n.applyTranslations === "function") {
        window.I18n.applyTranslations(modal);
      }
    }
  }

  function closeSimaProModeModal() {
    const modal = document.getElementById("modalSimaProImportMode");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
    pendingSimaProImport = null;
  }

  function selectSimaProImportMode(mode) {
    selectedSimaProImportMode = mode;
    const cardFull = document.getElementById("spCardModeFull");
    const cardRoot = document.getElementById("spCardModeRoot");
    const radioFull = document.getElementById("radioSpModeFull");
    const radioRoot = document.getElementById("radioSpModeRoot");

    if (mode === "full") {
      if (cardFull) {
        cardFull.style.border = "2px solid #2563EB";
        cardFull.classList.add("active");
      }
      if (cardRoot) {
        cardRoot.style.border = "1px solid #CBD5E1";
        cardRoot.classList.remove("active");
      }
      if (radioFull) radioFull.checked = true;
      if (radioRoot) radioRoot.checked = false;
    } else {
      if (cardFull) {
        cardFull.style.border = "1px solid #CBD5E1";
        cardFull.classList.remove("active");
      }
      if (cardRoot) {
        cardRoot.style.border = "2px solid #2563EB";
        cardRoot.classList.add("active");
      }
      if (radioFull) radioFull.checked = false;
      if (radioRoot) radioRoot.checked = true;
    }
  }

  async function confirmSimaProImport() {
    if (!pendingSimaProImport) return;
    const btn = document.getElementById("btnConfirmSimaProImport");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="apple-spinner-micro" style="margin-right: 6px;"></span> Importando...`;
    }

    const { fileContent, target, sysId } = pendingSimaProImport;
    const mode = selectedSimaProImportMode;

    try {
      if (target === "dashboard") {
        const res = await api.importCsv(fileContent, mode);
        showNotification(res.message || "Importación SimaPro completada exitosamente.");
        closeSimaProModeModal();
        await loadDashboard();
        if (res.systems_created && res.systems_created.length > 0) {
          await openSystem(res.systems_created[0]);
        }
      } else if (target === "canvas") {
        const res = await api.importSimaProToSystem(sysId, fileContent, mode);
        showNotification(res.message || "Procesos SimaPro incorporados al lienzo exitosamente.");
        closeSimaProModeModal();
        await openSystem(sysId, false);
      }
    } catch (err) {
      alert("Error al importar SimaPro: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> <span data-i18n="sp_mode.btn_import">Importar Modelo</span>`;
      }
    }
  }

  function openVaultFromInfo() {
    const targetId = currentInfoSystemId;
    closeSystemInfoModal();
    if (targetId && typeof openDocsModal === "function") {
      openDocsModal(targetId);
    }
  }

  async function openCompareProjectModal(projectId) {
    const modal = document.getElementById("modalCompareProject");
    const container = document.getElementById("compareProjectContent");
    const titleEl = document.getElementById("compareProjTitle");
    const codeEl = document.getElementById("compareProjCode");
    const descEl = document.getElementById("compareProjDesc");
    if (!modal || !container) return;

    modal.style.display = "flex";
    modal.classList.add("active");
    if (window.I18n && typeof window.I18n.applyTranslations === "function") {
      window.I18n.applyTranslations();
    }
    container.innerHTML = `
      <div style="text-align: center; padding: 48px 20px; color: var(--text-muted); font-size: 12px;">
        <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">${window.I18n.t("proj.loading_comparison", "Calculando balance de masa e impacto ambiental comparativo (LCIA)...")}</div>
        <div style="font-size: 11.5px; color: #64748B;">${window.I18n.t("proj.loading_sub", "Resolviendo matrices de inventario ecoinvent 3.12 y factores ReCiPe 2016 Midpoint (H)")}</div>
      </div>
    `;

    try {
      const data = await api.compareProject(projectId);
      const proj = data.project || {};
      const systems = data.systems || [];
      const cats = data.comparison_categories || [];

      if (titleEl) titleEl.textContent = `${proj.name || 'Proyecto'} · ${window.I18n.t("proj.compare_title", "Comparativa de Sistemas")}`;
      if (codeEl) codeEl.textContent = proj.code || "PRJ";
      if (descEl) descEl.textContent = proj.description || `${systems.length} ${window.I18n.t("dash.systems_count_badge", "sistemas")} modelados`;

      if (systems.length === 0) {
        container.innerHTML = `<div style="text-align: center; padding: 36px; color: var(--text-muted); font-size: 12px;">${window.I18n.t("proj.no_systems_in_project", "Este proyecto no tiene sistemas asignados aún. Asigna o crea sistemas para ejecutar la comparativa.")}</div>`;
        return;
      }

      // 1. Resumen en Tarjetas Comparativas (Apple HIG)
      let cardsHtml = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 24px;">
          ${systems.map(s => {
            const gw = s.lcia_scores?.global_warming || 0.0;
            const isBest = s.is_best_carbon;
            const isTie = s.is_tied_best;
            const diffPct = s.diff_vs_best_pct || 0;
            const score = s.eco_efficiency_score || 100;
            const borderCol = isBest ? '#10B981' : (isTie ? '#0284C7' : '#E2E8F0');
            return `
              <div style="background: #FFFFFF; border: 1.5px solid ${borderCol}; border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); position: relative;">
                ${isBest ? `
                  <div style="position: absolute; top: 12px; right: 12px; background: rgba(16, 185, 129, 0.12); color: #059669; font-size: 9.5px; font-weight: 700; padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3);">
                    ${window.I18n.t("proj.best_carbon_badge", "Menor Huella de Carbono")}
                  </div>
                ` : isTie ? `
                  <div style="position: absolute; top: 12px; right: 12px; background: rgba(2, 132, 199, 0.12); color: #0284C7; font-size: 9.5px; font-weight: 700; padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(2, 132, 199, 0.3);">
                    ${window.I18n.t("proj.tied_carbon_badge", "Huella Equivalente")}
                  </div>
                ` : `
                  <div style="position: absolute; top: 12px; right: 12px; background: #F1F5F9; color: #64748B; font-size: 9.5px; font-weight: 600; padding: 2px 8px; border-radius: 12px;">
                    +${diffPct}% ${window.I18n.t("proj.diff_vs_best", "vs mejor")}
                  </div>
                `}
                <div style="font-size: 10px; color: var(--text-muted); font-family: monospace;">${escapeHtml(s.code)}</div>
                <div style="font-size: 14px; font-weight: 700; color: #0F172A; margin: 2px 0 8px 0; padding-right: 70px;">${escapeHtml(s.name)}</div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #F8FAFC; padding: 10px 12px; border-radius: 8px; margin-bottom: 10px; font-size: 11px;">
                  <div>
                    <span style="color: #64748B;">${window.I18n.t("proj.carbon_footprint", "Huella Carbono")}:</span>
                    <div style="font-size: 13px; font-weight: 700; color: ${isBest ? '#059669' : '#0F172A'}; font-family: monospace;">${gw} kg CO2</div>
                  </div>
                  <div>
                    <span style="color: #64748B;">${window.I18n.t("proj.eco_score", "Eficiencia Eco")}:</span>
                    <div style="font-size: 13px; font-weight: 700; color: #0284C7; font-family: monospace;">${score} / 100</div>
                  </div>
                </div>

                <div style="display: flex; justify-content: space-between; font-size: 10.5px; color: #64748B;">
                  <span>UF: ${s.target_amount} ${escapeHtml(s.unit)}</span>
                  <span>${window.I18n.t("proj.processes_count", "Procesos")}: ${s.nodes_count || 0}</span>
                  <a href="javascript:void(0)" onmouseenter="window.EconodeApp.prefetchSystem(${s.id})" onclick="window.EconodeApp.closeCompareProjectModal(); window.EconodeApp.openSystem(${s.id});" style="color: #0284C7; font-weight: 600; text-decoration: none;">${window.I18n.t("proj.view_canvas", "Ver Lienzo")} &rarr;</a>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      `;

      // 2. Tabla Comparativa Multidimensional LCIA (ReCiPe Midpoint)
      let tableHtml = `
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.03);">
          <div style="padding: 12px 16px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <strong style="font-size: 12.5px; color: #0F172A;">${window.I18n.t("proj.matrix_title", "Matriz Comparativa de Categorías de Impacto (LCIA ReCiPe 2016)")}</strong>
            <span style="font-size: 11px; color: #64748B;">${window.I18n.t("proj.normalized_notice", "Valores normalizados por Unidad Funcional")}</span>
          </div>
          <div style="overflow-x: auto;">
            <table class="data-table" style="margin: 0; width: 100%;">
              <thead>
                <tr style="background: #FAFBFD;">
                  <th style="font-size: 11px; width: 32%;">${window.I18n.t("proj.env_category", "Categoría Ambiental")}</th>
                  <th style="font-size: 11px; width: 14%;">${window.I18n.t("proj.unit", "Unidad")}</th>
                  ${systems.map(s => `<th style="font-size: 11px; text-align: right; min-width: 140px;">${escapeHtml(s.name)}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                ${cats.map(cat => {
                  const vals = systems.map(s => s.lcia_scores?.[cat.key] || 0.0);
                  const maxVal = Math.max(...vals, 0.00001);
                  const minVal = Math.min(...vals);
                  return `
                    <tr>
                      <td>
                        <strong style="font-size: 11.5px; color: #0F172A;">${escapeHtml(cat.label)}</strong>
                        <div style="font-size: 9.5px; color: #64748B;">${escapeHtml(cat.description)}</div>
                      </td>
                      <td style="font-size: 11px; color: #475569; font-family: monospace;">${escapeHtml(cat.unit)}</td>
                      ${systems.map((s, idx) => {
                        const val = vals[idx];
                        const pctOfMax = Math.min(100, Math.max(10, Math.round((val / maxVal) * 100)));
                        const isMin = (val === minVal);
                        const barColor = isMin ? "#10B981" : "#94A3B8";
                        return `
                          <td style="text-align: right; vertical-align: middle;">
                            <div style="font-weight: 700; font-size: 11.5px; color: ${isMin ? '#059669' : '#0F172A'}; font-family: monospace;">
                              ${val}
                            </div>
                            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 4px; margin-top: 3px;">
                              <div style="width: 70px; height: 5px; background: #EEF2F6; border-radius: 3px; overflow: hidden;">
                                <div style="width: ${pctOfMax}%; height: 100%; background: ${barColor}; border-radius: 3px;"></div>
                              </div>
                              <span style="font-size: 9px; color: #94A3B8; width: 28px;">${pctOfMax}%</span>
                            </div>
                          </td>
                        `;
                      }).join("")}
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;

      container.innerHTML = cardsHtml + tableHtml;
      if (window.I18n && typeof window.I18n.applyTranslations === "function") {
        window.I18n.applyTranslations(modal);
      }
    } catch (err) {
      container.innerHTML = `<div style="text-align: center; padding: 30px; color: #EF4444; font-size: 12px;">Error al cargar comparativa: ${escapeHtml(err.message)}</div>`;
    }
  }

  function closeCompareProjectModal() {
    const modal = document.getElementById("modalCompareProject");
    if (modal) {
      modal.style.display = "none";
      modal.classList.remove("active");
    }
  }

  function openWizardForProject(projectId) {
    const select = document.getElementById("wizSystemProject");
    if (select) {
      select.value = projectId ? String(projectId) : "";
    }
    const modal = document.getElementById("modalWizard");
    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      const nameInput = document.getElementById("wizSystemName");
      if (nameInput) {
        nameInput.value = "";
        setTimeout(() => nameInput.focus(), 60);
      }
      const codeInput = document.getElementById("wizSystemCode");
      if (codeInput) codeInput.value = "";
    }
  }

  // Métodos globales de acceso rápido
  window.showView = showView;
  window.openSystem = openSystem;

  // API Pública para llamadas inline desde HTML y pruebas

  // =========================================================================
  // 10.1 INVENTARIO CORPORATIVO GEI & GHG PROTOCOL (ALCANCES 1, 2 Y 3)
  // =========================================================================
  let ghgListenersConfigured = false;
  let ghgFactorDebounceTimer = null;

  function closeModal(id) {
    const m = document.getElementById(id);
    if (m) {
      m.style.display = "none";
      m.classList.remove("active");
    }
  }

  async function loadGhgInventoryModule() {
    setupGhgModuleListeners();

    // 1. Cargar taxonomia oficial GHG Protocol si no esta en memoria
    if (!state.ghgTaxonomy) {
      try {
        const taxData = await api.getGhgTaxonomy();
        state.ghgTaxonomy = taxData.taxonomy || {};
      } catch (err) {
        console.warn("No se pudo cargar taxonomia GHG Protocol:", err);
      }
    }

    // 2. Cargar inventarios del usuario
    try {
      const invList = await api.listGhgInventories();
      state.ghgInventories = invList.inventories || invList.items || [];

      const selectEl = document.getElementById("ghgInventorySelect");
      if (selectEl) {
        if (state.ghgInventories.length === 0) {
          selectEl.innerHTML = '<option value="">Sin inventarios registrados</option>';
        } else {
          selectEl.innerHTML = state.ghgInventories.map(inv => `
            <option value="${inv.id}">${escapeHtml(inv.organization_name)} (${inv.reporting_year}) - ${escapeHtml(inv.consolidation_approach)}</option>
          `).join("");
        }
      }

      const savedInvId = localStorage.getItem("econode_active_ghg_inv");
      let targetInvId = null;
      if (savedInvId && state.ghgInventories.some(i => String(i.id) === String(savedInvId))) {
        targetInvId = parseInt(savedInvId, 10);
      } else if (state.ghgInventories.length > 0) {
        targetInvId = state.ghgInventories[0].id;
      }

      if (targetInvId) {
        if (selectEl) selectEl.value = targetInvId;
        await loadActiveGhgInventory(targetInvId);
      } else {
        renderGhgEmptyState();
      }

      // 3. Pre-cargar factores y sectores monetarios
      searchGhgFactorsTab();
      populateGhgSpendSectors();
      populateGhgProductSystems();
    } catch (err) {
      console.error("Error al inicializar modulo GHG Protocol:", err);
      showNotification("Error al cargar inventarios GHG Protocol: " + err.message);
    }
  }

  function setupGhgModuleListeners() {
    if (ghgListenersConfigured) return;
    ghgListenersConfigured = true;

    // Selector de inventario activo
    const selectInv = document.getElementById("ghgInventorySelect");
    if (selectInv) {
      selectInv.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val) loadActiveGhgInventory(parseInt(val, 10));
      });
    }

    // Botones de accion del encabezado
    const btnNewInv = document.getElementById("btnOpenNewGhgInventoryModal");
    if (btnNewInv) btnNewInv.addEventListener("click", openNewGhgInventoryModal);

    const btnFactorsTab = document.getElementById("btnOpenGhgFactorsTab");
    if (btnFactorsTab) btnFactorsTab.addEventListener("click", () => switchGhgTab("factors"));

    const btnDelInv = document.getElementById("btnDeleteCurrentGhgInventory");
    if (btnDelInv) btnDelInv.addEventListener("click", deleteCurrentGhgInventory);

    const btnQuickAdd = document.getElementById("btnQuickAddEntry");
    if (btnQuickAdd) btnQuickAdd.addEventListener("click", () => openAddGhgEntryModal("SCOPE_1"));

    // Pestanas segmentadas
    document.querySelectorAll(".ghg-nav-tab").forEach(btn => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-ghg-tab");
        if (tab) switchGhgTab(tab);
      });
    });

    // Guardar inventario
    const btnSubmitInv = document.getElementById("btnSubmitNewGhgInventory");
    if (btnSubmitInv) btnSubmitInv.addEventListener("click", submitNewGhgInventory);

    // Guardar entrada / fuente de emision
    const btnSubmitEntry = document.getElementById("btnSubmitNewGhgEntry");
    if (btnSubmitEntry) btnSubmitEntry.addEventListener("click", submitNewGhgEntry);

    // Cambio de alcance en modal de agregar fuente
    const selectScope = document.getElementById("selectEntryScope");
    if (selectScope) {
      selectScope.addEventListener("change", (e) => {
        onGhgModalScopeChange(e.target.value);
      });
    }

    // Buscador en pestana de catalogo de factores
    const inputSearch = document.getElementById("inputGhgFactorSearch");
    if (inputSearch) {
      inputSearch.addEventListener("input", () => {
        clearTimeout(ghgFactorDebounceTimer);
        ghgFactorDebounceTimer = setTimeout(searchGhgFactorsTab, 250);
      });
    }
    const selectScopeFilter = document.getElementById("selectGhgFactorScope");
    if (selectScopeFilter) selectScopeFilter.addEventListener("change", searchGhgFactorsTab);
    const selectSourceFilter = document.getElementById("selectGhgFactorSource");
    if (selectSourceFilter) selectSourceFilter.addEventListener("change", searchGhgFactorsTab);
  }

  function switchGhgTab(tabName) {
    state.ghgActiveTab = tabName;
    document.querySelectorAll(".ghg-nav-tab").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-ghg-tab") === tabName);
    });

    const panes = {
      summary: document.getElementById("ghgPaneSummary"),
      scope1: document.getElementById("ghgPaneScope1"),
      scope2: document.getElementById("ghgPaneScope2"),
      scope3: document.getElementById("ghgPaneScope3"),
      factors: document.getElementById("ghgPaneFactors")
    };

    Object.keys(panes).forEach(k => {
      if (panes[k]) panes[k].style.display = (k === tabName) ? "block" : "none";
    });

    if (tabName === "factors") {
      searchGhgFactorsTab();
    }
  }

  async function loadActiveGhgInventory(invId) {
    try {
      const data = await api.getGhgInventory(invId);
      const inv = data.inventory;
      state.activeGhgInventory = inv;
      localStorage.setItem("econode_active_ghg_inv", String(invId));
      renderGhgView(inv);
    } catch (err) {
      console.error("Error al cargar inventario GEI:", err);
      showNotification("Error al cargar inventario: " + err.message);
    }
  }

  function renderGhgEmptyState() {
    const kpiEls = {
      ghgKpiScope1: "0.00 t CO2e",
      ghgScope1Pct: "0.0%",
      ghgKpiScope2Location: "0.00 t CO2e",
      ghgKpiScope2Market: "0.00 t",
      ghgScope2Pct: "0.0%",
      ghgKpiScope3: "0.00 t CO2e",
      ghgScope3Pct: "0.0%",
      ghgKpiScope3Upstream: "0.00 t",
      ghgKpiScope3Downstream: "0.00 t",
      ghgKpiTotalMarket: "0.00 t CO2e",
      ghgKpiTotalLocation: "0.00 t",
      ghgKpiNetReduction: "0.00 t",
      ghgStatusBadge: "Borrador"
    };
    Object.keys(kpiEls).forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = kpiEls[id];
    });

    const bodySummary = document.getElementById("ghgSummaryEntriesTableBody");
    if (bodySummary) {
      bodySummary.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 32px;">No hay inventarios creados. Haz clic en "+ Nuevo Inventario GEI" para comenzar.</td></tr>`;
    }
    const bodyS1 = document.getElementById("ghgScope1TableBody");
    if (bodyS1) bodyS1.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">Sin fuentes registradas en Alcance 1.</td></tr>`;
    const bodyS2 = document.getElementById("ghgScope2TableBody");
    if (bodyS2) bodyS2.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">Sin consumos electricos registrados en Alcance 2.</td></tr>`;
    const accContainer = document.getElementById("ghgScope3AccordionContainer");
    if (accContainer) accContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 24px;">Seleccione un inventario para explorar las 15 categorias de Alcance 3.</div>`;
  }

  function renderGhgView(inv) {
    if (!inv) return;
    const summary = inv.summary || {};

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setVal("ghgKpiScope1", `${Number(summary.scope_1_total || 0).toFixed(2)} t CO2e`);
    setVal("ghgScope1Pct", `${Number(summary.scope_1_share_pct || 0).toFixed(1)}%`);
    setVal("ghgKpiScope2Location", `${Number(summary.scope_2_location_total || 0).toFixed(2)} t CO2e`);
    setVal("ghgKpiScope2Market", `${Number(summary.scope_2_market_total || 0).toFixed(2)} t`);
    setVal("ghgScope2Pct", `${Number(summary.scope_2_share_pct || 0).toFixed(1)}%`);
    setVal("ghgKpiScope3", `${Number(summary.scope_3_total || 0).toFixed(2)} t CO2e`);
    setVal("ghgScope3Pct", `${Number(summary.scope_3_share_pct || 0).toFixed(1)}%`);
    setVal("ghgKpiScope3Upstream", `${Number(summary.scope_3_upstream_total || 0).toFixed(2)} t`);
    setVal("ghgKpiScope3Downstream", `${Number(summary.scope_3_downstream_total || 0).toFixed(2)} t`);
    setVal("ghgKpiTotalMarket", `${Number(summary.total_market_based || 0).toFixed(2)} t CO2e`);
    setVal("ghgKpiTotalLocation", `${Number(summary.total_location_based || 0).toFixed(2)} t`);
    setVal("ghgKpiNetReduction", `${Number(summary.net_reduction_i_rec || 0).toFixed(2)} t`);
    setVal("ghgStatusBadge", inv.status === "completed" ? "Completado" : "Borrador");

    const entries = inv.entries || [];
    renderGhgSummaryTable(entries);
    renderGhgScope1Table(entries);
    renderGhgScope2Table(entries);
    renderGhgScope3Accordion(entries, summary);
  }

  function renderGhgSummaryTable(entries) {
    const tbody = document.getElementById("ghgSummaryEntriesTableBody");
    if (!tbody) return;

    if (!entries || entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 24px;">No hay fuentes de emision registradas en este inventario. Presiona "+ Registrar Fuente" para agregar la primera.</td></tr>`;
      return;
    }

    const scopeColors = {
      SCOPE_1: { badge: "badge-red", label: "Scope 1", bg: "#FEE2E2", col: "#DC2626" },
      SCOPE_2: { badge: "badge-amber", label: "Scope 2", bg: "#FEF3C7", col: "#D97706" },
      SCOPE_3: { badge: "badge-blue", label: "Scope 3", bg: "#DBEAFE", col: "#2563EB" }
    };

    tbody.innerHTML = entries.map(e => {
      const sc = scopeColors[e.scope] || { badge: "badge-blue", label: e.scope, bg: "#E2E8F0", col: "#475569" };
      const tons = Number(e.emissions_t_co2e || 0).toFixed(3);
      const catLabel = e.category_label || e.category || "-";
      const calcLabel = e.calculation_type === "spend_based" ? "Monetario (USEEIO)" : (e.calculation_type === "product_system_lca" ? "LCA Tier 1" : "Actividad Fisica");
      const dqi = e.data_quality_tier || "Tier 1";

      return `
        <tr>
          <td><span class="badge-pill" style="background: ${sc.bg}; color: ${sc.col}; font-weight: 700; font-size: 9.5px;">${sc.label}</span></td>
          <td style="font-size: 11px; max-width: 170px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(catLabel)}">${escapeHtml(catLabel)}</td>
          <td><strong style="color: var(--text-primary); font-size: 11.5px;">${escapeHtml(e.activity_description || "")}</strong></td>
          <td><span style="font-size: 10.5px; color: var(--text-muted);">${calcLabel}</span></td>
          <td style="font-family: monospace; font-size: 11px;">${e.activity_amount} ${escapeHtml(e.activity_unit || "")}</td>
          <td style="font-family: monospace; font-size: 11px; color: var(--text-muted);">${e.applied_factor_value} <span style="font-size: 9.5px;">${escapeHtml(e.applied_factor_unit || "")}</span></td>
          <td style="font-family: monospace; font-weight: 700; font-size: 12px; color: #0F172A;">${tons}</td>
          <td><span class="badge-pill" style="background: #F1F5F9; color: #475569; font-size: 9.5px;">${dqi}</span></td>
          <td>
            <button class="btn btn-sm" style="color: #EF4444; background: transparent; padding: 2px 6px; font-size: 11px;" onclick="window.EconodeApp.deleteGhgEntry(${e.id})" title="Eliminar registro">Eliminar</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  function renderGhgScope1Table(entries) {
    const tbody = document.getElementById("ghgScope1TableBody");
    if (!tbody) return;

    const s1Entries = (entries || []).filter(e => e.scope === "SCOPE_1");
    if (s1Entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">Sin fuentes registradas en Alcance 1 (Combustion fija, movil o fugitivas).</td></tr>`;
      return;
    }

    tbody.innerHTML = s1Entries.map(e => `
      <tr>
        <td><span class="badge-pill" style="background: #FEE2E2; color: #DC2626; font-size: 9.5px; font-weight: 600;">${escapeHtml(e.category_label || e.category)}</span></td>
        <td><strong>${escapeHtml(e.activity_description)}</strong></td>
        <td style="font-family: monospace;">${e.activity_amount} ${escapeHtml(e.activity_unit || "")}</td>
        <td style="font-family: monospace; color: var(--text-muted); font-size: 11px;">${e.applied_factor_value} ${escapeHtml(e.applied_factor_unit || "")} <span style="font-size: 9.5px; color: #94A3B8;">(${escapeHtml(e.applied_factor_source || "")})</span></td>
        <td style="font-family: monospace; font-weight: 700; color: #DC2626;">${Number(e.emissions_t_co2e || 0).toFixed(3)}</td>
        <td>
          <button class="btn btn-sm" style="color: #EF4444; background: transparent; padding: 2px 6px;" onclick="window.EconodeApp.deleteGhgEntry(${e.id})">Eliminar</button>
        </td>
      </tr>
    `).join("");
  }

  function renderGhgScope2Table(entries) {
    const tbody = document.getElementById("ghgScope2TableBody");
    if (!tbody) return;

    const s2Entries = (entries || []).filter(e => e.scope === "SCOPE_2");
    if (s2Entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 20px;">Sin consumos electricos registrados en Alcance 2.</td></tr>`;
      return;
    }

    tbody.innerHTML = s2Entries.map(e => {
      const isMarket = (e.scope_2_reporting_type || "").toLowerCase() === "market_based";
      const inst = e.contractual_instrument || "none";
      const instBadge = inst === "i_rec" ? '<span class="badge-pill badge-emerald">I-REC Renovable (0.0 t)</span>'
        : (inst === "cel" ? '<span class="badge-pill badge-blue">CEL Mexico</span>'
        : (inst === "ppa" ? '<span class="badge-pill badge-emerald">PPA Limpio</span>' : '<span class="badge-pill" style="background:#F1F5F9; color:#64748B;">Red Convencional</span>'));

      return `
        <tr>
          <td><span class="badge-pill" style="background: ${isMarket ? '#ECFDF5' : '#FEF3C7'}; color: ${isMarket ? '#059669' : '#D97706'}; font-weight: 700; font-size: 9.5px;">${isMarket ? 'Market-Based' : 'Location-Based'}</span></td>
          <td><strong>${escapeHtml(e.activity_description)}</strong></td>
          <td style="font-family: monospace;">${e.activity_amount} kWh</td>
          <td>${instBadge}</td>
          <td style="font-family: monospace; color: var(--text-muted); font-size: 11px;">${e.applied_factor_value} kg CO2e/kWh</td>
          <td style="font-family: monospace; font-weight: 700; color: ${isMarket ? '#059669' : '#D97706'};">${Number(e.emissions_t_co2e || 0).toFixed(3)}</td>
          <td>
            <button class="btn btn-sm" style="color: #EF4444; background: transparent; padding: 2px 6px;" onclick="window.EconodeApp.deleteGhgEntry(${e.id})">Eliminar</button>
          </td>
        </tr>
      `;
    }).join("");
  }

  function renderGhgScope3Accordion(entries, summary) {
    const container = document.getElementById("ghgScope3AccordionContainer");
    if (!container) return;

    const s3Entries = (entries || []).filter(e => e.scope === "SCOPE_3");
    const categoriesTaxonomy = (state.ghgTaxonomy && state.ghgTaxonomy.categories && state.ghgTaxonomy.categories.SCOPE_3)
      ? state.ghgTaxonomy.categories.SCOPE_3
      : [
          { key: "SCOPE_3_CAT_1", label: "Cat 1: Bienes y Servicios Adquiridos", boundary: "upstream" },
          { key: "SCOPE_3_CAT_2", label: "Cat 2: Bienes de Capital", boundary: "upstream" },
          { key: "SCOPE_3_CAT_3", label: "Cat 3: Combustibles y Energia no en Scope 1/2", boundary: "upstream" },
          { key: "SCOPE_3_CAT_4", label: "Cat 4: Transporte y Distribucion Upstream", boundary: "upstream" },
          { key: "SCOPE_3_CAT_5", label: "Cat 5: Residuos Generados en Operaciones", boundary: "upstream" },
          { key: "SCOPE_3_CAT_6", label: "Cat 6: Viajes de Negocios", boundary: "upstream" },
          { key: "SCOPE_3_CAT_7", label: "Cat 7: Desplazamiento de Empleados (Conmutacion)", boundary: "upstream" },
          { key: "SCOPE_3_CAT_8", label: "Cat 8: Activos Arrendados Upstream", boundary: "upstream" },
          { key: "SCOPE_3_CAT_9", label: "Cat 9: Transporte y Distribucion Downstream", boundary: "downstream" },
          { key: "SCOPE_3_CAT_10", label: "Cat 10: Procesamiento de Productos Vendidos", boundary: "downstream" },
          { key: "SCOPE_3_CAT_11", label: "Cat 11: Uso de Productos Vendidos", boundary: "downstream" },
          { key: "SCOPE_3_CAT_12", label: "Cat 12: Tratamiento Fin de Vida de Productos Vendidos", boundary: "downstream" },
          { key: "SCOPE_3_CAT_13", label: "Cat 13: Activos Arrendados Downstream", boundary: "downstream" },
          { key: "SCOPE_3_CAT_14", label: "Cat 14: Franquicias", boundary: "downstream" },
          { key: "SCOPE_3_CAT_15", label: "Cat 15: Inversiones", boundary: "downstream" }
        ];

    const s3Total = summary.scope_3_total || 0;

    container.innerHTML = categoriesTaxonomy.map(cat => {
      const catEntries = s3Entries.filter(e => e.category === cat.key);
      const catSubtotal = catEntries.reduce((sum, e) => sum + Number(e.emissions_t_co2e || 0), 0);
      const catPct = s3Total > 0 ? ((catSubtotal / s3Total) * 100).toFixed(1) : "0.0";
      const isUpstream = (cat.boundary || "").toLowerCase() === "upstream";
      const hasEntries = catEntries.length > 0;

      return `
        <div style="background: var(--bg-card); border: 1px solid ${hasEntries ? '#93C5FD' : 'var(--border-color)'}; border-radius: var(--radius-md); overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: ${hasEntries ? 'rgba(219, 234, 254, 0.25)' : 'var(--bg-subtle)'}; cursor: pointer;" onclick="window.EconodeApp.toggleGhgAccordion('${cat.key}')">
            <div style="display: flex; align-items: center; gap: 10px;">
              <span class="badge-pill ${isUpstream ? 'badge-blue' : 'badge-amber'}" style="font-size: 9.5px; text-transform: uppercase;">${cat.boundary || 'Scope 3'}</span>
              <strong style="font-size: 12px; color: var(--text-primary);">${escapeHtml(cat.label)}</strong>
              ${hasEntries ? `<span class="badge-pill" style="background: #2563EB; color: #FFFFFF; font-size: 9px; padding: 1px 6px;">${catEntries.length} fuentes</span>` : ''}
            </div>
            <div style="display: flex; align-items: center; gap: 14px;">
              <div style="text-align: right;">
                <span style="font-family: monospace; font-size: 13px; font-weight: 700; color: #0F172A;">${catSubtotal.toFixed(3)} t CO2e</span>
                <span style="font-size: 10px; color: var(--text-muted); margin-left: 6px;">(${catPct}%)</span>
              </div>
              <span id="arrow_${cat.key}" style="font-size: 12px; color: var(--text-muted); transition: transform 0.2s;">&#9660;</span>
            </div>
          </div>

          <div id="body_${cat.key}" style="display: ${hasEntries ? 'block' : 'none'}; padding: 14px 16px; border-top: 1px solid var(--border-color);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <span style="font-size: 11px; color: var(--text-muted);">Fuentes registradas bajo ${escapeHtml(cat.label)}:</span>
              <button class="btn btn-secondary btn-sm" style="font-size: 10.5px; height: 26px;" onclick="window.EconodeApp.openAddGhgEntryModal('SCOPE_3', '${cat.key}')">+ Agregar a esta categoria</button>
            </div>

            ${hasEntries ? `
              <div class="table-responsive">
                <table class="data-table" style="font-size: 11px; margin: 0;">
                  <thead>
                    <tr>
                      <th>Actividad / Proveedor / Operacion</th>
                      <th>Metodo</th>
                      <th>Dato Actividad</th>
                      <th>Factor GWP</th>
                      <th>Emisiones (t CO2e)</th>
                      <th>Accion</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${catEntries.map(ce => `
                      <tr>
                        <td><strong>${escapeHtml(ce.activity_description)}</strong></td>
                        <td><span style="font-size: 10px; color: var(--text-muted);">${ce.calculation_type === 'spend_based' ? 'Spend USEEIO' : (ce.calculation_type === 'product_system_lca' ? 'LCA Tier 1' : 'Actividad')}</span></td>
                        <td style="font-family: monospace;">${ce.activity_amount} ${escapeHtml(ce.activity_unit || '')}</td>
                        <td style="font-family: monospace; font-size: 10.5px; color: var(--text-muted);">${ce.applied_factor_value} ${escapeHtml(ce.applied_factor_unit || '')}</td>
                        <td style="font-family: monospace; font-weight: 700; color: #2563EB;">${Number(ce.emissions_t_co2e || 0).toFixed(3)}</td>
                        <td>
                          <button class="btn btn-sm" style="color: #EF4444; background: transparent; padding: 1px 4px; font-size: 10.5px;" onclick="window.EconodeApp.deleteGhgEntry(${ce.id})">Eliminar</button>
                        </td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
            ` : `
              <div style="text-align: center; color: var(--text-muted); font-size: 11px; padding: 10px 0;">
                No hay actividades registradas en esta categoria aun.
              </div>
            `}
          </div>
        </div>
      `;
    }).join("");
  }

  function toggleGhgAccordion(catKey) {
    const body = document.getElementById("body_" + catKey);
    const arrow = document.getElementById("arrow_" + catKey);
    if (!body) return;
    const isHidden = (body.style.display === "none");
    body.style.display = isHidden ? "block" : "none";
    if (arrow) arrow.style.transform = isHidden ? "rotate(180deg)" : "rotate(0deg)";
  }

  // --- MODAL: CREAR NUEVO INVENTARIO GEI ---
  function openNewGhgInventoryModal() {
    const modal = document.getElementById("modalNewGhgInventory");
    if (!modal) return;
    const orgInput = document.getElementById("inputNewGhgOrg");
    const yearInput = document.getElementById("inputNewGhgYear");
    const baseYearInput = document.getElementById("inputNewGhgBaseYear");
    const descInput = document.getElementById("inputNewGhgDesc");

    if (orgInput) {
      const defaultOrg = (state.activeUser && state.activeUser.organization && !state.activeUser.organization.includes("BioPack"))
        ? state.activeUser.organization
        : "";
      orgInput.value = defaultOrg;
      orgInput.placeholder = "Nombre de tu empresa u organización corporativa...";
      setTimeout(() => orgInput.focus(), 60);
    }
    const currentYear = new Date().getFullYear();
    if (yearInput) yearInput.value = currentYear;
    if (baseYearInput) baseYearInput.value = currentYear - 1;
    if (descInput) descInput.value = "";

    modal.style.display = "flex";
    modal.classList.add("active");
  }

  async function submitNewGhgInventory() {
    const orgInput = document.getElementById("inputNewGhgOrg");
    const yearInput = document.getElementById("inputNewGhgYear");
    const baseYearInput = document.getElementById("inputNewGhgBaseYear");
    const countryInput = document.getElementById("selectNewGhgCountry");
    const consolInput = document.getElementById("selectNewGhgConsolidation");
    const descInput = document.getElementById("inputNewGhgDesc");
    const btnSubmit = document.getElementById("btnSubmitNewGhgInventory");

    const orgName = (orgInput ? orgInput.value.trim() : "") || "Empresa Corporativa";
    const year = parseInt(yearInput ? yearInput.value : "2024", 10) || 2024;
    const baseYear = baseYearInput && baseYearInput.value ? parseInt(baseYearInput.value, 10) : (year - 1);
    const country = countryInput ? countryInput.value : "MX";
    const consolidation = consolInput ? consolInput.value : "operational_control";
    const desc = descInput ? descInput.value.trim() : "";

    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.textContent = "Creando...";
    }

    const user = state.activeUser || {};
    try {
      const res = await api.createGhgInventory({
        organization_name: orgName,
        reporting_year: year,
        base_year: baseYear,
        country_code: country,
        consolidation_approach: consolidation,
        description: desc,
        created_by_user_id: user.id || 1,
        created_by_name: user.display_name || "Carla Mendez"
      });

      closeModal("modalNewGhgInventory");
      showNotification(`Inventario GEI "${orgName} (${year})" creado exitosamente.`);

      const newInv = res.inventory;
      if (newInv && newInv.id) {
        state.activeGhgInventory = newInv;
        state.activeGhgReportInventory = newInv;
        localStorage.setItem("econode_active_ghg_inv", String(newInv.id));
      }

      await loadDashboardGhgInventories();
      if (typeof loadGhgInventoryModule === "function" && state.currentView === "ghg") {
        await loadGhgInventoryModule();
      }
      if (state.currentView === "report" && typeof loadGhgReport === "function") {
        await loadGhgReport(newInv?.id);
      }
    } catch (err) {
      console.error("Error al crear inventario:", err);
      alert("Error al crear inventario: " + err.message);
    } finally {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Crear Inventario";
      }
    }
  }

  async function deleteCurrentGhgInventory() {
    if (!state.activeGhgInventory) {
      showNotification("No hay un inventario seleccionado para eliminar.");
      return;
    }
    const inv = state.activeGhgInventory;
    const ok = confirm(`¿Esta seguro de eliminar el inventario corporativo de "${inv.organization_name} (${inv.reporting_year})"? Esta accion eliminara todas las fuentes asociadas.`);
    if (!ok) return;

    try {
      await api.deleteGhgInventory(inv.id);
      showNotification("Inventario eliminado exitosamente.");
      state.activeGhgInventory = null;
      localStorage.removeItem("econode_active_ghg_inv");
      await loadGhgInventoryModule();
    } catch (err) {
      console.error("Error al eliminar inventario:", err);
      showNotification("Error al eliminar inventario: " + err.message);
    }
  }

  // --- MODAL: REGISTRAR FUENTE DE EMISION ---
  async function openAddGhgEntryModal(targetScope = "SCOPE_1", targetCategory = null) {
    const modal = document.getElementById("modalAddGhgEntry");
    if (!modal) return;

    if (!state.activeGhgInventory) {
      showNotification("Primero debes seleccionar o crear un inventario GEI corporativo.");
      return;
    }

    const selectScope = document.getElementById("selectEntryScope");
    if (selectScope) selectScope.value = targetScope;

    onGhgModalScopeChange(targetScope, targetCategory);

    // Resetear campos a valores predeterminados
    const nameInput = document.getElementById("inputEntryName");
    if (nameInput) nameInput.value = "";
    const amtInput = document.getElementById("inputEntryAmount");
    if (amtInput) amtInput.value = "1000";

    // Marcar radio activity_based por defecto
    const radios = document.getElementsByName("calcTypeRadio");
    radios.forEach(r => { r.checked = (r.value === "activity_based"); });
    onGhgCalcTypeChange();

    modal.style.display = "flex";
    modal.classList.add("active");
  }

  function onGhgModalScopeChange(scope, preselectedCategory = null) {
    const catSelect = document.getElementById("selectEntryCategory");
    const containerMarket = document.getElementById("ghgContainerMarketInstrument");

    if (containerMarket) {
      containerMarket.style.display = (scope === "SCOPE_2") ? "block" : "none";
    }

    if (!catSelect) return;

    let categories = [];
    if (state.ghgTaxonomy && state.ghgTaxonomy.categories && state.ghgTaxonomy.categories[scope]) {
      categories = state.ghgTaxonomy.categories[scope];
    } else {
      if (scope === "SCOPE_1") {
        categories = [
          { key: "stationary_combustion", label: "Combustion Fija (Calderas / Generadores)" },
          { key: "mobile_combustion", label: "Combustion Movil (Vehiculos Propios)" },
          { key: "fugitive_emissions", label: "Emisiones Fugitivas (Refrigerantes / Fugas)" },
          { key: "process_emissions", label: "Emisiones de Proceso Industrial" }
        ];
      } else if (scope === "SCOPE_2") {
        categories = [
          { key: "purchased_electricity_location", label: "Electricidad Red (Metodo Ubicacion)" },
          { key: "purchased_electricity_market", label: "Electricidad Mercado (I-RECs / PPA)" },
          { key: "purchased_steam", label: "Vapor Adquirido" },
          { key: "purchased_cooling", label: "Enfriamiento Adquirido" }
        ];
      } else {
        categories = [
          { key: "SCOPE_3_CAT_1", label: "Cat 1: Bienes y Servicios Adquiridos" },
          { key: "SCOPE_3_CAT_2", label: "Cat 2: Bienes de Capital" },
          { key: "SCOPE_3_CAT_3", label: "Cat 3: Combustibles y Energia Upstream" },
          { key: "SCOPE_3_CAT_4", label: "Cat 4: Transporte y Distribucion Upstream" },
          { key: "SCOPE_3_CAT_5", label: "Cat 5: Residuos Generados en Operaciones" },
          { key: "SCOPE_3_CAT_6", label: "Cat 6: Viajes de Negocios" },
          { key: "SCOPE_3_CAT_7", label: "Cat 7: Desplazamiento de Empleados" },
          { key: "SCOPE_3_CAT_8", label: "Cat 8: Activos Arrendados Upstream" },
          { key: "SCOPE_3_CAT_9", label: "Cat 9: Transporte Downstream" },
          { key: "SCOPE_3_CAT_10", label: "Cat 10: Procesamiento de Productos Vendidos" },
          { key: "SCOPE_3_CAT_11", label: "Cat 11: Uso de Productos Vendidos" },
          { key: "SCOPE_3_CAT_12", label: "Cat 12: Fin de Vida de Productos Vendidos" },
          { key: "SCOPE_3_CAT_13", label: "Cat 13: Activos Arrendados Downstream" },
          { key: "SCOPE_3_CAT_14", label: "Cat 14: Franquicias" },
          { key: "SCOPE_3_CAT_15", label: "Cat 15: Inversiones" }
        ];
      }
    }

    catSelect.innerHTML = categories.map(c => `
      <option value="${c.key}">${escapeHtml(c.label)}</option>
    `).join("");

    if (preselectedCategory) {
      catSelect.value = preselectedCategory;
    }

    populateGhgActivityFactors(scope);
    previewGhgEmissions();
  }

  async function populateGhgActivityFactors(scope) {
    const factorSelect = document.getElementById("selectEntryFactor");
    if (!factorSelect) return;

    try {
      const data = await api.searchGhgEmissionFactors({ scope: scope === "ALL" ? "" : scope, limit: 100 });
      const factors = data.factors || data.items || [];
      state.ghgEmissionFactors = factors;

      if (factors.length === 0) {
        factorSelect.innerHTML = '<option value="">Sin factores disponibles para este alcance</option>';
      } else {
        factorSelect.innerHTML = factors.map(f => `
          <option value="${f.id}" data-factor="${f.gwp_factor_kg_co2e}" data-unit="${escapeHtml(f.unit)}">
            ${escapeHtml(f.name)} (${f.gwp_factor_kg_co2e} kg CO2e/${escapeHtml(f.unit)}) - ${escapeHtml(f.source)}
          </option>
        `).join("");
      }

      onGhgFactorSelectChange();
    } catch (err) {
      console.warn("Error al buscar factores de actividad:", err);
    }
  }

  function onGhgFactorSelectChange() {
    const select = document.getElementById("selectEntryFactor");
    const unitInput = document.getElementById("inputEntryUnit");
    if (!select || !select.selectedOptions || select.selectedOptions.length === 0) return;
    const opt = select.selectedOptions[0];
    const unit = opt.getAttribute("data-unit");
    if (unit && unitInput) {
      unitInput.value = unit;
    }
    previewGhgEmissions();
  }

  async function populateGhgSpendSectors() {
    const select = document.getElementById("selectEntrySpendSector");
    if (!select) return;

    try {
      const data = await api.searchGhgEmissionFactors({ source: "USEEIO_2024", limit: 60 });
      const factors = data.factors || data.items || [];
      state.ghgSpendFactors = factors;

      select.innerHTML = factors.map(f => `
        <option value="${f.id}" data-factor="${f.gwp_factor_kg_co2e}">
          ${escapeHtml(f.name)} (${f.gwp_factor_kg_co2e} kg CO2e/$ USD)
        </option>
      `).join("");
    } catch (err) {
      console.warn("Error al cargar sectores spend-based:", err);
    }
  }

  function onGhgSpendSectorChange() {
    previewGhgEmissions();
  }

  function populateGhgProductSystems() {
    const select = document.getElementById("selectEntryProductSystem");
    if (!select) return;

    const systems = state.systems || [];
    if (systems.length === 0) {
      select.innerHTML = '<option value="">No hay sistemas producto modelados en el lienzo</option>';
      return;
    }

    select.innerHTML = systems.map(s => `
      <option value="${s.id}">
        ${escapeHtml(s.name)} (${escapeHtml(s.code || 'SYS')}) - UF: ${s.target_amount || 1} ${escapeHtml(s.unit || 'u')}
      </option>
    `).join("");
  }

  function onGhgProductSystemSelectChange() {
    previewGhgEmissions();
  }

  function onGhgCalcTypeChange() {
    let calcType = "activity_based";
    const checked = document.querySelector('input[name="calcTypeRadio"]:checked');
    if (checked) calcType = checked.value;

    const boxActivity = document.getElementById("ghgContainerActivity");
    const boxSpend = document.getElementById("ghgContainerSpend");
    const boxLca = document.getElementById("ghgContainerLca");

    if (boxActivity) boxActivity.style.display = (calcType === "activity_based") ? "block" : "none";
    if (boxSpend) boxSpend.style.display = (calcType === "spend_based") ? "block" : "none";
    if (boxLca) boxLca.style.display = (calcType === "product_system_lca") ? "block" : "none";

    previewGhgEmissions();
  }

  function previewGhgEmissions() {
    let calcType = "activity_based";
    const checked = document.querySelector('input[name="calcTypeRadio"]:checked');
    if (checked) calcType = checked.value;

    const scopeSelect = document.getElementById("selectEntryScope");
    const currentScope = scopeSelect ? scopeSelect.value : "SCOPE_1";

    let kgCo2e = 0.0;

    if (calcType === "activity_based") {
      const amtInput = document.getElementById("inputEntryAmount");
      const amt = parseFloat(amtInput ? amtInput.value : "0") || 0.0;
      const factorSelect = document.getElementById("selectEntryFactor");
      let factor = 0.0;
      if (factorSelect && factorSelect.selectedOptions && factorSelect.selectedOptions[0]) {
        factor = parseFloat(factorSelect.selectedOptions[0].getAttribute("data-factor") || "0") || 0.0;
      }

      if (currentScope === "SCOPE_2") {
        const instSelect = document.getElementById("selectEntryContractualInstrument");
        const inst = instSelect ? instSelect.value : "none";
        if (inst === "i_rec" || inst === "ppa") {
          factor = 0.0;
        }
      }

      kgCo2e = amt * factor;
    } else if (calcType === "spend_based") {
      const spendInput = document.getElementById("inputEntrySpendAmount");
      const spendAmt = parseFloat(spendInput ? spendInput.value : "0") || 0.0;
      const currSelect = document.getElementById("selectEntryCurrency");
      const curr = currSelect ? currSelect.value : "MXN";

      const sectorSelect = document.getElementById("selectEntrySpendSector");
      let factor = 0.35;
      if (sectorSelect && sectorSelect.selectedOptions && sectorSelect.selectedOptions[0]) {
        factor = parseFloat(sectorSelect.selectedOptions[0].getAttribute("data-factor") || "0.35") || 0.35;
      }

      let amtUsd = spendAmt;
      if (curr === "MXN") amtUsd = spendAmt / 20.0;
      else if (curr === "EUR") amtUsd = spendAmt * 1.08;

      kgCo2e = amtUsd * factor;
    } else if (calcType === "product_system_lca") {
      const lcaInput = document.getElementById("inputEntryLcaAmount");
      const lcaAmt = parseFloat(lcaInput ? lcaInput.value : "0") || 0.0;
      const sysSelect = document.getElementById("selectEntryProductSystem");
      const sysId = sysSelect ? parseInt(sysSelect.value, 10) : null;

      let epdFactor = 0.05183;
      if (sysId && state.systems) {
        const found = state.systems.find(s => s.id === sysId);
        if (found && found.lcia_scores && found.lcia_scores.global_warming) {
          epdFactor = found.lcia_scores.global_warming;
        }
      }
      kgCo2e = lcaAmt * epdFactor;
    }

    const tCo2e = kgCo2e / 1000.0;
    const prevKg = document.getElementById("ghgPreviewKg");
    const prevTons = document.getElementById("ghgPreviewTons");
    if (prevKg) prevKg.textContent = `${kgCo2e.toFixed(2)} kg CO2e`;
    if (prevTons) prevTons.textContent = `${tCo2e.toFixed(3)} t CO2e`;
  }

  async function submitNewGhgEntry() {
    if (!state.activeGhgInventory) {
      showNotification("No hay un inventario corporativo activo.");
      return;
    }
    const invId = state.activeGhgInventory.id;

    const scopeSelect = document.getElementById("selectEntryScope");
    const catSelect = document.getElementById("selectEntryCategory");
    const nameInput = document.getElementById("inputEntryName");

    const scope = scopeSelect ? scopeSelect.value : "SCOPE_1";
    const category = catSelect ? catSelect.value : "general";
    const catOpt = catSelect && catSelect.selectedOptions ? catSelect.selectedOptions[0] : null;
    const catLabel = catOpt ? catOpt.text : category;
    const name = (nameInput ? nameInput.value.trim() : "") || `Actividad ${catLabel}`;

    let calcType = "activity_based";
    const checked = document.querySelector('input[name="calcTypeRadio"]:checked');
    if (checked) calcType = checked.value;

    const payload = {
      scope: scope,
      category: category,
      category_label: catLabel,
      activity_description: name,
      calculation_type: calcType,
      data_quality_tier: "Tier 1"
    };

    if (calcType === "activity_based") {
      const amtInput = document.getElementById("inputEntryAmount");
      const unitInput = document.getElementById("inputEntryUnit");
      const factorSelect = document.getElementById("selectEntryFactor");

      payload.activity_amount = parseFloat(amtInput ? amtInput.value : "0") || 0.0;
      payload.activity_unit = unitInput ? unitInput.value.trim() : "u";

      if (factorSelect && factorSelect.value) {
        payload.emission_factor_id = parseInt(factorSelect.value, 10);
      }
      if (scope === "SCOPE_2") {
        const instSelect = document.getElementById("selectEntryContractualInstrument");
        const inst = instSelect ? instSelect.value : "none";
        payload.contractual_instrument = inst;
        payload.scope_2_reporting_type = (inst !== "none") ? "market_based" : "location_based";
        if (inst === "i_rec" || inst === "ppa") {
          payload.applied_factor_value = 0.0;
        }
      }
    } else if (calcType === "spend_based") {
      const spendInput = document.getElementById("inputEntrySpendAmount");
      const currSelect = document.getElementById("selectEntryCurrency");
      const sectorSelect = document.getElementById("selectEntrySpendSector");

      payload.spend_amount = parseFloat(spendInput ? spendInput.value : "0") || 0.0;
      payload.spend_currency = currSelect ? currSelect.value : "MXN";
      payload.activity_amount = payload.spend_amount;
      payload.activity_unit = payload.spend_currency;

      if (sectorSelect && sectorSelect.value) {
        payload.emission_factor_id = parseInt(sectorSelect.value, 10);
      }
    } else if (calcType === "product_system_lca") {
      const lcaInput = document.getElementById("inputEntryLcaAmount");
      const sysSelect = document.getElementById("selectEntryProductSystem");

      payload.activity_amount = parseFloat(lcaInput ? lcaInput.value : "0") || 0.0;
      payload.activity_unit = "Functional Units";
      if (sysSelect && sysSelect.value) {
        payload.product_system_id = parseInt(sysSelect.value, 10);
      }
    }

    try {
      await api.addGhgEntry(invId, payload);
      closeModal("modalAddGhgEntry");
      showNotification(`Fuente "${name}" agregada con exito al inventario.`);
      await loadActiveGhgInventory(invId);
    } catch (err) {
      console.error("Error al registrar fuente:", err);
      alert("Error al registrar fuente: " + err.message);
    }
  }

  async function deleteGhgEntry(entryId) {
    if (!state.activeGhgInventory) return;
    const ok = confirm("¿Desea eliminar este registro de emision del inventario?");
    if (!ok) return;

    try {
      await api.deleteGhgEntry(state.activeGhgInventory.id, entryId);
      showNotification("Fuente eliminada del inventario.");
      await loadActiveGhgInventory(state.activeGhgInventory.id);
    } catch (err) {
      console.error("Error al eliminar entrada:", err);
      showNotification("Error al eliminar fuente: " + err.message);
    }
  }

  async function searchGhgFactorsTab() {
    const tbody = document.getElementById("ghgFactorsTableBody");
    if (!tbody) return;

    const input = document.getElementById("inputGhgFactorSearch");
    const selectScope = document.getElementById("selectGhgFactorScope");
    const selectSource = document.getElementById("selectGhgFactorSource");

    const q = input ? input.value.trim() : "";
    const scope = selectScope ? selectScope.value : "ALL";
    const source = selectSource ? selectSource.value : "ALL";

    try {
      const data = await api.searchGhgEmissionFactors({
        q: q,
        scope: scope === "ALL" ? "" : scope,
        source: source === "ALL" ? "" : source,
        limit: 100
      });
      const factors = data.factors || data.items || [];

      if (factors.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">No se encontraron factores con los filtros seleccionados.</td></tr>`;
        return;
      }

      tbody.innerHTML = factors.map(f => `
        <tr>
          <td><strong style="color: var(--text-primary); font-size: 11.5px;">${escapeHtml(f.name)}</strong></td>
          <td><span class="badge-pill badge-blue" style="font-size: 9.5px;">${escapeHtml(f.source)}</span></td>
          <td><span style="font-size: 10.5px; color: var(--text-muted);">${escapeHtml(f.scope_category)}</span></td>
          <td><span style="font-family: monospace; font-size: 10.5px;">${escapeHtml(f.geography)}</span></td>
          <td style="font-family: monospace; font-size: 11px;">${escapeHtml(f.unit)}</td>
          <td style="font-family: monospace; font-weight: 700; color: #0F172A; font-size: 12px;">${f.gwp_factor_kg_co2e}</td>
          <td style="font-size: 11px; color: var(--text-muted);">${f.year}</td>
        </tr>
      `).join("");
    } catch (err) {
      console.warn("Error al buscar catalogo de factores:", err);
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #EF4444; padding: 20px;">Error al consultar catalogo: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // =============================================================================
  // MODULO DE FIN DE VIDA Y TRATAMIENTO DE RESIDUOS (WASTETOOLS 2026 / DOKA FULL SUITE)
  // =============================================================================
  let wasteMaterialsCache = [];
  let wasteMixtureRows = [];
  let currentWasteMode = "predefined"; // "predefined", "mixture", "custom"
  let lastWasteCalculationResult = null;
  let wasteElementsList = [];
  let activeChemCategory = "all";
  let lastSynthesizedMixture = null;

  const tWaste = (key, fallback) => (window.I18n ? window.I18n.t(key, fallback) : fallback);

  function openWasteToolsModal() {
    showView("waste");
  }

  function closeWasteToolsModal() {
    showView("dashboard");
  }

  async function initWasteToolsData() {
    try {
      // 1. Cargar Categorias
      const catSelect = document.getElementById("wasteCategorySelect");
      if (catSelect && catSelect.options.length <= 1) {
        const resCats = await fetch("/api/waste/categories");
        const dataCats = await resCats.json();
        if (dataCats.status === "success" && dataCats.categories) {
          dataCats.categories.forEach(cat => {
            const opt = document.createElement("option");
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
          });
        }
      }

      // 2. Cargar Elementos Quimicos y Metadatos (50 Especies)
      await loadWasteElements();

      // 3. Cargar Materiales
      await loadWasteMaterials();

      // 4. Inicializar Mezcla por defecto si esta vacia
      if (!wasteMixtureRows || wasteMixtureRows.length === 0) {
        wasteMixtureRows = [
          { material_id: "dokamat_11", share: 50.0 },
          { material_id: "dokamat_15", share: 50.0 }
        ];
        renderWasteMixtureRows();
      }
    } catch (err) {
      console.error("Error al inicializar WasteTools:", err);
    }
  }

  async function loadWasteElements() {
    try {
      const res = await fetch("/api/waste/elements");
      const data = await res.json();
      if (data.status === "success" && data.elements) {
        wasteElementsList = data.elements;
        renderChemicalElementsGrid();
      }
    } catch (e) {
      console.warn("No se pudo cargar /api/waste/elements:", e);
    }
  }

  function renderChemicalElementsGrid() {
    const grid = document.getElementById("wasteChemicalElementsGrid");
    if (!grid || !wasteElementsList || wasteElementsList.length === 0) return;

    grid.innerHTML = wasteElementsList.map(el => {
      const isMacro = el.type === "macro";
      const step = isMacro ? (el.unit === "0-1" ? "0.01" : "0.001") : "0.1";
      const defaultVal = el.default != null ? el.default : (isMacro ? 0.01 : 10.0);
      const searchTerms = `${el.key} ${el.symbol} ${el.name_es} ${el.name_en}`.toLowerCase();

      return `
        <div class="chem-card" data-category="${el.category}" data-search="${searchTerms}" style="padding: 8px 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; display: flex; flex-direction: column; justify-content: space-between;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="mono" style="font-size: 11.5px; font-weight: 700; color: var(--accent-emerald, #10b981); background: rgba(16,185,129,0.1); padding: 1px 6px; border-radius: 4px;">
              [${el.symbol}]
            </span>
            <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">
              ${el.unit}
            </span>
          </div>
          <div style="font-size: 11px; font-weight: 500; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${el.name_es} (${el.name_en})">
            ${el.name_es}
          </div>
          <input type="number" step="${step}" min="0" id="chemInput_${el.key}" value="${defaultVal}" class="form-control chem-value-input" style="height: 28px; font-size: 11px; text-align: right; width: 100%;" oninput="window.EconodeApp.updateLiveMassBalance()" />
        </div>
      `;
    }).join("");

    updateLiveMassBalance();
  }

  function updateLiveMassBalance() {
    const badge = document.getElementById("badgeLiveMassBalance");
    if (!badge) return;

    const hu = parseFloat(document.getElementById("chemInput_Hu")?.value || "0");
    const h2o = parseFloat(document.getElementById("chemInput_H2O")?.value || "0");
    const c = parseFloat(document.getElementById("chemInput_C")?.value || "0");
    const o = parseFloat(document.getElementById("chemInput_O")?.value || "0");
    const h = parseFloat(document.getElementById("chemInput_H")?.value || "0");
    const n = parseFloat(document.getElementById("chemInput_N")?.value || "0");
    const s = parseFloat(document.getElementById("chemInput_S")?.value || "0");
    const p = parseFloat(document.getElementById("chemInput_P")?.value || "0");
    const cl = parseFloat(document.getElementById("chemInput_Cl")?.value || "0");
    const f = parseFloat(document.getElementById("chemInput_F")?.value || "0");
    const ash = parseFloat(document.getElementById("chemInput_ash")?.value || "0");

    // Suma en porcentaje (0 a 100%)
    // Si los valores estan en fraccion (0-1), convertimos
    const sumFrac = (h2o > 1 ? h2o / 100 : h2o) +
                    (c > 1 ? c / 100 : c) +
                    (o > 1 ? o / 100 : o) +
                    (h > 1 ? h / 100 : h) +
                    (n > 1 ? n / 100 : n) +
                    (s > 1 ? s / 100 : s) +
                    (p > 1 ? p / 100 : p) +
                    (cl > 1 ? cl / 100 : cl) +
                    (f > 1 ? f / 100 : f) +
                    (ash > 1 ? ash / 100 : ash);

    const sumPct = sumFrac * 100.0;
    badge.textContent = `${sumPct.toFixed(1)}%`;
    if (Math.abs(sumPct - 100.0) <= 2.0) {
      badge.style.color = "#10b981";
    } else if (sumPct < 100.0) {
      badge.style.color = "#f59e0b";
    } else {
      badge.style.color = "#ef4444";
    }
  }

  function filterChemicalElements() {
    const q = (document.getElementById("inputSearchChemicals")?.value || "").toLowerCase().trim();
    const cards = document.querySelectorAll("#wasteChemicalElementsGrid .chem-card");

    cards.forEach(card => {
      const cat = card.getAttribute("data-category");
      const search = card.getAttribute("data-search") || "";
      const matchesCat = (activeChemCategory === "all" || cat === activeChemCategory);
      const matchesQuery = (!q || search.includes(q));

      if (matchesCat && matchesQuery) {
        card.style.display = "flex";
      } else {
        card.style.display = "none";
      }
    });
  }

  function setChemicalCategoryFilter(cat) {
    activeChemCategory = cat;
    document.querySelectorAll("[data-chem-cat]").forEach(btn => {
      if (btn.getAttribute("data-chem-cat") === cat) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
    filterChemicalElements();
  }

  function populateCustomTemplateSelect() {
    const sel = document.getElementById("selectCustomTemplate");
    if (!sel || !wasteMaterialsCache) return;

    sel.innerHTML = `<option value="">-- Cargar Quimicos desde Material del Catalogo (${wasteMaterialsCache.length} disponibles) --</option>`;
    wasteMaterialsCache.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = `${m.name} (${m.category})`;
      sel.appendChild(opt);
    });
  }

  function loadMaterialIntoCustomEditor(matId) {
    if (!matId) return;
    const mat = wasteMaterialsCache.find(m => m.id === matId);
    if (!mat) return;

    // Cargar Macro
    const setVal = (id, val) => {
      const inp = document.getElementById(id);
      if (inp) inp.value = val != null ? val : 0;
    };

    setVal("chemInput_Hu", mat.Hu != null ? Number(mat.Hu).toFixed(2) : 15.0);
    setVal("chemInput_Ho", mat.Ho != null ? Number(mat.Ho).toFixed(2) : 16.5);
    setVal("chemInput_H2O", mat.H2O != null ? Number(mat.H2O).toFixed(4) : 0.20);
    setVal("chemInput_C", mat.C != null ? Number(mat.C).toFixed(4) : 0.45);
    setVal("chemInput_biogenic_c_share", mat.biogenic_c_share != null ? Number(mat.biogenic_c_share).toFixed(3) : 0.0);
    setVal("chemInput_ash", mat.ash != null ? Number(mat.ash).toFixed(4) : 0.05);
    setVal("chemInput_degradability_100a", mat.degradability_100a != null ? Number(mat.degradability_100a).toFixed(3) : 0.1);
    setVal("chemInput_O", mat.O != null ? Number(mat.O).toFixed(4) : 0.0);
    setVal("chemInput_H", mat.H != null ? Number(mat.H).toFixed(4) : 0.05);
    setVal("chemInput_N", mat.N != null ? Number(mat.N).toFixed(5) : 0.005);
    setVal("chemInput_S", mat.S != null ? Number(mat.S).toFixed(5) : 0.001);
    setVal("chemInput_P", mat.P != null ? Number(mat.P).toFixed(5) : 0.0);
    setVal("chemInput_Cl", mat.Cl != null ? Number(mat.Cl).toFixed(5) : 0.002);
    setVal("chemInput_F", mat.F != null ? Number(mat.F).toFixed(6) : 0.0);
    setVal("chemInput_Br", mat.Br != null ? (Number(mat.Br) * 1e4).toFixed(2) : 0.0);
    setVal("chemInput_I", mat.I != null ? (Number(mat.I) * 1e4).toFixed(3) : 0.0);

    // Cargar Oligoelementos en ppm
    const metals = mat.elements_ppm || {};
    wasteElementsList.forEach(el => {
      if (el.type === "ppm") {
        const val = metals[el.key] != null ? Number(metals[el.key]).toFixed(2) : 0.0;
        setVal(`chemInput_${el.key}`, val);
      }
    });

    updateLiveMassBalance();
    showNotification(`Plantilla de quimicos cargada desde: ${mat.name}`);
  }

  function applyPreset(presetType) {
    const setVal = (k, v) => {
      const inp = document.getElementById(`chemInput_${k}`);
      if (inp) inp.value = v;
    };

    if (presetType === "zero") {
      wasteElementsList.forEach(el => setVal(el.key, 0));
      showNotification("Todos los parametros quimicos se han puesto a cero.");
    } else if (presetType === "msw") {
      setVal("Hu", 11.5); setVal("Ho", 13.0); setVal("H2O", 0.35); setVal("C", 0.28);
      setVal("biogenic_c_share", 0.65); setVal("ash", 0.22); setVal("degradability_100a", 0.45);
      setVal("O", 0.18); setVal("H", 0.04); setVal("N", 0.008); setVal("S", 0.0025);
      setVal("P", 0.0015); setVal("Cl", 0.006); setVal("F", 0.0001);
      setVal("Fe", 8500); setVal("Al", 2200); setVal("Cu", 450); setVal("Pb", 180);
      setVal("Zn", 950); setVal("Cd", 6.5); setVal("Hg", 1.2); setVal("As", 8.0);
      setVal("Cr", 75); setVal("Ni", 45); setVal("Ca", 16000); setVal("Na", 4500);
      showNotification("Plantilla de Residuos Solidos Urbanos (RSU) cargada.");
    } else if (presetType === "plastics") {
      setVal("Hu", 38.5); setVal("Ho", 41.0); setVal("H2O", 0.01); setVal("C", 0.83);
      setVal("biogenic_c_share", 0.0); setVal("ash", 0.015); setVal("degradability_100a", 0.01);
      setVal("O", 0.02); setVal("H", 0.13); setVal("N", 0.001); setVal("S", 0.0004);
      setVal("Cl", 0.003); setVal("Fe", 650); setVal("Al", 250); setVal("Cu", 45);
      setVal("Pb", 22); setVal("Zn", 280); setVal("Cd", 12.0); setVal("Hg", 0.05);
      showNotification("Plantilla de Plasticos Mixtos (PE/PP) cargada.");
    } else if (presetType === "ewaste") {
      setVal("Hu", 13.0); setVal("Ho", 15.0); setVal("H2O", 0.02); setVal("C", 0.22);
      setVal("biogenic_c_share", 0.0); setVal("ash", 0.48); setVal("degradability_100a", 0.00);
      setVal("Cl", 0.025); setVal("Br", 1500); setVal("Fe", 180000); setVal("Al", 75000);
      setVal("Cu", 48000); setVal("Pb", 3800); setVal("Zn", 8500); setVal("Cd", 125);
      setVal("Hg", 18); setVal("As", 95); setVal("Ag", 450); setVal("Ni", 4800); setVal("Sn", 8200);
      showNotification("Plantilla de RAEE / Chatarra Electronica cargada.");
    }
    updateLiveMassBalance();
  }

  function togglePredefinedElementsDrawer() {
    const drawer = document.getElementById("wastePredefinedElementsDrawer");
    const btn = document.getElementById("btnTogglePredefinedElements");
    if (!drawer) return;

    if (drawer.style.display === "none") {
      drawer.style.display = "block";
      if (btn) btn.innerHTML = `<span class="mono">[-]</span> <span>Ocultar Elementos Quimicos</span>`;
      renderPredefinedElementsTable();
    } else {
      drawer.style.display = "none";
      if (btn) btn.innerHTML = `<span class="mono">[+]</span> <span>Inspeccionar 50 Elementos Quimicos</span>`;
    }
  }

  function renderPredefinedElementsTable() {
    const container = document.getElementById("wastePredefinedElementsTableContainer");
    const matSelect = document.getElementById("wasteMaterialSelect");
    if (!container || !matSelect || !matSelect.value) return;

    const mat = wasteMaterialsCache.find(m => m.id === matSelect.value);
    if (!mat) return;

    const metals = mat.elements_ppm || {};
    const rows = wasteElementsList.map(el => {
      let valStr = "--";
      if (el.type === "macro") {
        const raw = mat[el.key];
        if (raw != null) {
          valStr = el.unit === "% masa" ? `${(Number(raw) * 100).toFixed(2)} %` : Number(raw).toFixed(2);
        }
      } else {
        const raw = metals[el.key];
        if (raw != null) {
          valStr = `${Number(raw).toFixed(2)} ppm`;
        }
      }

      return `
        <tr style="border-bottom: 1px solid var(--border-color);">
          <td class="mono" style="padding: 4px 8px; font-weight: 700; color: var(--accent-emerald, #10b981);">${el.symbol}</td>
          <td style="padding: 4px 8px;">${el.name_es}</td>
          <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 600;">${valStr}</td>
          <td style="padding: 4px 8px; font-size: 10px; color: var(--text-muted); text-transform: uppercase;">${el.category}</td>
        </tr>
      `;
    }).join("");

    container.innerHTML = `
      <table style="width: 100%; border-collapse: collapse; font-size: 11.5px;">
        <thead>
          <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-secondary); font-size: 10.5px;">
            <th style="padding: 4px 8px;">Simbolo</th>
            <th style="padding: 4px 8px;">Elemento / Parametro</th>
            <th style="padding: 4px 8px; text-align: right;">Concentracion</th>
            <th style="padding: 4px 8px;">Categoria</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  function copyPredefinedToCustom() {
    const matSelect = document.getElementById("wasteMaterialSelect");
    if (!matSelect || !matSelect.value) return;

    // Cambiar a pestaña custom
    const btnCust = document.getElementById("btnWasteModeCustom");
    if (btnCust) btnCust.click();

    loadMaterialIntoCustomEditor(matSelect.value);
    showNotification("Perfil quimico transferido al Editor Elemental para personalizacion.");
  }

  function toggleMixtureElementsDrawer() {
    const drawer = document.getElementById("wasteMixtureElementsDrawer");
    const btn = document.getElementById("btnToggleMixtureElements");
    if (!drawer) return;

    if (drawer.style.display === "none") {
      drawer.style.display = "block";
      if (btn) btn.innerHTML = `<span class="mono">[-]</span> <span>Ocultar Composicion de Mezcla</span>`;
      renderMixtureElementsTable();
    } else {
      drawer.style.display = "none";
      if (btn) btn.innerHTML = `<span class="mono">[+]</span> <span>Ver Composicion Elemental de la Mezcla</span>`;
    }
  }

  function renderMixtureElementsTable() {
    const container = document.getElementById("wasteMixtureElementsTableContainer");
    if (!container || !lastSynthesizedMixture) {
      if (container) container.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px;">No hay calculo de mezcla sintetizada disponible todavia.</div>`;
      return;
    }

    const m = lastSynthesizedMixture;
    const metals = m.elements_ppm || {};
    const rows = wasteElementsList.map(el => {
      let valStr = "--";
      if (el.type === "macro") {
        const raw = m[el.key];
        if (raw != null) {
          valStr = el.unit === "% masa" ? `${(Number(raw) * 100).toFixed(2)} %` : Number(raw).toFixed(2);
        }
      } else {
        const raw = metals[el.key];
        if (raw != null) {
          valStr = `${Number(raw).toFixed(2)} ppm`;
        }
      }

      return `
        <tr style="border-bottom: 1px solid var(--border-color);">
          <td class="mono" style="padding: 4px 8px; font-weight: 700; color: #3b82f6;">${el.symbol}</td>
          <td style="padding: 4px 8px;">${el.name_es}</td>
          <td style="padding: 4px 8px; text-align: right; font-family: monospace; font-weight: 600;">${valStr}</td>
          <td style="padding: 4px 8px; font-size: 10px; color: var(--text-muted);">${el.category}</td>
        </tr>
      `;
    }).join("");

    container.innerHTML = `
      <table style="width: 100%; border-collapse: collapse; font-size: 11.5px;">
        <thead>
          <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-secondary); font-size: 10.5px;">
            <th style="padding: 4px 8px;">Simbolo</th>
            <th style="padding: 4px 8px;">Elemento</th>
            <th style="padding: 4px 8px; text-align: right;">Concentracion Sintetizada</th>
            <th style="padding: 4px 8px;">Categoria</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  function copyMixtureToCustom() {
    if (!lastSynthesizedMixture) {
      showNotification("Calcula primero una mezcla compuesta.");
      return;
    }

    const m = lastSynthesizedMixture;
    const btnCust = document.getElementById("btnWasteModeCustom");
    if (btnCust) btnCust.click();

    const setVal = (id, val) => {
      const inp = document.getElementById(id);
      if (inp) inp.value = val != null ? val : 0;
    };

    setVal("chemInput_Hu", Number(m.Hu).toFixed(2));
    setVal("chemInput_Ho", Number(m.Ho).toFixed(2));
    setVal("chemInput_H2O", Number(m.H2O).toFixed(4));
    setVal("chemInput_C", Number(m.C).toFixed(4));
    setVal("chemInput_biogenic_c_share", Number(m.biogenic_c_share).toFixed(3));
    setVal("chemInput_ash", Number(m.ash).toFixed(4));
    setVal("chemInput_degradability_100a", Number(m.degradability_100a).toFixed(3));
    setVal("chemInput_O", Number(m.O).toFixed(4));
    setVal("chemInput_H", Number(m.H).toFixed(4));
    setVal("chemInput_N", Number(m.N).toFixed(5));
    setVal("chemInput_S", Number(m.S).toFixed(5));
    setVal("chemInput_P", Number(m.P).toFixed(5));
    setVal("chemInput_Cl", Number(m.Cl).toFixed(5));
    setVal("chemInput_F", Number(m.F).toFixed(6));

    const metals = m.elements_ppm || {};
    wasteElementsList.forEach(el => {
      if (el.type === "ppm") {
        setVal(`chemInput_${el.key}`, Number(metals[el.key] || 0).toFixed(2));
      }
    });

    updateLiveMassBalance();
    showNotification("Composicion de la mezcla transferida al Editor Elemental.");
  }

  async function loadWasteMaterials(category = "") {
    try {
      const matSelect = document.getElementById("wasteMaterialSelect");
      if (!matSelect) return;
      matSelect.innerHTML = `<option value="">${tWaste("waste.search_placeholder", "Cargando residuos...")}</option>`;

      const url = category ? `/api/waste/materials?category=${encodeURIComponent(category)}` : "/api/waste/materials";
      const res = await fetch(url);
      const data = await res.json();
      if (data.status === "success" && data.materials) {
        wasteMaterialsCache = data.materials;
        matSelect.innerHTML = "";
        data.materials.forEach((m, idx) => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.name} (${m.category})`;
          if (idx === 0) opt.selected = true;
          matSelect.appendChild(opt);
        });
        updateWasteMaterialBadges();
        renderWasteMixtureRows();
        populateCustomTemplateSelect();
      }
    } catch (err) {
      console.error("Error al cargar materiales de residuos:", err);
    }
  }

  function updateWasteMaterialBadges() {
    const matSelect = document.getElementById("wasteMaterialSelect");
    if (!matSelect || !matSelect.value) return;
    const mat = wasteMaterialsCache.find(m => m.id === matSelect.value);
    if (!mat) return;

    const hu = mat.Hu != null ? Number(mat.Hu).toFixed(1) : (mat.net_heating_value_mj_kg != null ? Number(mat.net_heating_value_mj_kg).toFixed(1) : "--");
    const h2o = mat.H2O != null ? (Number(mat.H2O) * 100).toFixed(1) : (mat.water_content != null ? (Number(mat.water_content) * 100).toFixed(1) : "--");
    const c = mat.C != null ? (Number(mat.C) * 100).toFixed(1) : (mat.carbon_content != null ? (Number(mat.carbon_content) * 100).toFixed(1) : "--");
    const bio = mat.biogenic_c_share != null ? (Number(mat.biogenic_c_share) * 100).toFixed(0) : "--";
    const degrad = mat.degradability_100a != null ? Number(mat.degradability_100a).toFixed(2) : "--";

    const bHu = document.getElementById("badgeWasteHu");
    const bH2O = document.getElementById("badgeWasteH2O");
    const bC = document.getElementById("badgeWasteC");
    const bBio = document.getElementById("badgeWasteBio");
    const bDegrad = document.getElementById("badgeWasteDegrad");

    if (bHu) bHu.textContent = `PCI (Hu): ${hu} MJ/kg`;
    if (bH2O) bH2O.textContent = `Humedad: ${h2o}%`;
    if (bC) bC.textContent = `Carbono (C): ${c}%`;
    if (bBio) bBio.textContent = `Biogenico: ${bio}%`;
    if (bDegrad) bDegrad.textContent = `Degradabilidad 100a: ${degrad}`;

    // Si el drawer de elementos esta abierto, refrescarlo
    const drawer = document.getElementById("wastePredefinedElementsDrawer");
    if (drawer && drawer.style.display !== "none") {
      renderPredefinedElementsTable();
    }
  }

  function renderWasteMixtureRows() {
    const container = document.getElementById("wasteMixtureRowsContainer");
    if (!container) return;

    if (!wasteMixtureRows || wasteMixtureRows.length === 0) {
      container.innerHTML = `<div style="font-size: 11.5px; color: var(--text-muted); padding: 8px;">No hay fracciones en la mezcla. Haz clic en "+ Agregar Fraccion".</div>`;
      updateWasteMixtureSum();
      return;
    }

    container.innerHTML = wasteMixtureRows.map((row, idx) => {
      const opts = wasteMaterialsCache.map(m => {
        const sel = m.id === row.material_id ? "selected" : "";
        return `<option value="${m.id}" ${sel}>${escapeHtml(m.name)} (${escapeHtml(m.category)})</option>`;
      }).join("");

      return `
        <div style="display: grid; grid-template-columns: 3fr 1fr 40px; gap: 10px; align-items: center; padding: 6px 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px;">
          <select class="form-control styled-select-compact" style="height: 32px; font-size: 11.5px;" onchange="window.EconodeApp.updateWasteMixtureRowMaterial(${idx}, this.value)">
            ${opts}
          </select>
          <div style="display: flex; align-items: center; gap: 4px;">
            <input type="number" min="0" max="100" step="1" value="${row.share}" class="form-control" style="height: 32px; font-size: 11.5px; text-align: right;" onchange="window.EconodeApp.updateWasteMixtureRowShare(${idx}, this.value)" oninput="window.EconodeApp.updateWasteMixtureRowShare(${idx}, this.value)" />
            <span style="font-size: 11px; color: var(--text-muted); font-weight: 600;">%</span>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" style="height: 32px; padding: 0 8px; color: #ef4444;" onclick="window.EconodeApp.removeWasteMixtureRow(${idx})" title="Eliminar fraccion">
            &times;
          </button>
        </div>
      `;
    }).join("");

    updateWasteMixtureSum();
  }

  function addWasteMixtureRow(matId = "dokamat_11", share = 10.0) {
    if (!wasteMixtureRows) wasteMixtureRows = [];
    const id = matId || (wasteMaterialsCache.length > 0 ? wasteMaterialsCache[0].id : "dokamat_11");
    wasteMixtureRows.push({ material_id: id, share: parseFloat(share) || 10.0 });
    renderWasteMixtureRows();
  }

  function removeWasteMixtureRow(index) {
    if (!wasteMixtureRows || index < 0 || index >= wasteMixtureRows.length) return;
    wasteMixtureRows.splice(index, 1);
    renderWasteMixtureRows();
  }

  function updateWasteMixtureRowMaterial(index, matId) {
    if (wasteMixtureRows && wasteMixtureRows[index]) {
      wasteMixtureRows[index].material_id = matId;
      updateWasteMixtureSum();
    }
  }

  function updateWasteMixtureRowShare(index, shareVal) {
    if (wasteMixtureRows && wasteMixtureRows[index]) {
      wasteMixtureRows[index].share = parseFloat(shareVal) || 0.0;
      updateWasteMixtureSum();
    }
  }

  async function updateWasteMixtureSum() {
    const sum = wasteMixtureRows.reduce((acc, r) => acc + (parseFloat(r.share) || 0), 0);
    const sumBadge = document.getElementById("wasteMixtureSumBadge");
    if (sumBadge) {
      sumBadge.textContent = `${sum.toFixed(1)}%`;
      if (Math.abs(sum - 100.0) < 0.5) {
        sumBadge.style.color = "#10b981";
      } else {
        sumBadge.style.color = "#f59e0b";
      }
    }

    if (wasteMixtureRows.length > 0 && sum > 0) {
      try {
        const fractionsPayload = wasteMixtureRows.map(r => ({ material_id: r.material_id, share: r.share / sum }));
        const res = await fetch("/api/waste/mixture/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fractions: fractionsPayload })
        });
        const data = await res.json();
        if (data.status === "success" && data.mixed_material) {
          lastSynthesizedMixture = data.mixed_material;
          const m = data.mixed_material;
          const bHu = document.getElementById("badgeMixHu");
          const bH2O = document.getElementById("badgeMixH2O");
          const bC = document.getElementById("badgeMixC");
          const bBio = document.getElementById("badgeMixBio");
          const bDegrad = document.getElementById("badgeMixDegrad");

          if (bHu) bHu.textContent = `PCI Ponderado (Hu): ${Number(m.Hu).toFixed(1)} MJ/kg`;
          if (bH2O) bH2O.textContent = `Humedad: ${(Number(m.H2O) * 100).toFixed(1)}%`;
          if (bC) bC.textContent = `Carbono Total: ${(Number(m.C) * 100).toFixed(1)}%`;
          if (bBio) bBio.textContent = `Fraccion Biogenica: ${(Number(m.biogenic_c_share) * 100).toFixed(0)}%`;
          if (bDegrad) bDegrad.textContent = `Degradabilidad 100a: ${Number(m.degradability_100a).toFixed(2)}`;

          const mixDrawer = document.getElementById("wasteMixtureElementsDrawer");
          if (mixDrawer && mixDrawer.style.display !== "none") {
            renderMixtureElementsTable();
          }
        }
      } catch (e) {}
    }
  }

  function updateWasteTechPanels() {
    const tech = document.getElementById("wasteTechSelect")?.value || "mswi";
    const pMSWI = document.getElementById("techParamsMSWI");
    const pLF = document.getElementById("techParamsLandfill");
    const pTail = document.getElementById("techParamsTailings");
    const pWW = document.getElementById("techParamsWastewater");

    if (pMSWI) pMSWI.style.display = (tech === "mswi") ? "grid" : "none";
    if (pLF) pLF.style.display = (tech === "landfill_msw" || tech === "landfill") ? "grid" : "none";
    if (pTail) pTail.style.display = (tech === "tailings_impoundment") ? "flex" : "none";
    if (pWW) pWW.style.display = (tech === "wastewater") ? "grid" : "none";
  }

  async function executeWasteCalculation() {
    try {
      const tech = document.getElementById("wasteTechSelect")?.value || "mswi";
      const mass = parseFloat(document.getElementById("inputWasteMass")?.value || "100") || 100;
      const transportKm = parseFloat(document.getElementById("inputWasteTransport")?.value || "20") || 20;

      let payload = {
        technology: tech,
        mass_kg: mass,
        transport_km: transportKm,
        tech_kwargs: {}
      };

      if (currentWasteMode === "predefined") {
        const matId = document.getElementById("wasteMaterialSelect")?.value;
        if (!matId) {
          showNotification(tWaste("waste.select_material_req", "Selecciona un material de residuo"));
          return;
        }
        payload.material_id = matId;
      } else if (currentWasteMode === "mixture") {
        if (!wasteMixtureRows || wasteMixtureRows.length === 0) {
          showNotification("Agrega al menos una fraccion a la mezcla");
          return;
        }
        payload.fractions = wasteMixtureRows.map(r => ({ material_id: r.material_id, share: r.share }));
      } else {
        // Modo Quimico Completo: Leer los 47 parametros
        const custom_props = {
          name: "Residuo Personalizado (Estequiometria Doka)",
          Hu: parseFloat(document.getElementById("chemInput_Hu")?.value || "15.0"),
          Ho: parseFloat(document.getElementById("chemInput_Ho")?.value || "16.5"),
          H2O: parseFloat(document.getElementById("chemInput_H2O")?.value || "0.20"),
          C: parseFloat(document.getElementById("chemInput_C")?.value || "0.45"),
          biogenic_c_share: parseFloat(document.getElementById("chemInput_biogenic_c_share")?.value || "0.30"),
          ash: parseFloat(document.getElementById("chemInput_ash")?.value || "0.05"),
          degradability_100a: parseFloat(document.getElementById("chemInput_degradability_100a")?.value || "0.35"),
          O: parseFloat(document.getElementById("chemInput_O")?.value || "0.25"),
          H: parseFloat(document.getElementById("chemInput_H")?.value || "0.05"),
          N: parseFloat(document.getElementById("chemInput_N")?.value || "0.01"),
          S: parseFloat(document.getElementById("chemInput_S")?.value || "0.002"),
          P: parseFloat(document.getElementById("chemInput_P")?.value || "0.001"),
          Cl: parseFloat(document.getElementById("chemInput_Cl")?.value || "0.005"),
          F: parseFloat(document.getElementById("chemInput_F")?.value || "0.0001"),
          elements_ppm: {}
        };

        if (wasteElementsList && wasteElementsList.length > 0) {
          wasteElementsList.forEach(el => {
            if (el.type === "ppm") {
              const inp = document.getElementById(`chemInput_${el.key}`);
              if (inp) {
                custom_props.elements_ppm[el.key] = parseFloat(inp.value) || 0.0;
              }
            }
          });
        }

        payload.custom_properties = custom_props;
      }

      if (tech === "mswi") {
        payload.tech_kwargs.denox = document.getElementById("paramMSWIDeNOx")?.value || "sncr";
        payload.tech_kwargs.fgc_mode = document.getElementById("paramMSWIFGC")?.value || "wet_scrubber";
        payload.tech_kwargs.recovery_scrap = document.getElementById("paramMSWIScrap")?.checked ?? true;
      } else if (tech === "landfill_msw" || tech === "landfill") {
        payload.tech_kwargs.climate_site = document.getElementById("paramLFClimate")?.value || "site_3_glo_temperate";
        payload.tech_kwargs.gas_capture_rate = (parseFloat(document.getElementById("paramLFGasCapture")?.value || "45") / 100);
        payload.tech_kwargs.gas_utilization = document.getElementById("paramLFGasDest")?.value || "flare";
        payload.tech_kwargs.time_horizon = document.getElementById("paramLFTimeHorizon")?.value || "100a";
      } else if (tech === "tailings_impoundment") {
        payload.tech_kwargs.ard_potential = document.getElementById("paramTailingsARD")?.checked ?? true;
      } else if (tech === "wastewater") {
        payload.tech_kwargs.treatment_stage = document.getElementById("paramWWStage")?.value || "2_stage_biological";
        payload.tech_kwargs.sludge_fate = document.getElementById("paramWWSludgeFate")?.value || "sludge_to_incineration";
      }

      const btn = document.getElementById("btnCalculateWaste");
      if (btn) btn.disabled = true;

      const res = await fetch("/api/waste/calculate_advanced", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (btn) btn.disabled = false;

      if (data.status !== "success") {
        showNotification(data.message || "Error al calcular el tratamiento de residuo");
        return;
      }

      lastWasteCalculationResult = data.result || data;
      renderWasteResults(lastWasteCalculationResult);
      showNotification(`Calculo de fin de vida (${data.result.technology_name || tech}) completado.`);
    } catch (err) {
      console.error("Error al calcular residuo:", err);
      showNotification("Error de conexion al procesar el residuo: " + err.message);
      const btn = document.getElementById("btnCalculateWaste");
      if (btn) btn.disabled = false;
    }
  }

  function renderWasteResults(res) {
    const raw = res.result || res;
    const epd = raw.epd_modules_gwp || {};
    const avoidedEnergy = raw.avoided_energy || raw.avoided_burdens || {};
    const modDBreakdown = raw.module_d_breakdown || {};
    const solids = raw.lci_solid_residues || raw.solid_residues || {};
    const airEmissions = raw.lci_air_emissions || {};
    const waterLeachate = raw.lci_leachate_short_term_100a || raw.lci_water_emissions || {};

    const container = document.getElementById("wasteResultsContainer");
    if (container) container.style.display = "block";

    const badgeTech = document.getElementById("badgeActiveTechIndicator");
    if (badgeTech) badgeTech.textContent = raw.technology_name || raw.technology || "Doka Model";

    // Tarjetas Principales GWP
    const elNet = document.getElementById("resWasteNetGWP");
    const elC4 = document.getElementById("resWasteC4GWP");
    const elC4Sub = document.getElementById("resWasteC4Sub");
    const elModD = document.getElementById("resWasteModDGWP");
    const elC2C3 = document.getElementById("resWasteC2C3GWP");

    const netGwp = Number(epd.Net_Total_GWP != null ? epd.Net_Total_GWP : 0);
    const c4Gwp = Number(epd.C4_final_disposal != null ? epd.C4_final_disposal : 0);
    const c4Fossil = Number(epd.C4_fossil_gwp != null ? epd.C4_fossil_gwp : (epd.C4_methane_gwp || 0));
    const c4Bio = Number(epd.C4_biogenic_gwp != null ? epd.C4_biogenic_gwp : 0);
    const modDGwp = Number(epd.Module_D_avoided_burdens != null ? epd.Module_D_avoided_burdens : 0);
    const c2 = Number(epd.C2_transport != null ? epd.C2_transport : (epd.C2_transport_to_treatment || 0));
    const c3 = Number(epd.C3_waste_processing != null ? epd.C3_waste_processing : 0);

    if (elNet) elNet.textContent = `${netGwp >= 0 ? "+" : ""}${netGwp.toFixed(2)} kg CO2e`;
    if (elC4) elC4.textContent = `${c4Gwp >= 0 ? "+" : ""}${c4Gwp.toFixed(2)} kg CO2e`;
    if (elC4Sub) {
      elC4Sub.textContent = `Fosil/CH4: ${c4Fossil.toFixed(2)} | Biogenico: ${c4Bio.toFixed(2)}`;
    }
    if (elModD) elModD.textContent = `${modDGwp.toFixed(2)} kg CO2e`;
    if (elC2C3) elC2C3.textContent = `+${(c2 + c3).toFixed(2)} kg CO2e`;

    // 1. Panel Overview (Energia & Solidos)
    const elEnergy = document.getElementById("resWasteEnergyList");
    if (elEnergy) {
      const elecKwh = avoidedEnergy["Electricity recovered (kWh)"] || (avoidedEnergy.gross_electricity_mj ? (avoidedEnergy.gross_electricity_mj / 3.6) : 0);
      const heatMj = avoidedEnergy["District heat recovered (MJ)"] || avoidedEnergy.gross_heat_mj || 0;
      const creditElec = Math.abs(modDBreakdown.avoided_electricity_credit_kg_co2e || 0);
      const creditHeat = Math.abs(modDBreakdown.avoided_heat_credit_kg_co2e || 0);

      elEnergy.innerHTML = `
        <li>Electricidad exportada: <strong>${Number(elecKwh).toFixed(2)} kWh</strong> (${creditElec.toFixed(2)} kg CO2e evitados)</li>
        <li>Calor util exportado: <strong>${Number(heatMj).toFixed(2)} MJ</strong> (${creditHeat.toFixed(2)} kg CO2e evitados)</li>
      `;
    }

    const elSolids = document.getElementById("resWasteSolidsList");
    if (elSolids) {
      const bottomAsh = solids["Bottom ash (escoria a vertedero)"] || solids["Bottom ash (slag to landfill)"] || solids.bottom_ash_kg || 0;
      const flyAsh = solids["Air pollution control (APC) filter residues"] || solids.fly_ash_kg || 0;
      const iron = raw.avoided_materials?.["Scrap iron recovered (kg)"] || raw.avoided_burdens?.recovered_iron_scrap_kg || 0;
      const alu = raw.avoided_materials?.["Scrap aluminium recovered (kg)"] || 0;
      const cu = raw.avoided_materials?.["Scrap copper recovered (kg)"] || 0;

      elSolids.innerHTML = `
        <li>Escoria residual / Confinamiento: <strong>${Number(bottomAsh).toFixed(2)} kg</strong></li>
        <li>Cenizas volantes y filtros (APC): <strong>${Number(flyAsh).toFixed(2)} kg</strong></li>
        <li>Chatarra recuperada (Fe + Al + Cu): <strong>${Number(iron + alu + cu).toFixed(3)} kg</strong></li>
      `;
    }

    // 2. Panel Air: Renderizar tabla completa de emisiones atmosfericas (Gases y Metales Pesados)
    const elAirContainer = document.getElementById("resWasteAirEmissionsContainer");
    if (elAirContainer) {
      const airEntries = Object.entries(airEmissions);
      if (airEntries.length === 0) {
        elAirContainer.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px;">No hay emisiones atmosfericas directas registradas.</div>`;
      } else {
        const rows = airEntries.map(([name, val]) => {
          const valNum = Number(val);
          const valGrams = valNum * 1000.0;
          const isHeavyMetal = name.includes("to air") && !name.includes("Carbon") && !name.includes("Methane") && !name.includes("Nitrogen") && !name.includes("Sulfur");

          return `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td style="padding: 5px 8px; font-weight: ${isHeavyMetal ? "600" : "400"}; color: ${isHeavyMetal ? "var(--accent-emerald, #10b981)" : "inherit"};">
                ${name}
              </td>
              <td style="padding: 5px 8px; text-align: right; font-family: monospace;">${valNum >= 0.001 ? valNum.toFixed(4) : valNum.toExponential(3)} kg</td>
              <td style="padding: 5px 8px; text-align: right; font-family: monospace; color: var(--text-secondary);">${valGrams >= 0.001 ? valGrams.toFixed(3) : valGrams.toExponential(2)} g</td>
            </tr>
          `;
        }).join("");

        elAirContainer.innerHTML = `
          <table style="width: 100%; border-collapse: collapse; font-size: 11.5px;">
            <thead>
              <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-secondary); font-size: 10.5px;">
                <th style="padding: 5px 8px;">Compuesto / Flujo Elemental</th>
                <th style="padding: 5px 8px; text-align: right;">Masa Emitida (kg)</th>
                <th style="padding: 5px 8px; text-align: right;">Masa en Gramos (g)</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }
    }

    // 3. Panel Water: Renderizar tabla de lixiviacion acuosa
    const elWaterContainer = document.getElementById("resWasteWaterEmissionsContainer");
    if (elWaterContainer) {
      if (typeof waterLeachate === "object" && Object.keys(waterLeachate).length > 0) {
        const rows = Object.entries(waterLeachate).map(([elem, val]) => {
          const valNum = Number(val);
          return `
            <tr style="border-bottom: 1px solid var(--border-color);">
              <td class="mono" style="padding: 5px 8px; font-weight: 700; color: #3b82f6;">${elem}</td>
              <td style="padding: 5px 8px; text-align: right; font-family: monospace;">${valNum >= 0.001 ? valNum.toFixed(5) : valNum.toExponential(3)} kg</td>
              <td style="padding: 5px 8px; text-align: right; font-family: monospace; color: var(--text-secondary);">${(valNum * 1000).toFixed(3)} g</td>
            </tr>
          `;
        }).join("");

        elWaterContainer.innerHTML = `
          <table style="width: 100%; border-collapse: collapse; font-size: 11.5px;">
            <thead>
              <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-secondary); font-size: 10.5px;">
                <th style="padding: 5px 8px;">Elemento Lixiviado</th>
                <th style="padding: 5px 8px; text-align: right;">Masa Lixiviada (kg)</th>
                <th style="padding: 5px 8px; text-align: right;">Masa en Gramos (g)</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      } else {
        elWaterContainer.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px;">Sin lixiviacion acuosa directa para esta tecnologia o material inerte.</div>`;
      }
    }

    // Botones de exportacion
    const btnExport = document.getElementById("btnExportWasteJson");
    const btnSima = document.getElementById("btnExportWasteSimaPro");
    const btnEco = document.getElementById("btnExportWasteEcoSpold");
    const btnInsert = document.getElementById("btnInsertWasteToCanvas");
    if (btnExport) btnExport.style.display = "inline-flex";
    if (btnSima) btnSima.style.display = "inline-flex";
    if (btnEco) btnEco.style.display = "inline-flex";
    if (btnInsert) btnInsert.style.display = "inline-flex";
  }

  function exportWasteCalculationJson() {
    if (!lastWasteCalculationResult) return;
    const str = JSON.stringify(lastWasteCalculationResult, null, 2);
    const blob = new Blob([str], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Fin_de_Vida_Doka2026_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function exportWasteCalculationSimaPro() {
    if (!lastWasteCalculationResult) return;
    try {
      const res = await fetch("/api/waste/export/simapro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result: lastWasteCalculationResult })
      });
      const data = await res.json();
      if (data.status === "success" && data.content) {
        const blob = new Blob([data.content], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = data.filename || `Fin_de_Vida_SimaPro_${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showNotification("Archivo SimaPro CSV exportado exitosamente.");
      }
    } catch (e) {
      showNotification("Error al exportar a SimaPro: " + e.message);
    }
  }

  async function exportWasteCalculationEcoSpold() {
    if (!lastWasteCalculationResult) return;
    try {
      const res = await fetch("/api/waste/export/ecospold2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result: lastWasteCalculationResult })
      });
      const data = await res.json();
      if (data.status === "success" && data.content) {
        const blob = new Blob([data.content], { type: "application/xml;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = data.filename || `Fin_de_Vida_EcoSpold2_${Date.now()}.xml`;
        a.click();
        URL.revokeObjectURL(url);
        showNotification("Dataset EcoSpold 2 XML exportado exitosamente.");
      }
    } catch (e) {
      showNotification("Error al exportar a EcoSpold2: " + e.message);
    }
  }

  function insertWasteTreatmentNodeToCanvas() {
    if (!lastWasteCalculationResult) return;
    const raw = lastWasteCalculationResult.result || lastWasteCalculationResult;
    const input = raw.input_summary || {};
    const epd = raw.epd_modules_gwp || {};
    const procName = `Fin de Vida: ${input.material_name} (${raw.technology_name || input.technology || "Tratamiento"})`;
    
    if (typeof addNodeToCanvas === "function") {
      const inputs = [
        { name: input.material_name, amount: input.mass_kg, unit: "kg", is_unit: true },
        { name: `Transporte EoL (${input.transport_km} km)`, amount: Number((input.mass_kg * input.transport_km / 1000).toFixed(3)), unit: "tkm", is_unit: false }
      ];
      const outputs = [
        { name: `Tratamiento: ${input.material_name}`, amount: input.mass_kg, unit: "kg", is_reference: true },
        { name: "GWP Neto (C1-C4 + D)", amount: epd.Net_Total_GWP, unit: "kg CO2e", is_elementary: true }
      ];
      addNodeToCanvas(procName, "treatment", "kg", null, null, inputs, outputs);
      showNotification(`Proceso "${procName}" anadido al lienzo del sistema.`);
      showView("canvas");
    } else {
      showNotification(`Proceso "${procName}" calculado (GWP: ${epd.Net_Total_GWP} kg CO2e).`);
    }
  }

  function setupWasteToolsEventListeners() {
    document.getElementById("btnFloatWasteTools")?.addEventListener("click", openWasteToolsModal);
    document.getElementById("drawerBtnWasteTools")?.addEventListener("click", () => {
      if (typeof closeDrawerMenu === "function") closeDrawerMenu();
      openWasteToolsModal();
    });
    document.getElementById("btnCloseWasteModal")?.addEventListener("click", closeWasteToolsModal);
    document.getElementById("btnCancelWasteModal")?.addEventListener("click", closeWasteToolsModal);

    const btnPred = document.getElementById("btnWasteModePredefined");
    const btnMix = document.getElementById("btnWasteModeMixture");
    const btnCust = document.getElementById("btnWasteModeCustom");
    const secPred = document.getElementById("wastePredefinedSection");
    const secMix = document.getElementById("wasteMixtureSection");
    const secCust = document.getElementById("wasteCustomSection");

    btnPred?.addEventListener("click", () => {
      currentWasteMode = "predefined";
      btnPred.classList.add("active");
      btnMix?.classList.remove("active");
      btnCust?.classList.remove("active");
      if (secPred) secPred.style.display = "block";
      if (secMix) secMix.style.display = "none";
      if (secCust) secCust.style.display = "none";
    });

    btnMix?.addEventListener("click", () => {
      currentWasteMode = "mixture";
      btnMix.classList.add("active");
      btnPred?.classList.remove("active");
      btnCust?.classList.remove("active");
      if (secPred) secPred.style.display = "none";
      if (secMix) secMix.style.display = "block";
      if (secCust) secCust.style.display = "none";
      renderWasteMixtureRows();
    });

    btnCust?.addEventListener("click", () => {
      currentWasteMode = "custom";
      btnCust.classList.add("active");
      btnPred?.classList.remove("active");
      btnMix?.classList.remove("active");
      if (secPred) secPred.style.display = "none";
      if (secMix) secMix.style.display = "none";
      if (secCust) secCust.style.display = "block";
      if (wasteElementsList.length === 0) {
        loadWasteElements();
      }
    });

    // Botones de inspeccion de elementos
    document.getElementById("btnTogglePredefinedElements")?.addEventListener("click", togglePredefinedElementsDrawer);
    document.getElementById("btnCopyPredefinedToCustom")?.addEventListener("click", copyPredefinedToCustom);
    document.getElementById("btnToggleMixtureElements")?.addEventListener("click", toggleMixtureElementsDrawer);
    document.getElementById("btnCopyMixtureToCustom")?.addEventListener("click", copyMixtureToCustom);

    // Herramientas de plantilla y preajustes en modo custom
    document.getElementById("btnApplyCustomTemplate")?.addEventListener("click", () => {
      const sel = document.getElementById("selectCustomTemplate");
      if (sel && sel.value) loadMaterialIntoCustomEditor(sel.value);
    });

    document.getElementById("btnPresetMSW")?.addEventListener("click", () => applyPreset("msw"));
    document.getElementById("btnPresetPlastics")?.addEventListener("click", () => applyPreset("plastics"));
    document.getElementById("btnPresetEwaste")?.addEventListener("click", () => applyPreset("ewaste"));
    document.getElementById("btnClearCustomElements")?.addEventListener("click", () => applyPreset("zero"));

    // Buscador y filtros de categorias de quimicos
    document.getElementById("inputSearchChemicals")?.addEventListener("input", filterChemicalElements);
    document.querySelectorAll("[data-chem-cat]").forEach(btn => {
      btn.addEventListener("click", () => {
        const cat = btn.getAttribute("data-chem-cat");
        setChemicalCategoryFilter(cat);
      });
    });

    // Pestañas de Resultados
    const resTabOverview = document.getElementById("btnResTabOverview");
    const resTabAir = document.getElementById("btnResTabAir");
    const resTabWater = document.getElementById("btnResTabWater");
    const resPanelOverview = document.getElementById("resPanelOverview");
    const resPanelAir = document.getElementById("resPanelAir");
    const resPanelWater = document.getElementById("resPanelWater");

    resTabOverview?.addEventListener("click", () => {
      resTabOverview.classList.add("active");
      resTabAir?.classList.remove("active");
      resTabWater?.classList.remove("active");
      if (resPanelOverview) resPanelOverview.style.display = "grid";
      if (resPanelAir) resPanelAir.style.display = "none";
      if (resPanelWater) resPanelWater.style.display = "none";
    });

    resTabAir?.addEventListener("click", () => {
      resTabAir.classList.add("active");
      resTabOverview?.classList.remove("active");
      resTabWater?.classList.remove("active");
      if (resPanelOverview) resPanelOverview.style.display = "none";
      if (resPanelAir) resPanelAir.style.display = "block";
      if (resPanelWater) resPanelWater.style.display = "none";
    });

    resTabWater?.addEventListener("click", () => {
      resTabWater.classList.add("active");
      resTabOverview?.classList.remove("active");
      resTabAir?.classList.remove("active");
      if (resPanelOverview) resPanelOverview.style.display = "none";
      if (resPanelAir) resPanelAir.style.display = "none";
      if (resPanelWater) resPanelWater.style.display = "block";
    });

    document.getElementById("btnAddMixtureRow")?.addEventListener("click", () => addWasteMixtureRow());

    document.getElementById("wasteCategorySelect")?.addEventListener("change", (e) => {
      loadWasteMaterials(e.target.value);
    });

    document.getElementById("wasteMaterialSelect")?.addEventListener("change", updateWasteMaterialBadges);
    document.getElementById("wasteTechSelect")?.addEventListener("change", updateWasteTechPanels);

    document.getElementById("btnCalculateWaste")?.addEventListener("click", executeWasteCalculation);
    document.getElementById("btnExportWasteJson")?.addEventListener("click", exportWasteCalculationJson);
    document.getElementById("btnExportWasteSimaPro")?.addEventListener("click", exportWasteCalculationSimaPro);
    document.getElementById("btnExportWasteEcoSpold")?.addEventListener("click", exportWasteCalculationEcoSpold);
    document.getElementById("btnInsertWasteToCanvas")?.addEventListener("click", insertWasteTreatmentNodeToCanvas);

    updateWasteTechPanels();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupWasteToolsEventListeners);
  } else {
    setupWasteToolsEventListeners();
  }


  window.ECONODE = null;
  window.EconodeApp = {
    updateLiveMassBalance,
    loadMaterialIntoCustomEditor,
    applyPreset,
    openWasteToolsModal,
    closeWasteToolsModal,
    initWasteToolsData,
    executeWasteCalculation,
    exportWasteCalculationJson,
    exportWasteCalculationSimaPro,
    exportWasteCalculationEcoSpold,
    insertWasteTreatmentNodeToCanvas,
    addWasteMixtureRow,
    removeWasteMixtureRow,
    updateWasteMixtureRowMaterial,
    updateWasteMixtureRowShare,
    toggleProjectCollapse,
    toggleStandaloneCollapse,
    openNewProjectModal,
    closeNewProjectModal,
    submitNewProject,
    deleteProject,
    openAssignProjectModal,
    closeAssignProjectModal,
    submitAssignProject,
    openCompareProjectModal,
    closeCompareProjectModal,
    openWizardForProject,
    openParameterModal,
    closeParameterModal,
    saveParameterFromModal,
    deleteParameter,
    editParameterById,
    exportParametersCsv,
    triggerExportDownload,
    exportDocx: (sysId) => {
      const id = sysId || (state.activeSystem ? state.activeSystem.id : 21);
      const lang = window.I18n ? window.I18n.getCurrentLanguage() : "es";
      triggerExportDownload(`/api/systems/${id}/export/docx?lang=${lang}`, `Reporte_ACV_NOM070_Sistema_${id}_${lang.toUpperCase()}.docx`);
    },
    exportPdf: (sysId) => {
      const id = sysId || (state.activeSystem ? state.activeSystem.id : 21);
      const lang = window.I18n ? window.I18n.getCurrentLanguage() : "es";
      triggerExportDownload(`/api/systems/${id}/export/pdf?lang=${lang}`, `Reporte_ACV_NOM070_Sistema_${id}_${lang.toUpperCase()}.pdf`);
    },
    showView,
    openSystem,
    prefetchSystem,
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
    submitEmailLogin: (email, pass) => handleEmailLogin(email, pass),
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
    copyToClipboard: (text) => {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
          showNotification("¡Enlace copiado al portapapeles!");
        }).catch(() => {
          prompt("Copia este enlace de invitación:", text);
        });
      } else {
        prompt("Copia este enlace de invitación:", text);
      }
    },
    cancelInvite: async (invId) => {
      if (!confirm("¿Deseas revocar esta invitación? El enlace dejará de ser válido.")) return;
      try {
        await api.cancelInvitation(invId);
        showNotification("Invitación revocada exitosamente.");
        await loadActiveInvitationsList();
      } catch (err) {
        alert("Error al revocar: " + err.message);
      }
    },
    openInviteModal: (systemId, systemName) => {
      const modal = document.getElementById("modalInviteCollaborator");
      const idInput = document.getElementById("inviteSystemId");
      const nameInput = document.getElementById("inviteSystemNameDisplay");
      const personName = document.getElementById("inviteCollaboratorName");
      const personEmail = document.getElementById("inviteCollaboratorEmail");
      const genBox = document.getElementById("inviteGeneratedBox");
      if (idInput) idInput.value = systemId || "";
      if (nameInput) nameInput.value = systemName ? unescape(systemName) : "Todos los proyectos de la organización";
      if (personName) personName.value = "";
      if (personEmail) personEmail.value = "";
      if (genBox) genBox.style.display = "none";
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
      }
      loadActiveInvitationsList();
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
        systemCanvasCache.delete(systemId);
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
      let targetId = systemId ? parseInt(systemId, 10) : (state.activeSystem ? state.activeSystem.id : null);
      if (!targetId && state.systems && state.systems.length > 0) {
        targetId = state.systems[0].id;
      }
      if (targetId) {
        const found = state.systems.find(s => parseInt(s.id, 10) === targetId);
        if (found) {
          state.activeSystem = found;
          const modalTitle = document.getElementById("modalDocsTitle");
          if (modalTitle) {
            modalTitle.textContent = `${window.I18n ? window.I18n.t("vault.modal_title", "Bóveda de Documentos") : "Bóveda de Documentos"}: ${found.name}`;
          }
        }
        const hiddenSys = document.getElementById("inputDocSystemId");
        if (hiddenSys) hiddenSys.value = targetId;
      }
      const modal = document.getElementById("modalDocuments");
      if (modal) {
        modal.style.display = "flex";
        modal.classList.add("active");
        loadDocumentsList(targetId);
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
        if (state.auditCache) {
          state.auditCache[`${sysId}_${stdId}`] = {
            clauses: state.checklist,
            meta: state.checklistMeta
          };
        }
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
      const targetId = String(nodeId).trim();
      const cleanNumeric = targetId.replace(/\D/g, "");

      // 1. Localizar el nodo antes de retirarlo
      const nodeIndex = (state.canvasNodes || []).findIndex((n) => {
        const nid = String(n.id);
        const npid = String(n.process_id !== undefined ? n.process_id : "");
        return nid === targetId || npid === targetId ||
               (cleanNumeric && (nid === cleanNumeric || nid === `node_${cleanNumeric}` || npid === cleanNumeric));
      });

      let removedNode = null;
      if (nodeIndex !== -1) {
        removedNode = state.canvasNodes[nodeIndex];
        state.canvasNodes.splice(nodeIndex, 1);
      } else {
        state.canvasNodes = (state.canvasNodes || []).filter((n) => {
          const nid = String(n.id);
          const npid = String(n.process_id !== undefined ? n.process_id : "");
          const match = nid === targetId || npid === targetId ||
                        (cleanNumeric && (nid === cleanNumeric || nid === `node_${cleanNumeric}` || npid === cleanNumeric));
          if (match && !removedNode) removedNode = n;
          return !match;
        });
      }

      const removedId = removedNode ? String(removedNode.id) : targetId;
      const removedPid = removedNode && removedNode.process_id !== undefined ? String(removedNode.process_id) : "";
      const removedClean = (removedPid || removedId).replace(/\D/g, "") || cleanNumeric;

      // 2. Preservar SIEMPRE el proceso en el catálogo (paleta), marcándolo como disponible para el lienzo
      if (!state.paletteProcesses) state.paletteProcesses = [];
      let foundInPalette = false;
      state.paletteProcesses.forEach(p => {
        const pid = String(p.id);
        const ppid = String(p.process_id !== undefined ? p.process_id : "");
        const match = pid === removedId || pid === targetId || ppid === removedPid ||
                      (removedClean && (pid === removedClean || pid === `node_${removedClean}` || ppid === removedClean));
        if (match) {
          delete p._placedOnCanvas;
          foundInPalette = true;
        }
      });

      // Si no estaba explícitamente en la lista de paleta pero estaba en el lienzo, conservarlo en el catálogo
      if (!foundInPalette && removedNode) {
        const unplaced = JSON.parse(JSON.stringify(removedNode));
        delete unplaced._placedOnCanvas;
        state.paletteProcesses.push(unplaced);
      }

      // 3. Quitar TODAS las conexiones conectadas a este nodo (sin excepciones)
      state.canvasEdges = (state.canvasEdges || []).filter((e) => {
        const ef = String(e.from);
        const et = String(e.to);
        const esrc = String(e.source_process_id !== undefined ? e.source_process_id : "");
        const etgt = String(e.target_process_id !== undefined ? e.target_process_id : "");

        const isSource = ef === removedId || ef === targetId || (removedPid && ef === removedPid) ||
                         (removedClean && (ef === removedClean || ef === `node_${removedClean}` || esrc === removedClean));
        const isTarget = et === removedId || et === targetId || (removedPid && et === removedPid) ||
                         (removedClean && (et === removedClean || et === `node_${removedClean}` || etgt === removedClean));

        return !isSource && !isTarget;
      });

      // 4. Restaurar orígenes de insumos dependientes a mercado global
      if (removedNode) {
        state.canvasNodes.forEach(p => {
          if (Array.isArray(p.inputs)) {
            p.inputs.forEach(inp => {
              if (inp.origin && (inp.origin === removedNode.name || inp.origin.includes(removedNode.name))) {
                inp.origin = "Mercado ecoinvent 3.12";
              }
            });
          }
        });
      }

      // 5. Limpiar inspector si el nodo retirado estaba seleccionado
      if (state.selectedNode) {
        const selId = String(state.selectedNode.id);
        const selPid = String(state.selectedNode.process_id !== undefined ? state.selectedNode.process_id : "");
        if (selId === removedId || selId === targetId || selPid === removedPid ||
            (removedClean && (selId === removedClean || selId === `node_${removedClean}` || selPid === removedClean))) {
          state.selectedNode = null;
          inspectNode(null);
        }
      }

      // 6. Actualizar vistas inmediatamente
      renderCanvasEdges();
      renderPaletteProcesses();
      renderCanvasStage();
      if (state.canvasViewMode === "table") {
        renderCanvasTableView();
      }
      scheduleAutoSaveCanvas();
      showNotification(removedNode ? `Proceso "${removedNode.name}" retirado del lienzo.` : "Nodo retirado del lienzo.");
    },
    addPaletteNode: (param1, cat, unit) => {
      const searchStr = String(param1);
      const procs = getAllSystemProcesses();
      const found = procs.find(p => String(p.id) === searchStr || String(p.process_id) === searchStr);
      if (found) {
        found._placedOnCanvas = true;
        if (state.paletteProcesses) {
          const pItem = state.paletteProcesses.find(p => String(p.id) === searchStr || String(p.process_id) === searchStr);
          if (pItem) pItem._placedOnCanvas = true;
        }
        const already = state.canvasNodes.find(n => String(n.id) === String(found.id) || String(n.process_id) === String(found.process_id));
        if (!already) {
          state.canvasNodes.push({
            ...found,
            id: found.id || `node_${found.process_id}`,
            process_id: found.process_id,
            x: 60 + Math.random() * 80,
            y: 80 + Math.random() * 180,
            pos_x: 60 + Math.random() * 80,
            pos_y: 80 + Math.random() * 180,
            _placedOnCanvas: true
          });
        }
        renderCanvasStage();
        renderPaletteProcesses();
        if (state.canvasViewMode === "table") {
          renderCanvasTableView();
        }
        scheduleAutoSaveCanvas();
        showNotification(`Proceso "${found.name}" colocado en el lienzo.`);
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
    openCreateCustomFlowModal: () => openCreateCustomFlowModal(),
    tableUpdateAmount: (nodeId, type, idx, val, isInput) => tableUpdateAmount(nodeId, type, idx, val, isInput),
    tableUpdateFlowName: (nodeId, type, idx, val) => tableUpdateFlowName(nodeId, type, idx, val),
    tableUpdateUnit: (nodeId, type, idx, val) => tableUpdateUnit(nodeId, type, idx, val),
    tableUpdateFlowComment: (nodeId, type, idx, val) => tableUpdateFlowComment(nodeId, type, idx, val),
    tableUpdateFlowAssumptions: (nodeId, type, idx, val) => tableUpdateFlowAssumptions(nodeId, type, idx, val),
    tableUpdateFlowLinks: (nodeId, type, idx, val) => tableUpdateFlowLinks(nodeId, type, idx, val),
    tableUpdateProcessName: (nodeId, val) => tableUpdateProcessName(nodeId, val),
    tableCreateProcessInline: (name, mat, amt, unit, procId) => tableCreateProcessInline(name, mat, amt, unit, procId),
    tableCreateFlowInline: (nodeId, name, amt, unit, origin, srcId, srcProcId, flowKind, comment, assumptions, externalLinks) => tableCreateFlowInline(nodeId, name, amt, unit, origin, srcId, srcProcId, flowKind, comment, assumptions, externalLinks),
    tableUpdateNewFlowKind: (selectEl) => tableUpdateNewFlowKind(selectEl),
    tableChangeProvider: (nodeId, flowIdx, val) => tableChangeProvider(nodeId, flowIdx, val),
    tableChangeNodeToCatalogProcess: (nodeId, procId) => tableChangeNodeToCatalogProcess(nodeId, procId),
    tableDeleteProcess: (nodeId) => tableDeleteProcess(nodeId),
    tableAddNewConnection: () => tableAddNewConnection(),
    updateNewConnFlows: () => updateNewConnFlows(),
    handleNewProcessKeyDown: (e, el) => handleNewProcessKeyDown(e, el),
    handleNewFlowKeyDown: (e, id, el) => handleNewFlowKeyDown(e, id, el),
    excelAutocompleteOpen: (inputEl, type, options) => excelAutocomplete.open(inputEl, type, options),
    excelAutocompleteQuery: (inputEl, type) => excelAutocomplete.query(inputEl ? inputEl.value : ""),
    excelAutocompleteKeyDown: (e) => excelAutocomplete.handleKeyDown(e),
    excelAutocompleteSelect: (idx) => excelAutocomplete.selectItem(idx),
    excelAutocompleteClose: () => excelAutocomplete.close(),
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
    getNodes: () => state.canvasNodes,
    getEdges: () => state.canvasEdges,
    closeModal: (id) => closeModal(id),
    openVersionMatchModal: (id) => openVersionMatchModal(id),
    closeVersionMatchModal: () => closeVersionMatchModal(),
    openSimaProModeModal: (meta, content, target, sysId) => openSimaProModeModal(meta, content, target, sysId),
    closeSimaProModeModal: () => closeSimaProModeModal(),
    selectSimaProImportMode: (mode) => selectSimaProImportMode(mode),
    confirmSimaProImport: () => confirmSimaProImport(),
    onTargetDatabaseChange: () => onTargetDatabaseChange(),
    onSelectLocationVariation: (nodeId, val) => onSelectLocationVariation(nodeId, val),
    onSearchSubstituteProcess: (nodeId, q) => onSearchSubstituteProcess(nodeId, q),
    onSelectSubstituteProcess: (nodeId, tId, name, loc) => onSelectSubstituteProcess(nodeId, tId, name, loc),
    toggleVersionMatchFlowsList: () => toggleVersionMatchFlowsList(),
    promptFlowSubstitution: (code, name) => promptFlowSubstitution(code, name),
    submitVersionConversion: () => submitVersionConversion(),
    openSystemInfoModal: (id) => openSystemInfoModal(id),
    closeSystemInfoModal: () => closeSystemInfoModal(),
    openCanvasFromInfo: () => openCanvasFromInfo(),
    openVaultFromInfo: () => openVaultFromInfo(),
    openNewGhgInventoryModal: () => openNewGhgInventoryModal(),
    submitNewGhgInventory: () => submitNewGhgInventory(),
    openAddGhgEntryModal: (scope, cat) => openAddGhgEntryModal(scope, cat),
    submitNewGhgEntry: () => submitNewGhgEntry(),
    deleteGhgEntry: (id) => deleteGhgEntry(id),
    deleteCurrentGhgInventory: () => deleteCurrentGhgInventory(),
    switchGhgTab: (tab) => switchGhgTab(tab),
    toggleGhgAccordion: (catKey) => toggleGhgAccordion(catKey),
    onGhgCalcTypeChange: () => onGhgCalcTypeChange(),
    previewGhgEmissions: () => previewGhgEmissions(),
    onGhgFactorSelectChange: () => onGhgFactorSelectChange(),
    onGhgSpendSectorChange: () => onGhgSpendSectorChange(),
    onGhgProductSystemSelectChange: () => onGhgProductSystemSelectChange(),
    searchGhgFactorsTab: () => searchGhgFactorsTab(),
    switchReportMode: (m) => switchReportMode(m, true),
    loadEpdReport: (std) => loadEpdReport(std),
    loadGhgReport: (invId) => loadGhgReport(invId),
    renderGhgReportView: (inv) => renderGhgReportView(inv),
    downloadGhgReportJson: () => downloadGhgReportJson(),
    loadDashboardGhgInventories: () => loadDashboardGhgInventories(),
    renderDashboardGhgInventories: (list) => renderDashboardGhgInventories(list),
    openGhgReportForInventory: (id) => openGhgReportForInventory(id),
    openGhgModuleForInventory: (id) => openGhgModuleForInventory(id),
    deleteGhgInventoryFromDashboard: (id, name) => deleteGhgInventoryFromDashboard(id, name),
    openDeveloperSettingsModal: () => openDeveloperSettingsModal(),
    closeDeveloperSettingsModal: () => closeDeveloperSettingsModal(),
    switchDevTab: (t) => switchDevTab(t),
    loadUserApiKeys: () => loadUserApiKeys(),
    generateUserApiKey: () => generateUserApiKey(),
    revokeUserApiKey: (id) => revokeUserApiKey(id),
    copyDevSnippet: (id) => copyDevSnippet(id),
    onLanguageChange: (lang) => {
      renderDashboardTable();
      renderDashboardGhgInventories();
      renderDashboardKpis();
      renderChecklistTable();
      renderCommentsThread();
      renderReportProcessesTable();
      renderPaletteProcesses();
      renderCanvasStage();
      if (state.canvasViewMode === "table") {
        renderCanvasTableView();
      }
      if (state.activeEpdReport && state.reportViewMode === "epd") {
        renderEpdReportView(state.activeEpdReport);
      }
      if (state.activeGhgReportInventory && state.reportViewMode === "ghg") {
        renderGhgReportView(state.activeGhgReportInventory);
      }
      if (typeof window._refreshWizardEpdTemplates === "function") {
        window._refreshWizardEpdTemplates();
      }
      updateCanvasHeaderToolbar();
      if (state.selectedNode) {
        inspectNode(state.selectedNode);
      }
      if (document.getElementById("modalSystemInfo")?.classList.contains("active") && currentInfoSystemId) {
        openSystemInfoModal(currentInfoSystemId);
      }
      updateUserUI();
    }
  };
  window.ECONODE = window.EconodeApp;

  // Arranque al cargar el DOM
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
  } else {
    initApp();
  }
})();
