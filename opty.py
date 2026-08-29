#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptY - Windows 系统优化工具 v2.0
用法: opty [优化项目名称] [-e|-r] [参数]
     opty telemetry -e 1    # 启用优化（禁用遥测）
     opty telemetry -e -1   # 禁用优化（恢复遥测 = 关闭优化）
     opty telemetry -e 0    # 恢复默认状态
     opty telemetry -r      # 读取当前状态 -> status: -1/0/1
     opty all -e 1          # 开启所有优化
     opty list              # 列出所有优化项目

状态语义（统一）:
  -1 = 禁用（对应 Windows 功能被关闭）
   0 = 默认（出厂/推荐状态）
   1 = 启用（对应 Windows 功能被强制开启）
"""

import sys
import subprocess
import winreg
import ctypes
from enum import IntEnum


class S(IntEnum):
    DISABLED = -1   # 优化项被关闭（Windows 功能开启）
    DEFAULT = 0     # 默认状态
    ENABLED = 1     # 优化项被开启（Windows 功能关闭）
    UNKNOWN = 99


STATUS_TEXT = {-1: "disabled", 0: "default", 1: "enabled", 99: "unknown"}


class OptY:
    def __init__(self):
        # enable = 开启优化(关掉 Windows 功能)；disable = 关闭优化(恢复功能)；default = 出厂态
        self.optimizations = {
            # ==================== 视觉与性能 ====================
            "visual_fx": {
                "name": "视觉效果优化", "desc": "调整为最佳性能(关闭视觉特效)", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 1),
                "default": lambda: self._reg_del(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting"),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", {2: 1, 1: -1}),
            },
            "animations": {
                "name": "动画效果", "desc": "关闭窗口动画/最小化最大化动画", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", {0: 1, 1: -1}),
            },
            "transparency": {
                "name": "透明效果", "desc": "关闭窗口/任务栏透明", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", {0: 1, 1: -1}),
            },
            "shadow": {
                "name": "阴影效果", "desc": "关闭窗口阴影/列表阴影", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", {0: 1, 1: -1}),
            },
            "peek": {
                "name": "任务栏悬停预览", "desc": "关闭鼠标悬停任务栏缩略图", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisablePreviewDesktop", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisablePreviewDesktop", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisablePreviewDesktop", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisablePreviewDesktop", {1: 1, 0: -1}),
            },
            "menu_fade": {
                "name": "菜单淡入淡出", "desc": "关闭菜单动画(加快响应)", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuFade", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuFade", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuFade", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuFade", {0: 1, 1: -1}),
            },

            # ==================== 系统服务 ====================
            "sysmain": {
                "name": "SysMain(预读取)", "desc": "禁用 Superfetch 预读取服务", "category": "服务",
                "enable": lambda: self._svc_set("SysMain", "disabled"),
                "disable": lambda: self._svc_set("SysMain", "auto"),
                "default": lambda: self._svc_set("SysMain", "auto"),
                "read": lambda: self._svc_read("SysMain"),
            },
            "windows_search": {
                "name": "Windows 搜索索引", "desc": "禁用 Search 索引服务", "category": "服务",
                "enable": lambda: self._svc_set("WSearch", "disabled"),
                "disable": lambda: self._svc_set("WSearch", "auto"),
                "default": lambda: self._svc_set("WSearch", "auto"),
                "read": lambda: self._svc_read("WSearch"),
            },
            "diagnostic": {
                "name": "诊断跟踪(Telemetry)", "desc": "禁用 DiagTrack 遥测服务", "category": "隐私",
                "enable": lambda: self._svc_set("DiagTrack", "disabled"),
                "disable": lambda: self._svc_set("DiagTrack", "auto"),
                "default": lambda: self._svc_set("DiagTrack", "auto"),
                "read": lambda: self._svc_read("DiagTrack"),
            },
            "update_service": {
                "name": "Windows Update", "desc": "改为手动启动(按需更新)", "category": "服务",
                "enable": lambda: self._svc_set("wuauserv", "demand"),
                "disable": lambda: self._svc_set("wuauserv", "auto"),
                "default": lambda: self._svc_set("wuauserv", "auto"),
                "read": lambda: self._svc_read("wuauserv"),
            },
            "print_spooler": {
                "name": "打印后台处理", "desc": "无打印机时可禁用", "category": "服务",
                "enable": lambda: self._svc_set("Spooler", "disabled"),
                "disable": lambda: self._svc_set("Spooler", "auto"),
                "default": lambda: self._svc_set("Spooler", "auto"),
                "read": lambda: self._svc_read("Spooler"),
            },
            "bluetooth": {
                "name": "蓝牙支持服务", "desc": "禁用蓝牙服务", "category": "服务",
                "enable": lambda: self._svc_set("BthServ", "disabled"),
                "disable": lambda: self._svc_set("BthServ", "auto"),
                "default": lambda: self._svc_set("BthServ", "auto"),
                "read": lambda: self._svc_read("BthServ"),
            },
            "error_reporting": {
                "name": "Windows 错误报告", "desc": "禁用 WerSvc", "category": "隐私",
                "enable": lambda: self._svc_set("WerSvc", "disabled"),
                "disable": lambda: self._svc_set("WerSvc", "auto"),
                "default": lambda: self._svc_set("WerSvc", "auto"),
                "read": lambda: self._svc_read("WerSvc"),
            },
            "remote_registry": {
                "name": "远程注册表", "desc": "禁用 RemoteRegistry 服务", "category": "安全",
                "enable": lambda: self._svc_set("RemoteRegistry", "disabled"),
                "disable": lambda: self._svc_set("RemoteRegistry", "auto"),
                "default": lambda: self._svc_set("RemoteRegistry", "disabled"),
                "read": lambda: self._svc_read("RemoteRegistry"),
            },

            # ==================== 隐私与遥测 ====================
            "telemetry": {
                "name": "遥测数据收集", "desc": "组策略禁用遥测(AllowTelemetry=0)", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 3),
                "default": lambda: self._reg_del(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry"),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", {0: 1, 3: -1}),
            },
            "location": {
                "name": "定位服务", "desc": "禁用位置访问", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\Location", "Value", "Deny"),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\Location", "Value", "Allow"),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\Location", "Value", "Allow"),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\Location", "Value", {"Deny": 1, "Allow": -1}),
            },
            "advertising_id": {
                "name": "广告 ID", "desc": "禁用广告标识符", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", {0: 1, 1: -1}),
            },
            "activity_history": {
                "name": "活动历史记录", "desc": "禁用活动历史上传", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "ActivityHistoryEnabled", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "ActivityHistoryEnabled", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "ActivityHistoryEnabled", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "ActivityHistoryEnabled", {0: 1, 1: -1}),
            },
            "speech_recognition": {
                "name": "在线语音识别", "desc": "禁用在线语音", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy", "HasAccepted", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy", "HasAccepted", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy", "HasAccepted", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy", "HasAccepted", {0: 1, 1: -1}),
            },
            "tailored_experiences": {
                "name": "个性化体验(广告)", "desc": "禁用基于体验的个性化", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", {0: 1, 1: -1}),
            },
            "feedback": {
                "name": "用户反馈", "desc": "禁用 Windows 反馈频率", "category": "隐私",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feedback\Settings", "FeedbackFrequency", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feedback\Settings", "FeedbackFrequency", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feedback\Settings", "FeedbackFrequency", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feedback\Settings", "FeedbackFrequency", {0: 1, 1: -1}),
            },

            # ==================== 开始菜单与任务栏 ====================
            "start_menu_ads": {
                "name": "开始菜单推荐/广告", "desc": "禁用内容分发推荐", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "SubscribedContent-338388Enabled", {0: 1, 1: -1}),
            },
            "taskbar_news": {
                "name": "任务栏新闻与兴趣", "desc": "隐藏任务栏 Widgets/新闻", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 2),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", {2: 1, 0: -1}),
            },
            "search_bar": {
                "name": "任务栏搜索框", "desc": "隐藏搜索图标(0=隐藏 1=图标 2=框)", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", {0: 1, 1: -1, 2: -1}),
            },
            "task_view": {
                "name": "任务视图按钮", "desc": "隐藏任务栏任务视图", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowTaskViewButton", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowTaskViewButton", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowTaskViewButton", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowTaskViewButton", {0: 1, 1: -1}),
            },
            "people_bar": {
                "name": "联系人栏(People)", "desc": "隐藏任务栏联系人", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People", "PeopleBand", {0: 1, 1: -1}),
            },
            "taskbar_lock": {
                "name": "锁定任务栏", "desc": "锁定任务栏防止误拖", "category": "界面",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarLockAll", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarLockAll", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarLockAll", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarLockAll", {1: 1, 0: -1}),
            },

            # ==================== 文件资源管理器 ====================
            "quick_access": {
                "name": "快速访问最近文件", "desc": "隐藏快速访问中最近使用", "category": "文件管理",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "ShowRecent", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "ShowRecent", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "ShowRecent", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer", "ShowRecent", {0: 1, 1: -1}),
            },
            "onedrive": {
                "name": "OneDrive 资源管理器集成", "desc": "移除导航栏 OneDrive", "category": "文件管理",
                "enable": lambda: self._reg_set(winreg.HKEY_CLASSES_ROOT, r"CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CLASSES_ROOT, r"CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CLASSES_ROOT, r"CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CLASSES_ROOT, r"CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}", "System.IsPinnedToNameSpaceTree", {0: 1, 1: -1}),
            },
            "file_extensions": {
                "name": "显示文件扩展名", "desc": "HideFileExt=0 显示扩展名", "category": "文件管理",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", {0: 1, 1: -1}),
            },
            "hidden_files": {
                "name": "显示隐藏文件", "desc": "Hidden=1 显示 / 2 不显示", "category": "文件管理",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden", 2),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden", 2),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "Hidden", {1: 1, 2: -1}),
            },
            "thumbnail_cache": {
                "name": "缩略图缓存", "desc": "禁用缩略图缓存(省资源)", "category": "性能",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisableThumbnailCache", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisableThumbnailCache", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisableThumbnailCache", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "DisableThumbnailCache", {1: 1, 0: -1}),
            },
            "separate_process": {
                "name": "资源管理器独立进程", "desc": "提升稳定性", "category": "文件管理",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", {1: 1, 0: -1}),
            },

            # ==================== 网络优化 ====================
            "nagle": {
                "name": "Nagle 算法", "desc": "禁用 Nagle 降低延迟(TcpAckFrequency=1)", "category": "网络",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency", 1),
                "disable": lambda: self._reg_del(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency"),
                "default": lambda: self._reg_del(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency"),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency", {1: 1}),
            },
            "qos": {
                "name": "QoS 预留带宽", "desc": "释放 20% 预留带宽", "category": "网络",
                "enable": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=normal"),
                "disable": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=restricted"),
                "default": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=normal"),
                "read": lambda: S.UNKNOWN,
            },
            "dns_cache": {
                "name": "DNS 缓存大小", "desc": "增大 DNS 缓存条目", "category": "网络",
                "enable": lambda: (self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableBucketSize", 1) and
                                  self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableSize", 384)),
                "disable": lambda: (self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableBucketSize", 0) and
                                   self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableSize", 128)),
                "default": lambda: (self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableBucketSize", 0) and
                                   self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableSize", 128)),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters", "CacheHashTableSize", {384: 1, 128: -1}),
            },
            "tcp_autotune": {
                "name": "TCP 窗口自动调优", "desc": "启用接收窗口自动调优", "category": "网络",
                "enable": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=normal"),
                "disable": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=disabled"),
                "default": lambda: self._run_cmd("netsh int tcp set global autotuninglevel=normal"),
                "read": lambda: S.UNKNOWN,
            },

            # ==================== 电源与硬件 ====================
            "power_high_perf": {
                "name": "高性能电源计划", "desc": "激活 SCHEME_MIN(高性能)", "category": "电源",
                "enable": lambda: self._run_cmd("powercfg /setactive SCHEME_MIN"),
                "disable": lambda: self._run_cmd("powercfg /setactive SCHEME_BALANCED"),
                "default": lambda: self._run_cmd("powercfg /setactive SCHEME_BALANCED"),
                "read": lambda: self._power_read(),
            },
            "usb_selective": {
                "name": "USB 选择性暂停", "desc": "禁用 USB 选择性挂起", "category": "硬件",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USB\Parameters", "DisableSelectiveSuspend", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USB\Parameters", "DisableSelectiveSuspend", 0),
                "default": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USB\Parameters", "DisableSelectiveSuspend", 0),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USB\Parameters", "DisableSelectiveSuspend", {1: 1, 0: -1}),
            },
            "hard_disk_timeout": {
                "name": "硬盘休眠超时", "desc": "延长硬盘关闭时间(从不=0)", "category": "硬件",
                "enable": lambda: self._run_cmd("powercfg /change disk-timeout-ac 0"),
                "disable": lambda: self._run_cmd("powercfg /change disk-timeout-ac 20"),
                "default": lambda: self._run_cmd("powercfg /change disk-timeout-ac 20"),
                "read": lambda: S.UNKNOWN,
            },
            "fast_startup": {
                "name": "快速启动", "desc": "禁用休眠快速启动", "category": "电源",
                "enable": lambda: self._run_cmd("powercfg /h off"),
                "disable": lambda: self._run_cmd("powercfg /h on"),
                "default": lambda: self._run_cmd("powercfg /h on"),
                "read": lambda: S.UNKNOWN,
            },

            # ==================== 安全与维护 ====================
            "defender_scan": {
                "name": "Defender 实时防护", "desc": "通过组策略禁用 Defender(谨慎)", "category": "安全",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 0),
                "default": lambda: self._reg_del(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware"),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", {1: 1, 0: -1}),
            },
            "smartscreen": {
                "name": "SmartScreen 筛选器", "desc": "禁用应用筛选器", "category": "安全",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", 1),
                "default": lambda: self._reg_del(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen"),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen", {0: 1, 1: -1}),
            },
            "autoplay": {
                "name": "自动播放", "desc": "禁用媒体自动播放", "category": "安全",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers", "DisableAutoplay", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers", "DisableAutoplay", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers", "DisableAutoplay", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers", "DisableAutoplay", {1: 1, 0: -1}),
            },
            "remote_desktop": {
                "name": "远程桌面", "desc": "禁用远程桌面(fDenyTSConnections=1)", "category": "安全",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server", "fDenyTSConnections", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server", "fDenyTSConnections", 0),
                "default": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server", "fDenyTSConnections", 1),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server", "fDenyTSConnections", {1: 1, 0: -1}),
            },
            "uac": {
                "name": "UAC 通知", "desc": "启用始终通知(最高安全)", "category": "安全",
                "enable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "ConsentPromptBehaviorAdmin", 2),
                "disable": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "ConsentPromptBehaviorAdmin", 0),
                "default": lambda: self._reg_set(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "ConsentPromptBehaviorAdmin", 5),
                "read": lambda: self._read_choice(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "ConsentPromptBehaviorAdmin", {2: 1, 0: -1, 5: 0}),
            },

            # ==================== 输入设备 ====================
            "mouse_accel": {
                "name": "鼠标加速度", "desc": "关闭加速度(固定灵敏度)", "category": "输入",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", 0),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", 1),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseSpeed", {0: 1, 1: -1}),
            },
            "numlock": {
                "name": "开机 NumLock", "desc": "登录时自动开启数字键盘", "category": "输入",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "InitialKeyboardIndicators", 2),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "InitialKeyboardIndicators", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "InitialKeyboardIndicators", 0),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Keyboard", "InitialKeyboardIndicators", {2: 1, 0: -1}),
            },
            "capslock_sound": {
                "name": "CapsLock 提示音", "desc": "禁用切换键声音", "category": "输入",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", 58),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", 62),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", 62),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\ToggleKeys", "Flags", {58: 1, 62: -1}),
            },
            "mouse_hide": {
                "name": "键入时隐藏鼠标", "desc": "打字时自动隐藏指针", "category": "输入",
                "enable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "HidePointerWhileTyping", 1),
                "disable": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "HidePointerWhileTyping", 0),
                "default": lambda: self._reg_set(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "HidePointerWhileTyping", 1),
                "read": lambda: self._read_choice(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "HidePointerWhileTyping", {1: 1, 0: -1}),
            },
        }

    # ==================== 基础工具 ====================
    def _run_cmd(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False

    def _reg_set(self, key, path, name, value, type=winreg.REG_DWORD):
        try:
            with winreg.CreateKey(key, path) as k:
                winreg.SetValueEx(k, name, 0, type, value)
            return True
        except Exception:
            return False

    def _reg_del(self, key, path, name):
        try:
            with winreg.OpenKey(key, path, 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, name)
            return True
        except FileNotFoundError:
            return True  # 本来就不存在 = 已默认
        except Exception:
            return False

    def _reg_get(self, key, path, name):
        try:
            with winreg.OpenKey(key, path) as k:
                v, _ = winreg.QueryValueEx(k, name)
                return v
        except Exception:
            return None

    def _read_choice(self, key, path, name, mapping):
        """按 mapping = {注册表值: 状态} 反查；找不到值 -> 默认(0)"""
        v = self._reg_get(key, path, name)
        if v is None:
            return S.DEFAULT
        return mapping.get(v, S.UNKNOWN)

    # ==================== 服务封装 ====================
    def _svc_set(self, name, start_type):
        ok = self._run_cmd(f"sc config \"{name}\" start={start_type}")
        if start_type == "disabled":
            self._run_cmd(f"sc stop \"{name}\"")
        return ok

    def _svc_read(self, name):
        ok, out = self._cmd_out(f"sc qc \"{name}\"")
        if not ok:
            return S.UNKNOWN
        for line in out.splitlines():
            if "START_TYPE" in line:
                if "DISABLED" in line:
                    return S.ENABLED   # 服务被禁用 = 优化已启用
                elif "AUTO_START" in line or "DEMAND_START" in line:
                    return S.DISABLED  # 服务正常运行 = 优化未启用
        return S.UNKNOWN

    def _cmd_out(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return r.returncode == 0, r.stdout
        except Exception:
            return False, ""

    def _power_read(self):
        ok, out = self._cmd_out("powercfg /getactivescheme")
        if not ok:
            return S.UNKNOWN
        if "SCHEME_MIN" in out or "高性能" in out:
            return S.ENABLED
        return S.DISABLED

    # ==================== 公开 API ====================
    def list_optimizations(self):
        print()
        print("=" * 92)
        print("OptY  Windows 系统优化工具  v2.0  共 %d 项" % len(self.optimizations))
        print("=" * 92)
        print("  %-22s %-18s %s" % ("KEY", "分类", "说明"))
        print("-" * 92)
        cats = {}
        for k, o in self.optimizations.items():
            cats.setdefault(o["category"], []).append((k, o))
        for cat, items in cats.items():
            print("\n  [%s]" % cat)
            for k, o in items:
                print("    %-22s %-18s %s" % (k, o["name"], o["desc"]))
        print("\n" + "=" * 92)
        print("语法:")
        print("  opty <key> -e 1    启用优化(关闭对应 Windows 功能)")
        print("  opty <key> -e -1   禁用优化(恢复对应 Windows 功能)")
        print("  opty <key> -e 0    恢复默认状态")
        print("  opty <key> -r      读取状态 -> status: -1(default) / 0 / 1")
        print("  opty all -e 1/-1/0 批量操作")
        print("  opty list          显示本列表")
        print("返回值语义: -1=disabled  0=default  1=enabled")
        print("=" * 92)

    def edit(self, key, value):
        if key == "all":
            return self._edit_all(value)
        if key not in self.optimizations:
            print("error: 未知项目 '%s'，用 'opty list' 查看" % key)
            return False

        opt = self.optimizations[key]
        if value == 1:
            ok = opt["enable"]()
            verb = "enabled(优化已开启)"
        elif value == -1:
            ok = opt["disable"]()
            verb = "disabled(优化已关闭)"
        elif value == 0:
            ok = opt["default"]()
            verb = "default(已恢复默认)"
        else:
            print("error: -e 后只能接 -1 / 0 / 1")
            return False

        self._restart_explorer_hint(key)
        print("%-22s -> %s  [%s]" % (key, verb, "ok" if ok else "fail"))
        return ok

    def _edit_all(self, value):
        ok_cnt = fail_cnt = 0
        verb = {1: "启用", -1: "禁用", 0: "恢复默认"}[value]
        print("\n批量 %s 全部优化项...\n" % verb)
        for k, opt in self.optimizations.items():
            try:
                if value == 1:
                    ok = opt["enable"]()
                elif value == -1:
                    ok = opt["disable"]()
                else:
                    ok = opt["default"]()
            except Exception as e:
                ok = False
            if ok:
                ok_cnt += 1
                print("  [ok ] %-22s %s" % (k, opt["name"]))
            else:
                fail_cnt += 1
                print("  [fail] %-22s %s" % (k, opt["name"]))
        print("\n完成: 成功 %d / 失败 %d" % (ok_cnt, fail_cnt))
        print("提示: 部分设置需注销或重启后生效；服务类改动即时。")
        return fail_cnt == 0

    def read(self, key):
        if key == "all":
            return self._read_all()
        if key not in self.optimizations:
            print("error: 未知项目 '%s'" % key)
            return None
        st = self.optimizations[key]["read"]()
        self._print_read(key, st)
        return st

    def _print_read(self, key, st):
        sym = {-1: "-1 (disabled)", 0: " 0 (default)", 1: " 1 (enabled)", 99: " ? (unknown)"}
        print("%-22s status: %s" % (key, sym.get(int(st), "?")))
        return st

    def _read_all(self):
        print("\n%-22s %-12s %s" % ("KEY", "STATUS", "名称"))
        print("-" * 92)
        for k, opt in self.optimizations.items():
            try:
                st = opt["read"]()
            except Exception:
                st = S.UNKNOWN
            sym = {-1: "-1", 0: " 0", 1: " 1", 99: " ?"}[int(st)]
            print("%-22s %-12s %s" % (k, sym, opt["name"]))
        return None

    def _restart_explorer_hint(self, key):
        explorer_related = ("taskbar", "start_", "search", "people", "task_view", "task_",
                             "quick_access", "onedrive", "file_ext", "hidden_files",
                             "thumbnail", "separate", "visual", "anim", "transp", "shadow", "peek", "menu_fade")
        if any(k in key for k in explorer_related):
            print("  (注: 此项改动通常需要重启资源管理器或注销后生效)")


def parse_args(argv):
    """返回 (key, mode, value) 或 None"""
    args = [a.strip() for a in argv[1:] if a.strip()]
    if not args or args[0] in ("help", "-h", "--help", "list"):
        return None, None, None

    key = args[0].lower()
    mode = None
    value = None

    for a in args[1:]:
        al = a.lower()
        if al in ("-e", "/e", "e"):
            mode = "edit"
        elif al in ("-r", "/r", "r"):
            mode = "read"
        else:
            try:
                value = int(a)
            except ValueError:
                pass

    if mode is None:
        # 兼容旧式: opty key value  -> 视为 -e
        mode = "edit"
    return key, mode, value


def ensure_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
    except Exception:
        pass
    print("warning: 当前非管理员权限，注册表 HKLM / 服务类操作可能失败。")
    print("         建议右键「以管理员身份运行」CMD 后重试。\n")
    return False


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("help", "-h", "--help"):
        OptY().list_optimizations()
        return

    key, mode, value = parse_args(sys.argv)
    if key is None:
        OptY().list_optimizations()
        return

    opty = OptY()

    if key == "list":
        opty.list_optimizations()
        return

    if mode == "read":
        ensure_admin()
        opty.read(key)
        return

    # edit 模式
    ensure_admin()
    if value not in (-1, 0, 1):
        print("error: -e 模式必须指定参数: -1 / 0 / 1")
        print("  opty %s -e 1   启用优化" % key)
        print("  opty %s -e -1  禁用优化" % key)
        print("  opty %s -e 0   恢复默认" % key)
        sys.exit(1)

    opty.edit(key, value)


if __name__ == "__main__":
    main()
