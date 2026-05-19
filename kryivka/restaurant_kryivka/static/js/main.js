/* ── Helpers ────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

function toast(msg, err = false) {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'show' + (err ? ' err' : '');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.className = '', 3200);
}

async function api(method, url, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

const typeBadge = t => ({
  vip:     '<span class="badge badge-gold">VIP</span>',
  loyal:   '<span class="badge badge-blue">Постійний</span>',
  regular: '<span class="badge badge-muted">Звичайний</span>',
})[t] || '';

const statusBadge = s => ({
  pending:     '<span class="badge badge-orange">Прийнято</span>',
  in_progress: '<span class="badge badge-blue">Готується</span>',
  ready:       '<span class="badge badge-green">Готово</span>',
  completed:   '<span class="badge badge-muted">Закрито</span>',
})[s] || '';

const statusLabel = s => ({
  free:     'Вільний',
  reserved: 'Заброньований',
  occupied: 'Зайнятий',
})[s] || s;

const clientLabel = t => ({
  vip:     'VIP (−15%)',
  loyal:   'Постійний (−10%)',
  regular: 'Звичайний',
})[t] || t;

// Меню зі сторінки
const MENU_DATA = [];
document.querySelectorAll('#menu-data span').forEach(el => {
  MENU_DATA.push({
    id: parseInt(el.dataset.id),
    name: el.dataset.name,
    price: parseFloat(el.dataset.price),
    cat: el.dataset.cat,
  });
});

/* ── Navigation ─────────────────────────────────────────────── */
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('page-' + btn.dataset.tab).classList.add('active');
    const tab = btn.dataset.tab;
    if (tab === 'halls')    loadHalls();
    if (tab === 'queue')    loadQueue();
    if (tab === 'orders')   loadMyOrders();
    if (tab === 'receipts') loadReceipts();
  });
});

/* ── Logout ─────────────────────────────────────────────────── */
async function doLogout() {
  await api('POST', '/api/logout');
  window.location.href = '/login';
}

/* ══ ЗАЛИ ═══════════════════════════════════════════════════ */
async function loadHalls() {
  const halls = await api('GET', '/api/halls');
  const me    = await api('GET', '/api/me');
  const wrap  = $('halls-wrap');

  wrap.innerHTML = halls.map(h => {
    const tableHtml = h.tables.map(t => {
      const waiterLine = t.waiter_name
        ? '<div class="tt-waiter">👤 ' + t.waiter_name + '</div>'
        : '';
      const clientLine = t.client_name
        ? '<div class="tt-client">' + t.client_name + '</div>'
        : '';
      return '<div class="table-tile ' + t.status + '" onclick="openTableModal(' + t.table_id + ')">' +
        '<div class="tt-num">' + t.table_id + '</div>' +
        '<div class="tt-seats">' + t.seats + ' місць</div>' +
        waiterLine + clientLine +
        '<div class="tt-status">' + statusLabel(t.status) + '</div>' +
        '</div>';
    }).join('');

    const free    = h.tables.filter(t => t.status === 'free').length;
    const occ     = h.tables.filter(t => t.status === 'occupied').length;
    const res     = h.tables.filter(t => t.status === 'reserved').length;
    const summary = free + ' вільних' + (res ? ', ' + res + ' заброньованих' : '') + (occ ? ', ' + occ + ' зайнятих' : '');

    return '<div class="hall-section">' +
      '<div class="hall-title">' + h.name + ' <span>' + summary + '</span></div>' +
      '<div class="tables-grid">' + tableHtml + '</div>' +
      '</div>';
  }).join('');
}

/* ── Модальне вікно столика ─────────────────────────────────── */
let _currentTableId = null;
let _currentOrderId = null;
let _activeMenuCat  = null;

async function openTableModal(table_id) {
  _currentTableId = table_id;
  _currentOrderId = null;
  _activeMenuCat  = null;
  const data = await api('GET', '/api/table/' + table_id);
  const me   = await api('GET', '/api/me');
  renderTableModal(data, me);
  $('modal-table').classList.add('open');
}

function renderTableModal(t, me) {
  const o = t.order;
  if (o) _currentOrderId = o.order_id;

  // Статусні кроки
  const steps = ['pending','in_progress','ready','completed'];
  const stepLabels = ['Прийнято','Готується','Готово','Закрито'];
  const curIdx = o ? steps.indexOf(o.status) : -1;
  const statusBar = '<div class="status-bar">' +
    steps.map((s, i) => {
      const cls = i < curIdx ? ' done' : i === curIdx ? ' active' : '';
      return '<div class="status-step' + cls + '">' + stepLabels[i] + '</div>';
    }).join('') + '</div>';

  // Позиції замовлення
  let itemsHtml = '<div style="color:var(--muted);font-size:13px;padding:8px 0">Ще нічого не замовлено</div>';
  if (o && o.items.length) {
    itemsHtml = o.items.map(i =>
      '<div class="order-item-line">' +
      '<span class="oil-name">' + i.name + '</span>' +
      '<span class="oil-qty">× ' + i.qty + '</span>' +
      '<span class="oil-sub">' + i.subtotal.toFixed(2) + ' грн</span>' +
      '</div>'
    ).join('');
  }

  // Підсумок
  let summaryHtml = '';
  if (o && o.items.length) {
    const disc = o.discount > 0
      ? '<div style="color:var(--green);font-size:13px;display:flex;justify-content:space-between;padding:3px 0"><span>Знижка (' + clientLabel(o.client_type) + ')</span><span>−' + o.discount.toFixed(2) + ' грн</span></div>'
      : '';
    summaryHtml = '<div style="border-top:1px solid var(--border);margin-top:10px;padding-top:10px">' +
      disc +
      '<div style="display:flex;justify-content:space-between;font-family:Playfair Display,serif;font-size:22px;color:var(--gold2);padding-top:6px">' +
      '<span>РАЗОМ</span><span>' + o.total.toFixed(2) + ' грн</span></div></div>';
  }

  // Кнопки дій
  let actionsHtml = '';
  const isMyTable = !t.waiter_id || t.waiter_id === me.waiter_id;

  if (t.status === 'free') {
    actionsHtml = '<button class="btn btn-primary" style="width:100%" onclick="quickBookThisTable(' + t.table_id + ')">+ Забронювати цей столик</button>';
  } else if (t.status === 'reserved' && isMyTable) {
    actionsHtml = '<button class="btn btn-green" onclick="seatThisTable(' + t.reservation_id + ')">✓ Розмістити гостей</button>';
  } else if (t.status === 'occupied' && isMyTable) {
    const nextBtn = o && o.status !== 'completed'
      ? '<button class="btn btn-primary" onclick="advanceThisOrder()">→ Наступний статус</button>'
      : '';
    const closeBtn = '<button class="btn btn-red" onclick="closeThisTable(' + t.reservation_id + ')">Закрити стіл</button>';
    const printBtn = '<button class="btn btn-ghost" onclick="printReceiptFor(' + t.table_id + ')">🖨 Чек</button>';
    actionsHtml = '<div style="display:flex;gap:8px;flex-wrap:wrap">' + nextBtn + closeBtn + printBtn + '</div>';
  }

  // Панель додавання страв (тільки для зайнятих столиків офіціанта)
  let addItemHtml = '';
  if (t.status === 'occupied' && isMyTable) {
    const cats = [...new Set(MENU_DATA.map(m => m.cat))];
    const catPills = cats.map(c =>
      '<button class="cat-pill" onclick="filterMenuCat(\'' + c + '\')">' + c + '</button>'
    ).join('');
    const menuItems = MENU_DATA.map(m =>
      '<button class="menu-item-btn" data-cat="' + m.cat + '" onclick="addMenuItemToOrder(' + m.id + ')">' +
      '<span class="mib-name">' + m.name + '</span>' +
      '<span class="mib-price">' + m.price + ' грн</span>' +
      '</button>'
    ).join('');
    addItemHtml = '<div class="add-item-panel" style="margin-top:16px">' +
      '<div style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px">Додати страву</div>' +
      '<div class="menu-cats" id="menu-cats">' + catPills + '</div>' +
      '<div class="menu-items-row" id="menu-items-row">' + menuItems + '</div>' +
      '</div>';
  }

  const waiterInfo = t.waiter_name
    ? '<div style="font-size:13px;color:var(--gold)">👤 ' + t.waiter_name + (t.waiter_level === 'senior' ? ' ⭐' : '') + '</div>'
    : '';
  const noteInfo = t.note
    ? '<div style="font-size:12px;color:var(--muted);margin-top:2px">📝 ' + t.note + '</div>'
    : '';

  $('modal-table-content').innerHTML =
    '<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px">' +
      '<div>' +
        '<div style="font-family:Playfair Display,serif;font-size:28px;color:var(--gold2)">Столик #' + t.table_id + '</div>' +
        '<div style="font-size:12px;color:var(--muted)">' + t.hall_name + ' &nbsp;&middot;&nbsp; ' + t.seats + ' місць</div>' +
      '</div>' +
      statusBadge(t.status === 'free' ? 'free' : (o ? o.status : 'pending')) +
    '</div>' +
    (t.client_name ? (
      '<div style="background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:16px">' +
        '<div style="display:flex;justify-content:space-between;align-items:flex-start">' +
          '<div>' +
            '<div style="font-size:15px;font-weight:500">' + t.client_name + ' ' + (o ? typeBadge(o.client_type) : '') + '</div>' +
            '<div style="font-size:12px;color:var(--muted);margin-top:2px">' + t.guests + ' гостей</div>' +
            noteInfo +
          '</div>' + waiterInfo +
        '</div>' +
      '</div>'
    ) : '') +
    (o ? statusBar : '') +
    '<div style="margin-bottom:4px">' + itemsHtml + '</div>' +
    summaryHtml +
    addItemHtml +
    '<div style="margin-top:16px">' + actionsHtml + '</div>';
}

function filterMenuCat(cat) {
  _activeMenuCat = cat;
  document.querySelectorAll('.cat-pill').forEach(p => {
    p.classList.toggle('active', p.textContent === cat);
  });
  document.querySelectorAll('.menu-item-btn').forEach(b => {
    b.style.display = (b.dataset.cat === cat) ? '' : 'none';
  });
}

async function addMenuItemToOrder(item_id) {
  if (!_currentOrderId) { toast('Немає активного замовлення для цього столика', true); return; }
  const data = await api('POST', '/api/order/' + _currentOrderId + '/item', { item_id, qty: 1 });
  if (data.error) { toast(data.error, true); return; }
  toast('Страву додано');
  const t = await api('GET', '/api/table/' + _currentTableId);
  const me = await api('GET', '/api/me');
  renderTableModal(t, me);
  if (_activeMenuCat) filterMenuCat(_activeMenuCat);
}

async function advanceThisOrder() {
  if (!_currentOrderId) return;
  const data = await api('PATCH', '/api/order/' + _currentOrderId + '/status');
  if (data.error) { toast(data.error, true); return; }
  toast('Статус оновлено: ' + data.status);
  const t = await api('GET', '/api/table/' + _currentTableId);
  const me = await api('GET', '/api/me');
  renderTableModal(t, me);
  loadHalls();
}

async function seatThisTable(reservation_id) {
  const data = await api('POST', '/api/reservation/' + reservation_id + '/seat');
  if (data.error) { toast(data.error, true); return; }
  toast('Гостей розміщено!');
  const t = await api('GET', '/api/table/' + _currentTableId);
  const me = await api('GET', '/api/me');
  renderTableModal(t, me);
  loadHalls();
}

async function closeThisTable(reservation_id) {
  if (!confirm('Закрити стіл і звільнити столик?')) return;
  const data = await api('POST', '/api/reservation/' + reservation_id + '/close');
  if (data.error) { toast(data.error, true); return; }
  toast('Стіл закрито, столик вільний');
  closeModal('modal-table');
  loadHalls();
}

function quickBookThisTable(table_id) {
  closeModal('modal-table');
  $('bk-table').value = table_id;
  openBookingModal();
}

function closeModal(id) {
  $(id).classList.remove('open');
}

/* ══ ЧЕРГА ══════════════════════════════════════════════════ */
async function loadQueue() {
  const [items, me] = await Promise.all([
    api('GET', '/api/queue'),
    api('GET', '/api/me'),
  ]);
  const list = $('queue-list');
  if (!items.length) {
    list.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg><p>Черга порожня</p></div>';
    return;
  }
  list.innerHTML = '<div class="queue-grid">' +
    items.map((c, i) => {
      const halls = document.querySelectorAll('#bk-table optgroup');
      let optHtml = '';
      halls.forEach(og => {
        optHtml += '<optgroup label="' + og.label + '">';
        og.querySelectorAll('option').forEach(o => {
          optHtml += '<option value="' + o.value + '">' + o.textContent + '</option>';
        });
        optHtml += '</optgroup>';
      });
      return '<div class="queue-card">' +
        '<div class="qc-top">' +
          '<div class="qc-pos">' + (i + 1) + '</div>' +
          '<div>' +
            '<div class="qc-name">' + c.name + ' ' + typeBadge(c.type) + '</div>' +
            '<div class="qc-meta">Пріоритет: ' + c.priority + ' &nbsp;&middot;&nbsp; Очікує: ' + c.wait_min + ' хв</div>' +
          '</div>' +
        '</div>' +
        '<div class="qc-actions">' +
          '<button class="qc-serve-btn" onclick="serveAndBook(' + c.id + ', \'' + c.name + '\', \'' + c.type + '\')">Обслужити → призначити стіл</button>' +
        '</div>' +
      '</div>';
    }).join('') +
  '</div>';
}

async function serveAndBook(client_id, client_name, client_type) {
  // Викликати клієнта і одразу відкрити бронювання
  const data = await api('POST', '/api/serve/' + client_id);
  if (data.error) { toast(data.error, true); return; }
  toast('Клієнта обрано: ' + data.client_name);
  // Відкриваємо форму бронювання з ім'ям клієнта вже заповненим
  $('bk-client').value = data.client_name;
  openBookingModal();
  loadQueue();
}

/* ══ БРОНЮВАННЯ ═════════════════════════════════════════════ */
function openBookingModal() {
  $('modal-booking').classList.add('open');
}

async function submitBooking() {
  const client_name = $('bk-client').value.trim();
  const table_id    = parseInt($('bk-table').value);
  const guests      = parseInt($('bk-guests').value) || 2;
  const note        = $('bk-note').value.trim();
  if (!client_name) { toast("Введіть ім'я клієнта", true); return; }
  const data = await api('POST', '/api/reservation', { client_name, table_id, guests, note });
  if (data.error) { toast(data.error, true); return; }
  toast('Заброньовано: ' + data.client + ' → столик #' + data.table_id);
  $('bk-client').value = ''; $('bk-note').value = '';
  closeModal('modal-booking');
  loadHalls();
}

/* ══ ДОДАТИ КЛІЄНТА ═════════════════════════════════════════ */
function openAddClientModal() {
  $('modal-addclient').classList.add('open');
}

async function submitAddClient() {
  const name = $('ac-name').value.trim();
  const type = $('ac-type').value;
  if (!name) { toast("Введіть ім'я клієнта", true); return; }
  const data = await api('POST', '/api/client', { name, type });
  if (data.error) { toast(data.error, true); return; }
  toast(data.name + ' у черзі (#' + data.queue_size + ')');
  $('ac-name').value = '';
  closeModal('modal-addclient');
  loadQueue();
}

/* ══ МОЇ ЗАМОВЛЕННЯ ═════════════════════════════════════════ */
async function loadMyOrders() {
  const [orders, me, halls] = await Promise.all([
    api('GET', '/api/orders'),
    api('GET', '/api/me'),
    api('GET', '/api/halls'),
  ]);
  // Знайти столики офіціанта
  const myTableIds = new Set();
  halls.forEach(h => h.tables.forEach(t => {
    if (t.waiter_id === me.waiter_id) myTableIds.add(t.client_name);
  }));

  const myOrders = orders.filter(o => myTableIds.has(o.client));
  const list     = $('orders-list');

  if (!myOrders.length) {
    list.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg><p>У вас немає активних замовлень</p></div>';
    return;
  }

  // Завантажити деталі кожного замовлення
  const hallsFull = await api('GET', '/api/halls');
  const tableMap  = {};
  hallsFull.forEach(h => h.tables.forEach(t => {
    if (t.client_name) tableMap[t.client_name] = t;
  }));

  list.innerHTML = '<div class="orders-grid">' +
    myOrders.map(o => {
      const tInfo = tableMap[o.client];
      const tableLabel = tInfo ? 'Столик #' + tInfo.table_id + ' · ' + tInfo.hall_name : '';
      return '<div class="order-card">' +
        '<div class="order-card-head">' +
          '<div>' +
            '<div class="oc-title">Замовлення #' + o.order_id + '</div>' +
            '<div class="oc-client">' + o.client + ' ' + typeBadge(o.client_type) + (tableLabel ? ' &nbsp;·&nbsp; ' + tableLabel : '') + '</div>' +
          '</div>' +
          statusBadge(o.status) +
        '</div>' +
        '<div class="order-card-body" id="order-body-' + o.order_id + '">' +
          '<div style="color:var(--muted);font-size:13px">Завантаження…</div>' +
        '</div>' +
        '<div class="order-card-foot">' +
          '<div class="oc-total">' + o.total.toFixed(2) + ' грн</div>' +
          '<div class="oc-actions">' +
            (o.status !== 'completed' ? '<button class="btn btn-primary btn-sm" onclick="advanceOrder(' + o.order_id + ')">→ Статус</button>' : '') +
            (tInfo ? '<button class="btn btn-ghost btn-sm" onclick="openTableModal(' + tInfo.table_id + ')">Деталі</button>' : '') +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('') +
  '</div>';

  // Завантажити деталі позицій
  for (const o of myOrders) {
    const detail = await api('GET', '/api/table/' + (tableMap[o.client] ? tableMap[o.client].table_id : 0));
    if (detail && detail.order && detail.order.items) {
      const body = $('order-body-' + o.order_id);
      if (body) {
        body.innerHTML = detail.order.items.length
          ? detail.order.items.map(i =>
              '<div class="order-item-line">' +
              '<span class="oil-name">' + i.name + '</span>' +
              '<span class="oil-qty">× ' + i.qty + '</span>' +
              '<span class="oil-sub">' + i.subtotal.toFixed(2) + ' грн</span>' +
              '</div>'
            ).join('')
          : '<div style="color:var(--muted);font-size:13px">Позиції відсутні</div>';
      }
    }
  }
}

async function advanceOrder(oid) {
  const data = await api('PATCH', '/api/order/' + oid + '/status');
  if (data.error) { toast(data.error, true); return; }
  toast('Статус оновлено');
  loadMyOrders();
}

/* ══ ЧЕКИ ═══════════════════════════════════════════════════ */
async function loadReceipts() {
  const [halls, me] = await Promise.all([
    api('GET', '/api/halls'),
    api('GET', '/api/me'),
  ]);
  const myTables = [];
  halls.forEach(h => h.tables.forEach(t => {
    if (t.waiter_id === me.waiter_id && t.client_name) {
      myTables.push(Object.assign({}, t, { hall_name: h.name }));
    }
  }));

  const wrap = $('receipts-wrap');
  if (!myTables.length) {
    wrap.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><p>У вас немає активних столиків</p></div>';
    return;
  }

  wrap.innerHTML = '<div class="receipts-grid">' +
    myTables.map(t => {
      const o = t.order;
      const itemsHtml = o && o.items.length
        ? o.items.map(i =>
            '<div class="rc-line">' +
            '<span class="rcl-name">' + i.name + '</span>' +
            '<span class="rcl-qty">× ' + i.qty + '</span>' +
            '<span class="rcl-price">' + i.price.toFixed(2) + '</span>' +
            '<span class="rcl-sub">' + i.subtotal.toFixed(2) + ' грн</span>' +
            '</div>'
          ).join('')
        : '<div style="color:var(--muted);font-size:13px;padding:8px 0">Замовлення порожнє</div>';

      const summaryHtml = o && o.items.length
        ? '<div class="rc-summary">' +
            '<div class="rcs-line"><span>Без знижки</span><span>' + o.subtotal.toFixed(2) + ' грн</span></div>' +
            (o.discount > 0 ? '<div class="rcs-line" style="color:var(--green)"><span>Знижка (' + clientLabel(o.client_type) + ')</span><span>−' + o.discount.toFixed(2) + ' грн</span></div>' : '') +
            '<div class="rcs-total"><span>РАЗОМ</span><span>' + o.total.toFixed(2) + ' грн</span></div>' +
          '</div>'
        : '';

      return '<div class="receipt-card" id="receipt-' + t.table_id + '">' +
        '<div class="rc-head">' +
          '<div>' +
            '<div class="rc-table-num">Столик #' + t.table_id + '</div>' +
            '<div class="rc-hall">' + t.hall_name + ' &middot; ' + t.seats + ' місць</div>' +
          '</div>' +
          '<div style="text-align:right">' +
            '<div class="rc-waiter">👤 ' + t.waiter_name + '</div>' +
            '<div class="rc-client">' + t.client_name + ' &middot; ' + t.guests + ' гостей</div>' +
            (t.note ? '<div class="rc-note">📝 ' + t.note + '</div>' : '') +
            '<div style="margin-top:4px">' + (o ? statusBadge(o.status) : '') + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="rc-body">' +
          '<div class="rc-items-label">Позиції замовлення</div>' +
          itemsHtml +
        '</div>' +
        summaryHtml +
        '<div class="rc-foot">' +
          '<button class="btn btn-primary btn-sm" onclick="printReceiptFor(' + t.table_id + ')">🖨 Роздрукувати чек</button>' +
          '<button class="btn btn-ghost btn-sm" onclick="openTableModal(' + t.table_id + ')">Відкрити стіл</button>' +
        '</div>' +
      '</div>';
    }).join('') +
  '</div>';
}

async function printReceiptFor(table_id) {
  const data = await api('GET', '/api/receipt/' + table_id);
  if (data.error) { toast(data.error, true); return; }
  const discLine = data.discount > 0
    ? '<tr><td colspan="3" style="color:green">Знижка (' + clientLabel(data.client_type) + ')</td><td style="color:green;text-align:right">−' + data.discount.toFixed(2) + ' грн</td></tr>'
    : '';
  const rows = data.items.map(i =>
    '<tr><td>' + i.name + '</td><td style="text-align:center">' + i.qty + '</td><td style="text-align:right">' + i.price.toFixed(2) + '</td><td style="text-align:right">' + i.subtotal.toFixed(2) + '</td></tr>'
  ).join('');
  const noteRow = data.note ? '<tr><td><b>Примітка:</b></td><td colspan="3">' + data.note + '</td></tr>' : '';
  const win = window.open('', '_blank', 'width=440,height=720');
  win.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"/><title>Чек #' + data.receipt_num + '</title>' +
    '<style>body{font-family:"Courier New",monospace;font-size:13px;padding:28px;max-width:380px;margin:0 auto;color:#111}' +
    'h2{text-align:center;font-size:20px;margin-bottom:4px;font-family:Georgia,serif}' +
    '.sub{text-align:center;color:#666;margin-bottom:16px;font-size:12px}' +
    'hr{border:none;border-top:1px dashed #bbb;margin:12px 0}' +
    'table{width:100%;border-collapse:collapse}th{text-align:left;font-size:11px;color:#888;padding-bottom:6px}' +
    'td{padding:4px 0;vertical-align:top}td:last-child{text-align:right;white-space:nowrap}' +
    '.total-row td{font-weight:bold;font-size:16px;padding-top:10px;border-top:1px dashed #bbb}' +
    '.footer{text-align:center;color:#888;font-size:11px;margin-top:20px}' +
    '@media print{.no-print{display:none}}</style></head><body>' +
    '<h2>✦ Kryivka</h2>' +
    '<div class="sub">Чек № ' + data.receipt_num + ' &nbsp;&middot;&nbsp; ' + data.created_at + '</div>' +
    '<hr/>' +
    '<table>' +
    '<tr><td><b>Столик:</b></td><td colspan="3">#' + data.table_id + ' — ' + data.hall + '</td></tr>' +
    '<tr><td><b>Клієнт:</b></td><td colspan="3">' + data.client + ' (' + clientLabel(data.client_type) + ')</td></tr>' +
    '<tr><td><b>Гостей:</b></td><td colspan="3">' + data.guests + '</td></tr>' +
    '<tr><td><b>Офіціант:</b></td><td colspan="3">' + data.waiter + '</td></tr>' +
    noteRow + '</table><hr/>' +
    '<table><thead><tr><th>Страва</th><th style="text-align:center">К-сть</th><th style="text-align:right">Ціна</th><th style="text-align:right">Сума</th></tr></thead>' +
    '<tbody>' + rows + '</tbody>' +
    '<tfoot>' +
    '<tr><td colspan="3" style="padding-top:8px;color:#666">Сума:</td><td style="text-align:right;padding-top:8px">' + data.subtotal.toFixed(2) + ' грн</td></tr>' +
    discLine +
    '<tr class="total-row"><td colspan="3">ДО СПЛАТИ:</td><td>' + data.total.toFixed(2) + ' грн</td></tr>' +
    '</tfoot></table><hr/>' +
    '<div class="footer">Дякуємо за відвідування!<br/>Kryivka &copy; 2025</div><br/>' +
    '<div style="text-align:center" class="no-print"><button onclick="window.print()" style="padding:10px 28px;cursor:pointer;font-size:14px;font-family:Georgia,serif">🖨 Друк</button></div>' +
    '</body></html>');
  win.document.close();
}

/* ── Init ───────────────────────────────────────────────────── */
loadHalls();
