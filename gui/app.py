#!/usr/bin/env python3
"""
DnD GM Toolkit - Desktop GUI Application

Main GUI application using CustomTkinter for modern look.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import customtkinter as ctk
    from tkinter import messagebox, scrolledtext
    from PIL import Image, ImageTk
except ImportError:
    print("=" * 60)
    print("ERROR: Missing required packages for GUI mode")
    print("=" * 60)
    print()
    print("To use the Desktop GUI, install the required packages:")
    print()
    print("  pip install customtkinter Pillow")
    print()
    print("Or install all optional dependencies:")
    print("  pip install -r requirements.txt")
    print()
    print("=" * 60)
    sys.exit(1)

from core.db_manager import DatabaseManager
from ai.campaign_memory import CampaignMemory
from ai.linear_generator import LinearContentGenerator

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GUIApp(ctk.CTk):
    """Desktop GUI Application for GM Toolkit."""
    
    def __init__(self):
        super().__init__()
        
        self.db = DatabaseManager()
        self.memory = CampaignMemory()
        self.current_campaign = None
        
        # Window setup
        self.title("DnD GM Toolkit v3.0")
        self.geometry("1200x800")
        
        # Create main layout
        self.create_widgets()
        
        # Load initial data
        self.refresh_campaign_list()
    
    def create_widgets(self):
        """Create main widgets."""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left sidebar
        self.sidebar = ctk.CTkFrame(self.main_frame, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            self.sidebar, 
            text="DnD GM Toolkit", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Navigation buttons
        self.btn_campaigns = ctk.CTkButton(
            self.sidebar, text="📁 Campaigns", 
            command=self.show_campaigns_tab, height=40
        )
        self.btn_campaigns.pack(fill="x", padx=10, pady=5)
        
        self.btn_generate = ctk.CTkButton(
            self.sidebar, text="🎲 Generate", 
            command=self.show_generate_tab, height=40
        )
        self.btn_generate.pack(fill="x", padx=10, pady=5)
        
        self.btn_track = ctk.CTkButton(
            self.sidebar, text="📊 Track", 
            command=self.show_track_tab, height=40
        )
        self.btn_track.pack(fill="x", padx=10, pady=5)
        
        self.btn_ai = ctk.CTkButton(
            self.sidebar, text="🤖 AI Tools", 
            command=self.show_ai_tab, height=40
        )
        self.btn_ai.pack(fill="x", padx=10, pady=5)
        
        self.btn_utils = ctk.CTkButton(
            self.sidebar, text="🛠️ Utils", 
            command=self.show_utils_tab, height=40
        )
        self.btn_utils.pack(fill="x", padx=10, pady=5)
        
        # Right content area
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        # Create tabs (frames that we show/hide)
        self.create_campaigns_tab()
        self.create_generate_tab()
        self.create_track_tab()
        self.create_ai_tab()
        self.create_utils_tab()
        
        # Show campaigns tab by default
        self.show_campaigns_tab()
    
    def create_campaigns_tab(self):
        """Create campaigns tab."""
        self.campaigns_tab = ctk.CTkFrame(self.content_frame)
        
        # Header
        header = ctk.CTkLabel(
            self.campaigns_tab,
            text="Campaign Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Campaign list
        list_frame = ctk.CTkFrame(self.campaigns_tab)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.campaign_listbox = scrolledtext.ScrolledText(
            list_frame, height=20, width=80,
            bg="#2b2b2b", fg="white", font=("Courier", 11)
        )
        self.campaign_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.campaigns_tab)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(
            btn_frame, text="New Campaign",
            command=self.new_campaign
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="Select Campaign",
            command=self.select_campaign
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="Delete Campaign",
            command=self.delete_campaign,
            fg_color="red"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="Refresh",
            command=self.refresh_campaign_list
        ).pack(side="left", padx=10)
    
    def create_generate_tab(self):
        """Create generate tab."""
        self.generate_tab = ctk.CTkFrame(self.content_frame)
        
        header = ctk.CTkLabel(
            self.generate_tab,
            text="Content Generation",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Generator buttons
        gen_frame = ctk.CTkFrame(self.generate_tab)
        gen_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        generators = [
            ("⚔️ Encounter", self.generate_encounter),
            ("💰 Loot", self.generate_loot),
            ("👤 NPC", self.generate_npc),
            ("📜 Quest (AI)", self.generate_quest),
            ("🏰 Dungeon", self.generate_dungeon),
            ("🌤️ Weather", self.generate_weather),
        ]
        
        for i, (text, command) in enumerate(generators):
            row = i // 3
            col = i % 3
            
            btn = ctk.CTkButton(
                gen_frame, text=text, width=150, height=60,
                command=command, font=ctk.CTkFont(size=14)
            )
            btn.grid(row=row, column=col, padx=20, pady=20)
        
        # Output area
        self.generate_output = scrolledtext.ScrolledText(
            self.generate_tab, height=15, width=80,
            bg="#1a1a1a", fg="#00ff00", font=("Courier", 10)
        )
        self.generate_output.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_track_tab(self):
        """Create track tab."""
        self.track_tab = ctk.CTkFrame(self.content_frame)
        
        header = ctk.CTkLabel(
            self.track_tab,
            text="Campaign Tracking",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Stats frame
        stats_frame = ctk.CTkFrame(self.track_tab)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.stats_labels = {}
        stats = ["Sessions", "Characters", "NPCs", "Locations", "Plot Threads"]
        
        for i, stat in enumerate(stats):
            label = ctk.CTkLabel(
                stats_frame,
                text=f"{stat}\n0",
                font=ctk.CTkFont(size=14)
            )
            label.grid(row=0, column=i, padx=20, pady=10)
            self.stats_labels[stat] = label
        
        # Content area
        content_frame = ctk.CTkFrame(self.track_tab)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.track_output = scrolledtext.ScrolledText(
            content_frame, height=25, width=80,
            bg="#2b2b2b", fg="white", font=("Courier", 10)
        )
        self.track_output.pack(fill="both", expand=True)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(self.track_tab)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="New Session", command=self.new_session).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Add Character", command=self.add_character).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Add Plot Thread", command=self.add_plot_thread).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_track).pack(side="left", padx=10)
    
    def create_ai_tab(self):
        """Create AI tab."""
        self.ai_tab = ctk.CTkFrame(self.content_frame)
        
        header = ctk.CTkLabel(
            self.ai_tab,
            text="AI Tools",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # AI action buttons
        ai_frame = ctk.CTkFrame(self.ai_tab)
        ai_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(ai_frame, text="Train AI", command=self.train_ai).pack(side="left", padx=10)
        ctk.CTkButton(ai_frame, text="Show Status", command=self.show_ai_status).pack(side="left", padx=10)
        ctk.CTkButton(ai_frame, text="Generate Choices", command=self.generate_choices).pack(side="left", padx=10)
        
        # Output area
        self.ai_output = scrolledtext.ScrolledText(
            self.ai_tab, height=25, width=80,
            bg="#1a1a1a", fg="#00ff00", font=("Courier", 10)
        )
        self.ai_output.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_utils_tab(self):
        """Create utilities tab."""
        self.utils_tab = ctk.CTkFrame(self.content_frame)
        
        header = ctk.CTkLabel(
            self.utils_tab,
            text="Utilities",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Utility buttons
        utils_frame = ctk.CTkFrame(self.utils_tab)
        utils_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        utils = [
            ("🏨 Tavern", self.generate_tavern),
            ("🪤 Trap", self.generate_trap),
            ("❓ Riddle", self.generate_riddle),
            ("🦹 Villain", self.generate_villain),
            ("📊 Stats", self.show_stats),
        ]
        
        for i, (text, command) in enumerate(utils):
            btn = ctk.CTkButton(
                utils_frame, text=text, width=150, height=60,
                command=command, font=ctk.CTkFont(size=14)
            )
            btn.grid(row=i // 3, column=i % 3, padx=20, pady=20)
        
        # Output area
        self.utils_output = scrolledtext.ScrolledText(
            self.utils_tab, height=15, width=80,
            bg="#2b2b2b", fg="white", font=("Courier", 10)
        )
        self.utils_output.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Tab switching
    def show_campaigns_tab(self):
        self.hide_all_tabs()
        self.campaigns_tab.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_campaign_list()
    
    def show_generate_tab(self):
        self.hide_all_tabs()
        self.generate_tab.pack(fill="both", expand=True, padx=10, pady=10)
    
    def show_track_tab(self):
        self.hide_all_tabs()
        self.track_tab.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_track()
    
    def show_ai_tab(self):
        self.hide_all_tabs()
        self.ai_tab.pack(fill="both", expand=True, padx=10, pady=10)
    
    def show_utils_tab(self):
        self.hide_all_tabs()
        self.utils_tab.pack(fill="both", expand=True, padx=10, pady=10)
    
    def hide_all_tabs(self):
        for tab in [self.campaigns_tab, self.generate_tab, self.track_tab, self.ai_tab, self.utils_tab]:
            tab.pack_forget()
    
    # Campaign operations
    def refresh_campaign_list(self):
        """Refresh campaign list display."""
        self.campaign_listbox.delete(1.0, "end")
        
        campaigns = self.db.list_campaigns()
        
        if not campaigns:
            self.campaign_listbox.insert("end", "No campaigns yet. Create one!\n")
            return
        
        for camp in campaigns:
            stats = self.db.get_campaign_stats(camp['id'])
            line = f"[ID:{camp['id']}] {camp['name']}"
            line += f" | Sessions: {stats['sessions']}"
            line += f" | Last: {camp.get('last_played', 'Never')[:10] if camp.get('last_played') else 'Never'}\n"
            self.campaign_listbox.insert("end", line)
    
    def new_campaign(self):
        """Create new campaign dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Campaign")
        dialog.geometry("400x300")
        
        ctk.CTkLabel(dialog, text="Campaign Name:").pack(pady=10)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Description:").pack(pady=10)
        desc_entry = ctk.CTkEntry(dialog, width=300)
        desc_entry.pack(pady=5)
        
        def create():
            name = name_entry.get()
            desc = desc_entry.get()
            
            if name:
                self.db.create_campaign(name, desc)
                self.refresh_campaign_list()
                messagebox.showinfo("Success", f"Campaign '{name}' created!")
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter a campaign name")
        
        ctk.CTkButton(dialog, text="Create", command=create).pack(pady=20)
    
    def select_campaign(self):
        """Select a campaign."""
        try:
            line = self.campaign_listbox.get("current linestart", "current lineend")
            if "[ID:" in line:
                start = line.find("[ID:") + 4
                end = line.find("]", start)
                campaign_id = int(line[start:end])
                
                campaign = self.db.get_campaign(campaign_id=campaign_id)
                if campaign:
                    self.current_campaign = campaign
                    self.memory.set_campaign_name(campaign['name'])
                    messagebox.showinfo("Selected", f"Selected: {campaign['name']}")
                    self.refresh_track()
        except:
            messagebox.showwarning("Warning", "Please select a campaign from the list")
    
    def delete_campaign(self):
        """Delete selected campaign."""
        if messagebox.askyesno("Confirm", "Delete this campaign? All data will be lost!"):
            try:
                line = self.campaign_listbox.get("current linestart", "current lineend")
                if "[ID:" in line:
                    start = line.find("[ID:") + 4
                    end = line.find("]", start)
                    campaign_id = int(line[start:end])
                    
                    self.db.delete_campaign(campaign_id)
                    self.refresh_campaign_list()
                    messagebox.showinfo("Success", "Campaign deleted")
            except:
                messagebox.showwarning("Warning", "Please select a campaign")
    
    # Generate operations
    def generate_encounter(self):
        """Generate encounter."""
        from generators.encounter_gen import EncounterGenerator
        
        gen = EncounterGenerator()
        encounter = gen.generate_encounter(
            difficulty="medium",
            terrain="forest",
            party_level=5,
            party_size=4
        )
        
        output = f"=== Encounter ===\n"
        output += f"Difficulty: {encounter['difficulty']}\n"
        output += f"XP Budget: {encounter['xp_budget']}\n\n"
        output += "Monsters:\n"
        
        for m in encounter['monsters']:
            output += f"  • {m.get('count', 1)}x {m['name']} (CR {m['cr']}, AC {m.get('ac', 10)}, HP {m.get('hp', 10)})\n"
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    def generate_loot(self):
        """Generate loot."""
        from generators.loot_gen import LootGenerator
        
        gen = LootGenerator()
        hoard = gen.generate_hoard(party_level=5, party_size=4)
        
        output = f"=== Treasure Hoard ===\n"
        output += f"Gold: {hoard['gold_pieces']} gp\n"
        output += f"Gems: {hoard['gems']['count']} ({hoard['gems']['total_value']} gp)\n"
        output += f"Art: {hoard['art_objects']['count']} ({hoard['art_objects']['total_value']} gp)\n"
        output += f"Magic Items: {len(hoard['magic_items'])}\n"
        output += f"Total Value: {hoard['total_value']} gp\n"
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    def generate_npc(self):
        """Generate NPC."""
        from generators.npc_gen import NPCGenerator
        
        gen = NPCGenerator()
        npc = gen.generate_npc(race="human")
        
        output = f"=== {npc['identity']['name']} ===\n"
        output += f"{npc['identity']['race']} {npc['identity']['class']} (Level {npc['identity']['level']})\n"
        output += f"Background: {npc['identity']['background']}\n"
        output += f"Alignment: {npc['identity']['alignment']}\n\n"
        output += f"{npc.get('description', '')}\n"
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    def generate_quest(self):
        """Generate AI quest."""
        gen = LinearContentGenerator()
        quest = gen.generate_quest(theme="rescue", party_level=1, num_stages=5)
        
        output = f"=== {quest.title} ===\n"
        output += f"Theme: {quest.theme}\n"
        output += f"Levels: {quest.party_level_range[0]}-{quest.party_level_range[1]}\n\n"
        output += "Progression:\n"
        
        for stage in quest.stages:
            output += f"  Stage {stage.stage_number}: {stage.name} ({stage.difficulty})\n"
            output += f"    {stage.description}\n"
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    def generate_dungeon(self):
        """Generate dungeon."""
        from dungeon_generator import DungeonGenerator
        
        gen = DungeonGenerator()
        dungeon = gen.generate_dungeon(theme="crypt", levels=3)
        
        output = f"=== {dungeon.name} ===\n"
        output += f"Theme: {dungeon.theme}\n"
        output += f"Levels: {dungeon.total_levels}\n\n"
        output += f"{dungeon.backstory}\n\n"
        output += "Features:\n"
        
        for feature in dungeon.dungeon_features:
            output += f"  • {feature}\n"
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    def generate_weather(self):
        """Generate weather."""
        from weather_generator import WeatherGenerator
        
        gen = WeatherGenerator()
        forecast = gen.generate_forecast(days=7)
        
        output = gen.display_forecast(forecast)
        
        self.generate_output.delete(1.0, "end")
        self.generate_output.insert("end", output)
    
    # Track operations
    def refresh_track(self):
        """Refresh track tab."""
        if not self.current_campaign:
            self.track_output.delete(1.0, "end")
            self.track_output.insert("end", "No campaign selected. Select one from Campaigns tab.")
            return
        
        # Update stats
        stats = self.db.get_campaign_stats(self.current_campaign['id'])
        
        self.stats_labels["Sessions"].configure(text=f"Sessions\n{stats['sessions']}")
        self.stats_labels["Characters"].configure(text=f"Characters\n{stats['characters']}")
        self.stats_labels["NPCs"].configure(text=f"NPCs\n{stats['npcs']}")
        self.stats_labels["Locations"].configure(text=f"Locations\n{stats['locations']}")
        self.stats_labels["Plot Threads"].configure(text=f"Plot Threads\n{stats['active_threads']}")
        
        # Show recent content
        output = f"=== {self.current_campaign['name']} ===\n\n"
        
        # Sessions
        sessions = self.db.get_campaign_sessions(self.current_campaign['id'])
        output += "Recent Sessions:\n"
        for s in sessions[-3:]:
            output += f"  • Session {s['session_number']}: {s.get('title', 'Untitled')}\n"
        
        # Characters
        characters = self.db.get_campaign_characters(self.current_campaign['id'])
        output += "\nCharacters:\n"
        for c in characters:
            output += f"  • {c['name']} ({c.get('char_class', '?')} {c.get('level', 1)})\n"
        
        # Plot threads
        threads = self.db.get_campaign_plot_threads(self.current_campaign['id'], status="active")
        output += "\nActive Plot Threads:\n"
        for t in threads:
            output += f"  • {t['title']}\n"
        
        self.track_output.delete(1.0, "end")
        self.track_output.insert("end", output)
    
    def new_session(self):
        """Start new session."""
        if not self.current_campaign:
            messagebox.showwarning("Warning", "Select a campaign first")
            return
        
        sessions = self.db.get_campaign_sessions(self.current_campaign['id'])
        session_num = len(sessions) + 1
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Session")
        dialog.geometry("400x200")
        
        ctk.CTkLabel(dialog, text="Session Title:").pack(pady=10)
        title_entry = ctk.CTkEntry(dialog, width=300)
        title_entry.insert(0, f"Session {session_num}")
        title_entry.pack(pady=5)
        
        def create():
            title = title_entry.get()
            self.db.create_session(
                campaign_id=self.current_campaign['id'],
                session_number=session_num,
                title=title
            )
            self.memory.start_session(session_num, title)
            self.refresh_track()
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Start Session", command=create).pack(pady=20)
    
    def add_character(self):
        """Add character dialog."""
        if not self.current_campaign:
            messagebox.showwarning("Warning", "Select a campaign first")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Character")
        dialog.geometry("400x400")
        
        fields = {}
        for label, default in [("Name", ""), ("Player", ""), ("Class", "Fighter"), 
                               ("Race", "Human"), ("Level", "1"), ("Max HP", "10")]:
            ctk.CTkLabel(dialog, text=label + ":").pack(pady=5)
            entry = ctk.CTkEntry(dialog, width=300)
            entry.insert(0, default)
            entry.pack(pady=2)
            fields[label.lower()] = entry
        
        def add():
            self.db.create_character(
                campaign_id=self.current_campaign['id'],
                name=fields['name'].get(),
                player_name=fields['player'].get(),
                char_class=fields['class'].get(),
                race=fields['race'].get(),
                level=int(fields['level'].get()),
                hp_max=int(fields['max hp'].get())
            )
            self.refresh_track()
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Add Character", command=add).pack(pady=20)
    
    def add_plot_thread(self):
        """Add plot thread dialog."""
        if not self.current_campaign:
            messagebox.showwarning("Warning", "Select a campaign first")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Plot Thread")
        dialog.geometry("400x250")
        
        ctk.CTkLabel(dialog, text="Title:").pack(pady=5)
        title_entry = ctk.CTkEntry(dialog, width=300)
        title_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Description:").pack(pady=5)
        desc_entry = ctk.CTkEntry(dialog, width=300)
        desc_entry.pack(pady=5)
        
        def add():
            self.db.create_plot_thread(
                campaign_id=self.current_campaign['id'],
                title=title_entry.get(),
                description=desc_entry.get()
            )
            self.refresh_track()
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Add Thread", command=add).pack(pady=20)
    
    # AI operations
    def train_ai(self):
        """Train AI."""
        from ai.ai_trainer import AITrainer
        
        self.ai_output.delete(1.0, "end")
        self.ai_output.insert("end", "Training AI on all content...\n\n")
        
        trainer = AITrainer()
        stats = trainer.train_on_all_content()
        
        output = "=== Training Complete ===\n\n"
        for key, value in stats.items():
            output += f"{key}: {value}\n"
        
        self.ai_output.delete(1.0, "end")
        self.ai_output.insert("end", output)
    
    def show_ai_status(self):
        """Show AI status."""
        from ai.ai_trainer import AITrainer
        
        trainer = AITrainer()
        status = trainer.get_training_status()
        
        output = "=== AI Training Status ===\n\n"
        output += f"Content processed: {status.get('content_processed', 0)}\n"
        output += f"Patterns learned: {status.get('patterns_learned', 0)}\n"
        
        self.ai_output.delete(1.0, "end")
        self.ai_output.insert("end", output)
    
    def generate_choices(self):
        """Generate story choices."""
        from ai.choice_engine import ChoiceEngine
        
        engine = ChoiceEngine()
        choice = engine.generate_choices('conflict')
        
        output = f"{choice.question}\n\n"
        for i, opt in enumerate(choice.options, 1):
            risk = opt.get('risk', '')
            output += f"  {i}. {opt['text']} (Risk: {risk})\n"
        
        self.ai_output.delete(1.0, "end")
        self.ai_output.insert("end", output)
    
    # Utility operations
    def generate_tavern(self):
        """Generate tavern."""
        from gm_toolkit_extra import TavernGenerator
        
        gen = TavernGenerator()
        tavern = gen.generate_tavern()
        
        output = f"=== {tavern['name']} ===\n"
        output += f"Proprietor: {tavern['proprietor']['name']}\n"
        output += f"Atmosphere: {tavern['atmosphere']}\n\n"
        output += "Features:\n"
        for f in tavern['special_features']:
            output += f"  • {f}\n"
        
        self.utils_output.delete(1.0, "end")
        self.utils_output.insert("end", output)
    
    def generate_trap(self):
        """Generate trap."""
        from gm_utilities import TrapGenerator
        
        gen = TrapGenerator()
        trap = gen.generate_trap(level=3)
        
        output = f"=== {trap['name']} ===\n"
        output += f"Location: {trap['location']}\n"
        output += f"Trigger: {trap['trigger']}\n"
        output += f"Perception DC: {trap['perception_dc']}\n"
        output += f"Disable DC: {trap['disable_dc']}\n"
        output += f"Damage: {trap['damage']}\n"
        
        self.utils_output.delete(1.0, "end")
        self.utils_output.insert("end", output)
    
    def generate_riddle(self):
        """Generate riddle."""
        from gm_utilities import PuzzleGenerator
        
        gen = PuzzleGenerator()
        riddle = gen.generate_riddle()
        
        output = f"Riddle:\n  {riddle['riddle']}\n\n"
        output += f"Answer: {riddle['answer']}\n"
        
        self.utils_output.delete(1.0, "end")
        self.utils_output.insert("end", output)
    
    def generate_villain(self):
        """Generate villain."""
        from gm_utilities import VillainBuilder
        
        gen = VillainBuilder()
        villain = gen.generate_villain(cr=5)
        
        output = f"=== {villain['name']} ===\n"
        output += f"Archetype: {villain['archetype']}\n"
        output += f"Motivation: {villain['motivation']}\n"
        output += f"Goal: {villain['goal']}\n\n"
        output += f"Lair: {villain['lair']['type']}\n"
        output += f"Minions: {villain['minions']['count']} {villain['minions']['type']}\n"
        output += f"Scheme: {villain['scheme']}\n"
        output += f"Weakness: {villain['weakness']}\n"
        
        self.utils_output.delete(1.0, "end")
        self.utils_output.insert("end", output)
    
    def show_stats(self):
        """Show database stats."""
        stats = self.db.get_global_stats()
        
        output = "=== Database Statistics ===\n\n"
        for table, count in stats.items():
            output += f"{table}: {count}\n"
        
        self.utils_output.delete(1.0, "end")
        self.utils_output.insert("end", output)


def main():
    """Main entry point."""
    app = GUIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
