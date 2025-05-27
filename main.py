import json
import os
import random
from datetime import datetime
from pprint import pprint
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from price import PriceGetter

NUMBER = '零单双三'
plt.rcParams['font.family'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False
nicknames = {
    "swamp_planet": "沼",
    "aqua_planet": "海洋",
    "jungle_planet": "丛林",
    "gobo_planet": "哥布林",
    "planet_of_the_eyes": "眼",
    "sorcerers_tower": "法",
    "bear_with_it": "熊",
    "golem_cave": "石",
    "twilight_zone": "暮",
    "infernal_abyss": "地",
}


def get_color(key: str):
    random.seed(sum(ord(c) for c in key))
    return random.uniform(0, 0.75), random.uniform(0, 0.75), random.uniform(0, 0.75), 0.6


def get_zone_name(name, is_elite):
    name = name.split('/')[3]
    for key, value in nicknames.items():
        if name.startswith(key):
            return ("精" if is_elite else "普") + value


def get_key(name: str):
    return name[1 + name.find('普') + name.find('精'):]  # + name[0]


class Result:
    def __init__(self, simulation_name, result, price_getter, com_buff=False, ):
        self.simulation_hour = result["simulatedTime"] / 3_600_000_000_000
        self.is_elite = "_elite" in result["zoneName"]
        self.name = simulation_name + get_zone_name(result["zoneName"], self.is_elite)
        self.key = get_key(self.name)
        self.color = get_color(self.key)
        self.exp_per_hour = sum(result["experienceGained"]["player1"].values()) / self.simulation_hour / 1_000
        self.gains_per_day = sum(
            price_getter.get_enemy_price(
                enemy_hrid=enemy,
                elite_tier=1 if self.is_elite else 0,
                drop_rate_multiplier=result["dropRateMultiplier"]["player1"],
                rare_find_multiplier=result["rareFindMultiplier"]["player1"],
                com_buff_multiplier=1.295 if com_buff else 1.0
            ) * count / NUMBER.find(simulation_name[0])
            for enemy, count in result["deaths"].items() if (not enemy.startswith("player"))
        ) * 24 / self.simulation_hour / 1_000_000
        self.cost_per_day = sum(
            price_getter.get_price(
                item_hrid=item,
                mode="ask"
            ) * count
            for item, count in result["consumablesUsed"]["player1"].items()
        ) * 24 / self.simulation_hour / 1_000_000
        self.profit_per_day = self.gains_per_day - self.cost_per_day
        self.deaths_per_hour = result["deaths"].get("player1", 0) / self.simulation_hour
        self.oom = result["playerRanOutOfMana"]["player1"]

    def __repr__(self):
        return f"({self.name} | {self.exp_per_hour:.2f}, {self.profit_per_day:.2f}, {self.deaths_per_hour:.2f})"


class SimulationData:
    def __init__(self):
        self.all_data = []
        self.price_getter = PriceGetter()
        self.simulation_time = None
        self.convex_chain = None

    def add_data(self, file, com_buff=False):
        with open(file, mode='r', encoding='utf-8') as f:
            data = json.load(f)
        simulation_name = data["simulationName"].split(' ')[2]
        for res in data["results"]:
            self.all_data.append(Result(simulation_name, res, self.price_getter, com_buff))

    def wash_data(self,
                  max_deaths_per_hour=8.0,
                  superior_filter_map_only=True,
                  superior_filter=False,
                  inferior_filter=True,
                  inferior_filter_coefficient=0.8
                  ):
        self.all_data = list(filter(lambda res: res.deaths_per_hour <= max_deaths_per_hour, self.all_data))
        if superior_filter_map_only or superior_filter:
            self.all_data = list(filter(lambda res: all(
                (False if superior_filter else res.key != r.key) or
                # res.deaths_per_hour < r.deaths_per_hour or
                res.exp_per_hour > r.exp_per_hour or
                res.profit_per_day > r.profit_per_day
                for r in self.all_data if r != res
            ), self.all_data))
        if inferior_filter:
            max_xp = max(self.all_data, key=lambda res: res.exp_per_hour)
            max_profit = max(self.all_data, key=lambda res: res.profit_per_day)
            self.all_data = list(filter(lambda res:
                                        res.exp_per_hour >= max_profit.exp_per_hour * inferior_filter_coefficient and
                                        res.profit_per_day >= max_xp.profit_per_day * inferior_filter_coefficient,
                                        self.all_data))

    def find_convex_hull(self):
        now_node = max(self.all_data, key=lambda res: res.profit_per_day)
        self.convex_chain = [now_node]
        end_node = max(self.all_data, key=lambda res: res.exp_per_hour)
        while now_node != end_node:
            next_node = max(
                filter(lambda res: res.exp_per_hour > now_node.exp_per_hour, self.all_data),
                key=lambda res:
                (res.profit_per_day - now_node.profit_per_day) / (res.exp_per_hour - now_node.exp_per_hour)
            )
            self.convex_chain.append(next_node)
            now_node = next_node
        for res in self.convex_chain:
            res.color = res.color[:3] + (1.0,)


sd = SimulationData()
for file in os.listdir('./data'):
    if file.endswith('.json'):
        sd.add_data(os.path.join('./data', file), com_buff=True)
pprint(sd.all_data)
for res in sd.all_data:
    if get_key(res.key) == '单普地':
        print(res)

sd.wash_data(
    max_deaths_per_hour=2.0,
    superior_filter_map_only=True,
    superior_filter=False,
    inferior_filter=True,
    inferior_filter_coefficient=0.8
)
sd.find_convex_hull()

fig, ax = plt.subplots()
fig.set_size_inches(19.2, 10.8)

ax.scatter([], [], color='red', s=25, label='每小时0.0死', alpha=0.6)
ax.scatter([], [], color='red', s=50, label='每小时0.25死', alpha=0.6)
ax.scatter([], [], color='red', s=75, label='每小时0.5死', alpha=0.6)
ax.scatter([], [], color='red', s=125, label='每小时1.0死', alpha=0.6)
ax.legend()

for result in sd.all_data:
    ax.scatter(result.exp_per_hour, result.profit_per_day,
               s=25 * (4 * result.deaths_per_hour + 1), color=result.color,
               marker='x' if result.oom else 'o')
    ax.text(result.exp_per_hour, result.profit_per_day, result.name, color=result.color,
            fontsize=14, rotation=0)
for i in range(1, len(sd.convex_chain)):
    ax.plot([sd.convex_chain[i - 1].exp_per_hour, sd.convex_chain[i].exp_per_hour],
            [sd.convex_chain[i - 1].profit_per_day, sd.convex_chain[i].profit_per_day],
            color='black', alpha=0.6)
plt.xlabel('经验 (K/小时)', fontsize=16)
plt.ylabel('利润 (M/天)', fontsize=16)
plt.title('模拟结果\n'
          f'模拟时间=24h 价格更新时间{datetime.fromtimestamp(sd.price_getter.time).strftime("%m月%d日%H时")}。计算掉落社区buff，不计算经验buff\n'
          '点越大，死的越多。折线为凸包\n',
          fontsize=16)
plt.show()
