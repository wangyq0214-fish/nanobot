"""Seed script: create a gardening homework with test submissions (Chinese)."""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"
COURSE_ID = "ccfd35a21262"

QUESTIONS = [
    {
        "id": "q1", "type": "choice", "points": 10, "answer": "B",
        "content": "以下哪种植物属于一年生花卉？",
        "options": [
            {"key": "A", "text": "月季"},
            {"key": "B", "text": "向日葵"},
            {"key": "C", "text": "牡丹"},
            {"key": "D", "text": "菊花"},
        ],
    },
    {
        "id": "q2", "type": "choice", "points": 10, "answer": "C",
        "content": "植物进行光合作用的主要器官是？",
        "options": [
            {"key": "A", "text": "根"},
            {"key": "B", "text": "茎"},
            {"key": "C", "text": "叶"},
            {"key": "D", "text": "花"},
        ],
    },
    {
        "id": "q3", "type": "true_false", "points": 10, "answer": "false",
        "content": "多肉植物需要每天浇水。",
    },
    {
        "id": "q4", "type": "true_false", "points": 10, "answer": "true",
        "content": "堆肥可以改善土壤结构和肥力。",
    },
    {
        "id": "q5", "type": "choice", "points": 10, "answer": "A",
        "content": "以下哪种肥料属于有机肥？",
        "options": [
            {"key": "A", "text": "腐熟鸡粪"},
            {"key": "B", "text": "尿素"},
            {"key": "C", "text": "磷酸二铵"},
            {"key": "D", "text": "硫酸钾"},
        ],
    },
    {
        "id": "q6", "type": "short_answer", "points": 25,
        "content": "请简述植物扦插繁殖的基本步骤和注意事项。",
    },
    {
        "id": "q7", "type": "short_answer", "points": 25,
        "content": "描述三种常见的植物病虫害及其防治方法。",
    },
]

STUDENTS = [
    {
        "student_id": "W",
        "answers": {
            "q1": "B", "q2": "C", "q3": "false", "q4": "true", "q5": "A",
            "q6": "选取健壮枝条，长度约10-15厘米，保留2-3个芽点，下端斜切45度，插入湿润沙土中，保持温度20-25℃，避免阳光直射，约2-3周可生根。注意消毒工具，防止感染。",
            "q7": "1.蚜虫：可用肥皂水或吡虫啉喷洒防治。2.白粉病：保持通风透光，使用多菌灵或甲基托布津喷施。3.红蜘蛛：增加空气湿度，使用阿维菌素或哒螨灵喷杀。",
        },
    },
    {
        "student_id": "student_li",
        "answers": {
            "q1": "B", "q2": "C", "q3": "true", "q4": "true", "q5": "B",
            "q6": "扦插步骤：1.选择健康枝条 2.修剪保留2-3节 3.蘸生根粉 4.插入基质 5.覆盖保湿。注意保持湿度和温度适宜。",
            "q7": "蚜虫用吡虫啉杀虫剂防治，白粉病用多菌灵杀菌剂防治，红蜘蛛可以用水冲洗叶片背面。",
        },
    },
    {
        "student_id": "student_zhang",
        "answers": {
            "q1": "A", "q2": "D", "q3": "false", "q4": "true", "q5": "A",
            "q6": "选取半木质化枝条，保留顶部2-3片叶，插入珍珠岩和泥炭混合基质，覆盖保鲜膜保湿，每天通风一次。注意：工具需消毒，切口要平整，避免积水导致腐烂。",
            "q7": "1.蚜虫：物理清除（水冲）+ 生物防治（释放瓢虫）。2.根腐病：控制浇水频率，用甲基托布津灌根处理。3.介壳虫：用牙签或软刷刮除，喷施噻嗪酮或矿物油。",
        },
    },
]


async def main():
    engine = create_async_engine(DB_URL)
    hw_id = "hw" + uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=14)

    async with engine.connect() as conn:
        # Create missing student users
        for uid, name in [("student_li", "李同学"), ("student_zhang", "张同学")]:
            await conn.execute(
                text(
                    "INSERT INTO users (user_id, role, display_name, password_hash, password_salt) "
                    "VALUES (:uid, 'student', :name, 'seed_hash', 'seed_salt') ON CONFLICT DO NOTHING"
                ),
                {"uid": uid, "name": name},
            )
            await conn.execute(
                text(
                    "INSERT INTO course_members (course_id, user_id, user_role, display_name) "
                    "VALUES (:cid, :uid, 'student', :name) ON CONFLICT DO NOTHING"
                ),
                {"cid": COURSE_ID, "uid": uid, "name": name},
            )

        # Insert homework
        await conn.execute(
            text(
                "INSERT INTO homework "
                "(hw_id, course_id, title, description, total_points, deadline, created_by, settings, created_at) "
                "VALUES (:hw_id, :course_id, :title, :description, :total_points, :deadline, :created_by, CAST(:settings AS jsonb), :created_at)"
            ),
            {
                "hw_id": hw_id,
                "course_id": COURSE_ID,
                "title": "园艺基础知识测验",
                "description": "本次作业涵盖花卉分类、植物生理、栽培技术、病虫害防治等内容，请认真作答。",
                "total_points": 100,
                "deadline": deadline,
                "created_by": "teacher",
                "settings": json.dumps({"questions": QUESTIONS}, ensure_ascii=False),
                "created_at": now,
            },
        )

        # Insert submissions
        for i, s in enumerate(STUDENTS):
            sub_time = now - timedelta(hours=24 - i * 6)
            await conn.execute(
                text(
                    "INSERT INTO submissions "
                    "(hw_id, student_id, student_role, course_id, attempt_number, answers, status, score, feedback, submitted_at) "
                    "VALUES (:hw_id, :student_id, 'student', :course_id, 1, CAST(:answers AS jsonb), 'submitted', 0, CAST(:feedback AS jsonb), :submitted_at)"
                ),
                {
                    "hw_id": hw_id,
                    "student_id": s["student_id"],
                    "course_id": COURSE_ID,
                    "answers": json.dumps(s["answers"], ensure_ascii=False),
                    "feedback": "{}",
                    "submitted_at": sub_time,
                },
            )

        await conn.commit()

    await engine.dispose()
    print(f"作业 ID  : {hw_id}")
    print(f"作业标题 : 园艺基础知识测验")
    print(f"题目数量 : {len(QUESTIONS)} 题（3选择 + 2判断 + 2简答）")
    print(f"总分     : 100 分")
    print(f"提交人数 : {len(STUDENTS)} 人（W、李同学、张同学）")


if __name__ == "__main__":
    asyncio.run(main())
