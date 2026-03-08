import customtkinter as ctk
import threading
import tkinter as tk
import os
import csv
from backend import LegalEngine  

# ── Appearance ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Theme Presets ──────────────────────────────────────────────────────────────
THEMES = {
    "Executive Dark": {
        "bg":            "#0D0F14",
        "surface":       "#13161E",
        "surface_2":     "#1B1F2B",
        "border":        "#252A38",
        "accent":        "#C9A84C",
        "accent_dim":    "#8A6E2F",
        "text_primary":  "#E8E6DF",
        "text_secondary":"#7A8099",
        "text_dim":      "#3D4357",
        "positive":      "#3DAA72",
        "warning":       "#C9A84C",
        "danger":        "#C95C4C",
        "blue_soft":     "#3A6EA8",
        "dem_blue":      "#1A4F8A",
        "dem_light":     "#4A90D9",
        "rep_red":       "#8A1A1A",
        "rep_light":     "#D94A4A",
        "ind_purple":    "#5A3A8A",
        "ind_light":     "#9B72D4",
        "ctk_mode":      "Dark",
    },
    "Midnight Blue": {
        "bg":            "#070D1A",
        "surface":       "#0D1628",
        "surface_2":     "#132035",
        "border":        "#1E2E4A",
        "accent":        "#4FC3F7",
        "accent_dim":    "#2A7DA8",
        "text_primary":  "#E3EEF7",
        "text_secondary":"#6A8BAA",
        "text_dim":      "#2E3F55",
        "positive":      "#43C98A",
        "warning":       "#F7C948",
        "danger":        "#E05252",
        "blue_soft":     "#4FC3F7",
        "dem_blue":      "#1A4F8A",
        "dem_light":     "#4A90D9",
        "rep_red":       "#8A1A1A",
        "rep_light":     "#D94A4A",
        "ind_purple":    "#5A3A8A",
        "ind_light":     "#9B72D4",
        "ctk_mode":      "Dark",
    },
    "Forest": {
        "bg":            "#0A1209",
        "surface":       "#111A10",
        "surface_2":     "#182518",
        "border":        "#243524",
        "accent":        "#7EC850",
        "accent_dim":    "#4E8230",
        "text_primary":  "#E2ECD8",
        "text_secondary":"#6A8A60",
        "text_dim":      "#2E4228",
        "positive":      "#50C87E",
        "warning":       "#C8B450",
        "danger":        "#C85050",
        "blue_soft":     "#5088C8",
        "dem_blue":      "#1A4F8A",
        "dem_light":     "#4A90D9",
        "rep_red":       "#8A1A1A",
        "rep_light":     "#D94A4A",
        "ind_purple":    "#5A3A8A",
        "ind_light":     "#9B72D4",
        "ctk_mode":      "Dark",
    },
    "Ivory (Light)": {
        "bg":            "#F4F0E8",
        "surface":       "#EDEAE0",
        "surface_2":     "#E2DDD2",
        "border":        "#C8C2B4",
        "accent":        "#8B4513",
        "accent_dim":    "#5C2D0A",
        "text_primary":  "#1A1612",
        "text_secondary":"#5A5040",
        "text_dim":      "#A89A88",
        "positive":      "#2E7D32",
        "warning":       "#8B6914",
        "danger":        "#B71C1C",
        "blue_soft":     "#1565C0",
        "dem_blue":      "#1A4F8A",
        "dem_light":     "#1565C0",
        "rep_red":       "#8A1A1A",
        "rep_light":     "#C62828",
        "ind_purple":    "#5A3A8A",
        "ind_light":     "#6A1B9A",
        "ctk_mode":      "Light",
    },
    "Crimson": {
        "bg":            "#130808",
        "surface":       "#1E0D0D",
        "surface_2":     "#2A1212",
        "border":        "#3D1A1A",
        "accent":        "#E05252",
        "accent_dim":    "#A03030",
        "text_primary":  "#F0E0E0",
        "text_secondary":"#9A6A6A",
        "text_dim":      "#4A2A2A",
        "positive":      "#52A070",
        "warning":       "#E0A052",
        "danger":        "#E05252",
        "blue_soft":     "#5080C0",
        "dem_blue":      "#1A4F8A",
        "dem_light":     "#4A90D9",
        "rep_red":       "#8A1A1A",
        "rep_light":     "#D94A4A",
        "ind_purple":    "#5A3A8A",
        "ind_light":     "#9B72D4",
        "ctk_mode":      "Dark",
    },
}

# ── Active palette (mutable — updated on theme change) ────────────────────────
PALETTE = dict(THEMES["Executive Dark"])
CURRENT_THEME = ["Executive Dark"]  # mutable container so panels can read it

# ── Party Data ────────────────────────────────────────────────────────────────

PARTY_DATA = {
    "Democrat": {
        "color":     PALETTE["dem_light"],
        "dim_color": PALETTE["dem_blue"],
        "symbol":    "🫏",
        "tagline":   "Progress, Equity & Opportunity",
        "description": (
            "The Democratic Party, founded in 1828, is one of the two major "
            "contemporary political parties in the United States. It broadly "
            "advocates for social justice, regulated markets, and an active "
            "federal government role in addressing inequality."
        ),
        "core_goals": [
            ("Healthcare",        "Universal or expanded access; protect and strengthen the ACA."),
            ("Climate",           "Aggressive transition to clean energy; rejoin Paris Agreement."),
            ("Economy",           "Higher minimum wage, tax increases on corporations and wealthy."),
            ("Education",         "Expand public education funding, reduce student debt burden."),
            ("Civil Rights",      "Protect voting rights, LGBTQ+ equality, racial equity policies."),
            ("Immigration",       "Path to citizenship for undocumented residents; DACA protection."),
            ("Gun Policy",        "Universal background checks, assault weapons restrictions."),
            ("Social Safety Net", "Expand Medicaid, Social Security, and housing assistance."),
        ],
        "recent_impacts": [
            ("Inflation Reduction Act (2022)",  "~$369B in climate & energy investment; extended ACA subsidies."),
            ("American Rescue Plan (2021)",     "$1.9T COVID relief; child tax credit cut child poverty by ~30%."),
            ("Infrastructure Law (2021)",       "$1.2T for roads, bridges, broadband, and clean water."),
            ("Student Debt Relief",             "Ongoing efforts to cancel and restructure federal student loans."),
            ("CHIPS & Science Act (2022)",      "~$53B to revive domestic semiconductor manufacturing."),
        ],
    },
    "Republican": {
        "color":     PALETTE["rep_light"],
        "dim_color": PALETTE["rep_red"],
        "symbol":    "🐘",
        "tagline":   "Freedom, Free Markets & Traditional Values",
        "description": (
            "The Republican Party, founded in 1854, is the other major U.S. "
            "political party. It generally advocates for lower taxes, reduced "
            "government regulation, free-market economics, strong national "
            "defence, and traditional social values."
        ),
        "core_goals": [
            ("Economy",       "Cut taxes, reduce regulation, prioritise business growth."),
            ("Immigration",   "Secure borders; enforce existing law; reduce illegal immigration."),
            ("Gun Rights",    "Protect Second Amendment rights; oppose new firearms restrictions."),
            ("Military",      "Increase defence spending; project strength internationally."),
            ("Energy",        "Expand domestic fossil fuel production; energy independence."),
            ("Healthcare",    "Repeal ACA mandates; promote market-based health solutions."),
            ("Education",     "School choice, charter schools, parental curriculum rights."),
            ("Judicial",      "Appoint originalist judges; limit federal judicial overreach."),
        ],
        "recent_impacts": [
            ("Tax Cuts & Jobs Act (2017)",   "Cut corporate tax rate from 35% to 21%; individual rate reductions."),
            ("Three Supreme Court Seats",    "Confirmed Gorsuch, Kavanaugh, and Barrett — shifting court balance."),
            ("Dobbs v. Jackson (2022)",      "Overturned Roe v. Wade, returning abortion regulation to states."),
            ("Abraham Accords (2020)",       "Brokered Israel–UAE, Israel–Bahrain, and other normalisation deals."),
            ("Operation Warp Speed (2020)",  "Accelerated COVID-19 vaccine development in under 12 months."),
        ],
    },
    "Independent / Third Party": {
        "color":     PALETTE["ind_light"],
        "dim_color": PALETTE["ind_purple"],
        "symbol":    "⚖",
        "tagline":   "Beyond the Two-Party System",
        "description": (
            "Third parties and independents occupy a wide ideological spectrum "
            "outside the two-party duopoly. Notable parties include the Libertarian "
            "Party, Green Party, and Constitution Party, each offering distinct "
            "policy visions often ignored by the major parties."
        ),
        "core_goals": [
            ("Libertarian: Liberty",   "Maximise individual freedom; drastically shrink federal government."),
            ("Libertarian: Economy",   "Free markets, end the Federal Reserve, legalise victimless crimes."),
            ("Green: Environment",     "Green New Deal, 100% renewables, end fossil fuel subsidies."),
            ("Green: Justice",         "Social and economic justice; universal healthcare; demilitarise police."),
            ("Constitution: Founding", "Strict constitutional originalism; return power to states."),
            ("Constitution: Fiscal",   "End deficit spending, return to commodity-backed currency."),
            ("Reform: Electoral",      "Ranked-choice voting, campaign finance reform, term limits."),
            ("Common Goal",            "Break the duopoly; give voters more meaningful choices."),
        ],
        "recent_impacts": [
            ("2024 Spoiler Effect",      "Independent candidates influenced outcomes in several Senate races."),
            ("Ranked-Choice Adoption",   "Alaska and Maine now use RCV for federal elections."),
            ("Libertarian Ballot Access","Libertarians achieved ballot access in all 50 states in 2024 cycle."),
            ("Green Policy Influence",   "Green New Deal language adopted into mainstream Democratic platform."),
            ("Ross Perot Legacy",        "1992 independent run (19% popular vote) reshaped debate on deficits."),
        ],
    },
}

# ── Wars Data ─────────────────────────────────────────────────────────────────
# status: "historical" | "ongoing"
# Each entry: name, years, us_deaths, status, color_key, summary, impacts[]

WARS_DATA = [
    {
        "name":      "Operation Epic Fury — Iran War",
        "years":     "2026 – Ongoing",
        "us_deaths": "6 confirmed (18+ seriously wounded)",
        "status":    "ongoing",
        "summary": (
            "On February 28, 2026, the United States and Israel launched joint airstrikes "
            "(Operation Epic Fury) against military, nuclear, and government targets across "
            "Iran, including Tehran, Isfahan, Qom, and other cities. Supreme Leader Ali "
            "Khamenei was killed in the initial strikes along with senior IRGC commanders. "
            "Iran retaliated with missile and drone strikes across nine neighbouring countries. "
            "As of March 8, 2026, major combat operations are ongoing. Trump stated a "
            "four-to-five-week operational timeline."
        ),
        "impacts": [
            ("US Casualties",          "6 service members killed in action (Army reservists in Kuwait); 18+ seriously wounded. First KIA of Trump's second term."),
            ("Khamenei Killed",        "Supreme Leader Ali Khamenei assassinated in initial strikes — first killing of an Iranian head of state by a foreign power."),
            ("Nuclear Programme",      "Multiple Iranian nuclear facilities destroyed or severely damaged, including sites at Natanz, Isfahan, and Fordow."),
            ("Regional Destabilisation","Iran struck targets in Bahrain, Kuwait, UAE, Saudi Arabia, Qatar, Oman, Iraq, Jordan and Cyprus — threatening Gulf energy infrastructure."),
            ("Oil & Markets",          "Global oil prices surged sharply; Strait of Hormuz traffic disrupted, raising fears of supply shocks."),
            ("Diplomatic Fallout",     "Russia condemned strikes as 'unprovoked aggression'; China called for restraint; NATO allies split on support."),
            ("War Powers Dispute",     "Democrats and some Republicans moved to force a War Powers Act vote challenging Trump's authority to strike without Congress."),
        ],
    },
    {
        "name":      "War in Afghanistan",
        "years":     "2001 – 2021",
        "us_deaths": "2,461",
        "status":    "historical",
        "summary": (
            "Launched after the September 11 attacks, the US-led invasion toppled the Taliban "
            "government harbouring al-Qaeda. The war became the longest in American history, "
            "spanning four presidencies. The US withdrew in August 2021 under the Doha Agreement, "
            "and the Taliban retook control within days."
        ),
        "impacts": [
            ("Taliban Ousted & Returned",  "Taliban regime toppled in 2001; returned to full power within days of US withdrawal in August 2021."),
            ("Al-Qaeda Disrupted",         "Al-Qaeda's operational capacity severely degraded; Osama bin Laden killed in Pakistan in 2011."),
            ("Civilian Cost",              "Estimated 46,000+ Afghan civilians killed; 5.9 million displaced at peak of conflict."),
            ("Financial Cost",             "Estimated $2.3 trillion total US expenditure including veteran care over decades."),
            ("Nation-Building Failure",    "Afghan government and 300,000-strong army collapsed in days; $83B in US-funded equipment abandoned or seized."),
            ("Veterans Crisis",            "Over 20,000 US troops wounded; ongoing PTSD and suicide epidemic among veterans."),
        ],
    },
    {
        "name":      "Iraq War",
        "years":     "2003 – 2011 (2014–2021 re-engagement)",
        "us_deaths": "4,431 (2003–2011) + 96 (2014–2021)",
        "status":    "historical",
        "summary": (
            "The US invaded Iraq in March 2003 citing weapons of mass destruction that were "
            "never found. Saddam Hussein's regime fell within weeks. The subsequent occupation "
            "triggered a prolonged insurgency and sectarian civil war. The US re-engaged in "
            "2014 to fight ISIS after it seized large swaths of Iraqi territory."
        ),
        "impacts": [
            ("WMD Pretext Discredited",    "No weapons of mass destruction found; eroded US credibility and public trust in intelligence."),
            ("Saddam Hussein Removed",     "Regime toppled; Saddam captured in December 2003 and executed in 2006."),
            ("Sectarian Civil War",        "Power vacuum enabled Sunni–Shia–Kurdish conflict; ~150,000+ Iraqi civilian deaths 2003–2011."),
            ("Rise of ISIS",               "Al-Qaeda in Iraq evolved into ISIS, which seized territory across Iraq and Syria by 2014."),
            ("Financial Cost",             "Estimated $2 trillion+ in direct costs; $4–6 trillion including long-term veteran care."),
            ("Regional Iranian Influence", "Removal of Saddam dramatically expanded Iranian influence in Iraq and across the region."),
        ],
    },
    {
        "name":      "Vietnam War",
        "years":     "1955 – 1975",
        "us_deaths": "58,220",
        "status":    "historical",
        "summary": (
            "The US intervened to prevent the communist North from unifying Vietnam under Ho Chi Minh. "
            "Despite massive military force, the US failed to achieve a decisive victory. The fall of "
            "Saigon in April 1975 marked a humiliating withdrawal and profound national trauma."
        ),
        "impacts": [
            ("Communist Unification",      "North Vietnam unified the country under communist rule in 1975; remained so today."),
            ("The Draft & Protests",       "Anti-war movement reshaped American politics; widespread civil unrest and generational mistrust of government."),
            ("War Powers Act (1973)",      "Congress passed the War Powers Resolution limiting presidential power to commit troops without approval."),
            ("Agent Orange Legacy",        "3 million+ Vietnamese and thousands of US veterans affected by chemical defoliant exposure."),
            ("Refugee Crisis",             "Over 800,000 Vietnamese 'boat people' fled after the war; millions more displaced."),
            ("Military Doctrine Shift",    "Led to the all-volunteer military (1973) and the 'Vietnam Syndrome' — reluctance to commit ground troops."),
        ],
    },
    {
        "name":      "Korean War",
        "years":     "1950 – 1953",
        "us_deaths": "36,574",
        "status":    "historical",
        "summary": (
            "After North Korea invaded South Korea in June 1950, the US led a UN coalition to "
            "defend the South. China entered the war when US forces approached the Chinese border. "
            "An armistice in 1953 restored the pre-war border — technically, the war never ended."
        ),
        "impacts": [
            ("Divided Peninsula",          "Korea remains divided at the 38th parallel; armistice, not peace treaty, still in effect."),
            ("US-South Korea Alliance",    "Forged a permanent security alliance; ~28,500 US troops remain stationed in South Korea today."),
            ("Cold War Precedent",         "Established the doctrine of limited war and containment as alternatives to nuclear conflict."),
            ("Chinese Military Prestige",  "China's ability to fight the US to a standstill elevated its global and regional standing."),
            ("NATO Expansion",             "War accelerated West German rearmament and NATO's military buildup in Europe."),
        ],
    },
    {
        "name":      "World War II",
        "years":     "1941 – 1945",
        "us_deaths": "405,399",
        "status":    "historical",
        "summary": (
            "The US entered WWII after the Japanese attack on Pearl Harbor on December 7, 1941. "
            "Fighting on two fronts — Europe and the Pacific — the US played a decisive role "
            "in defeating Nazi Germany and Imperial Japan. The war ended with atomic bombings "
            "of Hiroshima and Nagasaki in August 1945."
        ),
        "impacts": [
            ("Allied Victory",             "Defeated Nazi Germany, Fascist Italy, and Imperial Japan; liberated occupied Europe and Asia."),
            ("Atomic Age Begins",          "US dropped atomic bombs on Hiroshima & Nagasaki — 110,000–210,000 killed; reshaped global strategy forever."),
            ("United Nations Founded",     "Post-war order established the UN, World Bank, and IMF to prevent future global conflicts."),
            ("US Superpower Status",       "US emerged as the world's dominant military and economic power with ~50% of global GDP."),
            ("Holocaust & Nuremberg",      "Liberation of Nazi death camps; Nuremberg Trials established international law on war crimes."),
            ("Cold War Origins",           "US-Soviet tensions over post-war Europe directly triggered the Cold War and nuclear arms race."),
        ],
    },
    {
        "name":      "World War I",
        "years":     "1917 – 1918",
        "us_deaths": "116,516",
        "status":    "historical",
        "summary": (
            "The US entered WWI in April 1917 after German submarine warfare threatened US ships "
            "and the Zimmermann Telegram revealed German overtures to Mexico. Fresh American troops "
            "and resources tipped the balance, leading to Allied victory and the Armistice of "
            "November 11, 1918."
        ),
        "impacts": [
            ("Allied Victory",             "2 million US troops deployed to Europe; American manpower and resources were decisive in the final offensive."),
            ("Versailles Treaty",          "Harsh reparations on Germany planted seeds for WWII; US Senate rejected the treaty and League of Nations."),
            ("Isolationism Reaffirmed",    "US retreated into isolationism through the 1920s–30s, refusing League membership."),
            ("Espionage & Sedition Acts",  "Sweeping domestic surveillance and suppression of anti-war speech set civil liberties precedents."),
            ("Spanish Flu Amplified",      "Troop movements spread the 1918 influenza pandemic that killed 50–100 million worldwide."),
        ],
    },
    {
        "name":      "Gulf War",
        "years":     "1990 – 1991",
        "us_deaths": "383",
        "status":    "historical",
        "summary": (
            "After Iraq invaded Kuwait in August 1990, a US-led coalition of 35 nations launched "
            "Operation Desert Storm in January 1991. The 100-hour ground war liberated Kuwait and "
            "decimated Iraq's military. President George H.W. Bush chose not to march on Baghdad."
        ),
        "impacts": [
            ("Kuwait Liberated",           "Iraqi forces expelled from Kuwait in 100 hours of ground combat; ceasefire declared February 28, 1991."),
            ("Limited Objectives Debate",  "Decision not to remove Saddam Hussein led to continued US presence and the 2003 war."),
            ("'New World Order'",          "Bush declared a 'New World Order' of US-led collective security backed by UN mandate."),
            ("Military Technology",        "Showcased precision-guided munitions, stealth aircraft, and network-centric warfare to the world."),
            ("US Bases in Saudi Arabia",   "Permanent US military presence in Saudi Arabia inflamed Islamist sentiment, cited by bin Laden as a grievance."),
        ],
    },
    {
        "name":      "War on Terror / Global Operations",
        "years":     "2001 – Present",
        "us_deaths": "7,074+ (all post-9/11 operations)",
        "status":    "ongoing",
        "summary": (
            "Following 9/11, the US launched a global counterterrorism campaign spanning "
            "Afghanistan, Iraq, Syria, Somalia, Yemen, Libya, the Philippines, and beyond. "
            "Operations continue today under various authorisations, targeting al-Qaeda, "
            "ISIS, and affiliated groups."
        ),
        "impacts": [
            ("Homeland Security Created",  "DHS established; TSA, FISA expansion, and PATRIOT Act transformed domestic surveillance."),
            ("Drone Warfare Normalised",   "US drone strikes conducted in 7+ countries; set global precedent for remote targeted killing."),
            ("Bin Laden Killed",           "Osama bin Laden killed in Abbottabad, Pakistan, on May 2, 2011 by SEAL Team Six."),
            ("ISIS Rise & Fall",           "ISIS declared caliphate 2014; US-led coalition degraded it by 2019; leader al-Baghdadi killed."),
            ("Civil Liberties Erosion",    "Mass surveillance programs (PRISM etc.) revealed by Snowden in 2013; ongoing legal battles."),
            ("Veteran Mental Health",      "Estimated 30% of post-9/11 veterans experience PTSD; suicide rates exceed combat deaths."),
        ],
    },
]

# ── Components ─────────────────────────────────────────────────────────────────

class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, command, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            corner_radius=8,
            height=45,
            fg_color="transparent",
            text_color=PALETTE["text_secondary"],
            hover_color=PALETTE["surface_2"],
            anchor="w",
            font=("Georgia", 13, "bold"),
            **kwargs
        )


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select):
        super().__init__(master, fg_color=PALETTE["surface"], width=240, corner_radius=0)
        self.on_select = on_select
        self._active   = None

        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=30)

        ctk.CTkLabel(brand_frame, text="EXECUTIVE", font=("Georgia", 20, "bold"),
                     text_color=PALETTE["accent"]).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="INSIGHT", font=("Courier New", 12, "bold"),
                     text_color=PALETTE["text_secondary"]).pack(anchor="w")

        ctk.CTkFrame(self, height=1, fg_color=PALETTE["border"]).pack(fill="x", padx=16, pady=(0, 10))

        self._nav_btns = {}

        nav_items = [
            ("Dashboard",   "  Dashboard"),
            ("Legal Q&A",   "  Legal Q&A"),
            ("Bills",       "  Bills"),
            ("Party Impact","  Party Impact"),
            ("US Wars",     "  US Wars"),
            ("Gov. History","  Gov. History"),
        ]
        for key, label in nav_items:
            btn = SidebarButton(self, label, lambda k=key: on_select(k))
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_btns[key] = btn

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=10, pady=20)
        ctk.CTkFrame(footer, height=1, fg_color=PALETTE["border"]).pack(fill="x", pady=(0, 10))
        settings_btn = SidebarButton(footer, "  Settings", lambda: on_select("Settings"))
        settings_btn.pack(fill="x")
        self._nav_btns["Settings"] = settings_btn

    def set_active(self, name):
        """Highlight the active nav button, reset all others."""
        for key, btn in self._nav_btns.items():
            if key == name:
                btn.configure(
                    fg_color=PALETTE["surface_2"],
                    text_color=PALETTE["accent"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=PALETTE["text_secondary"],
                )
        self._active = name


# ── Panels ────────────────────────────────────────────────────────────────────

class DashboardPanel(ctk.CTkFrame):

    # ── Recent events feed ────────────────────────────────────────────────────
    # Each entry: (date, category, headline, detail, color_key)
    EVENTS = [
        (
            "Mar 8, 2026", "WAR",
            "US–Iran War: 6 US KIA, operations ongoing",
            "Operation Epic Fury airstrikes launched Feb 28 with Israel. Supreme Leader Khamenei killed. "
            "US casualties confirmed at 6 KIA (Army reservists, Kuwait). Trump states 4–5 week timeline.",
            "danger",
        ),
        (
            "Feb 14, 2026", "GOVERNMENT",
            "DHS Partial Shutdown begins",
            "Second federal shutdown of 2026 began after Senate Democrats blocked DHS funding bill "
            "following the killing of Alex Pretti by CBP agents on Jan 24. Immigration agencies operating "
            "on mandatory funding and fees.",
            "warning",
        ),
        (
            "Feb 3, 2026", "GOVERNMENT",
            "4-day federal shutdown ends",
            "The Jan 31 – Feb 3 partial shutdown ended after Congress passed a continuing resolution. "
            "Seven Republicans joined all Democrats in initially blocking the funding package over DHS "
            "reform disagreements.",
            "positive",
        ),
        (
            "Jan 1, 2026", "POLICY",
            "Expanded Travel Ban takes effect — 39 countries",
            "Presidential Proclamation 10998 (Dec 16, 2025) expanded entry restrictions to nationals "
            "of 39 countries plus Palestinian Authority travel document holders. 19 countries face full "
            "suspension; 20 face partial suspension.",
            "accent",
        ),
        (
            "Nov 12, 2025", "GOVERNMENT",
            "Government shutdown ends after 42 days",
            "Trump signed funding bill ending the Oct 1 shutdown. Deal included a continuing resolution "
            "and full-year appropriations for Veterans Affairs, Agriculture, military construction, and "
            "the Legislative Branch.",
            "positive",
        ),
        (
            "Oct 1, 2025", "GOVERNMENT",
            "Federal government shutdown begins",
            "Funding expired on Oct 1 after Congress failed to pass appropriations. Dispute centred on "
            "ACA subsidy extensions — Democrats demanded renewal, Republicans refused.",
            "danger",
        ),
        (
            "Sep 14, 2025", "POLITICS",
            "Charlie Kirk assassinated",
            "Turning Point USA co-founder Charlie Kirk was killed. Speaker Mike Johnson, Karoline Leavitt "
            "and Tulsi Gabbard attended memorials. TPUSA reported 121,000 new chapter requests in the "
            "two weeks following his death.",
            "danger",
        ),
        (
            "Aug 19, 2025", "POLICY",
            "USCIS expands social media vetting to include 'anti-Americanism'",
            "US Citizenship and Immigration Services announced it will review social media for "
            "'anti-American' and 'antisemitic' activity, treating findings as an 'overwhelmingly "
            "negative factor' in immigration benefit decisions.",
            "warning",
        ),
        (
            "Jun 4, 2025", "POLICY",
            "First Travel Ban — 19 countries suspended",
            "Trump issued a proclamation suspending entry of certain nationals from 19 countries, "
            "citing deficiencies in security screening. Expanded in December to 39 countries.",
            "warning",
        ),
        (
            "Jan 20, 2025", "POLITICS",
            "Trump inaugurated for second term",
            "Donald J. Trump was inaugurated as the 47th President of the United States — the first "
            "convicted felon elected to the presidency. JD Vance sworn in as Vice President. A wave of "
            "executive orders signed on day one targeting immigration, DEI, and federal workforce.",
            "accent",
        ),
        (
            "Nov 5, 2024", "POLITICS",
            "Trump wins 2024 presidential election",
            "Donald Trump defeated Vice President Kamala Harris in a decisive Electoral College victory. "
            "Republicans also recaptured the Senate. Trump became the first president in US history "
            "to win a non-consecutive second term since Grover Cleveland.",
            "accent",
        ),
        (
            "Jul 13, 2024", "POLITICS",
            "Trump assassination attempt — Butler, Pennsylvania",
            "A gunman opened fire at a Trump rally in Butler, PA. Trump was struck in the right ear "
            "and raised his fist to the crowd. One rallygoer was killed and two others critically "
            "wounded. The 20-year-old shooter was killed by Secret Service.",
            "danger",
        ),
        (
            "Jun 1, 2024", "LEGAL",
            "Trump convicted on 34 felony counts",
            "Donald Trump became the first former US president convicted of felony crimes. A New York "
            "jury found him guilty on all 34 counts of falsifying business records. Sentencing was "
            "later deferred after his election victory.",
            "danger",
        ),
        (
            "Jan 6, 2021", "POLITICS",
            "Capitol riot — certification of 2020 election disrupted",
            "Supporters of President Trump stormed the US Capitol building, disrupting the congressional "
            "certification of Joe Biden's election victory. Over 1,000 people were charged. Trump was "
            "impeached for a second time eight days later.",
            "danger",
        ),
        (
            "Mar 11, 2020", "CRISIS",
            "COVID-19 declared a global pandemic",
            "The WHO declared COVID-19 a pandemic. The US eventually recorded the world's highest death "
            "toll — over 1.1 million Americans died. Congress passed $5+ trillion in emergency relief. "
            "Operation Warp Speed delivered vaccines by late 2020.",
            "warning",
        ),
    ]

    CATEGORY_COLORS = {
        "WAR":        "danger",
        "GOVERNMENT": "blue_soft",
        "POLICY":     "warning",
        "POLITICS":   "accent",
        "LEGAL":      "rep_light",
        "CRISIS":     "danger",
    }

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self._build(engine)

    def _build(self, engine):
        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 0))

        ctk.CTkLabel(hdr, text="Platform Overview",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")

        # Live indicator
        live = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"], corner_radius=4,
                             border_width=1, border_color=PALETTE["border"])
        live.pack(side="right", pady=6)
        dot = ctk.CTkFrame(live, width=7, height=7, corner_radius=4,
                            fg_color=PALETTE["positive"])
        dot.pack(side="left", padx=(10, 4), pady=6)
        dot.pack_propagate(False)
        ctk.CTkLabel(live, text="LIVE  ",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["positive"]).pack(side="left")

        ctk.CTkLabel(self,
                     text="Executive intelligence dashboard — current status and recent historical events.",
                     font=("Courier New", 11),
                     text_color=PALETTE["text_secondary"], anchor="w"
                     ).pack(fill="x", padx=40, pady=(4, 20))

        # ── Stat cards ────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40, pady=(0, 24))

        self._stat_card(stats_frame, "DATABASE RECORDS", str(len(engine.all_data_content)), 0)
        self._stat_card(stats_frame, "ACTIVE LIBRARIES",  str(len(engine.csv_files)),        1)
        self._stat_card(stats_frame, "ACTIVE CONFLICTS",  "2",                               2)
        self._stat_card(stats_frame, "AI STATUS",         "CONNECTED",                       3)

        # ── Two-column layout: feed left, filter right ────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=(0, 32))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)

        # Feed column
        feed_frame = ctk.CTkFrame(body, fg_color="transparent")
        feed_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        feed_hdr = ctk.CTkFrame(feed_frame, fg_color="transparent")
        feed_hdr.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(feed_hdr, text="RECENT EVENTS & HISTORY",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(side="left")

        ctk.CTkLabel(feed_hdr,
                     text=f"{len(self.EVENTS)} events",
                     font=("Courier New", 9),
                     text_color=PALETTE["text_dim"]).pack(side="right")

        self._feed_scroll = ctk.CTkScrollableFrame(
            feed_frame, fg_color=PALETTE["surface"],
            corner_radius=10, border_width=1, border_color=PALETTE["border"],
            scrollbar_button_color=PALETTE["border"],
        )
        self._feed_scroll.pack(fill="both", expand=True)
        self._event_cards = []
        self._active_filter = "ALL"
        self._render_feed("ALL")

        # Filter column
        filter_frame = ctk.CTkFrame(body, fg_color="transparent")
        filter_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(filter_frame, text="FILTER BY CATEGORY",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(0, 10))

        categories = ["ALL", "WAR", "POLITICS", "POLICY", "GOVERNMENT", "LEGAL", "CRISIS"]
        self._filter_btns = {}
        for cat in categories:
            color = PALETTE.get(self.CATEGORY_COLORS.get(cat, "text_secondary"),
                                PALETTE["text_secondary"])
            btn = ctk.CTkButton(
                filter_frame,
                text=cat,
                height=34, corner_radius=6,
                fg_color=PALETTE["accent"] if cat == "ALL" else PALETTE["surface_2"],
                hover_color=PALETTE["accent_dim"],
                text_color=PALETTE["bg"] if cat == "ALL" else PALETTE["text_secondary"],
                font=("Courier New", 10, "bold"),
                command=lambda c=cat: self._filter(c)
            )
            btn.pack(fill="x", pady=(0, 6))
            self._filter_btns[cat] = btn

        # Ongoing alerts box
        ctk.CTkLabel(filter_frame, text="ACTIVE ALERTS",
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", pady=(16, 8))

        alerts = [
            ("● Iran War",         "Ongoing since Feb 28",  "danger"),
            ("● DHS Shutdown",     "Ongoing since Feb 14",  "warning"),
            ("● Travel Ban",       "39 countries, active",  "warning"),
        ]
        for label, sub, color_key in alerts:
            alert_card = ctk.CTkFrame(filter_frame, fg_color=PALETTE["surface"],
                                       corner_radius=6, border_width=1,
                                       border_color=PALETTE["border"])
            alert_card.pack(fill="x", pady=(0, 6))

            ctk.CTkLabel(alert_card, text=label,
                         font=("Courier New", 10, "bold"),
                         text_color=PALETTE.get(color_key, PALETTE["accent"]),
                         anchor="w").pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(alert_card, text=sub,
                         font=("Courier New", 9),
                         text_color=PALETTE["text_dim"], anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    def _stat_card(self, master, title, value, col):
        card = ctk.CTkFrame(master, fg_color=PALETTE["surface"],
                            border_color=PALETTE["border"], border_width=1,
                            corner_radius=8, height=100)
        card.grid(row=0, column=col, padx=(0, 14) if col < 3 else 0, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(card, text=title, font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_secondary"]).pack(pady=(16, 4))
        ctk.CTkLabel(card, text=value, font=("Georgia", 18, "bold"),
                     text_color=PALETTE["accent"]).pack(pady=(0, 16))

    def _filter(self, category):
        self._active_filter = category
        # Update button styles
        for cat, btn in self._filter_btns.items():
            if cat == category:
                btn.configure(fg_color=PALETTE["accent"],
                              text_color=PALETTE["bg"])
            else:
                btn.configure(fg_color=PALETTE["surface_2"],
                              text_color=PALETTE["text_secondary"])
        self._render_feed(category)

    def _render_feed(self, category):
        for w in self._feed_scroll.winfo_children():
            w.destroy()

        filtered = [e for e in self.EVENTS
                    if category == "ALL" or e[1] == category]

        if not filtered:
            ctk.CTkLabel(self._feed_scroll, text="No events in this category.",
                         font=("Courier New", 11),
                         text_color=PALETTE["text_dim"]).pack(pady=30)
            return

        for date, cat, headline, detail, color_key in filtered:
            self._make_event_card(date, cat, headline, detail, color_key)

    def _make_event_card(self, date, cat, headline, detail, color_key):
        color = PALETTE.get(color_key, PALETTE["accent"])
        cat_color = PALETTE.get(
            self.CATEGORY_COLORS.get(cat, "text_secondary"),
            PALETTE["text_secondary"]
        )

        card = ctk.CTkFrame(self._feed_scroll, fg_color="transparent",
                             corner_radius=0)
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)

        # Top row: date + category badge
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", pady=(0, 4))

        # Left colour bar accent
        ctk.CTkFrame(inner, width=3, height=0, fg_color=color,
                     corner_radius=2).pack(side="left", fill="y", padx=(0, 12))

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(side="left", fill="x", expand=True)

        meta_row = ctk.CTkFrame(content, fg_color="transparent")
        meta_row.pack(fill="x", pady=(0, 3))

        ctk.CTkLabel(meta_row, text=date,
                     font=("Courier New", 9, "bold"),
                     text_color=PALETTE["text_dim"], anchor="w").pack(side="left")

        badge = ctk.CTkFrame(meta_row, fg_color=PALETTE["surface_2"],
                              corner_radius=3)
        badge.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(badge, text=cat,
                     font=("Courier New", 8, "bold"),
                     text_color=cat_color).pack(padx=6, pady=2)

        ctk.CTkLabel(content, text=headline,
                     font=("Georgia", 12, "bold"),
                     text_color=PALETTE["text_primary"],
                     anchor="w", wraplength=520, justify="left"
                     ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(content, text=detail,
                     font=("Courier New", 10),
                     text_color=PALETTE["text_secondary"],
                     anchor="w", wraplength=520, justify="left"
                     ).pack(fill="x")

        # Divider
        ctk.CTkFrame(self._feed_scroll, height=1,
                     fg_color=PALETTE["border"], corner_radius=0).pack(fill="x", padx=12)


class LegalQAPanel(ctk.CTkFrame):
    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(header, text="Legal Intelligence", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(side="left")

        self.chat_box = ctk.CTkTextbox(
            self, fg_color=PALETTE["surface"], border_color=PALETTE["border"],
            border_width=1, text_color=PALETTE["text_primary"],
            font=("Courier New", 13), padx=20, pady=20
        )
        self.chat_box.pack(fill="both", expand=True, padx=40, pady=10)
        self.chat_box.configure(state="disabled")

        input_container = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                        border_color=PALETTE["border"], border_width=1)
        input_container.pack(fill="x", padx=40, pady=(10, 40))

        self.input_field = ctk.CTkEntry(
            input_container, placeholder_text="Query the executive record...",
            fg_color="transparent", border_width=0,
            text_color=PALETTE["text_primary"], font=("Georgia", 14)
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=20)
        self.input_field.bind("<Return>", lambda e: self.handle_submission())

        self.submit_btn = ctk.CTkButton(
            input_container, text="SUBMIT INQUIRY",
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_dim"],
            text_color=PALETTE["bg"], font=("Courier New", 12, "bold"),
            width=140, command=self.handle_submission
        )
        self.submit_btn.pack(side="right", padx=10, pady=10)

    def handle_submission(self):
        query = self.input_field.get().strip()
        if not query:
            return
        self.input_field.delete(0, "end")
        self._append_to_chat(f"YOU: {query}\n")
        self.submit_btn.configure(state="disabled", text="ANALYZING...")
        threading.Thread(target=self.run_ai, args=(query,), daemon=True).start()

    def run_ai(self, query):
        try:
            response = self.engine.query_ai(query)
            self.after(0, self._append_to_chat, f"EXECUTIVE INSIGHT: {response}\n\n")
        except Exception as e:
            self.after(0, self._append_to_chat, f"SYSTEM ERROR: {str(e)}\n\n")
        finally:
            self.after(0, lambda: self.submit_btn.configure(state="normal", text="SUBMIT INQUIRY"))

    def _append_to_chat(self, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")


class BillsPanel(ctk.CTkFrame):
    # Map display name → CSV filename (relative to this file)
    SOURCES = {
        "Trump 2nd Term":  "trump2.csv",
        "Trump 1st Term":  "trump_eos.csv",
        "Biden":           "biden.csv",
        "Obama":           "obama.csv",
        "W. Bush":         "w_bush.csv",
        "Clinton":         "clinton.csv",
        "H.W. Bush":       "h_w_bush.csv",
        "Reagan":          "reagan.csv",
        "Carter":          "carter.csv",
        "Ford":            "ford.csv",
        "Nixon":           "nixon.csv",
        "Johnson":         "johnson.csv",
        "Kennedy":         "kennedy.csv",
        "Eisenhower":      "eisenhower.csv",
        "Truman":          "truman.csv",
        "Roosevelt":       "roosevelt.csv",
        "Historical":      "past.csv",
    }

    # Party colour mapping
    PARTY_COLORS = {
        "Trump 2nd Term":  "#D94A4A",
        "Trump 1st Term":  "#D94A4A",
        "Biden":           "#4A90D9",
        "Obama":           "#4A90D9",
        "W. Bush":         "#D94A4A",
        "Clinton":         "#4A90D9",
        "H.W. Bush":       "#D94A4A",
        "Reagan":          "#D94A4A",
        "Carter":          "#4A90D9",
        "Ford":            "#D94A4A",
        "Nixon":           "#D94A4A",
        "Johnson":         "#4A90D9",
        "Kennedy":         "#4A90D9",
        "Eisenhower":      "#D94A4A",
        "Truman":          "#4A90D9",
        "Roosevelt":       "#4A90D9",
        "Historical":      "#7A8099",
    }

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine      = engine
        self._all_rows   = []   # full loaded dataset for current president
        self._filtered   = []   # rows after search/type filter
        self._current_president = list(self.SOURCES.keys())[0]
        self._base_dir   = os.path.dirname(os.path.abspath(__file__))
        self._build()

    def _build(self):
        import csv as _csv
        self._csv = _csv

        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(32, 0))

        ctk.CTkLabel(hdr, text="Executive Orders Database",
                     font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"], anchor="w").pack(side="left")

        self._count_badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"],
                                          corner_radius=4, border_width=1,
                                          border_color=PALETTE["border"])
        self._count_badge.pack(side="right", pady=6)
        self._count_lbl = ctk.CTkLabel(self._count_badge, text="",
                                        font=("Courier New", 9, "bold"),
                                        text_color=PALETTE["text_dim"])
        self._count_lbl.pack(padx=10, pady=4)

        ctk.CTkLabel(self, text="Browse, search, and filter every presidential executive order on record.",
                     font=("Courier New", 11), text_color=PALETTE["text_secondary"],
                     anchor="w").pack(fill="x", padx=40, pady=(4, 16))

        # ── President selector tabs (scrollable row) ──────────────────────
        tab_outer = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                  corner_radius=8, border_width=1,
                                  border_color=PALETTE["border"])
        tab_outer.pack(fill="x", padx=40, pady=(0, 14))

        tab_canvas = tk.Canvas(tab_outer, height=46, bg=PALETTE["surface"],
                                highlightthickness=0)
        tab_canvas.pack(side="left", fill="x", expand=True)

        tab_scroll = tk.Scrollbar(tab_outer, orient="horizontal",
                                   command=tab_canvas.xview)
        tab_scroll.pack(side="bottom", fill="x")
        tab_canvas.configure(xscrollcommand=tab_scroll.set)

        self._tab_inner = tk.Frame(tab_canvas, bg=PALETTE["surface"])
        self._tab_win   = tab_canvas.create_window((0, 0), window=self._tab_inner,
                                                    anchor="nw")

        def _on_tab_configure(e):
            tab_canvas.configure(scrollregion=tab_canvas.bbox("all"))
        self._tab_inner.bind("<Configure>", _on_tab_configure)

        self._tab_btns = {}
        for name in self.SOURCES:
            color = self.PARTY_COLORS.get(name, PALETTE["text_secondary"])
            btn = tk.Button(
                self._tab_inner, text=name,
                bg=PALETTE["surface"], fg=PALETTE["text_secondary"],
                activebackground=PALETTE["surface_2"], activeforeground=color,
                relief="flat", cursor="hand2", padx=10, pady=8,
                font=("Courier New", 10),
                command=lambda n=name: self._select_president(n)
            )
            btn.pack(side="left", padx=2, pady=4)
            self._tab_btns[name] = btn

        # ── Search & filter bar ───────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                            corner_radius=8, border_width=1,
                            border_color=PALETTE["border"])
        bar.pack(fill="x", padx=40, pady=(0, 12))

        self._search_entry = ctk.CTkEntry(
            bar, placeholder_text="Search titles, EO numbers, disposition notes...",
            placeholder_text_color=PALETTE["text_dim"],
            fg_color="transparent", border_width=0,
            text_color=PALETTE["text_primary"], font=("Georgia", 13)
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=16, pady=10)
        self._search_entry.bind("<Return>", lambda e: self._apply_filter())
        self._search_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        # Type filter
        self._type_var = ctk.StringVar(value="All Types")
        self._type_menu = ctk.CTkOptionMenu(
            bar, variable=self._type_var,
            values=["All Types", "Executive Order", "Proclamation",
                    "Memorandum", "Notice", "Other"],
            width=160, height=32, corner_radius=6,
            fg_color=PALETTE["surface_2"],
            button_color=PALETTE["border"],
            button_hover_color=PALETTE["accent_dim"],
            dropdown_fg_color=PALETTE["surface_2"],
            dropdown_text_color=PALETTE["text_primary"],
            dropdown_hover_color=PALETTE["border"],
            text_color=PALETTE["text_primary"],
            font=("Courier New", 11),
            command=lambda _: self._apply_filter()
        )
        self._type_menu.pack(side="right", padx=(6, 12), pady=8)

        ctk.CTkButton(
            bar, text="Clear",
            width=60, height=32, corner_radius=6,
            fg_color=PALETTE["surface_2"], hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._clear_search
        ).pack(side="right", padx=(0, 6), pady=8)

        # ── Column headers ────────────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self, fg_color="transparent")
        col_hdr.pack(fill="x", padx=40, pady=(0, 4))
        col_hdr.columnconfigure(0, weight=0, minsize=70)
        col_hdr.columnconfigure(1, weight=3)
        col_hdr.columnconfigure(2, weight=1, minsize=110)
        col_hdr.columnconfigure(3, weight=1, minsize=110)

        for i, label in enumerate(("EO #", "TITLE", "TYPE", "SIGNED")):
            ctk.CTkLabel(col_hdr, text=label,
                         font=("Courier New", 9, "bold"),
                         text_color=PALETTE["text_dim"], anchor="w"
                         ).grid(row=0, column=i, sticky="w", padx=6)

        # ── Results list ──────────────────────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=PALETTE["surface"],
            corner_radius=8, border_width=1, border_color=PALETTE["border"],
            scrollbar_button_color=PALETTE["border"],
        )
        self._list_frame.pack(fill="both", expand=True, padx=40, pady=(0, 8))

        # ── Detail panel (hidden until a row is clicked) ──────────────────
        self._detail_panel = ctk.CTkFrame(
            self, fg_color=PALETTE["surface_2"],
            corner_radius=8, border_width=1, border_color=PALETTE["accent"]
        )
        # packed on demand

        self._detail_title = ctk.CTkLabel(
            self._detail_panel, text="",
            font=("Georgia", 13, "bold"),
            text_color=PALETTE["text_primary"],
            wraplength=900, justify="left", anchor="w"
        )
        self._detail_title.pack(fill="x", padx=20, pady=(16, 4))

        detail_meta = ctk.CTkFrame(self._detail_panel, fg_color="transparent")
        detail_meta.pack(fill="x", padx=20, pady=(0, 4))
        self._detail_meta = ctk.CTkLabel(detail_meta, text="",
                                          font=("Courier New", 10),
                                          text_color=PALETTE["text_secondary"], anchor="w")
        self._detail_meta.pack(side="left")

        self._detail_notes = ctk.CTkLabel(
            self._detail_panel, text="",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"],
            wraplength=900, justify="left", anchor="w"
        )
        self._detail_notes.pack(fill="x", padx=20, pady=(0, 16))

        close_btn = ctk.CTkButton(
            self._detail_panel, text="✕ Close", width=70, height=24,
            corner_radius=4,
            fg_color=PALETTE["border"], hover_color=PALETTE["surface"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._hide_detail
        )
        close_btn.place(relx=1.0, y=8, anchor="ne", x=-12)

        # Load default president
        self._select_president(self._current_president)

    # ── Data loading ──────────────────────────────────────────────────────────
    def _load_csv(self, name):
        import csv
        filename = self.SOURCES[name]
        # look beside this file first, then uploads folder
        for folder in (self._base_dir,
                       "/mnt/user-data/uploads",
                       "/mnt/user-data/outputs"):
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    return list(csv.DictReader(f))
        return []

    # ── Tab selection ─────────────────────────────────────────────────────────
    def _select_president(self, name):
        self._current_president = name
        self._hide_detail()

        # Update tab highlight
        active_color = self.PARTY_COLORS.get(name, PALETTE["accent"])
        for n, btn in self._tab_btns.items():
            if n == name:
                btn.configure(bg=PALETTE["surface_2"], fg=active_color,
                              font=("Courier New", 10, "bold"))
            else:
                btn.configure(bg=PALETTE["surface"], fg=PALETTE["text_secondary"],
                              font=("Courier New", 10))

        self._all_rows = self._load_csv(name)
        self._search_entry.delete(0, "end")
        self._type_var.set("All Types")
        self._apply_filter()

    # ── Filter / search ───────────────────────────────────────────────────────
    def _apply_filter(self):
        q      = self._search_entry.get().strip().lower()
        t_filt = self._type_var.get()

        results = []
        for row in self._all_rows:
            subtype = row.get("subtype", "").strip()
            title   = row.get("title", "")
            eo_num  = str(row.get("executive_order_number", ""))
            notes   = row.get("disposition_notes", "")

            # Type filter
            if t_filt != "All Types":
                if t_filt == "Executive Order" and "Executive Order" not in subtype:
                    continue
                elif t_filt == "Proclamation" and "Proclamation" not in subtype:
                    continue
                elif t_filt == "Memorandum" and "Memorandum" not in subtype:
                    continue
                elif t_filt == "Notice" and "Notice" not in subtype:
                    continue
                elif t_filt == "Other" and subtype in ("Executive Order", "Proclamation",
                                                        "Memorandum", "Notice"):
                    continue

            # Text search
            if q and q not in title.lower() and q not in eo_num and q not in notes.lower():
                continue

            results.append(row)

        self._filtered = results
        self._render_rows()

    def _clear_search(self):
        self._search_entry.delete(0, "end")
        self._type_var.set("All Types")
        self._apply_filter()

    # ── Render rows into the list frame ──────────────────────────────────────
    def _render_rows(self):
        # Clear existing rows
        for w in self._list_frame.winfo_children():
            w.destroy()

        color = self.PARTY_COLORS.get(self._current_president, PALETTE["accent"])
        total = len(self._all_rows)
        shown = len(self._filtered)
        self._count_lbl.configure(
            text=f"  {shown:,} of {total:,} RECORDS — {self._current_president}  "
        )

        if not self._filtered:
            ctk.CTkLabel(self._list_frame, text="No records match your search.",
                         font=("Courier New", 12),
                         text_color=PALETTE["text_dim"]).pack(pady=40)
            return

        for row in self._filtered:
            self._make_row(row, color)

    def _make_row(self, row, color):
        eo_num  = str(row.get("executive_order_number", "")).strip() or "—"
        title   = row.get("title", "Untitled").strip()
        subtype = row.get("subtype", "").strip() or "Document"
        signed  = row.get("signing_date", "").strip() or row.get("publication_date", "").strip()

        frame = ctk.CTkFrame(self._list_frame, fg_color="transparent",
                              cursor="hand2")
        frame.pack(fill="x", pady=1)
        frame.columnconfigure(0, weight=0, minsize=70)
        frame.columnconfigure(1, weight=3)
        frame.columnconfigure(2, weight=1, minsize=110)
        frame.columnconfigure(3, weight=1, minsize=110)

        ctk.CTkLabel(frame, text=eo_num,
                     font=("Courier New", 11, "bold"),
                     text_color=color, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=(10, 4), pady=6)

        ctk.CTkLabel(frame, text=title,
                     font=("Georgia", 12),
                     text_color=PALETTE["text_primary"], anchor="w"
                     ).grid(row=0, column=1, sticky="ew", padx=4, pady=6)

        ctk.CTkLabel(frame, text=subtype,
                     font=("Courier New", 10),
                     text_color=PALETTE["text_secondary"], anchor="w"
                     ).grid(row=0, column=2, sticky="w", padx=4, pady=6)

        ctk.CTkLabel(frame, text=signed,
                     font=("Courier New", 10),
                     text_color=PALETTE["text_dim"], anchor="w"
                     ).grid(row=0, column=3, sticky="w", padx=(4, 10), pady=6)

        # Divider
        ctk.CTkFrame(self._list_frame, height=1,
                     fg_color=PALETTE["border"], corner_radius=0).pack(fill="x", padx=8)

        # Click to expand detail
        def _click(e, r=row):
            self._show_detail(r)

        for w in frame.winfo_children():
            w.bind("<Button-1>", _click)
        frame.bind("<Button-1>", _click)

        # Hover effect
        def _enter(e, f=frame):
            f.configure(fg_color=PALETTE["surface_2"])
        def _leave(e, f=frame):
            f.configure(fg_color="transparent")
        frame.bind("<Enter>", _enter)
        frame.bind("<Leave>", _leave)

    # ── Detail panel ──────────────────────────────────────────────────────────
    def _show_detail(self, row):
        title   = row.get("title", "").strip()
        eo_num  = str(row.get("executive_order_number", "")).strip()
        subtype = row.get("subtype", "").strip()
        signed  = row.get("signing_date", "").strip()
        pub     = row.get("publication_date", "").strip()
        notes   = row.get("disposition_notes", "").strip()
        html    = row.get("html_url", "").strip()

        self._detail_title.configure(text=title or "Untitled")
        meta = f"EO #{eo_num}  •  {subtype}  •  Signed: {signed}  •  Published: {pub}"
        if html:
            meta += f"  •  {html}"
        self._detail_meta.configure(text=meta)
        self._detail_notes.configure(
            text=f"Disposition: {notes}" if notes else "No disposition notes recorded."
        )
        self._detail_panel.pack(fill="x", padx=40, pady=(0, 16))

    def _hide_detail(self):
        self._detail_panel.pack_forget()


# ══════════════════════════════════════════════════════════════════════════════
#  PARTY IMPACT PANEL
# ══════════════════════════════════════════════════════════════════════════════

class PartyCard(ctk.CTkFrame):
    """Expandable card showing goals and impact for a single political party."""

    def __init__(self, master, party_name, data, **kwargs):
        super().__init__(
            master,
            fg_color=PALETTE["surface"],
            border_color=data["dim_color"],
            border_width=1,
            corner_radius=10,
            **kwargs
        )
        self.data       = data
        self.party_name = party_name
        self._expanded  = False
        self._build_header()
        self._build_body()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", padx=20, pady=16)

        # Coloured left stripe
        stripe = ctk.CTkFrame(self, width=4, fg_color=self.data["color"], corner_radius=0)
        stripe.place(x=0, y=0, relheight=1)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row, text=self.party_name,
            font=("Georgia", 17, "bold"),
            text_color=self.data["color"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            top_row, text=f"  {self.data['symbol']}",
            font=("Georgia", 18),
            text_color=self.data["color"]
        ).pack(side="left")

        ctk.CTkLabel(
            left, text=self.data["tagline"],
            font=("Courier New", 10),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x")

        self.toggle_btn = ctk.CTkButton(
            hdr, text="▼  Expand", width=110, height=28,
            corner_radius=6,
            fg_color=PALETTE["surface_2"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._toggle
        )
        self.toggle_btn.pack(side="right")

        for w in (hdr, left, top_row):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        # hidden until expanded

        # Description
        ctk.CTkLabel(
            self.body,
            text=self.data["description"],
            font=("Georgia", 12),
            text_color=PALETTE["text_secondary"],
            wraplength=820, justify="left", anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 16))

        # Two-column: Goals | Impact
        cols = ctk.CTkFrame(self.body, fg_color="transparent")
        cols.pack(fill="x", padx=24, pady=(0, 20))
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        self._build_column(
            cols, 0, "CORE GOALS", self.data["core_goals"]
        )
        self._build_column(
            cols, 1, "RECENT LEGISLATIVE IMPACT", self.data["recent_impacts"]
        )

    def _build_column(self, parent, col, heading, items):
        frame = ctk.CTkFrame(
            parent, fg_color=PALETTE["surface_2"],
            corner_radius=8, border_width=1, border_color=PALETTE["border"]
        )
        frame.grid(
            row=0, column=col, sticky="nsew",
            padx=(0, 10) if col == 0 else (10, 0)
        )

        ctk.CTkLabel(
            frame, text=heading,
            font=("Courier New", 9, "bold"),
            text_color=self.data["color"]
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for label, detail in items:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            dot = ctk.CTkFrame(row, width=6, height=6, corner_radius=3,
                               fg_color=self.data["color"])
            dot.pack(side="left", padx=(0, 10))
            dot.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                inner, text=label,
                font=("Georgia", 12, "bold"),
                text_color=PALETTE["text_primary"], anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                inner, text=detail,
                font=("Courier New", 10),
                text_color=PALETTE["text_secondary"],
                wraplength=330, justify="left", anchor="w"
            ).pack(fill="x")

        ctk.CTkFrame(frame, height=12, fg_color="transparent").pack()

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(0, 12))
            self.toggle_btn.configure(text="▲  Collapse")
        else:
            self.body.pack_forget()
            self.toggle_btn.configure(text="▼  Expand")


class PartyImpactPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 4))

        ctk.CTkLabel(
            hdr, text="Party Impact & Goals",
            font=("Georgia", 24, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"],
                              corner_radius=4, border_width=1,
                              border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(
            badge, text="NON-PARTISAN  •  INFORMATIONAL",
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"]
        ).pack(padx=10, pady=4)

        ctk.CTkLabel(
            self,
            text="An objective overview of U.S. political parties — their goals, values, and recent legislative impact.",
            font=("Courier New", 11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=40, pady=(0, 16))

        # Disclaimer banner
        disc = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"],
                             corner_radius=8, border_width=1,
                             border_color=PALETTE["border"])
        disc.pack(fill="x", padx=40, pady=(0, 20))
        ctk.CTkLabel(
            disc,
            text=(
                "⚠   This panel presents factual policy positions and legislative records. "
                "It does not endorse any party or candidate."
            ),
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=16, pady=10)

        # Scrollable party cards
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=PALETTE["border"],
            scrollbar_fg_color=PALETTE["surface"],
        )
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        for party_name, data in PARTY_DATA.items():
            PartyCard(scroll, party_name, data).pack(fill="x", pady=(0, 16))


# ══════════════════════════════════════════════════════════════════════════════
#  US WARS PANEL
# ══════════════════════════════════════════════════════════════════════════════

class WarCard(ctk.CTkFrame):
    """Expandable card for a single US war."""

    STATUS_COLORS = {
        "ongoing":    "#D94A4A",   # red — active conflict
        "historical": "#3D4357",   # dim grey
    }

    def __init__(self, master, war, **kwargs):
        self._status_color = self.STATUS_COLORS.get(war["status"], PALETTE["border"])
        super().__init__(
            master,
            fg_color=PALETTE["surface"],
            border_color=self._status_color,
            border_width=1,
            corner_radius=10,
            **kwargs
        )
        self.war       = war
        self._expanded = False
        self._build_header()
        self._build_body()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", padx=20, pady=14)

        # Left colour stripe
        stripe = ctk.CTkFrame(self, width=4, fg_color=self._status_color, corner_radius=0)
        stripe.place(x=0, y=0, relheight=1)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        # Title row
        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text=self.war["name"],
            font=("Georgia", 15, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        # Status badge
        status_text = "● ONGOING" if self.war["status"] == "ongoing" else "HISTORICAL"
        badge = ctk.CTkFrame(title_row, fg_color=PALETTE["surface_2"],
                              corner_radius=4, border_width=1,
                              border_color=self._status_color)
        badge.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(
            badge, text=status_text,
            font=("Courier New", 9, "bold"),
            text_color=self._status_color
        ).pack(padx=8, pady=3)

        # Subtitle row: years + deaths
        sub_row = ctk.CTkFrame(left, fg_color="transparent")
        sub_row.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            sub_row, text=self.war["years"],
            font=("Courier New", 10),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            sub_row, text="  |  ",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"]
        ).pack(side="left")

        ctk.CTkLabel(
            sub_row, text=f"US Deaths: {self.war['us_deaths']}",
            font=("Courier New", 10, "bold"),
            text_color=PALETTE["accent"], anchor="w"
        ).pack(side="left")

        self.toggle_btn = ctk.CTkButton(
            hdr, text="▼  Details", width=100, height=28,
            corner_radius=6,
            fg_color=PALETTE["surface_2"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._toggle
        )
        self.toggle_btn.pack(side="right")

        for w in (hdr, left, title_row, sub_row):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        # hidden until expanded

        # Summary paragraph
        ctk.CTkLabel(
            self.body,
            text=self.war["summary"],
            font=("Georgia", 12),
            text_color=PALETTE["text_secondary"],
            wraplength=860, justify="left", anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 16))

        # Impact rows
        impacts_frame = ctk.CTkFrame(
            self.body, fg_color=PALETTE["surface_2"],
            corner_radius=8, border_width=1, border_color=PALETTE["border"]
        )
        impacts_frame.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(
            impacts_frame, text="KEY IMPACTS",
            font=("Courier New", 9, "bold"),
            text_color=self._status_color
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for label, detail in self.war["impacts"]:
            row = ctk.CTkFrame(impacts_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)

            dot = ctk.CTkFrame(row, width=6, height=6, corner_radius=3,
                               fg_color=self._status_color)
            dot.pack(side="left", padx=(0, 12))
            dot.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                inner, text=label,
                font=("Georgia", 12, "bold"),
                text_color=PALETTE["text_primary"], anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                inner, text=detail,
                font=("Courier New", 10),
                text_color=PALETTE["text_secondary"],
                wraplength=820, justify="left", anchor="w"
            ).pack(fill="x")

        ctk.CTkFrame(impacts_frame, height=12, fg_color="transparent").pack()

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(0, 12))
            self.toggle_btn.configure(text="▲  Close")
        else:
            self.body.pack_forget()
            self.toggle_btn.configure(text="▼  Details")


class USWarsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 4))

        ctk.CTkLabel(
            hdr, text="U.S. Wars & Military Conflicts",
            font=("Georgia", 24, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        # Ongoing count badge
        ongoing = sum(1 for w in WARS_DATA if w["status"] == "ongoing")
        badge = ctk.CTkFrame(hdr, fg_color="#8A1A1A", corner_radius=4)
        badge.pack(side="right", pady=6)
        ctk.CTkLabel(
            badge, text=f"  {ongoing} ACTIVE CONFLICT{'S' if ongoing != 1 else ''}  ",
            font=("Courier New", 9, "bold"),
            text_color="#D94A4A"
        ).pack(pady=4)

        ctk.CTkLabel(
            self,
            text="Historical and ongoing US military engagements — causes, US deaths, and lasting impacts.",
            font=("Courier New", 11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=40, pady=(0, 16))

        # Death toll summary bar
        summary = ctk.CTkFrame(self, fg_color=PALETTE["surface_2"],
                                corner_radius=8, border_width=1,
                                border_color=PALETTE["border"])
        summary.pack(fill="x", padx=40, pady=(0, 20))

        inner = ctk.CTkFrame(summary, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="⚠  Figures are historically documented totals. Iran War deaths reflect confirmed US KIA as of March 8, 2026 — the conflict is ongoing and figures will change.",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"],
            wraplength=900, justify="left", anchor="w"
        ).pack(fill="x")

        # Filter row
        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.pack(fill="x", padx=40, pady=(0, 12))

        ctk.CTkLabel(
            filter_row, text="FILTER:",
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"]
        ).pack(side="left", padx=(0, 10))

        self._filter_var = ctk.StringVar(value="All")
        for label in ("All", "Ongoing", "Historical"):
            ctk.CTkButton(
                filter_row,
                text=label,
                width=90, height=26,
                corner_radius=6,
                fg_color=PALETTE["surface_2"],
                hover_color=PALETTE["border"],
                text_color=PALETTE["text_secondary"],
                font=("Courier New", 10, "bold"),
                command=lambda l=label: self._apply_filter(l)
            ).pack(side="left", padx=(0, 6))

        # Scrollable war cards
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=PALETTE["border"],
            scrollbar_fg_color=PALETTE["surface"],
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        self._cards = []
        for war in WARS_DATA:
            card = WarCard(self.scroll, war)
            card.pack(fill="x", pady=(0, 12))
            self._cards.append((war["status"], card))

    def _apply_filter(self, label):
        for status, card in self._cards:
            if label == "All":
                card.pack(fill="x", pady=(0, 12))
            elif label == "Ongoing" and status == "ongoing":
                card.pack(fill="x", pady=(0, 12))
            elif label == "Historical" and status == "historical":
                card.pack(fill="x", pady=(0, 12))
            else:
                card.pack_forget()


# ══════════════════════════════════════════════════════════════════════════════
#  GOVERNMENT HISTORY DATA
# ══════════════════════════════════════════════════════════════════════════════

GOV_ERAS = [
    {
        "era":     "Founding & Federalist Era",
        "years":   "1789 – 1801",
        "color":   "#C9A84C",
        "summary": (
            "The United States government was established under the new Constitution. "
            "The first two presidents were unaffiliated with formal parties, though "
            "deep ideological splits between Federalists and Democratic-Republicans "
            "rapidly formed around figures like Hamilton and Jefferson."
        ),
        "presidents": [
            {
                "number": 1, "name": "George Washington", "party": "Unaffiliated",
                "years": "1789–1797", "vp": "John Adams",
                "key_facts": [
                    "First president; set two-term precedent voluntarily.",
                    "Signed the Judiciary Act (1789), creating the federal court system.",
                    "Suppressed the Whiskey Rebellion (1794), asserting federal authority.",
                    "Issued Proclamation of Neutrality (1793) keeping US out of European wars.",
                    "Warned against political parties and foreign alliances in Farewell Address.",
                ],
            },
            {
                "number": 2, "name": "John Adams", "party": "Federalist",
                "years": "1797–1801", "vp": "Thomas Jefferson",
                "key_facts": [
                    "Avoided full-scale war with France during the Quasi-War (1798–1800).",
                    "Signed the controversial Alien and Sedition Acts (1798).",
                    "First president to live in the White House (moved in 1800).",
                    "Lost re-election to Thomas Jefferson in the first peaceful transfer of power.",
                ],
            },
        ],
    },
    {
        "era":     "Democratic-Republican Dominance",
        "years":   "1801 – 1825",
        "color":   "#4A90D9",
        "summary": (
            "The Federalist Party collapsed and the Democratic-Republicans dominated "
            "unchallenged. This 'Era of Good Feelings' saw westward expansion, the "
            "Louisiana Purchase, the War of 1812, and the beginnings of American "
            "industrial and territorial growth."
        ),
        "presidents": [
            {
                "number": 3, "name": "Thomas Jefferson", "party": "Democratic-Republican",
                "years": "1801–1809", "vp": "Aaron Burr / George Clinton",
                "key_facts": [
                    "Louisiana Purchase (1803) doubled the size of the US for ~$15 million.",
                    "Commissioned the Lewis & Clark Expedition (1804–1806).",
                    "Signed the Act Prohibiting Importation of Slaves (1807).",
                    "Imposed the Embargo Act (1807) to avoid European wars — economically disastrous.",
                ],
            },
            {
                "number": 4, "name": "James Madison", "party": "Democratic-Republican",
                "years": "1809–1817", "vp": "George Clinton / Elbridge Gerry",
                "key_facts": [
                    "Led the US through the War of 1812 against Britain.",
                    "The White House and Capitol were burned by British forces in 1814.",
                    "Treaty of Ghent (1814) ended the War of 1812 with status quo ante bellum.",
                    "Known as 'Father of the Constitution' for his role at the Constitutional Convention.",
                ],
            },
            {
                "number": 5, "name": "James Monroe", "party": "Democratic-Republican",
                "years": "1817–1825", "vp": "Daniel D. Tompkins",
                "key_facts": [
                    "Issued the Monroe Doctrine (1823) — warning Europe against re-colonising the Americas.",
                    "Missouri Compromise (1820) temporarily resolved slavery expansion tensions.",
                    "Acquired Florida from Spain via the Adams-Onís Treaty (1819).",
                    "Re-elected with virtually no opposition in 1820 — height of the 'Era of Good Feelings'.",
                ],
            },
        ],
    },
    {
        "era":     "Jacksonian Democracy & Expansion",
        "years":   "1825 – 1849",
        "color":   "#D94A4A",
        "summary": (
            "A new populist politics emerged under Andrew Jackson, expanding voting rights "
            "to white men without property. This era saw the forced removal of Native "
            "Americans, the rise of the Whig Party, and major territorial expansion "
            "through the Mexican-American War."
        ),
        "presidents": [
            {
                "number": 6, "name": "John Quincy Adams", "party": "Democratic-Republican / National Republican",
                "years": "1825–1829", "vp": "John C. Calhoun",
                "key_facts": [
                    "Won presidency in the 'Corrupt Bargain' — no candidate won an Electoral majority.",
                    "Advocated for national infrastructure, education, and science funding.",
                    "Heavily opposed by Jacksonians; later served in Congress as a strong anti-slavery voice.",
                ],
            },
            {
                "number": 7, "name": "Andrew Jackson", "party": "Democrat",
                "years": "1829–1837", "vp": "John C. Calhoun / Martin Van Buren",
                "key_facts": [
                    "Indian Removal Act (1830) — forced relocation of 60,000+ Native Americans; Trail of Tears.",
                    "Vetoed renewal of the Second Bank of the United States, destroying it.",
                    "Survived the first assassination attempt on a US president (1835).",
                    "Nullification Crisis — threatened military force to prevent South Carolina secession.",
                ],
            },
            {
                "number": 8, "name": "Martin Van Buren", "party": "Democrat",
                "years": "1837–1841", "vp": "Richard Mentor Johnson",
                "key_facts": [
                    "Faced the Panic of 1837, one of the worst economic depressions to that point.",
                    "Established the Independent Treasury System.",
                    "Continued forced Native American removal policies.",
                ],
            },
            {
                "number": 9, "name": "William Henry Harrison", "party": "Whig",
                "years": "1841", "vp": "John Tyler",
                "key_facts": [
                    "Shortest presidency in US history — died of pneumonia 31 days after inauguration.",
                    "Delivered the longest inaugural address in history (1 hour 45 minutes) in cold rain.",
                ],
            },
            {
                "number": 10, "name": "John Tyler", "party": "Whig (expelled)",
                "years": "1841–1845", "vp": "None",
                "key_facts": [
                    "First VP to assume presidency due to death of predecessor.",
                    "Expelled from the Whig Party; served as president with no party affiliation.",
                    "Annexed Texas in his final days in office (1845).",
                ],
            },
            {
                "number": 11, "name": "James K. Polk", "party": "Democrat",
                "years": "1845–1849", "vp": "George M. Dallas",
                "key_facts": [
                    "Oversaw the greatest territorial expansion in US history — Oregon, California, the Southwest.",
                    "Mexican-American War (1846–1848) added 525,000 sq miles to the US.",
                    "Served one term by choice; fulfilled every major campaign promise.",
                ],
            },
        ],
    },
    {
        "era":     "Slavery Crisis & Civil War",
        "years":   "1849 – 1869",
        "color":   "#8A6E2F",
        "summary": (
            "The nation fractured over slavery. The new Republican Party rose on an "
            "anti-slavery platform. Abraham Lincoln's election triggered Southern secession "
            "and the bloodiest conflict in American history. The Union was preserved and "
            "slavery abolished, but Reconstruction began amid deep national wounds."
        ),
        "presidents": [
            {
                "number": 12, "name": "Zachary Taylor", "party": "Whig",
                "years": "1849–1850", "vp": "Millard Fillmore",
                "key_facts": [
                    "Died in office July 1850, possibly from gastroenteritis.",
                    "War hero of Mexican-American War; resisted extreme pro-slavery demands.",
                ],
            },
            {
                "number": 13, "name": "Millard Fillmore", "party": "Whig",
                "years": "1850–1853", "vp": "None",
                "key_facts": [
                    "Signed the Compromise of 1850, temporarily defusing the slavery crisis.",
                    "Signed the Fugitive Slave Act, deeply angering Northern abolitionists.",
                    "Last Whig president; party collapsed shortly after.",
                ],
            },
            {
                "number": 14, "name": "Franklin Pierce", "party": "Democrat",
                "years": "1853–1857", "vp": "William Rufus DeVane King",
                "key_facts": [
                    "Kansas-Nebraska Act (1854) reopened slavery debate; triggered 'Bleeding Kansas' violence.",
                    "His pro-Southern stance alienated the North and accelerated sectional crisis.",
                ],
            },
            {
                "number": 15, "name": "James Buchanan", "party": "Democrat",
                "years": "1857–1861", "vp": "John C. Breckinridge",
                "key_facts": [
                    "Widely considered one of the worst presidents for failing to prevent secession.",
                    "Dred Scott decision (1857) — Supreme Court ruled enslaved people had no rights.",
                    "Seven states seceded before he left office; he took no action to stop them.",
                ],
            },
            {
                "number": 16, "name": "Abraham Lincoln", "party": "Republican",
                "years": "1861–1865", "vp": "Hannibal Hamlin / Andrew Johnson",
                "key_facts": [
                    "Led the Union through the Civil War (1861–1865); ~620,000 soldiers died.",
                    "Emancipation Proclamation (1863) freed enslaved people in Confederate states.",
                    "Gettysburg Address (1863) redefined the war as a fight for human equality.",
                    "13th Amendment (1865) abolished slavery nationwide.",
                    "Assassinated by John Wilkes Booth on April 14, 1865 — 5 days after Confederate surrender.",
                ],
            },
            {
                "number": 17, "name": "Andrew Johnson", "party": "Democrat (National Union ticket)",
                "years": "1865–1869", "vp": "None",
                "key_facts": [
                    "Clashed bitterly with Radical Republicans over Reconstruction policy.",
                    "First president impeached by the House (1868); acquitted by the Senate by one vote.",
                    "Purchased Alaska from Russia for $7.2 million (1867).",
                    "Vetoed the Civil Rights Act of 1866; Congress overrode the veto.",
                ],
            },
        ],
    },
    {
        "era":     "Reconstruction & Gilded Age",
        "years":   "1869 – 1901",
        "color":   "#3A6EA8",
        "summary": (
            "Reconstruction attempted to integrate freed Black Americans into civic life, "
            "but was undermined by Southern resistance and Northern fatigue. The Gilded Age "
            "saw explosive industrialisation, the rise of robber barons, massive immigration, "
            "and growing calls for reform."
        ),
        "presidents": [
            {
                "number": 18, "name": "Ulysses S. Grant", "party": "Republican",
                "years": "1869–1877", "vp": "Schuyler Colfax / Henry Wilson",
                "key_facts": [
                    "Led Reconstruction-era federal enforcement against the KKK.",
                    "His administration was marred by the Crédit Mobilier and Whiskey Ring scandals.",
                    "15th Amendment ratified (1870) — gave Black men the right to vote.",
                ],
            },
            {
                "number": 19, "name": "Rutherford B. Hayes", "party": "Republican",
                "years": "1877–1881", "vp": "William A. Wheeler",
                "key_facts": [
                    "Won the disputed 1876 election via the Compromise of 1877.",
                    "Effectively ended Reconstruction by withdrawing federal troops from the South.",
                ],
            },
            {
                "number": 20, "name": "James A. Garfield", "party": "Republican",
                "years": "1881", "vp": "Chester A. Arthur",
                "key_facts": [
                    "Shot by a disappointed office-seeker July 2, 1881; died September 19.",
                    "His assassination galvanised civil service reform.",
                ],
            },
            {
                "number": 21, "name": "Chester A. Arthur", "party": "Republican",
                "years": "1881–1885", "vp": "None",
                "key_facts": [
                    "Signed the Pendleton Civil Service Reform Act (1883) — merit-based federal jobs.",
                    "Signed the Chinese Exclusion Act (1882), barring Chinese immigration for 10 years.",
                ],
            },
            {
                "number": 22, "name": "Grover Cleveland", "party": "Democrat",
                "years": "1885–1889", "vp": "Thomas A. Hendricks",
                "key_facts": [
                    "Only president to serve non-consecutive terms (22nd and 24th).",
                    "Vetoed hundreds of spending bills; known for fiscal conservatism.",
                    "First Democrat elected president since before the Civil War.",
                ],
            },
            {
                "number": 23, "name": "Benjamin Harrison", "party": "Republican",
                "years": "1889–1893", "vp": "Levi P. Morton",
                "key_facts": [
                    "Six states admitted to the Union during his term.",
                    "Sherman Antitrust Act (1890) — first federal law targeting monopolies.",
                    "Lost re-election to Grover Cleveland despite winning more electoral votes in 1888.",
                ],
            },
            {
                "number": 24, "name": "Grover Cleveland", "party": "Democrat",
                "years": "1893–1897", "vp": "Adlai Stevenson I",
                "key_facts": [
                    "Second non-consecutive term; faced the severe Panic of 1893.",
                    "Sent federal troops to break the Pullman Strike (1894).",
                ],
            },
            {
                "number": 25, "name": "William McKinley", "party": "Republican",
                "years": "1897–1901", "vp": "Garret Hobart / Theodore Roosevelt",
                "key_facts": [
                    "Spanish-American War (1898) — US acquired Puerto Rico, Guam, and the Philippines.",
                    "Presided over the annexation of Hawaii (1898).",
                    "Assassinated September 14, 1901 by anarchist Leon Czolgosz.",
                ],
            },
        ],
    },
    {
        "era":     "Progressive Era & World Power",
        "years":   "1901 – 1933",
        "color":   "#3DAA72",
        "summary": (
            "Reformers challenged industrial inequality, corruption, and monopoly power. "
            "The US emerged as a genuine world power, entered WWI, rejected the League "
            "of Nations, enjoyed the Roaring Twenties, and then collapsed into the "
            "Great Depression."
        ),
        "presidents": [
            {
                "number": 26, "name": "Theodore Roosevelt", "party": "Republican",
                "years": "1901–1909", "vp": "Charles W. Fairbanks",
                "key_facts": [
                    "Youngest president at 42; trust-buster who filed 44 antitrust suits.",
                    "Pure Food and Drug Act & Meat Inspection Act (1906) — consumer protections.",
                    "Won Nobel Peace Prize for mediating the Russo-Japanese War (1905).",
                    "Conservation — created 150 national forests and 5 national parks.",
                ],
            },
            {
                "number": 27, "name": "William Howard Taft", "party": "Republican",
                "years": "1909–1913", "vp": "James S. Sherman",
                "key_facts": [
                    "Filed more antitrust suits than Roosevelt despite being seen as less progressive.",
                    "16th Amendment (1913) — federal income tax authorised.",
                    "17th Amendment (1913) — direct election of US senators.",
                ],
            },
            {
                "number": 28, "name": "Woodrow Wilson", "party": "Democrat",
                "years": "1913–1921", "vp": "Thomas R. Marshall",
                "key_facts": [
                    "Led the US into WWI (1917); his Fourteen Points shaped the Paris Peace Conference.",
                    "Federal Reserve Act (1913) — created the central banking system.",
                    "League of Nations proposed by Wilson; rejected by the US Senate.",
                    "18th Amendment (Prohibition) and 19th Amendment (women's suffrage) ratified.",
                    "Suffered a severe stroke in 1919; his wife Edith effectively ran the presidency.",
                ],
            },
            {
                "number": 29, "name": "Warren G. Harding", "party": "Republican",
                "years": "1921–1923", "vp": "Calvin Coolidge",
                "key_facts": [
                    "Died in office August 2, 1923, likely from a heart attack.",
                    "Teapot Dome Scandal — administration rocked by corruption in oil leases.",
                    "Called for a 'return to normalcy' after WWI.",
                ],
            },
            {
                "number": 30, "name": "Calvin Coolidge", "party": "Republican",
                "years": "1923–1929", "vp": "Charles G. Dawes",
                "key_facts": [
                    "Presided over the economic boom of the 'Roaring Twenties'.",
                    "Known for minimal government intervention and fiscal restraint.",
                    "Declined to seek re-election in 1928.",
                ],
            },
            {
                "number": 31, "name": "Herbert Hoover", "party": "Republican",
                "years": "1929–1933", "vp": "Charles Curtis",
                "key_facts": [
                    "The Great Depression began with the stock market crash of October 1929.",
                    "Smoot-Hawley Tariff (1930) deepened the global depression.",
                    "Bonus Army — WWI veterans marching for benefits were dispersed by the military.",
                ],
            },
        ],
    },
    {
        "era":     "New Deal, WWII & Cold War Roots",
        "years":   "1933 – 1961",
        "color":   "#C9A84C",
        "summary": (
            "FDR transformed the federal government's role through the New Deal. "
            "The US led the Allied victory in WWII and emerged as a global superpower. "
            "The Cold War with the Soviet Union defined foreign policy and domestic life "
            "through McCarthyism and the nuclear arms race."
        ),
        "presidents": [
            {
                "number": 32, "name": "Franklin D. Roosevelt", "party": "Democrat",
                "years": "1933–1945", "vp": "Garner / Wallace / Truman",
                "key_facts": [
                    "Only president elected to four terms; served longer than any other.",
                    "New Deal programs (1933–39) — Social Security, SEC, FDIC, unemployment insurance.",
                    "Led the US through WWII; died April 12, 1945, just before Allied victory.",
                    "Executive Order 9066 — interned 120,000 Japanese Americans.",
                ],
            },
            {
                "number": 33, "name": "Harry S. Truman", "party": "Democrat",
                "years": "1945–1953", "vp": "Alben Barkley",
                "key_facts": [
                    "Authorised atomic bombings of Hiroshima and Nagasaki (August 1945).",
                    "Marshall Plan (1948) — $13B to rebuild war-torn Europe.",
                    "NATO founded (1949); Korean War (1950); desegregated the military (1948).",
                    "Truman Doctrine (1947) — US would support nations resisting communism.",
                ],
            },
            {
                "number": 34, "name": "Dwight D. Eisenhower", "party": "Republican",
                "years": "1953–1961", "vp": "Richard Nixon",
                "key_facts": [
                    "Interstate Highway System authorised (1956) — transformed American infrastructure.",
                    "Warned of the 'military-industrial complex' in his Farewell Address.",
                    "Sent federal troops to enforce school desegregation in Little Rock (1957).",
                    "NASA created (1958) in response to Soviet Sputnik launch.",
                ],
            },
        ],
    },
    {
        "era":     "Civil Rights, Vietnam & the Cultural Revolution",
        "years":   "1961 – 1981",
        "color":   "#4A90D9",
        "summary": (
            "America was torn apart and remade. JFK's assassination, the Civil Rights "
            "movement, Vietnam, Nixon's Watergate, and the energy crisis defined a "
            "generation. The era ended with a deep national crisis of confidence."
        ),
        "presidents": [
            {
                "number": 35, "name": "John F. Kennedy", "party": "Democrat",
                "years": "1961–1963", "vp": "Lyndon B. Johnson",
                "key_facts": [
                    "Youngest elected president; first Catholic president.",
                    "Cuban Missile Crisis (1962) — brought the world to the brink of nuclear war.",
                    "Peace Corps founded (1961); Apollo programme launched.",
                    "Assassinated in Dallas on November 22, 1963.",
                ],
            },
            {
                "number": 36, "name": "Lyndon B. Johnson", "party": "Democrat",
                "years": "1963–1969", "vp": "Hubert Humphrey",
                "key_facts": [
                    "Civil Rights Act (1964) and Voting Rights Act (1965) — landmark racial equality legislation.",
                    "Great Society programmes — Medicare, Medicaid, federal education funding.",
                    "Escalated Vietnam War to 500,000+ US troops; domestically devastating.",
                    "Declined to run for re-election amid anti-war protests.",
                ],
            },
            {
                "number": 37, "name": "Richard Nixon", "party": "Republican",
                "years": "1969–1974", "vp": "Agnew / Ford",
                "key_facts": [
                    "First president to resign; Watergate scandal (1972–74).",
                    "Opened diplomatic relations with China (1972).",
                    "Ended US involvement in Vietnam (1973 Paris Peace Accords).",
                    "EPA and OSHA created; Clean Air Act signed.",
                ],
            },
            {
                "number": 38, "name": "Gerald Ford", "party": "Republican",
                "years": "1974–1977", "vp": "Nelson Rockefeller",
                "key_facts": [
                    "Only president never elected as president or VP.",
                    "Pardoned Nixon — deeply unpopular; likely cost him the 1976 election.",
                    "Fall of Saigon (1975) — end of the Vietnam War.",
                ],
            },
            {
                "number": 39, "name": "Jimmy Carter", "party": "Democrat",
                "years": "1977–1981", "vp": "Walter Mondale",
                "key_facts": [
                    "Camp David Accords (1978) — brokered peace between Egypt and Israel.",
                    "Iran Hostage Crisis (1979–81) — 52 Americans held for 444 days.",
                    "Energy crisis and stagflation; Department of Energy created.",
                    "Later awarded the Nobel Peace Prize (2002) for post-presidential humanitarian work.",
                ],
            },
        ],
    },
    {
        "era":     "Reagan Revolution to the 21st Century",
        "years":   "1981 – 2001",
        "color":   "#D94A4A",
        "summary": (
            "Ronald Reagan reshaped American conservatism and accelerated the end of the "
            "Cold War. The Soviet Union dissolved in 1991. The 1990s brought economic "
            "prosperity, budget surpluses, and the dawn of the internet age, ending "
            "with the contested 2000 election."
        ),
        "presidents": [
            {
                "number": 40, "name": "Ronald Reagan", "party": "Republican",
                "years": "1981–1989", "vp": "George H. W. Bush",
                "key_facts": [
                    "Reaganomics — major tax cuts, deregulation, defence spending increases.",
                    "Iran-Contra Affair — secret arms sales to Iran to fund Nicaraguan rebels.",
                    "Challenged Soviet Union with military buildup and Strategic Defence Initiative.",
                    "Survived assassination attempt (March 30, 1981).",
                    "The Cold War effectively ended under his presidency.",
                ],
            },
            {
                "number": 41, "name": "George H. W. Bush", "party": "Republican",
                "years": "1989–1993", "vp": "Dan Quayle",
                "key_facts": [
                    "Led the Gulf War coalition (1991) to liberate Kuwait.",
                    "Oversaw the peaceful dissolution of the Soviet Union (1991).",
                    "Americans with Disabilities Act (1990) signed.",
                    "Broke 'no new taxes' pledge; lost re-election to Clinton.",
                ],
            },
            {
                "number": 42, "name": "Bill Clinton", "party": "Democrat",
                "years": "1993–2001", "vp": "Al Gore",
                "key_facts": [
                    "Longest economic expansion in US history; first budget surpluses since 1969.",
                    "NAFTA (1994); Family and Medical Leave Act; Brady Bill gun controls.",
                    "Impeached by House over the Lewinsky scandal (1998); acquitted by Senate.",
                    "NATO intervention in Kosovo; bombed Iraq over weapons inspections.",
                ],
            },
        ],
    },
    {
        "era":     "Post-9/11, Financial Crisis & Obama Years",
        "years":   "2001 – 2017",
        "color":   "#3A6EA8",
        "summary": (
            "The September 11 attacks redefined American foreign and domestic policy. "
            "Two costly wars followed. The 2008 financial crisis was the worst since "
            "the Great Depression. Barack Obama became the first Black president, "
            "passed landmark healthcare reform, and wound down the Iraq War."
        ),
        "presidents": [
            {
                "number": 43, "name": "George W. Bush", "party": "Republican",
                "years": "2001–2009", "vp": "Dick Cheney",
                "key_facts": [
                    "9/11 attacks (2001) — launched wars in Afghanistan and Iraq.",
                    "PATRIOT Act and creation of DHS transformed domestic security.",
                    "Iraq War (2003) based on faulty WMD intelligence; no weapons found.",
                    "2008 financial crisis — $700B TARP bank bailout signed.",
                    "Medicare Part D prescription drug benefit added.",
                ],
            },
            {
                "number": 44, "name": "Barack Obama", "party": "Democrat",
                "years": "2009–2017", "vp": "Joe Biden",
                "key_facts": [
                    "First African-American president; won Nobel Peace Prize 2009.",
                    "Affordable Care Act (2010) — largest healthcare reform since Medicare.",
                    "Ordered the mission that killed Osama bin Laden (May 2011).",
                    "Dodd-Frank financial reform; Recovery Act stimulus ($787B).",
                    "Legalisation of same-sex marriage nationwide (Obergefell v. Hodges, 2015).",
                ],
            },
        ],
    },
    {
        "era":     "Populist Era & Political Polarisation",
        "years":   "2017 – Present",
        "color":   "#C95C4C",
        "summary": (
            "Donald Trump's first term upended political norms, trade policy, and "
            "alliances. Joe Biden oversaw post-COVID recovery and record inflation. "
            "Trump's 2024 landslide return to power — the first convicted felon elected "
            "president — ushered in aggressive executive action including military "
            "strikes on Iran in early 2026."
        ),
        "presidents": [
            {
                "number": 45, "name": "Donald J. Trump (1st term)", "party": "Republican",
                "years": "2017–2021", "vp": "Mike Pence",
                "key_facts": [
                    "Tax Cuts and Jobs Act (2017) — largest corporate tax cut in US history.",
                    "Withdrew from the Paris Climate Agreement and Trans-Pacific Partnership.",
                    "Abraham Accords (2020) — normalised Israel-Arab relations.",
                    "COVID-19 pandemic; Operation Warp Speed delivered vaccines in record time.",
                    "Impeached twice (2019 and 2021); acquitted both times by the Senate.",
                    "January 6, 2021 Capitol riot followed his election loss to Biden.",
                ],
            },
            {
                "number": 46, "name": "Joe Biden", "party": "Democrat",
                "years": "2021–2025", "vp": "Kamala Harris",
                "key_facts": [
                    "Infrastructure Investment and Jobs Act (2021) — $1.2 trillion.",
                    "Inflation Reduction Act (2022) — $369B in climate spending.",
                    "US withdrawal from Afghanistan (August 2021).",
                    "Record inflation peaking at 9.1% (June 2022).",
                    "Oldest president in US history; declined to seek re-election July 2024.",
                ],
            },
            {
                "number": 47, "name": "Donald J. Trump (2nd term)", "party": "Republican",
                "years": "2025–Present", "vp": "JD Vance",
                "key_facts": [
                    "First president convicted of felony crimes (34 counts) before taking office.",
                    "Launched sweeping tariffs on imports, triggering global trade tensions.",
                    "Ordered Operation Epic Fury airstrikes on Iran (February 28, 2026) with Israel.",
                    "Rapid executive order campaign targeting immigration, DEI, and federal workforce.",
                    "DOGE — Department of Government Efficiency created under Elon Musk to cut federal spending.",
                ],
            },
        ],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  GOVERNMENT HISTORY PANEL
# ══════════════════════════════════════════════════════════════════════════════

class PresidentCard(ctk.CTkFrame):
    """Compact card for a single president, expandable for key facts."""

    def __init__(self, master, pres, era_color, **kwargs):
        super().__init__(
            master,
            fg_color=PALETTE["bg"],
            corner_radius=8,
            border_width=1,
            border_color=PALETTE["border"],
            **kwargs
        )
        self.pres      = pres
        self.era_color = era_color
        self._expanded = False
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", padx=14, pady=10)

        # Number circle
        num_frame = ctk.CTkFrame(hdr, width=36, height=36, corner_radius=18,
                                  fg_color=PALETTE["surface_2"],
                                  border_width=1, border_color=self.era_color)
        num_frame.pack(side="left", padx=(0, 12))
        num_frame.pack_propagate(False)
        ctk.CTkLabel(
            num_frame, text=str(self.pres["number"]),
            font=("Courier New", 10, "bold"),
            text_color=self.era_color
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Name & meta
        info = ctk.CTkFrame(hdr, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info, text=self.pres["name"],
            font=("Georgia", 13, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(fill="x")

        meta_row = ctk.CTkFrame(info, fg_color="transparent")
        meta_row.pack(fill="x")

        ctk.CTkLabel(
            meta_row, text=self.pres["years"],
            font=("Courier New", 10),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            meta_row, text="  |  ",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"]
        ).pack(side="left")

        party_color = (PALETTE["dem_light"] if "Democrat" in self.pres["party"]
                       else PALETTE["rep_light"] if "Republican" in self.pres["party"]
                       else PALETTE["text_secondary"])
        ctk.CTkLabel(
            meta_row, text=self.pres["party"],
            font=("Courier New", 10),
            text_color=party_color, anchor="w"
        ).pack(side="left")

        self.toggle_btn = ctk.CTkButton(
            hdr, text="▼", width=30, height=24,
            corner_radius=4,
            fg_color=PALETTE["surface_2"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._toggle
        )
        self.toggle_btn.pack(side="right")

        self.facts_frame = ctk.CTkFrame(self, fg_color="transparent")
        # hidden until expanded

        for fact in self.pres["key_facts"]:
            row = ctk.CTkFrame(self.facts_frame, fg_color="transparent")
            row.pack(fill="x", padx=62, pady=2)

            dot = ctk.CTkFrame(row, width=5, height=5, corner_radius=3,
                               fg_color=self.era_color)
            dot.pack(side="left", padx=(0, 8))
            dot.pack_propagate(False)

            ctk.CTkLabel(
                row, text=fact,
                font=("Courier New", 10),
                text_color=PALETTE["text_secondary"],
                wraplength=750, justify="left", anchor="w"
            ).pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self.facts_frame, height=8, fg_color="transparent").pack()

        for w in (hdr, info, meta_row):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.facts_frame.pack(fill="x")
            self.toggle_btn.configure(text="▲")
        else:
            self.facts_frame.pack_forget()
            self.toggle_btn.configure(text="▼")


class EraSection(ctk.CTkFrame):
    """Collapsible section for one historical era containing president cards."""

    def __init__(self, master, era_data, **kwargs):
        super().__init__(master, fg_color=PALETTE["surface"],
                         border_width=1, border_color=era_data["color"],
                         corner_radius=10, **kwargs)
        self.era_data  = era_data
        self._expanded = False
        self._build_header()
        self._build_body()

    def _build_header(self):
        # Left stripe
        stripe = ctk.CTkFrame(self, width=4, fg_color=self.era_data["color"], corner_radius=0)
        stripe.place(x=0, y=0, relheight=1)

        hdr = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        hdr.pack(fill="x", padx=20, pady=14)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top, text=self.era_data["era"],
            font=("Georgia", 15, "bold"),
            text_color=self.era_data["color"], anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            top, text=f"   {self.era_data['years']}",
            font=("Courier New", 10),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(side="left")

        pres_count = len(self.era_data["presidents"])
        ctk.CTkLabel(
            left,
            text=f"{pres_count} President{'s' if pres_count != 1 else ''} — click to expand",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x")

        self.toggle_btn = ctk.CTkButton(
            hdr, text="▼  Expand", width=110, height=28,
            corner_radius=6,
            fg_color=PALETTE["surface_2"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._toggle
        )
        self.toggle_btn.pack(side="right")

        for w in (hdr, left, top):
            w.bind("<Button-1>", lambda e: self._toggle())

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")

        # Era summary
        ctk.CTkLabel(
            self.body,
            text=self.era_data["summary"],
            font=("Georgia", 12),
            text_color=PALETTE["text_secondary"],
            wraplength=860, justify="left", anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 12))

        # President cards
        for pres in self.era_data["presidents"]:
            PresidentCard(self.body, pres, self.era_data["color"]).pack(
                fill="x", padx=24, pady=(0, 8))

        ctk.CTkFrame(self.body, height=12, fg_color="transparent").pack()

    def _toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(0, 12))
            self.toggle_btn.configure(text="▲  Collapse")
        else:
            self.body.pack_forget()
            self.toggle_btn.configure(text="▼  Expand")


class GovHistoryPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 4))

        ctk.CTkLabel(
            hdr, text="U.S. Government & Presidential History",
            font=("Georgia", 24, "bold"),
            text_color=PALETTE["text_primary"], anchor="w"
        ).pack(side="left")

        badge = ctk.CTkFrame(hdr, fg_color=PALETTE["surface_2"],
                              corner_radius=4, border_width=1,
                              border_color=PALETTE["border"])
        badge.pack(side="right", pady=6)
        total_presidents = sum(len(e["presidents"]) for e in GOV_ERAS)
        ctk.CTkLabel(
            badge, text=f"  {total_presidents} PRESIDENTS  •  {len(GOV_ERAS)} ERAS  ",
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"]
        ).pack(pady=4)

        ctk.CTkLabel(
            self,
            text="The progression of American leadership from 1789 to the present day.",
            font=("Courier New", 11),
            text_color=PALETTE["text_secondary"], anchor="w"
        ).pack(fill="x", padx=40, pady=(0, 16))

        # Expand / Collapse all controls
        ctrl_row = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=40, pady=(0, 12))

        ctk.CTkLabel(
            ctrl_row, text="QUICK ACTIONS:",
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            ctrl_row, text="Expand All", width=100, height=26,
            corner_radius=6,
            fg_color=PALETTE["surface_2"], hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._expand_all
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_row, text="Collapse All", width=100, height=26,
            corner_radius=6,
            fg_color=PALETTE["surface_2"], hover_color=PALETTE["border"],
            text_color=PALETTE["text_secondary"],
            font=("Courier New", 10, "bold"),
            command=self._collapse_all
        ).pack(side="left")

        # Scrollable era sections
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=PALETTE["border"],
            scrollbar_fg_color=PALETTE["surface"],
        )
        self.scroll.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        self._era_sections = []
        for era in GOV_ERAS:
            section = EraSection(self.scroll, era)
            section.pack(fill="x", pady=(0, 12))
            self._era_sections.append(section)

    def _expand_all(self):
        for section in self._era_sections:
            if not section._expanded:
                section._toggle()

    def _collapse_all(self):
        for section in self._era_sections:
            if section._expanded:
                section._toggle()


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, on_theme_change, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_theme_change = on_theme_change
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Preferences", font=("Georgia", 24, "bold"),
                     text_color=PALETTE["text_primary"]).pack(anchor="w", padx=40, pady=(40, 20))

        container = ctk.CTkFrame(self, fg_color=PALETTE["surface"],
                                  border_color=PALETTE["border"], border_width=1,
                                  corner_radius=12)
        container.pack(fill="x", padx=40, pady=(0, 20))

        # ── Theme selector ────────────────────────────────────────────────
        self._section(container, "APPEARANCE", first=True)

        ctk.CTkLabel(
            container,
            text="Select a theme — changes apply instantly across the entire application.",
            font=("Courier New", 10),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=30, pady=(0, 16))

        # Theme preview swatches
        swatch_frame = ctk.CTkFrame(container, fg_color="transparent")
        swatch_frame.pack(fill="x", padx=30, pady=(0, 24))

        self.swatches = {}
        for name, theme in THEMES.items():
            col = ctk.CTkFrame(swatch_frame, fg_color="transparent", cursor="hand2")
            col.pack(side="left", padx=(0, 16))

            is_active = (name == CURRENT_THEME[0])
            size = 80 if is_active else 60

            swatch = ctk.CTkFrame(col, width=size, height=size, corner_radius=12,
                                   fg_color=theme["bg"],
                                   border_width=0)
            swatch.pack()
            swatch.pack_propagate(False)

            # Accent dot inside
            dot_size = 24 if is_active else 18
            dot = ctk.CTkFrame(swatch, width=dot_size, height=dot_size, corner_radius=dot_size // 2,
                                fg_color=theme["accent"])
            dot.place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(col, text=name,
                         font=("Courier New", 9, "bold" if is_active else "normal"),
                         text_color=theme["accent"] if is_active else PALETTE["text_dim"]
                         ).pack(pady=(6, 0))

            self.swatches[name] = (swatch, dot, col)

            def _click(e, n=name):
                self._on_theme_selected(n)

            for w in (swatch, dot, col):
                w.bind("<Button-1>", _click)

        # ── Divider ───────────────────────────────────────────────────────
        ctk.CTkFrame(container, height=1, fg_color=PALETTE["border"]).pack(
            fill="x", padx=20, pady=(0, 20))

        # ── AI section ────────────────────────────────────────────────────
        self._section(container, "AI CORE ENGINE")

        ai_row = ctk.CTkFrame(container, fg_color="transparent")
        ai_row.pack(fill="x", padx=30, pady=(0, 24))

        dot = ctk.CTkFrame(ai_row, width=10, height=10, corner_radius=5,
                            fg_color=PALETTE["positive"])
        dot.pack(side="left", padx=(0, 10))
        dot.pack_propagate(False)

        ctk.CTkLabel(
            ai_row,
            text="Connected via OpenAI API (gpt-3.5-turbo-instruct)",
            text_color=PALETTE["positive"],
            font=("Courier New", 12)
        ).pack(side="left")

    def _section(self, parent, label, first=False):
        ctk.CTkLabel(
            parent, text=label,
            font=("Courier New", 9, "bold"),
            text_color=PALETTE["text_dim"], anchor="w"
        ).pack(fill="x", padx=30, pady=(24 if not first else 24, 10))

    def _on_theme_selected(self, name):
        self.on_theme_change(name)
        # UI is rebuilt by on_theme_change so no swatch update needed here


# ── Main Application ──────────────────────────────────────────────────────────

class ExecutiveInsight(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Executive Insight")
        self.geometry("1280x800")
        self.configure(fg_color=PALETTE["bg"])
        self.engine = LegalEngine()
        self._build_ui()
        self._show_panel("Dashboard")

    # ── Build all UI from current PALETTE ─────────────────────────────────────
    def _build_ui(self):
        # Destroy any previous body if rebuilding
        for w in self.winfo_children():
            w.destroy()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        self.sidebar = Sidebar(body, on_select=self._show_panel)
        self.sidebar.pack(side="left", fill="y")

        self._divider = ctk.CTkFrame(body, width=1, fg_color=PALETTE["border"], corner_radius=0)
        self._divider.pack(side="left", fill="y")

        self.content_area = ctk.CTkFrame(body, fg_color=PALETTE["bg"], corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        self.panels = {
            "Dashboard":    DashboardPanel(self.content_area, self.engine),
            "Legal Q&A":    LegalQAPanel(self.content_area, self.engine),
            "Bills":        BillsPanel(self.content_area, self.engine),
            "Party Impact": PartyImpactPanel(self.content_area),
            "US Wars":      USWarsPanel(self.content_area),
            "Gov. History": GovHistoryPanel(self.content_area),
            "Settings":     SettingsPanel(self.content_area, on_theme_change=self._apply_theme),
        }

    # ── Theme application ──────────────────────────────────────────────────────
    def _apply_theme(self, theme_name):
        if theme_name not in THEMES:
            return

        # Update global palette in-place so all future widget refs use new colours
        PALETTE.update(THEMES[theme_name])
        CURRENT_THEME[0] = theme_name

        # Switch CTk light/dark mode if needed
        ctk.set_appearance_mode(PALETTE["ctk_mode"])

        # Update root window background
        self.configure(fg_color=PALETTE["bg"])

        # Rebuild the entire UI with the new palette
        self._build_ui()
        self._show_panel("Settings")

    # ── Panel switching ────────────────────────────────────────────────────────
    def _show_panel(self, name):
        for panel in self.panels.values():
            panel.pack_forget()
        if name in self.panels:
            self.panels[name].pack(fill="both", expand=True)
        # Keep sidebar active state in sync
        if hasattr(self, "sidebar"):
            self.sidebar.set_active(name)


if __name__ == "__main__":
    app = ExecutiveInsight()
    app.mainloop()
