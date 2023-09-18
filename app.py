import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
from PIL import Image


# 前置作業
scopes = ["https://spreadsheets.google.com/feeds"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["cjson"], scopes)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(st.secrets["sheet_key"])
sheet_1 = spreadsheet.sheet1
usernames = [user for user in st.secrets["credential"]["usernames"].keys()]


# 取得投注資訊DataFrame
def get_bet_data(sheet):
  source = sheet.get_all_values()

  lotter_type = source[0][6]
  end_time = source[0][1]
  remain_time = source[1][1]
  draw_date = source[2][1]
  estimated_prize = int(source[2][3].replace(',', ''))
  co_info = source[31][0] + source[32][0]  # 新增成員需修改
  probability = source[30][8]  # 新增成員需修改

  col_index = [0, 1, 4, 5, 6, 7]
  member_index = [i for i in range(4,30)]  # 新增成員需修改
  columns = [source[3][i] for i in col_index]
  members = [[source[m][i] for i in col_index ] for m in member_index]
  index = [i for i in range(1,len(members)+1)]

  df = pd.DataFrame(members, index=index, columns=columns)
  source_data = {"df":df, "lotter_type":lotter_type, "end_time":end_time, "remain_time":remain_time, "draw_date":draw_date, "estimated_prize":estimated_prize, "co_info":co_info, "probability":probability}
  return source_data

## 取得會員資訊
def get_member_info(df, username, column):
  return df.loc[df.識別碼==username, column].values[0]


## 更新個人投注金額
def update_bet(sheet, row, bet):
  sheet.update(st.secrets["column_dict"]["投注金額"] + row, bet)


# 設定轉帳圖片
def set_img():
  img_url = st.secrets["img_url"]
  try:
    urllib.request.urlretrieve(img_url,"pay.jpg")
    image = Image.open("pay.jpg")
    img_caption = st.secrets["img_caption"]
    st.session_state.image = (image, img_caption)
    return st.session_state.image
  except:
    return None


# 確認是否可以登入
def check_login(username_, password_):
  if username_ not in usernames:
    return False
  if password_ == st.secrets["credential"]["usernames"][username_]["password"]:
    return True
  else:
    return False


# 初始化 session_state
if "login" not in st.session_state:
  st.session_state.login = False
if 'username' not in st.session_state:
  st.session_state.username = ""
if 'source_data' not in st.session_state:
  st.session_state.source_data = {}
if 'bet' not in st.session_state:
  st.session_state.bet = 0
if 'image' not in st.session_state:
    st.session_state.image = None


# 登入頁面
def login_page():
  lg_left, lg_middle, lg_right = st.columns((3, 2, 3))
  with lg_middle:
    st.title("登入頁面")
    username = st.text_input("請輸入工號")
    password = st.text_input("請輸入密碼", type="password")
    login_button = st.button("登入")

    if login_button:
      if check_login(username, password):
        st.success("Loading")
        st.session_state.login = True
        st.session_state.username = username
        st.session_state.source_data = get_bet_data(sheet_1)
        st.session_state.name = get_member_info(st.session_state.source_data["df"], st.session_state.username, "姓名")
        st.session_state.bet = int(get_member_info(st.session_state.source_data["df"], st.session_state.username, "投注金額"))
        set_img()
        st.experimental_rerun()
      else:
        st.error("帳號或密碼錯誤")


# 主頁面
def main_page():
  # backend
  lottery_type = st.session_state.source_data["lotter_type"]  # 威力彩/大樂透
  draw_date = st.session_state.source_data["draw_date"]    # 開獎日期
  end_time = st.session_state.source_data["end_time"]  # 結束下注時間
  estimated_prize = st.session_state.source_data["estimated_prize"]
  remain_time = st.session_state.source_data["remain_time"]
  co_info = st.session_state.source_data["co_info"]
  probability = st.session_state.source_data["probability"]

  name = st.session_state.name
  row = st.secrets["credential"]["usernames"][st.session_state.username]["row"]  # 寫入投注金額時，取得使用者列號用

  credit = get_member_info(st.session_state.source_data["df"], st.session_state.username, "可抵金")
  accum_arrears = get_member_info(st.session_state.source_data["df"], st.session_state.username, "累積未繳金額")
  paid = get_member_info(st.session_state.source_data["df"], st.session_state.username, "已繳金額")


  # front
  col_t1, col_t2, colt3 = st.columns((2, 5, 2))
  with col_t2:
    st.title(f"TPC{lottery_type}集資")

  col1, col2, col3, col4 = st.columns((4, 5, 5, 4))
  with col2:
    st.success("開獎日期：" + draw_date)
    st.info("結束下注時間：" + end_time)

  with col3:
    st.success("預估頭獎獎金：" + format(estimated_prize, ","))
    st.info("距離收單還有：" + remain_time)

  col5, col6, col7, col8, col9 = st.columns((20, 17, 17, 17, 20))
  with col6:
    st.write(f"已繳金額：{paid}")
  with col7:
    st.write(f"可抵金：{credit}")
  with col8:
    st.write(f"累積未繳金額：{accum_arrears}")

  left, middle, right = st.columns((2, 5, 2))

  with middle:
    st.error(f"{name}您好 確認投注金額後，請務必按「提交」")
    if 'bet_preview' not in st.session_state:
      st.session_state.bet_preview = int(st.session_state.source_data["df"].loc[st.session_state.source_data["df"].姓名== name,'投注金額'])
    bet_preview = st.slider("你想要投注的金額是：", min_value=0, max_value=2000, value=int(st.session_state.bet_preview), step=100, key=f"bet_slider_{st.session_state.username}")
    st.session_state.source_data["df"].loc[st.session_state.source_data["df"].姓名== name,'投注金額'] = bet_preview


  # backend
  if st.session_state.source_data["df"]['投注金額'].astype("float64").sum(axis=0) != 0:
    st.session_state.source_data["df"]['預估分得金額'] = ((st.session_state.source_data["df"]['投注金額'].astype("float64") * estimated_prize * 0.796)/ st.session_state.source_data["df"]['投注金額'].astype("float64").sum(axis=0))
    st.session_state.source_data["df"]['預估分得金額'] = st.session_state.source_data["df"]['預估分得金額'].astype(int)
  else:
    st.session_state.source_data["df"]['預估分得金額'] = 0

  # front
  with middle:
    st.write(f"預估頭獎開出機率：{probability}")
    st.title(f"您預估分的頭獎金額為：{format(st.session_state.source_data['df'].loc[st.session_state.source_data['df'].姓名==name, '預估分得金額'].values[0], ',')}")
    fig = px.bar(st.session_state.source_data["df"],x='投注金額',y='姓名', text='預估分得金額', orientation='h')
    fig.update_layout(height=550)
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[0, 2100])
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width = True)

    send = st.button("提交")
    if send:
      update_bet(sheet_1, row, bet_preview)
      st.session_state.bet = int(bet_preview)
      st.session_state.source_data = get_bet_data(sheet_1)
      send = False
      st.experimental_rerun()
    st.write(co_info)
    st.error(f"您目前的投注金額為：{st.session_state.bet}")

  if st.session_state.image != None:
    left_2, middle_2, right_2 = st.columns((2, 5, 2))
    with middle_2:
      st.image(st.session_state.image[0], caption=st.session_state.image[1])


# 主程式
def main():
  st.set_page_config(
    # 網頁標題
    page_title="TPC台灣彩券集資",
    # 網頁圖標
    page_icon="🤑", # st.image / random / emoji ("🐧" or ":penguin:")
    # 網頁介面的佈局寬度
    layout="wide", # centered
    # 側邊欄的顯示狀態
    initial_sidebar_state="collapsed") # expanded or auto(預設)

  if not st.session_state.login:
    login_page()
  else:
    main_page()


if __name__ == "__main__":
  main()

