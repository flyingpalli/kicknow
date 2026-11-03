"""Exports scraped pitches and BFV match occupations to JSON and updates kicknow/js/data.js."""

import os
import json
from typing import List, Dict, Any


def export_json(data: Any, filepath: str, indent: int = 2) -> None:
    """Save data object as formatted JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    print(f"[Exporter] Saved {filepath} ({len(data) if isinstance(data, list) else 1} items).")


def update_kicknow_data_js(pitches: List[Dict[str, Any]], target_data_js: str = "kicknow/js/data.js") -> bool:
    """Generates the complete kicknow/js/data.js bundle with real pitches, realistic club schedules, and BFV matches."""
    if not os.path.exists(os.path.dirname(target_data_js)):
        os.makedirs(os.path.dirname(target_data_js), exist_ok=True)

    pitches_json = json.dumps(pitches, ensure_ascii=False, indent=2)

    js_template = f"""// KickNow - Zentraler Datenbestand & Generierungslogik
// Automatisch generiert durch KickNow Scraper mit BFV-Match-Integration und realistischen Vereins-Trainingszeiten

(function() {{
  'use strict';

  function xmur3(str) {{
    let h = 1779033703 ^ str.length;
    for (let i = 0; i < str.length; i++) {{
      h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }}
    return function() {{
      h = Math.imul(h ^ (h >>> 16), 2246822507);
      h = Math.imul(h ^ (h >>> 13), 3266489909);
      return (h ^= h >>> 16) >>> 0;
    }};
  }}

  function mulberry32(a) {{
    return function() {{
      let t = (a += 0x6D2B79F5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }};
  }}

  function rng(seedStr) {{
    return mulberry32(xmur3(seedStr)());
  }}

  function pick(r, arr) {{
    return arr[Math.floor(r() * arr.length)];
  }}

  function randInt(r, min, max) {{
    return min + Math.floor(r() * (max - min + 1));
  }}

  function shuffle(r, arr) {{
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {{
      const j = Math.floor(r() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }}
    return a;
  }}

  /* ---------- Aktueller Nutzer & Standort ---------- */
  const USER = {{
    id: 'u0',
    name: 'Alex Mayer',
    first: 'Alex',
    short: 'Alex M.',
    handle: '@alex_mayer',
    age: 26,
    position: 'Mittelfeld',
    level: 'Fortgeschritten',
    games: 34,
    lvl: 3,
    xp: 8,
    xpMax: 12,
    color: '#0D5C3A'
  }};

  const USER_LOCATION = {{
    lat: 48.137154,
    lng: 11.576124,
    name: 'Marienplatz, München',
    label: 'Marienplatz, München'
  }};

  const CITIES = {{
    munich: {{ key: 'munich', name: 'München', lat: 48.137154, lng: 11.576124, label: 'Marienplatz, München' }},
    nuremberg: {{ key: 'nuremberg', name: 'Nürnberg', lat: 49.452102, lng: 11.076665, label: 'Hauptmarkt, Nürnberg' }},
    berlin: {{ key: 'berlin', name: 'Berlin', lat: 52.520008, lng: 13.404954, label: 'Alexanderplatz, Berlin' }},
    hamburg: {{ key: 'hamburg', name: 'Hamburg', lat: 53.551086, lng: 9.993682, label: 'Rathausmarkt, Hamburg' }},
    cologne: {{ key: 'cologne', name: 'Köln', lat: 50.937531, lng: 6.960279, label: 'Heumarkt, Köln' }},
    frankfurt: {{ key: 'frankfurt', name: 'Frankfurt', lat: 50.110924, lng: 8.682127, label: 'Römerberg, Frankfurt' }}
  }};

  const MUNICH_LOCATIONS = [
    {{ name: 'Schwabing', lat: 48.1642, lng: 11.5861, desc: 'München-Nord' }},
    {{ name: 'Maxvorstadt', lat: 48.1497, lng: 11.5679, desc: 'Universitätsviertel, München' }},
    {{ name: 'Giesing', lat: 48.1140, lng: 11.5794, desc: 'Obergiesing / Untergiesing' }},
    {{ name: 'Sendling', lat: 48.1188, lng: 11.5394, desc: 'München-Südwest' }},
    {{ name: 'Neuhausen-Nymphenburg', lat: 48.1558, lng: 11.5225, desc: 'München-West' }},
    {{ name: 'Haidhausen', lat: 48.1306, lng: 11.6025, desc: 'Au-Haidhausen, München' }},
    {{ name: 'Pasing', lat: 48.1472, lng: 11.4614, desc: 'Pasing-Obermenzing' }},
    {{ name: 'Bogenhausen', lat: 48.1544, lng: 11.6228, desc: 'München-Nordost' }},
    {{ name: 'Garching bei München', lat: 48.2489, lng: 11.6528, desc: 'Landkreis München (Nord)' }},
    {{ name: 'Unterhaching', lat: 48.0658, lng: 11.6133, desc: 'Landkreis München (Süd)' }},
    {{ name: 'Nürnberg Zentrum', lat: 49.4521, lng: 11.0767, desc: 'Mittelfranken' }},
    {{ name: 'Nürnberg-St. Johannis', lat: 49.4628, lng: 11.0580, desc: 'Nürnberg-Nordwest' }},
    {{ name: 'Nürnberg-Zerzabelshof', lat: 49.4360, lng: 11.1270, desc: 'Nürnberg-Ost' }},
    {{ name: 'Berlin-Kreuzberg', lat: 52.4986, lng: 13.4033, desc: 'Friedrichshain-Kreuzberg, Berlin' }},
    {{ name: 'Berlin-Mitte', lat: 52.5200, lng: 13.4050, desc: 'Berlin Zentrum' }},
    {{ name: 'Berlin-Prenzlauer Berg', lat: 52.5388, lng: 13.4244, desc: 'Pankow, Berlin' }},
    {{ name: 'Berlin-Neukölln', lat: 52.4813, lng: 13.4351, desc: 'Berlin-Südost' }},
    {{ name: 'Berlin-Charlottenburg', lat: 52.5160, lng: 13.3040, desc: 'Berlin-West' }},
    {{ name: 'Hamburg-Eimsbüttel', lat: 53.5755, lng: 9.9515, desc: 'Hamburg' }},
    {{ name: 'Hamburg-Altona', lat: 53.5526, lng: 9.9351, desc: 'Hamburg-West' }},
    {{ name: 'Hamburg-Winterhude', lat: 53.5960, lng: 10.0080, desc: 'Hamburg-Nord' }},
    {{ name: 'Köln-Südstadt', lat: 50.9214, lng: 6.9603, desc: 'Köln-Innenstadt' }},
    {{ name: 'Köln-Ehrenfeld', lat: 50.9510, lng: 6.9180, desc: 'Köln-West' }},
    {{ name: 'Köln-Lindenthal', lat: 50.9280, lng: 6.9120, desc: 'Köln-Südwest' }},
    {{ name: 'Köln-Nippes', lat: 50.9650, lng: 6.9530, desc: 'Köln-Nord' }},
    {{ name: 'Frankfurt-Ostend', lat: 50.1109, lng: 8.7061, desc: 'Frankfurt am Main' }},
    {{ name: 'Frankfurt-Bornheim', lat: 50.1258, lng: 8.7110, desc: 'Frankfurt-Nordost' }},
    {{ name: 'Frankfurt-Sachsenhausen', lat: 50.0990, lng: 8.6850, desc: 'Frankfurt-Süd' }},
    {{ name: 'Frankfurt-Bockenheim', lat: 50.1215, lng: 8.6440, desc: 'Frankfurt-West' }}
  ];

  /* ---------- Scraped Fußballplätze (München & Landkreis + Multi-City) ---------- */
  const PITCHES = {pitches_json};

  /* ---------- Spielerpool ---------- */
  const PLAYER_BASE = [
    ['Maximilian Bauer', 24], ['Lukas Schmidt', 27], ['Felix Weber', 22],
    ['Jonas Müller', 29], ['David Wagner', 25], ['Niklas Fischer', 23],
    ['Tim Becker', 28], ['Leon Hoffmann', 21], ['Paul Schäfer', 26],
    ['Moritz Koch', 30], ['Julian Richter', 24], ['Simon Klein', 27],
    ['Fabian Wolf', 23], ['Jan Neumayer', 25], ['Elias Schwarz', 22],
    ['Tobias Braun', 31], ['Sebastian Zimmermann', 29], ['Philipp Krüger', 26],
    ['Alexander Hof', 28], ['Florian Lang', 24], ['Marco Walter', 27],
    ['Dominik Maier', 25], ['Stefan Huber', 32], ['Christoph Leitner', 28],
    ['Matthias Gruber', 26], ['Daniel Pichler', 23], ['Christian Moser', 29]
  ];
  const POSITIONS = ['Sturm', 'Mittelfeld', 'Abwehr', 'Torwart'];
  const LEVELS_PLAYER = ['Hobby', 'Fortgeschritten', 'Verein'];
  const AVATAR_COLORS = ['#103B2F', '#215243', '#2E4A3E', '#3B6E59', '#1E3F35', '#2A5A4A', '#174D3B'];

  const PLAYERS = PLAYER_BASE.map(([name, age], i) => {{
    const r = rng('p' + i);
    const parts = name.split(' ');
    return {{
      id: 'u' + (i + 1), name, first: parts[0], short: parts[0] + ' ' + parts[1][0] + '.', age,
      position: pick(r, POSITIONS), level: pick(r, LEVELS_PLAYER),
      games: randInt(r, 4, 120), color: AVATAR_COLORS[i % AVATAR_COLORS.length]
    }};
  }});

  /* ---------- Zeitslots (9 Slots á 90 Min) ---------- */
  const SLOT_STARTS = [510, 600, 690, 780, 870, 960, 1050, 1140, 1230];
  const SLOT_LEN = 90;
  const LEVELS = ['Locker', 'Mittel', 'Ambitioniert'];

  const ORG_LINES = [
    'Hey Leute! Wir kicken um {{time}} – Leibchen bringe ich mit 👕',
    'Wir sind aktuell {{n}} Leute und suchen noch Verstärkung 💪',
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

  function genMessages(r, game, isToday) {{
    const msgs = [];
    const org = game.organizer;
    const firstAgo = isToday ? randInt(r, 90, 360) : randInt(r, 300, 2400);
    msgs.push({{
      from: org,
      text: pick(r, ORG_LINES).replace('{{time}}', fmt(game.start)).replace('{{n}}', game.participants.length + game.extra),
      ago: firstAgo
    }});
    const others = game.participants.filter(p => p !== org);
    const n = Math.min(others.length, randInt(r, 1, 4));
    let ago = firstAgo;
    const lines = shuffle(r, OTHER_LINES);
    for (let i = 0; i < n; i++) {{
      ago = Math.max(3, Math.round(ago * (0.35 + r() * 0.4)));
      const line = lines[i];
      msgs.push({{ from: others[i], text: line, ago }});
      if (/\?/.test(line) && r() < 0.8) {{
        ago = Math.max(2, ago - randInt(r, 1, 4));
        msgs.push({{ from: org, text: pick(r, ORG_REPLIES), ago }});
      }}
    }}
    return msgs;
  }}
  function fmt(m) {{ return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); }}

  function genGame(p, slot, isToday) {{
    const r = rng('game' + slot.id);
    const max = p.maxPlayers;
    const people = shuffle(r, PLAYERS.map(x => x.id));
    const total = randInt(r, 3, max - 2);
    const extra = total > 4 && r() < 0.35 ? 1 : 0;
    const participants = people.slice(0, total - extra);
    const game = {{
      type: 'game', organizer: participants[0], participants, extra, maxPlayers: max,
      level: pick(r, LEVELS), open: true, start: slot.start
    }};
    game.messages = genMessages(r, game, isToday);
    return game;
  }}

  /**
   * Erzeugt die Belegung eines Platzes für ein konkretes Datum.
   * Wendet echte BFV-Spiele als 1. Priorität an.
   * Erzeugt realistische, strukturierte Trainingszeiten für Vereinsplätze (BSA/Sportparks)
   * und stellt sicher, dass öffentliche Bolzplätze frei von Vereinszeiten bleiben.
   */
  function genDay(p, dk, curIdx) {{
    const r = rng(p.id + dk);
    const occs = p.occupations || [];
    const occMap = {{}};
    occs.forEach(o => {{
      if (o.date === dk) occMap[o.slot_idx] = o;
    }});

    const dObj = new Date(dk + 'T12:00:00');
    const dayOfWeek = dObj.getDay(); // 0 = So, 1 = Mo, 2 = Di, 3 = Mi, 4 = Do, 5 = Fr, 6 = Sa
    const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
    const isOfficial = (p.access !== 'Öffentlich') || !!p.club;
    const club = p.club || (isOfficial ? 'Heimverein' : null);

    // Di/Do-Rhythmus für geradzahlige Platz-IDs, Mo/Mi-Rhythmus für ungeradzahlige Platz-IDs
    const isDiDo = (p.id.charCodeAt(p.id.length - 1) % 2 === 0);
    const isPrimaryTrainingDay = isDiDo ? (dayOfWeek === 2 || dayOfWeek === 4) : (dayOfWeek === 1 || dayOfWeek === 3);
    const isSecondaryTrainingDay = isDiDo ? (dayOfWeek === 3 || dayOfWeek === 5) : (dayOfWeek === 2 || dayOfWeek === 5);

    const slots = SLOT_STARTS.map((startMin, i) => {{
      // 1. Priorität: Echtes BFV-Spiel auf diesem Platz an diesem Datum und Slot
      if (occMap[i]) {{
        return {{ type: 'busy', label: occMap[i].label, bfvGame: occMap[i] }};
      }}

      // 2. Belegungslogik nach Platzart
      if (isOfficial) {{
        // Offizielle Bezirkssportanlage oder Sportpark mit Fußballverein
        if (!isWeekend) {{
          // Werktage (Montag - Freitag)
          if (i <= 2) {{
            // Vormittag/Mittag (08:30 - 13:00): Schulsport auf städtischen BSAs
            const isBSA = p.name.includes('Bezirkssportanlage') || p.name.includes('BSA');
            if (isBSA && r() < 0.75) {{
              return {{ type: 'busy', label: 'Schulsport (Gymnasium / Realschule)' }};
            }}
            return {{ type: 'free' }};
          }}
          if (i === 3 || i === 4) {{
            // Früher Nachmittag (13:00 - 16:00): Platzpflege oder frei
            if (r() < 0.25) return {{ type: 'busy', label: 'Platzpflege / Freies Vereinstraining' }};
            return {{ type: 'free' }};
          }}
          if (i === 5) {{
            // 16:00 - 17:30: Jugendtraining (D- bis C-Junioren)
            return {{ type: 'busy', label: 'Jugendtraining: ' + club + ' (U11-U15)' }};
          }}
          if (i === 6) {{
            // 17:30 - 19:00: Jugendtraining (B- bis A-Junioren)
            return {{ type: 'busy', label: 'Jugendtraining: ' + club + ' (U17/U19)' }};
          }}
          if (i === 7) {{
            // 19:00 - 20:30: Prime Time Herren 1 bzw. Damen
            if (isPrimaryTrainingDay) {{
              return {{ type: 'busy', label: 'Training: ' + club + ' (1. Mannschaft)' }};
            }} else if (isSecondaryTrainingDay) {{
              return {{ type: 'busy', label: 'Training: ' + club + ' (Damen / U19)' }};
            }} else {{
              // Freitag oder freier Tag
              return r() < 0.4 ? {{ type: 'game' }} : {{ type: 'free' }};
            }}
          }}
          if (i === 8) {{
            // 20:30 - 22:00: Prime Time Herren 2 / Senioren (AH)
            if (isPrimaryTrainingDay) {{
              return {{ type: 'busy', label: 'Training: ' + club + ' (2. Mannschaft / AH)' }};
            }} else if (isSecondaryTrainingDay) {{
              return {{ type: 'busy', label: 'Training: ' + club + ' (Senioren Ü32)' }};
            }} else {{
              return r() < 0.35 ? {{ type: 'game' }} : {{ type: 'free' }};
            }}
          }}
        }} else {{
          // Wochenende (Samstag & Sonntag)
          if (dayOfWeek === 6) {{
            // Samstag
            if (i >= 1 && i <= 3) {{
              // Vormittag/Mittag: Jugend-Punktspiele
              if (r() < 0.65) return {{ type: 'busy', label: 'BFV-Jugendspiel: ' + club + ' U17/U15' }};
              return {{ type: 'free' }};
            }}
            if (i === 4 || i === 5) {{
              // Nachmittag: Herren-/Damenspiele
              if (r() < 0.60) return {{ type: 'busy', label: 'BFV-Ligaspiel: ' + club + ' (Herren)' }};
              if (r() < 0.85) return {{ type: 'game' }};
              return {{ type: 'free' }};
            }}
          }} else if (dayOfWeek === 0) {{
            // Sonntag
            if (i === 2 || i === 3) {{
              // Vormittag/Mittag: 2. Mannschaft
              if (r() < 0.65) return {{ type: 'busy', label: 'BFV-Spiel: ' + club + ' II' }};
              return {{ type: 'free' }};
            }}
            if (i === 4 || i === 5) {{
              // Nachmittag: 1. Mannschaft Hauptspiel
              if (r() < 0.70) return {{ type: 'busy', label: 'BFV-Punktspiel: ' + club + ' I' }};
              if (r() < 0.90) return {{ type: 'game' }};
              return {{ type: 'free' }};
            }}
          }}
          // Randslots am Wochenende
          const x = r();
          if (x < 0.45) return {{ type: 'free' }};
          if (x < 0.75) return {{ type: 'game' }};
          return {{ type: 'free' }};
        }}
      }} else {{
        // Öffentlicher Bolzplatz, Käfig oder Streetcourt (KEIN Vereinstraining!)
        if (i <= 3) {{
          // Vormittags & früher Nachmittag meistens frei
          return r() < 0.85 ? {{ type: 'free' }} : {{ type: 'game' }};
        }}
        // Nachmittags & abends beliebt bei Freizeitkickern
        const x = r();
        if (x < 0.35) return {{ type: 'free' }};
        if (x < 0.75) return {{ type: 'game' }};
        return {{ type: 'busy', label: 'Belegt (Freizeitkicker)' }};
      }}
    }});

    if (curIdx >= 0) {{
      const set = (i, v) => {{ if (i < slots.length && !occMap[i]) slots[i] = v; }};
      const curSlot = slots[curIdx];
      if (occMap[curIdx]) {{
        p.now = 'belegt';
      }} else if (curSlot.type === 'game') {{
        p.now = 'spiel';
      }} else if (curSlot.type === 'busy') {{
        p.now = 'belegt';
      }} else {{
        p.now = 'frei';
        set(curIdx, {{ type: 'free' }});
        set(curIdx + 1, {{ type: 'free' }});
      }}
    }}

    return slots.map((s, i) => {{
      const slot = Object.assign({{}}, s, {{
        idx: i, start: SLOT_STARTS[i], end: SLOT_STARTS[i] + SLOT_LEN, dk, pitchId: p.id, id: p.id + '_' + dk + '_' + i
      }});
      return slot.type === 'game' ? Object.assign(slot, genGame(p, slot, curIdx >= 0)) : slot;
    }});
  }}

  /* ---------- Bewertungen ---------- */
  const REVIEW_TEXTS = {{
    5: ['Super Platz, guter Zustand und oft frei.', 'Top gepflegter Rasen, die Tore haben sogar Netze!',
      'Meine Lieblingswiese in München – abends immer Leute zum Kicken da.', 'Sehr nette Community hier, man findet immer ein Team.',
      'Flutlicht funktioniert einwandfrei, perfekt nach Feierabend.'],
    4: ['Platz ist top, aber manchmal etwas viel los.', 'Guter Belag, nur die Tore wackeln etwas.',
      'Schöne Lage, nur am Wochenende schwer einen freien Slot zu bekommen.', 'Solider Platz, gerne wieder.'],
    3: ['Okay für einen Kick nach der Arbeit, Linien kaum noch zu sehen.', 'Boden recht hart, bei Regen rutschig.',
      'Ganz in Ordnung, aber keine Toiletten in der Nähe.'],
    2: ['Tore ohne Netze und viele Scherben am Rand – schade.', 'Oft vom Verein belegt, obwohl als frei angezeigt.'],
    1: ['Leider komplett zugewachsen, kaum bespielbar.']
  }};
  const TAGS_BY_STARS = {{
    5: ['Belag: Sehr gut', 'Flutlicht: Ja', 'Sauber'], 4: ['Belag: Gut', 'Oft voll'], 3: ['Belag: Okay'],
    2: ['Belag: Schlecht'], 1: ['Belag: Schlecht']
  }};

  const reviewCache = {{}};
  function genReviews(p) {{
    if (reviewCache[p.id]) return reviewCache[p.id];
    const r = rng('rev' + p.id);
    const dist = [0, 0, 0, 0, 0];
    const count = p.ratingCount || 15;
    const rating = p.rating || 4.2;
    for (let i = 0; i < count; i++) {{
      const noise = (r() + r() + r() - 1.5) * 1.4;
      const v = Math.min(5, Math.max(1, Math.round(rating + noise)));
      dist[v - 1]++;
    }}
    const people = shuffle(r, PLAYERS.map(x => x.id));
    const n = Math.min(count, randInt(r, 3, 6));
    const reviews = [];
    const texts = {{}};
    for (const k in REVIEW_TEXTS) texts[k] = shuffle(r, REVIEW_TEXTS[k]);
    let agoDays = randInt(r, 1, 6);
    for (let i = 0; i < n; i++) {{
      let x = r() * count, stars = 5;
      for (let s = 5; s >= 1; s--) {{ x -= dist[s - 1]; if (x < 0) {{ stars = s; break; }} }}
      const tags = [pick(r, TAGS_BY_STARS[stars])];
      if (p.amenities && p.amenities.flutlicht && r() < 0.5) tags.push('Flutlicht: Ja');
      reviews.push({{ from: people[i], stars, text: texts[stars].shift() || '', agoDays, tags: [...new Set(tags)] }});
      agoDays += randInt(r, 3, 40);
    }}
    return (reviewCache[p.id] = {{ dist, reviews }});
  }}

  window.KN = {{
    rng, pick, randInt, shuffle,
    USER, USER_LOCATION, CITIES, MUNICH_LOCATIONS, PITCHES, PLAYERS, SLOT_STARTS, SLOT_LEN, LEVELS,
    genDay, genReviews
  }};
}})();
"""

    with open(target_data_js, "w", encoding="utf-8") as f:
        f.write(js_template)
    print(f"[Exporter] Updated {target_data_js} with {len(pitches)} pitches and real BFV occupations.")
    return True
