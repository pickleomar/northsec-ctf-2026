// NovaSec Blog — internal employee platform
package main

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	ttemplate "text/template"
	"time"

	pg "github.com/go-pg/pg/v10"
	"github.com/go-pg/pg/v10/orm"
)

// ── Models ────────────────────────────────────────────────────────────────────

type User struct {
	tableName struct{} `pg:"users"`
	ID        int64    `pg:"id,pk"`
	Username  string   `pg:"username,unique"`
	Password  string   `pg:"password"`
	Role      string   `pg:"role"`
	Bio       string   `pg:"bio"`
}

type Post struct {
	tableName struct{}  `pg:"posts"`
	ID        int64     `pg:"id,pk"`
	UserID    int64     `pg:"user_id"`
	Author    string    `pg:"author"`
	Title     string    `pg:"title"`
	Body      string    `pg:"body"`
	CreatedAt time.Time `pg:"created_at,default:now()"`
}

type Message struct {
	tableName struct{}  `pg:"messages"`
	ID        int64     `pg:"id,pk"`
	UserID    int64     `pg:"user_id"`
	Author    string    `pg:"author"`
	Body      string    `pg:"body"`
	CreatedAt time.Time `pg:"created_at,default:now()"`
}

// ── Globals ───────────────────────────────────────────────────────────────────

var (
	db         *pg.DB
	sessions   = make(map[string]int64)
	sessionsMu sync.RWMutex
	ctfFlag    = envOr("CTF_FLAG", "NSC{Tanjwa_a_khawa_dyali_wlad_costa_dhafa}")
)

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

// ── Session ───────────────────────────────────────────────────────────────────

func newToken() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func currentUser(r *http.Request) *User {
	c, err := r.Cookie("session")
	if err != nil {
		return nil
	}
	sessionsMu.RLock()
	uid, ok := sessions[c.Value]
	sessionsMu.RUnlock()
	if !ok {
		return nil
	}
	u := &User{ID: uid}
	if err := db.Model(u).WherePK().Select(); err != nil {
		return nil
	}
	return u
}

func setSession(w http.ResponseWriter, uid int64) {
	tok := newToken()
	sessionsMu.Lock()
	sessions[tok] = uid
	sessionsMu.Unlock()
	http.SetCookie(w, &http.Cookie{Name: "session", Value: tok, Path: "/", HttpOnly: true})
}

// ── Base layout ───────────────────────────────────────────────────────────────

const baseTpl = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>NovaSec Blog</title>
  <style>
    *{box-sizing:border-box}
    body{font-family:'Courier New',monospace;max-width:900px;margin:40px auto;padding:0 24px;
         background:#0d0d0d;color:#c8c8c8;line-height:1.6}
    h1{color:#7ec8e3;margin-bottom:4px}
    h2{color:#5ab0d0;border-bottom:1px solid #222;padding-bottom:6px}
    h3{color:#4a90b8}
    a{color:#7ec8e3;text-decoration:none}a:hover{text-decoration:underline}
    nav{background:#111;padding:10px 14px;margin-bottom:24px;border:1px solid #222}
    nav a{margin-right:16px;font-size:0.9em}
    input,textarea,select{background:#1a1a1a;border:1px solid #333;color:#c8c8c8;
      padding:8px;width:100%;margin-bottom:10px;font-family:inherit}
    input:focus,textarea:focus{border-color:#5ab0d0;outline:none}
    button,.btn{background:#1e3a5f;color:#7ec8e3;border:1px solid #5ab0d0;
      padding:8px 18px;cursor:pointer;font-family:inherit;font-size:0.9em}
    button:hover{background:#254a72}
    .card{border:1px solid #222;padding:14px;margin:10px 0;background:#111}
    .card .meta{color:#666;font-size:0.82em;margin-bottom:6px}
    .badge{display:inline-block;font-size:0.72em;padding:2px 7px;border-radius:3px}
    .badge-user{background:#1a2a3a;color:#7ec8e3}
    .badge-admin{background:#3a1a1a;color:#e37c7c}
    .flag-box{font-size:1.15em;background:#0a1f0a;border:1px solid #2a5a2a;
      color:#5af05a;padding:16px;margin:16px 0;letter-spacing:0.05em;word-break:break-all}
    .err{color:#e37c7c;font-size:0.9em}
    .ok{color:#5af05a;font-size:0.9em}
    .denied{text-align:center;padding:60px 0;color:#666}
    .denied h2{color:#e37c7c;border:none}
    pre{background:#111;border:1px solid #333;padding:12px;overflow-x:auto;color:#aaa}
    code{background:#1a1a1a;padding:2px 5px;color:#aaa}
    hr{border:none;border-top:1px solid #222;margin:20px 0}
    table{width:100%;border-collapse:collapse}
    th,td{border:1px solid #2a2a2a;padding:8px 12px;text-align:left}
    th{background:#111;color:#5ab0d0}
    #resp{margin-top:10px;color:#5ab0d0;font-size:0.88em}
  </style>
</head>
<body>
<h1>&gt; NovaSec Blog</h1>
<nav>
  <a href="/">Home</a>
  <a href="/chat">Chat</a>
  <a href="/search">Search</a>
  {{if .User}}
    <a href="/profile">[ {{.User.Username}} ]</a>
    {{if eq .User.Role "admin"}}<a href="/admin" style="color:#e37c7c">Admin &#9760;</a>{{else}}<a href="/admin">Admin</a>{{end}}
    <a href="/logout">Logout</a>
  {{else}}
    <a href="/login">Login</a>
    <a href="/register">Register</a>
  {{end}}
</nav>
{{.Content}}
</body>
</html>`

type pageData struct {
	User    *User
	Content template.HTML
}

var baseParsed = template.Must(template.New("base").Parse(baseTpl))

func render(w http.ResponseWriter, r *http.Request, content string) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	baseParsed.Execute(w, pageData{
		User:    currentUser(r),
		Content: template.HTML(content),
	})
}

// ── Handlers ──────────────────────────────────────────────────────────────────

func homeHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	var posts []Post
	db.Model(&posts).OrderExpr("created_at DESC").Limit(30).Select()

	u := currentUser(r)
	form := ""
	if u != nil {
		form = `<form method="POST" action="/post" class="card">
  <h3 style="margin-top:0">New Post</h3>
  <input name="title" placeholder="Title">
  <textarea name="body" rows="3" placeholder="Content..."></textarea>
  <button type="submit">Publish</button>
</form>`
	} else {
		form = `<p><a href="/register">Register</a> or <a href="/login">login</a> to post.</p>`
	}

	list := ""
	for _, p := range posts {
		list += fmt.Sprintf(`<div class="card">
  <div class="meta">%s &mdash; %s</div>
  <strong>%s</strong>
  <p style="margin:8px 0 0">%s</p>
</div>`,
			template.HTMLEscapeString(p.Author),
			p.CreatedAt.Format("2006-01-02 15:04"),
			template.HTMLEscapeString(p.Title),
			template.HTMLEscapeString(p.Body))
	}
	if list == "" {
		list = `<p style="color:#666">No posts yet.</p>`
	}

	render(w, r, `<h2>Blog Posts</h2>`+form+list)
}

func postHandler(w http.ResponseWriter, r *http.Request) {
	u := currentUser(r)
	if u == nil {
		http.Redirect(w, r, "/login", 302)
		return
	}
	r.ParseForm()
	p := &Post{UserID: u.ID, Author: u.Username, Title: r.FormValue("title"), Body: r.FormValue("body")}
	db.Model(p).Insert()
	http.Redirect(w, r, "/", 302)
}

// ── RABBIT HOLE 1: Stored XSS in chat ────────────────────────────────────────
// Messages are rendered as raw HTML. XSS works in the browser.
// Dead end: there is no admin bot — stealing a session cookie gets nothing.

func chatHandler(w http.ResponseWriter, r *http.Request) {
	var msgs []Message
	db.Model(&msgs).OrderExpr("created_at ASC").Limit(60).Select()

	u := currentUser(r)
	form := ""
	if u != nil {
		form = `<form method="POST" action="/chat/send" style="display:flex;gap:8px;margin-bottom:16px">
  <input name="msg" placeholder="Type a message..." style="flex:1;margin:0">
  <button type="submit" style="width:80px">Send</button>
</form>`
	}

	list := ""
	for _, m := range msgs {
		style := ""
		if m.Author == "admin" {
			style = `style="border-color:#3a1a1a"`
		}
		// XSS: message body rendered without escaping
		list += fmt.Sprintf(`<div class="card" %s>
  <span style="color:#7ec8e3">%s</span>
  <span class="meta" style="margin-left:8px">%s</span>
  <div style="margin-top:4px">%s</div>
</div>`, style,
			template.HTMLEscapeString(m.Author),
			m.CreatedAt.Format("15:04"),
			m.Body) // intentionally unescaped
	}

	render(w, r, `<h2>Chat Room</h2>`+form+list)
}

func chatSendHandler(w http.ResponseWriter, r *http.Request) {
	u := currentUser(r)
	if u == nil {
		http.Redirect(w, r, "/login", 302)
		return
	}
	r.ParseForm()
	if msg := r.FormValue("msg"); msg != "" {
		db.Model(&Message{UserID: u.ID, Author: u.Username, Body: msg}).Insert()
	}
	http.Redirect(w, r, "/chat", 302)
}

// ── RABBIT HOLE 2: Search — looks like SQLi / reflected injection ─────────────
// Uses parameterised ILIKE — SQLi is not possible.
// The query is reflected back through html/template as data — not a template directive.

func searchHandler(w http.ResponseWriter, r *http.Request) {
	q := strings.TrimSpace(r.URL.Query().Get("q"))

	results := ""
	if q != "" {
		var posts []Post
		pattern := "%" + q + "%"
		db.Model(&posts).
			Where("title ILIKE ? OR body ILIKE ?", pattern, pattern).
			OrderExpr("created_at DESC").Limit(20).Select()

		if len(posts) == 0 {
			results = `<p style="color:#666">No results found.</p>`
		}
		for _, p := range posts {
			results += fmt.Sprintf(`<div class="card">
  <div class="meta">%s &mdash; %s</div>
  <strong>%s</strong>
  <p style="margin:8px 0 0">%s</p>
</div>`,
				template.HTMLEscapeString(p.Author),
				p.CreatedAt.Format("2006-01-02 15:04"),
				template.HTMLEscapeString(p.Title),
				template.HTMLEscapeString(p.Body))
		}
	}

	render(w, r, fmt.Sprintf(`<h2>Search</h2>
<form method="GET" action="/search">
  <div style="display:flex;gap:8px">
    <input name="q" value="%s" placeholder="Search posts..." style="flex:1;margin:0">
    <button type="submit">Search</button>
  </div>
</form>
<p style="color:#555;font-size:0.82em;margin-top:6px">
  NovaSec Search Engine v2.3 &mdash; powered by NovaSec/tmpl
</p>
%s`, template.HTMLEscapeString(q), results))
}

// ── RABBIT HOLE 3: Template preview — real text/template, restricted scope ────
// {{.AppName}} works. {{.Version}} works. {{len "x"}} works.
// Nothing in scope touches the flag or any user data.
// Arithmetic like {{7*7}} fails (Go text/template has no arithmetic operators).

type previewData struct {
	AppName string
	Version string
	Env     string
}

func previewHandler(w http.ResponseWriter, r *http.Request) {
	t := r.URL.Query().Get("t")

	output := ""
	errMsg := ""

	if t != "" {
		tmpl, err := ttemplate.New("p").Parse(t)
		if err != nil {
			errMsg = fmt.Sprintf("parse error: %s", err.Error())
		} else {
			var buf bytes.Buffer
			err = tmpl.Execute(&buf, previewData{
				AppName: "NovaSec Blog",
				Version: "2.3.1",
				Env:     "production",
			})
			if err != nil {
				errMsg = fmt.Sprintf("render error: %s", err.Error())
			} else {
				output = buf.String()
			}
		}
	}

	errBlock := ""
	if errMsg != "" {
		errBlock = fmt.Sprintf(`<p class="err">%s</p>`, template.HTMLEscapeString(errMsg))
	}
	outBlock := ""
	if output != "" {
		outBlock = fmt.Sprintf(`<div class="card"><strong>Rendered output:</strong><pre>%s</pre></div>`,
			template.HTMLEscapeString(output))
	}

	render(w, r, fmt.Sprintf(`<h2>Template Preview</h2>
<p style="color:#666;font-size:0.85em">
  NovaSec/tmpl engine &mdash; supports a subset of Go template syntax.
  Available context fields: <code>.AppName</code>, <code>.Version</code>, <code>.Env</code>
</p>
<form method="GET" action="/preview">
  <textarea name="t" rows="4" placeholder="Hello {{.AppName}}!">%s</textarea>
  <button type="submit">Render</button>
</form>
%s%s`,
		template.HTMLEscapeString(t), errBlock, outBlock))
}

// ── robots.txt + fake 403 targets ─────────────────────────────────────────────

func robotsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprintln(w, `User-agent: *
Disallow: /admin
Disallow: /backup
Disallow: /.git
Disallow: /api/`)
}

func backupHandler(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "403 Forbidden", 403)
}

// ── Auth ──────────────────────────────────────────────────────────────────────

func registerHandler(w http.ResponseWriter, r *http.Request) {
	errMsg := ""
	if r.Method == "POST" {
		r.ParseForm()
		user, pass := r.FormValue("username"), r.FormValue("password")
		if user == "" || pass == "" {
			errMsg = "username and password are required"
		} else {
			u := &User{Username: user, Password: pass, Role: "user", Bio: ""}
			if _, err := db.Model(u).Insert(); err != nil {
				errMsg = "username already taken"
			} else {
				setSession(w, u.ID)
				http.Redirect(w, r, "/", 302)
				return
			}
		}
	}
	render(w, r, fmt.Sprintf(`<h2>Register</h2>
<div class="card" style="max-width:420px">
<form method="POST">
  <label>Username</label>
  <input name="username" autocomplete="off">
  <label>Password</label>
  <input type="password" name="password">
  <button type="submit">Create Account</button>
  <p class="err">%s</p>
</form>
</div>
<p>Already registered? <a href="/login">Login</a></p>`, errMsg))
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	errMsg := ""
	if r.Method == "POST" {
		r.ParseForm()
		u := &User{}
		err := db.Model(u).Where("username = ? AND password = ?",
			r.FormValue("username"), r.FormValue("password")).Select()
		if err != nil {
			errMsg = "invalid credentials"
		} else {
			setSession(w, u.ID)
			http.Redirect(w, r, "/", 302)
			return
		}
	}
	render(w, r, fmt.Sprintf(`<h2>Login</h2>
<div class="card" style="max-width:420px">
<form method="POST">
  <label>Username</label>
  <input name="username" autocomplete="off">
  <label>Password</label>
  <input type="password" name="password">
  <button type="submit">Login</button>
  <p class="err">%s</p>
</form>
</div>
<p>No account? <a href="/register">Register</a></p>`, errMsg))
}

func logoutHandler(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie("session"); err == nil {
		sessionsMu.Lock()
		delete(sessions, c.Value)
		sessionsMu.Unlock()
	}
	http.SetCookie(w, &http.Cookie{Name: "session", Value: "", MaxAge: -1, Path: "/"})
	http.Redirect(w, r, "/", 302)
}

// ── Profile ───────────────────────────────────────────────────────────────────

func profileHandler(w http.ResponseWriter, r *http.Request) {
	u := currentUser(r)
	if u == nil {
		http.Redirect(w, r, "/login", 302)
		return
	}
	badge := fmt.Sprintf(`<span class="badge badge-%s">%s</span>`, u.Role, u.Role)
	render(w, r, fmt.Sprintf(`<h2>Profile</h2>
<div class="card">
  <div class="meta">Account details</div>
  <table style="width:auto;margin-top:6px">
    <tr><td style="color:#666;padding-right:20px">Username</td><td>%s</td></tr>
    <tr><td style="color:#666">Role</td><td>%s</td></tr>
    <tr><td style="color:#666">Bio</td><td>%s</td></tr>
  </table>
</div>
<h3>Update Bio</h3>
<div class="card">
<textarea id="bioInput" rows="3" placeholder="Tell us about yourself...">%s</textarea>
<button onclick="doUpdate()">Save</button>
<div id="resp"></div>
</div>
<script>
function doUpdate() {
  fetch('/api/profile', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({bio: document.getElementById('bioInput').value})
  })
  .then(r => r.json())
  .then(d => { document.getElementById('resp').textContent = JSON.stringify(d) })
  .catch(e => { document.getElementById('resp').textContent = String(e) });
}
</script>`,
		template.HTMLEscapeString(u.Username),
		badge,
		template.HTMLEscapeString(u.Bio),
		template.HTMLEscapeString(u.Bio)))
}

func apiProfileHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method != "PATCH" {
		w.WriteHeader(405)
		json.NewEncoder(w).Encode(map[string]string{"error": "PATCH only"})
		return
	}
	u := currentUser(r)
	if u == nil {
		w.WriteHeader(401)
		json.NewEncoder(w).Encode(map[string]string{"error": "not authenticated"})
		return
	}

	var fields map[string]string
	if err := json.NewDecoder(r.Body).Decode(&fields); err != nil {
		w.WriteHeader(400)
		json.NewEncoder(w).Encode(map[string]string{"error": "invalid JSON"})
		return
	}

	fresh := &User{ID: u.ID}
	db.Model(fresh).WherePK().Select()

	q := db.Model(fresh).WherePK().Column("bio")
	for col, val := range fields {
		q = q.Value(col, "?", val)
	}

	result, err := q.Update()
	if err != nil {
		w.WriteHeader(500)
		json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":       "profile updated",
		"rows_affected": result.RowsAffected(),
	})
}

// ── Admin ─────────────────────────────────────────────────────────────────────

func adminHandler(w http.ResponseWriter, r *http.Request) {
	u := currentUser(r)
	if u == nil {
		http.Redirect(w, r, "/login", 302)
		return
	}
	if u.Role != "admin" {
		render(w, r, `<div class="denied">
  <h2>&#128683; Access Denied</h2>
  <p>This area is restricted to administrators only.</p>
  <p style="color:#555;font-size:0.85em">Your current role: `+u.Role+`</p>
</div>`)
		return
	}

	var users []User
	db.Model(&users).OrderExpr("id ASC").Select()
	rows := ""
	for _, usr := range users {
		badge := fmt.Sprintf(`<span class="badge badge-%s">%s</span>`, usr.Role, usr.Role)
		rows += fmt.Sprintf("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>",
			usr.ID,
			template.HTMLEscapeString(usr.Username),
			badge,
			template.HTMLEscapeString(usr.Bio))
	}
	render(w, r, fmt.Sprintf(`<h2>&#9760; Admin Dashboard</h2>
<div class="flag-box">FLAG: %s</div>
<h3>User Table</h3>
<table>
  <tr><th>ID</th><th>Username</th><th>Role</th><th>Bio</th></tr>
  %s
</table>`, template.HTMLEscapeString(ctfFlag), rows))
}

// ── DB setup ──────────────────────────────────────────────────────────────────

func createSchema() {
	for _, m := range []interface{}{(*User)(nil), (*Post)(nil), (*Message)(nil)} {
		if err := db.Model(m).CreateTable(&orm.CreateTableOptions{IfNotExists: true}); err != nil {
			log.Printf("createTable: %v", err)
		}
	}
}

func seed() {
	adminUser := &User{Username: "admin", Password: "s3cr3t!adm1n#2026", Role: "admin", Bio: "Site administrator."}
	db.Model(adminUser).OnConflict("(username) DO NOTHING").Insert()

	var admin User
	db.Model(&admin).Where("username = 'admin'").Select()
	if admin.ID == 0 {
		return
	}

	// Wipe and re-seed posts and messages so stale seed data never lingers.
	db.Exec("TRUNCATE posts RESTART IDENTITY CASCADE")
	db.Exec("TRUNCATE messages RESTART IDENTITY CASCADE")

	postCount := 0
	db.Model((*Post)(nil)).QueryOne(pg.Scan(&postCount), "SELECT COUNT(*) FROM posts")
	if postCount == 0 {
		posts := []Post{
			{
				UserID: admin.ID, Author: "admin",
				Title: "Welcome to NovaSec Blog",
				Body:  "This is the internal NovaSec employee blog. Powered by go-pg on the backend. Discuss projects, share updates, and collaborate. The admin panel at /admin is restricted — do not attempt to access it without authorisation.",
			},
			{
				UserID: admin.ID, Author: "admin",
				Title: "New feature: Template Preview",
				Body:  "We've added a template preview tool at /preview for drafting formatted announcements. It supports a subset of our internal NovaSec/tmpl syntax. Give it a try.",
			},
			{
				UserID: admin.ID, Author: "admin",
				Title: "Reminder: account security",
				Body:  "Please use a strong password. Role-based access controls are enforced server-side — your account role is what determines what you can see.",
			},
		}
		for i := range posts {
			db.Model(&posts[i]).Insert()
		}
	}

	msgs := []Message{
		{
			UserID: admin.ID, Author: "admin",
			Body: "Morning everyone. I keep an eye on this chat, so please keep it professional.",
		},
		{
			UserID: admin.ID, Author: "admin",
			Body: "Reminder: the flag is in the admin panel. You won't get in without the right role. 🙂",
		},
		{
			UserID: admin.ID, Author: "admin",
			Body: "Security team flagged some suspicious search queries earlier. Just so you know — we log everything.",
		},
	}
	for i := range msgs {
		db.Model(&msgs[i]).Insert()
	}
}

// ── Main ──────────────────────────────────────────────────────────────────────

func setupDB() {
	pgAddr := envOr("PG_ADDR", "localhost:5433")
	pgUser := envOr("PG_USER", "demo")
	pgPass := envOr("PG_PASS", "demo")

	bootstrap := pg.Connect(&pg.Options{Addr: pgAddr, User: pgUser, Password: pgPass, Database: "demodb"})
	_, err := bootstrap.Exec("CREATE DATABASE ctfdb")
	if err != nil && !strings.Contains(err.Error(), "already exists") {
		log.Fatalf("create ctfdb: %v", err)
	}
	bootstrap.Close()

	db = pg.Connect(&pg.Options{Addr: pgAddr, User: pgUser, Password: pgPass, Database: "ctfdb"})
	for i := 0; i < 10; i++ {
		if _, err := db.Exec("SELECT 1"); err == nil {
			return
		}
		time.Sleep(500 * time.Millisecond)
	}
	log.Fatal("could not connect to PostgreSQL — is the demo app running?")
}

func main() {
	fmt.Println("[*] Starting NovaSec Blog ...")
	setupDB()
	defer db.Close()
	createSchema()
	seed()
	fmt.Println("[+] Database ready")

	mux := http.NewServeMux()
	mux.HandleFunc("/", homeHandler)
	mux.HandleFunc("/register", registerHandler)
	mux.HandleFunc("/login", loginHandler)
	mux.HandleFunc("/logout", logoutHandler)
	mux.HandleFunc("/post", postHandler)
	mux.HandleFunc("/chat", chatHandler)
	mux.HandleFunc("/chat/send", chatSendHandler)
	mux.HandleFunc("/search", searchHandler)
	mux.HandleFunc("/preview", previewHandler)
	mux.HandleFunc("/profile", profileHandler)
	mux.HandleFunc("/api/profile", apiProfileHandler)
	mux.HandleFunc("/admin", adminHandler)
	mux.HandleFunc("/robots.txt", robotsHandler)
	mux.HandleFunc("/backup", backupHandler)
	mux.HandleFunc("/.git", backupHandler)

	fmt.Println("[+] NovaSec Blog running at http://localhost:8081")
	fmt.Printf("[+] Flag loaded\n")
	fmt.Println("[+] Press Ctrl+C to stop.")

	if err := http.ListenAndServe(":8081", mux); err != nil {
		log.Fatal(err)
	}
}
