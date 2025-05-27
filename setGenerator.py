import itertools
import json
import os
from pprint import pprint

NUMBER = '零单双三'
STEP = 8


def trange(start, stop, step, custom_name=''):
    return dict((i, custom_name + str(i)) for i in range(start, stop, step))


# auras会控制玩家光环和人数
# 所有变量的各种取值作笛卡尔积
auras = [
    ["/abilities/fierce_aura"],
    ["/abilities/fierce_aura", "/abilities/speed_aura"],
    ["/abilities/fierce_aura", "/abilities/speed_aura", "/abilities/critical_aura"],
]
all_tests = {
    "food./action_types/combat[1].itemHrid": {
        "/items/spaceberry_donut": "双红",
        "/items/star_fruit_gummy": "双蓝"
    },
    "drinks./action_types/combat[1].itemHrid": {
        "/items/power_coffee": "力量",
        "/items/super_power_coffee": "超力",
        "/items/ultra_power_coffee": "究力",
    },
    "drinks./action_types/combat[0].itemHrid": {
        "/items/wisdom_coffee": "经验",
        "/items/lucky_coffee": "幸运",
        "/items/super_stamina_coffee": "超耐",
        "/items/ultra_stamina_coffee": "究耐",
    },
    "abilities[4].abilityHrid": {
        "/abilities/sweep": "重扫",
        "/abilities/stunning_blow": "重锤",
        "/abilities/precision": "精确",
        # "/abilities/vampirism": "吸血",
    },
}


def update_json(json_data, path, value):
    keys = path.split('.')
    for i, key in enumerate(keys):
        if '[' in key and ']' in key:
            key, index = key.split('[')
            index = int(index.rstrip(']'))
            if i == len(keys) - 1:
                json_data[key][index] = value
            else:
                json_data = json_data[key][index]
        else:
            if i == len(keys) - 1:
                json_data[key] = value
            else:
                json_data = json_data[key]


with open('singlePlayer.json', 'r') as f:
    template = json.load(f)
result = []


def deepcopy(obj):
    return json.loads(json.dumps(obj))


for auras, *st in itertools.product(auras, *(
        list(tuple(((key, item) for item in all_tests[key].keys())) for key in all_tests.keys())
)):
    new_set = {
        "name": NUMBER[len(auras)] + "人",
        "zone": "all",
        "simulationTimeLimit": 24,
        "players": []
    }
    if len(list(x[1] for x in st)) != len(set(x[1] for x in st)):
        print(f'Duplicate item in {auras=} | {st=}')
        continue
    for no, aura in enumerate(auras):
        new_player = deepcopy(template)
        update_json(new_player, 'abilities[0].abilityHrid', aura)
        for key, item in st:
            update_json(new_player, key, item)
            if no == 0:
                new_set["name"] += all_tests[key][item]
        new_set["players"].append(new_player)
    result.append(new_set)

# for f in os.listdir('./setResults'):
#     os.remove('./setResults/' + f)

for i in range(0, len(result), STEP):
    with open(f'./setResults/result{i // STEP}.json', 'w', encoding='utf-8') as f:
        json.dump(result[i:min(i + STEP, len(result))], f, indent=2, ensure_ascii=False)
