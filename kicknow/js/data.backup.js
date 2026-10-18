/* KickNow – Demo-Daten für München
 * Alle Daten sind fiktiv. Belegungen, Spiele, Chats und Bewertungen werden
 * deterministisch (seeded) erzeugt, damit die Demo bei jedem Laden gleich aussieht.
 */
(function () {
  'use strict';

  /* ---------- Seeded Zufall ---------- */
  function xmur3(str) {
    let h = 1779033703 ^ str.length;
    for (let i = 0; i < str.length; i++) {
      h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }
    return function () {
      h = Math.imul(h ^ (h >>> 16), 2246822507);
      h = Math.imul(h ^ (h >>> 13), 3266489909);
      return (h ^= h >>> 16) >>> 0;
    };
  }
  function rng(seed) {
    let a = xmur3(String(seed))();
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const pick = (r, a) => a[Math.floor(r() * a.length)];
  const randInt = (r, a, b) => a + Math.floor(r() * (b - a + 1));
  function shuffle(r, arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(r() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  /* ---------- Nutzer & Standort ---------- */
  const USER = {
    id: 'me', name: 'Louis Gnaier', short: 'Louis G.', first: 'Louis', handle: '@louis_87',
    age: 24, position: 'Mittelfeld', level: 'Hobby', color: '#103B2F',
    lvl: 2, xp: 6, xpMax: 10
  };

  // Simulierter aktueller Standort (Maxvorstadt, nahe TU München)
  const USER_LOCATION = { lat: 48.1497, lng: 11.5679, label: 'Maxvorstadt, München' };

  /* ---------- Plätze ---------- */
  const PITCHES = [
    { id: 'p1', name: 'Nordbad-Sportanlage', surface: 'Rasenplatz', cage: false, size: [105, 68], lat: 48.1608, lng: 11.5660,
      address: 'Schleißheimer Str. 142', district: 'Schwabing-West', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: true, umkleide: true, toiletten: true }, maxPlayers: 14, rating: 4.3, ratingCount: 24,
      desc: 'Großer, gepflegter Naturrasen direkt neben dem Nordbad. Abends unter Flutlicht, unter der Woche meist ab 17 Uhr frei.' },
    { id: 'p2', name: 'Käfigplatz Giesing', surface: 'Kunstrasen', cage: true, size: [20, 13], lat: 48.1172, lng: 11.5800,
      address: 'Tegernseer Landstr. 75', district: 'Obergiesing', access: 'Öffentlich', now: 'spiel',
      amenities: { flutlicht: true, umkleide: false, toiletten: false }, maxPlayers: 8, rating: 4.1, ratingCount: 12,
      desc: 'Kompakter Soccer-Käfig mit Banden – perfekt für schnelle 4-gegen-4-Spiele. Ball bleibt immer im Spiel.' },
    { id: 'p3', name: 'Westpark Bolzplatz', surface: 'Kunstrasen', cage: false, size: [28, 16], lat: 48.1222, lng: 11.5195,
      address: 'Westendstr. 305', district: 'Sendling-Westpark', access: 'Öffentlich', now: 'belegt',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 10, rating: 4.6, ratingCount: 37,
      desc: 'Beliebter Kunstrasen-Bolzplatz im Westpark mit festen Toren. Am Wochenende gut besucht.' },
    { id: 'p4', name: 'Maßmannpark Bolzplatz', surface: 'Hartplatz', cage: true, size: [40, 25], lat: 48.1532, lng: 11.5598,
      address: 'Heßstraße 26', district: 'Maxvorstadt', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: false, umkleide: false, toiletten: false }, maxPlayers: 10, rating: 3.8, ratingCount: 19,
      desc: 'Eingezäunter Hartplatz mitten in der Maxvorstadt. Kurzer Weg von der Uni – ideal für die Mittagspause.' },
    { id: 'p5', name: 'Englischer Garten – Hirschau', surface: 'Rasenplatz', cage: false, size: [60, 40], lat: 48.1665, lng: 11.6015,
      address: 'Gyßlingstraße 15', district: 'Schwabing', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 14, rating: 4.5, ratingCount: 52,
      desc: 'Große Wiese mit mobilen Toren im Norden des Englischen Gartens. Im Sommer jeden Abend offene Runden.' },
    { id: 'p6', name: 'Luitpoldpark Bolzplatz', surface: 'Rasenplatz', cage: false, size: [50, 30], lat: 48.1712, lng: 11.5703,
      address: 'Brunnerstraße 2', district: 'Schwabing-West', access: 'Öffentlich', now: 'spiel',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 12, rating: 4.2, ratingCount: 21,
      desc: 'Ruhig gelegener Rasenplatz am Rand des Luitpoldparks. Tore mit Netzen, leichtes Gefälle zur Nordseite.' },
    { id: 'p7', name: 'ZHS Kunstrasen', surface: 'Kunstrasen', cage: false, size: [105, 68], lat: 48.1786, lng: 11.5480,
      address: 'Connollystraße 32', district: 'Olympiapark', access: 'Mit Anmeldung', now: 'belegt',
      amenities: { flutlicht: true, umkleide: true, toiletten: true }, maxPlayers: 16, rating: 4.7, ratingCount: 64,
      desc: 'Moderner Kunstrasen am Zentralen Hochschulsport. Außerhalb der Kurszeiten für Studierende buchbar.' },
    { id: 'p8', name: 'Hirschgarten Bolzplatz', surface: 'Rasenplatz', cage: false, size: [70, 45], lat: 48.1527, lng: 11.5142,
      address: 'De-la-Paz-Straße 2', district: 'Neuhausen-Nymphenburg', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 14, rating: 4.4, ratingCount: 31,
      desc: 'Weitläufiger Rasen neben dem Biergarten – nach dem Spiel direkt auf ein Radler.' },
    { id: 'p9', name: 'Bavariapark Soccer-Käfig', surface: 'Kunstrasen', cage: true, size: [30, 15], lat: 48.1360, lng: 11.5455,
      address: 'Theresienhöhe 15', district: 'Schwanthalerhöhe', access: 'Öffentlich', now: 'spiel',
      amenities: { flutlicht: true, umkleide: false, toiletten: false }, maxPlayers: 10, rating: 4.0, ratingCount: 15,
      desc: 'Soccer-Court mit Kunstrasen und Flutlicht bis 22 Uhr, direkt hinter der Theresienwiese.' },
    { id: 'p10', name: 'Arnulfpark Kleinfeld', surface: 'Kunstrasen', cage: false, size: [40, 20], lat: 48.1437, lng: 11.5395,
      address: 'Luise-Ullrich-Straße 6', district: 'Maxvorstadt', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: true, umkleide: false, toiletten: false }, maxPlayers: 10, rating: 4.3, ratingCount: 18,
      desc: 'Neuer Kleinfeldplatz im Arnulfpark mit Ballfangzäunen und Flutlicht.' },
    { id: 'p11', name: 'Leopoldpark Bolzplatz', surface: 'Hartplatz', cage: false, size: [35, 20], lat: 48.1610, lng: 11.5845,
      address: 'Leopoldstraße 53', district: 'Schwabing', access: 'Öffentlich', now: 'belegt',
      amenities: { flutlicht: false, umkleide: false, toiletten: false }, maxPlayers: 10, rating: 3.6, ratingCount: 9,
      desc: 'Kleiner Hartplatz im Leopoldpark. Nachmittags oft Schulsport, abends frei.' },
    { id: 'p12', name: 'Sportpark Haidhausen', surface: 'Kunstrasen', cage: false, size: [90, 60], lat: 48.1285, lng: 11.5978,
      address: 'Weißenburger Str. 40', district: 'Haidhausen', access: 'Vereinsgelände', now: 'frei',
      amenities: { flutlicht: true, umkleide: true, toiletten: true }, maxPlayers: 16, rating: 4.4, ratingCount: 27,
      desc: 'Vereinsanlage mit großem Kunstrasen. Freie Zeiten können über KickNow reserviert werden.' },
    { id: 'p13', name: 'Flaucher Bolzwiese', surface: 'Rasenplatz', cage: false, size: [80, 50], lat: 48.1108, lng: 11.5555,
      address: 'Isarauen beim Flaucher', district: 'Thalkirchen', access: 'Öffentlich', now: 'spiel',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 14, rating: 4.8, ratingCount: 73,
      desc: 'Kultwiese an der Isar. Im Sommer täglich offene Spiele – danach ab ins Wasser.' },
    { id: 'p14', name: 'Sportanlage Dantestraße', surface: 'Rasenplatz', cage: false, size: [100, 64], lat: 48.1640, lng: 11.5280,
      address: 'Dantestraße 14', district: 'Neuhausen', access: 'Vereinsgelände', now: 'frei',
      amenities: { flutlicht: true, umkleide: true, toiletten: true }, maxPlayers: 16, rating: 4.2, ratingCount: 33,
      desc: 'Klassischer Großfeld-Rasen neben dem Dantestadion. Umkleiden mit Duschen vorhanden.' },
    { id: 'p15', name: 'Ostpark Fußballwiese', surface: 'Rasenplatz', cage: false, size: [90, 60], lat: 48.1125, lng: 11.6430,
      address: 'Staudinger Straße 17', district: 'Ramersdorf-Perlach', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: false, umkleide: false, toiletten: true }, maxPlayers: 14, rating: 4.2, ratingCount: 16,
      desc: 'Große Wiese im Ostpark mit zwei Toren. Selten überfüllt.' },
    { id: 'p16', name: 'Petuelpark Käfig', surface: 'Kunstrasen', cage: true, size: [25, 15], lat: 48.1782, lng: 11.5720,
      address: 'Petuelring 42', district: 'Milbertshofen', access: 'Öffentlich', now: 'frei',
      amenities: { flutlicht: true, umkleide: false, toiletten: false }, maxPlayers: 8, rating: 4.5, ratingCount: 22,
      desc: 'Moderner Soccer-Käfig über dem Petueltunnel. Gute Banden, Flutlicht bis 22 Uhr.' }
  ];

  /* ---------- Spieler ---------- */
  const PLAYER_BASE = [
    ['Max Schneider', 27], ['Lena Kraus', 25], ['Jonas Weber', 31], ['Ali Yılmaz', 23], ['Sophie Bauer', 22],
    ['Lukas Hofmann', 29], ['Mehmet Demir', 34], ['Anna Fischer', 26], ['Paul Wagner', 20], ['Leon Becker', 24],
    ['Emma Schulz', 28], ['Felix Wolf', 33], ['Noah Richter', 19], ['Mia Klein', 24], ['Elias Neumann', 30],
    ['Luca Rossi', 27], ['Tim Schwarz', 36], ['Julian Zimmermann', 25], ['Hannah Braun', 23], ['David Krüger', 32],
    ['Niklas Hartmann', 21], ['Sara Lange', 29], ['Moritz Werner', 26], ['Ben Schmitt', 22], ['Finn Lehmann', 20],
    ['Kerem Aydın', 28], ['Laura Maier', 27], ['Tobias Huber', 38], ['Jakob Brunner', 24], ['Marie Gruber', 21],
    ['Samuel Okafor', 26], ['Ivan Petrović', 30]
  ];
  const POSITIONS = ['Torwart', 'Abwehr', 'Abwehr', 'Mittelfeld', 'Mittelfeld', 'Sturm'];
  const LEVELS_PLAYER = ['Anfänger', 'Hobby', 'Hobby', 'Fortgeschritten', 'Vereinsspieler'];
  const AVATAR_COLORS = ['#2E7D5B', '#5F86A2', '#C3875A', '#8467AE', '#C26464', '#3F8F8F', '#A8902F', '#55648A', '#6F9650', '#A0618A'];
  const PLAYERS = PLAYER_BASE.map(([name, age], i) => {
    const r = rng('player' + i);
    const parts = name.split(' ');
    return {
      id: 'u' + (i + 1), name, first: parts[0], short: parts[0] + ' ' + parts[1][0] + '.', age,
      position: pick(r, POSITIONS), level: pick(r, LEVELS_PLAYER),
      games: randInt(r, 4, 120), color: AVATAR_COLORS[i % AVATAR_COLORS.length]
    };
  });

  /* ---------- Zeitslots ---------- */
  // 9 Slots à 90 Minuten: 08:30 … 20:30–22:00
  const SLOT_STARTS = [510, 600, 690, 780, 870, 960, 1050, 1140, 1230];
  const SLOT_LEN = 90;
  const BUSY_LABELS = ['Training (Verein)', 'Spiel (Verein)', 'Schulsport', 'Privat gebucht', 'Jugendtraining'];
  const LEVELS = ['Locker', 'Mittel', 'Ambitioniert'];

  const ORG_LINES = [
    'Hey Leute! Wir kicken um {time} – Leibchen bringe ich mit 👕',
    'Wir sind aktuell {n} Leute und suchen noch Verstärkung 💪',
    'Lockeres Spiel, jeder ist willkommen. Bitte pünktlich sein!',
    'Bin 10 Minuten früher da und stelle schon mal die Tore auf.',
    'Wir spielen je nach Anzahl 5 gegen 5 oder 6 gegen 6. Kommt gern vorbei!'
  ];
  const OTHER_LINES = [
    'Bin dabei 👍', 'Bringe noch einen Ball mit ⚽', 'Komme direkt von der Arbeit, kann 5 Min. später werden.',
    'Wetter sieht gut aus ☀️', 'Hat jemand eine Pumpe dabei?', 'Ich kann helle Shirts mitbringen.',
    'Super, freu mich!', 'Ist der Platz nass? Stollen oder Multinocken?', 'Ich bin auch da 🙌',
    'Nehme noch meinen Kumpel mit, falls das ok ist?', 'Wer hat Lust, danach noch was trinken zu gehen? 🍻'
  ];
  const ORG_REPLIES = ['Klar, gerne!', 'Multinocken reichen locker.', 'Passt! 👌', 'Sehr gut, danke!'];

  function genMessages(r, game, isToday) {
    const msgs = [];
    const org = game.organizer;
    const firstAgo = isToday ? randInt(r, 90, 360) : randInt(r, 300, 2400);
    msgs.push({
      from: org,
      text: pick(r, ORG_LINES).replace('{time}', fmt(game.start)).replace('{n}', game.participants.length + game.extra),
      ago: firstAgo
    });
    const others = game.participants.filter(p => p !== org);
    const n = Math.min(others.length, randInt(r, 1, 4));
    let ago = firstAgo;
    const lines = shuffle(r, OTHER_LINES);
    for (let i = 0; i < n; i++) {
      ago = Math.max(3, Math.round(ago * (0.35 + r() * 0.4)));
      const line = lines[i];
      msgs.push({ from: others[i], text: line, ago });
      if (/\?/.test(line) && r() < 0.8) {
        ago = Math.max(2, ago - randInt(r, 1, 4));
        msgs.push({ from: org, text: pick(r, ORG_REPLIES), ago });
      }
    }
    return msgs;
  }
  function fmt(m) { return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); }

  function genGame(p, slot, isToday) {
    const r = rng('game' + slot.id);
    const max = p.maxPlayers;
    const people = shuffle(r, PLAYERS.map(x => x.id));
    const total = randInt(r, 3, max - 2);
    const extra = total > 4 && r() < 0.35 ? 1 : 0;
    const participants = people.slice(0, total - extra);
    const game = {
      type: 'game', organizer: participants[0], participants, extra, maxPlayers: max,
      level: pick(r, LEVELS), open: true, start: slot.start
    };
    game.messages = genMessages(r, game, isToday);
    return game;
  }

  /**
   * Erzeugt die Belegung eines Platzes für einen Tag.
   * curIdx >= 0 bedeutet "heute": Der aktuelle Slot wird passend zum Demo-Status des Platzes gesetzt.
   */
  function genDay(p, dk, curIdx) {
    const r = rng(p.id + dk);
    const slots = SLOT_STARTS.map(() => {
      const x = r();
      if (x < 0.46) return { type: 'free' };
      if (x < 0.72) return { type: 'game' };
      return { type: 'busy', label: pick(r, BUSY_LABELS) };
    });
    if (curIdx >= 0) {
      const set = (i, v) => { if (i < slots.length) slots[i] = v; };
      const busy = { type: 'busy', label: pick(r, BUSY_LABELS.slice(0, 3)) };
      if (p.now === 'frei') { set(curIdx, { type: 'free' }); set(curIdx + 1, { type: 'free' }); set(curIdx + 2, { type: 'game' }); }
      if (p.now === 'spiel') { set(curIdx, { type: 'game' }); }
      if (p.now === 'belegt') { set(curIdx, busy); set(curIdx + 1, { type: 'game' }); }
    }
    return slots.map((s, i) => {
      const slot = Object.assign({}, s, {
        idx: i, start: SLOT_STARTS[i], end: SLOT_STARTS[i] + SLOT_LEN, dk, pitchId: p.id, id: `${p.id}_${dk}_${i}`
      });
      return slot.type === 'game' ? Object.assign(slot, genGame(p, slot, curIdx >= 0)) : slot;
    });
  }

  /* ---------- Bewertungen ---------- */
  const REVIEW_TEXTS = {
    5: ['Super Platz, guter Zustand und oft frei.', 'Top gepflegter Rasen, die Tore haben sogar Netze!',
      'Meine Lieblingswiese in München – abends immer Leute zum Kicken da.', 'Sehr nette Community hier, man findet immer ein Team.',
      'Flutlicht funktioniert einwandfrei, perfekt nach Feierabend.'],
    4: ['Platz ist top, aber manchmal etwas viel los.', 'Guter Belag, nur die Tore wackeln etwas.',
      'Schöne Lage, nur am Wochenende schwer einen freien Slot zu bekommen.', 'Solider Platz, gerne wieder.'],
    3: ['Okay für einen Kick nach der Arbeit, Linien kaum noch zu sehen.', 'Boden recht hart, bei Regen rutschig.',
      'Ganz in Ordnung, aber keine Toiletten in der Nähe.'],
    2: ['Tore ohne Netze und viele Scherben am Rand – schade.', 'Oft vom Verein belegt, obwohl als frei angezeigt.'],
    1: ['Leider komplett zugewachsen, kaum bespielbar.']
  };
  const TAGS_BY_STARS = {
    5: ['Belag: Sehr gut', 'Flutlicht: Ja', 'Sauber'], 4: ['Belag: Gut', 'Oft voll'], 3: ['Belag: Okay'],
    2: ['Belag: Schlecht'], 1: ['Belag: Schlecht']
  };

  const reviewCache = {};
  function genReviews(p) {
    if (reviewCache[p.id]) return reviewCache[p.id];
    const r = rng('rev' + p.id);
    const dist = [0, 0, 0, 0, 0];
    for (let i = 0; i < p.ratingCount; i++) {
      const noise = (r() + r() + r() - 1.5) * 1.4;
      const v = Math.min(5, Math.max(1, Math.round(p.rating + noise)));
      dist[v - 1]++;
    }
    const people = shuffle(r, PLAYERS.map(x => x.id));
    const n = Math.min(p.ratingCount, randInt(r, 3, 6));
    const reviews = [];
    const texts = {};
    for (const k in REVIEW_TEXTS) texts[k] = shuffle(r, REVIEW_TEXTS[k]);
    let agoDays = randInt(r, 1, 6);
    for (let i = 0; i < n; i++) {
      // Bewertung proportional zur Verteilung ziehen
      let x = r() * p.ratingCount, stars = 5;
      for (let s = 5; s >= 1; s--) { x -= dist[s - 1]; if (x < 0) { stars = s; break; } }
      const tags = [pick(r, TAGS_BY_STARS[stars])];
      if (p.amenities.flutlicht && r() < 0.5) tags.push('Flutlicht: Ja');
      // Texte nicht doppelt verwenden; wenn eine Sternekategorie aufgebraucht ist, nur Sterne ohne Text
      reviews.push({ from: people[i], stars, text: texts[stars].shift() || '', agoDays, tags: [...new Set(tags)] });
      agoDays += randInt(r, 3, 40);
    }
    return (reviewCache[p.id] = { dist, reviews });
  }

  window.KN = {
    rng, pick, randInt, shuffle,
    USER, USER_LOCATION, PITCHES, PLAYERS, SLOT_STARTS, SLOT_LEN, LEVELS,
    genDay, genReviews
  };
})();
