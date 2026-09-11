import os
import sys
import json
import math
import urllib.request
from datetime import datetime

GITHUB_USER = os.getenv("GITHUB_USER", "Alarave")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def fetch_contributions(username, token):
    if not token:
        import subprocess
        try:
            cmd = ["gh", "api", "graphql", "-f", f'query=query {{ user(login: "{username}") {{ contributionsCollection {{ contributionCalendar {{ totalContributions weeks {{ contributionDays {{ contributionCount date }} }} }} }} }} }}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Warning: gh cli failed: {e}", file=sys.stderr)
            return None

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHub-Roller-Coaster-Generator"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def parse_monthly_data(data):
    if not data or "data" not in data or not data["data"].get("user"):
        months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        counts = [12, 45, 20, 5, 60, 35, 110, 80, 25, 150, 40, 95]
        return months, counts, 677

    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal.get("totalContributions", 0)
    
    month_counts = {}
    for week in cal.get("weeks", []):
        for day in week.get("contributionDays", []):
            d_str = day["date"]
            ym = d_str[:7]
            month_counts[ym] = month_counts.get(ym, 0) + day["contributionCount"]

    sorted_ym = sorted(month_counts.keys())
    if len(sorted_ym) > 12:
        sorted_ym = sorted_ym[-12:]
    
    months = []
    counts = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for ym in sorted_ym:
        m_idx = int(ym.split("-")[1]) - 1
        months.append(month_names[m_idx])
        counts.append(month_counts[ym])

    while len(months) < 12:
        months.insert(0, "-")
        counts.insert(0, 0)

    return months, counts, total

def catmull_rom_to_bezier(pts):
    if len(pts) < 2:
        return ""
    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2

        cp1x = p1[0] + (p2[0] - p0[0]) / 6.0
        cp1y = p1[1] + (p2[1] - p0[1]) / 6.0
        cp2x = p2[0] - (p3[0] - p1[0]) / 6.0
        cp2y = p2[1] - (p3[1] - p1[1]) / 6.0

        d.append(f"C {cp1x:.1f} {cp1y:.1f}, {cp2x:.1f} {cp2y:.1f}, {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d)

def generate_svg(months, counts, total, output_path):
    width = 850
    height = 340
    margin_left = 60
    margin_right = 60
    track_width = width - margin_left - margin_right
    base_y = 230
    peak_y = 80
    
    max_count = max(counts) if max(counts) > 0 else 1

    step_x = track_width / (len(months) - 1)
    track_pts = []
    for i, c in enumerate(counts):
        x = margin_left + i * step_x
        ratio = (c / max_count)
        ratio_curved = math.pow(ratio, 0.8)
        y = base_y - (ratio_curved * (base_y - peak_y))
        track_pts.append((x, y))

    start_pt = (25, 235)
    end_pt = (825, 235)
    return_y = 285

    full_ride_pts = [start_pt] + track_pts + [end_pt]
    full_ride_pts.append((830, return_y))
    full_ride_pts.append((425, return_y + 10))
    full_ride_pts.append((20, return_y))
    full_ride_pts.append(start_pt)

    track_d = catmull_rom_to_bezier(full_ride_pts)

    supports_svg = []
    for i, (x, y) in enumerate(track_pts):
        supports_svg.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{base_y + 15}" stroke="#2e344e" stroke-width="2.5" stroke-dasharray="4,2"/>')
        if i < len(track_pts) - 1:
            next_x, next_y = track_pts[i + 1]
            supports_svg.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{next_x:.1f}" y2="{base_y + 15}" stroke="#1e2238" stroke-width="1.2"/>')
            supports_svg.append(f'<line x1="{x:.1f}" y1="{base_y + 15}" x2="{next_x:.1f}" y2="{next_y:.1f}" stroke="#1e2238" stroke-width="1.2"/>')

    labels_svg = []
    dots_svg = []
    for i, (m, c, (x, y)) in enumerate(zip(months, counts, track_pts)):
        labels_svg.append(f'<text x="{x:.1f}" y="{base_y + 35}" text-anchor="middle" fill="#7aa2f7" font-size="11" font-family="JetBrains Mono, monospace" font-weight="600">{m}</text>')
        dots_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#38bdf8" stroke="#0f172a" stroke-width="2"/>')
        if c > 0:
            dots_svg.append(f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" fill="#f77f00" font-size="9" font-family="JetBrains Mono, monospace" font-weight="bold">{c}</text>')

    import random
    random.seed(42)
    stars = []
    for _ in range(35):
        sx = random.randint(20, width - 20)
        sy = random.randint(20, base_y - 20)
        sr = random.choice([0.8, 1.2, 1.6])
        sop = random.choice([0.3, 0.6, 0.9])
        stars.append(f'<circle cx="{sx}" cy="{sy}" r="{sr}" fill="#e2e8f0" opacity="{sop}"/>')

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background: transparent;">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b132b" />
      <stop offset="50%" stop-color="#1c2541" />
      <stop offset="100%" stop-color="#0b132b" />
    </linearGradient>

    <linearGradient id="trackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#38bdf8" />
      <stop offset="35%" stop-color="#fc5c7d" />
      <stop offset="70%" stop-color="#ff9e64" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>

    <linearGradient id="cartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fc5c7d" />
      <stop offset="100%" stop-color="#f77f00" />
    </linearGradient>

    <linearGradient id="headlightGrad" x1="0%" y1="50%" x2="100%" y2="50%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0" />
    </linearGradient>

    <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <path id="coasterTrack" d="{track_d}" fill="none"/>
  </defs>

  <rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="url(#bgGrad)" stroke="#38bdf8" stroke-width="1" stroke-opacity="0.4"/>

  <g id="stars">
    {''.join(stars)}
  </g>

  <g id="header">
    <text x="30" y="38" fill="#38bdf8" font-size="16" font-family="JetBrains Mono, monospace" font-weight="800" letter-spacing="1">
      🎢 GITHUB ACTIVITY ROLLER COASTER
    </text>
    <text x="30" y="55" fill="#7aa2f7" font-size="11" font-family="JetBrains Mono, monospace">
      Passenger: @{GITHUB_USER} | Total Activity: <tspan fill="#ff9e64" font-weight="bold">{total}</tspan> Contributions
    </text>
    <rect x="{width - 160}" y="22" width="130" height="28" rx="6" fill="#1c2541" stroke="#38bdf8" stroke-opacity="0.5"/>
    <text x="{width - 95}" y="40" text-anchor="middle" fill="#38bdf8" font-size="11" font-family="JetBrains Mono, monospace" font-weight="700">
      ⚡ SPEED: 100%
    </text>
  </g>

  <line x1="20" y1="{base_y + 15}" x2="{width - 20}" y2="{base_y + 15}" stroke="#24283b" stroke-width="2"/>

  <g id="supports">
    {''.join(supports_svg)}
  </g>

  <path d="{track_d}" fill="none" stroke="#2e344e" stroke-width="2.5" stroke-dasharray="6,4"/>

  <path d="{track_d}" fill="none" stroke="url(#trackGrad)" stroke-width="4.5" filter="url(#neonGlow)"/>
  <path d="{track_d}" fill="none" stroke="#ffffff" stroke-width="1.2" stroke-opacity="0.8"/>

  <g id="dots">
    {''.join(dots_svg)}
  </g>
  <g id="labels">
    {''.join(labels_svg)}
  </g>

  <g id="train-engine">
    <polygon points="12,-2 45,-12 45,8 12,2" fill="url(#headlightGrad)"/>
    <rect x="-14" y="-9" width="28" height="13" rx="4" fill="url(#cartGrad)" stroke="#ffffff" stroke-width="1.2"/>
    <path d="M 6 -8 L 11 -2 L 6 -2 Z" fill="#38bdf8" opacity="0.9"/>
    <circle cx="-2" cy="-9" r="3.2" fill="#38bdf8"/>
    <circle cx="5" cy="-7" r="3.2" fill="#facc15"/>
    <circle cx="-8" cy="5" r="3" fill="#38bdf8" stroke="#0b132b" stroke-width="1.5"/>
    <circle cx="8" cy="5" r="3" fill="#38bdf8" stroke="#0b132b" stroke-width="1.5"/>
    <rect x="-2" y="3" width="4" height="4" fill="#ff9e64"/>

    <animateMotion dur="14s" repeatCount="indefinite" rotate="auto">
      <mpath href="#coasterTrack"/>
    </animateMotion>
  </g>

  <g id="train-cart-1">
    <rect x="-13" y="-8" width="26" height="12" rx="4" fill="#38bdf8" stroke="#ffffff" stroke-width="1.2"/>
    <circle cx="-4" cy="-8" r="3" fill="#fc5c7d"/>
    <circle cx="4" cy="-8" r="3" fill="#38bdf8"/>
    <circle cx="-7" cy="5" r="3" fill="#ff9e64" stroke="#0b132b" stroke-width="1.5"/>
    <circle cx="7" cy="5" r="3" fill="#ff9e64" stroke="#0b132b" stroke-width="1.5"/>

    <animateMotion dur="14s" begin="-0.38s" repeatCount="indefinite" rotate="auto">
      <mpath href="#coasterTrack"/>
    </animateMotion>
  </g>

  <g id="train-cart-2">
    <rect x="-13" y="-8" width="26" height="12" rx="4" fill="#f77f00" stroke="#ffffff" stroke-width="1.2"/>
    <polygon points="-13,-3 -22,-6 -13,-9" fill="#fc5c7d"/>
    <circle cx="0" cy="-8" r="3" fill="#a78bfa"/>
    <circle cx="-7" cy="5" r="3" fill="#38bdf8" stroke="#0b132b" stroke-width="1.5"/>
    <circle cx="7" cy="5" r="3" fill="#38bdf8" stroke="#0b132b" stroke-width="1.5"/>

    <animateMotion dur="14s" begin="-0.76s" repeatCount="indefinite" rotate="auto">
      <mpath href="#coasterTrack"/>
    </animateMotion>
  </g>
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Successfully generated Roller Coaster SVG at {output_path}")

def main():
    token = os.getenv("GITHUB_TOKEN", "")
    username = os.getenv("GITHUB_USER", "Alarave")
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "github-roller-coaster.svg")

    data = fetch_contributions(username, token)
    months, counts, total = parse_monthly_data(data)
    print(f"Months: {months}")
    print(f"Counts: {counts}")
    print(f"Total: {total}")
    generate_svg(months, counts, total, output_file)

if __name__ == "__main__":
    main()
