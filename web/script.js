let allPrograms = {};
let selectedProgram = null;
let currentLang = 'tr'; // Default

// Setup language handling
function getI18n(key) {
    if (typeof translations !== 'undefined' && translations[currentLang] && translations[currentLang][key]) {
        return translations[currentLang][key];
    }
    return key;
}

function setLanguage(lang) {
    if (typeof translations === 'undefined' || !translations[lang]) return;
    currentLang = lang;
    
    // Update standard text elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang][key]) {
            el.placeholder = translations[lang][key];
        }
    });

    // Update titles
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (translations[lang][key]) {
            el.title = translations[lang][key];
        }
    });

    // Ensure select is synced
    const langSelect = document.getElementById('langSelect');
    if (langSelect && langSelect.value !== lang) {
        langSelect.value = lang;
    }

    // Re-render dynamic content
    if (Object.keys(allPrograms).length > 0) {
        renderTable();
    }
    const servicesPage = document.getElementById('page-services');
    if (servicesPage && !servicesPage.classList.contains('hidden')) {
        loadServices();
    }
}

async function changeLanguageHandler() {
    const langSelect = document.getElementById('langSelect');
    if (langSelect) {
        setLanguage(langSelect.value);
        // Language change is immediate, but we can also save it when Save button is pressed
    }
}

function changeTheme() {
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        if (themeSelect.value === 'light') {
            document.documentElement.classList.remove('dark');
        } else {
            document.documentElement.classList.add('dark');
        }
    }
}

async function saveSettings() {
    const langSelect = document.getElementById('langSelect');
    const themeSelect = document.getElementById('themeSelect');
    
    if (window.pywebview && window.pywebview.api) {
        const settings = await window.pywebview.api.get_settings();
        if (langSelect) settings.lang = langSelect.value;
        if (themeSelect) settings.theme = themeSelect.value;
        
        const res = await window.pywebview.api.save_settings(settings);
        if (res.success) {
            await customAlert(getI18n("msg_saved_title"), getI18n("msg_saved_desc"));
        } else {
            await customAlert(getI18n("msg_error_title"), getI18n("msg_error_desc") + res.error);
        }
    }
}

// Initialize when pywebview is ready
window.addEventListener('pywebviewready', async function() {
    if (window.pywebview && window.pywebview.api) {
        const settings = await window.pywebview.api.get_settings();
        if (settings && settings.lang) {
            setLanguage(settings.lang);
            const langSelect = document.getElementById('langSelect');
            if(langSelect) langSelect.value = settings.lang;
        } else {
            setLanguage('tr');
        }
        
        if (settings && settings.theme) {
            const themeSelect = document.getElementById('themeSelect');
            if (themeSelect) themeSelect.value = settings.theme;
            if (settings.theme === 'light') {
                document.documentElement.classList.remove('dark');
            } else {
                document.documentElement.classList.add('dark');
            }
        }
    }
    refreshData();
    setTimeout(checkForUpdates, 1500); // Check for updates shortly after load
});

// Close modal when clicking on the overlay background
document.getElementById('modal-overlay').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Close dialog when clicking on overlay background
document.getElementById('dialog-overlay').addEventListener('click', function(e) {
    if (e.target === this) {
        closeDialog();
    }
});

// If testing in browser without pywebview
if (window.pywebview === undefined) {
    console.log("pywebview not detected. Running in mock mode.");
    // Mock data
    allPrograms = {
        "Discord": { path: "\"C:\\Users\\Admin\\AppData\\Local\\Discord\\app.exe\"", status: "Etkin", location: "HKCU\\Run", impact: "Orta", is_disabled_by_taskmanager: false },
        "Spotify": { path: "C:\\Users\\Admin\\AppData\\Roaming\\Spotify\\Spotify.exe", status: "Devre Dışı", location: "HKCU\\Run", impact: "Orta", is_disabled_by_taskmanager: false }
    };
    setLanguage('tr');
    renderTable();
}

async function refreshData() {
    if (window.pywebview && window.pywebview.api) {
        try {
            allPrograms = await window.pywebview.api.get_programs();
            renderTable();
        } catch (error) {
            console.error("Error fetching programs:", error);
        }
    }
}

async function globalRefresh() {
    const icon = document.getElementById('global-refresh-icon');
    if (icon) icon.classList.add('animate-spin');
    
    // figure out which page is active
    const activePage = document.querySelector('.page-content:not(.hidden)');
    if (activePage) {
        if (activePage.id === 'page-dashboard') {
            await refreshData();
        } else if (activePage.id === 'page-services') {
            await loadServices();
        } else if (activePage.id === 'page-logs') {
            await loadLogs();
        } else if (activePage.id === 'page-registry') {
            await loadRegistry();
        }
    } else {
        await refreshData();
    }
    
    setTimeout(() => {
        if (icon) icon.classList.remove('animate-spin');
    }, 500); // 500ms delay to ensure the user sees the spin
}

function renderTable() {
    const tbody = document.getElementById('programs-table-body');
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    tbody.innerHTML = '';
    
    let total = 0;
    let active = 0;
    let disabled = 0;
    
    const entries = Object.entries(allPrograms);
    total = entries.length;

    for (const [name, info] of entries) {
        if (info.status === 'Etkin') active++;
        else disabled++;

        if (searchInput && !name.toLowerCase().includes(searchInput) && !info.path.toLowerCase().includes(searchInput)) {
            continue;
        }
        
        if (statusFilter === 'active' && info.status !== 'Etkin') {
            continue;
        }
        if (statusFilter === 'disabled' && info.status === 'Etkin') {
            continue;
        }

        const tr = document.createElement('tr');
        tr.className = "border-b border-borderSubtle table-row-hover transition-colors cursor-pointer";
        tr.onclick = () => openModal(name, info);
        
        let iconSvg = `<svg class="w-5 h-5 text-accentBlue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>`;
        
        let statusBadge = '';
        if (info.status === 'Etkin') {
            statusBadge = `<span class="bg-statusActive/10 text-statusActive px-2 py-0.5 rounded-full flex items-center gap-1.5 w-max"><span class="w-1.5 h-1.5 rounded-full bg-statusActive"></span>${getI18n('status_active')}</span>`;
        } else if (info.status === 'Devre Dışı' || info.status === 'Task Manager Devre Dışı') {
            statusBadge = `<span class="bg-statusDisabled/10 text-statusDisabled px-2 py-0.5 rounded-full flex items-center gap-1.5 w-max"><span class="w-1.5 h-1.5 rounded-full bg-statusDisabled"></span>${getI18n('status_disabled')}</span>`;
        } else {
            statusBadge = `<span class="bg-gray-500/10 text-gray-400 px-2 py-0.5 rounded-full flex items-center gap-1.5 w-max"><span class="w-1.5 h-1.5 rounded-full bg-gray-400"></span>${getI18n('status_unknown')}</span>`;
        }

        tr.innerHTML = `
            <td class="py-3 px-4 flex items-center gap-3">
                <div class="w-8 h-8 bg-accentBlue/10 rounded flex items-center justify-center">
                    ${iconSvg}
                </div>
                <span class="font-medium text-textMain">${name}</span>
            </td>
            <td class="py-3 px-4 text-textMuted font-mono text-xs truncate max-w-xs">${info.path}</td>
            <td class="py-3 px-4">${statusBadge}</td>
            <td class="py-3 px-4 text-textMuted text-xs font-mono">${info.location}</td>
        `;
        tbody.appendChild(tr);
    }

    document.getElementById('stat-total').innerText = total;
    document.getElementById('stat-active').innerText = active;
    document.getElementById('stat-disabled').innerText = disabled;
    
    // Update footer
    const footerTxt = document.getElementById('footer-loaded-text');
    if(footerTxt) footerTxt.innerText = `${total} programs loaded`;
}

document.getElementById('searchInput').addEventListener('input', renderTable);
document.getElementById('statusFilter').addEventListener('change', renderTable);

async function openModal(name, info) {
    selectedProgram = { name, ...info };
    
    document.getElementById('modal-title').innerText = name;
    document.getElementById('modal-prog-name').innerText = name;
    document.getElementById('modal-prog-path').innerText = info.path;
    
    const warningPill = document.getElementById('modal-warning-pill');
    if (info.status === 'Task Manager Devre Dışı' || info.is_disabled_by_taskmanager) {
        warningPill.classList.remove('hidden');
        document.getElementById('modal-prog-status').innerText = 'Task Manager Devre Dışı';
        document.getElementById('modal-prog-status').className = 'font-bold text-statusDisabled';
    } else {
        warningPill.classList.add('hidden');
        document.getElementById('modal-prog-status').innerText = info.status === 'Etkin' ? getI18n('status_active') : getI18n('status_disabled');
        document.getElementById('modal-prog-status').className = 'font-bold ' + (info.status === 'Etkin' ? 'text-statusActive' : 'text-statusDisabled');
    }
    
    document.getElementById('modal-prog-location').innerText = info.location;
    
    let impactHtml = '';
    if (info.impact === 'Düşük') {
        impactHtml = `
            <div class="flex gap-1">
                <div class="w-3 h-1.5 bg-statusActive rounded-full"></div>
                <div class="w-3 h-1.5 bg-borderSubtle rounded-full"></div>
                <div class="w-3 h-1.5 bg-borderSubtle rounded-full"></div>
            </div>
            <span class="text-statusActive font-bold text-sm">${getI18n('impact_low')}</span>
        `;
    } else if (info.impact === 'Orta') {
        impactHtml = `
            <div class="flex gap-1">
                <div class="w-3 h-1.5 bg-statusDisabled rounded-full"></div>
                <div class="w-3 h-1.5 bg-statusDisabled rounded-full"></div>
                <div class="w-3 h-1.5 bg-borderSubtle rounded-full"></div>
            </div>
            <span class="text-statusDisabled font-bold text-sm">${getI18n('impact_medium')}</span>
        `;
    } else if (info.impact === 'Yüksek') {
        impactHtml = `
            <div class="flex gap-1">
                <div class="w-3 h-1.5 bg-statusDanger rounded-full"></div>
                <div class="w-3 h-1.5 bg-statusDanger rounded-full"></div>
                <div class="w-3 h-1.5 bg-statusDanger rounded-full"></div>
            </div>
            <span class="text-statusDanger font-bold text-sm">${getI18n('impact_high')}</span>
        `;
    } else {
        impactHtml = `<span class="text-textMuted font-bold text-sm">${getI18n('impact_unknown')}</span>`;
    }
    document.getElementById('modal-prog-impact').innerHTML = impactHtml;

    document.getElementById('modal-file-info').innerHTML = `> Yükleniyor...\n`;
    if (window.pywebview && window.pywebview.api) {
        const fileDetails = await window.pywebview.api.get_file_info(info.path);
        document.getElementById('modal-file-info').innerHTML = fileDetails.replace(/\n/g, '<br>');
    } else {
        document.getElementById('modal-file-info').innerHTML = `> Dosya Yolu:<br>${info.path}<br><br>> Mock Mode: Details not available.`;
    }

    const btnEnable = document.getElementById('btn-enable');
    if (info.status === 'Etkin') {
        btnEnable.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> <span>${getI18n('action_disable')}</span>`;
        btnEnable.className = "flex items-center gap-2 px-4 py-2 bg-statusDisabled text-white rounded text-sm font-bold hover:bg-yellow-600 transition-colors";
        btnEnable.onclick = disableProgram;
    } else {
        btnEnable.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> <span>${getI18n('action_enable')}</span>`;
        btnEnable.className = "flex items-center gap-2 px-4 py-2 bg-statusActive text-white rounded text-sm font-bold hover:bg-emerald-600 transition-colors";
        btnEnable.onclick = enableProgram;
    }

    const overlay = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    overlay.classList.remove('hidden');
    setTimeout(() => {
        overlay.classList.remove('opacity-0');
        content.classList.remove('scale-95');
    }, 10);
}

function closeModal() {
    const overlay = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    overlay.classList.add('opacity-0');
    content.classList.add('scale-95');
    setTimeout(() => {
        overlay.classList.add('hidden');
        selectedProgram = null;
    }, 300);
}

async function enableProgram() {
    if (!selectedProgram) return;
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.enable_program(selectedProgram.name);
        if(res.success) {
            closeModal();
            refreshData();
            await customAlert(selectedProgram.name + " " + getI18n('msg_enabled_success', "başarıyla etkinleştirildi!"), getI18n('msg_success_title', "Başarılı"));
        } else {
            await customAlert(res.error, 'dlg_title_error', true);
        }
    }
}

async function disableProgram() {
    if (!selectedProgram) return;
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.disable_program(selectedProgram.name);
        if(res.success) {
            closeModal();
            refreshData();
            await customAlert(selectedProgram.name + " " + getI18n('msg_disabled_success', "başarıyla devre dışı bırakıldı!"), getI18n('msg_success_title', "Başarılı"));
        } else {
            await customAlert(res.error, 'dlg_title_error', true);
        }
    }
}

async function uninstallProgram() {
    if (!selectedProgram) return;
    const confirmMsg = getI18n('msg_delete_confirm').replace('{0}', selectedProgram.name);
    if (await customConfirm(confirmMsg, 'dlg_title_warning')) {
        if (window.pywebview && window.pywebview.api) {
            const res = await window.pywebview.api.delete_program(selectedProgram.name);
            if(res.success) {
                closeModal();
                refreshData();
                await customAlert(selectedProgram.name + " " + getI18n('msg_deleted_success', "başarıyla kaldırıldı!"), getI18n('msg_success_title', "Başarılı"));
            } else {
                await customAlert(res.error, 'dlg_title_error', true);
            }
        }
    }
}

async function openFolder() {
    if (!selectedProgram) return;
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.open_location(selectedProgram.path);
    }
}

async function searchInternet() {
    if (!selectedProgram) return;
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.search_internet(selectedProgram.name);
    }
}

// SPA Routing
function switchPage(pageId) {
    document.querySelectorAll('.page-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.sidebar-link').forEach(el => {
        el.classList.remove('bg-bgCard', 'text-textMain', 'border-accentBlue');
        el.classList.add('text-textMuted', 'border-transparent');
        const icon = el.querySelector('.nav-icon');
        if (icon) icon.classList.remove('text-accentBlue');
    });

    const targetPage = document.getElementById(`page-${pageId}`);
    if (targetPage) targetPage.classList.remove('hidden');
    
    const activeLink = document.getElementById(`nav-${pageId}`);
    if(activeLink) {
        activeLink.classList.remove('text-textMuted', 'border-transparent');
        activeLink.classList.add('bg-bgCard', 'text-textMain', 'border-accentBlue');
        const icon = activeLink.querySelector('.nav-icon');
        if (icon) icon.classList.add('text-accentBlue');
    }

    if (pageId === 'services') loadServices();
    if (pageId === 'logs') loadLogs();
    if (pageId === 'registry') loadRegistry();
}

async function loadServices() {
    const tbody = document.getElementById('services-table-body');
    tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-textMuted">Yükleniyor...</td></tr>`;
    
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.get_services();
        if (res.success) {
            tbody.innerHTML = '';
            for (const svc of res.services) {
                const tr = document.createElement('tr');
                tr.className = "border-b border-borderSubtle table-row-hover transition-colors";
                
                let statusBadge = svc.status === 'running' 
                    ? `<span class="text-statusActive font-bold">${getI18n('srv_running')}</span>` 
                    : `<span class="text-statusDisabled font-bold">${getI18n('srv_stopped')}</span>`;
                
                let actionBtn = svc.status === 'running'
                    ? `<button onclick="stopService('${svc.name}')" class="px-3 py-1 bg-statusDisabled/20 text-statusDisabled border border-statusDisabled/50 rounded hover:bg-statusDisabled hover:text-white transition-colors text-xs font-bold">${getI18n('action_stop')}</button>`
                    : `<button onclick="startService('${svc.name}')" class="px-3 py-1 bg-statusActive/20 text-statusActive border border-statusActive/50 rounded hover:bg-statusActive hover:text-white transition-colors text-xs font-bold">${getI18n('action_start')}</button>`;

                tr.innerHTML = `
                    <td class="py-3 px-4 font-medium text-textMain">${svc.name}</td>
                    <td class="py-3 px-4 text-textMuted text-xs truncate max-w-[200px]" title="${svc.display_name}">${svc.display_name}</td>
                    <td class="py-3 px-4">${statusBadge}</td>
                    <td class="py-3 px-4 text-textMuted text-xs uppercase">${svc.start_type}</td>
                    <td class="py-3 px-4 text-right">${actionBtn}</td>
                `;
                tbody.appendChild(tr);
            }
        }
    }
}

async function loadRegistry() {
    const tbody = document.getElementById('registry-table-body');
    if(!tbody) return;
    
    tbody.innerHTML = `<tr><td colspan="4" class="p-8 text-center text-textMuted"><svg class="w-8 h-8 mx-auto mb-2 opacity-50 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>Yükleniyor...</td></tr>`;
    
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_registry_keys) {
        try {
            const res = await window.pywebview.api.get_registry_keys();
            if (res.success) {
                tbody.innerHTML = '';
                if (res.keys.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-textMuted">Kayıt bulunamadı.</td></tr>`;
                    return;
                }
                
                for (const key of res.keys) {
                    const tr = document.createElement('tr');
                    tr.className = "border-b border-borderSubtle table-row-hover transition-colors";
                    
                    tr.innerHTML = `
                        <td class="py-3 px-4 text-textMuted font-mono text-xs truncate max-w-[200px]" title="${key.location}">${key.location}</td>
                        <td class="py-3 px-4 font-medium text-textMain break-all">${key.name}</td>
                        <td class="py-3 px-4 text-accentBlue text-xs font-mono">${key.type}</td>
                        <td class="py-3 px-4 text-textMuted font-mono text-xs break-all max-w-[300px]">${key.data}</td>
                    `;
                    tbody.appendChild(tr);
                }
            } else {
                tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-statusDanger">Hata: ${res.error}</td></tr>`;
            }
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-statusDanger">Bir hata oluştu.</td></tr>`;
        }
    }
}

async function startService(name) {
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.start_service(name);
        if(res.success) {
            loadServices();
        } else {
            await customAlert(getI18n('msg_error_admin').replace('{0}', res.error), 'dlg_title_error', true);
        }
    }
}

async function stopService(name) {
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.stop_service(name);
        if(res.success) {
            loadServices();
        } else {
            await customAlert(getI18n('msg_error_admin').replace('{0}', res.error), 'dlg_title_error', true);
        }
    }
}

async function loadLogs() {
    const container = document.getElementById('logs-container');
    container.innerHTML = '> Yükleniyor...\n';
    if (window.pywebview && window.pywebview.api) {
        const logs = await window.pywebview.api.get_logs();
        container.innerText = logs;
        container.scrollTop = container.scrollHeight;
    }
}

async function clearLogs() {
    if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.clear_logs();
        loadLogs();
    }
}

async function saveSettings() {
    if (window.pywebview && window.pywebview.api) {
        const langSelect = document.getElementById('langSelect');
        const settings = await window.pywebview.api.get_settings();
        if(langSelect) settings.lang = langSelect.value;
        await window.pywebview.api.save_settings(settings);
        await customAlert(getI18n('msg_save_success'), 'dlg_title_success');
    }
}

async function importData() {
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.import_data();
        if (res.success) {
            await customAlert(getI18n('msg_import_success'), 'dlg_title_success');
            refreshData();
        } else if (res.error && res.error !== "İptal edildi") {
            await customAlert(res.error, 'dlg_title_error', true);
        }
    }
}

async function exportData() {
    if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.export_data();
        if (res.success) {
            await customAlert(getI18n('msg_export_success').replace('{0}', res.path), 'dlg_title_success');
        } else if (res.error && res.error !== "İptal edildi") {
            await customAlert(res.error, 'dlg_title_error', true);
        }
    }
}

// --- Custom Dialog System ---
function customAlert(message, titleKey = 'dlg_title_warning', isError = false) {
    return new Promise(resolve => {
        const overlay = document.getElementById('dialog-overlay');
        const content = document.getElementById('dialog-content');
        
        document.getElementById('dialog-title').innerText = getI18n(titleKey);
        if (isError) {
            document.getElementById('dialog-title').className = "font-bold text-lg text-statusDanger leading-tight";
        } else {
            document.getElementById('dialog-title').className = "font-bold text-lg text-textMain leading-tight";
        }
        
        document.getElementById('dialog-message').innerText = message;
        
        const btnContainer = document.getElementById('dialog-buttons');
        btnContainer.innerHTML = `<button id="dlg-btn-ok" class="bg-accentBlue text-white px-4 py-2 rounded text-sm font-medium hover:bg-accentBlueHover transition-colors">${getI18n('dlg_btn_ok')}</button>`;
        
        document.getElementById('dlg-btn-ok').onclick = () => {
            closeDialog();
            resolve(true);
        };
        
        overlay.classList.remove('hidden');
        setTimeout(() => {
            overlay.classList.remove('opacity-0');
            content.classList.remove('scale-95');
        }, 10);
    });
}

function customConfirm(message, titleKey = 'dlg_title_warning') {
    return new Promise(resolve => {
        const overlay = document.getElementById('dialog-overlay');
        const content = document.getElementById('dialog-content');
        
        document.getElementById('dialog-title').innerText = getI18n(titleKey);
        document.getElementById('dialog-title').className = "font-bold text-lg text-textMain leading-tight";
        
        document.getElementById('dialog-message').innerText = message;
        
        const btnContainer = document.getElementById('dialog-buttons');
        btnContainer.innerHTML = `
            <button id="dlg-btn-cancel" class="px-4 py-2 border border-borderSubtle text-textMuted hover:text-textMain hover:bg-bgCard rounded text-sm font-medium transition-colors">${getI18n('dlg_btn_cancel')}</button>
            <button id="dlg-btn-ok" class="bg-statusDanger text-white px-4 py-2 rounded text-sm font-medium hover:bg-red-600 transition-colors">${getI18n('dlg_btn_ok')}</button>
        `;
        
        document.getElementById('dlg-btn-cancel').onclick = () => {
            closeDialog();
            resolve(false);
        };
        document.getElementById('dlg-btn-ok').onclick = () => {
            closeDialog();
            resolve(true);
        };
        
        overlay.classList.remove('hidden');
        setTimeout(() => {
            overlay.classList.remove('opacity-0');
            content.classList.remove('scale-95');
        }, 10);
    });
}

function closeDialog() {
    const overlay = document.getElementById('dialog-overlay');
    const content = document.getElementById('dialog-content');
    overlay.classList.add('opacity-0');
    content.classList.add('scale-95');
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

// Update Checker Logic
let updateUrl = "";

async function checkForUpdates() {
    if (window.pywebview && window.pywebview.api) {
        try {
            const res = await window.pywebview.api.check_for_updates();
            if (res.success && res.update_available) {
                updateUrl = res.release_url;
                const banner = document.getElementById('update-banner');
                const desc = document.getElementById('update-desc');
                
                const descText = getI18n('update_desc').replace('{0}', res.latest_version);
                desc.innerText = descText;
                
                banner.classList.remove('hidden');
                setTimeout(() => {
                    banner.classList.remove('translate-y-20', 'opacity-0');
                }, 100);
            }
        } catch (e) {
            console.error("Update check failed", e);
        }
    }
}

function downloadUpdate() {
    if (updateUrl && window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_url(updateUrl);
    }
    dismissUpdate();
}

function dismissUpdate() {
    const banner = document.getElementById('update-banner');
    if (banner) {
        banner.classList.add('translate-y-20', 'opacity-0');
        setTimeout(() => {
            banner.classList.add('hidden');
        }, 500);
    }
}
