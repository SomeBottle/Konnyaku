"""
Bangumi API 接入模块

参考: https://bangumi.github.io/api/
"""

import requests


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
        print('API KEY', self.api_key)
        if api_key:
            self.api_key = api_key
        print('API KEY', self.api_key)

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
        url = f"{BANGUMI_API_URL}/{BANGUMI_API_VERSION}/subjects/{subject_id}/characters"
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
