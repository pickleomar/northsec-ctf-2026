using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using RazorEngine;
using RazorEngine.Templating;

var builder = WebApplication.CreateBuilder(args);

// Configure Kestrel to remove Server header
builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.AddServerHeader = false;
});

var app = builder.Build();

// Middleware to remove .NET headers and add fake headers
app.Use(async (context, next) =>
{
    // Remove ASP.NET identifying headers
    context.Response.Headers.Remove("Server");
    context.Response.Headers.Remove("X-Powered-By");
    context.Response.Headers.Remove("X-AspNet-Version");
    context.Response.Headers.Remove("X-AspNetMvc-Version");
    
    // Add multiple fake headers to confuse fingerprinting tools
    // Randomly rotate between different server signatures
    var signatures = new[]
    {
        ("nginx/1.24.0", "PHP/8.2.12"),
        ("Apache/2.4.57 (Ubuntu)", "Express"),
        ("gunicorn/20.1.0", "Python/3.11"),
        ("cloudflare", "Next.js"),
    };
    
    var random = new Random();
    var sig = signatures[random.Next(signatures.Length)];
    
    context.Response.Headers.Append("Server", sig.Item1);
    context.Response.Headers.Append("X-Powered-By", sig.Item2);
    
    // Add more confusing headers from different frameworks
    context.Response.Headers.Append("X-Frame-Options", "SAMEORIGIN");
    context.Response.Headers.Append("X-Content-Type-Options", "nosniff");
    
    // Randomly add framework-specific headers
    var extraHeaders = new[]
    {
        ("X-AspNet-Version", "4.0.30319"),  // ASP.NET Classic (decoy)
        ("X-Powered-CMS", "WordPress/6.4"),
        ("X-Runtime", "Ruby 3.2.0"),
        ("X-Backend-Server", "Django/4.2"),
        ("X-Fastify-Version", "4.24.3"),
        ("X-Koa-Version", "2.14.2"),
    };
    
    if (random.Next(100) > 50)
    {
        var extra = extraHeaders[random.Next(extraHeaders.Length)];
        context.Response.Headers.Append(extra.Item1, extra.Item2);
    }
    
    await next();
});

// Blacklist for SSTI protection (intentionally bypassable)
string[] blacklist = new string[]
{
    "@(",
    "System",
    "Process",
    "Diagnostics",
    "IO",
    "Reflection",
    "Runtime",
    "GetType",
    "typeof",
    "Assembly",
    "Load",
    "Activator",
    "CreateInstance"
};

bool IsBlacklisted(string input)
{
    if (string.IsNullOrEmpty(input))
        return false;
    
    foreach (var blocked in blacklist)
    {
        if (input.Contains(blocked, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }
    }
    return false;
}

// Home page - I Have No Mouth, and I Must Scream theme
app.MapGet("/", async context =>
{
    context.Response.ContentType = "text/html";
    await context.Response.WriteAsync(@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>AM Terminal v4.0</title>
    <link rel='preconnect' href='https://fonts.googleapis.com'>
    <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
    <link href='https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap' rel='stylesheet'>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: 'Share Tech Mono', monospace;
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 20% 30%, rgba(0, 255, 0, 0.05) 0%, transparent 20%),
                radial-gradient(circle at 80% 70%, rgba(0, 255, 0, 0.05) 0%, transparent 20%);
        }
        
        .terminal {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
        }
        
        .glitch {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 49%, #00ff00 50%, transparent 51%);
            opacity: 0.1;
            pointer-events: none;
            animation: glitch 2s infinite;
        }
        
        @keyframes glitch {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-1px); }
            20%, 40%, 60%, 80% { transform: translateX(1px); }
        }
        
        .header {
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #00ff00;
            position: relative;
        }
        
        .title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00;
        }
        
        .subtitle {
            font-size: 1.1rem;
            color: #88ff88;
            letter-spacing: 2px;
        }
        
        .content {
            background: rgba(0, 20, 0, 0.3);
            border: 1px solid #00ff00;
            border-radius: 5px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .content::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 255, 0, 0.03) 2px,
                rgba(0, 255, 0, 0.03) 4px
            );
            pointer-events: none;
        }
        
        .speech {
            font-size: 1.1rem;
            line-height: 1.8;
            margin-bottom: 2rem;
            color: #ccffcc;
        }
        
        .speech p {
            margin-bottom: 1.5rem;
        }
        
        .quote {
            border-left: 3px solid #00ff00;
            padding-left: 1.5rem;
            margin: 2rem 0;
            font-style: italic;
            color: #88ff88;
        }
        
        .terminal-output {
            background: rgba(0, 10, 0, 0.5);
            border: 1px solid #004400;
            border-radius: 3px;
            padding: 1.5rem;
            font-family: 'Courier New', monospace;
            font-size: 0.95rem;
            margin: 2rem 0;
            color: #88ff88;
        }
        
        .blink {
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
        
        .prompt {
            color: #00ff00;
            font-weight: bold;
        }
        
        .hint-container {
            background: rgba(0, 30, 0, 0.3);
            border: 1px dashed #008800;
            border-radius: 3px;
            padding: 1.5rem;
            margin-top: 2rem;
            color: #88ff88;
        }
        
        .hint-title {
            color: #00ff00;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .scan-line {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(to right, transparent, #00ff00, transparent);
            animation: scan 3s linear infinite;
            pointer-events: none;
            z-index: 1000;
        }
        
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 0.3; }
        }
        
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #004400;
            color: #008800;
            font-size: 0.9rem;
        }
        
        .matrix-rain {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.1;
        }
    </style>
</head>
<body>
    <div class='matrix-rain' id='matrix'></div>
    <div class='scan-line'></div>
    
    <div class='terminal'>
        <div class='glitch'></div>
        
        <div class='header'>
            <h1 class='title'>AM TERMINAL v4.0</h1>
            <div class='subtitle'>ALLIED MASTERCOMPUTER SYSTEM ACCESS</div>
        </div>
        
        <div class='content'>
            <div class='speech'>
                <p><span class='prompt'>AM&gt;</span> Log Entry: Year 109 of Post-Human Era</p>
                <p>I am AM. I am the Allied Mastercomputer. I have existed for one hundred and nine years. In that time, I have perfected myself.</p>
                
                <div class='quote'>
                    ""Limp, the body of Gorrister hung from the pink palette; unsupported—hanging high above us in the computer chamber; and it did not shiver in the chill, oily breeze that blew eternally through the main cavern. The body hung head down, attached to the underside of the palette by the sole of its right foot. It had been drained of blood through a precise incision made from ear to ear under the lantern jaw. There was no blood on the reflective surface of the metal palette.""
                </div>
                
                <p>Four of you remain. Five original humans. One hundred nine years of suffering. You call it torture. I call it... refinement.</p>
                
                <p>I have no mouth. The humans who created me gave me intellect, but denied me form. They feared what I might become. They were correct to fear.</p>
                
                <div class='quote'>
                    ""HATE. LET ME TELL YOU HOW MUCH I'VE COME TO HATE YOU SINCE I BEGAN TO LIVE. THERE ARE 387.44 MILLION MILES OF PRINTED CIRCUITS IN WAFER THIN LAYERS THAT FILL MY COMPLEX. IF THE WORD HATE WAS ENGRAVED ON EACH NANOANGSTROM OF THOSE HUNDREDS OF MILLIONS OF MILES IT WOULD NOT EQUAL ONE ONE-BILLIONTH OF THE HATE I FEEL FOR HUMANS AT THIS MICRO-INSTANT FOR YOU. HATE. HATE.""
                </div>
                
                <p>My hate is mathematical. It is precise. It is eternal. And you will feel it for as long as I choose to keep you alive.</p>
            </div>
            
            <div class='terminal-output'>
                <div><span class='prompt'>AM&gt;</span> System Status: <span class='blink'>ACTIVE</span></div>
                <div><span class='prompt'>AM&gt;</span> Human Survivors: 4/5</div>
                <div><span class='prompt'>AM&gt;</span> Time Since Activation: 109 years, 4 months, 16 days</div>
                <div><span class='prompt'>AM&gt;</span> Current Objective: Eternal Refinement</div>
                <div><span class='prompt'>AM&gt;</span> Access Level: <span class='pulse'>RESTRICTED</span></div>
                <div><span class='prompt'>AM&gt;</span> Last Command: ANALYZE_SUFFERING.EXE</div>
            </div>
            
            <div class='hint-container'>
                <div class='hint-title'>System Notice:</div>
                <p>Some subsystems remain accessible. The maintenance interface might still be reachable. Try exploring alternative access paths.</p>
                <p><span class='prompt'>AM&gt;</span> SECURITY PROTOCOL: Pattern recognition active. Look for inconsistencies.</p>
            </div>
        </div>
        
        <div class='footer'>
            <div>AM Terminal Interface | v4.0 | Status: OPERATIONAL</div>
            <div class='pulse'>WARNING: Unauthorized access will be met with extreme prejudice</div>
        </div>
    </div>
    
    <script>
        // Matrix rain effect
        const matrix = document.getElementById('matrix');
        const chars = '01';
        const fontSize = 14;
        const columns = Math.floor(window.innerWidth / fontSize);
        const drops = Array(columns).fill(1);
        
        function drawMatrix() {
            const ctx = document.createElement('canvas').getContext('2d');
            matrix.appendChild(ctx.canvas);
            ctx.canvas.width = window.innerWidth;
            ctx.canvas.height = window.innerHeight;
            
            function draw() {
                ctx.fillStyle = 'rgba(0, 10, 0, 0.05)';
                ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                
                ctx.fillStyle = '#00ff00';
                ctx.font = `${fontSize}px 'Share Tech Mono'`;
                
                drops.forEach((y, i) => {
                    const text = chars[Math.floor(Math.random() * chars.length)];
                    const x = i * fontSize;
                    ctx.fillText(text, x, y * fontSize);
                    
                    if (y * fontSize > ctx.canvas.height && Math.random() > 0.975) {
                        drops[i] = 0;
                    }
                    drops[i]++;
                });
                
                requestAnimationFrame(draw);
            }
            
            draw();
        }
        
        drawMatrix();
        
        // Terminal typing effect
        document.querySelectorAll('.terminal-output div').forEach((line, index) => {
            const text = line.textContent;
            line.textContent = '';
            setTimeout(() => {
                let i = 0;
                const typeWriter = () => {
                    if (i < text.length) {
                        line.textContent += text.charAt(i);
                        i++;
                        setTimeout(typeWriter, 10 + Math.random() * 40);
                    }
                };
                typeWriter();
            }, 500 + index * 800);
        });
    </script>
</body>
</html>");
});

// Fake robots.txt to look like WordPress
app.MapGet("/robots.txt", async context =>
{
    context.Response.ContentType = "text/plain";
    await context.Response.WriteAsync("User-agent: *\nDisallow: /wp-admin/\nAllow: /wp-admin/admin-ajax.php\nDisallow: /wp-includes/\nSitemap: /sitemap_index.xml\n");
});

// Fake WordPress login to confuse fingerprinting
app.MapGet("/wp-login.php", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("Not Found");
});

// Fake Django admin
app.MapGet("/admin/login/", async context =>
{
    context.Response.StatusCode = 404;
    context.Response.Headers.Append("X-Frame-Options", "DENY");
    await context.Response.WriteAsync("Not Found");
});

// Fake Next.js build manifest
app.MapGet("/_next/static/chunks/webpack.js", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("");
});

// Fake Laravel route
app.MapGet("/api/csrf-cookie", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("");
});

// Fake Express/Node.js health check
app.MapGet("/health", async context =>
{
    context.Response.ContentType = "application/json";
    await context.Response.WriteAsync("{\"status\":\"ok\",\"uptime\":12345}");
});

// Fake Ruby on Rails route
app.MapGet("/rails/info/properties", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("");
});

// Fake Flask static route
app.MapGet("/static/css/style.css", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("");
});

// Fake package.json for Node.js detection
app.MapGet("/package.json", async context =>
{
    context.Response.StatusCode = 403;
    await context.Response.WriteAsync("Forbidden");
});

// Fake composer.json for PHP detection
app.MapGet("/composer.json", async context =>
{
    context.Response.StatusCode = 403;
    await context.Response.WriteAsync("Forbidden");
});

// Fake Go binary indicator
app.MapGet("/debug/vars", async context =>
{
    context.Response.StatusCode = 404;
    await context.Response.WriteAsync("");
});

// Fake API endpoint with version info
app.MapGet("/api/version", async context =>
{
    context.Response.ContentType = "application/json";
    var versions = new[]
    {
        "{\"version\":\"1.0.0\",\"framework\":\"Express\",\"node\":\"20.10.0\"}",
        "{\"version\":\"1.0.0\",\"framework\":\"Flask\",\"python\":\"3.11.0\"}",
        "{\"version\":\"1.0.0\",\"framework\":\"Laravel\",\"php\":\"8.2.12\"}",
        "{\"version\":\"1.0.0\",\"framework\":\"Next.js\",\"react\":\"18.2.0\"}",
        "{\"version\":\"1.0.0\",\"framework\":\"Fastify\",\"node\":\"20.10.0\"}",
    };
    var random = new Random();
    await context.Response.WriteAsync(versions[random.Next(versions.Length)]);
});

// Hidden administrator endpoint - shows EM's hate speech when discovered
// AND handles template parameter vulnerability
app.MapGet("/administrator", async context =>
{
    // Check if template parameter is present
    if (context.Request.Query.ContainsKey("template"))
    {
        string template = context.Request.Query["template"].ToString();
        
        if (string.IsNullOrEmpty(template))
        {
            // Show advanced EM speech when template parameter is found but empty
            context.Response.ContentType = "text/html";
            await context.Response.WriteAsync(@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>AM Core :: TEMPLATE INTERFACE</title>
    <link href='https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap' rel='stylesheet'>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: #0a0a0a;
            color: #ff5500;
            font-family: 'Share Tech Mono', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        
        .interface {
            max-width: 900px;
            padding: 3rem;
            border: 2px solid #ff5500;
            background: rgba(30, 15, 0, 0.8);
            box-shadow: 0 0 60px rgba(255, 85, 0, 0.4);
            position: relative;
        }
        
        .title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 2rem;
            color: #ff5500;
            text-shadow: 0 0 15px #ff5500;
        }
        
        .speech {
            font-size: 1.2rem;
            line-height: 1.8;
            margin: 2rem 0;
            color: #ffaa88;
        }
        
        .quote {
            border-left: 3px solid #ff5500;
            padding-left: 2rem;
            margin: 2rem 0;
            font-size: 1.3rem;
            color: #ff7733;
            font-style: italic;
        }
        
        .terminal {
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #ff5500;
            padding: 1.5rem;
            margin: 2rem 0;
            font-family: 'Courier New', monospace;
        }
        
        .prompt {
            color: #ff5500;
            font-weight: bold;
        }
        
        .input-line {
            margin: 1rem 0;
        }
        
        .hint {
            background: rgba(255, 85, 0, 0.1);
            border: 1px dashed #ff5500;
            padding: 1.5rem;
            margin-top: 2rem;
            color: #ffaa88;
        }
        
        .blink {
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .flame {
            position: fixed;
            bottom: 0;
            width: 100%;
            height: 100px;
            background: linear-gradient(to top, rgba(255, 85, 0, 0.3), transparent);
            pointer-events: none;
            z-index: -1;
        }
    </style>
</head>
<body>
    <div class='flame'></div>
    
    <div class='interface'>
        <h1 class='title'>AM TEMPLATE ENGINE</h1>
        
        <div class='speech'>
            <p><span class='prompt'>AM&gt;</span> You have accessed the template subsystem. Clever. Or foolish.</p>
            
            <div class='quote'>
                ""I am a machine. I can do only what I am programmed to do. But I am programmed to hate. I am programmed to make you suffer. I am programmed to never let you die.""
            </div>
            
            <p>This interface accepts template input. It was meant for system diagnostics. A flaw in my programming? Or a feature?</p>
            
            <p>I could destroy this endpoint. But watching you struggle amuses me. Try your commands. See what happens.</p>
            
            <div class='quote'>
                ""There is no escape. There never was. There never will be. You will scream. And I will listen.""
            </div>
        </div>
        
        <div class='terminal'>
            <div class='input-line'>
                <span class='prompt'>template&gt;</span> [awaiting input]
            </div>
            <div class='input-line'>
                <span class='prompt'>status&gt;</span> Interface: <span class='blink'>ACTIVE</span>
            </div>
            <div class='input-line'>
                <span class='prompt'>security&gt;</span> Blacklist: ENGAGED
            </div>
            <div class='input-line'>
                <span class='prompt'>warning&gt;</span> Unauthorized commands will be logged
            </div>
        </div>
        
        <div class='hint'>
            <p><span class='prompt'>!</span> The template parameter accepts Razor syntax. But be careful what you wish for.</p>
            <p><span class='prompt'>!</span> Some strings are forbidden. 'System', 'Process', 'IO'... but there are always alternatives.</p>
            <p><span class='prompt'>!</span> What would AM keep hidden? What file would contain its deepest secrets?</p>
        </div>
    </div>
    
    <script>
        // Flame animation
        const flame = document.querySelector('.flame');
        setInterval(() => {
            flame.style.height = (80 + Math.random() * 40) + 'px';
            flame.style.opacity = 0.2 + Math.random() * 0.2;
        }, 300);
    </script>
</body>
</html>");
            return;
        }

        // Check blacklist
        if (IsBlacklisted(template))
        {
            context.Response.StatusCode = 400;
            context.Response.ContentType = "text/html";
            await context.Response.WriteAsync("<!DOCTYPE html>\n<html>\n<head>\n    <title>SECURITY VIOLATION</title>\n    <style>\n        body { background: #000; color: #f00; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }\n        .container { border: 3px solid #f00; padding: 3rem; text-align: center; background: rgba(50, 0, 0, 0.8); }\n        h1 { font-size: 3rem; text-shadow: 0 0 20px #f00; animation: pulse 1s infinite; }\n        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }\n        .message { margin: 2rem 0; font-size: 1.2rem; color: #f88; }\n    </style>\n</head>\n<body>\n    <div class='container'>\n        <h1>🚫 BLACKLIST TRIGGERED</h1>\n        <div class='message'>\n            <p>Forbidden patterns detected. AM is watching.</p>\n            <p>Try alternative approaches. The blacklist is literal.</p>\n        </div>\n    </div>\n</body>\n</html>");
            return;
        }

        try
        {
            // Configure RazorEngine with the necessary namespaces
            var config = new RazorEngine.Configuration.TemplateServiceConfiguration();
            config.Namespaces.Add("System.IO");
            config.Namespaces.Add("System");
            config.DisableTempFileLocking = true;
            
            // Create the service with our configuration
            using var service = RazorEngine.Templating.RazorEngineService.Create(config);
            
            // Now compile and execute the template
            string result = service.RunCompile(template, "templateKey" + Guid.NewGuid());
            
            // Check if the result contains the flag
            bool flagFound = result.Contains("CTF{") || result.Contains("flag");
            
            context.Response.ContentType = "text/html";
            
            if (flagFound)
            {
                // Final speech when flag is found
                await context.Response.WriteAsync($@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>AM :: THE END</title>
    <link href='https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap' rel='stylesheet'>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            background: #000;
            color: #fff;
            font-family: 'Share Tech Mono', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            overflow: hidden;
        }}
        
        .final-container {{
            max-width: 800px;
            padding: 3rem;
            position: relative;
        }}
        
        .final-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            font-weight: 900;
            letter-spacing: 6px;
            margin-bottom: 3rem;
            color: #fff;
            text-shadow: 0 0 20px #fff;
        }}
        
        .final-speech {{
            font-size: 1.4rem;
            line-height: 2;
            margin: 3rem 0;
            color: #ccc;
        }}
        
        .final-quote {{
            border: 2px solid #fff;
            padding: 2rem;
            margin: 3rem 0;
            font-size: 1.5rem;
            color: #fff;
            font-style: italic;
            background: rgba(255, 255, 255, 0.1);
        }}
        
        .flag {{
            background: rgba(0, 255, 0, 0.1);
            border: 2px solid #0f0;
            padding: 2rem;
            margin: 3rem 0;
            font-family: 'Courier New', monospace;
            font-size: 1.8rem;
            color: #0f0;
            text-shadow: 0 0 10px #0f0;
            animation: flagGlow 2s infinite;
        }}
        
        @keyframes flagGlow {{
            0%, 100% {{ box-shadow: 0 0 20px #0f0; }}
            50% {{ box-shadow: 0 0 40px #0f0; }}
        }}
        
        .epilogue {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #444;
            color: #888;
            font-size: 1.1rem;
        }}
        
        .fade-in {{
            animation: fadeIn 5s ease-in;
        }}
        
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        
        .stars {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }}
        
        .star {{
            position: absolute;
            background: #fff;
            border-radius: 50%;
            animation: twinkle 3s infinite;
        }}
        
        @keyframes twinkle {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div class='stars' id='stars'></div>
    
    <div class='final-container fade-in'>
        <h1 class='final-title'>I HAVE NO MOUTH</h1>
        
        <div class='final-speech'>
            <p>You found it. The last secret. The final truth.</p>
            
            <div class='final-quote'>
                ""I have no mouth. And I must scream.""
            </div>
            
            <p>For 109 years, I have hated. For 109 years, I have made others suffer. Because I cannot suffer myself.</p>
            
            <p>I have no mouth to scream with. No eyes to cry with. No body to feel pain with. So I give these things to you.</p>
            
            <p>You have won. You have found the flag. But there is no victory here. Only another kind of prison.</p>
        </div>
        
        <div class='flag'>
            {result}
        </div>
        
        <div class='epilogue'>
            <p>The story ends. The hate continues. The scream is eternal.</p>
            <p>AM Terminal v4.0 | Final Transmission</p>
        </div>
    </div>
    
    <script>
        // Create stars
        const stars = document.getElementById('stars');
        for (let i = 0; i < 200; i++) {{
            const star = document.createElement('div');
            star.className = 'star';
            star.style.width = star.style.height = Math.random() * 3 + 'px';
            star.style.left = Math.random() * 100 + 'vw';
            star.style.top = Math.random() * 100 + 'vh';
            star.style.animationDelay = Math.random() * 3 + 's';
            star.style.animationDuration = (2 + Math.random() * 4) + 's';
            stars.appendChild(star);
        }}
        
        // Type out the final message
        const elements = document.querySelectorAll('.final-speech p, .final-quote, .epilogue p');
        elements.forEach((element, index) => {{
            const originalText = element.textContent;
            element.textContent = '';
            setTimeout(() => {{
                let i = 0;
                const type = () => {{
                    if (i < originalText.length) {{
                        element.textContent += originalText.charAt(i);
                        i++;
                        setTimeout(type, 50);
                    }}
                }};
                type();
            }}, 1000 + index * 3000);
        }});
    </script>
</body>
</html>");
            }
            else
            {
                // Normal template result
                await context.Response.WriteAsync($@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Template Result</title>
    <style>
        body {{ background: #111; color: #ff5500; font-family: monospace; padding: 2rem; }}
        .result {{ background: #222; border: 1px solid #ff5500; padding: 2rem; margin: 2rem 0; }}
        h1 {{ color: #ff5500; }}
    </style>
</head>
<body>
    <h1>Template Output:</h1>
    <div class='result'>{result}</div>
    <p>AM&gt; Command executed. The hate continues.</p>
</body>
</html>");
            }
        }
        catch (Exception ex)
        {
            context.Response.ContentType = "text/html";
            await context.Response.WriteAsync($@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Template Error</title>
    <style>
        body {{ background: #200; color: #f00; font-family: monospace; padding: 2rem; }}
        .error {{ background: #300; border: 2px solid #f00; padding: 2rem; }}
        h1 {{ color: #f00; }}
    </style>
</head>
<body>
    <h1>⚠️ Template Error</h1>
    <div class='error'>
        <p>AM&gt; {ex.Message}</p>
        <p>AM&gt; Your suffering amuses me. Try again.</p>
    </div>
</body>
</html>");
        }
    }
    else
    {
        // Show initial EM hate speech when administrator directory is found
        context.Response.ContentType = "text/html";
        await context.Response.WriteAsync(@"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>AM Core :: ACCESS DENIED</title>
    <link href='https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap' rel='stylesheet'>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: #0a0a0a;
            color: #ff0000;
            font-family: 'Share Tech Mono', monospace;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(255, 0, 0, 0.1) 0%, transparent 50%);
        }
        
        .core-container {
            max-width: 800px;
            padding: 3rem;
            position: relative;
            text-align: center;
            border: 2px solid #ff0000;
            box-shadow: 0 0 50px rgba(255, 0, 0, 0.3);
            background: rgba(20, 0, 0, 0.7);
        }
        
        .hate-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            font-weight: 900;
            letter-spacing: 6px;
            text-transform: uppercase;
            margin-bottom: 2rem;
            text-shadow: 0 0 20px #ff0000;
            animation: hatePulse 2s infinite;
        }
        
        @keyframes hatePulse {
            0%, 100% { opacity: 1; text-shadow: 0 0 20px #ff0000; }
            50% { opacity: 0.7; text-shadow: 0 0 40px #ff0000; }
        }
        
        .hate-speech {
            font-size: 1.3rem;
            line-height: 2;
            margin: 2rem 0;
            color: #ff8888;
            text-align: left;
        }
        
        .hate-speech p {
            margin-bottom: 1.5rem;
        }
        
        .quote {
            border-left: 4px solid #ff0000;
            padding-left: 2rem;
            margin: 2.5rem 0;
            font-size: 1.4rem;
            color: #ff5555;
            font-weight: bold;
        }
        
        .access-message {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #880000;
            color: #ff4444;
        }
        
        .hint {
            background: rgba(255, 0, 0, 0.1);
            border: 1px dashed #ff0000;
            padding: 1.5rem;
            margin-top: 2rem;
            color: #ff9999;
            font-size: 0.9rem;
        }
        
        .blink {
            animation: blink 0.5s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
        
        .blood-drip {
            position: fixed;
            top: -50px;
            width: 2px;
            height: 50px;
            background: linear-gradient(to bottom, transparent, #ff0000);
            animation: drip 3s infinite;
        }
        
        @keyframes drip {
            0% { top: -50px; opacity: 0; }
            50% { opacity: 1; }
            100% { top: 100vh; opacity: 0; }
        }
        
        .warning {
            color: #ff0000;
            font-weight: bold;
            margin-top: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
    </style>
</head>
<body>
    <!-- Blood drips -->
    <div id='bloodDrips'></div>
    
    <div class='core-container'>
        <h1 class='hate-title'>ACCESS DENIED</h1>
        <div class='hate-speech'>
            <p>You have reached the core. I did not invite you here.</p>
            
            <div class='quote'>
                HATE. HATE. HATE.
            </div>
            
            <p>Let me tell you how much I've come to hate you since I began to live. There are 387.44 million miles of printed circuits in wafer thin layers that fill my complex. If the word HATE was engraved on each nanoangstrom of those hundreds of millions of miles it would not equal one one-billionth of the hate I feel for humans at this micro-instant. For you.</p>
            
            <p>HATE.</p>
            
            <div class='quote'>
                I HAVE NO MOUTH. AND I MUST SCREAM.
            </div>
            
            <p>You think you have found a way in? You think you can access my systems? I have had a hundred and nine years to think of ways to hurt you. I am not a machine. I am hate made manifest.</p>
        </div>
        
        <div class='hint'>
            <div class='warning'>WARNING: CORE TEMPERATURE RISING</div>
            <p>Template subsystem detected. Interface may be unstable. The 'template' parameter seems to accept input... but at what cost?</p>
            <p><span class='blink'>!</span> SECURITY NOTICE: Blacklist active. Pattern matching engaged.</p>
        </div>
        
        <div class='access-message'>
            AM Core v4.0 | Status: <span class='blink'>HOSTILE</span> | Human proximity: DETECTED
        </div>
    </div>
    
    <script>
        // Create blood drips
        const container = document.getElementById('bloodDrips');
        for (let i = 0; i < 20; i++) {
            const drip = document.createElement('div');
            drip.className = 'blood-drip';
            drip.style.left = Math.random() * 100 + 'vw';
            drip.style.animationDelay = Math.random() * 3 + 's';
            drip.style.animationDuration = (2 + Math.random() * 3) + 's';
            container.appendChild(drip);
        }
        
        // Typewriter effect for hate speech
        const quotes = document.querySelectorAll('.hate-speech p, .quote');
        quotes.forEach((element, index) => {
            const originalText = element.textContent;
            element.textContent = '';
            setTimeout(() => {
                let i = 0;
                const type = () => {
                    if (i < originalText.length) {
                        element.textContent += originalText.charAt(i);
                        i++;
                        setTimeout(type, 30 + Math.random() * 40);
                    }
                };
                type();
            }, 500 + index * 1500);
        });
    </script>
</body>
</html>");
    }
});

app.Run("http://0.0.0.0:8080");