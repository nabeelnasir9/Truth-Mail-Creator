# -*- coding:utf-8 -*-
"""
@Author  :   g1879
@Contact :   g1879@qq.com
"""
from json import loads, JSONDecodeError
from time import sleep

from requests.structures import CaseInsensitiveDict

from .base import BaseListener


class RequestData(object):
    """网络请求数据包管理类"""
    __slots__ = ('_data', 'requestId', 'fetchId', 'request', 'tab', 'target', 'url', 'urlFragment', 'method',
                 'hasPostData', 'postDataEntries', 'mixedContentType', 'initialPriority', 'referrerPolicy',
                 'isLinkPreload', 'trustTokenParams', 'isSameSite', '_postData')

    def __init__(self, data, tab, target):
        """
        :param data: 请求的数据
        :param tab: 产生这个数据包的tab的id
        :param target: 监听目标
        """
        self._data = data
        self.requestId = data.get('networkId', None)
        self.fetchId = data.get('requestId', None)
        self.request = CaseInsensitiveDict(data['request'])
        self.tab = tab
        self.target = target
        self._postData = None

    def __getattr__(self, item):
        return self.request.get(item, None)

    def __getitem__(self, item):
        return self.request.get(item, None)

    def __repr__(self):
        return f'<RequestData target={self.target} request_id={self.requestId}>'

    @property
    def headers(self):
        """以大小写不敏感字典返回headers数据"""
        h = self.request.get('headers', None)
        return CaseInsensitiveDict(h) if h else None

    @property
    def postData(self):
        """返回post数据"""
        if self._postData is None:
            try:
                self._postData = loads(self.request.get('postData', None))
            except JSONDecodeError:
                self._postData = self.request.get('postData', None)
        return self._postData


class RequestMan(BaseListener):
    """浏览器的数据包监听器"""

    def __init__(self,
                 browser=None,
                 tab_handle=None):
        """
        :param browser: 要监听的url:port、端口或MixPage对象，WebPage，ChromiumPage。
                        MixPage对象须设置了local_port参数。为None时自动从系统中寻找可监听的浏览器
        :param tab_handle: 要监听的标签页的handle，不输入读取当前活动标签页
        """
        super().__init__(browser, tab_handle)

    def to_tab(self,
               handle_or_id=None,
               browser=None):
        """设置要监听的标签页
        :param handle_or_id: 要监听的标签页的handle，不输入读取当前活动标签页
        :param browser: 更换别的浏览器
        :return: None
        """
        if self.listening:
            self._tab.Fetch.disable()

        super().to_tab(handle_or_id, browser)

        if self.listening:
            self._tab.Fetch.enable()

    def listen(self,
               targets=None,
               count=None,
               timeout=None,
               asyn=True):
        """拦截目标请求，直到超时或达到拦截个数，每次拦截前清空结果
        可监听多个目标，请求url包含这些字符串就会被记录
        :param targets: 要监听的目标字符串或其组成的列表，True监听所有，None则保留之前的目标不变
        :param count: 要记录的个数，到达个数停止监听
        :param timeout: 监听最长时间，到时间即使未达到记录个数也停止，None为无限长
        :param asyn: 是否异步监听
        :return: None
        """
        self._tab.Fetch.enable()
        super().listen(targets, count, timeout)

    def get_results(self, target=None):
        """获取结果列表
        :param target: 要获取的目标，为None时获取全部
        :return: 结果数据组成的列表
        """
        return super().get_results(target)

    def steps(self, gap=1):
        """用于单步操作，可实现没收到若干个数据包执行一步操作（如翻页）
        于是可以根据数据包是否加载完成来决定是否翻页，无须从页面dom去判断是否加载完成
        大大简化代码，提高可靠性
        eg: for i in listener.steps(2):
                btn.click()
        :param gap: 每接收到多少个数据包触发
        :return: 用于在接收到监听目标时触发动作的可迭代对象
        """
        if not isinstance(gap, int) or gap < 1:
            raise ValueError('gap参数必须为大于0的整数。')
        while self.listening or not self._tmp.empty():
            while self._tmp.qsize() >= gap:
                yield self._tmp.get(False) if gap == 1 else [self._tmp.get(False) for _ in range(gap)]

            sleep(.1)

    def _request_paused(self, **kwargs):
        """接收到请求时的回调函数"""
        if not self._is_continue():
            return

        fetch_id = kwargs['requestId']
        if self.targets is True:
            request = RequestData(kwargs, self.tab_id, True)
            self._caught_count += 1
            self._tmp.put(request)
            self.results.append(request)

        else:
            for target in self.targets:
                if target in kwargs['request']['url']:
                    request = RequestData(kwargs, self.tab_id, True)
                    self._caught_count += 1
                    self._tmp.put(request)
                    self.results.append(request)

        self._tab.Fetch.continueRequest(requestId=fetch_id)

    def _set_callback_func(self):
        """设置监听的回调函数"""
        self._tab.Fetch.requestPaused = self._request_paused

    def _stop(self):
        """停止监听前要做的工作"""
        self._tab.Fetch.disable()
        self._tab.Fetch.requestPaused = None
