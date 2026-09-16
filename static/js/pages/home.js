/**
 * home.js — NEXGEN Web POS Admin Landing Page Module
 *
 * Provides live clock, system greeting, network status, and real-time
 * overview statistics (sales, orders, items, products, recent activity).
 */

const OVERVIEW_REFRESH_MS = 30000;

const timers = [];
const listeners = [];
const inFlight = [];

function el(id) {
  return document.getElementById(id);
}

function formatMoney(n) {
  const num = Number(n) || 0;
  return `₱${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatItems(n) {
  const num = Number(n) || 0;
  return `${num.toLocaleString('en-US')} items`;
}

/* ---- Clock line ----------------------------------------------------------- */
function updateClock() {
  const timeNode = el('homeClockTime');
  const dateNode = el('homeClockDate');
  if (!timeNode && !dateNode) return;

  const now = new Date();
  if (timeNode) {
    timeNode.textContent = now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }
  if (dateNode) {
    dateNode.textContent = now.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }
}

/* ---- Network status chip -------------------------------------------------- */
function setNetworkStatus() {
  const chip = el('homeNetworkChip');
  const text = el('homeNetworkText');
  if (!chip || !text) return;

  const online = navigator.onLine;
  chip.dataset.status = online ? 'online' : 'offline';
  chip.classList.toggle('status-chip--online', online);
  chip.classList.toggle('status-chip--offline', !online);
  text.textContent = online ? 'Cloud Online' : 'Network Offline';
}

/* ---- Overview metrics & recent orders ------------------------------------- */
function renderRecent(orders) {
  const list = el('homeRecentOrders') || el('homeRecentList');
  if (!list) return;

  list.innerHTML = '';
  if (!orders || orders.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'home-recent-empty';
    empty.textContent = 'No orders recorded yet today.';
    list.appendChild(empty);
    return;
  }

  for (const order of orders) {
    const row = document.createElement('li');
    row.className = 'home-recent-row';

    const orderNo = document.createElement('span');
    orderNo.className = 'home-recent-mono';
    orderNo.textContent = order.order_no ? `#${order.order_no}` : `#${order.id || ''}`;

    const customer = document.createElement('span');
    customer.className = 'home-recent-customer';
    customer.textContent = order.customer_name || 'Walk-in Customer';

    const time = document.createElement('span');
    time.className = 'home-recent-mono home-recent-time';
    time.textContent = order.time || '--:--';

    const total = document.createElement('span');
    total.className = 'home-recent-mono home-recent-total';
    total.textContent = typeof order.total === 'number' ? formatMoney(order.total) : (order.total || '₱0.00');

    const status = document.createElement('span');
    const statusKey = String(order.status || 'completed').toLowerCase();
    status.className = `home-chip home-chip--${statusKey}`;
    status.textContent = statusKey.toUpperCase();

    row.append(orderNo, customer, time, total, status);
    list.appendChild(row);
  }
}

function fetchOverview() {
  const controller = new AbortController();
  inFlight.push(controller);

  fetch('/home/overview', { cache: 'no-store', signal: controller.signal })
    .then((response) => response.json())
    .then((data) => {
      if (!data || !data.success) return;
      const sales = el('homeStatSales');
      const orders = el('homeStatOrders');
      const items = el('homeStatItems');
      const products = el('homeStatProducts');
      const salesVal = data.sales != null ? data.sales : data.sales_today;
      const ordersVal = data.orders != null ? data.orders : data.orders_today;
      const itemsVal = data.items != null ? data.items : data.items_today;
      const productsVal = data.products != null ? data.products : data.products_count;
      if (sales) sales.textContent = typeof salesVal === 'number' ? formatMoney(salesVal) : (salesVal || '₱0.00');
      if (orders) orders.textContent = String(ordersVal ?? 0);
      if (items) items.textContent = formatItems(itemsVal ?? 0);
      if (products) products.textContent = String(productsVal ?? 0);
      renderRecent(data.recent || data.recent_orders || []);
    })
    .catch((error) => {
      if (controller.signal.aborted || (error && (error.name === 'AbortError' || error.message?.includes('Failed to fetch')))) return;
      console.warn('Overview fetch notice:', error);
    })
    .finally(() => {
      const idx = inFlight.indexOf(controller);
      if (idx !== -1) inFlight.splice(idx, 1);
    });
}

/* ---- Greeting line ------------------------------------------------------- */
function setGreeting() {
  const node = el('homeGreeting');
  if (!node) return;
  const hour = new Date().getHours();
  const part = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  node.textContent = `${part}, ${node.dataset.user || 'Admin'}`;
}

export default {
  mount() {
    setGreeting();
    updateClock();
    timers.push(window.setInterval(updateClock, 1000));

    setNetworkStatus();
    const onNetwork = () => setNetworkStatus();
    window.addEventListener('online', onNetwork);
    window.addEventListener('offline', onNetwork);
    listeners.push(['online', onNetwork], ['offline', onNetwork]);

    fetchOverview();
    timers.push(window.setInterval(fetchOverview, OVERVIEW_REFRESH_MS));
  },

  destroy() {
    timers.forEach((id) => window.clearInterval(id));
    timers.length = 0;
    listeners.forEach(([name, fn]) => window.removeEventListener(name, fn));
    listeners.length = 0;
    inFlight.forEach((controller) => controller.abort());
    inFlight.length = 0;
  },
};
