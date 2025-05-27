import requests


class PriceGetter:
    def __init__(self,
                 market_url='https://raw.githubusercontent.com/holychikenz/MWIApi/main/medianmarket.json',
                 init_client_data_url='https://raw.githubusercontent.com/silent1b/MWIData/main/init_client_info.json'):
        self.raw_market_data = requests.get(market_url).json()
        self.init_client_data = requests.get(init_client_data_url).json()
        self.cache_item_prices = {"bid": {}, "ask": {}}
        self.cache_enemy_prices = {}
        self.time = round(self.raw_market_data["time"])

    def get_price(self, item_hrid, mode="bid"):
        if item_hrid not in self.cache_item_prices[mode]:
            if item_hrid == "/items/coin":
                self.cache_item_prices[mode][item_hrid] = 1
            elif item_hrid == "/items/cowbell":
                self.cache_item_prices[mode][item_hrid] = round(self.get_price("/items/bag_of_10_cowbells", mode) / 10)
            elif item_hrid in self.init_client_data["openableLootDropMap"] and item_hrid != "/items/bag_of_10_cowbells":
                drop_map = self.init_client_data["openableLootDropMap"][item_hrid]
                self.cache_item_prices[mode][item_hrid] = round(sum(
                    item["dropRate"] * (item["minCount"] + item["maxCount"]) *
                    self.get_price(item["itemHrid"], mode) / 2
                    for item in drop_map
                ))
            else:
                self.cache_item_prices[mode][item_hrid] = self.raw_market_data["market"] \
                    [self.init_client_data["itemDetailMap"][item_hrid]["name"]][mode]
        return self.cache_item_prices[mode][item_hrid]

    def get_enemy_price(
            self,
            enemy_hrid,
            elite_tier=0,
            drop_rate_multiplier=1.0,
            rare_find_multiplier=1.0,
            com_buff_multiplier=1.0
    ):
        if (enemy_hrid, elite_tier, drop_rate_multiplier, rare_find_multiplier) not in self.cache_enemy_prices:
            self.cache_enemy_prices[
                (enemy_hrid, elite_tier, drop_rate_multiplier, rare_find_multiplier)
            ] = round(
                sum(
                    min(1.0, item["dropRate"] * drop_rate_multiplier) *
                    (item["minCount"] + item["maxCount"]) *
                    self.get_price(item["itemHrid"], "bid") / 2
                    for item in self.init_client_data["combatMonsterDetailMap"][enemy_hrid]["dropTable"]
                    if elite_tier >= item["minEliteTier"]
                ) + sum(
                    min(1.0, item["dropRate"] * drop_rate_multiplier * rare_find_multiplier) *
                    (item["minCount"] + item["maxCount"]) *
                    self.get_price(item["itemHrid"], "bid") / 2
                    for item in self.init_client_data["combatMonsterDetailMap"][enemy_hrid]["rareDropTable"]
                    if elite_tier >= item["minEliteTier"]
                )
            )
        return round(
            self.cache_enemy_prices[
                (enemy_hrid, elite_tier, drop_rate_multiplier, rare_find_multiplier)] * com_buff_multiplier)

