# FreelancePilot – Commercial Strategy & Distribution Guide

This document outlines the commercial roadmap, pricing models, installer packaging, and go-to-market strategy for **FreelancePilot**.

---

## 1. Product Positioning & Value Proposition

### One-Sentence Hook
> **"FreelancePilot is the private, AI-powered desktop operating system for modern freelancers, developers, and creative agencies."**

### Why Customers Choose FreelancePilot Over Cloud SaaS (Bonsai, HoneyBook, Dubsado):
1. **Zero Recurring SaaS Subscriptions for AI**: Uses free Google Gemini, Groq, and local Ollama keys. Users don't pay \$30-\$50/mo just for AI features.
2. **100% Privacy & Local Storage**: Client lists, contracts, invoices, and rates live safely in a local SQLite database on the user's PC — never uploaded to external servers.
3. **Blazing Native Performance**: Starts in under a second and uses ~80MB RAM, unlike bloated web apps.
4. **Professional Vector PDF Output**: Generates print-ready invoices and proposals.

---

## 2. Freemium Monetization Architecture

FreelancePilot is architected to support a smooth freemium upgrade path:

| Feature | Free Tier | Pro Tier (\$19/mo or \$149 Lifetime) |
| :--- | :--- | :--- |
| **Client Management** | Up to 5 Active Clients | **Unlimited Clients** |
| **Project Tracking** | Up to 5 Active Projects | **Unlimited Projects** |
| **Invoicing & PDF** | Standard Invoices with watermarking | **Custom Studio Branding & Logo** |
| **AI Providers** | Gemini, Groq, Ollama | **Gemini, Groq, Ollama + Pre-Tuned Prompts** |
| **Proposal Generator** | Standard Proposals | **Multi-Milestone PDF Proposals** |
| **SEO Studio** | Basic Meta Tags | **Full Long-Tail Keyword Clusters** |
| **Reports & Analytics** | Last 30 Days | **Full Historical LTV & CSV/PDF Audits** |
| **Backups** | Manual Snapshot | **Automated Scheduled Backups** |

---

## 3. Creating a Windows Installer Wizard (Inno Setup)

To distribute FreelancePilot commercially as a single `FreelancePilot_Setup.exe` installer:

1. Download the free [Inno Setup Compiler](https://jrsoftware.org/isdl.php).
2. Build the PyInstaller binary using `build_exe.bat`.
3. Create an `installer.iss` script pointing to the `dist\FreelancePilot\` directory:
   ```pascal
   [Setup]
   AppName=FreelancePilot
   AppVersion=1.0.0
   DefaultDirName={autopf}\FreelancePilot
   DefaultGroupName=FreelancePilot
   UninstallDisplayIcon={app}\FreelancePilot.exe
   OutputBaseFilename=FreelancePilot_Setup_v1.0.0

   [Files]
   Source: "dist\FreelancePilot\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

   [Icons]
   Name: "{group}\FreelancePilot"; Filename: "{app}\FreelancePilot.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"
   Name: "{autodesktop}\FreelancePilot"; Filename: "{app}\FreelancePilot.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"
   ```
4. Compile with Inno Setup to produce `FreelancePilot_Setup_v1.0.0.exe`.

---

## 4. Go-To-Market Launch Checklist

### A. Community Launch (Day 1 - 7)
- **ProductHunt**: Launch under "Productivity" and "Artificial Intelligence".
- **Reddit**:
  - `r/freelance`: Share as an open local tool for freelancers tired of cloud monthly fees.
  - `r/webdev` & `r/python`: Highlight the PySide6 architecture and free LLM integration.
- **Hacker News (Show HN)**: "Show HN: FreelancePilot – AI business management desktop app with free LLMs".

### B. Landing Page Copy Blueprint
- **Headline**: *Manage Your Entire Freelance Business in One High-Performance Desktop App.*
- **Subheadline**: *Create professional invoices, draft winning proposals, manage client sprints, and run free AI models on your own terms. No monthly cloud subscription required.*
- **Call-to-Action**: *Download for Windows (Free Beta)*.
