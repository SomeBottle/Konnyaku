"""
Bangumi API 接入模块

参考: https://bangumi.github.io/api/
"""

import requests

from time import sleep
from konnyaku.config import BANGUMI_API_KEY

BANGUMI_API_URL = "https://api.bgm.tv"
BANGUMI_API_VERSION = "v0"

USER_AGENT = "SomeBottle/Konnyaku (https://github.com/SomeBottle/Konnyaku)"


class BangumiAPI:
    """
    Bangumi API 接入类
    """

    def __init__(self, api_key: str = None):
        """
        初始化

        :param api_key: Bangumi API Key，如果不提供则从环境变量中读取
        """
        self.api_key = BANGUMI_API_KEY
        if api_key:
            self.api_key = api_key

    def _get(self, url: str) -> dict:
        """
        发送 GET 请求

        :param url: 请求的 URL
        :return: 请求结果
        :raises requests.HTTPError: 请求异常
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_subject_info(self, subject_id: str) -> dict:
        """
        获取番剧基本信息

        :param subject_id: 番剧 ID
        :return: 番剧基本信息
        :raises requests.HTTPError: 请求异常
        """
        url = f"{BANGUMI_API_URL}/{BANGUMI_API_VERSION}/subjects/{subject_id}"
        return self._get(url)

    def get_subject_characters(self, subject_id: str) -> dict:
        """
        获取番剧角色信息

        :param subject_id: 番剧 ID
        :return: 番剧角色信息
        :raises requests.HTTPError: 请求异常
        """
        url = (
            f"{BANGUMI_API_URL}/{BANGUMI_API_VERSION}/subjects/{subject_id}/characters"
        )
        return self._get(url)

    def get_character_info(self, character_id: str) -> dict:
        """
        获取角色信息

        :param character_id: 角色 ID
        :return: 角色信息
        :raises requests.HTTPError: 请求异常
        """
        url = f"{BANGUMI_API_URL}/{BANGUMI_API_VERSION}/characters/{character_id}"
        return self._get(url)

    def get_subject_all_character_infos(self, subject_id: str) -> list[dict]:
        """
        提取 Bangumi 番剧中的所有角色的信息，主要是名字、关系

        :param subject_id: 番剧 ID
        :return: 角色名列表 [{relation: str, name: str, name_chs: str, gender: str}, ...]
        :raises requests.HTTPError: 请求异常
        """
        RATE_LIMIT = 10  # 每经过多少次请求就休息一下

        characters = self.get_subject_characters(subject_id)
        character_ids = []
        # 临时存储角色在番剧中的关系
        id_to_relation = {}
        for character in characters:
            if "id" in character:
                character_ids.append(character["id"])
                if "relation" in character:
                    id_to_relation[character["id"]] = character["relation"]

        result = []
        request_count = 0
        for character_id in character_ids:
            if (request_count + 1) % RATE_LIMIT == 0:
                # 休息一下
                print("Let me take a break...ε-(´-ᗜ-`;)", end="\r")
                sleep(1)

            print(
                f"Getting character info ...({request_count + 1}/{len(character_ids)})",
                end="\r",
            )
            character_info = self.get_character_info(character_id)
            res_info = {"relation": "", "name": "", "name_chs": "", "gender": ""}
            if "name" in character_info:
                res_info["name"] = character_info["name"]

            if "gender" in character_info and character_info["gender"]:
                res_info["gender"] = character_info["gender"]

            if "infobox" in character_info and isinstance(
                character_info["infobox"], list
            ):
                for info_dict in character_info["infobox"]:
                    if info_dict["key"] == "简体中文名":
                        res_info["name_chs"] = info_dict["value"]
                    elif info_dict["key"] == "性别":
                        res_info["gender"] = info_dict["value"]

            if character_id in id_to_relation:
                res_info["relation"] = id_to_relation[character_id]

            result.append(res_info)

            request_count += 1

        print()

        return result
