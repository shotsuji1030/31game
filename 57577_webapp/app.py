"""57577: one-player Japanese tanka card game (Streamlit)."""
from pathlib import Path
import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="31 | 短歌カードゲーム", page_icon="㉛", layout="wide")
st.markdown("""<style>
.stApp {background: #faf8f3; color: #29251f;}
.card {border: 1px solid #d9d1c4; border-radius: 8px; padding: 10px 6px;
text-align:center; background:white; min-height:60px; display:flex; flex-direction:column;
justify-content:center; gap:6px; box-shadow:0 2px 5px #0000000c;}
.card.five {background:#e9f3fa;} .card.seven {background:#fceee5;}
.kind {font-size:12px;color:#746b63;} .phrase {font-size:15px;font-weight:500; overflow-wrap:anywhere; color:#29251f;}
/* 選択状態を黒ではなく明るい青緑に統一 */
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
 background-color:#167d78 !important; color:#ffffff !important; border:2px solid #167d78 !important;
}
.stButton > button[kind="primary"]:hover {background-color:#11645f !important; color:#ffffff !important;}
.stButton > button[kind="secondary"] {background-color:#ffffff !important; color:#29251f !important; border:1px solid #bcb4aa !important;}
.stButton > button[kind="secondary"]:hover {border-color:#167d78 !important; color:#11645f !important;}
.stButton > button:disabled {opacity:.5 !important;}

/* ダウンロードボタン */
.stDownloadButton > button {
    background-color: #ffffff !important;
    color: #29251f !important;
    border: 1px solid #bcb4aa !important;
    border-radius: 10px !important;
}

.stDownloadButton > button:hover {
    background-color: #e9f3fa !important;
    color: #167d78 !important;
    border-color: #167d78 !important;
}

.stDownloadButton > button:active,
.stDownloadButton > button:focus {
    background-color: #d5ebe8 !important;
    color: #11645f !important;
}
</style>""", unsafe_allow_html=True)



FILE = Path(__file__).with_name('57577_cards.xlsx')
PATTERN = [5, 7, 5, 7, 7]
FIELD_COUNTS = {5: 5, 7: 5}

@st.cache_data(show_spinner=False)
def load_cards(path, mtime):
    decks = {}
    for n in (5, 7):
        df = pd.read_excel(path, sheet_name=f'{n}音カード', dtype=str)
        col = 'テキスト' if 'テキスト' in df.columns else df.columns[-1]
        vals = [str(v).strip() for v in df[col].dropna() if str(v).strip()]
        decks[n] = list(dict.fromkeys(vals))
    return decks

def start_game():
    source = load_cards(FILE, FILE.stat().st_mtime)
    if len(source[5]) < 2 + FIELD_COUNTS[5] or len(source[7]) < 3 + FIELD_COUNTS[7]:
        st.error('カード不足です。5音は5枚以上、7音は8枚以上必要です。')
        st.stop()
    decks = {n: random.sample(source[n], len(source[n])) for n in (5, 7)}
    hand = [decks[n].pop() for n in PATTERN]
    field = {n: [decks[n].pop() for _ in range(FIELD_COUNTS[n])] for n in (5, 7)}
    st.session_state.game = dict(decks=decks, hand=hand, field=field,
                                 selected_hand=None, selected_field=None,
                                 round=1, swaps=0, done=False)

def refresh_field(game):
    """Discard all current field cards and deal a fresh field from the decks."""
    for n in (5, 7):
        game['field'][n] = [game['decks'][n].pop()
                            for _ in range(min(FIELD_COUNTS[n], len(game['decks'][n])))]

def card_html(phrase, n):
    cls = 'five' if n == 5 else 'seven'
    import html
    return f'<div class="card {cls}"><div class="kind">{n}音</div><div class="phrase">{html.escape(phrase)}</div></div>'

#st.title('31')
#st.caption('短歌をつくろう。')
if not FILE.exists():
    st.error('57577_cards.xlsx が見つかりません。app.py と同じフォルダに置いてください。')
    st.stop()
try:
    load_cards(FILE, FILE.stat().st_mtime)
except Exception as exc:
    st.error(f'Excelを読み込めません: {exc}')
    st.stop()

if 'game' not in st.session_state:
    start_game()
g = st.session_state.game
with st.sidebar:
    st.header('あそびかた')
    st.write('① 手札を1枚選択  ② 同じ音数の場札を選択  ③ 交換ボタンを押す')
    if st.button('新しいゲーム', use_container_width=True):
        start_game()
        st.rerun()
    st.divider()
    st.write(f'ラウンド: **{g["round"]} / 2**')
    st.write(f'交換: **{g["swaps"]} / 3**')
    st.write(f'山札: 5音 {len(g["decks"][5])}枚 / 7音 {len(g["decks"][7])}枚')

st.subheader('あなたの短歌')
cols = st.columns(5)
for i, (n, phrase) in enumerate(zip(PATTERN, g['hand'])):
    with cols[i]:
        st.markdown(card_html(phrase, n), unsafe_allow_html=True)
        if not g['done']:
            selected = g['selected_hand'] == i
            if st.button('✓ 選択中' if selected else 'この札を選ぶ', key=f'hand_{i}',
                         type='primary' if selected else 'secondary', use_container_width=True):
                g['selected_hand'] = None if selected else i
                g['selected_field'] = None
                st.rerun()

if not g['done']:
    st.divider()
    st.subheader('場のカード')
    #st.caption('手札を選ぶと、交換可能な音数のカードを選べます。')
    chosen = g['selected_hand']
    allowed = PATTERN[chosen] if chosen is not None else None
    for n in (5, 7):
        st.markdown(f'**{n}音カード**')
        if not g['field'][n]:
            st.info('この音数の場札はありません。')
            continue
        cols = st.columns(FIELD_COUNTS[n])
        for j, phrase in enumerate(g['field'][n]):
            with cols[j]:
                st.markdown(card_html(phrase, n), unsafe_allow_html=True)
                selected = g['selected_field'] == (n, j)
                if st.button('✓ 選択中' if selected else '選ぶ', key=f'field_{n}_{j}',
                             disabled=allowed != n or g['swaps'] >= 3,
                             type='primary' if selected else 'secondary', use_container_width=True):
                    g['selected_field'] = None if selected else (n, j)
                    st.rerun()
    c1, c2 = st.columns(2)
    with c1:
        ready = chosen is not None and g['selected_field'] is not None and g['swaps'] < 3
        if st.button('選択したカードを交換', disabled=not ready, type='primary', use_container_width=True):
            n, j = g['selected_field']
            g['hand'][chosen], g['field'][n][j] = g['field'][n][j], g['hand'][chosen]
            # Exchanged-out card is removed from play rather than left in the field.
            g['field'][n].pop(j)
            # Refill the exact vacated slot with one fresh card of the same mora count.
            if g['decks'][n]:
                g['field'][n].insert(j, g['decks'][n].pop())
            g['selected_hand'] = None
            g['selected_field'] = None
            g['swaps'] += 1
            st.rerun()
    with c2:
        label = '短歌を完成させる' if g['round'] == 2 else '次のラウンドへ'
        if st.button(label, use_container_width=True):
            if g['round'] == 2:
                g['done'] = True
            else:
                g['round'] += 1
                g['swaps'] = 0
                refresh_field(g)
            g['selected_hand'] = None
            g['selected_field'] = None
            st.rerun()
    if g['swaps'] >= 3:
        st.info('このラウンドの交換は3回までです。次へ進んでください。')
else:
    st.success('短歌が完成しました！')
    poem = '\n'.join(g['hand'])
 
    st.download_button('短歌をテキスト保存', poem, file_name='57577_tanka.txt', mime='text/plain')
    if st.button('もう一度遊ぶ', type='primary'):
        start_game()
        st.rerun()
