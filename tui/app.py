#!/usr/bin/env python3
"""
DnD GM Toolkit - Terminal UI Application

Main TUI application using rich and questionary for interactive terminal interface.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
    from rich.menu import Menu
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
except ImportError:
    print("=" * 60)
    print("ERROR: Missing required packages for TUI mode")
    print("=" * 60)
    print()
    print("To use the Terminal UI, install the required packages:")
    print()
    print("  pip install rich questionary")
    print()
    print("Or install all optional dependencies:")
    print("  pip install -r requirements.txt")
    print()
    print("=" * 60)
    sys.exit(1)

from core.db_manager import DatabaseManager
from ai.campaign_memory import CampaignMemory
from ai.linear_generator import LinearContentGenerator
from ai.choice_engine import ChoiceEngine

console = Console()


class TUIApp:
    """Terminal UI Application for GM Toolkit."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.memory = CampaignMemory()
        self.current_campaign = None
        self.running = True
    
    def run(self):
        """Main application loop."""
        self.clear_screen()
        self.show_banner()
        
        while self.running:
            self.main_menu()
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Show application banner."""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║           DnD GM TOOLKIT - Terminal Interface             ║
║                    Version 3.0                             ║
╠═══════════════════════════════════════════════════════════╣
║  Generate content • Track campaigns • AI assistance       ║
╚═══════════════════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="bold magenta"))
        console.print()
    
    def main_menu(self):
        """Display main menu."""
        console.print("\n[bold cyan]Main Menu[/bold cyan]\n")
        
        menu_items = [
            ("1", "📁 Campaigns", self.campaign_menu),
            ("2", "🎲 Generate Content", self.generate_menu),
            ("3", "📊 Trackers", self.tracker_menu),
            ("4", "🤖 AI Tools", self.ai_menu),
            ("5", "🛠️ Utilities", self.utility_menu),
            ("0", "🚪 Exit", self.exit_app),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Option", style="cyan")
        
        for key, label, _ in menu_items:
            table.add_row(f"[{key}]", label)
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask("Select option", default="1", choices=[str(i) for i in range(len(menu_items))])
        
        for key, _, action in menu_items:
            if choice == key:
                action()
                break
    
    def campaign_menu(self):
        """Campaign management menu."""
        while True:
            self.clear_screen()
            console.print(Panel("[bold cyan]Campaign Management[/bold cyan]"))
            
            campaigns = self.db.list_campaigns()
            
            if campaigns:
                table = Table(title="Your Campaigns")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bold")
                table.add_column("Last Played")
                table.add_column("Sessions")
                
                for camp in campaigns:
                    stats = self.db.get_campaign_stats(camp['id'])
                    table.add_row(
                        str(camp['id']),
                        camp['name'],
                        camp.get('last_played', 'Never')[:10] if camp.get('last_played') else 'Never',
                        str(stats['sessions'])
                    )
                
                console.print(table)
            
            console.print("\n[1] New Campaign  [2] Select Campaign  [3] Delete  [0] Back")
            choice = Prompt.ask("Select", default="0", choices=["0", "1", "2", "3"])
            
            if choice == "0":
                break
            elif choice == "1":
                self.create_campaign()
            elif choice == "2" and campaigns:
                self.select_campaign()
            elif choice == "3" and campaigns:
                self.delete_campaign()
    
    def create_campaign(self):
        """Create a new campaign."""
        console.print("\n[bold]Create New Campaign[/bold]\n")
        
        name = Prompt.ask("Campaign name")
        description = Prompt.ask("Description (optional)", default="")
        
        campaign_id = self.db.create_campaign(name, description)
        console.print(f"\n[green]✓ Campaign '{name}' created (ID: {campaign_id})[/green]\n")
        Prompt.ask("Press Enter to continue")
    
    def select_campaign(self):
        """Select a campaign to work with."""
        campaign_id = IntPrompt.ask("Enter campaign ID")
        campaign = self.db.get_campaign(campaign_id=campaign_id)
        
        if campaign:
            self.current_campaign = campaign
            self.memory.set_campaign_name(campaign['name'])
            console.print(f"\n[green]✓ Selected: {campaign['name']}[/green]\n")
            
            # Show campaign stats
            stats = self.db.get_campaign_stats(campaign_id)
            console.print("[dim]Sessions: {} | Characters: {} | NPCs: {} | Active Threads: {}[/dim]\n".format(
                stats['sessions'], stats['characters'], stats['npcs'], stats['active_threads']
            ))
            Prompt.ask("Press Enter to continue")
        else:
            console.print("\n[red]Campaign not found[/red]\n")
            Prompt.ask("Press Enter to continue")
    
    def delete_campaign(self):
        """Delete a campaign."""
        campaign_id = IntPrompt.ask("Enter campaign ID to delete")
        
        if Confirm.ask(f"Are you sure? This will delete all data!"):
            if self.db.delete_campaign(campaign_id):
                console.print(f"\n[green]✓ Campaign deleted[/green]\n")
            else:
                console.print("\n[red]Failed to delete campaign[/red]\n")
        
        Prompt.ask("Press Enter to continue")
    
    def generate_menu(self):
        """Content generation menu."""
        console.print("\n[bold cyan]Generate Content[/bold cyan]\n")
        
        menu_items = [
            ("1", "⚔️ Encounter", lambda: self.generate_encounter()),
            ("2", "💰 Loot/Treasure", lambda: self.generate_loot()),
            ("3", "👤 NPC", lambda: self.generate_npc()),
            ("4", "📜 Quest (AI Linear)", lambda: self.generate_quest()),
            ("5", "🏰 Dungeon", lambda: self.generate_dungeon()),
            ("0", "Back", lambda: None),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Option", style="cyan")
        
        for key, label, _ in menu_items:
            table.add_row(f"[{key}]", label)
        
        console.print(table)
        
        choice = Prompt.ask("Select", default="0", choices=[str(i) for i in range(len(menu_items))])
        
        for key, _, action in menu_items:
            if choice == key:
                action()
                break
    
    def generate_encounter(self):
        """Generate an encounter."""
        from generators.encounter_gen import EncounterGenerator
        
        console.print("\n[bold]Generate Encounter[/bold]\n")
        
        terrain = Prompt.ask("Terrain", default="forest", 
                            choices=["forest", "dungeon", "mountain", "plains", "swamp", "desert", "any"])
        difficulty = Prompt.ask("Difficulty", default="medium",
                               choices=["easy", "medium", "hard", "deadly"])
        party_level = IntPrompt.ask("Party level", default=5)
        party_size = IntPrompt.ask("Party size", default=4)
        
        gen = EncounterGenerator()
        encounter = gen.generate_encounter(
            difficulty=difficulty,
            terrain=terrain,
            party_level=party_level,
            party_size=party_size
        )
        
        # Display encounter
        console.print(f"\n[bold]{difficulty.capitalize()} Encounter - {terrain}[/bold]")
        console.print(f"XP Budget: {encounter['xp_budget']} | Adjusted XP: {encounter['adjusted_xp']}\n")
        
        table = Table(title="Monsters")
        table.add_column("Count", style="yellow")
        table.add_column("Name", style="bold")
        table.add_column("CR")
        table.add_column("AC")
        table.add_column("HP")
        
        for monster in encounter['monsters']:
            table.add_row(
                str(monster.get('count', 1)),
                monster['name'],
                str(monster['cr']),
                str(monster.get('ac', 10)),
                str(monster.get('hp', 10))
            )
        
        console.print(table)
        
        # Save to library if campaign selected
        if self.current_campaign and Confirm.ask("\nSave to campaign library?", default=False):
            self.db.save_to_library(
                campaign_id=self.current_campaign['id'],
                content_type="encounter",
                title=f"{terrain.capitalize()} {difficulty.capitalize()} Encounter",
                data=encounter,
                theme=terrain,
                difficulty=difficulty
            )
            console.print("[green]✓ Saved to library[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_loot(self):
        """Generate loot."""
        from generators.loot_gen import LootGenerator
        
        console.print("\n[bold]Generate Loot[/bold]\n")
        
        gen_type = Prompt.ask("Type", default="item", choices=["item", "hoard"])
        
        gen = LootGenerator()
        
        if gen_type == "hoard":
            party_level = IntPrompt.ask("Party level", default=5)
            party_size = IntPrompt.ask("Party size", default=4)
            hoard = gen.generate_hoard(party_level=party_level, party_size=party_size)
            
            console.print(f"\n[bold]Treasure Hoard[/bold]")
            console.print(f"Gold: {hoard['gold_pieces']} gp")
            console.print(f"Gems: {hoard['gems']['count']} (worth {hoard['gems']['total_value']} gp)")
            console.print(f"Art: {hoard['art_objects']['count']} (worth {hoard['art_objects']['total_value']} gp)")
            console.print(f"Magic Items: {len(hoard['magic_items'])}")
            console.print(f"[bold]Total Value: {hoard['total_value']} gp[/bold]")
        else:
            rarity = Prompt.ask("Rarity", default="uncommon",
                               choices=["common", "uncommon", "rare", "very rare", "legendary"])
            item = gen.generate_magic_item(rarity=rarity)
            
            console.print(f"\n[bold]{item['name']}[/bold]")
            console.print(f"Rarity: {item['rarity']}")
            console.print(f"Type: {item['type']}")
            console.print(f"Property: {item['property']}")
            console.print(f"Value: {item.get('gold_value', 0)} gp")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_npc(self):
        """Generate an NPC."""
        from generators.npc_gen import NPCGenerator
        
        console.print("\n[bold]Generate NPC[/bold]\n")
        
        race = Prompt.ask("Race", default="human",
                         choices=["human", "elf", "dwarf", "halfling", "orc", "tiefling", "any"])
        
        gen = NPCGenerator()
        npc = gen.generate_npc(race=race if race != "any" else "human")
        
        # Display NPC
        console.print(f"\n[bold]{npc['identity']['name']}[/bold]")
        console.print(f"{npc['identity']['race']} {npc['identity']['class']} (Level {npc['identity']['level']})")
        console.print(f"Background: {npc['identity']['background']}")
        console.print(f"Alignment: {npc['identity']['alignment']}")
        
        if 'stat_block' in npc:
            sb = npc['stat_block']
            console.print(f"\n[dim]AC: {sb['armor_class']} | HP: {sb['hit_points']}[/dim]")
        
        console.print(f"\n[italic]{npc.get('description', '')}[/italic]")
        
        # Save to campaign if selected
        if self.current_campaign and Confirm.ask("\nSave to campaign NPCs?", default=False):
            self.db.create_npc(
                campaign_id=self.current_campaign['id'],
                name=npc['identity']['name'],
                race=npc['identity']['race'],
                char_class=npc['identity']['class'],
                description=npc.get('description', '')
            )
            console.print("[green]✓ NPC saved to campaign[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_quest(self):
        """Generate AI linear quest."""
        console.print("\n[bold]Generate AI Linear Quest[/bold]\n")
        console.print("[dim]Beginner-friendly progressive quest structure[/dim]\n")
        
        theme = Prompt.ask("Theme", default="rescue",
                          choices=["rescue", "hunt", "retrieve", "dungeon"])
        party_level = IntPrompt.ask("Party level", default=1)
        num_stages = IntPrompt.ask("Number of stages (3-8)", default=5)
        num_stages = max(3, min(8, num_stages))
        
        gen = LinearContentGenerator()
        quest = gen.generate_quest(theme=theme, party_level=party_level, num_stages=num_stages)
        
        # Display quest
        console.print(f"\n[bold]{quest.title}[/bold]")
        console.print(f"Theme: {quest.theme} | Levels: {quest.party_level_range[0]}-{quest.party_level_range[1]}")
        
        table = Table(title="Quest Progression")
        table.add_column("Stage", style="yellow")
        table.add_column("Name", style="bold")
        table.add_column("Difficulty")
        table.add_column("Description")
        
        for stage in quest.stages:
            diff_color = {
                "tutorial": "green",
                "easy": "light_green",
                "moderate": "yellow",
                "challenging": "orange",
                "boss": "red"
            }.get(stage.difficulty, "white")
            
            table.add_row(
                str(stage.stage_number),
                stage.name,
                f"[{diff_color}]{stage.difficulty}[/{diff_color}]",
                stage.description[:40] + "..." if len(stage.description) > 40 else stage.description
            )
        
        console.print(table)
        
        # Show choices for first stage
        if quest.stages and quest.stages[0].choices:
            console.print("\n[bold]Starting Choices:[/bold]")
            choice = quest.stages[0].choices[0]
            console.print(f"  {choice['question']}")
            for i, opt in enumerate(choice['options'], 1):
                console.print(f"    {i}. {opt['text']}")
        
        # Save to campaign
        if self.current_campaign and Confirm.ask("\nSave quest to campaign?", default=False):
            self.db.save_to_library(
                campaign_id=self.current_campaign['id'],
                content_type="quest",
                title=quest.title,
                data=quest.to_dict(),
                theme=theme,
                tags=["linear", "progressive"]
            )
            console.print("[green]✓ Quest saved[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_dungeon(self):
        """Generate a dungeon."""
        from dungeon_generator import DungeonGenerator
        
        console.print("\n[bold]Generate Dungeon[/bold]\n")
        
        theme = Prompt.ask("Theme", default="crypt",
                          choices=["crypt", "cave", "castle", "ruins", "mine", "temple"])
        levels = IntPrompt.ask("Number of levels", default=3)
        
        gen = DungeonGenerator()
        dungeon = gen.generate_dungeon(name=f"The {theme.title()}", theme=theme, levels=levels)
        
        console.print(f"\n[bold]{dungeon.name}[/bold]")
        console.print(f"Theme: {dungeon.theme} | Levels: {dungeon.total_levels}")
        console.print(f"\n[italic]{dungeon.backstory}[/italic]")
        
        console.print("\n[bold]Features:[/bold]")
        for feature in dungeon.dungeon_features:
            console.print(f"  • {feature}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def tracker_menu(self):
        """Trackers menu."""
        console.print("\n[bold cyan]Trackers[/bold cyan]\n")
        
        menu_items = [
            ("1", "📋 Sessions", lambda: self.session_tracker()),
            ("2", "👥 Characters", lambda: self.character_tracker()),
            ("3", "🎭 Plot Threads", lambda: self.plot_thread_tracker()),
            ("0", "Back", lambda: None),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Option", style="cyan")
        
        for key, label, _ in menu_items:
            table.add_row(f"[{key}]", label)
        
        console.print(table)
        
        choice = Prompt.ask("Select", default="0", choices=["0", "1", "2", "3"])
        
        if choice == "1":
            self.session_tracker()
        elif choice == "2":
            self.character_tracker()
        elif choice == "3":
            self.plot_thread_tracker()
    
    def session_tracker(self):
        """Session tracking."""
        if not self.current_campaign:
            console.print("\n[red]Please select a campaign first[/red]\n")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print("\n[bold]Session Tracker[/bold]\n")
        
        sessions = self.db.get_campaign_sessions(self.current_campaign['id'])
        
        if sessions:
            table = Table(title="Sessions")
            table.add_column("#", style="dim")
            table.add_column("Title")
            table.add_column("Summary")
            
            for session in sessions[-5:]:  # Last 5 sessions
                table.add_row(
                    str(session['session_number']),
                    session.get('title', 'Untitled'),
                    (session.get('summary', '')[:50] + '...') if session.get('summary') else ''
                )
            
            console.print(table)
        
        if Confirm.ask("\nStart new session?", default=False):
            session_num = len(sessions) + 1
            title = Prompt.ask("Session title", default=f"Session {session_num}")
            
            self.db.create_session(
                campaign_id=self.current_campaign['id'],
                session_number=session_num,
                title=title
            )
            
            self.memory.start_session(session_num, title)
            console.print(f"[green]✓ Session {session_num} started[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def character_tracker(self):
        """Character tracking."""
        if not self.current_campaign:
            console.print("\n[red]Please select a campaign first[/red]\n")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print("\n[bold]Character Tracker[/bold]\n")
        
        characters = self.db.get_campaign_characters(self.current_campaign['id'])
        
        if characters:
            table = Table(title="Characters")
            table.add_column("Name", style="bold")
            table.add_column("Player")
            table.add_column("Class")
            table.add_column("Level")
            table.add_column("HP")
            
            for char in characters:
                hp = f"{char.get('hp_current', 0)}/{char.get('hp_max', 0)}"
                table.add_row(
                    char['name'],
                    char.get('player_name', '-'),
                    char.get('char_class', '-'),
                    str(char.get('level', 1)),
                    hp
                )
            
            console.print(table)
        else:
            console.print("[dim]No characters yet[/dim]")
        
        if Confirm.ask("\nAdd new character?", default=False):
            name = Prompt.ask("Character name")
            player = Prompt.ask("Player name")
            char_class = Prompt.ask("Class", default="Fighter")
            race = Prompt.ask("Race", default="Human")
            level = IntPrompt.ask("Level", default=1)
            hp_max = IntPrompt.ask("Max HP", default=10)
            
            self.db.create_character(
                campaign_id=self.current_campaign['id'],
                name=name,
                player_name=player,
                char_class=char_class,
                race=race,
                level=level,
                hp_max=hp_max
            )
            console.print("[green]✓ Character added[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def plot_thread_tracker(self):
        """Plot thread tracking."""
        if not self.current_campaign:
            console.print("\n[red]Please select a campaign first[/red]\n")
            Prompt.ask("Press Enter to continue")
            return
        
        console.print("\n[bold]Plot Threads[/bold]\n")
        
        threads = self.db.get_campaign_plot_threads(self.current_campaign['id'])
        
        if threads:
            table = Table(title="Plot Threads")
            table.add_column("Title", style="bold")
            table.add_column("Status")
            table.add_column("Priority")
            table.add_column("Description")
            
            for thread in threads:
                status_color = "green" if thread['status'] == 'resolved' else "yellow"
                table.add_row(
                    thread['title'],
                    f"[{status_color}]{thread['status']}[/{status_color}]",
                    thread.get('priority', 'normal'),
                    (thread.get('description', '')[:40] + '...') if thread.get('description') else ''
                )
            
            console.print(table)
        else:
            console.print("[dim]No plot threads yet[/dim]")
        
        if Confirm.ask("\nAdd new plot thread?", default=False):
            title = Prompt.ask("Thread title")
            description = Prompt.ask("Description", default="")
            
            self.db.create_plot_thread(
                campaign_id=self.current_campaign['id'],
                title=title,
                description=description
            )
            console.print("[green]✓ Plot thread added[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def ai_menu(self):
        """AI tools menu."""
        console.print("\n[bold cyan]AI Tools[/bold cyan]\n")
        console.print("[dim]Pattern-based content generation and campaign memory[/dim]\n")
        
        menu_items = [
            ("1", "🧠 Training Status", lambda: self.show_ai_status()),
            ("2", "📚 Train on Content", lambda: self.train_ai()),
            ("3", "💬 Story Choices", lambda: self.generate_choices()),
            ("0", "Back", lambda: None),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Option", style="cyan")
        
        for key, label, _ in menu_items:
            table.add_row(f"[{key}]", label)
        
        console.print(table)
        
        choice = Prompt.ask("Select", default="0", choices=["0", "1", "2", "3"])
        
        if choice == "1":
            self.show_ai_status()
        elif choice == "2":
            self.train_ai()
        elif choice == "3":
            self.generate_choices()
    
    def show_ai_status(self):
        """Show AI training status."""
        from ai.ai_trainer import AITrainer
        
        trainer = AITrainer()
        status = trainer.get_training_status()
        
        console.print("\n[bold]AI Training Status[/bold]\n")
        console.print(f"Content processed: {status.get('content_processed', 0)}")
        console.print(f"Patterns learned: {status.get('patterns_learned', 0)}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def train_ai(self):
        """Train AI on content."""
        from ai.ai_trainer import AITrainer
        
        console.print("\n[bold]Training AI...[/bold]\n")
        
        trainer = AITrainer()
        stats = trainer.train_on_all_content()
        
        console.print("[bold]Training Complete[/bold]\n")
        for key, value in stats.items():
            console.print(f"  {key}: {value}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_choices(self):
        """Generate story choices."""
        console.print("\n[bold]Story Choices Generator[/bold]\n")
        
        situation = Prompt.ask("Situation", default="conflict",
                              choices=["approach", "conflict", "mystery", "travel", "treasure", "npc_interaction"])
        
        engine = ChoiceEngine()
        choice = engine.generate_choices(situation)
        
        console.print(f"\n[bold]{choice.question}[/bold]\n")
        
        for i, opt in enumerate(choice.options, 1):
            risk = opt.get('risk', '')
            risk_indicator = {
                'low': '[green]●[/green]',
                'medium': '[yellow]●[/yellow]',
                'high': '[red]●[/red]'
            }.get(risk, '○')
            
            console.print(f"  {risk_indicator} {i}. {opt['text']}")
        
        # Get consequence for selected option
        selected = IntPrompt.ask("\nSelect option", default=1, 
                                choices=[str(i) for i in range(1, len(choice.options) + 1)])
        
        consequence = engine.get_consequence(choice, selected - 1)
        
        console.print(f"\n[bold]Consequence:[/bold]")
        console.print(f"  Immediate: {consequence.immediate_effect}")
        console.print(f"  Long-term: {consequence.long_term_effect}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def utility_menu(self):
        """Utilities menu."""
        console.print("\n[bold cyan]Utilities[/bold cyan]\n")
        
        menu_items = [
            ("1", "🏨 Tavern Generator", lambda: self.generate_tavern()),
            ("2", "🪤 Trap Generator", lambda: self.generate_trap()),
            ("3", "❓ Riddle Generator", lambda: self.generate_riddle()),
            ("4", "🦹 Villain Generator", lambda: self.generate_villain()),
            ("0", "Back", lambda: None),
        ]
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Option", style="cyan")
        
        for key, label, _ in menu_items:
            table.add_row(f"[{key}]", label)
        
        console.print(table)
        
        choice = Prompt.ask("Select", default="0", choices=["0", "1", "2", "3", "4"])
        
        if choice == "1":
            self.generate_tavern()
        elif choice == "2":
            self.generate_trap()
        elif choice == "3":
            self.generate_riddle()
        elif choice == "4":
            self.generate_villain()
    
    def generate_tavern(self):
        """Generate a tavern."""
        from gm_toolkit_extra import TavernGenerator
        
        gen = TavernGenerator()
        tavern = gen.generate_tavern()
        
        console.print(f"\n[bold]{tavern['name']}[/bold]")
        console.print(f"Proprietor: {tavern['proprietor']['name']} ({tavern['proprietor']['trait']})")
        console.print(f"Atmosphere: {tavern['atmosphere']}")
        
        console.print("\n[bold]Features:[/bold]")
        for feature in tavern['special_features']:
            console.print(f"  • {feature}")
        
        console.print("\n[bold]Current Patrons:[/bold]")
        for patron in tavern['current_patrons']:
            console.print(f"  • {patron}")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_trap(self):
        """Generate a trap."""
        from gm_utilities import TrapGenerator
        
        gen = TrapGenerator()
        trap = gen.generate_trap(level=IntPrompt.ask("Level", default=1))
        
        console.print(f"\n[bold]{trap['name']}[/bold]")
        console.print(f"Location: {trap['location']}")
        console.print(f"Trigger: {trap['trigger']}")
        console.print(f"\nPerception DC: [yellow]{trap['perception_dc']}[/yellow]")
        console.print(f"Disable DC: [yellow]{trap['disable_dc']}[/yellow]")
        console.print(f"Damage: [red]{trap['damage']}[/red]")
        console.print(f"\n[dim]Hint: {trap['hint']}[/dim]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_riddle(self):
        """Generate a riddle."""
        from gm_utilities import PuzzleGenerator
        
        gen = PuzzleGenerator()
        riddle = gen.generate_riddle()
        
        console.print(f"\n[bold]Riddle:[/bold]")
        console.print(f"  {riddle['riddle']}")
        
        if Confirm.ask("\nShow answer?", default=False):
            console.print(f"\n[green]Answer: {riddle['answer']}[/green]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def generate_villain(self):
        """Generate a villain."""
        from gm_utilities import VillainBuilder
        
        gen = VillainBuilder()
        villain = gen.generate_villain(cr=IntPrompt.ask("CR", default=5))
        
        console.print(f"\n[bold red]{villain['name']}[/bold red]")
        console.print(f"Archetype: {villain['archetype']}")
        console.print(f"Motivation: {villain['motivation']}")
        console.print(f"\n[bold]Goal:[/bold] {villain['goal']}")
        console.print(f"\n[bold]Lair:[/bold] {villain['lair']['type']}")
        console.print(f"[bold]Minions:[/bold] {villain['minions']['count']} {villain['minions']['type']}")
        console.print(f"\n[bold]Scheme:[/bold] {villain['scheme']}")
        console.print(f"[dim]Weakness: {villain['weakness']}[/dim]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def exit_app(self):
        """Exit the application."""
        if Confirm.ask("Exit GM Toolkit?", default=False):
            self.running = False
            console.print("\n[bold]Goodbye![/bold]\n")


def main():
    """Main entry point."""
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()
