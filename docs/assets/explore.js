/* Interactive map and chart for the study page. Reads data/grace_cells.json (straight-line storage trend per 1-degree
   GRACE cell) and data/storage_monthly.json (monthly series for the basin unit). No numbers are typed here. */
(() => {
    'use strict';
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs = {}, text) => {
        const e = document.createElementNS(NS, tag);
        Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
        if (text != null) e.textContent = text;
        return e;
    };
    const minus = s => String(s).replace('-', '−');
    const fmt = v => (v == null ? 'no value' : minus(`${v > 0 ? '+' : ''}${v.toFixed(1)}`));
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

    fetch('data/grace_cells.json').then(r => r.json()).then(drawMap).catch(() => { mapBox.textContent = 'The map data did not load.'; });
    fetch('data/storage_monthly.json').then(r => r.json()).then(d => {
        const draw = () => drawChart(d);
        draw();
        let t;
        window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(draw, 150); });
    }).catch(() => { chartBox.textContent = 'The chart data did not load.'; });

    function drawMap(d) {
        const cs = d.cells.filter(c => c.trend != null);
        const h = d.cell_deg / 2;
        const lons = cs.map(c => c.lon), lats = cs.map(c => c.lat);
        const x0 = Math.min(...lons) - h, x1 = Math.max(...lons) + h, y0 = Math.min(...lats) - h, y1 = Math.max(...lats) + h;
        const W = 640, s = W / (x1 - x0), H = Math.round((y1 - y0) * s);
        const px = lon => (lon - x0) * s, py = lat => (y1 - lat) * s;
        const lim = Math.max(...cs.map(c => Math.abs(c.trend)));
        const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'grid', 'aria-label': 'Storage trend in each GRACE cell. Use the arrow keys to move between cells.' });
        const cols = [...new Set(lons)].sort((a, b) => a - b), rows = [...new Set(lats)].sort((a, b) => b - a);
        const at = new Map(cs.map(c => [`${c.lat},${c.lon}`, c]));
        const rects = new Map();
        const rowG = new Map(rows.map(lat => [lat, el('g', { role: 'row' })]));
        rowG.forEach(g => svg.append(g));
        cs.forEach(c => {
            const r = el('rect', { x: px(c.lon - h).toFixed(1), y: py(c.lat + h).toFixed(1), width: (2 * h * s).toFixed(1), height: (2 * h * s).toFixed(1),
                fill: diverge(c.trend, lim), class: 'gr-cell', tabindex: '-1', role: 'gridcell',
                'aria-label': `Cell centred ${c.lat.toFixed(1)}° N, ${c.lon.toFixed(1)}° E: ${fmt(c.trend)} mm per year` });
            r.addEventListener('click', () => focus(c));
            r.addEventListener('focus', () => show(c));
            r.addEventListener('mouseenter', () => show(c));
            rowG.get(c.lat).append(r);
            rects.set(`${c.lat},${c.lon}`, r);
        });
        const order = [...d.domains.features].sort((a, b) => (a.properties.id === d.main ? 1 : -1));
        order.forEach(f => {
            const rings = f.geometry.type === 'Polygon' ? [f.geometry.coordinates[0]] : f.geometry.coordinates.map(p => p[0]);
            rings.forEach(ring => svg.append(el('path', { d: 'M' + ring.map(p => `${px(p[0]).toFixed(1)},${py(p[1]).toFixed(1)}`).join('L') + 'Z',
                class: f.properties.id === d.main ? 'gr-dom' : 'gr-dom2', 'aria-hidden': 'true' })));
        });
        if (d.lake) {
            svg.append(el('circle', { cx: px(d.lake[0]), cy: py(d.lake[1]), r: 5, class: 'gr-lake', 'aria-hidden': 'true' }));
            svg.append(el('text', { x: px(d.lake[0]) + 8, y: py(d.lake[1]) - 6, class: 'gr-lake-label', 'aria-hidden': 'true' }, 'Lake Chad'));
        }
        mapBox.append(svg);
        let cur = cs.reduce((a, b) => (Math.abs(b.lat - (d.lake ? d.lake[1] : 13)) + Math.abs(b.lon - (d.lake ? d.lake[0] : 14)) <
                                       Math.abs(a.lat - (d.lake ? d.lake[1] : 13)) + Math.abs(a.lon - (d.lake ? d.lake[0] : 14)) ? b : a));
        rects.get(`${cur.lat},${cur.lon}`).setAttribute('tabindex', '0');
        function show(c) { readout.textContent = `Cell centred ${c.lat.toFixed(1)}° N, ${c.lon.toFixed(1)}° E: ${fmt(c.trend)} mm per year, 2002 to 2026.`; }
        function focus(c) {
            rects.get(`${cur.lat},${cur.lon}`).setAttribute('tabindex', '-1');
            cur = c;
            const r = rects.get(`${c.lat},${c.lon}`);
            r.setAttribute('tabindex', '0');
            r.focus();
        }
        svg.addEventListener('keydown', e => {
            const moves = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] };
            if (!moves[e.key]) return;
            e.preventDefault();
            let ri = rows.indexOf(cur.lat), ci = cols.indexOf(cur.lon);
            for (let k = 0; k < 40; k++) {
                ri += moves[e.key][0]; ci += moves[e.key][1];
                if (ri < 0 || ci < 0 || ri >= rows.length || ci >= cols.length) return;
                const c = at.get(`${rows[ri]},${cols[ci]}`);
                if (c) { focus(c); return; }
            }
        });
        document.getElementById('gr-lim-lo').textContent = minus(`-${lim.toFixed(0)}`);
        document.getElementById('gr-lim-hi').textContent = `+${lim.toFixed(0)} mm per year`;
        document.getElementById('gr-bar').style.background = `linear-gradient(90deg, ${[-1, -0.5, 0, 0.5, 1].map(v => diverge(v * lim, lim)).join(',')})`;
        // text alternative: cells that overlap the main area
        const tb = document.getElementById('gr-table');
        if (tb && d.main_cells) {
            const inside = cs.filter(c => d.main_cells.some(m => m[0] === c.lat && m[1] === c.lon)).sort((a, b) => b.trend - a.trend);
            tb.innerHTML = '<table><thead><tr><th scope="col">Latitude</th><th scope="col">Longitude</th><th scope="col">Trend, mm per year</th></tr></thead><tbody>' +
                inside.map(c => `<tr><td>${c.lat.toFixed(1)}° N</td><td>${c.lon.toFixed(1)}° E</td><td>${fmt(c.trend)}</td></tr>`).join('') + '</tbody></table>';
        }
    }

    function drawChart(d) {
        chartBox.textContent = '';
        const rows = d.rows;
        const SER = [
            { key: 'tws_mm_anom', label: 'GRACE total storage', cls: 'gr-s1', on: true },
            { key: 'res_gldas', label: 'Storage minus soil water (GLDAS)', cls: 'gr-s2', on: true },
            { key: 'res_tc', label: 'Storage minus soil water (TerraClimate, to 2021)', cls: 'gr-s3', on: false },
            { key: 'sm_gldas_anom', label: 'Soil water (GLDAS)', cls: 'gr-s4', on: false },
        ];
        const t = m => { const [y, mo] = m.split('-').map(Number); return y + (mo - 0.5) / 12; };
        // draw in screen pixels so text stays readable on phones
        const W = Math.max(300, Math.round(chartBox.clientWidth || 640)), H = Math.round(Math.min(360, Math.max(240, W * 0.55)));
        const L = 56, R = 10, T = 14, B = 44;
        const xs = rows.map(r => t(r.month));
        const allv = rows.flatMap(r => SER.map(s => r[s.key]).filter(v => v != null));
        const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(0, ...allv), ymax = Math.max(...allv);
        const X = v => L + (v - xmin) / (xmax - xmin) * (W - L - R), Y = v => T + (ymax - v) / (ymax - ymin) * (H - T - B);
        const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'img',
            'aria-label': 'Monthly storage anomalies for the basin unit, in millimetres from the 2004 to 2009 mean, 2002 to 2026' });
        svg.append(el('rect', { x: X(2017 + 6 / 12), y: T, width: X(2018 + 5 / 12) - X(2017 + 6 / 12), height: H - T - B, class: 'gr-gap' }));
        const step = (ymax - ymin) > 500 ? 200 : 100;
        for (let y = Math.ceil(ymin / step) * step; y <= ymax; y += step) {
            svg.append(el('line', { x1: L, x2: W - R, y1: Y(y), y2: Y(y), class: y === 0 ? 'gr-zero' : 'gr-grid' }));
            svg.append(el('text', { x: L - 6, y: Y(y) + 4, class: 'gr-tick', 'text-anchor': 'end' }, minus(`${y}`)));
        }
        const every = W < 500 ? 8 : 4;
        for (let yr = Math.ceil(xmin / every) * every; yr <= xmax; yr += every) svg.append(el('text', { x: X(yr), y: H - B + 18, class: 'gr-tick', 'text-anchor': 'middle' }, `${yr}`));
        svg.append(el('text', { x: 14, y: T + (H - T - B) / 2, class: 'gr-axis', 'text-anchor': 'middle', transform: `rotate(-90 14 ${T + (H - T - B) / 2})` }, 'mm, from 2004–2009 mean'));
        svg.append(el('text', { x: L + (W - L - R) / 2, y: H - 6, class: 'gr-axis', 'text-anchor': 'middle' }, 'Year (grey band: gap between missions)'));
        const lines = {};
        SER.forEach(s => {
            let dpath = '', prev = null;
            rows.forEach((r, i) => {
                const v = r[s.key];
                if (v == null) { prev = null; return; }
                const gap = prev != null && xs[i] - xs[prev] > 1.5 / 12;
                dpath += `${prev == null || gap ? 'M' : 'L'}${X(xs[i]).toFixed(1)},${Y(v).toFixed(1)}`;
                prev = i;
            });
            const p = el('path', { d: dpath, class: `gr-line ${s.cls}` });
            svg.append(p);
            lines[s.key] = p;
        });
        chartBox.append(svg);
        const bar = document.getElementById('gr-toggles');
        if (!bar.childElementCount) {
            SER.forEach(s => {
                const b = document.createElement('button');
                b.type = 'button'; b.className = 'gr-btn'; b.dataset.key = s.key; b.setAttribute('aria-pressed', String(s.on));
                const sw = document.createElement('span'); sw.className = `gr-swatch ${s.cls}`; sw.setAttribute('aria-hidden', 'true');
                b.append(sw, document.createTextNode(s.label));
                b.addEventListener('click', () => {
                    b.setAttribute('aria-pressed', String(b.getAttribute('aria-pressed') !== 'true'));
                    apply();
                });
                bar.append(b);
            });
        }
        function apply() {
            bar.querySelectorAll('.gr-btn').forEach(b => { lines[b.dataset.key].style.display = b.getAttribute('aria-pressed') === 'true' ? '' : 'none'; });
        }
        apply();
    }
})();
