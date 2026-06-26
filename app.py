import streamlit as st
import json
import uuid
import time
from pathlib import Path
from datetime import datetime

# ── 설정 ──────────────────────────────────────────────────────
TASKS_FILE = Path("tasks.json")
CATEGORIES = ["업무", "개인", "공부"]

CAT_STYLE = {
    "업무": {"bg": "#EBF1FD", "color": "#1A4DB8", "bar": "#3B82F6"},
    "개인": {"bg": "#E6F7EF", "color": "#0D6641", "bar": "#10B981"},
    "공부": {"bg": "#FEF7E0", "color": "#8A5F00", "bar": "#F59E0B"},
}

# ── 키워드 사전 ────────────────────────────────────────────────
# 우선순위 높은 순으로 나열 (앞에 있을수록 먼저 매칭)
KEYWORDS: dict[str, list[str]] = {
    "업무": [
        "회의", "미팅", "보고서", "보고", "기획", "발표", "프레젠테이션", "PPT",
        "프로젝트", "마감", "데드라인", "제안서", "계약", "출장", "메일", "이메일",
        "슬랙", "결재", "협업", "클라이언트", "고객", "업무", "작업", "태스크",
        "스프린트", "배포", "릴리즈", "코드리뷰", "PR", "면접", "채용", "인사",
        "연봉", "급여", "월급", "세금", "경비", "예산", "견적", "청구",
    ],
    "공부": [
        "공부", "강의", "과제", "시험", "학습", "강좌", "복습", "예습",
        "노트", "연습문제", "자격증", "어학", "영어", "수학", "토익", "토플",
        "수업", "강연", "세미나", "튜토리얼", "인강", "알고리즘", "leetcode",
        "독서", "책", "읽기", "논문", "리서치", "스터디",
    ],
    "개인": [
        "운동", "헬스", "요가", "러닝", "청소", "정리", "장보기", "마트",
        "요리", "병원", "약국", "가족", "친구", "여행", "산책", "취미",
        "영화", "드라마", "휴식", "쇼핑", "드라이브", "데이트", "생일",
        "결혼", "약속", "모임", "파티", "집안일", "빨래", "설거지", "청구서",
    ],
}


def classify_category(text: str) -> tuple[str, str]:
    """키워드 매칭으로 카테고리와 매칭된 키워드를 반환. 없으면 ('', '')."""
    text_lower = text.lower()
    for cat, keywords in KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return cat, kw
    return "", ""


# ── 페이지 설정 ────────────────────────────────────────────────
st.set_page_config(page_title="할 일 관리", page_icon="✅", layout="centered")

st.markdown("""
<style>
  .stApp { background: #F0F2F7; }
  section[data-testid="stSidebar"] { display: none; }

  .prog-label {
    font-size: 12px; font-weight: 600; color: #7A8099;
    letter-spacing: .08em; text-transform: uppercase; margin-bottom: 14px;
  }
  .prog-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .prog-row:last-child { margin-bottom: 0; }
  .prog-name { font-size: 13px; font-weight: 500; color: #3D4358; width: 36px; flex-shrink: 0; }
  .prog-bar-bg { flex: 1; height: 7px; background: #E4E8F0; border-radius: 99px; overflow: hidden; }
  .prog-bar-fill { height: 100%; border-radius: 99px; }
  .prog-pct { font-size: 12px; font-weight: 600; color: #7A8099; width: 34px; text-align: right; }
  .prog-cnt { font-size: 11px; color: #7A8099; width: 46px; text-align: right; }

  .card {
    background: #fff; border-radius: 12px; padding: 20px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(26,29,39,.07), 0 1px 2px rgba(26,29,39,.04);
  }
  .badge {
    display: inline-block; font-size: 11px; font-weight: 700;
    padding: 3px 9px; border-radius: 99px; letter-spacing: .02em;
  }
  .auto-chip {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12px; font-weight: 600;
    padding: 4px 10px; border-radius: 99px;
    border: 1.5px dashed;
    margin-bottom: 6px;
  }
  .task-text { font-size: 15px; color: #1A1D27; line-height: 1.45; }
  .task-text.done { text-decoration: line-through; color: #7A8099; }

  .app-title { font-size: 22px; font-weight: 800; color: #1A1D27; letter-spacing: -.03em; margin: 0; }
  .app-sub { font-size: 13px; color: #7A8099; margin: 2px 0 0; }
  .app-date { font-size: 12px; color: #7A8099; }

  div[data-testid="stForm"] { background: #fff; border-radius: 12px;
    padding: 14px; box-shadow: 0 1px 3px rgba(26,29,39,.07); border: none; }
  div[data-testid="stForm"] > div { border: none !important; }
</style>
""", unsafe_allow_html=True)


# ── 데이터 레이어 ──────────────────────────────────────────────
def load_tasks() -> list[dict]:
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_tasks(tasks: list[dict]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_task(text: str, category: str) -> None:
    text = text.strip()
    if not text:
        return
    st.session_state.tasks.append({
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category,
        "done": False,
        "createdAt": time.time(),
        "updatedAt": time.time(),
    })
    save_tasks(st.session_state.tasks)


def update_task(task_id: str, **fields) -> None:
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t.update(fields)
            t["updatedAt"] = time.time()
            break
    save_tasks(st.session_state.tasks)


def delete_task(task_id: str) -> dict | None:
    tasks = st.session_state.tasks
    idx = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if idx is None:
        return None
    removed = tasks.pop(idx)
    save_tasks(tasks)
    return removed


# ── 자동 분류 콜백 ─────────────────────────────────────────────
def on_input_change() -> None:
    text = st.session_state.get("new_task_text", "")
    cat, kw = classify_category(text)
    st.session_state.auto_cat = cat
    st.session_state.auto_kw = kw


# ── 세션 초기화 ────────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "tasks":      load_tasks(),
        "cat_filter": "전체",
        "hide_done":  False,
        "editing_id": None,
        "undo_task":  None,
        "undo_time":  0.0,
        "auto_cat":   "",
        "auto_kw":    "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── 진행률 ────────────────────────────────────────────────────
def calc_progress(tasks: list[dict], category: str) -> tuple[int, int, int]:
    subset = tasks if category == "전체" else [t for t in tasks if t["category"] == category]
    total = len(subset)
    done  = sum(1 for t in subset if t["done"])
    return (round(done / total * 100) if total else 0), done, total


def progress_bar_html(label: str, pct: int, done: int, total: int, color: str) -> str:
    cnt = f"{done} / {total}" if total else "–"
    return (
        f'<div class="prog-row">'
        f'<span class="prog-name">{label}</span>'
        f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%;background:{color};"></div></div>'
        f'<span class="prog-pct">{pct}%</span>'
        f'<span class="prog-cnt">{cnt}</span>'
        f'</div>'
    )


# ── 헤더 ──────────────────────────────────────────────────────
now  = datetime.now()
days = ["월", "화", "수", "목", "금", "토", "일"]
date_str = f"{now.year}. {now.month}. {now.day}. ({days[now.weekday()]})"

col_t, col_d = st.columns([3, 1])
with col_t:
    st.markdown('<div><p class="app-title">할 일 관리</p><p class="app-sub">Task Manager</p></div>',
                unsafe_allow_html=True)
with col_d:
    st.markdown(f'<p class="app-date" style="text-align:right;margin-top:18px">{date_str}</p>',
                unsafe_allow_html=True)


# ── 진행률 카드 ────────────────────────────────────────────────
tasks = st.session_state.tasks
html  = '<div class="card"><div class="prog-label">진행률</div>'
pct, done, total = calc_progress(tasks, "전체")
html += progress_bar_html("전체", pct, done, total, "#2F6FEB")
for cat in CATEGORIES:
    pct, done, total = calc_progress(tasks, cat)
    html += progress_bar_html(cat, pct, done, total, CAT_STYLE[cat]["bar"])
html += "</div>"
st.markdown(html, unsafe_allow_html=True)


# ── 할 일 입력 ────────────────────────────────────────────────
# 텍스트 입력 (폼 밖 — on_change로 실시간 자동 분류)
st.text_input(
    "할 일 입력",
    placeholder="할 일을 입력하세요  (키워드를 감지해 카테고리를 자동 분류합니다)",
    key="new_task_text",
    max_chars=200,
    label_visibility="collapsed",
    on_change=on_input_change,
)

# 자동 분류 결과 표시
auto_cat = st.session_state.auto_cat
auto_kw  = st.session_state.auto_kw
input_text = st.session_state.get("new_task_text", "")

if auto_cat and input_text.strip():
    s = CAT_STYLE[auto_cat]
    st.markdown(
        f'<div class="auto-chip" style="color:{s["color"]};border-color:{s["bar"]};background:{s["bg"]};">'
        f'✨ <strong>{auto_cat}</strong>으로 자동 분류&nbsp;'
        f'<span style="opacity:.7;font-weight:400;">· 키워드: {auto_kw}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# 카테고리 선택 + 추가 버튼
col_cat, col_btn = st.columns([2, 1])
with col_cat:
    default_idx = CATEGORIES.index(auto_cat) if auto_cat else 0
    chosen_cat = st.selectbox(
        "카테고리",
        CATEGORIES,
        index=default_idx,
        key="chosen_cat",
        label_visibility="collapsed",
    )
with col_btn:
    if st.button("추가", use_container_width=True, type="primary"):
        text = st.session_state.get("new_task_text", "").strip()
        if text:
            add_task(text, chosen_cat)
            # 입력 초기화
            st.session_state.new_task_text = ""
            st.session_state.auto_cat = ""
            st.session_state.auto_kw  = ""
            st.rerun()
        else:
            st.warning("할 일 내용을 입력해주세요.", icon="⚠️")


# ── Undo 배너 ─────────────────────────────────────────────────
if st.session_state.undo_task and (time.time() - st.session_state.undo_time) < 5:
    col_msg, col_undo = st.columns([4, 1])
    with col_msg:
        st.info(f"「{st.session_state.undo_task['text']}」이(가) 삭제됐습니다.")
    with col_undo:
        if st.button("되돌리기", use_container_width=True):
            restored = st.session_state.undo_task
            st.session_state.tasks.append(restored)
            st.session_state.tasks.sort(key=lambda t: t["createdAt"])
            save_tasks(st.session_state.tasks)
            st.session_state.undo_task = None
            st.rerun()
else:
    st.session_state.undo_task = None


# ── 필터 + 완료 숨기기 ─────────────────────────────────────────
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
col_filter, col_hide = st.columns([3, 1])
with col_filter:
    options  = ["전체"] + CATEGORIES
    selected = st.radio(
        "필터", options,
        index=options.index(st.session_state.cat_filter),
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected != st.session_state.cat_filter:
        st.session_state.cat_filter = selected
        st.rerun()
with col_hide:
    hide = st.checkbox("완료 숨기기", value=st.session_state.hide_done)
    if hide != st.session_state.hide_done:
        st.session_state.hide_done = hide
        st.rerun()


# ── 할 일 목록 ────────────────────────────────────────────────
cat_filter = st.session_state.cat_filter
visible = [t for t in tasks if cat_filter == "전체" or t["category"] == cat_filter]
if st.session_state.hide_done:
    visible = [t for t in visible if not t["done"]]

if not visible:
    st.markdown("""
    <div style="background:#fff;border-radius:12px;padding:48px 24px;text-align:center;
                box-shadow:0 1px 3px rgba(26,29,39,.07);margin-top:8px;">
      <div style="font-size:15px;font-weight:600;color:#3D4358;margin-bottom:4px;">할 일이 없습니다</div>
      <div style="font-size:13px;color:#7A8099;">위에서 새 할 일을 추가하면 진행률이 표시됩니다</div>
    </div>""", unsafe_allow_html=True)
else:
    for task in visible:
        tid        = task["id"]
        is_editing = st.session_state.editing_id == tid
        s          = CAT_STYLE[task["category"]]

        if is_editing:
            with st.container():
                st.markdown(
                    '<div style="background:#fff;border-radius:12px;padding:14px 16px;'
                    'margin-bottom:8px;box-shadow:0 1px 3px rgba(26,29,39,.07);">',
                    unsafe_allow_html=True,
                )
                e1, e2, e3, e4 = st.columns([4, 1.5, 0.8, 0.8])
                with e1:
                    edited_text = st.text_input(
                        "수정", value=task["text"],
                        key=f"edit_input_{tid}", label_visibility="collapsed", max_chars=200,
                    )
                with e2:
                    edited_cat = st.selectbox(
                        "카테고리", CATEGORIES,
                        index=CATEGORIES.index(task["category"]),
                        key=f"edit_cat_{tid}", label_visibility="collapsed",
                    )
                with e3:
                    if st.button("저장", key=f"save_{tid}", use_container_width=True):
                        if edited_text.strip():
                            update_task(tid, text=edited_text.strip(), category=edited_cat)
                            st.session_state.editing_id = None
                            st.rerun()
                with e4:
                    if st.button("취소", key=f"cancel_{tid}", use_container_width=True):
                        st.session_state.editing_id = None
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            badge_html = (
                f'<span class="badge" style="background:{s["bg"]};color:{s["color"]};">'
                f'{task["category"]}</span>'
            )
            text_cls = "task-text done" if task["done"] else "task-text"

            col_chk, col_text, col_badge, col_edit, col_del = st.columns([0.5, 4, 1, 0.6, 0.6])

            with col_chk:
                checked = st.checkbox(
                    "완료", value=task["done"],
                    key=f"chk_{tid}", label_visibility="collapsed",
                )
                if checked != task["done"]:
                    update_task(tid, done=checked)
                    st.rerun()

            with col_text:
                st.markdown(
                    f'<div style="padding:10px 0;"><span class="{text_cls}">{task["text"]}</span></div>',
                    unsafe_allow_html=True,
                )

            with col_badge:
                st.markdown(
                    f'<div style="padding:10px 0;">{badge_html}</div>',
                    unsafe_allow_html=True,
                )

            with col_edit:
                if st.button("✏️", key=f"edit_{tid}", help="수정", use_container_width=True):
                    st.session_state.editing_id = tid
                    st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_{tid}", help="삭제", use_container_width=True):
                    removed = delete_task(tid)
                    if removed:
                        st.session_state.undo_task = removed
                        st.session_state.undo_time = time.time()
                    st.rerun()
