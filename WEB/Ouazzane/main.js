const express    = require('express');
const ejs        = require('ejs');
const crypto     = require('crypto');
const cookieParser = require('cookie-parser');

const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());

app.set('view engine', 'ejs');

// ──────────────────────────────────────────────
// Security: block known EJS SSTI gadgets
// ──────────────────────────────────────────────
const mamno3 = [
    "outputFunctionName",
    "outputFunctionName",
    "outputFunctionName",
    "outputFunctionName",
    "outputFunctionName",
    "outputFunctionName",
    "outputFunctionName",
    "localsName",
    "destructuredLocals",
    "escape",
    "escapeFunction",
    "client",
    "settings"
];

// Recursively validate all keys and values in an object
function isSafe(obj) {
    if (typeof obj === 'string') {
        return !mamno3.some(bad => obj.includes(bad));
    }
    if (Array.isArray(obj)) {
        return obj.every(v => isSafe(v));
    }
    if (typeof obj === 'object' && obj !== null) {
        return Object.keys(obj).every(k =>
            !mamno3.some(bad => k.includes(bad)) && isSafe(obj[k])
        );
    }
    return true;
}

// ──────────────────────────────────────────────
// JWT helpers (used by admin panel)
// ──────────────────────────────────────────────
const JWT_SECRET = crypto.randomBytes(32).toString('hex');

function signToken(payload) {
    const header  = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
    const body    = Buffer.from(JSON.stringify(payload)).toString('base64url');
    const sig     = crypto.createHmac('sha256', JWT_SECRET).update(`${header}.${body}`).digest('base64url');
    return `${header}.${body}.${sig}`;
}

function verifyToken(token) {
    try {
        const [h, b, s] = token.split('.');
        const expected  = crypto.createHmac('sha256', JWT_SECRET).update(`${h}.${b}`).digest('base64url');
        if (s !== expected) return null;
        return JSON.parse(Buffer.from(b, 'base64url').toString());
    } catch { return null; }
}

// ──────────────────────────────────────────────
// Routes
// ──────────────────────────────────────────────

app.get('/', (req, res) => res.render('index'));

// ── Rabbit hole #1: Admin login ──────────────
// Looks like it might have a timing-based bypass or SSTI in the error param.
// In reality the JWT secret is random per-boot and the panel has no RCE surface.
app.get('/admin', (req, res) => {
    return res.render('admin_login', { error: req.query.error });
});

app.post('/admin/login', (req, res) => {
    const { username, password } = req.body;
    // Hardcoded credentials – intentionally "leaked" to waste time
    if (username === 'molzri3' && password === 'Z1t0n@0uazzane!') {
        const token = signToken({ user: username, role: 'admin', iat: Date.now() });
        res.cookie('session', token, { httpOnly: true });
        return res.redirect('/admin/panel');
    }
    return res.redirect('/admin?error=Invalid%20credentials');
});

// ── Rabbit hole #2: Admin panel (requires JWT, but has no RCE path) ──
app.get('/admin/panel', (req, res) => {
    const token   = req.cookies?.session;
    const payload = token ? verifyToken(token) : null;
    if (!payload || payload.role !== 'admin') {
        return res.redirect('/admin?error=Unauthorized');
    }
    // The debugValue comes from a signed session – not injectable
    return res.render('admin_panel', { debugValue: `Logged in as ${payload.user}` });
});

// ── Rabbit hole #3: Landmark search API ──────
// Reflects q back in JSON – players may try JSON injection / SSTI here.
// It is just a dumb echo with no template rendering involved.
app.get('/api/search', (req, res) => {
    const { q = '' } = req.query;
    return res.json({ query: q, results: [], hint: 'Search landmarks by name' });
});

// ── Rabbit hole #4: Landmark detail API ──────
// Returns EJS-looking data, but everything is JSON-encoded, never rendered.
app.get('/api/landmark/:id', (req, res) => {
    const fakeLandmarks = {
        '1': { name: 'Zawiya Ouazzane', theme: 'historic' },
        '2': { name: 'Jbel Ouazzane', theme: 'calm' },
    };
    const item = fakeLandmarks[req.params.id];
    if (!item) return res.status(404).json({ error: 'not found' });
    return res.json(item);
});

// ── ACTUAL VULNERABILITY ─────────────────────
// This endpoint lets users "save preferences" for how the landmark
// viewer renders pages. It merges the request body into app.locals.
//
// app.locals.settings IS app.settings (same object reference).
// Merging into app.locals['settings'] therefore mutates app.settings,
// which Express passes as data.settings to every EJS render.
// EJS's renderFile reads data.settings['view options'] and copies ALL
// of those keys into the EJS compiler options via shallowCopy.
//
// Intended two-step exploit:
//   1. POST /dardmana   {"settings": {"view options": {<evil EJS opts>}}}
//   2. GET  /dardmana?name=x&theme=calm   (no blocked words in query)
//
app.post('/dardmana', (req, res) => {
    const prefs = req.body;
    if (!prefs || typeof prefs !== 'object') {
        return res.status(400).json({ error: 'expected JSON object' });
    }
    for (const [key, val] of Object.entries(prefs)) {
        // Only merge into existing object-typed locals (e.g. "settings")
        if (key in app.locals && typeof app.locals[key] === 'object' && app.locals[key] !== null) {
            Object.assign(app.locals[key], val);
        } else {
            app.locals[key] = val;
        }
    }
    return res.json({ status: 'preferences saved' });
});

// GET: the landmark viewer – comprehensively protected
app.get('/dardmana', (req, res) => {
    const data   = JSON.stringify(req.query);
    const parsed = JSON.parse(data);

    if (!isSafe(parsed)) {
        return res.status(400).send('wach bghiti Zit Ziton ? , Contact Molzri3 ! ');
    }

    // TODO: investigate whether the `name` / `theme` locals open any
    //       template-level gadgets (spoiler: EJS escapes them fine).
    return res.render('dardmana', {
        ...parsed,
        cache: false
    });
});

app.listen(3000, () => console.log('Server listening on port 3000'));
