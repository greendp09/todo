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

st.set_page_config(
    page_title="할 일 관리",
    page_icon="✅",
    layout="centered",
)

st.markdown("""
<style>
  /* 전체 배경 */
  .stApp { background: #F0F2F7; }
  section[data-testid="stSidebar"] { display: none; }

  /* 카드 공통 */
  .card {
    background: #fff;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(26,29,39,.07), 0 1px 2px rgba(26,29,39,.04);
  }

  /* 진행률 레이블 */
  .prog-label {
    font-size: 12px; font-weight: 600;
    color: #7A8099; letter-spacing: .08em;
    text-transform: uppercase; margin-bottom: 14px;
  }
  .prog-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .prog-row:last-child { margin-bottom: 0; }
  .prog-name { font-size: 13px; font-weight: 500; color: #3D4358; width: 36px; flex-shrink: 0; }
  .prog-bar-bg { flex: 1; height: 7px; background: #E4E8F0; border-radius: 99px; overflow: hidden; }
  .prog-bar-fill { height: 100%; border-radius: 99px; }
  .prog-pct { font-size: 12px; font-weight: 600; color: #7A8099; width: 34px; text-align: right; }
  .prog-cnt { font-size: 11px; color: #7A8099; width: 46px; text-align: right; }

  /* 할 일 카드 */
  .task-card {
    background: #fff;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(26,29,39,.07);
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .task-card.done { opacity: .65; }
  .task-text { flex: 1; font-size: 15px; color: #1A1D27; line-height: 1.45; }
  .task-text.done { text-decoration: line-through; color: #7A8099; }
  .badge {
    display: inline-block;
    font-size: 11px; font-weight: 700;
    padding: 3px 9px; border-radius: 99px;
    letter-spacing: .02em;
  }

  /* 버튼 기본 스타일 재정의 */
  div[data-testid="stHorizontalBlock"] button {
    min-height: 44px !important;
  }

  /* 헤더 */
  .app-header { padding: 4px 0 8px; margin-bottom: 6px; }
  .app-title { font-size: 22px; font-weight: 800; color: #1A1D27; letter-spacing: -.03em; margin: 0; }
  .app-sub { font-size: 13px; color: #7A8099; margin: 2px 0 0; }
  .app-date { font-size: 12px; color: #7A8099; }

  /* Streamlit 기본 요소 조정 */
  .stTextInput > div > div > input { border-radius: 8px !important; }
  .stSelectbox > div > div { border-radius: 8px !important; }
  div[data-testid="stForm"] { background: #fff; border-radius: 12px; padding: 14px; box-shadow: 0 1px 3px rgba(26,29,39,.07); border: none; }
  div[data-testid="stForm"] > div { border: none !important; }
  .stCheckbox label { font-size: 14px !important; color: #3D4358 !important; }
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
    TASKS_FILE.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_task(text: str, category: str) -> None:
    text = text.strip()
    if not text:
        return
    task = {
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category,
        "done": False,
        "createdAt": time.time(),
        "updatedAt": time.time(),
    }
    st.session_state.tasks.append(task)
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


# ── 세션 상태 초기화 ───────────────────────────────────────────
def init_state() -> None:
    if "tasks" not in st.session_state:
        st.session_state.tasks = load_tasks()
    if "cat_filter" not in st.session_state:
        st.session_state.cat_filter = "전체"
    if "hide_done" not in st.session_state:
        st.session_state.hide_done = False
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "undo_task" not in st.session_state:
        st.session_state.undo_task = None
    if "undo_time" not in st.session_state:
        st.session_state.undo_time = 0.0


init_state()


# ── 진행률 계산 ────────────────────────────────────────────────
def calc_progress(tasks: list[dict], category: str) -> tuple[int, int, int]:
    subset = tasks if category == "전체" else [t for t in tasks if t["category"] == category]
    total = len(subset)
    done = sum(1 for t in subset if t["done"])
    pct = round(done / total * 100) if total else 0
    return pct, done, total


def render_progress_bar(label: str, pct: int, done: int, total: int, color: str) -> str:
    cnt_str = f"{done} / {total}" if total else "–"
    return f"""
    <div class="prog-row">
      <span class="prog-name">{label}</span>
      <div class="prog-bar-bg">
        <div class="prog-bar-fill" style="width:{pct}%; background:{color};"></div>
      </div>
      <span class="prog-pct">{pct}%</span>
      <span class="prog-cnt">{cnt_str}</span>
    </div>"""


# ── 헤더 ──────────────────────────────────────────────────────
now = datetime.now()
days = ["월", "화", "수", "목", "금", "토", "일"]
date_str = f"{now.year}. {now.month}. {now.day}. ({days[now.weekday()]})"

col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div class="app-header">
      <p class="app-title">할 일 관리</p>
      <p class="app-sub">Task Manager</p>
    </div>""", unsafe_allow_html=True)
with col_date:
    st.markdown(f'<p class="app-date" style="text-align:right;margin-top:18px">{date_str}</p>', unsafe_allow_html=True)


# ── 진행률 카드 ────────────────────────────────────────────────
tasks = st.session_state.tasks
bars_html = '<div class="card"><div class="prog-label">진행률</div>'

overall_pct, overall_done, overall_total = calc_progress(tasks, "전체")
bars_html += render_progress_bar("전체", overall_pct, overall_done, overall_total, "#2F6FEB")

for cat in CATEGORIES:
    pct, done, total = calc_progress(tasks, cat)
    bars_html += render_progress_bar(cat, pct, done, total, CAT_STYLE[cat]["bar"])

bars_html += "</div>"
st.markdown(bars_html, unsafe_allow_html=True)


# ── 할 일 추가 폼 ──────────────────────────────────────────────
with st.form("add_form", clear_on_submit=True):
    col_inp, col_cat, col_btn = st.columns([4, 1.5, 1])
    with col_inp:
        new_text = st.text_input(
            "할 일",
            placeholder="할 일을 입력하세요",
            label_visibility="collapsed",
            max_chars=200,
        )
    with col_cat:
        new_cat = st.selectbox(
            "카테고리",
            CATEGORIES,
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button("추가", use_container_width=True)

    if submitted:
        if new_text.strip():
            add_task(new_text, new_cat)
            st.rerun()
        else:
            st.warning("할 일 내용을 입력해주세요.", icon="⚠️")


# ── Undo 배너 ─────────────────────────────────────────────────
if st.session_state.undo_task and (time.time() - st.session_state.undo_time) < 5:
    undo_col, btn_col = st.columns([4, 1])
    with undo_col:
        st.info(f"「{st.session_state.undo_task['text']}」이(가) 삭제됐습니다.")
    with btn_col:
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
col_filter, col_hide = st.columns([3, 1])
with col_filter:
    filter_options = ["전체"] + CATEGORIES
    selected = st.radio(
        "필터",
        filter_options,
        index=filter_options.index(st.session_state.cat_filter),
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected != st.session_state.cat_filter:
        st.session_state.cat_filter = selected
        st.rerun()

with col_hide:
    hide_done = st.checkbox("완료 숨기기", value=st.session_state.hide_done)
    if hide_done != st.session_state.hide_done:
        st.session_state.hide_done = hide_done
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
        tid = task["id"]
        is_editing = st.session_state.editing_id == tid
        s = CAT_STYLE[task["category"]]

        if is_editing:
            # 수정 모드
            with st.container():
                st.markdown('<div style="background:#fff;border-radius:12px;padding:14px 16px;'
                            'margin-bottom:8px;box-shadow:0 1px 3px rgba(26,29,39,.07);">', unsafe_allow_html=True)
                e_col1, e_col2, e_col3, e_col4 = st.columns([4, 1.5, 0.8, 0.8])
                with e_col1:
                    edited_text = st.text_input(
                        "수정",
                        value=task["text"],
                        key=f"edit_input_{tid}",
                        label_visibility="collapsed",
                        max_chars=200,
                    )
                with e_col2:
                    edited_cat = st.selectbox(
                        "카테고리",
                        CATEGORIES,
                        index=CATEGORIES.index(task["category"]),
                        key=f"edit_cat_{tid}",
                        label_visibility="collapsed",
                    )
                with e_col3:
                    if st.button("저장", key=f"save_{tid}", use_container_width=True):
                        if edited_text.strip():
                            update_task(tid, text=edited_text.strip(), category=edited_cat)
                            st.session_state.editing_id = None
                            st.rerun()
                with e_col4:
                    if st.button("취소", key=f"cancel_{tid}", use_container_width=True):
                        st.session_state.editing_id = None
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 일반 모드
            badge_html = (
                f'<span class="badge" style="background:{s["bg"]};color:{s["color"]};">'
                f'{task["category"]}</span>'
            )
            text_cls = "task-text done" if task["done"] else "task-text"

            col_chk, col_text, col_badge, col_edit, col_del = st.columns([0.5, 4, 1, 0.6, 0.6])

            with col_chk:
                checked = st.checkbox(
                    "완료",
                    value=task["done"],
                    key=f"chk_{tid}",
                    label_visibility="collapsed",
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
