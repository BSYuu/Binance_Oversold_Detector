import ccxt # 코인 거래소 API 불러오는 라이브러리
import talib # 보조지표 지원 라이브러리
import numpy as np # 배열 처리 라이브러리

# 데이터를 도면화 하기 위한 라이브러리
import plotly.graph_objs as go 
from plotly import tools
import plotly.offline as offline

# 시간 관련 라이브러리
from datetime import datetime
from time import sleep

# 쓰레드 사용 라이브러리
import threading

#gui 라이브러리
from tkinter import *

# Is_btn_start를 전역변수화 시킴. 실행 or 실행 취소 토크용 변수. 실행 버튼을 누르면 True가 되며 실행취소를 누르면 False가 됨
global Is_btn_start
global Is_second_API
global binance
Is_btn_start = False
Is_second_API = False

# 메인 프레임 함수
def main_frame(): 
    # 메인 프레임 생성. center배치 하도록 함. 테두리가 보이도록 설정  
    frame = Frame(root, relief="solid", bd=1)
    frame.pack(anchor="center")

    # 리스트박스 데이터가 많을 경우 scrollbar로 부분적으로 나누어 볼 수 있도록 공간 활용을 위해 scrollbar 설정
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side="right", fill="y") # 프레임의 가장 오른쪽에 배치.

    # 위 쪽에 년, 월, 일 데이터가 보이도록 time 값을 label로 설정하여 배치
    time = str(datetime.now().year) + "년 " + str(datetime.now().month) + "월 " + str(datetime.now().day) + "일"
    time_label = Label(frame, text=time)
    time_label.pack()

    # 리스트박스 생성. 다중 선택을 할 수 없도록 설정.
    # 스크롤 바와 연동 되도록 설정.
    global listbox
    listbox = Listbox(frame, selectmode="single", width=30, height=15, yscrollcommand=scrollbar.set)
    listbox.pack()
    scrollbar.config(command=listbox.yview)

    # 버튼 프레임 생성
    frame2 = Frame(root, relief="solid", bd=1, width=60)
    frame2.pack(anchor="center")

    # 실행 버튼 생성. cammand에 함수를 설정하여, 버튼 클릭 이벤트가 실행되면 cammand에 설정된 함수가 실행 됨
    btn_start = Button(frame2, text="실행", command=btncmd_start, height=2, width=32)
    btn_start.pack(fill="both")

    # 실행 취소 버튼 생성. cammand에 함수를 설정하여, 버튼 클릭 이벤트가 실행되면 cammand에 설정된 함수가 실행 됨
    btn_stop = Button(frame2, text="실행취소", command=btncmd_stop, height=2)
    btn_stop.pack(fill="both")

    # 차트 보기 버튼 생성. cammand에 함수를 설정하여, 버튼 클릭 이벤트가 실행되면 cammand에 설정된 함수가 실행 됨
    btn_chart = Button(frame2, text="차트보기", command=btncmd_chart, height=2)
    btn_chart.pack(fill="both")

# 실행 버튼 작동 시 호출되는 함수
def btncmd_start():
    global Is_btn_start

    # 버튼을 여러번 누를 때마다 중복 실행을 막기 위한 조건문. False 상태 일 때 작동되며, 그 후 True 상태가 됨
    if Is_btn_start == False:
        # 중지 하기 전까지 무한 반복을 하므로, 응답없음을 막기 위해 쓰레드를 따로 생성 
        t1 = threading.Thread(target=search_start)
        t1.start()      

    # 버튼 중복 실행을 막기 위해 한번 실행 후 True 상태로 변환    
    Is_btn_start = True

# 실행 중지 버튼 작동 시 호출되는 함수
def btncmd_stop():
    # 실행 중지 버튼이 눌러지면 True -> False 로 변환되어 다시 실행 버튼을 누를 수 있는 상태가 됨
    global Is_btn_start
    Is_btn_start = False

# 차트보기 버튼 작동 시 호출되는 함수
def btncmd_chart():
    # 리스트박스에 현재 선택되는게 없으면 작동이 되지 않도록 조건문 생성. Tuple 문으로 되어있으므로, 값이 없으면 빈 Tuple로 되어 있음.
    if listbox.curselection() != ():
        # 리스트박스에 현재 선택되어 있는 코인의 심볼 텍스트를 그대로 들고옴
        simbol = listbox.get(listbox.curselection())

        # 해당 심볼에 맞는 데이터를 코인 거래소 API에서 불러옴
        # 가격 정보(일자, 시가, 고가, 저가, 종가, 거래량)가 리스트로 저장
        # 첫번째 인자값은 거래종목 명의 텍스트 값, timeframe 은 시간 기준 값을 나타냄. 1h는 1시간 기준
        ohlcvs = binance.fetch_ohlcv(simbol, timeframe="1h")
        
        # 가격 정보 중 종가 값만을 불러와서 다시 리스트로 담음
        close_lst = [x[4] for x in ohlcvs]
        # 차트 데이터로 사용하기 위해 가격 정보들을 분리하여 저장할 리스트들을 따로 만듬
        x = []
        open = []
        high = []
        low = []
        close = []
        volume = []

        # 이동평균선 20일선의 데이터를 sma20 리스트에 저장. 이 때 talib 라이브러리를 활용하여 보조지표의 데이터를 뽑아옴.
        sma20 = talib.SMA(np.array(close_lst), timeperiod=20)
        # 이동평균선 20일선의 20%낮은 값을 다시 sma20_lower20 리스트에 저장
        sma20_lower20 = sma20 * 0.8

        # 차트 데이터로 사용하기 위해 가격 정보들을 따로 나누어서 저장
        for ohlcv in ohlcvs:
            # 가공되지 않은 시간데이터 값을 datetime을 이용하여 가공하여 저장. 차트의 X축인 시간값을 보기쉽게 출력하도록 가공함
            # 가격 정보(일자, 시가, 고가, 저가, 종가, 거래량)
            x.append(datetime.fromtimestamp(ohlcv[0]/1000).strftime('%Y-%m-%d %H:%M:%S')) 
            open.append(ohlcv[1])
            high.append(ohlcv[2]) 
            low.append(ohlcv[3])
            close.append(ohlcv[4])
            volume.append(ohlcv[5])

        # 캔들차트를 나타내기 위한 데이터 입력.
        price_trace = go.Candlestick(x=x, 
                                open=open, 
                                high=high, 
                                low=low, 
                                close=close,
                                name="가격")

        # 거래량차트를 나타내기 위한 데이터 입력. 거래량은 Bar차트
        volume_trace = go.Bar(x=x, 
                            y=volume,
                            name="거래량")
        # 이동평균선 20일선에서 20% 낮은 값을 선으로 표현하기 위한 데이터 입력 
        sma20_trace = go.Scatter(x=x, 
                                y=sma20_lower20, 
                                name="Envelope lower 20")

        # 캔틀차트와 이동평균선 보조지표는 같이 표출 시킴                     
        data = [price_trace, sma20_trace] 

        # 거래량은 따로 보여주기 위해 그리드를 위, 아래 2개 나누어 공간을 설정. 여기서 X축은 서로 공유하도록 함
        fig = tools.make_subplots(rows=2, cols=1, shared_xaxes=True)

        # 레이아웃의 타이틀 명을 설정
        layout = go.Layout(title=f"{simbol} 1시간 차트") 

        # 그리드 위에 data 리스트에 넣은 2개 차트를 배치
        for trace in data:
            fig.append_trace(trace, 1,1)

        # 그리드 아래부분에 거래량차트를 배치
        fig.append_trace(volume_trace, 2,1)

        # 가변 슬라이드 바 제거 
        fig.update_layout(xaxis_rangeslider_visible=False)   
       
        # 레이아웃 설정값과 모든 차트 설정 값을 합침
        f = go.Figure(data=fig, layout=layout)
        
        # 오프라인(HTML)로 출력
        offline.iplot(f)
        

# 응답없음을 피하기 위해 따로 쓰레드를 할당한 함수
def search_start():
    global Is_btn_start
    global Is_second_API
    global binance
    # 비교 프로그램을 5초마다 계속 무한 반복 진행
    while Is_btn_start:
        # 첫번째는 미리 API 데이터 추출을 했으므로, 다음 반복문 실행시에 재주출 할 수 있도록 하기 위한 조건문 
        if Is_second_API == True:
            # binance 거래소 API 데이터 재추출. 실시간으로 감지 하기 위함.
            binance = ccxt.binance()
            print("두번째 반복문 실행")
        Is_second_API = True

        # 모든 USDT 목록들을 하나씩 열어서 비교       
        for usdt in usdt_lst:
            # 실행 취소 버튼이 눌러지면 탈출
            if Is_btn_start == False:
                break

            # 해당 심볼에 맞는 데이터를 코인 거래소 API에서 불러옴
            # 가격 정보(일자, 시가, 고가, 저가, 종가, 거래량)가 리스트로 저장
            # 첫번째 인자값은 거래종목 명의 텍스트 값, timeframe 은 시간 기준 값을 나타냄. 1h는 1시간 기준
            ohlcvs = binance.fetch_ohlcv(usdt, timeframe="1h") 

            # 가격 정보 중 종가값만 뽑아내어 close_lst 리스트에 저장
            close_lst = [x[4] for x in ohlcvs]

            # 이동평균선 20일선 값을 종가값 기준으로 sma20 리스트에 저장
            sma20 = talib.SMA(np.array(close_lst), timeperiod=20)

            # 순간적인 과매도 포착을 위해 이동평균선 20일선 20%의 값을 낮춘 값. 즉 Envelope 하락 괴리율 20
            sma20_low20 = sma20[-1] * 0.9

            # 마지막 시점(최신 가격)이 Envelope lower 선에 터치 할 경우 감지 알람 표시
            if sma20_low20 >= ohlcvs[-1][4]:

                # 리스트박스에 감지 알람 중복을 방지하기 위한 조건문 설정
                if usdt in listbox.get(0, END):
                    continue
                else:
                    listbox.insert(END, f"{usdt}")
    
        # 1초 후에 다시 처음으로 반복    
        sleep(1)
      


# 여기서 부터 메인

# GUI생성. 타이틀 명, 창 크기 설정
root = Tk()
root.title("바이낸스 거래소 USDT 과매도 감지 프로그램")
root.geometry("260x400")
# 크기 조절 금지
root.resizable(False, False)

# binance 거래소 API 데이터 추출
binance = ccxt.binance()

# 거래소에서 지원하는 거래 목록들을 표시
markets = binance.fetch_tickers() 
usdt_lst = []

# USDT를 기준으로 거래하는 목록들만 필터링 하여 usdt_lst 리스트에 담음
for x in markets.keys(): 
    if 'USDT' in x:
        usdt_lst.append(x)

# 메인 프레임 생성
main_frame()

# GUI 실행 loop
root.mainloop()
