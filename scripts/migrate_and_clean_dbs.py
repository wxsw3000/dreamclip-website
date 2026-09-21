import sys
import os
import io

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import pymysql
from pymysql.cursors import DictCursor

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "19870404")

def run_migration():
    print("==================================================")
    print("  🚀 Starting Database Migration & Cleanup")
    print("==================================================")
    
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True
    )
    cur = conn.cursor()
    
    # 1. Ensure target databases exist
    print("\n[Step 1] Creating target databases: magicstar_platform_db & dreamclip_service_db...")
    cur.execute("CREATE DATABASE IF NOT EXISTS `magicstar_platform_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cur.execute("CREATE DATABASE IF NOT EXISTS `dreamclip_service_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    
    # 2. Check existing databases
    cur.execute("SHOW DATABASES;")
    all_dbs = [r['Database'] for r in cur.fetchall()]
    print(f"Existing databases: {all_dbs}")
    
    # Let's import SQLAlchemy models from both services to create tables
    sys.path.insert(0, os.path.abspath("magicstar-platform"))
    sys.path.insert(0, os.path.abspath("dreamclip-service"))
    
    from sqlalchemy import create_engine
    
    # Target engines
    platform_engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/magicstar_platform_db?charset=utf8mb4")
    business_engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/dreamclip_service_db?charset=utf8mb4")
    
    # Import platform models
    from app.models.base import Base as PlatformBase
    import app.models as platform_models
    print("\n[Step 2] Initializing tables and schema in magicstar_platform_db...")
    PlatformBase.metadata.create_all(bind=platform_engine)
    
    # Import dreamclip models
    from app.models.base import Base as UniverseBase
    import app.models.universe as universe_models
    print("\n[Step 3] Initializing tables and schema in dreamclip_service_db...")
    UniverseBase.metadata.create_all(bind=business_engine)
    
    # 3. Migrate mcp_base_db -> magicstar_platform_db
    if "mcp_base_db" in all_dbs:
        print("\n[Step 4] Migrating data from mcp_base_db to magicstar_platform_db...")
        
        # 4.1 sys_dict_type
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_dict_type`")
        dict_types = cur.fetchall()
        for r in dict_types:
            cur.execute("""
                INSERT INTO `magicstar_platform_db`.`sys_dict_type` 
                (id, dict_code, dict_name, status, remark, is_deleted, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE dict_name=VALUES(dict_name), status=VALUES(status)
            """, (r['id'], r['dict_code'], r['dict_name'], r['status'], r['remark'], r['is_deleted'], r['created_by'], r['created_at'], r['updated_by'], r['updated_at']))
        print(f"  - sys_dict_type: migrated {len(dict_types)} rows")
        
        # 4.2 sys_dict_data
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_dict_data`")
        dict_datas = cur.fetchall()
        for r in dict_datas:
            cur.execute("""
                INSERT INTO `magicstar_platform_db`.`sys_dict_data` 
                (id, dict_code, data_label, data_value, sort_order, css_class, status, remark, is_deleted, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE data_label=VALUES(data_label), data_value=VALUES(data_value), sort_order=VALUES(sort_order), status=VALUES(status)
            """, (r['id'], r['dict_code'], r['data_label'], r['data_value'], r['sort_order'], r['css_class'], r['status'], r['remark'], r['is_deleted'], r['created_by'], r['created_at'], r['updated_by'], r['updated_at']))
        print(f"  - sys_dict_data: migrated {len(dict_datas)} rows")
        
        # 4.3 sys_config
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_config`")
        configs = cur.fetchall()
        for r in configs:
            val = r['config_value']
            if r['config_key'] == 'sys.platform.name':
                val = 'MagicStarPlatform 平台底座'
            cur.execute("""
                INSERT INTO `magicstar_platform_db`.`sys_config` 
                (id, config_key, config_name, config_value, is_system, remark, is_deleted, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE config_value=VALUES(config_value), config_name=VALUES(config_name)
            """, (r['id'], r['config_key'], r['config_name'], val, r['is_system'], r['remark'], r['is_deleted'], r['created_by'], r['created_at'], r['updated_by'], r['updated_at']))
        print(f"  - sys_config: migrated {len(configs)} rows")
        
        # 4.4 sys_role
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_role`")
        roles = cur.fetchall()
        for r in roles:
            cur.execute("""
                INSERT INTO `magicstar_platform_db`.`sys_role`
                (id, role_code, role_name, role_level, is_system, status, remark, is_deleted, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE role_name=VALUES(role_name), role_level=VALUES(role_level), status=VALUES(status)
            """, (r['id'], r['role_code'], r['role_name'], r['role_level'], 1 if r['role_code'] in ['ROLE_SUPER_ADMIN', 'ROLE_OPERATOR', 'ROLE_MEMBER'] else 0, r['status'], r['remark'], r['is_deleted'], r['created_by'], r['created_at'], r['updated_by'], r['updated_at']))
        
        # Also ensure ROLE_MEMBER exists
        cur.execute("""
            INSERT INTO `magicstar_platform_db`.`sys_role`
            (id, role_code, role_name, role_level, is_system, status, remark, is_deleted, created_at, updated_at)
            VALUES (10, 'ROLE_MEMBER', '平台标准注册会员', 20, 1, 'ACTIVE', '平台默认注册用户角色', 0, NOW(), NOW())
            ON DUPLICATE KEY UPDATE role_name=VALUES(role_name)
        """)
        print(f"  - sys_role: migrated {len(roles)} rows + ROLE_MEMBER")
        
        # 4.5 sys_user
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_user`")
        users = cur.fetchall()
        for r in users:
            cur.execute("""
                INSERT INTO `magicstar_platform_db`.`sys_user`
                (id, username, password_hash, real_name, email, phone, avatar, is_superadmin, tenant_code, status, remark, is_deleted, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash), real_name=VALUES(real_name), email=VALUES(email), avatar=VALUES(avatar), is_superadmin=VALUES(is_superadmin), status=VALUES(status), is_deleted=VALUES(is_deleted)
            """, (r['id'], r['username'], r['password_hash'], r['real_name'], r['email'], r['phone'], r['avatar'], r['is_superadmin'], r['tenant_code'], r['status'], r['remark'], r['is_deleted'], r['created_by'], r['created_at'], r['updated_by'], r['updated_at']))
        print(f"  - sys_user: migrated {len(users)} rows")
        
        # 4.6 sys_user_role
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_user_role`")
        user_roles = cur.fetchall()
        for r in user_roles:
            cur.execute("""
                INSERT IGNORE INTO `magicstar_platform_db`.`sys_user_role` (user_id, role_id)
                VALUES (%s, %s)
            """, (r['user_id'], r['role_id']))
        print(f"  - sys_user_role: migrated {len(user_roles)} relations")
        
        # 4.7 sys_login_log
        cur.execute("SELECT * FROM `mcp_base_db`.`sys_login_log`")
        logs = cur.fetchall()
        for r in logs:
            cur.execute("""
                INSERT IGNORE INTO `magicstar_platform_db`.`sys_login_log`
                (id, username, login_ip, browser, os, status, msg, login_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (r['id'], r['username'], r['login_ip'], r['browser'], r['os'], r['status'], r['msg'], r['login_time']))
        print(f"  - sys_login_log: migrated {len(logs)} logs")
    
    # 4.8 Update sys_microservice and sys_menu in magicstar_platform_db
    print("\n[Step 5] Normalizing microservices & menu permissions in magicstar_platform_db...")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cur.execute("DELETE FROM `magicstar_platform_db`.`sys_role_menu`;")
    cur.execute("DELETE FROM `magicstar_platform_db`.`sys_menu`;")
    cur.execute("DELETE FROM `magicstar_platform_db`.`sys_microservice`;")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    cur.execute("""
        INSERT INTO `magicstar_platform_db`.`sys_microservice`
        (id, service_code, service_name, tech_stack, base_url, health_url, docs_url, gateway_prefix, category, version, status, health_status, description, is_deleted, created_at, updated_at)
        VALUES
        (1, 'magicstar-platform', 'MagicStarPlatform 平台底座', 'PYTHON', 'http://127.0.0.1:8000', '/health', '/docs', '/base', 'BASE', '1.0.0', 'ACTIVE', 'HEALTHY', '统一网关、SSO 单点认证中心、PortalOS 平台桌面、用户角色权限与微服务生命周期治理', 0, NOW(), NOW()),
        (2, 'dreamclip-service', 'DreamClip 梦之厅业务微服务 (dreamclip-service)', 'PYTHON', 'http://127.0.0.1:8081', '/health', '/docs', '/dreamclip', 'UNIVERSE', '1.0.0', 'ACTIVE', 'HEALTHY', '沉浸式梦之厅官网、情绪胶囊切片流、AVG 互动剧场与 DreamClip Studio 独立内容工坊', 0, NOW(), NOW())
    """)
    
    cur.execute("DELETE FROM `magicstar_platform_db`.`sys_menu`;")
    cur.execute("""
        INSERT INTO `magicstar_platform_db`.`sys_menu`
        (id, parent_id, menu_name, menu_type, path, icon, service_code, sort_order, is_visible, is_deleted, created_at, updated_at)
        VALUES
        (1, 0, 'MagicStarPlatform 平台底座', 'APP', '/admin', '⭐', 'magicstar-platform', 1, 1, 0, NOW(), NOW()),
        (2, 0, 'DreamClip 梦之厅', 'APP', 'http://127.0.0.1:8081/', '🌌', 'dreamclip-service', 2, 1, 0, NOW(), NOW())
    """)
    
    cur.execute("SELECT id, role_code FROM `magicstar_platform_db`.`sys_role`;")
    role_map = {r['role_code']: r['id'] for r in cur.fetchall()}
    
    cur.execute("SELECT id, service_code FROM `magicstar_platform_db`.`sys_menu`;")
    menu_map = {r['service_code']: r['id'] for r in cur.fetchall()}
    
    cur.execute("DELETE FROM `magicstar_platform_db`.`sys_role_menu`;")
    role_menu_pairs = []
    if "ROLE_SUPER_ADMIN" in role_map:
        for m_id in menu_map.values():
            role_menu_pairs.append((role_map["ROLE_SUPER_ADMIN"], m_id))
    if "ROLE_OPERATOR" in role_map:
        for m_id in menu_map.values():
            role_menu_pairs.append((role_map["ROLE_OPERATOR"], m_id))
    if "ROLE_MEMBER" in role_map and "dreamclip-service" in menu_map:
        role_menu_pairs.append((role_map["ROLE_MEMBER"], menu_map["dreamclip-service"]))
        
    for r_id, m_id in role_menu_pairs:
        cur.execute("INSERT IGNORE INTO `magicstar_platform_db`.`sys_role_menu` (role_id, menu_id) VALUES (%s, %s)", (r_id, m_id))
    print("  - Microservices, menus, and role permissions normalized to magicstar-platform and dreamclip-service.")

    # 4. Migrate dreamclip_db (or mcp_universe_db) -> dreamclip_service_db
    source_business_db = None
    if "dreamclip_db" in all_dbs:
        source_business_db = "dreamclip_db"
    elif "mcp_universe_db" in all_dbs:
        source_business_db = "mcp_universe_db"
        
    if source_business_db:
        print(f"\n[Step 6] Migrating business data from {source_business_db} to dreamclip_service_db...")
        
        # 6.1 uc_worldviews
        cur.execute(f"SELECT * FROM `{source_business_db}`.`uc_worldviews`")
        wvs = cur.fetchall()
        for r in wvs:
            cur.execute("""
                INSERT INTO `dreamclip_service_db`.`uc_worldviews`
                (id, code, title, subtitle, summary, description, banner_url, icon_url, theme_color, tags, sort_order, is_active, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title=VALUES(title), summary=VALUES(summary), description=VALUES(description)
            """, (r['id'], r['code'], r['title'], r['subtitle'], r['summary'], r['description'], r['banner_url'], r['icon_url'], r['theme_color'], r['tags'], r['sort_order'], r['is_active'], r['is_deleted'], r['created_at'], r['updated_at']))
        print(f"  - uc_worldviews: migrated {len(wvs)} rows")
        
        # 6.2 uc_characters
        cur.execute(f"SELECT * FROM `{source_business_db}`.`uc_characters`")
        chars = cur.fetchall()
        for r in chars:
            import json
            details_val = json.dumps(r['details_json']) if isinstance(r['details_json'], (dict, list)) else r['details_json']
            cur.execute("""
                INSERT INTO `dreamclip_service_db`.`uc_characters`
                (id, worldview_id, code, name, title, tagline, personality_color, zodiac, avatar_url, illustration_url, bio, personality_desc, appearance_desc, details_json, sort_order, is_active, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name=VALUES(name), bio=VALUES(bio), details_json=VALUES(details_json)
            """, (r['id'], r['worldview_id'], r['code'], r['name'], r['title'], r['tagline'], r['personality_color'], r['zodiac'], r['avatar_url'], r['illustration_url'], r['bio'], r['personality_desc'], r['appearance_desc'], details_val, r['sort_order'], r['is_active'], r['is_deleted'], r['created_at'], r['updated_at']))
        print(f"  - uc_characters: migrated {len(chars)} rows")
        
        # 6.3 uc_emotion_capsules
        cur.execute(f"SELECT * FROM `{source_business_db}`.`uc_emotion_capsules`")
        capsules = cur.fetchall()
        for r in capsules:
            cur.execute("""
                INSERT INTO `dreamclip_service_db`.`uc_emotion_capsules`
                (id, worldview_id, character_id, title, slug, cover_image, summary, content_md, content_html, word_count, mood_tag, mood_color, reading_time_mins, view_count, like_count, is_featured, is_published, published_at, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title=VALUES(title), content_md=VALUES(content_md), content_html=VALUES(content_html)
            """, (r['id'], r['worldview_id'], r['character_id'], r['title'], r['slug'], r['cover_image'], r['summary'], r['content_md'], r['content_html'], r['word_count'], r['mood_tag'], r['mood_color'], r['reading_time_mins'], r['view_count'], r['like_count'], r['is_featured'], r['is_published'], r['published_at'], r['is_deleted'], r['created_at'], r['updated_at']))
        print(f"  - uc_emotion_capsules: migrated {len(capsules)} rows")
        
        # 6.4 uc_avg_chapters
        cur.execute(f"SELECT * FROM `{source_business_db}`.`uc_avg_chapters`")
        chapters = cur.fetchall()
        for r in chapters:
            cur.execute("""
                INSERT INTO `dreamclip_service_db`.`uc_avg_chapters`
                (id, worldview_id, character_id, chapter_code, chapter_name, chapter_no, cover_image, summary, game_url, playtime_mins, is_free, is_published, sort_order, is_deleted, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE chapter_name=VALUES(chapter_name), game_url=VALUES(game_url)
            """, (r['id'], r['worldview_id'], r['character_id'], r['chapter_code'], r['chapter_name'], r['chapter_no'], r['cover_image'], r['summary'], r['game_url'], r['playtime_mins'], r['is_free'], r['is_published'], r['sort_order'], r['is_deleted'], r['created_at'], r['updated_at']))
        print(f"  - uc_avg_chapters: migrated {len(chapters)} rows")
        
        # 6.5 uc_hall_banners (if in dreamclip_db)
        if source_business_db == "dreamclip_db":
            cur.execute("SELECT * FROM `dreamclip_db`.`uc_hall_banners`")
            banners = cur.fetchall()
            for r in banners:
                cur.execute("""
                    INSERT INTO `dreamclip_service_db`.`uc_hall_banners`
                    (id, title, subtitle, badge_text, image_url, link_url, theme_color, sort_order, is_active, is_deleted, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), image_url=VALUES(image_url), link_url=VALUES(link_url)
                """, (r['id'], r['title'], r['subtitle'], r['badge_text'], r['image_url'], r['link_url'], r['theme_color'], r['sort_order'], r['is_active'], r['is_deleted'], r['created_at'], r['updated_at']))
            print(f"  - uc_hall_banners: migrated {len(banners)} rows")

    # 5. Drop legacy MySQL databases
    print("\n[Step 7] Safely dropping legacy databases...")
    legacy_dbs = ["mcp_base_db", "mcp_universe_db", "dreamclip_db", "dreamclip_base_db", "dream_base_clip"]
    for ldb in legacy_dbs:
        if ldb in all_dbs:
            cur.execute(f"DROP DATABASE IF EXISTS `{ldb}`;")
            print(f"  🗑️ Dropped legacy database: {ldb}")
        else:
            print(f"  ℹ️ Database {ldb} not present, skipping.")

    # 6. Verify target databases
    cur.execute("SHOW DATABASES;")
    final_dbs = [r['Database'] for r in cur.fetchall()]
    print(f"\n[Step 8] Migration completed! Current databases: {final_dbs}")
    
    conn.close()

if __name__ == "__main__":
    run_migration()
