import tkinter as tk
from tkinter import messagebox, simpledialog, font
import random
from collections import namedtuple, defaultdict, Counter

# --- 既存のゲームロジック (クラス、定数、データ構造) ---
# (変更なし)

Item = namedtuple("Item", ["name", "description", "effect"])
MapCell = namedtuple("MapCell", ["description", "item", "monster"])

MAP_WIDTH = 5
MAP_HEIGHT = 5
INITIAL_PLAYER_HP = 30
INITIAL_PLAYER_ATK = 5
NUM_TREASURES = 5
NUM_MONSTERS = 3

ITEMS = {
    "ポーション": Item("ポーション", "HPを10回復する。", 10),
    "すごいポーション": Item("すごいポーション", "HPを20回復する。", 20),
    "毒キノコ": Item("毒キノコ", "食べるとHPが5減る。", -5),
    "伝説のオーブ": Item("伝説のオーブ", "まばゆい光を放つ。これが目的の品だ！", 0)
}

MONSTER_TYPES = [
    ("スライム", 10, 3),
    ("ゴブリン", 15, 5),
    ("スケルトン", 12, 4)
]

class Player:
    def __init__(self, x, y, hp, atk):
        self.x = x
        self.y = y
        self.hp = hp
        self.atk = atk
        self.inventory = Counter()
        self.max_hp = hp

    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            self.x, self.y = new_x, new_y
            return True, f"({self.x}, {self.y}) へ移動した。"
        else:
            return False, "壁だ！そちらへは移動できない。"

    def attack(self, monster):
        damage = random.randint(self.atk // 2, self.atk)
        log_msg = f"プレイヤーの攻撃！ {monster.name} に {damage} のダメージ！\n"
        monster.hp -= damage
        if monster.hp <= 0:
            log_msg += f"{monster.name} を倒した！"
            return True, log_msg
        else:
            log_msg += f"{monster.name} の残りHP: {monster.hp}"
            return False, log_msg

    def use_item(self, item_name):
        if self.inventory[item_name] > 0:
            item = ITEMS.get(item_name)
            if item:
                log_msg = f"{item.name} を使った。{item.description}\n"
                self.hp += item.effect
                if self.hp > self.max_hp: self.hp = self.max_hp
                if item.effect < 0: log_msg += f"HPが {abs(item.effect)} 減った...\n"
                log_msg += f"現在のHP: {self.hp}"
                self.inventory[item_name] -= 1
                if self.inventory[item_name] == 0:
                    del self.inventory[item_name]
                return True, log_msg
            else:
                return False, "そんなアイテムは存在しないようだ..."
        else:
            return False, f"{item_name} は持っていない。"

    def pickup_item(self, item):
        log_msg = f"{item.name} を拾った！ ({item.description})"
        self.inventory[item.name] += 1
        return log_msg

    def is_alive(self):
        return self.hp > 0

class Monster:
    def __init__(self, name, hp, atk, x, y):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.x = x
        self.y = y

    def attack(self, player):
        damage = random.randint(self.atk // 2, self.atk)
        log_msg = f"{self.name} の攻撃！ プレイヤーに {damage} のダメージ！\n"
        player.hp -= damage
        log_msg += f"プレイヤーの残りHP: {player.hp}"
        return log_msg

    def is_alive(self):
        return self.hp > 0

# --- GUI アプリケーションクラス ---

class TreasureHunterGUI:
    CELL_SIZE = 60
    COLOR_BG = "#2c3e50"
    COLOR_WALL = "#34495e"
    COLOR_FLOOR = "#95a5a6"
    COLOR_PLAYER = "#3498db"
    COLOR_TREASURE = "#f1c40f"
    COLOR_MONSTER = "#e74c3c"
    COLOR_ORB = "#9b59b6"
    COLOR_TEXT = "#ecf0f1"

    def __init__(self, root):
        self.root = root
        self.root.title("コレクト・トレジャーハンター GUI")
        self.root.configure(bg=self.COLOR_BG)

        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10)
        self.title_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.map_font = font.Font(family="Arial", size=16, weight="bold")

        self.player = None
        self.game_map = None
        self.monsters = None
        self.current_monster = None
        self.game_over = False

        self.main_frame = tk.Frame(root, bg=self.COLOR_BG, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.map_frame = tk.Frame(self.main_frame, bg=self.COLOR_BG)
        self.map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.canvas = tk.Canvas(self.map_frame,
                               width=MAP_WIDTH * self.CELL_SIZE,
                               height=MAP_HEIGHT * self.CELL_SIZE,
                               bg=self.COLOR_WALL,
                               highlightthickness=0)
        self.canvas.pack(pady=(0, 10))
        self.map_cells_gui = {}

        self.info_frame = tk.Frame(self.main_frame, bg=self.COLOR_BG)
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # プレイヤー情報 (padyの指定を修正)
        tk.Label(self.info_frame, text="プレイヤー情報", font=self.title_font, fg=self.COLOR_TEXT, bg=self.COLOR_BG).pack(pady=5)
        self.hp_label = tk.Label(self.info_frame, text="HP: -/-", fg=self.COLOR_TEXT, bg=self.COLOR_BG, justify=tk.LEFT)
        self.hp_label.pack(anchor=tk.W)
        self.atk_label = tk.Label(self.info_frame, text="ATK: -", fg=self.COLOR_TEXT, bg=self.COLOR_BG, justify=tk.LEFT)
        self.atk_label.pack(anchor=tk.W)
        # ----- 修正箇所 -----
        tk.Label(self.info_frame, text="持ち物:", font=self.title_font, fg=self.COLOR_TEXT, bg=self.COLOR_BG).pack(anchor=tk.W, pady=(10,0)) # pack時にpadyを指定
        # ----- 修正ここまで -----
        self.inventory_label = tk.Label(self.info_frame, text="-", wraplength=180, fg=self.COLOR_TEXT, bg=self.COLOR_BG, justify=tk.LEFT)
        self.inventory_label.pack(anchor=tk.W)

        # メッセージログ (padyの指定を修正)
        # ----- 修正箇所 -----
        tk.Label(self.info_frame, text="メッセージ", font=self.title_font, fg=self.COLOR_TEXT, bg=self.COLOR_BG).pack(anchor=tk.W, pady=(15,5)) # pack時にpadyを指定
        # ----- 修正ここまで -----
        self.message_label = tk.Label(self.info_frame, text="ゲーム開始！", height=6, wraplength=180, fg=self.COLOR_TEXT, bg=self.COLOR_BG, justify=tk.LEFT, anchor=tk.NW, relief=tk.SUNKEN, bd=1)
        self.message_label.pack(fill=tk.X)

        # 操作ボタン (移動)
        self.control_frame = tk.Frame(self.info_frame, bg=self.COLOR_BG)
        self.control_frame.pack(pady=15)
        tk.Button(self.control_frame, text="↑", command=lambda: self.handle_move(0, -1), width=3).grid(row=0, column=1)
        tk.Button(self.control_frame, text="←", command=lambda: self.handle_move(-1, 0), width=3).grid(row=1, column=0)
        tk.Button(self.control_frame, text="→", command=lambda: self.handle_move(1, 0), width=3).grid(row=1, column=2)
        tk.Button(self.control_frame, text="↓", command=lambda: self.handle_move(0, 1), width=3).grid(row=2, column=1)

        # 操作ボタン (アクション)
        self.action_frame = tk.Frame(self.info_frame, bg=self.COLOR_BG)
        self.action_frame.pack(pady=5)
        self.item_button = tk.Button(self.action_frame, text="アイテム使用", command=self.handle_use_item)
        self.item_button.pack(fill=tk.X)

        # 戦闘用ボタン
        self.combat_frame = tk.Frame(self.info_frame, bg=self.COLOR_BG)
        self.attack_button = tk.Button(self.combat_frame, text="たたかう", command=self.handle_attack)
        self.attack_button.pack(side=tk.LEFT, padx=5)
        self.run_button = tk.Button(self.combat_frame, text="にげる", command=self.handle_run)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.setup_game()
        self.draw_map()
        self.update_display()

    def setup_game(self):
        # (変更なし)
        self.game_map = defaultdict(lambda: MapCell("何もない空間だ。", None, None))
        self.monsters = []
        occupied_coords = set()

        player_start_x, player_start_y = 0, 0
        self.player = Player(player_start_x, player_start_y, INITIAL_PLAYER_HP, INITIAL_PLAYER_ATK)
        occupied_coords.add((player_start_x, player_start_y))
        self.game_map[(player_start_x, player_start_y)] = MapCell("冒険の始まりの場所だ。", None, None)

        def get_random_coords(exclude_coords):
            while True:
                x = random.randint(0, MAP_WIDTH - 1)
                y = random.randint(0, MAP_HEIGHT - 1)
                coord = (x, y)
                if coord != exclude_coords and coord not in occupied_coords:
                    return coord

        available_items = [name for name in ITEMS if name != "伝説のオーブ"]
        for _ in range(NUM_TREASURES):
            coord = get_random_coords((player_start_x, player_start_y))
            item_name = random.choice(available_items)
            self.game_map[coord] = MapCell("宝箱がある！", ITEMS[item_name], None)
            occupied_coords.add(coord)

        for _ in range(NUM_MONSTERS):
            coord = get_random_coords((player_start_x, player_start_y))
            monster_type = random.choice(MONSTER_TYPES)
            monster = Monster(monster_type[0], monster_type[1], monster_type[2], coord[0], coord[1])
            self.game_map[coord] = MapCell(f"{monster.name} が待ち構えている！", None, monster)
            self.monsters.append(monster)
            occupied_coords.add(coord)

        while True:
           orb_coord = get_random_coords((player_start_x, player_start_y))
           if abs(orb_coord[0] - player_start_x) + abs(orb_coord[1] - player_start_y) > (MAP_WIDTH + MAP_HEIGHT) // 3:
               break
        self.game_map[orb_coord] = MapCell("祭壇があり、まばゆい光を放つオーブが置かれている！", ITEMS["伝説のオーブ"], None)
        occupied_coords.add(orb_coord)

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if (x, y) not in occupied_coords:
                     self.game_map[(x, y)] = MapCell("何もない空間だ。", None, None)

        self.game_over = False
        self.current_monster = None
        self.log_message("洞窟を探検し、伝説のオーブを見つけよう！")


    def draw_map(self):
        # (変更なし)
        self.canvas.delete("all")
        self.map_cells_gui.clear()

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                cell_x1 = x * self.CELL_SIZE
                cell_y1 = y * self.CELL_SIZE
                cell_x2 = cell_x1 + self.CELL_SIZE
                cell_y2 = cell_y1 + self.CELL_SIZE
                coord = (x, y)
                map_cell_data = self.game_map[coord]

                fill_color = self.COLOR_WALL
                text_char = ""
                text_color = self.COLOR_TEXT

                if map_cell_data.item:
                    fill_color = self.COLOR_TREASURE
                    text_char = "T"
                elif map_cell_data.monster and map_cell_data.monster.is_alive():
                    fill_color = self.COLOR_MONSTER
                    text_char = "M"
                elif map_cell_data.description != "何もない空間だ。":
                     fill_color = self.COLOR_FLOOR
                else:
                     fill_color = self.COLOR_FLOOR

                if self.player and self.player.x == x and self.player.y == y:
                    fill_color = self.COLOR_PLAYER
                    text_char = "P"

                rect_id = self.canvas.create_rectangle(cell_x1, cell_y1, cell_x2, cell_y2, fill=fill_color, outline="#bdc3c7")
                text_id = self.canvas.create_text(cell_x1 + self.CELL_SIZE / 2,
                                                 cell_y1 + self.CELL_SIZE / 2,
                                                 text=text_char, fill=text_color, font=self.map_font)
                self.map_cells_gui[coord] = (rect_id, text_id)

    def update_display(self):
        # (変更なし)
        if not self.player: return

        self.hp_label.config(text=f"HP: {self.player.hp}/{self.player.max_hp}")
        self.atk_label.config(text=f"ATK: {self.player.atk}")
        inv_text = "\n".join([f"- {name}: {count}" for name, count in self.player.inventory.items()])
        if not inv_text: inv_text = "何も持っていない"
        self.inventory_label.config(text=inv_text)

        self.draw_map()

        if not self.player.is_alive():
            self.handle_game_over("あなたは力尽きてしまった...")
        elif self.game_over:
            pass

        current_cell = self.game_map[(self.player.x, self.player.y)]
        if current_cell.monster and current_cell.monster.is_alive() and not self.game_over:
            self.current_monster = current_cell.monster
            # 戦闘開始時は既存のログに追加
            self.log_message(f"\n{self.current_monster.name}(HP:{self.current_monster.hp}) と戦闘！")
            self.show_combat_buttons(True)
        else:
            # 戦闘中でなければ、現在地の説明を表示（上書き）
            if not self.game_over and not self.current_monster:
                 self.log_message(current_cell.description, add_log=False)
            # 戦闘が終わったらボタンを隠す
            if self.current_monster is None:
                 self.show_combat_buttons(False)


        state = tk.DISABLED if self.game_over or self.current_monster else tk.NORMAL
        for child in self.control_frame.winfo_children():
             child.config(state=state)
        self.item_button.config(state=tk.NORMAL if not self.game_over else tk.DISABLED)

    def log_message(self, msg, add_log=True):
        # (変更なし)
        if add_log:
            current_log = self.message_label.cget("text")
            log_lines = current_log.split('\n')
            if len(log_lines) > 4:
                log_lines = log_lines[-4:]
            new_log = "\n".join(log_lines) + "\n" + msg
            self.message_label.config(text=new_log.strip())
        else:
             self.message_label.config(text=msg)

    def show_combat_buttons(self, show):
        # (変更なし)
        if show:
            self.combat_frame.pack(pady=5)
        else:
            self.combat_frame.pack_forget()

    # --- イベントハンドラ ---

    def handle_move(self, dx, dy):
        # (変更なし)
        if self.game_over or self.current_monster: return

        moved, msg = self.player.move(dx, dy)
        # 移動メッセージはログに追加せず、update_displayでセル情報が表示されるようにする
        # self.log_message(msg) # 移動メッセージは必須ではないのでコメントアウトしても良い

        if moved:
            current_coord = (self.player.x, self.player.y)
            cell = self.game_map[current_coord]

            if cell.item:
                item = cell.item
                pickup_msg = self.player.pickup_item(item)
                self.log_message(pickup_msg)
                self.game_map[current_coord] = cell._replace(item=None, description="空っぽの宝箱がある。")

                if item.name == "伝説のオーブ":
                    self.handle_game_over("伝説のオーブを手に入れた！ あなたの勝利だ！", win=True)
                    return

            self.update_display()
        else:
            # 移動失敗時のみメッセージ表示
            self.log_message(msg, add_log=False)


    def handle_use_item(self):
        # (変更なし)
        if self.game_over: return
        if not self.player.inventory:
            messagebox.showinfo("アイテム", "何も持っていません。")
            return

        item_name = simpledialog.askstring("アイテム使用", "どのアイテムを使いますか？\n" + "\n".join([f"- {name}: {count}" for name, count in self.player.inventory.items()]))

        if item_name:
            used, msg = self.player.use_item(item_name)
            self.log_message(msg)
            if used:
                self.update_display()

    def handle_attack(self):
        # (ログメッセージ処理を微調整)
        if not self.current_monster or self.game_over: return

        # 攻撃前に現在のセル情報を表示しておく
        cell_desc = self.game_map[(self.player.x, self.player.y)].description
        self.log_message(f"{cell_desc}\n--------------------", add_log=False) # 戦闘ログの前に区切り

        defeated, player_attack_msg = self.player.attack(self.current_monster)
        self.log_message(player_attack_msg) # プレイヤー攻撃ログを追加

        if defeated:
            coord = (self.current_monster.x, self.current_monster.y)
            cell = self.game_map[coord]
            self.game_map[coord] = cell._replace(monster=None, description=f"{self.current_monster.name}の残骸が転がっている。")
            # self.monsters.remove(self.current_monster) # リストからの削除は必須ではない
            self.current_monster = None # 戦闘終了
            self.update_display()
        else:
            monster_attack_msg = self.current_monster.attack(self.player)
            self.log_message(monster_attack_msg) # モンスター攻撃ログを追加
            self.update_display()


    def handle_run(self):
        # (ログメッセージ処理を微調整)
        if not self.current_monster or self.game_over: return

        cell_desc = self.game_map[(self.player.x, self.player.y)].description
        self.log_message(f"{cell_desc}\n--------------------", add_log=False) # ログの前に区切り

        if random.random() < 0.5:
            self.log_message("うまく逃げ出した！")
            self.current_monster = None
            self.update_display()
        else:
            self.log_message("逃げきれなかった！")
            monster_attack_msg = self.current_monster.attack(self.player)
            self.log_message(monster_attack_msg)
            self.update_display()


    def handle_game_over(self, message, win=False):
        # (変更なし)
        self.game_over = True
        self.log_message(message, add_log=False)
        self.show_combat_buttons(False)
        for child in self.control_frame.winfo_children():
             child.config(state=tk.DISABLED)
        self.item_button.config(state=tk.DISABLED)
        for child in self.combat_frame.winfo_children():
             child.config(state=tk.DISABLED)

        if win:
            messagebox.showinfo("ゲームクリア！", message)
        else:
            messagebox.showerror("ゲームオーバー", message)


# --- アプリケーションの実行 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TreasureHunterGUI(root)
    root.mainloop()
