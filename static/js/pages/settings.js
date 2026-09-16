/* =============================================================================
   js/pages/settings.js — Web Admin Store, Receipt & Theme Settings
   =============================================================================
   SPA contract: default export { mount, destroy }.
   ========================================================================== */
'use strict';

import { api } from '../core/api.js';
import modal from '../core/modal.js';
import { notify } from '../core/toast.js';

let rootEl = null;
let destroyFns = [];

const SETTINGS_TAB_KEY = 'nexgen_webpos_settings_tab';

/* Tab Navigation */
function initTabNavigation(el) {
  const tabButtons = el.querySelectorAll('.settings-tab-btn');
  const panes = el.querySelectorAll('.settings-pane');

  const switchTab = (tabName) => {
    tabButtons.forEach((btn) => {
      const isTarget = btn.dataset.tabTarget === tabName;
      btn.classList.toggle('active', isTarget);
      btn.style.background = isTarget ? 'var(--bg-surface-elevated, #2563eb)' : 'transparent';
      btn.style.color = isTarget ? '#fff' : 'var(--text-muted)';
      btn.style.borderColor = isTarget ? 'transparent' : 'var(--border-color)';
    });

    panes.forEach((pane) => {
      pane.classList.toggle('active', pane.id === `pane-${tabName}`);
    });

    try {
      localStorage.setItem(SETTINGS_TAB_KEY, tabName);
    } catch (e) {}
  };

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tabTarget);
    });
  });

  const savedTab = localStorage.getItem(SETTINGS_TAB_KEY) || 'store';
  switchTab(savedTab);
}

/* Interactive Chip Toggling */
function initChips(container) {
  if (!container) return;
  const chips = container.querySelectorAll('.settings-chip');
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
    });
  });
}

function getChipValues(container) {
  if (!container) return [];
  const activeChips = container.querySelectorAll('.settings-chip.active');
  return Array.from(activeChips).map((c) => c.dataset.value);
}

function setChipValues(container, values) {
  if (!container || !Array.isArray(values)) return;
  const chips = container.querySelectorAll('.settings-chip');
  chips.forEach((chip) => {
    if (values.includes(chip.dataset.value)) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

/* Theme Selection */
function initThemeCards(el) {
  const lightCard = el.querySelector('#themeCardLight');
  const darkCard = el.querySelector('#themeCardDark');

  const getThemeMode = () => {
    if (window.POS && window.POS.theme) return window.POS.theme.get();
    return document.documentElement.getAttribute('data-theme') || 'dark';
  };

  const setThemeMode = (mode) => {
    if (window.POS && window.POS.theme) {
      window.POS.theme.set(mode);
    } else {
      document.documentElement.setAttribute('data-theme', mode);
      localStorage.setItem('pos_theme', mode);
    }
  };

  const updateActiveThemeUI = () => {
    const currentTheme = getThemeMode() || 'dark';
    if (lightCard) {
      lightCard.classList.toggle('active', currentTheme === 'light');
    }
    if (darkCard) {
      darkCard.classList.toggle('active', currentTheme === 'dark');
    }
  };

  updateActiveThemeUI();

  if (lightCard) {
    lightCard.addEventListener('click', () => {
      setThemeMode('light');
      updateActiveThemeUI();
      notify.info('Theme set to Light mode.');
    });
  }

  if (darkCard) {
    darkCard.addEventListener('click', () => {
      setThemeMode('dark');
      updateActiveThemeUI();
      notify.info('Theme set to Dark mode.');
    });
  }
}

/* Live Receipt Paper Preview Sync */
function initReceiptPreview(el) {
  const prevStoreName = el.querySelector('#prevStoreName');
  const prevTin = el.querySelector('#prevTin');
  const prevPtu = el.querySelector('#prevPtu');
  const prevPtuIssued = el.querySelector('#prevPtuIssued');
  const prevBranch = el.querySelector('#prevBranchName');
  const prevAddr = el.querySelector('#prevAddress');
  const prevMin = el.querySelector('#prevMin');
  const prevSerial = el.querySelector('#prevSerial');
  const prevFooterMsg = el.querySelector('#prevFooterMsg');

  const sync = () => {
    const nameVal = (el.querySelector('#cfgReceiptStoreName') || {}).value || '';
    const tinVal = (el.querySelector('#cfgTin') || {}).value || '';
    const ptuVal = (el.querySelector('#cfgPtu') || {}).value || '';
    const ptuIssuedVal = (el.querySelector('#cfgPtuIssued') || {}).value || '';
    const branchVal = (el.querySelector('#cfgBranchName') || {}).value || '';
    const addrVal = (el.querySelector('#cfgStoreAddress') || {}).value || '';
    const minVal = (el.querySelector('#cfgMin') || {}).value || '';
    const serialVal = (el.querySelector('#cfgSerial') || {}).value || '';
    const footerVal = (el.querySelector('#cfgFooterLines') || {}).value || '';

    if (prevStoreName) prevStoreName.textContent = nameVal || 'STORE NAME';
    if (prevTin) prevTin.textContent = tinVal ? (tinVal.startsWith('TIN') || tinVal.startsWith('VAT') ? tinVal : `VAT REG. TIN: ${tinVal}`) : 'VAT REG. TIN: ---';
    if (prevPtu) prevPtu.textContent = ptuVal ? (ptuVal.startsWith('PTU') ? ptuVal : `PTU NO: ${ptuVal}`) : 'PTU NO: ---';
    if (prevPtuIssued) prevPtuIssued.textContent = ptuIssuedVal ? (ptuIssuedVal.startsWith('DATE') ? ptuIssuedVal : `DATE ISSUED: ${ptuIssuedVal}`) : 'DATE ISSUED: ---';
    if (prevBranch) prevBranch.textContent = branchVal || '';
    if (prevAddr) prevAddr.textContent = addrVal || '';
    if (prevMin) prevMin.textContent = minVal ? (minVal.startsWith('MIN') ? minVal : `MIN: ${minVal}`) : 'MIN: ---';
    if (prevSerial) prevSerial.textContent = serialVal ? (serialVal.startsWith('SN') ? serialVal : `SN: ${serialVal}`) : 'SN: ---';
    if (prevFooterMsg) prevFooterMsg.textContent = footerVal.split('\n')[0] || 'Thank you for dining with us!';
  };

  const inputs = el.querySelectorAll('#receiptSettingsForm input, #receiptSettingsForm textarea');
  inputs.forEach((inp) => inp.addEventListener('input', sync));
  sync();
  return sync;
}

/* Load Settings Data */
async function loadAllSettings(el, syncPreview) {
  try {
    const data = await api.get('/receipt_settings');
    if (data && data.success) {
      const s = data.settings || {};
      const setVal = (id, val) => {
        const inp = el.querySelector(id);
        if (inp && val !== undefined && val !== null) inp.value = val;
      };

      // Store settings
      setVal('#ssBusinessType', s.business_type || '');
      setVal('#ssOpenTime', s.open_time || '');
      setVal('#ssCloseTime', s.close_time || '');
      setChipValues(el.querySelector('#ssBusinessDays'), s.business_days || []);
      setChipValues(el.querySelector('#ssServiceTypes'), s.service_types || []);
      setChipValues(el.querySelector('#ssPaymentTypes'), s.payment_types || []);

      // Receipt settings
      setVal('#cfgReceiptStoreName', s.store_name || '');
      setVal('#cfgTin', s.tin || '');
      setVal('#cfgPtu', s.ptu_no || '');
      setVal('#cfgPtuIssued', s.ptu_date_issued || '');
      setVal('#cfgBranchName', s.branch_name || '');
      setVal('#cfgStoreAddress', s.store_location || '');
      setVal('#cfgMin', s.min || '');
      setVal('#cfgSerial', s.serial_number || '');

      let footerText = s.thank_you_message || '';
      if (Array.isArray(s.footer_lines) && s.footer_lines.length > 0) {
        footerText = s.footer_lines.join('\n');
      }
      setVal('#cfgFooterLines', footerText);

      if (syncPreview) syncPreview();
    }
  } catch (err) {
    console.warn('Could not load settings from server:', err);
  }
}

export async function mount(container) {
  rootEl = container || document.getElementById('appMain') || document.body;
  destroyFns = [];

  initTabNavigation(rootEl);
  initChips(rootEl.querySelector('#ssBusinessDays'));
  initChips(rootEl.querySelector('#ssServiceTypes'));
  initChips(rootEl.querySelector('#ssPaymentTypes'));
  initThemeCards(rootEl);
  const syncPreview = initReceiptPreview(rootEl);

  await loadAllSettings(rootEl, syncPreview);

  // Store Settings Form Save
  const storeForm = rootEl.querySelector('#storeSettingsForm');
  if (storeForm) {
    storeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = rootEl.querySelector('#btnSaveStoreSettings');
      btn.disabled = true;
      const orig = btn.innerHTML;
      btn.textContent = 'Saving...';

      const payload = {
        business_type: (rootEl.querySelector('#ssBusinessType') || {}).value || '',
        open_time: (rootEl.querySelector('#ssOpenTime') || {}).value || '',
        close_time: (rootEl.querySelector('#ssCloseTime') || {}).value || '',
        business_days: getChipValues(rootEl.querySelector('#ssBusinessDays')),
        service_types: getChipValues(rootEl.querySelector('#ssServiceTypes')),
        payment_types: getChipValues(rootEl.querySelector('#ssPaymentTypes')),
      };

      try {
        const res = await api.post('/receipt_settings', payload);
        if (res && res.success) {
          notify.success('Store settings saved successfully.');
        } else {
          notify.error((res && res.message) || 'Error saving store settings.');
        }
      } catch (err) {
        notify.error('Network error saving store settings.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    });
  }

  // Receipt Settings Form Save
  const receiptForm = rootEl.querySelector('#receiptSettingsForm');
  if (receiptForm) {
    receiptForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = rootEl.querySelector('#btnSaveReceiptSettings');
      btn.disabled = true;
      const orig = btn.innerHTML;
      btn.textContent = 'Saving...';

      const footerVal = (rootEl.querySelector('#cfgFooterLines') || {}).value || '';
      const payload = {
        store_name: (rootEl.querySelector('#cfgReceiptStoreName') || {}).value || '',
        tin: (rootEl.querySelector('#cfgTin') || {}).value || '',
        ptu_no: (rootEl.querySelector('#cfgPtu') || {}).value || '',
        ptu_date_issued: (rootEl.querySelector('#cfgPtuIssued') || {}).value || '',
        branch_name: (rootEl.querySelector('#cfgBranchName') || {}).value || '',
        store_location: (rootEl.querySelector('#cfgStoreAddress') || {}).value || '',
        min: (rootEl.querySelector('#cfgMin') || {}).value || '',
        serial_number: (rootEl.querySelector('#cfgSerial') || {}).value || '',
        thank_you_message: footerVal,
        footer_lines: footerVal.split('\n').map((l) => l.trim()).filter(Boolean),
      };

      try {
        const res = await api.post('/receipt_settings', payload);
        if (res && res.success) {
          notify.success('Receipt & Header settings saved.');
          if (syncPreview) syncPreview();
        } else {
          notify.error((res && res.message) || 'Error saving receipt settings.');
        }
      } catch (err) {
        notify.error('Network error saving receipt settings.');
      } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    });
  }
}

export function destroy() {
  destroyFns.forEach((fn) => {
    try { fn(); } catch (e) {}
  });
  destroyFns = [];
  rootEl = null;
}

export default { mount, destroy };
