"""
CI 自动化质量门禁与端到端健康探测脚本 (CI Smoke Test)
用于在 GitHub Actions 构建阶段自动验证全平台核心链路，确保 0 缺陷发布。
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

class TestMagicStarAndDreamClip(unittest.TestCase):
    
    def test_01_magicstar_platform(self):
        """测试 MagicStarPlatform 平台底座核心链路"""
        sys.path.insert(0, os.path.abspath("magicstar-platform"))
        from app.main import app as platform_app, init_db_and_seed_data
        
        # 显式初始化数据库表与预置超管账号 (兼容 CI 环境中的 SQLite 内存/本地回退)
        init_db_and_seed_data()
        
        with TestClient(platform_app) as client:
            # 1. 探活端点
            res_health = client.get("/health")
            self.assertEqual(res_health.status_code, 200, "平台底座 /health 探活失败")
            self.assertEqual(res_health.json().get("status"), "UP")
            
            # 2. 页面路由渲染
            res_portal = client.get("/portal")
            self.assertEqual(res_portal.status_code, 200, "PortalOS 页面渲染失败")
            self.assertIn("html", res_portal.headers.get("content-type", "").lower())
            
            res_login = client.get("/login")
            self.assertEqual(res_login.status_code, 200, "统一登录页渲染失败")
            
            res_admin = client.get("/admin")
            self.assertEqual(res_admin.status_code, 200, "SuperAdmin 控制台渲染失败")
            
            # 3. 超管登录与 JWT 凭证派发
            res_login_api = client.post("/api/v1/auth/login", json={
                "username": "superadmin",
                "password": "123456"
            })
            self.assertEqual(res_login_api.status_code, 200, "超级管理员登录失败")
            data = res_login_api.json().get("data", {})
            token = data.get("access_token")
            self.assertTrue(bool(token), "未能正确派发 JWT Token")
            
            # 4. 权限与已授权应用清单拉取
            res_apps = client.get("/api/v1/auth/my-apps", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res_apps.status_code, 200, "获取已授权应用清单失败")
            app_codes = [a["service_code"] for a in res_apps.json().get("data", [])]
            self.assertIn("magicstar-platform", app_codes, "已授权应用中缺失 magicstar-platform")
            self.assertTrue("dreamclip-service" in app_codes or "dreamclip" in app_codes, "已授权应用中缺失 dreamclip-service")
            print("[PASS] MagicStarPlatform (5 critical test assertions passed)")

    def test_02_dreamclip_service(self):
        """测试 DreamClip 梦之厅业务微服务核心链路"""
        # 清理此前模块引用缓存
        for k in list(sys.modules.keys()):
            if k.startswith("app."):
                del sys.modules[k]
        if "magicstar-platform" in sys.path[0]:
            sys.path.pop(0)
            
        sys.path.insert(0, os.path.abspath("dreamclip-service"))
        from app.main import app as dreamclip_app, init_seed_universe_data
        
        # 显式初始化数据库表与业务种子数据 (世界观/角色/胶囊/跑马灯)
        init_seed_universe_data()
        
        with TestClient(dreamclip_app) as client:
            # 1. 探活端点
            res_health = client.get("/health")
            self.assertEqual(res_health.status_code, 200, "DreamClip /health 探活失败")
            self.assertEqual(res_health.json().get("status"), "UP")
            
            # 2. 页面路由渲染
            res_hall = client.get("/")
            self.assertEqual(res_hall.status_code, 200, "梦之厅主站渲染失败")
            
            res_studio = client.get("/studio")
            self.assertEqual(res_studio.status_code, 200, "DreamClip Studio 渲染失败")
            
            res_games = client.get("/games")
            self.assertEqual(res_games.status_code, 200, "AVG 游戏中心渲染失败")

            # 3. 剧院场景、童话绘本工坊、吉卜力治愈大厅与实验室路由测试
            for t_route in ["/workshop", "/picturebook", "/fairytale-workshop", "/ghibli", "/theater-ghibli", "/theater", "/theater-lab", "/theater-svg", "/theater-parallax", "/theater-webp", "/theater-3d", "/theater-video"]:
                res_t = client.get(t_route)
                self.assertEqual(res_t.status_code, 200, f"剧院/工坊方案路由 {t_route} 渲染失败")
            
            # 4. 业务 API 数据拉取及多前缀兼容
            res_banners = client.get("/api/universe/hall/banners")
            self.assertEqual(res_banners.status_code, 200, "跑马灯/焦点接口异常")
            self.assertGreater(len(res_banners.json().get("data", [])), 0, "跑马灯数据为空")
            
            res_capsules = client.get("/api/universe/capsules")
            self.assertEqual(res_capsules.status_code, 200, "情绪胶囊接口异常")
            self.assertGreater(len(res_capsules.json().get("data", {}).get("items", [])), 0, "情绪胶囊数据为空")
            
            res_characters = client.get("/api/universe/characters")
            self.assertEqual(res_characters.status_code, 200, "角色档案接口异常")
            self.assertGreater(len(res_characters.json().get("data", [])), 0, "角色档案数据为空")
            print("[PASS] DreamClip Service (10 critical test assertions passed)")

if __name__ == "__main__":
    unittest.main(verbosity=2)
