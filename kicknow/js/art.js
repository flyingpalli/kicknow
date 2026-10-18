/* KickNow – Icons und generierte Platz-Illustrationen */
(function () {
  'use strict';

  /* ---------- Icons (Strichstärke 1.8, 24er Raster) ---------- */
  const P = {
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>',
    sliders: '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2.2"/><circle cx="9" cy="17" r="2.2"/>',
    pin: '<path d="M12 21.5s-7-6.3-7-11.8a7 7 0 0 1 14 0c0 5.5-7 11.8-7 11.8z"/><circle cx="12" cy="9.7" r="2.6"/>',
    list: '<rect x="5" y="3.5" width="14" height="17.5" rx="2.2"/><path d="M9 3.5v-1h6v1M9 9h6M9 13h6M9 17h3.5"/>',
    signup: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.2"/><path d="M3.5 10h17M8 3v4M16 3v4M9 15.2l2 2 4-4"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4.5 21c0-4 3.4-6.5 7.5-6.5s7.5 2.5 7.5 6.5"/>',
    users: '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6M16 5a3.5 3.5 0 0 1 0 7M18.2 14.4c2 .8 3.3 2.8 3.3 5.6"/>',
    arrowLeft: '<path d="M20 12H4.5M10.5 5.5 4 12l6.5 6.5"/>',
    chevronLeft: '<path d="m15 5-7 7 7 7"/>',
    chevronRight: '<path d="m9 5.5 6.5 6.5L9 18.5"/>',
    chevronDown: '<path d="m6 9 6 6 6-6"/>',
    heart: '<path d="M12 20.5S3.5 15.4 3.5 9.3A4.8 4.8 0 0 1 12 6.4a4.8 4.8 0 0 1 8.5 2.9c0 6.1-8.5 11.2-8.5 11.2z"/>',
    star: '<path d="m12 3.2 2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.7 10.7c.7.6 1.2 1.4 1.2 2.3h5c0-.9.5-1.7 1.2-2.3A6 6 0 0 0 12 3z"/>',
    hanger: '<path d="M10 6.2a2 2 0 1 1 2.6 1.9c-.4.1-.6.5-.6.9V10M12 10l-8.4 6.1A1.2 1.2 0 0 0 4.3 18.3h15.4a1.2 1.2 0 0 0 .7-2.2L12 10"/>',
    wc: '<circle cx="7" cy="4.8" r="1.8"/><circle cx="17" cy="4.8" r="1.8"/><path d="M5 9h4v6.5H8V21H6v-5.5H5zM17 9l3 7.5h-2V21h-2v-4.5h-2z"/>',
    door: '<path d="M6 21V4.2c0-.7.5-1.2 1.2-1.2h9.6c.7 0 1.2.5 1.2 1.2V21M3.5 21h17M14.5 12.2v.1"/>',
    calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    nav: '<path d="M20.5 3.5 3.5 10.6l7.2 2.7 2.7 7.2z" fill="currentColor"/>',
    send: '<path d="M21 3 10.2 13.8M21 3l-6.8 18-4-7.2L3 9.8z"/>',
    check: '<path d="m5 12.5 4.5 4.5L19.5 7"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    chat: '<path d="M20.5 11.5a8 8 0 0 1-11.7 7.1L3.5 20l1.4-5A8 8 0 1 1 20.5 11.5z"/><path d="M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01" stroke-width="2.6"/>',
    locate: '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2.2" fill="currentColor"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
    pitch: '<rect x="2.5" y="5.5" width="19" height="13" rx="1.2"/><path d="M12 5.5v13"/><circle cx="12" cy="12" r="2.6"/><path d="M2.5 9.2h2.8v5.6H2.5M21.5 9.2h-2.8v5.6h2.8"/>',
    ball: '<circle cx="12" cy="12" r="9"/><path d="m12 7.3 3.6 2.6-1.4 4.2H9.8L8.4 9.9zM12 3v4.3M15.6 9.9l4.6-1.5M14.2 14.1l2.8 3.9M9.8 14.1 7 18M8.4 9.9 3.8 8.4"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M5.5 7l1 13h11l1-13M9 7V4h6v3"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.6-4.5L4 8M4 4v4h4M4 13a8 8 0 0 0 14.6 4.5L20 16M20 20v-4h-4"/>',
    info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.1"/>',
    bell: '<path d="M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 2h-15zM10 21h4"/>',
    flag: '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'
  };
  window.icon = function (name, cls) {
    return `<svg class="ic ${cls || ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ''}</svg>`;
  };

  /* ---------- Platz-Illustration (als Foto-Ersatz) ---------- */
  const imgCache = {};
  const f = n => n.toFixed(1);

  window.pitchImage = function (p) {
    if (imgCache[p.id]) return imgCache[p.id];
    const r = window.KN.rng('img' + p.id);
    const W = 400, H = 240, hz = 116 + Math.round(r() * 10);
    const evening = r() < 0.3;
    const sky1 = evening ? '#f2cfa6' : '#b6d4ea', sky2 = evening ? '#f8eedf' : '#edf4f2';
    const hard = p.surface === 'Hartplatz', turf = p.surface === 'Kunstrasen';
    const g1 = hard ? '#b56d47' : turf ? '#3c9853' : '#5a983d';
    const g2 = hard ? '#bf7952' : turf ? '#46a55d' : '#67a549';
    const line = hard ? '#f4ece4' : '#ffffff';

    let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" preserveAspectRatio="xMidYMid slice">`;
    s += `<defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sky1}"/><stop offset="1" stop-color="${sky2}"/></linearGradient>`;
    s += `<linearGradient id="v" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient>`;
    s += `<pattern id="m" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0v9M0 0h9" stroke="#e8eeee" stroke-width=".8" stroke-opacity=".55"/></pattern></defs>`;
    s += `<rect width="${W}" height="${H}" fill="url(#s)"/>`;
    // Wolken
    for (let i = 0; i < 3; i++) {
      const cx = r() * W, cy = 18 + r() * 40;
      s += `<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${f(26 + r() * 30)}" ry="${f(6 + r() * 5)}" fill="#fff" opacity=".55"/>`;
    }
    // Häuser im Hintergrund
    if (r() < 0.55) {
      for (let x = -10; x < W;) {
        const w = 22 + r() * 40, h = 18 + r() * 40;
        s += `<rect x="${f(x)}" y="${f(hz - h - 14)}" width="${f(w)}" height="${f(h + 14)}" fill="${r() < 0.5 ? '#c4cfd3' : '#d3dadb'}"/>`;
        x += w + r() * 36;
      }
    }
    // Baumreihen
    const trees = ['#2f5d34', '#3a6b3c', '#274f2d', '#467a45', '#335f37'];
    for (let row = 0; row < 2; row++) {
      for (let x = -20; x < W + 20; x += 13 + r() * 17) {
        const rad = (row ? 14 : 19) + r() * 15, cy = hz - (row ? 10 : 22) - r() * 12;
        s += `<circle cx="${f(x)}" cy="${f(cy)}" r="${f(rad)}" fill="${trees[Math.floor(r() * trees.length)]}"/>`;
      }
    }
    s += `<rect x="0" y="${hz - 14}" width="${W}" height="16" fill="#2b5331"/>`;
    // Flutlichtmasten
    if (p.amenities.flutlicht) {
      [60 + r() * 40, 290 + r() * 50].forEach(x => {
        s += `<line x1="${f(x)}" y1="${hz}" x2="${f(x)}" y2="26" stroke="#59615f" stroke-width="2.2"/>`;
        s += `<rect x="${f(x - 10)}" y="18" width="20" height="9" rx="1.5" fill="#3b4341"/><rect x="${f(x - 8)}" y="20.5" width="16" height="3.5" rx="1" fill="#f6f1d2"/>`;
      });
    }
    // Ballfangzaun hinten
    s += `<rect x="0" y="${hz - 30}" width="${W}" height="30" fill="url(#m)" opacity=".7"/>`;
    s += `<line x1="0" y1="${hz - 30}" x2="${W}" y2="${hz - 30}" stroke="#7b8784" stroke-width="1.2"/>`;
    for (let x = 0; x <= W; x += 50) s += `<line x1="${x}" y1="${hz - 30}" x2="${x}" y2="${hz}" stroke="#6b7774" stroke-width="1.4"/>`;
    // Boden
    s += `<rect x="0" y="${hz}" width="${W}" height="${H - hz}" fill="${g1}"/>`;
    if (!hard) {
      const vx = 200, vy = hz - 320, t = (hz - vy) / (H - vy);
      for (let i = -12; i < 12; i += 2) {
        const b1 = 200 + i * 38, b2 = b1 + 38;
        const t1 = vx + (b1 - vx) * t, t2 = vx + (b2 - vx) * t;
        s += `<polygon points="${f(t1)},${hz} ${f(t2)},${hz} ${b2},${H} ${b1},${H}" fill="${g2}"/>`;
      }
    } else {
      for (let i = 0; i < 40; i++) s += `<circle cx="${f(r() * W)}" cy="${f(hz + r() * (H - hz))}" r="${f(.6 + r() * 1.4)}" fill="#9c5c3b" opacity=".5"/>`;
    }
    // Linien
    const ft = hz + 8, cy = ft + (H - ft) * 0.48;
    s += `<g fill="none" stroke="${line}" stroke-opacity=".88" stroke-width="2">`;
    s += `<line x1="-10" y1="${ft}" x2="${W + 10}" y2="${ft}"/><line x1="200" y1="${ft}" x2="200" y2="${H}"/>`;
    s += `<ellipse cx="200" cy="${f(cy)}" rx="62" ry="17"/>`;
    s += `<path d="M-10 ${ft + 18} H58 L30 ${ft + 78} H-40"/><path d="M${W + 10} ${ft + 18} H${W - 58} L${W - 30} ${ft + 78} H${W + 40}"/>`;
    s += `</g><circle cx="200" cy="${f(cy)}" r="2.4" fill="${line}"/>`;
    // Tore
    const goal = (x, dir) => {
      const fx = x, bx = x + dir * 16, top = ft - 6;
      return `<polygon points="${fx},${ft + 30} ${fx},${top + 6} ${bx},${top} ${bx},${ft + 14}" fill="#fff" fill-opacity=".22"/>` +
        `<path d="M${fx} ${ft + 30} V${top + 6} L${bx} ${top} V${ft + 14}" fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/>`;
    };
    s += goal(14, 1) + goal(W - 14, -1);
    // Käfig vorne
    if (p.cage) {
      s += `<rect x="0" y="0" width="${W}" height="${H}" fill="url(#m)" opacity=".55"/>`;
      s += `<line x1="0" y1="14" x2="${W}" y2="14" stroke="#4c5552" stroke-width="3"/>`;
      for (let x = 30; x < W; x += 120) s += `<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#4c5552" stroke-width="3.5"/>`;
      s += `<rect x="0" y="${H - 18}" width="${W}" height="18" fill="#3f4744" opacity=".8"/>`;
    }
    s += `<rect width="${W}" height="${H}" fill="url(#v)"/></svg>`;
    return (imgCache[p.id] = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s));
  };
})();
