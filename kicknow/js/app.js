/* KickNow – App-Logik (Vanilla JS, keine Build-Tools nötig) */
(function () {
  'use strict';

  /* ---------- Unconditional Splash Dismiss & Error Catching ---------- */
  function dismissSplash() {
    const s = document.getElementById('splash');
    if (s && !s.classList.contains('hide')) {
      s.classList.add('hide');
      setTimeout(() => { if (s && s.parentNode) s.remove(); }, 600);
    }
  }
  setTimeout(dismissSplash, 900);
  window.addEventListener('error', () => { setTimeout(dismissSplash, 50); });
  window.addEventListener('unhandledrejection', () => { setTimeout(dismissSplash, 50); });

  const KN = window.KN, ic = window.icon, img = window.pitchImage;
  const { USER, USER_LOCATION, PITCHES, PLAYERS, SLOT_STARTS, SLOT_LEN, LEVELS } = KN;

  /* =====================================================================
     Hilfsfunktionen
     ===================================================================== */
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const rand = a => a[Math.floor(Math.random() * a.length)];
  const chev = ic('chevronRight', 'chev');

  // Demo-Uhr: Außerhalb der Öffnungszeiten wird auf 17:40 Uhr gesetzt, damit die Demo immer "lebt".
  const LOAD_REAL = Date.now();
  const DEMO_BASE = (() => {
    const d = new Date();
    const m = d.getHours() * 60 + d.getMinutes();
    if (m < SLOT_STARTS[0] || m >= 19 * 60) d.setHours(17, 40, 0, 0);
    return d.getTime();
  })();
  const now = () => DEMO_BASE + (Date.now() - LOAD_REAL);
  const nowMin = () => { const d = new Date(now()); return d.getHours() * 60 + d.getMinutes(); };

  const pad = n => String(n).padStart(2, '0');
  const dkOf = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const dkDate = dk => { const [y, m, d] = dk.split('-').map(Number); return new Date(y, m - 1, d); };
  const dkAdd = (dk, n) => { const d = dkDate(dk); d.setDate(d.getDate() + n); return dkOf(d); };
  const TODAY = dkOf(new Date(DEMO_BASE));
  const DAYS = Array.from({ length: 14 }, (_, i) => dkAdd(TODAY, i));
  const WD = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  const MON = ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sep.', 'Okt.', 'Nov.', 'Dez.'];

  const fmtTime = m => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
  const fmtRange = s => `${fmtTime(s.start)} – ${fmtTime(s.end)}`;
  const shortDate = dk => { const d = dkDate(dk); return `${d.getDate()}. ${MON[d.getMonth()]}`; };
  function dayLabel(dk) {
    if (dk === TODAY) return 'Heute';
    if (dk === dkAdd(TODAY, 1)) return 'Morgen';
    const d = dkDate(dk);
    return `${WD[d.getDay()]}, ${shortDate(dk)}`;
  }
  function fmtClock(ts) {
    const d = new Date(ts), dk = dkOf(d), t = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
    if (dk === TODAY) return t;
    if (dk === dkAdd(TODAY, -1)) return `Gestern, ${t}`;
    return `${d.getDate()}.${d.getMonth() + 1}., ${t}`;
  }
  function relDays(ts) {
    const d = Math.floor((now() - ts) / 86400000);
    if (d <= 0) return 'Heute';
    if (d === 1) return 'Gestern';
    if (d < 7) return `vor ${d} Tagen`;
    if (d < 30) { const w = Math.round(d / 7); return `vor ${w} ${w === 1 ? 'Woche' : 'Wochen'}`; }
    const m = Math.round(d / 30); return `vor ${m} ${m === 1 ? 'Monat' : 'Monaten'}`;
  }
  const dec1 = x => x.toFixed(1).replace('.', ',');
  const fmtKm = km => km < 1 ? `${Math.round(km * 100) * 10} m` : `${dec1(km)} km`;
  const freeText = n => n <= 0 ? 'Ausgebucht' : n === 1 ? '1 Platz frei' : `${n} Plätze frei`;

  function distKm(a, b) {
    const R = 6371, toR = x => x * Math.PI / 180;
    const dLat = toR(b.lat - a.lat), dLng = toR(b.lng - a.lng);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(toR(a.lat)) * Math.cos(toR(b.lat)) * Math.sin(dLng / 2) ** 2;
    return Math.round(2 * R * Math.asin(Math.sqrt(h)) * 10) / 10;
  }
  let currentCenter = { lat: USER_LOCATION.lat, lng: USER_LOCATION.lng, label: USER_LOCATION.label };
  function updateDistances(center) {
    PITCHES.forEach(p => { p.dist = distKm(center, p); });
  }
  updateDistances(currentCenter);

  const CUR_IDX = (() => {
    const m = nowMin(), i = SLOT_STARTS.findIndex(s => m < s + SLOT_LEN);
    return i < 0 ? SLOT_STARTS.length - 1 : i;
  })();
  const liveIdx = () => {
    const m = nowMin(), i = SLOT_STARTS.findIndex(s => m < s + SLOT_LEN);
    return i < 0 ? SLOT_STARTS.length : i;
  };

  /* =====================================================================
     Zustand (lokal im Browser gespeichert)
     ===================================================================== */
  const STORE = 'kicknow-demo-v1';
  const DEFAULT_FILTER = { radius: 10, onlyFree: false, surface: 'alle', sort: 'distance' };
  const freshState = () => ({ v: 1, favs: [], bookings: {}, joined: {}, chats: {}, reviews: {}, filter: Object.assign({}, DEFAULT_FILTER) });
  let state = (() => {
    try {
      const s = JSON.parse(localStorage.getItem(STORE));
      if (s && s.v === 1) return Object.assign(freshState(), s);
    } catch (e) { /* ignorieren */ }
    return freshState();
  })();
  const save = () => { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) { /* ignorieren */ } };
  let query = '';

  /* =====================================================================
     Datenmodell
     ===================================================================== */
  const pitchById = id => PITCHES.find(p => p.id === id);
  const playerMap = Object.fromEntries(PLAYERS.map(p => [p.id, p]));
  const person = id => (id === 'me' ? USER : playerMap[id]);

  const baseCache = {};
  const baseDay = (p, dk) => baseCache[p.id + dk] || (baseCache[p.id + dk] = KN.genDay(p, dk, dk === TODAY ? CUR_IDX : -1));
  const isPast = s => s.dk < TODAY || (s.dk === TODAY && s.end <= nowMin());

  function decorate(base) {
    const s = Object.assign({}, base);
    const b = state.bookings[s.id];
    if (b && s.type === 'free') {
      Object.assign(s, {
        type: 'game', mine: true, organizer: 'me', participants: ['me'], extra: b.group - 1,
        maxPlayers: b.open ? b.maxPlayers : b.group, level: b.level, open: b.open, messages: []
      });
    }
    if (s.type === 'game') {
      const j = state.joined[s.id];
      s.participants = s.participants.slice();
      s.extra = s.extra || 0;
      if (j && !s.mine) { s.participants.push('me'); s.extra += j.count - 1; }
      s.joined = !!(j || s.mine);
      s.count = s.participants.length + s.extra;
      s.free = Math.max(0, s.maxPlayers - s.count);
    }
    s.past = isPast(s);
    return s;
  }
  const getDay = (p, dk) => baseDay(p, dk).map(decorate);
  function getSlot(id) {
    const [pid, dk, i] = id.split('_');
    const p = pitchById(pid);
    return { p, g: p ? getDay(p, dk)[+i] : null };
  }
  function messagesOf(g) {
    const base = (g.messages || []).map(m => ({ from: m.from, text: m.text, ts: DEMO_BASE - m.ago * 60000 }));
    return base.concat(state.chats[g.id] || []).sort((a, b) => a.ts - b.ts);
  }

  const STATUS_LABEL = { frei: 'Frei', spiel: 'Spiel geplant', belegt: 'Belegt' };
  function currentSlot(p) { const i = liveIdx(); return i < SLOT_STARTS.length ? getDay(p, TODAY)[i] : null; }
  function statusOf(p) {
    const s = currentSlot(p);
    if (!s) return 'belegt';
    return s.type === 'free' ? 'frei' : s.type === 'game' ? 'spiel' : 'belegt';
  }
  function featuredGame(p) {
    for (const dk of [TODAY, dkAdd(TODAY, 1)]) {
      const g = getDay(p, dk).find(s => s.type === 'game' && !s.past && (s.open !== false || s.mine));
      if (g) return g;
    }
    return null;
  }
  function availability(p) {
    const st = statusOf(p), day = getDay(p, TODAY), i = liveIdx(), cur = day[i];
    if (!cur) return { st, title: 'Geschlossen', sub: 'Öffnungszeiten 08:30 – 22:00 Uhr' };
    if (st === 'frei') {
      let j = i;
      while (j + 1 < day.length && day[j + 1].type === 'free') j++;
      return { st, title: 'Frei jetzt', sub: `Verfügbar von ${fmtTime(cur.start)} – ${fmtTime(day[j].end)} Uhr` };
    }
    if (st === 'spiel') return { st, title: cur.mine ? 'Dein Spiel' : 'Spiel geplant', sub: `Offenes Spiel ${fmtRange(cur)} Uhr · ${freeText(cur.free)}` };
    return { st, title: 'Belegt', sub: `${cur.label} bis ${fmtTime(cur.end)} Uhr` };
  }
  function ratingOf(p) {
    const base = KN.genReviews(p), dist = base.dist.slice(), mine = state.reviews[p.id] || [];
    mine.forEach(r => { dist[r.stars - 1]++; });
    const count = dist.reduce((a, b) => a + b, 0);
    const avg = count ? dist.reduce((a, c, i) => a + c * (i + 1), 0) / count : 0;
    const reviews = mine.map(r => Object.assign({ from: 'me' }, r)).reverse()
      .concat(base.reviews.map(r => Object.assign({ ts: DEMO_BASE - r.agoDays * 86400000 }, r)));
    return { dist, count, avg, reviews };
  }
  const surfaceMatch = (p, s) => s === 'alle' || (s === 'Käfig' ? p.cage : p.surface === s);
  const filterActive = () => { const f = state.filter; return f.radius !== DEFAULT_FILTER.radius || f.onlyFree || f.surface !== 'alle'; };
  function visiblePitches() {
    const f = state.filter, q = query.trim().toLowerCase();
    const list = PITCHES.filter(p => p.dist <= f.radius && surfaceMatch(p, f.surface) &&
      (!f.onlyFree || statusOf(p) === 'frei') &&
      (!q || `${p.name} ${p.district} ${p.surface} ${p.address}`.toLowerCase().includes(q)));
    list.sort(f.sort === 'rating' ? (a, b) => ratingOf(b).avg - ratingOf(a).avg : (a, b) => a.dist - b.dist);
    return list;
  }
  const sortKey = g => g.dk + String(g.start).padStart(4, '0');
  function myGames() {
    const ids = new Set(Object.keys(state.bookings).concat(Object.keys(state.joined)));
    return Array.from(ids).map(getSlot)
      .filter(x => x.g && x.g.type === 'game' && x.g.joined && !x.g.past)
      .sort((a, b) => sortKey(a.g).localeCompare(sortKey(b.g)));
  }

  /* =====================================================================
     UI-Bausteine
     ===================================================================== */
  function avatar(id, size) {
    const u = person(id);
    if (!u) return '';
    const ini = u.name.split(' ').map(x => x[0]).join('').slice(0, 2);
    return `<span class="av ${size || ''}" style="background:${u.color}">${esc(ini)}</span>`;
  }
  function avatarStack(g, max = 3) {
    const ids = g.participants.slice(0, max), rest = g.count - ids.length;
    return `<span class="av-stack">${ids.map(id => avatar(id, 'sm')).join('')}${rest > 0 ? `<span class="av sm more">+${rest}</span>` : ''}</span>`;
  }
  function stars(n) {
    let s = '';
    for (let i = 1; i <= 5; i++) s += `<span class="${i <= Math.round(n) ? 'on' : ''}">${ic('star')}</span>`;
    return `<span class="stars">${s}</span>`;
  }
  const pill = st => `<span class="pill pill--${st}">${STATUS_LABEL[st]}</span>`;
  function ratingInline(p) {
    const r = ratingOf(p);
    return `<span class="rating">${ic('star')}<b>${dec1(r.avg)}</b><span>(${r.count})</span></span>`;
  }
  const sizeText = p => `${p.size[0]} × ${p.size[1]} m`;
  function pitchCard(p) {
    return `<button class="pitch-card" data-act="pitch" data-id="${p.id}">
      <img class="thumb" src="${img(p)}" alt="">
      <span class="pc-main"><span class="pc-name">${esc(p.name)}</span>
        <span class="pc-meta">${p.surface} · ${sizeText(p)}</span>${ratingInline(p)}</span>
      <span class="pc-side">${pill(statusOf(p))}<span class="pc-dist">${fmtKm(p.dist)}</span></span>
    </button>`;
  }
  function gameCard({ p, g }) {
    const side = g.mine ? '<span class="tag tag--dark">Organisator</span>'
      : g.joined ? '<span class="tag tag--mint">Dabei</span>'
        : `<span class="pc-dist">${fmtKm(p.dist)}</span>`;
    return `<button class="game-card" data-act="game" data-id="${g.id}">
      <img class="thumb" src="${img(p)}" alt="">
      <span class="pc-main"><span class="gc-when">${dayLabel(g.dk)} · ${fmtRange(g)} Uhr</span>
        <span class="pc-name">${esc(p.name)}</span>
        <span class="gc-row">${avatarStack(g)}<span class="gc-count">${g.count}/${g.maxPlayers} · ${g.free > 0 ? `${g.free} frei` : 'voll'}</span></span></span>
      <span class="pc-side">${side}${chev}</span>
    </button>`;
  }
  function navbar(title, sub, right) {
    return `<header class="nav">
      <button class="icon-btn" data-act="back" aria-label="Zurück">${ic('chevronLeft')}</button>
      <div class="nav-title"><b>${title}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</div>
      <div class="nav-right">${right || ''}</div>
    </header>`;
  }
  const emptyBox = (icon, title, text, btn) => `<div class="empty">${ic(icon)}<b>${title}</b><p>${text}</p>${btn || ''}</div>`;

  function toast(msg, icon) {
    const t = $('#toast');
    t.innerHTML = `${ic(icon || 'check')}<span>${esc(msg)}</span>`;
    t.classList.add('show');
    clearTimeout(toast.t);
    toast.t = setTimeout(() => t.classList.remove('show'), 2400);
  }

  /* ---------- Bottom-Sheets ---------- */
  function openSheet(html) {
    const layer = $('#sheet-layer');
    layer.innerHTML = `<div class="sheet-backdrop" data-act="close-sheet"></div>
      <div class="sheet" role="dialog"><span class="grabber"></span><div class="sheet-inner">${html}</div></div>`;
    layer.getBoundingClientRect();
    layer.classList.add('open');
    return $('.sheet', layer);
  }
  function closeSheet() {
    const layer = $('#sheet-layer');
    layer.classList.remove('open');
    setTimeout(() => { if (!layer.classList.contains('open')) layer.innerHTML = ''; }, 320);
  }
  function confirmSheet(title, text, okLabel, onOk) {
    const sh = openSheet(`<h2>${title}</h2><p class="muted">${text}</p>
      <div class="btn-row"><button class="btn btn-ghost" data-act="close-sheet">Abbrechen</button>
      <button class="btn btn-danger" id="ok-btn">${okLabel}</button></div>`);
    $('#ok-btn', sh).addEventListener('click', () => { closeSheet(); onOk(); });
  }

  /* =====================================================================
     Tabs
     ===================================================================== */
  const TABS = [['karte', 'Karte', 'pin'], ['liste', 'Liste', 'list'], ['anmelden', 'Anmelden', 'signup'], ['profil', 'Profil', 'user']];
  let activeTab = 'karte';

  function renderTabbar() {
    const n = myGames().length;
    $('#tabbar').innerHTML = TABS.map(([id, label, icn]) =>
      `<button class="tab ${activeTab === id ? 'on' : ''}" data-act="tab" data-tab="${id}">${ic(icn)}<span>${label}</span>${id === 'anmelden' && n ? `<i class="badge">${n}</i>` : ''}</button>`).join('');
  }
  function showTab(id) {
    activeTab = id;
    $$('.tab-screen').forEach(s => s.classList.toggle('active', s.dataset.tab === id));
    renderTabbar();
    if (id === 'karte') {
      if (map) setTimeout(() => (map.resize ? map.resize() : map.invalidateSize()), 0);
      setSheetState(currentSheetState, false);
    }
  }
  function refreshTabs() {
    updateMap();
    renderMapList();
    updateListe();
    renderAnmelden();
    renderProfil();
    renderTabbar();
  }
  function syncQuery(src) {
    $$('#q-map, #q-list').forEach(i => { if (i !== src) i.value = query; });
  }

  /* ---------- Karte & Sheet-Steuerung (GPU-beschleunigt) ---------- */
  let map, userMarker, selectedId = null;
  const markers = {};
  let currentSheetState = 'normal';
  let setSheetState = () => {};

  function initSheetDrag() {
    const sheet = $('#list-sheet');
    const tk = $('#tab-karte');
    if (!sheet || !tk) return;

    let startY = 0;
    let startSheetY = 0;
    let currentSheetY = 0;
    let isDragging = false;
    let canDrag = false;
    let startTime = 0;
    let justDragged = false;
    let rafId = null;
    let activePointerId = null;

    function getSnapPoints() {
      const containerH = tk.clientHeight || window.innerHeight;
      const sheetH = sheet.offsetHeight || (containerH - 64);
      return {
        expanded: 0,
        normal: Math.max(0, Math.round(containerH * 0.52 - 64)),
        collapsed: Math.max(0, sheetH - 106),
        sheetH
      };
    }

    setSheetState = function(target, animate = true) {
      currentSheetState = target;
      tk.classList.remove('collapsed', 'expanded');
      if (target === 'collapsed') tk.classList.add('collapsed');
      else if (target === 'expanded') tk.classList.add('expanded');

      const snaps = getSnapPoints();
      const targetY = snaps[target] != null ? snaps[target] : snaps.normal;
      currentSheetY = targetY;
      const peek = Math.max(0, snaps.sheetH - targetY);

      if (animate) {
        sheet.classList.remove('dragging');
        sheet.style.transition = 'transform 0.35s cubic-bezier(0.25, 1, 0.5, 1)';
        tk.style.setProperty('--sheet-peek', `${Math.round(peek)}px`);
      } else {
        sheet.classList.add('dragging');
        sheet.style.transition = 'none';
        tk.style.setProperty('--sheet-peek', `${Math.round(peek)}px`);
      }
      sheet.style.transform = `translate3d(0, ${Math.round(targetY)}px, 0)`;
    };

    sheet.addEventListener('click', e => {
      if (justDragged) {
        e.stopPropagation();
        e.preventDefault();
        return;
      }
      if (currentSheetState === 'collapsed') {
        e.stopPropagation();
        e.preventDefault();
        setSheetState('normal');
      }
    }, true);

    function onPointerDown(e) {
      if (e.button != null && e.button !== 0) return;

      if (currentSheetState === 'collapsed') {
        canDrag = true;
      } else if (e.target.closest('.grabber-btn, .list-head')) {
        canDrag = true;
      } else {
        const list = $('#map-list');
        canDrag = !!(list && list.scrollTop <= 0);
      }

      if (!canDrag) return;

      startY = e.clientY;
      startSheetY = currentSheetY;
      startTime = Date.now();
      isDragging = false;
      activePointerId = e.pointerId;

      try { sheet.setPointerCapture(e.pointerId); } catch (_) {}
    }

    function onPointerMove(e) {
      if (!canDrag || activePointerId !== e.pointerId) return;
      const dy = e.clientY - startY;
      const snaps = getSnapPoints();

      if (!isDragging) {
        if (currentSheetState === 'collapsed') {
          if (dy < -6) isDragging = true;
        } else if (currentSheetState === 'normal') {
          if (Math.abs(dy) > 7) {
            if (dy < 0 && !e.target.closest('.grabber-btn, .list-head')) {
              canDrag = false;
              try { sheet.releasePointerCapture(e.pointerId); } catch (_) {}
              return;
            }
            isDragging = true;
          }
        } else if (currentSheetState === 'expanded') {
          if (dy > 7) isDragging = true;
        }
      }

      if (isDragging) {
        let targetY = startSheetY + dy;
        if (targetY < snaps.expanded) {
          targetY = snaps.expanded + (targetY - snaps.expanded) * 0.22;
        } else if (targetY > snaps.collapsed) {
          targetY = snaps.collapsed + (targetY - snaps.collapsed) * 0.22;
        }
        currentSheetY = targetY;

        if (!rafId) {
          rafId = requestAnimationFrame(() => {
            sheet.classList.add('dragging');
            sheet.style.transform = `translate3d(0, ${Math.round(currentSheetY)}px, 0)`;
            const peek = Math.max(0, snaps.sheetH - currentSheetY);
            tk.style.setProperty('--sheet-peek', `${Math.round(peek)}px`);
            rafId = null;
          });
        }
      }
    }

    function onPointerUp(e) {
      if (activePointerId !== e.pointerId) return;
      activePointerId = null;
      try { sheet.releasePointerCapture(e.pointerId); } catch (_) {}

      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }

      if (isDragging) {
        justDragged = true;
        setTimeout(() => { justDragged = false; }, 120);

        const dy = e.clientY - startY;
        const dt = Math.max(1, Date.now() - startTime);
        const velocity = dy / dt;
        const snaps = getSnapPoints();

        let nextState = 'normal';
        if (velocity > 0.42) {
          nextState = currentSheetState === 'expanded' ? 'normal' : 'collapsed';
        } else if (velocity < -0.42) {
          nextState = currentSheetState === 'collapsed' ? 'normal' : 'expanded';
        } else {
          const dCollapsed = Math.abs(currentSheetY - snaps.collapsed);
          const dNormal = Math.abs(currentSheetY - snaps.normal);
          const dExpanded = Math.abs(currentSheetY - snaps.expanded);

          if (dCollapsed < dNormal && dCollapsed < dExpanded) {
            nextState = 'collapsed';
          } else if (dExpanded < dNormal) {
            nextState = 'expanded';
          } else {
            nextState = 'normal';
          }
        }
        setSheetState(nextState, true);
      }
      isDragging = false;
      canDrag = false;
    }

    sheet.addEventListener('pointerdown', onPointerDown);
    sheet.addEventListener('pointermove', onPointerMove);
    sheet.addEventListener('pointerup', onPointerUp);
    sheet.addEventListener('pointercancel', onPointerUp);

    window.addEventListener('resize', () => {
      setSheetState(currentSheetState, false);
    });

    setTimeout(() => {
      setSheetState('normal', false);
    }, 0);
  }

  /* ---------- Kreis-Berechnung für GeoJSON (MapLibre) ---------- */
  function makeCirclePolygon(lng, lat, radiusKm, points = 64) {
    const coords = [];
    const distanceX = radiusKm / (111.32 * Math.cos(lat * Math.PI / 180));
    const distanceY = radiusKm / 110.574;
    for (let i = 0; i <= points; i++) {
      const theta = (i / points) * (2 * Math.PI);
      coords.push([lng + distanceX * Math.cos(theta), lat + distanceY * Math.sin(theta)]);
    }
    return {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [coords] }
    };
  }

  function setCenterLocation(loc) {
    currentCenter = { lat: loc.lat, lng: loc.lng, label: loc.name };
    updateDistances(currentCenter);
    const inp = $('#q-map');
    if (inp) {
      inp.value = '';
      inp.placeholder = loc.name;
    }
    query = '';
    syncQuery(null);
    const suggestBox = $('#search-suggest');
    if (suggestBox) suggestBox.classList.remove('show');
    selectPitch(null);
    updateMap();
    renderMapList();
    updateListe();
    if (map) {
      map.flyTo({ center: [loc.lng, loc.lat], zoom: 13.5, duration: 600 });
      setTimeout(() => fitRadius(true), 650);
    }
    toast(`Suche zentriert auf ${loc.name}`, 'pin');
  }

  function buildMapTab() {
    $('#tab-karte').innerHTML = `
      <div class="map-area">
        <div id="map"></div>
        <div class="map-top">
          <div class="search-box">
            <label class="search">${ic('search')}<input type="search" id="q-map" placeholder="${esc(currentCenter.label || 'In meiner Nähe')}" autocomplete="off" enterkeyhint="search"></label>
            <div class="search-suggest" id="search-suggest"></div>
          </div>
          <button class="square-btn" data-act="filters" aria-label="Filter">${ic('sliders')}<i class="dot" id="filter-dot"></i></button>
        </div>

        <button class="map-fab" data-act="recenter" aria-label="Auf meinen Standort zentrieren">${ic('locate')}</button>
        <div class="map-preview" id="map-preview"></div>
      </div>
      <div class="list-sheet" id="list-sheet">
        <button class="grabber-btn" data-act="toggle-sheet" aria-label="Liste vergrößern"><span class="grabber"></span></button>
        <div class="list-head"><h2 id="near-count"></h2><button class="select-chip" data-act="sort" id="sort-chip"></button></div>
        <div class="scroll list" id="map-list"></div>
      </div>`;

    const useMapLibre = typeof maplibregl !== 'undefined' && (typeof maplibregl.supported !== 'function' || maplibregl.supported());

    if (useMapLibre) {
      try {
        const mapStyle = window.KICKNOW_MAP_STYLE || 'https://tiles.openfreemap.org/styles/positron';

        map = new maplibregl.Map({
          container: 'map',
          style: mapStyle,
          center: [currentCenter.lng, currentCenter.lat],
          zoom: 13.5,
          attributionControl: false
        });

        map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

        function setupLayers() {
          if (!map || map.getSource('radius-source')) return;
          map.addSource('radius-source', {
            type: 'geojson',
            data: makeCirclePolygon(currentCenter.lng, currentCenter.lat, state.filter.radius)
          });
          map.addLayer({
            id: 'radius-fill',
            type: 'fill',
            source: 'radius-source',
            paint: {
              'fill-color': '#8BEA9B',
              'fill-opacity': 0.12
            }
          });
          map.addLayer({
            id: 'radius-stroke',
            type: 'line',
            source: 'radius-source',
            paint: {
              'line-color': '#103B2F',
              'line-width': 1.5,
              'line-opacity': 0.45,
              'line-dasharray': [3, 3]
            }
          });

          fitRadius(false);
        }

        if (map.isStyleLoaded()) {
          setupLayers();
        } else {
          map.on('load', setupLayers);
        }

        // Nutzer-Standort-Marker
        const meEl = document.createElement('div');
        meEl.className = 'me-marker';
        meEl.style.width = '24px';
        meEl.style.height = '24px';
        meEl.innerHTML = '<span class="me-pulse"></span><span class="me-dot"></span>';
        userMarker = new maplibregl.Marker({ element: meEl, anchor: 'center' })
          .setLngLat([USER_LOCATION.lng, USER_LOCATION.lat])
          .addTo(map);

        // Platz-Marker
        PITCHES.forEach(p => {
          const el = document.createElement('div');
          el.className = 'pin-wrap';
          el.innerHTML = pinHtml(p, true, false);
          el.addEventListener('click', e => {
            e.stopPropagation();
            selectPitch(p.id);
          });
          markers[p.id] = new maplibregl.Marker({ element: el, anchor: 'bottom' })
            .setLngLat([p.lng, p.lat])
            .addTo(map);
        });

        map.on('click', () => {
          selectPitch(null);
          const sb = $('#search-suggest');
          if (sb) sb.classList.remove('show');
        });
      } catch (err) {
        console.error('MapLibre init error, falling back:', err);
      }
    } else if (typeof L !== 'undefined') {
      // Leaflet fallback
      try {
        map = L.map('map', { zoomControl: false }).setView([USER_LOCATION.lat, USER_LOCATION.lng], 14);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '© OpenStreetMap-Mitwirkende'
        }).addTo(map);

        L.marker([USER_LOCATION.lat, USER_LOCATION.lng], {
          icon: L.divIcon({ className: 'me-marker', html: '<span class="me-pulse"></span><span class="me-dot"></span>', iconSize: [22, 22], iconAnchor: [11, 11] }),
          interactive: false, zIndexOffset: 1000
        }).addTo(map);

        radiusCircle = L.circle([USER_LOCATION.lat, USER_LOCATION.lng], {
          radius: state.filter.radius * 1000, color: '#103B2F', weight: 1.5, opacity: 0.45, dashArray: '4 6',
          fillColor: '#8BEA9B', fillOpacity: 0.1, interactive: false
        }).addTo(map);

        PITCHES.forEach(p => {
          const m = L.marker([p.lat, p.lng], {
            icon: L.divIcon({ className: 'pin-wrap', html: pinHtml(p, true, false), iconSize: [36, 46], iconAnchor: [18, 45] }),
            keyboard: false
          }).addTo(map).on('click', () => selectPitch(p.id));
          markers[p.id] = m;
        });

        map.on('click', () => selectPitch(null));
      } catch (err) {
        console.error('Leaflet fallback error:', err);
      }
    }

    // Suche & Vorschläge für Münchner Stadtteile
    const qInp = $('#q-map');
    const suggestBox = $('#search-suggest');

    qInp.addEventListener('input', e => {
      query = e.target.value;
      syncQuery(e.target);
      selectPitch(null);

      const val = query.trim().toLowerCase();
      if (val.length >= 2) {
        const locMatches = (window.KN?.MUNICH_LOCATIONS || []).filter(l =>
          l.name.toLowerCase().includes(val) || (l.desc && l.desc.toLowerCase().includes(val))
        ).slice(0, 4);

        const pitchMatches = PITCHES.filter(p =>
          `${p.name} ${p.district} ${p.surface} ${p.address}`.toLowerCase().includes(val)
        ).slice(0, 5);

        const items = [];
        locMatches.forEach(l => {
          items.push(`
            <button type="button" class="suggest-item" data-type="loc" data-val="${esc(l.name)}">
              <span class="suggest-pin">${ic('pin')}</span>
              <div class="suggest-info">
                <div class="suggest-name">${esc(l.name)}</div>
                <div class="suggest-desc">${esc(l.desc || 'München')}</div>
              </div>
              <span class="suggest-badge">Stadtteil</span>
            </button>
          `);
        });

        pitchMatches.forEach(p => {
          items.push(`
            <button type="button" class="suggest-item" data-type="pitch" data-val="${p.id}">
              <span class="suggest-pin suggest-pin--pitch">${ic('pitch')}</span>
              <div class="suggest-info">
                <div class="suggest-name">${esc(p.name)}</div>
                <div class="suggest-desc">${p.surface} · ${esc(p.district)} · ${fmtKm(p.dist)}</div>
              </div>
              ${pill(statusOf(p))}
            </button>
          `);
        });

        if (items.length > 0) {
          suggestBox.innerHTML = items.join('');
          suggestBox.classList.add('show');
        } else {
          suggestBox.classList.remove('show');
        }
      } else {
        suggestBox.classList.remove('show');
      }

      renderMapList();
      updateMap();
      updateListe();
    });

    suggestBox.addEventListener('click', e => {
      const b = e.target.closest('[data-type]');
      if (!b) return;
      const type = b.dataset.type;
      const val = b.dataset.val;
      if (type === 'loc') {
        const loc = (window.KN?.MUNICH_LOCATIONS || []).find(l => l.name === val);
        if (loc) setCenterLocation(loc);
      } else if (type === 'pitch') {
        const p = pitchById(val);
        if (p) {
          suggestBox.classList.remove('show');
          qInp.value = p.name;
          query = '';
          if (p.dist > state.filter.radius) {
            currentCenter = { lat: p.lat, lng: p.lng, label: p.name };
            updateDistances(currentCenter);
          }
          selectPitch(p.id);
          renderMapList();
          updateMap();
          updateListe();
          if (map) {
            map.flyTo({ center: [p.lng, p.lat], zoom: 15.5, duration: 550 });
          }
        }
      }
    });

    qInp.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const val = qInp.value.trim().toLowerCase();
        const pitch = PITCHES.find(p => p.name.toLowerCase() === val || p.name.toLowerCase().startsWith(val));
        if (pitch) {
          suggestBox.classList.remove('show');
          qInp.value = pitch.name;
          query = '';
          if (pitch.dist > state.filter.radius) {
            currentCenter = { lat: pitch.lat, lng: pitch.lng, label: pitch.name };
            updateDistances(currentCenter);
          }
          selectPitch(pitch.id);
          renderMapList();
          updateMap();
          updateListe();
          if (map) map.flyTo({ center: [pitch.lng, pitch.lat], zoom: 15.5, duration: 550 });
          qInp.blur();
          return;
        }
        const loc = (window.KN?.MUNICH_LOCATIONS || []).find(l => l.name.toLowerCase() === val || l.name.toLowerCase().startsWith(val));
        if (loc) {
          setCenterLocation(loc);
        }
        suggestBox.classList.remove('show');
        qInp.blur();
      } else if (e.key === 'Escape') {
        suggestBox.classList.remove('show');
      }
    });

    initSheetDrag();
    setTimeout(() => fitRadius(false), 80);
  }

  function pinHtml(p, active, selected) {
    const st = statusOf(p);
    return `<div class="pin ${active ? '' : 'pin--off'} ${selected ? 'pin--sel' : ''}">
      <svg viewBox="0 0 36 46" class="pin-shape"><path d="M18 45S2 31 2 18a16 16 0 0 1 32 0c0 13-16 27-16 27z"/></svg>
      ${active ? `<span class="pin-ico">${ic('pitch')}</span><span class="pin-st pin-st--${st}"></span>` : '<span class="pin-hole"></span>'}
    </div>`;
  }

  function updateMap() {
    if (!map) return;
    const vis = new Set(visiblePitches().map(p => p.id));
    PITCHES.forEach(p => {
      const sel = selectedId === p.id;
      const m = markers[p.id];
      if (m) {
        const el = m.getElement();
        el.innerHTML = pinHtml(p, vis.has(p.id), sel);
        el.style.zIndex = sel ? '900' : (vis.has(p.id) ? '200' : '50');
      }
    });
    const src = map.getSource && map.getSource('radius-source');
    if (src) {
      src.setData(makeCirclePolygon(currentCenter.lng, currentCenter.lat, state.filter.radius));
    }
    const dot = $('#filter-dot');
    if (dot) dot.classList.toggle('on', filterActive());
  }

  function fitRadius(animate) {
    if (!map) return;
    try {
      const container = map.getContainer ? map.getContainer() : document.getElementById('map');
      if (container && (container.clientWidth === 0 || container.clientHeight === 0)) {
        setTimeout(() => fitRadius(animate), 120);
        return;
      }
      const r = state.filter.radius;
      const dx = r / (111.32 * Math.cos(currentCenter.lat * Math.PI / 180));
      const dy = r / 110.574;
      const bounds = [
        [currentCenter.lng - dx, currentCenter.lat - dy],
        [currentCenter.lng + dx, currentCenter.lat + dy]
      ];
      const tk = $('#tab-karte');
      const sheetPeek = parseInt(tk?.style.getPropertyValue('--sheet-peek') || '260', 10);
      if (map.fitBounds) {
        map.fitBounds(bounds, {
          padding: { top: 70, bottom: Math.max(100, Math.round(sheetPeek * 0.7)), left: 24, right: 24 },
          duration: animate !== false ? 500 : 0
        });
      }
    } catch (_) {}
  }

  function selectPitch(id) {
    selectedId = id;
    const box = $('#map-preview');
    if (!id) { box.classList.remove('show'); updateMap(); return; }
    const p = pitchById(id);
    box.innerHTML = `<button class="preview-card" data-act="pitch" data-id="${id}">
      <img class="thumb" src="${img(p)}" alt="">
      <span class="pc-main"><span class="pc-name">${esc(p.name)}</span><span class="pc-meta">${p.surface} · ${fmtKm(p.dist)}</span>${ratingInline(p)}</span>
      <span class="pc-side">${pill(statusOf(p))}${chev}</span></button>`;
    box.classList.add('show');
    updateMap();
  }

  function renderMapList() {
    if (!map) return;
    const list = visiblePitches();
    $('#near-count').textContent = `${list.length} ${list.length === 1 ? 'Platz' : 'Plätze'} in der Nähe`;
    $('#sort-chip').innerHTML = `${state.filter.sort === 'rating' ? 'Bewertung' : 'Entfernung'} ${ic('chevronDown')}`;
    $('#map-list').innerHTML = list.length ? list.map(pitchCard).join('')
      : emptyBox('search', 'Keine Plätze gefunden', 'Vergrößere den Umkreis oder passe die Filter an.', '<button class="btn btn-small" data-act="filters">Filter anpassen</button>');
  }

  /* ---------- Liste ---------- */
  const LIST_CHIPS = [['frei', 'Jetzt frei'], ['Rasenplatz', 'Rasen'], ['Kunstrasen', 'Kunstrasen'], ['Käfig', 'Käfig'], ['Hartplatz', 'Hartplatz']];
  function buildListe() {
    const el = $('#tab-liste');
    el.innerHTML = `
      <header class="tab-head"><h1>Fußballplätze</h1>
        <button class="square-btn" data-act="filters" aria-label="Filter">${ic('sliders')}<i class="dot" id="filter-dot-2"></i></button></header>
      <div class="pad-x"><label class="search">${ic('search')}<input type="search" id="q-list" placeholder="Platz oder Stadtteil suchen" autocomplete="off" enterkeyhint="search"></label></div>
      <div class="chips" id="list-chips"></div>
      <div class="list-meta"><span id="list-count"></span><button class="select-chip" data-act="sort" id="sort-chip-2"></button></div>
      <div class="scroll list tab-body" id="list-list"></div>`;
    $('#q-list').addEventListener('input', e => { query = e.target.value; syncQuery(e.target); updateListe(); renderMapList(); updateMap(); });
    $('#q-list').addEventListener('keydown', e => { if (e.key === 'Enter') e.target.blur(); });
  }
  function updateListe() {
    const f = state.filter, list = visiblePitches();
    $('#list-chips').innerHTML = LIST_CHIPS.map(([k, l]) =>
      `<button class="chip ${(k === 'frei' ? f.onlyFree : f.surface === k) ? 'on' : ''}" data-act="chip" data-k="${k}">${k === 'frei' ? '<i class="chip-dot"></i>' : ''}${l}</button>`).join('');
    $('#list-count').textContent = `${list.length} ${list.length === 1 ? 'Platz' : 'Plätze'} · Umkreis ${f.radius} km`;
    $('#sort-chip-2').innerHTML = `${f.sort === 'rating' ? 'Bewertung' : 'Entfernung'} ${ic('chevronDown')}`;
    $('#filter-dot-2').classList.toggle('on', filterActive());
    $('#list-list').innerHTML = list.length ? list.map(pitchCard).join('')
      : emptyBox('search', 'Keine Plätze gefunden', 'Vergrößere den Umkreis oder entferne Filter.', '<button class="btn btn-small" data-act="filters">Filter anpassen</button>');
  }

  /* ---------- Anmeldungen ---------- */
  function renderAnmelden() {
    const el = $('#tab-anmelden');
    const prev = $('.scroll', el), top = prev ? prev.scrollTop : 0;
    const games = myGames();
    const open = PITCHES.filter(p => p.dist <= state.filter.radius)
      .map(p => ({ p, g: featuredGame(p) }))
      .filter(x => x.g && x.g.dk === TODAY && !x.g.joined && x.g.free > 0)
      .sort((a, b) => a.g.start - b.g.start || a.p.dist - b.p.dist).slice(0, 6);
    el.innerHTML = `
      <header class="tab-head"><h1>Meine Anmeldungen</h1></header>
      <div class="scroll tab-body">
        <h2 class="sec-title">Bevorstehend</h2>
        ${games.length ? games.map(gameCard).join('') : emptyBox('calendar', 'Noch keine Anmeldungen', 'Reserviere einen Platz oder tritt einem offenen Spiel bei.', '<button class="btn btn-small" data-act="tab" data-tab="karte">Platz finden</button>')}
        <h2 class="sec-title">Offene Spiele in deiner Nähe</h2>
        <p class="sec-sub">Heute · Diese Gruppen suchen noch Mitspieler</p>
        ${open.length ? open.map(gameCard).join('') : '<p class="empty-line">Gerade keine offenen Spiele im Umkreis.</p>'}
      </div>`;
    $('.scroll', el).scrollTop = top;
  }

  /* ---------- Profil ---------- */
  function renderProfil() {
    const el = $('#tab-profil');
    const prev = $('.scroll', el), top = prev ? prev.scrollTop : 0;
    const n = myGames().length;
    const favs = state.favs.map(pitchById).filter(Boolean);
    const revCount = Object.values(state.reviews).reduce((a, l) => a + l.length, 0);
    const xp = Math.min(USER.xpMax, USER.xp + n);
    el.innerHTML = `
      <header class="tab-head"><h1>Mein Profil</h1></header>
      <div class="scroll tab-body">
        <div class="profile-card">${avatar('me', 'xl')}
          <div><h2>${esc(USER.name)}</h2><span class="muted">${USER.handle}</span>
          <span class="small">${USER.position} · ${USER.level} · ${USER.age} Jahre</span></div></div>
        <div class="level-box"><div class="lv-head"><b>Level ${USER.lvl}</b><span>${xp}/${USER.xpMax} Spiele bis Level ${USER.lvl + 1}</span></div>
          <div class="bar"><i style="width:${xp / USER.xpMax * 100}%"></i></div></div>
        <div class="stats">
          <div><b>${14 + n}</b><span>Spiele</span></div>
          <div><b>${favs.length}</b><span>Favoriten</span></div>
          <div><b>${3 + revCount}</b><span>Bewertungen</span></div>
        </div>
        <div class="menu">
          <button class="menu-row" data-act="tab" data-tab="anmelden">${ic('signup')}<span>Meine Anmeldungen</span><em>${n}</em>${chev}</button>
          <div class="menu-row">${ic('pin')}<span>Mein Standort</span><em>${USER_LOCATION.label}</em></div>
          <button class="menu-row" data-act="filters">${ic('locate')}<span>Suchradius</span><em>${state.filter.radius} km</em>${chev}</button>
        </div>
        <h2 class="sec-title">Favoriten</h2>
        ${favs.length ? favs.map(pitchCard).join('') : '<p class="empty-line">Tippe auf das Herz bei einem Platz, um ihn hier zu speichern.</p>'}
        <button class="btn btn-ghost mt" data-act="reset-demo">${ic('refresh')} Demo zurücksetzen</button>
        <p class="app-foot"><img src="assets/logo.svg" alt=""> KickNow Demo · alle Daten fiktiv<br>Kartendaten © OpenStreetMap-Mitwirkende</p>
      </div>`;
    $('.scroll', el).scrollTop = top;
  }

  /* =====================================================================
     Navigation (Stapel von Unterseiten)
     ===================================================================== */
  const stack = [];
  function push(view, params) {
    const el = document.createElement('section');
    el.className = 'screen push';
    $('#push-layer').appendChild(el);
    const entry = { view, params: params || {}, el, fresh: true };
    stack.push(entry);
    render(entry);
    entry.fresh = false;
    el.getBoundingClientRect();
    el.classList.add('in');
    if (stack.length > 1) stack[stack.length - 2].el.classList.add('behind');
    return entry;
  }
  function render(entry) {
    const sc = $('.scroll', entry.el), top = sc ? sc.scrollTop : 0;
    VIEWS[entry.view](entry.el, entry.params, entry);
    const sc2 = $('.scroll', entry.el);
    if (sc2 && !entry.fresh) sc2.scrollTop = top;
  }
  function back() {
    const e = stack.pop();
    if (!e) return;
    e.el.classList.remove('in');
    e.el.classList.add('out');
    setTimeout(() => e.el.remove(), 360);
    const top = stack[stack.length - 1];
    if (top) { top.el.classList.remove('behind'); render(top); }
    refreshTabs();
  }
  function replaceTop(view, params) {
    const old = stack.pop();
    push(view, params);
    if (old) setTimeout(() => old.el.remove(), 360);
  }
  function popAll() { while (stack.length) stack.pop().el.remove(); }
  const topEntry = view => { const t = stack[stack.length - 1]; return t && t.view === view ? t : null; };
  const rerenderTop = () => { const t = stack[stack.length - 1]; if (t) render(t); };

  /* =====================================================================
     Unterseiten
     ===================================================================== */
  const VIEWS = {};

  /* ---------- Platz-Details ---------- */
  VIEWS.pitch = function (el, { id }) {
    const p = pitchById(id), av = availability(p), r = ratingOf(p), fg = featuredGame(p);
    const fav = state.favs.includes(id);
    const amen = (icn, label, on) => `<div class="amen ${on ? '' : 'off'}">${ic(icn)}<span>${label}</span></div>`;
    const hint = fg
      ? `${ic('chat')}<span>${fg.dk === TODAY ? 'Heute' : 'Morgen'} ${fmtTime(fg.start)} Uhr: ${fg.count} Spieler · ${freeText(fg.free)}</span>`
      : `${ic('info')}<span>Heute keine offenen Spiele</span>`;
    el.innerHTML = `
      <div class="scroll has-footer">
        <div class="hero">
          <img src="${img(p)}" alt="">
          <div class="hero-bar">
            <button class="round-btn" data-act="back" aria-label="Zurück">${ic('arrowLeft')}</button>
            <button class="round-btn fav ${fav ? 'on' : ''}" data-act="fav" data-id="${id}" aria-label="Favorit">${ic('heart')}</button>
          </div>
        </div>
        <div class="detail">
          <div class="title-row"><h1>${esc(p.name)}</h1>
            <button class="rating-btn" data-act="reviews" data-id="${id}">${ic('star')}<b>${dec1(r.avg)}</b><span>(${r.count})</span></button></div>
          <p class="meta">${p.surface}${p.cage ? ' · Käfig' : ''} · ${sizeText(p)} · ${fmtKm(p.dist)}</p>
          <div class="amenities">
            ${amen('bulb', 'Flutlicht', p.amenities.flutlicht)}${amen('hanger', 'Umkleide', p.amenities.umkleide)}
            ${amen('wc', 'Toiletten', p.amenities.toiletten)}${amen('door', p.access, true)}
          </div>
          <button class="avail avail--${av.st}" data-act="game" data-id="${fg ? fg.id : ''}">
            <span class="avail-dot"></span>
            <span class="avail-text"><b>${av.title}</b><span>${av.sub}</span></span>
            <span class="avail-cta">${ic('chat')}</span>
            <span class="avail-hint">${hint}${chev}</span>
          </button>
          <button class="row-card" data-act="calendar" data-id="${id}">${ic('calendar')}<span>Belegungskalender</span>${chev}</button>
          <div class="rows">
            <button class="row" data-act="players" data-id="${id}">
              <span class="row-main"><b>Anmeldungen</b>
              ${fg ? `<span class="row-inline">${avatarStack(fg, 3)}<span class="row-small"><span>${fg.count} / ${fg.maxPlayers} Spieler · ${dayLabel(fg.dk)} ${fmtTime(fg.start)}</span><span class="green">${freeText(fg.free)}</span></span></span>`
                : '<span class="row-small">Heute noch keine Anmeldungen</span>'}</span>${chev}</button>
            <button class="row" data-act="reviews" data-id="${id}">
              <span class="row-main row-h"><b>Bewertungen</b>${ratingInline(p)}</span>${chev}</button>
          </div>
          <div class="about"><h3>Über den Platz</h3><p>${esc(p.desc)}</p>
            ${p.club ? `<p class="addr">${ic('flag')}<span>Heimverein: <b>${esc(p.club)}</b></span></p>` : ''}
            <p class="addr">${ic('pin')}<span>${esc(p.address)}, ${esc(p.district)}</span></p></div>
        </div>
      </div>
      <div class="footer-bar"><a class="btn btn-dark" href="https://maps.apple.com/?daddr=${p.lat},${p.lng}&dirflg=w" target="_blank" rel="noopener">${ic('nav')} Route starten</a></div>`;
  };

  /* ---------- Belegungskalender ---------- */
  function slotCard(s) {
    const time = `<span class="slot-time">${fmtRange(s)}</span>`;
    if (s.past) return `<div class="slot slot--past"><span class="slot-l">${time}<span class="slot-info">Vorbei</span></span></div>`;
    if (s.type === 'free') {
      return `<button class="slot slot--frei" data-act="reserve" data-id="${s.pitchId}" data-dk="${s.dk}" data-idx="${s.idx}">
        <span class="slot-l">${time}<span class="slot-info">${ic('plus')} Tippen zum Reservieren</span></span>${pill('frei')}</button>`;
    }
    if (s.type === 'game') {
      const info = s.mine ? 'Deine Reservierung' : s.open === false ? 'Privat' : `Offenes Spiel · ${s.level}`;
      return `<button class="slot slot--spiel ${s.joined ? 'slot--mine' : ''}" data-act="game" data-id="${s.id}">
        <span class="slot-l">${time}<span class="slot-info">${avatarStack(s)}<span>${s.count}/${s.maxPlayers} · ${info}</span></span></span>
        <span class="pill pill--spiel">${s.joined ? 'Dabei' : s.free > 0 ? freeText(s.free) : 'Voll'}</span></button>`;
    }
    return `<div class="slot slot--belegt"><span class="slot-l">${time}<span class="slot-info">${ic('flag')} ${esc(s.label)}</span></span>${pill('belegt')}</div>`;
  }
  VIEWS.calendar = function (el, params, entry) {
    const p = pitchById(params.id), dk = params.dk || TODAY, day = getDay(p, dk);
    el.innerHTML = `
      ${navbar('Belegungskalender', p.name)}
      <div class="day-strip">${DAYS.map(d => {
        const dt = dkDate(d);
        return `<button class="day ${d === dk ? 'on' : ''}" data-act="cal-day" data-dk="${d}"><span>${WD[dt.getDay()]}</span><b>${dt.getDate()}</b>${d === TODAY ? '<i></i>' : ''}</button>`;
      }).join('')}</div>
      <div class="scroll has-footer pad">
        <div class="cal-head"><h2>${dayLabel(dk)}${dk === TODAY || dk === dkAdd(TODAY, 1) ? `, ${shortDate(dk)}` : ''}</h2>
          <span class="legend"><i class="lg frei"></i>Frei<i class="lg spiel"></i>Spiel<i class="lg belegt"></i>Belegt</span></div>
        <div class="slots">${day.map(slotCard).join('')}</div>
        <p class="foot-note">Öffnungszeiten 08:30 – 22:00 Uhr · Slots à 90 Minuten</p>
      </div>
      <div class="footer-bar"><button class="btn btn-dark" data-act="reserve" data-id="${p.id}" data-dk="${dk}">${ic('calendar')} Platz reservieren</button></div>`;
    const strip = $('.day-strip', el), on = $('.day.on', strip);
    strip.scrollLeft = Math.max(0, on.offsetLeft - strip.clientWidth / 2 + on.clientWidth / 2);
    // Beim Öffnen direkt zum aktuellen Zeitraum springen (vergangene Slots überspringen)
    const sc = $('.scroll', el), firstLive = $('.slot:not(.slot--past)', el);
    if (entry.fresh && firstLive && firstLive.previousElementSibling) sc.scrollTop = firstLive.offsetTop - sc.offsetTop - 12;
  };

  /* ---------- Reservieren ---------- */
  VIEWS.reserve = function (el, params, entry) {
    const p = pitchById(params.id);
    if (!entry.form) {
      entry.form = { dk: params.dk || TODAY, idx: params.idx, group: Math.min(4, p.maxPlayers), open: true, max: p.maxPlayers, level: 'Locker', note: '' };
    }
    const f = entry.form;
    const freeSlots = getDay(p, f.dk).filter(s => s.type === 'free' && !s.past);
    if (!freeSlots.some(s => s.idx === f.idx)) f.idx = freeSlots.length ? freeSlots[0].idx : null;
    if (f.max < f.group) f.max = f.group;
    const stepper = (k, v, min, max) => `<div class="stepper" data-k="${k}" data-min="${min}" data-max="${max}">
      <button type="button" data-d="-1" ${v <= min ? 'disabled' : ''} aria-label="Weniger">${ic('minus')}</button>
      <output>${v}</output><button type="button" data-d="1" ${v >= max ? 'disabled' : ''} aria-label="Mehr">${ic('plus')}</button></div>`;
    const sel = freeSlots.find(s => s.idx === f.idx);
    el.innerHTML = `
      ${navbar('Platz reservieren', p.name)}
      <div class="scroll has-footer pad form">
        <div class="mini-pitch"><img class="thumb" src="${img(p)}" alt=""><div><b>${esc(p.name)}</b><span>${p.surface} · ${sizeText(p)}</span></div></div>
        <label class="field-label">Wann?</label>
        <div class="field">${ic('calendar')}<select id="r-day">${DAYS.map(d =>
          `<option value="${d}" ${d === f.dk ? 'selected' : ''}>${dayLabel(d)}${d === TODAY || d === dkAdd(TODAY, 1) ? ', ' + shortDate(d) : ''}</option>`).join('')}</select>${ic('chevronDown', 'chev')}</div>
        <div class="field">${ic('clock')}<select id="r-slot" ${freeSlots.length ? '' : 'disabled'}>${freeSlots.length
          ? freeSlots.map(s => `<option value="${s.idx}" ${s.idx === f.idx ? 'selected' : ''}>${fmtRange(s)} Uhr</option>`).join('')
          : '<option>Keine freien Zeiten an diesem Tag</option>'}</select>${ic('chevronDown', 'chev')}</div>
        <label class="field-label">Wie viele seid ihr?</label>
        ${stepper('group', f.group, 1, p.maxPlayers)}
        <div class="toggle-row"><div><b>Offen für Mitspieler</b><span>Andere Spieler sehen euer Spiel, können beitreten und mit euch chatten.</span></div>
          <button type="button" class="switch ${f.open ? 'on' : ''}" data-r="open" aria-label="Offen für Mitspieler"><i></i></button></div>
        ${f.open ? `<label class="field-label">Maximale Spielerzahl</label>${stepper('max', f.max, Math.max(2, f.group), 22)}
          <label class="field-label">Niveau</label>
          <div class="seg">${LEVELS.map(l => `<button type="button" class="seg-btn ${f.level === l ? 'on' : ''}" data-level="${l}">${l}</button>`).join('')}</div>` : ''}
        <label class="field-label">Nachricht an Mitspieler (optional)</label>
        <textarea id="r-note" rows="3" placeholder="z. B. Bringt helle und dunkle Shirts mit …">${esc(f.note)}</textarea>
        ${sel ? `<div class="summary">${ic('info')}<span>${dayLabel(f.dk)}, ${fmtRange(sel)} Uhr · ${f.group} ${f.group === 1 ? 'Spieler' : 'Spieler'}${f.open ? ` · noch ${freeText(f.max - f.group)}` : ' · privat'}</span></div>` : ''}
      </div>
      <div class="footer-bar"><button class="btn btn-mint" id="r-go" ${f.idx == null ? 'disabled' : ''}>Verbindlich reservieren</button></div>`;

    $('#r-day', el).addEventListener('change', e => { f.dk = e.target.value; f.idx = null; render(entry); });
    $('#r-slot', el).addEventListener('change', e => { f.idx = +e.target.value; render(entry); });
    $('#r-note', el).addEventListener('input', e => { f.note = e.target.value; });
    $('#r-go', el).addEventListener('click', () => createBooking(p, f));
    if (!entry.bound) {
      entry.bound = true;
      el.addEventListener('click', e => {
        const step = e.target.closest('.stepper [data-d]');
        if (step) {
          const box = step.closest('.stepper'), k = box.dataset.k;
          f[k] = Math.min(+box.dataset.max, Math.max(+box.dataset.min, f[k] + +step.dataset.d));
          render(entry); return;
        }
        if (e.target.closest('[data-r="open"]')) { f.open = !f.open; render(entry); return; }
        const lv = e.target.closest('[data-level]');
        if (lv) { f.level = lv.dataset.level; render(entry); }
      });
    }
  };
  function createBooking(p, f) {
    const s = f.idx == null ? null : getDay(p, f.dk)[f.idx];
    if (!s || s.type !== 'free' || s.past) { toast('Dieser Zeitraum ist nicht mehr frei', 'info'); return; }
    state.bookings[s.id] = {
      group: f.group, open: f.open, maxPlayers: f.open ? Math.max(f.max, f.group) : f.group, level: f.level, created: now()
    };
    state.chats[s.id] = [{ system: true, text: `${USER.first} hat den Platz reserviert`, ts: now() }];
    if (f.note.trim()) state.chats[s.id].push({ from: 'me', text: f.note.trim(), ts: now() + 1 });
    save();
    refreshTabs();
    toast('Reservierung bestätigt');
    replaceTop('game', { id: s.id });
    if (f.open) setTimeout(() => simulateInterest(s.id), 7000);
  }

  /* ---------- Spiel & Gruppenchat ---------- */
  const typing = {};
  function chatHtml(g) {
    const msgs = messagesOf(g);
    let html = msgs.map(m => {
      if (m.system) return `<div class="msg-sys">${esc(m.text)}</div>`;
      const mine = m.from === 'me', u = person(m.from);
      return `<div class="msg ${mine ? 'mine' : ''}">${mine ? '' : avatar(m.from, 'sm')}
        <div class="bubble">${mine ? '' : `<b>${esc(u.short)}${m.from === g.organizer ? ' · Orga' : ''}</b>`}<p>${esc(m.text)}</p><time>${fmtClock(m.ts)}</time></div></div>`;
    }).join('');
    if (typing[g.id]) {
      html += `<div class="msg">${avatar(typing[g.id], 'sm')}<div class="bubble typing"><b>${esc(person(typing[g.id]).short)}</b><p><i></i><i></i><i></i></p></div></div>`;
    }
    return html || '<div class="msg-sys">Noch keine Nachrichten – frag die Gruppe, ob noch Spieler willkommen sind!</div>';
  }
  VIEWS.game = function (el, { id }, entry) {
    const { p, g } = getSlot(id);
    if (!g || g.type !== 'game') {
      el.innerHTML = `${navbar('Spiel')}<div class="scroll pad">${emptyBox('info', 'Spiel nicht gefunden', 'Dieses Spiel existiert nicht mehr.')}</div>`;
      return;
    }
    const org = person(g.organizer), j = state.joined[id];
    const title = g.mine ? 'Dein Spiel' : g.joined ? 'Du bist dabei' : 'Spiel beitreten';
    let action;
    if (g.past) action = '<div class="info-bar">Dieses Spiel ist bereits vorbei.</div>';
    else if (g.mine) action = `<div class="joined-bar">${ic('check')}<span>Du hast diesen Platz reserviert</span><button class="link-btn danger" data-act="cancel-booking" data-id="${id}">Stornieren</button></div>`;
    else if (g.joined) action = `<div class="joined-bar">${ic('check')}<span>Du bist dabei${j && j.count > 1 ? ` (+${j.count - 1})` : ''}</span><button class="link-btn danger" data-act="leave" data-id="${id}">Absagen</button></div>`;
    else if (g.free > 0) action = `<button class="btn btn-mint" data-act="join" data-id="${id}">Mitspielen</button><p class="hint-center">Unsicher? Frag einfach unten im Chat nach.</p>`;
    else action = '<button class="btn btn-mint" disabled>Ausgebucht</button>';

    const members = new Set(g.participants);
    messagesOf(g).forEach(m => m.from && members.add(m.from));

    el.innerHTML = `
      ${navbar(title)}
      <div class="scroll pad game-scroll">
        <img class="banner" src="${img(p)}" alt="">
        <div class="title-row"><h1 class="h-md">${esc(p.name)}</h1>${ratingInline(p)}</div>
        <p class="meta">${p.surface} · ${sizeText(p)} · ${fmtKm(p.dist)}</p>
        <div class="game-box">
          <div class="gb-row"><span class="gb-when">${ic('calendar')}<b>${dayLabel(g.dk)}, ${fmtTime(g.start)}</b></span><span class="gb-dur">${ic('clock')}1,5 h</span></div>
          <div class="gb-row"><span class="gb-free">${ic('users')}${freeText(g.free)}</span>${avatarStack(g, 4)}</div>
          <div class="gb-tags"><span class="tag">Niveau: ${g.level}</span><span class="tag">${g.count}/${g.maxPlayers} Spieler</span>
            <span class="tag">Orga: ${g.mine ? 'Du' : esc(org.short)}</span></div>
        </div>
        ${action}
        <div class="chat-head"><h2>${ic('chat')} Gruppenchat</h2><span>${members.size + g.extra} Teilnehmer</span></div>
        <div class="chat-list">${chatHtml(g)}</div>
      </div>
      <form class="composer" autocomplete="off">
        <input type="text" class="chat-input" placeholder="Nachricht an die Gruppe …" enterkeyhint="send" value="${esc(entry.draft || '')}">
        <button type="submit" class="send-btn" aria-label="Senden">${ic('send')}</button>
      </form>`;
    const input = $('.chat-input', el);
    input.addEventListener('input', () => { entry.draft = input.value; });
    $('.composer', el).addEventListener('submit', e => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = ''; entry.draft = '';
      addMsg(id, { from: 'me', text, ts: now() });
      rerenderChat(id);
      scheduleReply(id, text);
    });
  };
  function addMsg(id, m) { (state.chats[id] = state.chats[id] || []).push(m); save(); }
  function rerenderChat(id) {
    const t = stack.find(e => e.view === 'game' && e.params.id === id);
    if (!t) return;
    const { g } = getSlot(id), box = $('.chat-list', t.el), sc = $('.scroll', t.el);
    if (!box) return;
    box.innerHTML = chatHtml(g);
    sc.scrollTo({ top: sc.scrollHeight, behavior: 'smooth' });
  }
  function responders(g) {
    const set = new Set(g.participants.filter(x => x !== 'me'));
    (state.chats[g.id] || []).forEach(m => { if (m.from && m.from !== 'me') set.add(m.from); });
    return Array.from(set);
  }
  function replyFor(g, text) {
    const t = text.toLowerCase(), free = g.free;
    if (/(platz|plätze|mitspiel|mitmach|dazu|noch (jemand|leute|spieler)|mehr leute|willkommen|kann ich|können wir|darf ich|dabei sein|komm)/.test(t)) {
      return free > 0
        ? rand([`Klar, wir haben noch ${freeText(free)} – komm einfach vorbei! ⚽`, `Gerne! Aktuell ${freeText(free)}, je mehr desto besser 🙌`, `Na klar! Noch ${freeText(free)} – meld dich einfach über „Mitspielen“ an 👍`])
        : 'Leider sind wir schon komplett – schau gern beim nächsten Termin vorbei!';
    }
    if (/(ball|bälle|leibchen|trikot|shirt|pumpe)/.test(t)) return rand(['Ball hab ich dabei, Leibchen bringt Max mit 👕', 'Bring gern noch einen Ball mit, schaden kann’s nicht ⚽']);
    if (/(wann|uhr|zeit|treffpunkt|treffen|wo )/.test(t)) return `Wir treffen uns um ${fmtTime(g.start)} direkt am Platz – halt einfach nach der Gruppe mit den Leibchen Ausschau 😉`;
    if (/(niveau|level|anfänger|stark|schlecht|gut genug)/.test(t)) return `Ganz entspannt – Niveau ist eher „${g.level}“. Jeder ist willkommen!`;
    if (/(regen|wetter|nass|gewitter)/.test(t)) return 'Wir spielen auch bei leichtem Regen. Falls Gewitter kommt, sagen wir hier im Chat ab.';
    if (/(schuh|stollen|nocken)/.test(t)) return 'Multinocken oder Turnschuhe reichen völlig.';
    if (/(danke|super|cool|top|nice|perfekt|geil|klasse)/.test(t)) return rand(['Gerne! Bis später 👋', '👍', 'Freu mich, bis gleich!']);
    if (/(hallo|hi|hey|servus|moin|grüß)/.test(t)) return rand(['Servus! 👋', 'Hey, willkommen in der Runde!', 'Hi! Was gibt’s?']);
    return rand(['Klingt gut! 👍', 'Alles klar, bis später!', 'Passt, danke für die Info!', 'Top, freu mich ⚽']);
  }
  function scheduleReply(id, text) {
    const { g } = getSlot(id), rs = responders(g);
    if (!rs.length) return;
    const who = rs.includes(g.organizer) && Math.random() < 0.65 ? g.organizer : rand(rs);
    setTimeout(() => {
      typing[id] = who; rerenderChat(id);
      setTimeout(() => {
        delete typing[id];
        addMsg(id, { from: who, text: replyFor(getSlot(id).g, text), ts: now() });
        rerenderChat(id);
      }, 1400 + Math.random() * 1000);
    }, 700);
  }
  function simulateInterest(id) {
    const { g } = getSlot(id);
    if (!g || !g.mine) return;
    const who = rand(PLAYERS).id;
    typing[id] = who; rerenderChat(id);
    setTimeout(() => {
      delete typing[id];
      addMsg(id, { from: who, text: rand(['Hi! Habt ihr noch Platz? Würde gern mitspielen 🙂', 'Servus, wäre mit einem Kumpel dabei, falls ihr noch Leute braucht!', 'Hey, ist das Spiel noch offen? Ich wäre dabei ⚽']), ts: now() });
      rerenderChat(id);
      if (!stack.some(e => e.view === 'game' && e.params.id === id)) toast('Neue Nachricht in deinem Spiel', 'chat');
    }, 1800);
  }
  function openJoinSheet(id) {
    const { p, g } = getSlot(id);
    const maxBring = Math.min(4, g.free);
    let count = 1;
    const sh = openSheet(`
      <h2>Mitspielen</h2>
      <p class="muted">${esc(p.name)} · ${dayLabel(g.dk)}, ${fmtRange(g)} Uhr</p>
      <label class="field-label">Wie viele Spieler bringst du mit?</label>
      <div class="seg" id="join-count">${Array.from({ length: maxBring }, (_, i) => i + 1).map(n =>
        `<button type="button" class="seg-btn ${n === 1 ? 'on' : ''}" data-n="${n}">${n === 1 ? 'Nur ich' : n === maxBring && maxBring === 4 ? '4' : n}</button>`).join('')}</div>
      <label class="field-label">Nachricht (optional)</label>
      <textarea id="join-msg" rows="2" placeholder="Kurze Nachricht an die Gruppe …"></textarea>
      <button class="btn btn-mint" id="join-go">Mitspielen</button>`);
    $('#join-count', sh).addEventListener('click', e => {
      const b = e.target.closest('[data-n]');
      if (!b) return;
      count = +b.dataset.n;
      $$('.seg-btn', sh).forEach(x => x.classList.toggle('on', x === b));
    });
    $('#join-go', sh).addEventListener('click', () => {
      const msg = $('#join-msg', sh).value.trim();
      state.joined[id] = { count, ts: now() };
      addMsg(id, { system: true, text: `${USER.first} spielt mit${count > 1 ? ` (+${count - 1})` : ''}`, ts: now() });
      if (msg) addMsg(id, { from: 'me', text: msg, ts: now() + 1 });
      closeSheet();
      rerenderTop();
      refreshTabs();
      toast('Du bist dabei!');
      const org = g.organizer;
      setTimeout(() => {
        typing[id] = org; rerenderChat(id);
        setTimeout(() => {
          delete typing[id];
          addMsg(id, { from: org, text: `Willkommen, ${USER.first}! 🙌 Bis ${fmtTime(g.start)} am Platz.`, ts: now() });
          rerenderChat(id);
        }, 1500);
      }, 900);
    });
  }

  /* ---------- Angemeldete Spieler ---------- */
  VIEWS.players = function (el, { id }) {
    const p = pitchById(id);
    let dk = TODAY;
    let games = getDay(p, dk).filter(s => s.type === 'game' && !s.past);
    if (!games.length) { dk = dkAdd(TODAY, 1); games = getDay(p, dk).filter(s => s.type === 'game'); }
    const total = games.reduce((a, g) => a + g.count, 0);
    const row = (uid, g) => {
      const u = person(uid);
      return `<div class="player-row">${avatar(uid)}<div class="pr-main"><b>${esc(u.name)}${uid === 'me' ? ' (du)' : ''}</b>
        <span>${u.age} J. · ${u.position} · ${u.level}</span></div>${uid === g.organizer ? '<span class="tag tag--dark">Orga</span>' : ''}</div>`;
    };
    el.innerHTML = `
      ${navbar('Anmeldungen', p.name)}
      <div class="scroll pad">
        <div class="players-sum">${ic('users')}<div><b>${total} Spieler</b><span>${dk === TODAY ? 'heute' : 'morgen'} auf diesem Platz angemeldet</span></div></div>
        ${games.length ? games.map(g => `
          <section class="pgroup">
            <button class="pgroup-head" data-act="game" data-id="${g.id}">
              <span><b>${dayLabel(g.dk)}, ${fmtRange(g)} Uhr</b><small>${g.mine ? 'Deine Reservierung' : `Offenes Spiel · ${g.level}`} · ${freeText(g.free)}</small></span>
              <span class="pill pill--spiel">${g.count}/${g.maxPlayers}</span>${chev}</button>
            ${g.participants.map(uid => row(uid, g)).join('')}
            ${g.extra ? `<div class="player-row guest"><span class="av more">+${g.extra}</span><div class="pr-main"><b>${g.extra} ${g.extra === 1 ? 'Gast' : 'Gäste'}</b><span>ohne KickNow-Profil</span></div></div>` : ''}
          </section>`).join('') : emptyBox('users', 'Keine Anmeldungen', 'Für heute und morgen hat sich noch niemand angemeldet.')}
      </div>`;
  };

  /* ---------- Bewertungen ---------- */
  VIEWS.reviews = function (el, { id }) {
    const p = pitchById(id), r = ratingOf(p), max = Math.max(1, ...r.dist);
    el.innerHTML = `
      ${navbar('Bewertungen', p.name)}
      <div class="scroll pad">
        <div class="rate-sum">
          <div class="rate-big"><b>${dec1(r.avg)}</b>${stars(r.avg)}<span>${r.count} Bewertungen</span></div>
          <div class="rate-bars">${[5, 4, 3, 2, 1].map(s => `<div class="bar-row"><span>${s}</span>${ic('star')}
            <div class="bar"><i style="width:${r.dist[s - 1] / max * 100}%"></i></div><em>${r.dist[s - 1]}</em></div>`).join('')}</div>
        </div>
        <button class="btn btn-dark" data-act="write-review" data-id="${id}">${ic('star')} Bewertung schreiben</button>
        <div class="reviews">${r.reviews.map(rv => {
          const u = person(rv.from);
          return `<article class="review"><div class="rv-head">${avatar(rv.from)}<div><b>${esc(u.short)}${rv.from === 'me' ? ' (du)' : ''}</b><span>${relDays(rv.ts)}</span></div>${stars(rv.stars)}</div>
            ${rv.text ? `<p>${esc(rv.text)}</p>` : ''}${rv.tags && rv.tags.length ? `<div class="rv-tags">${rv.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>` : ''}</article>`;
        }).join('')}</div>
      </div>`;
  };
  function openReviewSheet(id) {
    const p = pitchById(id);
    let val = 0;
    const sh = openSheet(`
      <h2>Bewertung schreiben</h2><p class="muted">${esc(p.name)}</p>
      <div class="star-pick">${[1, 2, 3, 4, 5].map(n => `<button type="button" data-s="${n}" aria-label="${n} Sterne">${ic('star')}</button>`).join('')}</div>
      <textarea id="rv-text" rows="3" placeholder="Wie war der Platz? Belag, Tore, Atmosphäre …"></textarea>
      <button class="btn btn-dark" id="rv-go" disabled>Bewertung abschicken</button>`);
    $('.star-pick', sh).addEventListener('click', e => {
      const b = e.target.closest('[data-s]');
      if (!b) return;
      val = +b.dataset.s;
      $$('.star-pick button', sh).forEach(x => x.classList.toggle('on', +x.dataset.s <= val));
      $('#rv-go', sh).disabled = false;
    });
    $('#rv-go', sh).addEventListener('click', () => {
      (state.reviews[id] = state.reviews[id] || []).push({ stars: val, text: $('#rv-text', sh).value.trim(), ts: now(), tags: [] });
      save(); closeSheet(); rerenderTop(); refreshTabs();
      toast('Danke für deine Bewertung!');
    });
  }

  /* ---------- Filter & Sortierung ---------- */
  function openFilters() {
    const f = state.filter;
    const body = () => `
      <h2>Filter</h2>
      <label class="field-label">Umkreis</label>
      <div class="seg">${[2, 5, 10, 15, 25].map(km => `<button type="button" class="seg-btn ${f.radius === km ? 'on' : ''}" data-f="radius" data-v="${km}">${km} km</button>`).join('')}</div>
      <div class="toggle-row"><div><b>Nur jetzt freie Plätze</b><span>Plätze ohne aktuelle Buchung oder Spiel</span></div>
        <button type="button" class="switch ${f.onlyFree ? 'on' : ''}" data-f="onlyFree"><i></i></button></div>
      <label class="field-label">Belag</label>
      <div class="seg wrap">${[['alle', 'Alle'], ['Rasenplatz', 'Rasen'], ['Kunstrasen', 'Kunstrasen'], ['Käfig', 'Käfig'], ['Hartplatz', 'Hartplatz'], ['Asphalt', 'Asphalt']].map(([k, l]) =>
        `<button type="button" class="seg-btn ${f.surface === k ? 'on' : ''}" data-f="surface" data-v="${k}">${l}</button>`).join('')}</div>
      <label class="field-label">Sortieren nach</label>
      <div class="seg">${[['distance', 'Entfernung'], ['rating', 'Bewertung']].map(([k, l]) =>
        `<button type="button" class="seg-btn ${f.sort === k ? 'on' : ''}" data-f="sort" data-v="${k}">${l}</button>`).join('')}</div>
      <div class="btn-row"><button type="button" class="btn btn-ghost" data-f="reset">Zurücksetzen</button>
        <button type="button" class="btn btn-dark" data-act="close-sheet">${visiblePitches().length} Plätze anzeigen</button></div>`;
    const sh = openSheet(body());
    sh.addEventListener('click', e => {
      const b = e.target.closest('[data-f]');
      if (!b) return;
      const k = b.dataset.f;
      if (k === 'radius') f.radius = +b.dataset.v;
      else if (k === 'onlyFree') f.onlyFree = !f.onlyFree;
      else if (k === 'reset') Object.assign(f, DEFAULT_FILTER);
      else f[k] = b.dataset.v;
      save();
      refreshTabs();
      if (k === 'radius' || k === 'reset') fitRadius();
      $('.sheet-inner', sh).innerHTML = body();
    });
  }
  function openSort() {
    const f = state.filter;
    const sh = openSheet(`<h2>Sortieren nach</h2>
      <div class="option-list">${[['distance', 'Entfernung', 'pin'], ['rating', 'Bewertung', 'star']].map(([k, l, icn]) =>
        `<button type="button" class="option ${f.sort === k ? 'on' : ''}" data-v="${k}">${ic(icn)}<span>${l}</span>${f.sort === k ? ic('check', 'ok') : ''}</button>`).join('')}</div>`);
    sh.addEventListener('click', e => {
      const b = e.target.closest('[data-v]');
      if (!b) return;
      f.sort = b.dataset.v; save(); refreshTabs(); closeSheet();
    });
  }

  /* =====================================================================
     Aktionen (Event-Delegation)
     ===================================================================== */
  const ACT = {
    tab: t => { closeSheet(); popAll(); showTab(t.dataset.tab); refreshTabs(); },
    pitch: t => push('pitch', { id: t.dataset.id }),
    back: () => back(),
    fav: t => {
      const id = t.dataset.id, i = state.favs.indexOf(id);
      if (i >= 0) state.favs.splice(i, 1); else state.favs.push(id);
      save(); rerenderTop(); renderProfil();
      toast(i >= 0 ? 'Aus Favoriten entfernt' : 'Zu Favoriten hinzugefügt', 'heart');
    },
    game: t => { if (t.dataset.id) push('game', { id: t.dataset.id }); else toast('Heute keine offenen Spiele', 'info'); },
    calendar: t => push('calendar', { id: t.dataset.id }),
    'cal-day': t => { const e = topEntry('calendar'); if (e) { e.params.dk = t.dataset.dk; e.fresh = true; render(e); e.fresh = false; } },
    reserve: t => {
      const params = { id: t.dataset.id, dk: t.dataset.dk || TODAY };
      if (t.dataset.idx != null) params.idx = +t.dataset.idx;
      push('reserve', params);
    },
    players: t => push('players', { id: t.dataset.id }),
    reviews: t => push('reviews', { id: t.dataset.id }),
    'write-review': t => openReviewSheet(t.dataset.id),
    join: t => openJoinSheet(t.dataset.id),
    leave: t => confirmSheet('Absagen?', 'Die Gruppe wird im Chat informiert, dass du doch nicht kommst.', 'Absagen', () => {
      const id = t.dataset.id;
      delete state.joined[id];
      addMsg(id, { system: true, text: `${USER.first} hat abgesagt`, ts: now() });
      rerenderTop(); refreshTabs(); toast('Du hast abgesagt', 'info');
    }),
    'cancel-booking': t => confirmSheet('Reservierung stornieren?', 'Der Platz wird wieder freigegeben und der Gruppenchat gelöscht.', 'Stornieren', () => {
      const id = t.dataset.id;
      delete state.bookings[id]; delete state.chats[id];
      save(); back(); toast('Reservierung storniert', 'info');
    }),
    filters: () => openFilters(),
    sort: () => openSort(),
    chip: t => {
      const f = state.filter, k = t.dataset.k;
      if (k === 'frei') f.onlyFree = !f.onlyFree; else f.surface = f.surface === k ? 'alle' : k;
      save(); refreshTabs();
    },
    recenter: () => {
      currentCenter = { lat: USER_LOCATION.lat, lng: USER_LOCATION.lng, label: USER_LOCATION.label };
      updateDistances(currentCenter);
      const qInp = $('#q-map');
      if (qInp) {
        qInp.value = '';
        qInp.placeholder = USER_LOCATION.label;
      }
      query = '';
      syncQuery(null);
      const sb = $('#search-suggest');
      if (sb) sb.classList.remove('show');
      selectPitch(null);
      updateMap();
      renderMapList();
      updateListe();
      if (map) {
        map.flyTo({ center: [USER_LOCATION.lng, USER_LOCATION.lat], zoom: 13.5, duration: 600 });
        setTimeout(() => fitRadius(true), 650);
      }
      toast('Standort: ' + USER_LOCATION.label, 'locate');
    },
    'toggle-sheet': () => {
      if (currentSheetState === 'collapsed') {
        setSheetState('normal');
      } else if (currentSheetState === 'expanded') {
        setSheetState('normal');
      } else {
        setSheetState('expanded');
      }
    },
    'close-sheet': () => closeSheet(),
    'reset-demo': () => confirmSheet('Demo zurücksetzen?', 'Alle Reservierungen, Anmeldungen, Nachrichten, Favoriten und Bewertungen werden gelöscht.', 'Zurücksetzen', () => {
      state = freshState(); query = ''; syncQuery(null); save(); refreshTabs(); fitRadius(); toast('Demo zurückgesetzt', 'refresh');
    })
  };
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-act]');
    if (!t || t.disabled) return;
    const fn = ACT[t.dataset.act];
    if (fn) { e.preventDefault(); fn(t, e); }
  });

  /* =====================================================================
     iOS-Viewport (Tastatur) & Start
     ===================================================================== */
  function fitViewport() {
    const vv = window.visualViewport;
    const h = vv ? vv.height : window.innerHeight;
    document.documentElement.style.setProperty('--app-h', `${h}px`);
    const app = $('#app');
    app.style.transform = vv && vv.offsetTop > 0 ? `translateY(${vv.offsetTop}px)` : '';
  }
  if (window.visualViewport) {
    visualViewport.addEventListener('resize', fitViewport);
    visualViewport.addEventListener('scroll', fitViewport);
  }
  window.addEventListener('resize', fitViewport);
  fitViewport();

  showTab('karte'); // zuerst sichtbar machen, damit Leaflet die Kartengröße kennt
  buildMapTab();
  buildListe();
  refreshTabs();
  // Status alle 30 s aktualisieren (z. B. wenn ein Slot endet)
  setInterval(() => { if (!$('#sheet-layer').classList.contains('open')) { updateMap(); renderMapList(); } }, 30000);

  setTimeout(() => {
    dismissSplash();
    if (map) { if (map.resize) map.resize(); else if (map.invalidateSize) map.invalidateSize(); }
  }, 900);
})();
