import json, os, sqlite3, threading, webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "Google Review Generator Pro"
BASE = Path(os.getenv("APPDATA", str(Path.home()))) / "GoogleReviewGeneratorPro"
BASE.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE / "reviews.db"
TOKEN_PATH = BASE / "token.json"
CREDENTIALS_PATH = BASE / "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/business.manage"]

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS drafts(
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, business TEXT,
        keywords TEXT, tone TEXT, review TEXT)""")
    con.commit()
    return con

def make_review(business, keywords, tone, length):
    words = [w.strip() for w in keywords.replace("\n", ",").split(",") if w.strip()]
    if not words:
        raise ValueError("Please enter at least one keyword.")
    # A truthful draft: no invented visit details, purchases, or claims.
    items = words[:8]
    if length == "Short":
        text = f"{business + ': ' if business else ''}A positive experience. {', '.join(items)}. Thank you!"
    elif length == "Long":
        text = (f"{business + ' — ' if business else ''}I appreciate the experience. "
                f"The points that stood out to me were {', '.join(items)}. "
                "Thank you for the service. I would be happy to recommend this business "
                "based on these points.")
    else:
        text = (f"{business + ' — ' if business else ''}A good experience, especially with "
                f"{', '.join(items)}. Thank you for the service!")
    if tone == "Professional":
        text = text.replace("A good experience", "A positive experience").replace("Thank you!", "Thank you for the service.")
    elif tone == "Friendly":
        text = text.replace("I appreciate the experience.", "Really appreciated the experience!")
        text = text.replace("Thank you for the service!", "Thanks for the great experience!")
    return text

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1100x720")
        self.minsize(920, 620)
        self.configure(bg="#f3f6fb")
        self.style = ttk.Style(self)
        try: self.style.theme_use("clam")
        except Exception: pass
        self.style.configure("TFrame", background="#f3f6fb")
        self.style.configure("TLabel", background="#f3f6fb", foreground="#1d2939", font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"), foreground="#142b4a")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#667085")
        self.style.configure("TButton", font=("Segoe UI", 10), padding=8)
        self.style.configure("Accent.TButton", background="#1769e0", foreground="white")
        self.style.configure("Treeview", rowheight=30, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.business_var = tk.StringVar()
        self.keywords_var = tk.StringVar()
        self.tone_var = tk.StringVar(value="Natural")
        self.length_var = tk.StringVar(value="Medium")
        self.location_var = tk.StringVar()
        self.account_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready — generator works offline.")
        self._build()
        self.refresh_history()
        self.refresh_stats()

    def _build(self):
        shell = ttk.Frame(self, padding=18); shell.pack(fill="both", expand=True)
        header = ttk.Frame(shell); header.pack(fill="x", pady=(0, 15))
        ttk.Label(header, text="Google Review Generator Pro", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Create honest review drafts • View reviews from a connected Google Business Profile",
                  style="Sub.TLabel").pack(anchor="w", pady=(3,0))
        self.tabs = ttk.Notebook(shell); self.tabs.pack(fill="both", expand=True)
        self.dashboard = ttk.Frame(self.tabs, padding=18)
        self.generator = ttk.Frame(self.tabs, padding=18)
        self.google = ttk.Frame(self.tabs, padding=18)
        self.settings = ttk.Frame(self.tabs, padding=18)
        self.tabs.add(self.dashboard, text="  Dashboard  ")
        self.tabs.add(self.generator, text="  Review Generator  ")
        self.tabs.add(self.google, text="  Google Reviews  ")
        self.tabs.add(self.settings, text="  Settings  ")
        self._dashboard_ui(); self._generator_ui(); self._google_ui(); self._settings_ui()
        ttk.Label(shell, textvariable=self.status_var, style="Sub.TLabel").pack(anchor="w", pady=(10,0))

    def _card(self, parent, title, value, col):
        box = tk.Frame(parent, bg="white", highlightbackground="#e3eaf3", highlightthickness=1)
        box.grid(row=0, column=col, sticky="nsew", padx=6)
        tk.Label(box, text=title, bg="white", fg="#667085", font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(14,4))
        lbl = tk.Label(box, text=value, bg="white", fg="#1769e0", font=("Segoe UI", 23, "bold"))
        lbl.pack(anchor="w", padx=16, pady=(0,14))
        return lbl

    def _dashboard_ui(self):
        ttk.Label(self.dashboard, text="Overview", style="Title.TLabel").pack(anchor="w", pady=(0,15))
        cards = ttk.Frame(self.dashboard); cards.pack(fill="x")
        for i in range(3): cards.columnconfigure(i, weight=1)
        self.drafts_card = self._card(cards, "Saved drafts", "0", 0)
        self.reviews_card = self._card(cards, "Google reviews loaded", "0", 1)
        self.rating_card = self._card(cards, "Average rating", "—", 2)
        ttk.Label(self.dashboard, text="Quick actions", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(28,10))
        actions = ttk.Frame(self.dashboard); actions.pack(anchor="w")
        ttk.Button(actions, text="Create a review draft", command=lambda:self.tabs.select(self.generator)).pack(side="left", padx=(0,8))
        ttk.Button(actions, text="Connect Google Business Profile", command=lambda:self.tabs.select(self.settings)).pack(side="left")
        note = ("Google connection is optional. Draft generation and saved history work offline. "
                "Google review access requires an authorized Business Profile, approved API access, "
                "and your own OAuth credentials.")
        ttk.Label(self.dashboard, text=note, wraplength=850, style="Sub.TLabel").pack(anchor="w", pady=(28,0))

    def _generator_ui(self):
        ttk.Label(self.generator, text="Create a review draft", style="Title.TLabel").pack(anchor="w", pady=(0,12))
        form = ttk.Frame(self.generator); form.pack(fill="x")
        ttk.Label(form, text="Business name (optional)").grid(row=0,column=0,sticky="w",pady=6)
        ttk.Entry(form, textvariable=self.business_var, width=60).grid(row=0,column=1,sticky="ew",pady=6)
        ttk.Label(form, text="Keywords / real experience points (comma separated)").grid(row=1,column=0,sticky="w",pady=6)
        ttk.Entry(form, textvariable=self.keywords_var, width=60).grid(row=1,column=1,sticky="ew",pady=6)
        ttk.Label(form, text="Writing style").grid(row=2,column=0,sticky="w",pady=6)
        ttk.Combobox(form, textvariable=self.tone_var, values=["Natural","Professional","Friendly"], state="readonly", width=20).grid(row=2,column=1,sticky="w",pady=6)
        ttk.Label(form, text="Length").grid(row=3,column=0,sticky="w",pady=6)
        ttk.Combobox(form, textvariable=self.length_var, values=["Short","Medium","Long"], state="readonly", width=20).grid(row=3,column=1,sticky="w",pady=6)
        form.columnconfigure(1, weight=1)
        ttk.Button(self.generator, text="Generate review", command=self.generate).pack(anchor="w",pady=12)
        ttk.Label(self.generator, text="Generated draft — edit it to match the customer's genuine experience").pack(anchor="w")
        self.output = tk.Text(self.generator, height=8, wrap="word", font=("Segoe UI", 11), relief="solid", bd=1)
        self.output.pack(fill="both", expand=True, pady=(6,8))
        buttons = ttk.Frame(self.generator); buttons.pack(anchor="w")
        ttk.Button(buttons, text="Copy draft", command=self.copy_draft).pack(side="left", padx=(0,8))
        ttk.Button(buttons, text="Save draft", command=self.save_draft).pack(side="left")
        ttk.Label(self.generator, text="This tool creates drafts only. It does not create, post, or fabricate customer reviews.",
                  style="Sub.TLabel").pack(anchor="w",pady=(10,0))

    def _google_ui(self):
        top = ttk.Frame(self.google); top.pack(fill="x")
        ttk.Label(top, text="Google Business Profile reviews", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Refresh reviews", command=self.load_reviews).pack(side="right")
        self.review_tree = ttk.Treeview(self.google, columns=("rating","reviewer","date","comment"), show="headings")
        for c,t,w in [("rating","Rating",85),("reviewer","Reviewer",150),("date","Date",150),("comment","Review",550)]:
            self.review_tree.heading(c,text=t); self.review_tree.column(c,width=w,anchor="w")
        self.review_tree.pack(fill="both",expand=True,pady=12)
        self.google_info = ttk.Label(self.google, text="Connect your Google Business Profile in Settings to load reviews.", style="Sub.TLabel")
        self.google_info.pack(anchor="w")

    def _settings_ui(self):
        ttk.Label(self.settings, text="Google connection settings", style="Title.TLabel").pack(anchor="w",pady=(0,12))
        ttk.Label(self.settings, text="Step 1 — Add your Google OAuth desktop client file").pack(anchor="w")
        ttk.Label(self.settings, text=f"Expected file: {CREDENTIALS_PATH}", style="Sub.TLabel").pack(anchor="w",pady=4)
        row = ttk.Frame(self.settings); row.pack(anchor="w",pady=8)
        ttk.Button(row, text="Choose credentials.json", command=self.choose_credentials).pack(side="left",padx=(0,8))
        ttk.Button(row, text="Connect Google account", command=self.connect_google).pack(side="left")
        ttk.Separator(self.settings).pack(fill="x",pady=16)
        ttk.Label(self.settings, text="Step 2 — Select your business location").pack(anchor="w")
        ttk.Label(self.settings, text="Account").pack(anchor="w",pady=(8,2))
        self.account_combo = ttk.Combobox(self.settings,textvariable=self.account_var,state="readonly",width=75)
        self.account_combo.pack(anchor="w")
        ttk.Label(self.settings, text="Location").pack(anchor="w",pady=(8,2))
        self.location_combo = ttk.Combobox(self.settings,textvariable=self.location_var,state="readonly",width=75)
        self.location_combo.pack(anchor="w")
        ttk.Button(self.settings,text="Load locations",command=self.load_locations).pack(anchor="w",pady=8)
        ttk.Label(self.settings, text="Google API setup guide is included in the downloaded ZIP (README.md).",
                  style="Sub.TLabel").pack(anchor="w",pady=(14,0))

    def generate(self):
        try:
            draft = make_review(self.business_var.get().strip(), self.keywords_var.get(), self.tone_var.get(), self.length_var.get())
            self.output.delete("1.0","end"); self.output.insert("1.0",draft)
            self.status_var.set("Draft generated. Please verify it reflects the real experience.")
        except Exception as e: messagebox.showwarning("Missing keywords",str(e))

    def copy_draft(self):
        value=self.output.get("1.0","end").strip()
        if value:
            self.clipboard_clear(); self.clipboard_append(value); self.status_var.set("Draft copied to clipboard.")

    def save_draft(self):
        value=self.output.get("1.0","end").strip()
        if not value: return messagebox.showinfo("No draft","Generate a draft first.")
        con=db(); con.execute("INSERT INTO drafts(created,business,keywords,tone,review) VALUES(?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"),self.business_var.get(),self.keywords_var.get(),self.tone_var.get(),value))
        con.commit(); con.close(); self.refresh_history(); self.refresh_stats()
        self.status_var.set("Draft saved locally.")

    def refresh_history(self):
        # History is stored locally in SQLite; dashboard counts saved drafts.
        pass

    def refresh_stats(self):
        con=db()
        n=con.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
        con.close()
        self.drafts_card.config(text=str(n))

    def choose_credentials(self):
        p=filedialog.askopenfilename(title="Select Google OAuth credentials",filetypes=[("JSON files","*.json")])
        if p:
            try:
                data=json.loads(Path(p).read_text(encoding="utf-8"))
                if "installed" not in data and "web" not in data: raise ValueError("This is not an OAuth client JSON file.")
                CREDENTIALS_PATH.write_text(json.dumps(data),encoding="utf-8")
                messagebox.showinfo("Credentials added",f"Saved securely for this Windows user at:\\n{CREDENTIALS_PATH}")
            except Exception as e: messagebox.showerror("Invalid file",str(e))

    def _google_service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        if not TOKEN_PATH.exists(): raise RuntimeError("Connect your Google account first.")
        creds=Credentials.from_authorized_user_file(str(TOKEN_PATH),SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request()); TOKEN_PATH.write_text(creds.to_json(),encoding="utf-8")
        return build("mybusiness","v4",credentials=creds,cache_discovery=False)

    def connect_google(self):
        if not CREDENTIALS_PATH.exists():
            return messagebox.showwarning("Credentials needed","Choose your Google OAuth credentials.json first. See README.md.")
        def work():
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow=InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH),SCOPES)
                creds=flow.run_local_server(port=0, open_browser=True)
                TOKEN_PATH.write_text(creds.to_json(),encoding="utf-8")
                self.after(0,lambda:self.status_var.set("Google account connected."))
                self.after(0,lambda:messagebox.showinfo("Connected","Google account authorization successful. Now load locations."))
            except Exception as e:
                self.after(0,lambda:messagebox.showerror("Google connection failed",str(e)))
        self.status_var.set("Opening Google sign-in…")
        threading.Thread(target=work,daemon=True).start()

    def load_locations(self):
        def work():
            try:
                svc=self._google_service()
                result=svc.accounts().list().execute()
                accounts=result.get("accounts",[])
                if not accounts: raise RuntimeError("No Business Profile accounts found for this Google account.")
                self.accounts=accounts
                labels=[f'{a.get("accountName",a.get("name"))}  ({a.get("name")})' for a in accounts]
                self.after(0,lambda:self.account_combo.configure(values=labels))
                self.after(0,lambda:self.account_combo.current(0))
                self.after(0,lambda:self.status_var.set(f"Found {len(accounts)} account(s). Select one and click Load locations again."))
                if self.account_var.get():
                    idx=self.account_combo.current()
                    if idx>=0:
                        locs=svc.accounts().locations().list(parent=accounts[idx]["name"],pageSize=100).execute().get("locations",[])
                        self.locations=locs
                        opts=[f'{x.get("locationName",x.get("name"))}  ({x.get("name")})' for x in locs]
                        self.after(0,lambda:self.location_combo.configure(values=opts))
                        if opts: self.after(0,lambda:self.location_combo.current(0))
            except Exception as e: self.after(0,lambda:messagebox.showerror("Could not load locations",str(e)))
        # If account already selected, second click fetches locations.
        threading.Thread(target=work,daemon=True).start()

    def load_reviews(self):
        if not hasattr(self,"locations") or not self.locations:
            messagebox.showinfo("Select location","Open Settings, connect Google, then load and select a location."); return
        idx=self.location_combo.current()
        if idx<0: messagebox.showinfo("Select location","Select a location in Settings first."); return
        loc=self.locations[idx]
        parent=loc.get("name","")
        account_name=parent.split("/locations/")[0]
        def work():
            try:
                svc=self._google_service()
                data=svc.accounts().locations().reviews().list(parent=parent,pageSize=50,orderBy="updateTime desc").execute()
                reviews=data.get("reviews",[])
                def update():
                    for item in self.review_tree.get_children(): self.review_tree.delete(item)
                    ratings=[]
                    for r in reviews:
                        rating=r.get("starRating","")
                        ratings.append({"ONE":1,"TWO":2,"THREE":3,"FOUR":4,"FIVE":5}.get(rating,0))
                        reviewer=r.get("reviewer",{}).get("displayName","Google user")
                        date=r.get("createTime","")[:10]
                        comment=r.get("comment","")
                        self.review_tree.insert("","end",values=(rating,reviewer,date,comment))
                    valid=[x for x in ratings if x]
                    avg=round(sum(valid)/len(valid),2) if valid else "—"
                    self.reviews_card.config(text=str(len(reviews)))
                    self.rating_card.config(text=str(avg))
                    self.google_info.config(text=f"Loaded {len(reviews)} review(s) for {loc.get('locationName',parent)}.")
                    self.status_var.set("Google reviews refreshed.")
                self.after(0,update)
            except Exception as e: self.after(0,lambda:messagebox.showerror("Review loading failed",str(e)))
        self.status_var.set("Loading Google reviews…")
        threading.Thread(target=work,daemon=True).start()

if __name__ == "__main__":
    App().mainloop()
