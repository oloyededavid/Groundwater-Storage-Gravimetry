/* Interactive map and chart for the study page. Reads data/grace_cells.json (storage trend per 1-degree GRACE cell)
   and data/storage_monthly.json (monthly series for the Lake Chad sink catchment). No numbers are typed here. */
(() => {
    'use strict';
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs = {}, text) => {
        const e = document.createElementNS(NS, tag);
        Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
        if (text != null) e.textContent = text;
        return e;
    };
    const fmt = v => (v == null ? 'no value' : `${v > 0 ? '+' : ''}${v.toFixed(1)}`);
    const diverge = (v, lim) => {
        const x = Math.max(-1, Math.min(1, v / lim));
        const neg = [178, 24, 43], mid = [247, 247, 247], pos = [33, 102, 172];
        const to = x < 0 ? neg : pos, a = Math.abs(x);
        return `rgb(${mid.map((c, i) => Math.round(c + (to[i] - c) * a)).join(',')})`;
    };

    const mapBox = document.getElementById('gr-map');
    const chartBox = document.getElementById('gr-chart');
    if (!mapBox || !chartBox) return;
    const readout = document.getElementById('gr-readout');

    Promise.all([fetch('data/grace_cells.json').then(r => r.json()), fetch('data/storage_monthly.json').then(r => r.json())])
        .then(([cells, series]) => { drawMap(cells); drawChart(series); })
        .catch(() => { mapBox.textContent = 'The data did not load.'; });

    function drawMap(d) {
        const cs = d.cells.filter(c => c.trend != null);
        const lons = cs.map(c => c.lon), lats = cs.map(c => c.lat), h = d.cell_deg / 2;
        const x0 = Math.min(...lons) - h, x1 = Math.max(...lons) + h, y0 = Math.min(...lats) - h, y1 = Math.max(...lats) + h;
        const W = 640, s = W / (x1 - x0), H = Math.round((y1 - y0) * s);
        const px = lon => (lon - x0) * s, py = lat => (y1 - lat) * s;
        const lim = Math.max(...cs.map(c => Math.abs(c.trend)));
        const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': 'Map of the storage trend in each GRACE cell. Select a cell for its value.' });
        cs.forEach(c => {
            const r = el('rect', { x: px(c.lon - h).toFixed(1), y: py(c.lat + h).toFixed(1), width: (2 * h * s).toFixed(1), height: (2 * h * s).toFixed(1),
                fill: diverge(c.trend, lim), class: 'gr-cell', tabindex: '0', role: 'button',
                'aria-label': `Cell centred ${c.lat.toFixed(1)}° N, ${c.lon.toFixed(1)}° E: ${fmt(c.trend)} mm per year` });
            const show = () => { readout.textContent = `Cell centred ${c.lat.toFixed(1)}° N, ${c.lon.toFixed(1)}° E: ${fmt(c.trend)} mm per year, 2002–2026.`; };
            r.addEventListener('mouseenter', show); r.addEventListener('focus', show); r.addEventListener('click', show);
            svg.append(r);
        });
        d.domains.features.forEach((f, i) => {
            const rings = f.geometry.type === 'Polygon' ? [f.geometry.coordinates[0]] : f.geometry.coordinates.map(p => p[0]);
            rings.forEach(ring => svg.append(el('path', { d: 'M' + ring.map(p => `${px(p[0]).toFixed(1)},${py(p[1]).toFixed(1)}`).join('L') + 'Z',
                class: i === 0 ? 'gr-dom' : 'gr-dom2', 'aria-hidden': 'true' })));
        });
        mapBox.append(svg);
        document.getElementById('gr-lim-lo').textContent = `${(-lim).toFixed(0)}`;
        document.getElementById('gr-lim-hi').textContent = `+${lim.toFixed(0)} mm per year`;
        document.getElementById('gr-bar').style.background = `linear-gradient(90deg, ${[-1, -0.5, 0, 0.5, 1].map(v => diverge(v * lim, lim)).join(',')})`;
    }

    function drawChart(d) {
        const rows = d.rows;
        const SER = [
            { key: 'tws_mm_anom', label: 'GRACE total storage', cls: 'gr-s1', on: true },
            { key: 'res_gldas', label: 'Storage minus soil water (GLDAS)', cls: 'gr-s2', on: true },
            { key: 'res_tc', label: 'Storage minus soil water (TerraClimate, to 2021)', cls: 'gr-s3', on: false },
            { key: 'sm_gldas_anom', label: 'Soil water (GLDAS)', cls: 'gr-s4', on: false },
        ];
        const t = m => { const [y, mo] = m.split('-').map(Number); return y + (mo - 0.5) / 12; };
        const W = 720, H = 300, L = 48, R = 12, T = 12, B = 28;
        const xs = rows.map(r => t(r.month));
        const allv = rows.flatMap(r => SER.map(s => r[s.key]).filter(v => v != null));
        const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(0, ...allv), ymax = Math.max(...allv);
        const X = v => L + (v - xmin) / (xmax - xmin) * (W - L - R), Y = v => T + (ymax - v) / (ymax - ymin) * (H - T - B);
        const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Monthly storage anomalies for the Lake Chad sink catchment' });
        for (let y = Math.ceil(ymin / 100) * 100; y <= ymax; y += 100) {
            svg.append(el('line', { x1: L, x2: W - R, y1: Y(y), y2: Y(y), class: y === 0 ? 'gr-zero' : 'gr-grid' }));
            svg.append(el('text', { x: L - 6, y: Y(y) + 4, class: 'gr-tick', 'text-anchor': 'end' }, `${y}`));
        }
        for (let yr = Math.ceil(xmin / 4) * 4; yr <= xmax; yr += 4) svg.append(el('text', { x: X(yr), y: H - 8, class: 'gr-tick', 'text-anchor': 'middle' }, `${yr}`));
        const lines = {};
        SER.forEach(s => {
            // break the line wherever a month is missing
            let dpath = '', prev = null;
            rows.forEach((r, i) => {
                const v = r[s.key];
                if (v == null) { prev = null; return; }
                const gap = prev != null && xs[i] - xs[prev] > 1.5 / 12;
                dpath += `${prev == null || gap ? 'M' : 'L'}${X(xs[i]).toFixed(1)},${Y(v).toFixed(1)}`;
                prev = i;
            });
            const p = el('path', { d: dpath, class: `gr-line ${s.cls}` });
            if (!s.on) p.style.display = 'none';
            svg.append(p);
            lines[s.key] = p;
        });
        chartBox.append(svg);
        const bar = document.getElementById('gr-toggles');
        SER.forEach(s => {
            const b = document.createElement('button');
            b.type = 'button'; b.className = `gr-btn ${s.cls}`; b.textContent = s.label; b.setAttribute('aria-pressed', String(s.on));
            b.addEventListener('click', () => {
                const on = b.getAttribute('aria-pressed') !== 'true';
                b.setAttribute('aria-pressed', String(on));
                lines[s.key].style.display = on ? '' : 'none';
            });
            bar.append(b);
        });
    }
})();
