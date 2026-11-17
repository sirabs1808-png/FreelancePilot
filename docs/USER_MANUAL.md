# FreelancePilot – Official User Manual & Quick Start Guide

**FreelancePilot** is an AI-powered desktop command center for freelancers, developers, designers, agencies, and independent consultants.

---

## 1. Quick Start & Desktop Launch

### Launching the Application
- **Desktop Shortcut**: Double-click the **FreelancePilot** shortcut on your Windows Desktop.
- **Project Launcher**: Double-click `FreelancePilot.bat` inside the project folder.
- **VS Code / Terminal**:
  ```powershell
  .\.venv\Scripts\pythonw.exe main.py
  ```

---

## 2. Setting Up Free AI Services (0$ Cost)

FreelancePilot is designed from the ground up to use **free-tier AI models**. You do not need paid OpenAI or Claude subscriptions.

### A. Google Gemini Free Tier
1. Visit [Google AI Studio](https://aistudio.google.com).
2. Click **Get API key** and create a free API key.
3. In FreelancePilot, navigate to **Settings** > **Google Gemini API Key**.
4. Paste your key and click **Test Gemini**.
5. Click **Save All Settings**.

### B. Groq Developer Tier (Ultra-Fast)
1. Visit [Groq Console](https://console.groq.com).
2. Sign in with GitHub/Google and generate a free API key (starts with `gsk_`).
3. In FreelancePilot, paste your key under **Groq Developer API Key** and click **Test Groq**.

### C. Local Ollama (100% Private & Offline)
1. Download and install [Ollama](https://ollama.com) on Windows.
2. In terminal, download a free model: `ollama run llama3.2`.
3. In FreelancePilot **Settings**, click **Test Ollama** — the app will automatically detect your installed models!

---

## 3. Core Modules Guide

### 1. Executive Dashboard
- **Live Metrics**: Total earnings, monthly revenue, active clients, and pending invoice totals.
- **Revenue & Cashflow Chart**: Vector-rendered monthly gross income vs. operating expenses.
- **Active Projects**: Visual delivery progress bars and due date countdowns.
- **Deadlines**: Prioritized tasks (*Urgent*, *High*, *Medium*) with relative date alerts (*"Today"*, *"In 2 days"*).

### 2. Client Management (CRM)
- Register clients with company names, emails, phone numbers, and billing addresses.
- **View Details**: Double-click any client to inspect their lifetime billing, active projects, and invoice records.
- Instant search filter by name, company, or email.

### 3. Project Engagements
- Create projects with custom budgets, deadlines, and milestone descriptions.
- Set statuses: *Not Started*, *In Progress*, *On Hold*, *Completed*, *Cancelled*.
- Auto-calculated progress bars updated by completed tasks.

### 4. Interactive Tasks
- Click the **Done** checkbox on any task: the parent project's completion percentage updates automatically in the database!
- Overdue tasks are highlighted in red with an *Urgent/Overdue* badge.

### 5. Invoices & Billing
- **Automatic Numbering**: Sequentially generates numbers (`INV-2026-001`, `INV-2026-002`, etc.).
- **Dynamic Line Items**: Add/remove services, quantities, and unit rates.
- **Real-Time Math**: Subtotals, discounts, taxes, and totals update as you type.
- **PDF Export**: Click the 📄 **PDF** icon to export a print-ready vector PDF invoice.
- **Mark as Paid**: Instantly update collected cash and net profit.

### 6. Expense Tracking
- Log operational expenditures (*Software & SaaS*, *Hosting*, *Assets*, *Hardware*, *Travel*).
- Attach expenses to projects to track per-project profitability.
- Live Net Profit indicator ($\text{Collected Revenue} - \text{Total Expenses}$).

### 7. AI Proposal Generator
- 2-column studio: enter client details, deliverables, timeline, and budget.
- Click **✨ Generate Proposal** to produce an executive freelance proposal.
- Edit any text directly in the proposal editor.
- Click **Export PDF** to create a client-ready vector PDF proposal.

### 8. AI SEO Studio
- Generate Google-optimized **Meta Titles** (under 60 chars) and **Meta Descriptions** (under 155 chars).
- Research keyword intent clusters and build H1/H2/H3 blog post outlines.

### 9. Templates Library
- 5 pre-seeded templates (*Milestone Payment Reminder*, *Scope Creep Notice*, *Cold Outreach*, *Development Proposal*, *SEO Audit*).
- One-click **Copy to Clipboard** or create custom templates.

### 10. Reports & Analytics
- Monthly cashflow breakdowns and Client Lifetime Value (LTV) tables.
- One-click **Export CSV** (opens in Excel) and **Export PDF Report** (executive audit document).

### 11. Database Backups
- In **Settings**, click **Create Backup Snapshot** to create a backup file in `~/.freelancepilot/backups/`.
- Click **Restore From Backup** to safely roll back with automatic pre-restore protection.
