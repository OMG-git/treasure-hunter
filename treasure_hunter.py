import random
from collections import namedtuple, defaultdict, Counter

# --- データ構造の定義 ---

# アイテム情報を格納する名前付きタプル
# effect は仮に回復量とする (負の値ならダメージ)
Item = namedtuple("Item", ["name", "description", "effect"])

# マップの各セルの情報を格納する名前付きタプル
MapCell = namedtuple("MapCell", ["description", "item", "monster"])

# --- 定数の定義 ---
MAP_WIDTH = 5
MAP_HEIGHT = 5
INITIAL_PLAYER_HP = 30
INITIAL_PLAYER_ATK = 5
NUM_TREASURES = 5
NUM_MONSTERS = 3

# アイテムの種類を定義
ITEMS = {
    "ポーション": Item("ポーション", "HPを10回復する。", 10),
    "すごいポーション": Item("すごいポーション", "HPを20回復する。", 20),
    "毒キノコ": Item("毒キノコ", "食べるとHPが5減る。", -5),
    "伝説のオーブ": Item("伝説のオーブ", "まばゆい光を放つ。これが目的の品だ！", 0) # ゴールアイテム
}

# モンスターの種類を定義 (名前, HP, ATK)
MONSTER_TYPES = [
    ("スライム", 10, 3),
    ("ゴブリン", 15, 5),
    ("スケルトン", 12, 4)
]

# --- クラスの定義 ---

class Player:
    """プレイヤーを表すクラス"""
    def __init__(self, x, y, hp, atk):
        self.x = x
        self.y = y
        self.hp = hp
        self.atk = atk
        # Counterで持ち物を管理
        self.inventory = Counter()
        self.max_hp = hp

    def move(self, dx, dy, game_map):
        """プレイヤーを移動させる"""
        new_x, new_y = self.x + dx, self.y + dy

        # マップ範囲内かチェック
        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            self.x, self.y = new_x, new_y
            print(f"\n({self.x}, {self.y}) へ移動した。")
            return True
        else:
            print("\n壁だ！そちらへは移動できない。")
            return False

    def attack(self, monster):
        """モンスターを攻撃する"""
        damage = random.randint(self.atk // 2, self.atk) # ダメージに少し揺らぎを
        print(f"プレイヤーの攻撃！ {monster.name} に {damage} のダメージ！")
        monster.hp -= damage
        if monster.hp <= 0:
            print(f"{monster.name} を倒した！")
            return True # 倒した
        else:
            print(f"{monster.name} の残りHP: {monster.hp}")
            return False # まだ生きている

    def use_item(self, item_name):
        """アイテムを使用する"""
        if self.inventory[item_name] > 0:
            item = ITEMS.get(item_name)
            if item:
                print(f"{item.name} を使った。{item.description}")
                self.hp += item.effect
                if self.hp > self.max_hp:
                    self.hp = self.max_hp # 最大HPを超えない
                if item.effect < 0:
                    print(f"HPが {abs(item.effect)} 減った...")
                print(f"現在のHP: {self.hp}")
                self.inventory[item_name] -= 1
                if self.inventory[item_name] == 0:
                    del self.inventory[item_name] # 個数が0になったらインベントリから削除
            else:
                print("そんなアイテムは存在しないようだ...")
        else:
            print(f"{item_name} は持っていない。")

    def pickup_item(self, item):
        """アイテムを拾う"""
        print(f"{item.name} を拾った！ ({item.description})")
        self.inventory[item.name] += 1

    def is_alive(self):
        """プレイヤーが生きているか"""
        return self.hp > 0

class Monster:
    """モンスターを表すクラス"""
    def __init__(self, name, hp, atk, x, y):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.x = x
        self.y = y

    def attack(self, player):
        """プレイヤーを攻撃する"""
        damage = random.randint(self.atk // 2, self.atk)
        print(f"{self.name} の攻撃！ プレイヤーに {damage} のダメージ！")
        player.hp -= damage
        print(f"プレイヤーの残りHP: {player.hp}")

    def is_alive(self):
        """モンスターが生きているか"""
        return self.hp > 0

# --- ゲームのセットアップ ---

def setup_game():
    """ゲームの初期設定を行う"""
    print("ようこそ『コレクト・トレジャーハンター』へ！")
    print("洞窟を探検し、「伝説のオーブ」を見つけ出そう。\n")

    # defaultdictでマップを生成。デフォルトは「何もない空間」
    game_map = defaultdict(lambda: MapCell("何もない空間だ。", None, None))

    # 開始位置 (0, 0)
    player_start_x, player_start_y = 0, 0
    player = Player(player_start_x, player_start_y, INITIAL_PLAYER_HP, INITIAL_PLAYER_ATK)

    # ランダムな座標を生成するヘルパー関数
    def get_random_coords(exclude_coords):
        while True:
            x = random.randint(0, MAP_WIDTH - 1)
            y = random.randint(0, MAP_HEIGHT - 1)
            coord = (x, y)
            if coord != exclude_coords and coord not in occupied_coords:
                return coord

    occupied_coords = set([(player_start_x, player_start_y)]) # すでに使われている座標

    # アイテムを配置 (伝説のオーブ以外)
    available_items = [name for name in ITEMS if name != "伝説のオーブ"]
    for _ in range(NUM_TREASURES):
        coord = get_random_coords((player_start_x, player_start_y))
        item_name = random.choice(available_items)
        game_map[coord] = MapCell("宝箱がある！", ITEMS[item_name], None)
        occupied_coords.add(coord)
        # print(f"DEBUG: Item {item_name} at {coord}") # デバッグ用

    # モンスターを配置
    monsters = []
    for _ in range(NUM_MONSTERS):
        coord = get_random_coords((player_start_x, player_start_y))
        monster_type = random.choice(MONSTER_TYPES)
        monster = Monster(monster_type[0], monster_type[1], monster_type[2], coord[0], coord[1])
        game_map[coord] = MapCell(f"{monster.name} が待ち構えている！", None, monster)
        monsters.append(monster) # モンスターリストにも追加
        occupied_coords.add(coord)
        # print(f"DEBUG: Monster {monster.name} at {coord}") # デバッグ用

    # 伝説のオーブを配置 (スタート地点から遠い場所に)
    while True:
       orb_coord = get_random_coords((player_start_x, player_start_y))
       # 簡単な距離計算で遠い場所を選ぶ (マンハッタン距離)
       if abs(orb_coord[0] - player_start_x) + abs(orb_coord[1] - player_start_y) > (MAP_WIDTH + MAP_HEIGHT) // 3:
           break
    game_map[orb_coord] = MapCell("祭壇があり、まばゆい光を放つオーブが置かれている！", ITEMS["伝説のオーブ"], None)
    occupied_coords.add(orb_coord)
    print(f"DEBUG: Orb at {orb_coord}") # デバッグ用

    return player, game_map, monsters

# --- ゲームループ ---

def game_loop(player, game_map, monsters):
    """メインのゲームループ"""
    while player.is_alive():
        current_coord = (player.x, player.y)
        cell = game_map[current_coord] # defaultdictなのでキーがなくてもエラーにならない

        print("-" * 20)
        print(f"現在地: ({player.x}, {player.y}) HP: {player.hp}/{player.max_hp} ATK: {player.atk}")
        print(f"持ち物: {dict(player.inventory)}") # Counterを辞書で見やすく表示
        print(f"周りの様子: {cell.description}")

        # --- 現在地のイベント処理 ---
        # アイテムがあれば拾う
        if cell.item:
            player.pickup_item(cell.item)
            # 伝説のオーブならゲームクリア
            if cell.item.name == "伝説のオーブ":
                print("\n★★★★★★★★★★★★★★★★★★★★")
                print("伝説のオーブを手に入れた！ あなたの勝利だ！")
                print("★★★★★★★★★★★★★★★★★★★★\n")
                return # ゲーム終了
            # アイテムを拾ったらセルから削除 (Noneにする)
            game_map[current_coord] = cell._replace(item=None, description="空っぽの宝箱がある。") # namedtupleは不変なので_replaceで新しいのを作る

        # モンスターがいれば戦闘
        elif cell.monster and cell.monster.is_alive():
            monster = cell.monster
            print(f"\n{monster.name}が現れた！ (HP: {monster.hp}, ATK: {monster.atk})")
            while player.is_alive() and monster.is_alive():
                action = input("戦闘！ どうする？ (たたかう[a] / アイテム[i] / にげる[r]): ").lower()
                if action == 'a':
                    # プレイヤーの攻撃
                    if player.attack(monster): # モンスターを倒したか？
                        print(f"{monster.name}のいた場所は空っぽになった。")
                        game_map[current_coord] = cell._replace(monster=None, description=f"{monster.name}の残骸が転がっている。")
                        monsters.remove(monster) # モンスターリストからも削除
                        break # 戦闘終了
                elif action == 'i':
                    item_name = input("どのアイテムを使う？ (名前を入力): ")
                    player.use_item(item_name)
                    # アイテム使用後、HPが0以下になった場合も考慮 (毒キノコなど)
                    if not player.is_alive(): break
                elif action == 'r':
                    if random.random() < 0.5: # 50%の確率で逃げる成功
                        print("うまく逃げ出した！")
                        # 移動先はランダムではなく、前の位置に戻るなどの実装が良いかも
                        # ここではシンプルに戦闘ループを抜けるだけ
                        break
                    else:
                        print("逃げきれなかった！")
                else:
                    print("有効なコマンドを入力してください。")
                    continue # 再度入力を促す

                # モンスターが生きていれば攻撃してくる
                if monster.is_alive():
                    monster.attack(player)

            # 戦闘後、プレイヤーがやられていたらループを抜ける
            if not player.is_alive():
                break

        # --- プレイヤーの行動選択 ---
        action = input("\nどうする？ (移動[w/a/s/d] / アイテム[i] / やめる[q]): ").lower()

        if action == 'w':
            player.move(0, -1, game_map)
        elif action == 's':
            player.move(0, 1, game_map)
        elif action == 'a':
            player.move(-1, 0, game_map)
        elif action == 'd':
            player.move(1, 0, game_map)
        elif action == 'i':
            item_name = input("どのアイテムを使う？ (名前を入力): ")
            player.use_item(item_name)
        elif action == 'q':
            print("冒険をあきらめた...")
            break
        else:
            print("有効なコマンドを入力してください。")

    # ループを抜けた後の処理 (ゲームオーバー)
    if not player.is_alive():
        print("\n--------------------")
        print("GAME OVER...")
        print("あなたは力尽きてしまった...")
        print("--------------------\n")

# --- ゲーム実行 ---
if __name__ == "__main__":
    player, game_map, monsters = setup_game()
    game_loop(player, game_map, monsters)