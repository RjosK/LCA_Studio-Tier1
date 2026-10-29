/**
 * ECONODE Studio - Integración de Almacenamiento en Google Drive (BYOS - Bring Your Own Storage)
 * 
 * Permite a cada Analista almacenar sus proyectos, modelos ACV, evidencias documentales
 * y reportes directamente dentro de su propio Google Drive.
 * 
 * Alcance OAuth 2.0: https://www.googleapis.com/auth/drive.file
 * (Acceso estricto y seguro: únicamente lee y escribe archivos creados por ECONODE Studio).
 */

(function () {
  "use strict";

  const CLIENT_ID = "968718859059-81u6bj6l4op1e0dsnblqg73ego8ns59j.apps.googleusercontent.com";
  const DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file";
  const ROOT_FOLDER_NAME = "ECONODE Studio Projects";

  let tokenClient = null;
  let accessToken = null;
  let tokenExpiration = 0;
  let cachedRootFolderId = null;

  /**
   * Comprueba si existe un token de Google Drive válido y no expirado.
   */
  function hasToken() {
    if (accessToken && Date.now() < tokenExpiration) return true;
    const storedTok = sessionStorage.getItem("econode_drive_token");
    const storedExp = parseInt(sessionStorage.getItem("econode_drive_token_exp") || "0", 10);
    return Boolean(storedTok && Date.now() < storedExp);
  }

  /**
   * Obtiene un Access Token de Google Identity Services con el scope drive.file.
   * Si ya existe un token válido en memoria o sessionStorage, lo reutiliza.
   */
  async function getAccessToken() {
    // 1. Verificar si tenemos token en memoria no expirado
    if (accessToken && Date.now() < tokenExpiration) {
      return accessToken;
    }

    // 2. Verificar si existe en sessionStorage
    const storedTok = sessionStorage.getItem("econode_drive_token");
    const storedExp = parseInt(sessionStorage.getItem("econode_drive_token_exp") || "0", 10);
    if (storedTok && Date.now() < storedExp) {
      accessToken = storedTok;
      tokenExpiration = storedExp;
      return accessToken;
    }

    // 3. Solicitar autorización mediante popup de Google Identity Services
    return new Promise((resolve, reject) => {
      if (!window.google || !window.google.accounts || !window.google.accounts.oauth2) {
        return reject(new Error("La librería de Google Identity Services aún no está cargada."));
      }

      tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: CLIENT_ID,
        scope: DRIVE_FILE_SCOPE,
        callback: (resp) => {
          if (resp && resp.access_token) {
            accessToken = resp.access_token;
            // Expiración por defecto 3500 segundos (~1 hora)
            const expiresInMs = (parseInt(resp.expires_in, 10) || 3500) * 1000;
            tokenExpiration = Date.now() + expiresInMs;
            try {
              sessionStorage.setItem("econode_drive_token", accessToken);
              sessionStorage.setItem("econode_drive_token_exp", tokenExpiration.toString());
            } catch (e) {}
            resolve(accessToken);
          } else {
            reject(new Error(resp?.error_description || resp?.error || "Autorización de Google Drive cancelada"));
          }
        },
        error_callback: (err) => {
          reject(new Error(err?.message || "Error al solicitar permisos de Google Drive"));
        }
      });

      tokenClient.requestAccessToken({ prompt: "" });
    });
  }

  /**
   * Helper para peticiones HTTP autenticadas a la API REST v3 de Google Drive.
   */
  async function driveFetch(url, options = {}) {
    const token = await getAccessToken();
    const headers = options.headers ? { ...options.headers } : {};
    headers["Authorization"] = `Bearer ${token}`;

    const resp = await fetch(url, { ...options, headers });
    if (!resp.ok) {
      let errMsg = `Error Google Drive (${resp.status})`;
      try {
        const errJson = await resp.json();
        errMsg = errJson?.error?.message || errMsg;
      } catch (e) {}
      throw new Error(errMsg);
    }
    if (resp.status === 204) return null;
    return await resp.json();
  }

  /**
   * Localiza o crea la carpeta raíz "ECONODE Studio Projects" en el Google Drive del usuario.
   */
  async function getOrCreateRootFolder() {
    if (cachedRootFolderId) return cachedRootFolderId;

    const q = `'root' in parents and name = '${ROOT_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`;
    const searchUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name,webViewLink)`;
    const listRes = await driveFetch(searchUrl);

    if (listRes.files && listRes.files.length > 0) {
      cachedRootFolderId = listRes.files[0].id;
      return cachedRootFolderId;
    }

    // Crear carpeta raíz si no existe
    const createUrl = "https://www.googleapis.com/drive/v3/files";
    const newFolder = await driveFetch(createUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: ROOT_FOLDER_NAME,
        mimeType: "application/vnd.google-apps.folder",
        description: "Carpeta principal de sistemas producto, modelos ACV y evidencias de ECONODE Studio"
      })
    });

    cachedRootFolderId = newFolder.id;
    return cachedRootFolderId;
  }

  /**
   * Crea la carpeta dedicada para un proyecto específico en Google Drive, con subcarpetas
   * para Evidencias y Reportes.
   */
  async function createProjectFolder(projectName, projectCode) {
    const rootId = await getOrCreateRootFolder();
    const folderDisplayName = `[${projectCode || "SYS"}] ${projectName}`;

    // Verificar si ya existe una carpeta con este nombre para evitar duplicados en Drive
    try {
      const q = `'${rootId}' in parents and name = '${folderDisplayName.replace(/'/g, "\\'")}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`;
      const searchUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name)`;
      const listRes = await driveFetch(searchUrl);
      if (listRes.files && listRes.files.length > 0) {
        const existing = listRes.files[0];
        return {
          folderId: existing.id,
          folderName: existing.name,
          folderUrl: `https://drive.google.com/drive/folders/${existing.id}`
        };
      }
    } catch (e) {
      console.warn("Verificación de carpeta existente en Drive omitida:", e);
    }

    // 1. Crear carpeta principal del proyecto
    const projectFolder = await driveFetch("https://www.googleapis.com/drive/v3/files", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: folderDisplayName,
        mimeType: "application/vnd.google-apps.folder",
        parents: [rootId],
        description: `Proyecto ACV de ECONODE Studio: ${projectName}`
      })
    });

    // 2. Crear subcarpetas estándar para orden y auditoría
    const subEvidence = await driveFetch("https://www.googleapis.com/drive/v3/files", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "01_Evidencias_y_Facturas",
        mimeType: "application/vnd.google-apps.folder",
        parents: [projectFolder.id],
        description: "Bóveda documental: Recibos CFE, facturas de materias primas y certificados de proveedores"
      })
    });

    const subReports = await driveFetch("https://www.googleapis.com/drive/v3/files", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "02_Reportes_y_Auditorias",
        mimeType: "application/vnd.google-apps.folder",
        parents: [projectFolder.id],
        description: "Expedientes de conformidad NOM-070/ISO-14040, reportes EPD y dictámenes de auditoría"
      })
    });

    return {
      folderId: projectFolder.id,
      folderName: folderDisplayName,
      folderUrl: `https://drive.google.com/drive/folders/${projectFolder.id}`,
      evidencesFolderId: subEvidence.id,
      reportsFolderId: subReports.id
    };
  }

  /**
   * Obtiene o crea la subcarpeta '01_Evidencias_y_Facturas' para un proyecto en Google Drive.
   */
  async function getOrCreateEvidencesFolder(projectName, projectCode) {
    const proj = await createProjectFolder(projectName, projectCode);
    if (proj.evidencesFolderId) return proj.evidencesFolderId;

    try {
      const q = `'${proj.folderId}' in parents and name = '01_Evidencias_y_Facturas' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`;
      const searchUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name)`;
      const listRes = await driveFetch(searchUrl);
      if (listRes.files && listRes.files.length > 0) {
        return listRes.files[0].id;
      }
    } catch (e) {
      console.warn("Búsqueda de subcarpeta evidencias:", e);
    }

    const subEvidence = await driveFetch("https://www.googleapis.com/drive/v3/files", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "01_Evidencias_y_Facturas",
        mimeType: "application/vnd.google-apps.folder",
        parents: [proj.folderId],
        description: "Bóveda documental: Recibos CFE, facturas de materias primas y certificados de proveedores"
      })
    });
    return subEvidence.id;
  }

  /**
   * Guarda o actualiza el archivo 'model.econode' (JSON) dentro de la carpeta del proyecto.
   */
  async function saveProjectModel(folderId, projectData) {
    if (!folderId) throw new Error("Se requiere el ID de la carpeta de Google Drive del proyecto.");

    const token = await getAccessToken();
    const fileName = "model.econode";
    const fileContent = JSON.stringify(projectData, null, 2);

    // Buscar si ya existe el archivo en la carpeta
    const q = `'${folderId}' in parents and name = '${fileName}' and trashed = false`;
    const searchUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name,version)`;
    const listRes = await driveFetch(searchUrl);

    if (listRes.files && listRes.files.length > 0) {
      // Actualizar archivo existente (uploadType=media)
      const existingId = listRes.files[0].id;
      const updateUrl = `https://www.googleapis.com/upload/drive/v3/files/${existingId}?uploadType=media`;
      const updateResp = await fetch(updateUrl, {
        method: "PATCH",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: fileContent
      });
      if (!updateResp.ok) throw new Error("Error al actualizar model.econode en Google Drive");
      return await updateResp.json();
    } else {
      // Crear archivo mediante multipart upload
      const metadata = {
        name: fileName,
        mimeType: "application/json",
        parents: [folderId],
        description: "Modelo oficial de Sistema Producto de ECONODE Studio"
      };

      const boundary = "-------314159265358979323846";
      const delimiter = "\r\n--" + boundary + "\r\n";
      const closeDelim = "\r\n--" + boundary + "--";

      const multipartRequestBody =
        delimiter +
        "Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        JSON.stringify(metadata) +
        delimiter +
        "Content-Type: application/json\r\n\r\n" +
        fileContent +
        closeDelim;

      const createResp = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": `multipart/related; boundary=${boundary}`
        },
        body: multipartRequestBody
      });
      if (!createResp.ok) throw new Error("Error al crear model.econode en Google Drive");
      return await createResp.json();
    }
  }

  /**
   * Lee y parsea el archivo 'model.econode' desde la carpeta del proyecto en Google Drive.
   */
  async function loadProjectModel(folderId) {
    const q = `'${folderId}' in parents and name = 'model.econode' and trashed = false`;
    const searchUrl = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name)`;
    const listRes = await driveFetch(searchUrl);

    if (!listRes.files || listRes.files.length === 0) {
      return null;
    }

    const fileId = listRes.files[0].id;
    const downloadUrl = `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`;
    const token = await getAccessToken();

    const resp = await fetch(downloadUrl, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!resp.ok) throw new Error("Error al descargar model.econode desde Google Drive");
    return await resp.json();
  }

  /**
   * Comparte la carpeta del proyecto con un Auditor o Cliente usando Google Drive Permissions API.
   * 
   * @param {string} folderId - ID de la carpeta en Drive
   * @param {string} emailAddress - Correo Google Workspace del destinatario
   * @param {string} role - 'commenter' (Auditor), 'reader' (Cliente), 'writer' (Analista)
   * @param {boolean} sendEmail - Enviar correo automático de notificación de Google Drive
   */
  async function shareProjectFolder(folderId, emailAddress, role = "commenter", sendEmail = true) {
    if (!folderId || !emailAddress) {
      throw new Error("Se requiere folderId y emailAddress para compartir la carpeta en Google Drive.");
    }

    // Mapear rol a roles nativos de Google Drive API:
    // 'commenter': Puede ver y dejar comentarios (ideal para Auditor)
    // 'reader': Solo lectura (ideal para Cliente Productor)
    // 'writer': Puede editar (ideal para Analista Colaborador)
    const validRoles = ["reader", "commenter", "writer"];
    const driveRole = validRoles.includes(role) ? role : "commenter";

    const permUrl = `https://www.googleapis.com/drive/v3/files/${folderId}/permissions?sendNotificationEmail=${sendEmail}`;
    return await driveFetch(permUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: driveRole,
        type: "user",
        emailAddress: emailAddress
      })
    });
  }

  /**
   * Sube un archivo de evidencia (factura, PDF, certificado) directamente a Google Drive.
   */
  async function uploadEvidenceFile(folderId, file) {
    if (!folderId || !file) throw new Error("Parámetros insuficientes para subir evidencia a Drive.");
    const token = await getAccessToken();

    const metadata = {
      name: file.name,
      mimeType: file.type || "application/octet-stream",
      parents: [folderId]
    };

    const boundary = "-------314159265358979323846";
    const d = "\r\n--" + boundary + "\r\n";
    const cd = "\r\n--" + boundary + "--";

    const metaHeader = d + "Content-Type: application/json; charset=UTF-8\r\n\r\n" + JSON.stringify(metadata);
    const fileHeader = d + "Content-Type: " + (file.type || "application/octet-stream") + "\r\n\r\n";

    const multipartRequestBody = new Blob([
      metaHeader,
      fileHeader,
      file,
      cd
    ], { type: "multipart/related; boundary=" + boundary });

    const res = await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink,size", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token
      },
      body: multipartRequestBody
    });

    if (!res.ok) {
      let errText = "Error al subir archivo a Google Drive (" + res.status + ")";
      try {
        const errJson = await res.json();
        errText = errJson?.error?.message || errText;
      } catch (e) {}
      throw new Error(errText);
    }
    return await res.json();
  }

  async function listProjects() {
    try {
      const rootId = await getOrCreateRootFolder();
      const q = `'${rootId}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false`;
      const url = `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id,name,createdTime,modifiedTime,webViewLink)&orderBy=modifiedTime desc`;
      const res = await driveFetch(url);
      return res.files || [];
    } catch (e) {
      console.warn("No se pudieron listar proyectos de Google Drive:", e);
      return [];
    }
  }

  // Exportar API global
  window.EconodeDrive = {
    hasToken,
    getAccessToken,
    getOrCreateRootFolder,
    createProjectFolder,
    getOrCreateEvidencesFolder,
    saveProjectModel,
    loadProjectModel,
    shareProjectFolder,
    uploadEvidenceFile,
    listProjects
  };

})();

