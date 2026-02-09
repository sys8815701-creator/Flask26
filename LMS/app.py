# pip install flask
# 플라스크 : 파이썬으로 만든 DB 연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 공간
# app.py : 플라스크로 서버를 동작하기 위한 파일명 (기본 파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아 놓은 폴더 (e.g. html, css, js)
# templates : 동적 파일을 모아 놓은 폴더 (e.g. CRUD 화면, 레이아웃, index)
from flask import Flask, render_template, request, redirect, url_for, session
#                플라스크   프론트 연결     요청, 응답 / 주소 전달 / 주소 생성 / 상태 저장소
from LMS.common import Session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# session을 사용하기 위해 보안키 설정 (아무 문자열이나 입력)
# RuntimeError: The session is unavailable because no secret key was set.
# Set the secret_key on the application to something unique and secret.

@app.route('/login', methods=['GET','POST']) # http://localhost:5000/login
# methods : 웹의 동작을 관여한다.
# GET : URL 주소로 데이터를 처리한다. (e.g. 화면(HTML 렌더) 요청) => 보안상 좋지 않지만 속도가 빠르다.
# POST : BODY 영역에서 데이터를 처리한다. (e.g.화면에 있는 내용을 백엔드로 전달) => 보안상 좋고 대용량에서 많이 사용한다.

def login() :

    if request.method == 'GET': # 처음 접속하면 GET 방식으로 화면을 출력한다.
        return render_template('login.html') # GET 방식으로 요청하면 'login.html' 화면이 나온다.

    # login.html의 'action="/login" method="POST"'를 처리하는 코드
    # 'login.html'에서 넘어온 폼 데이터 : uid / upw
    uid = request.form.get('uid') # 요청한  폼 내용을 가져온다.
    upw = request.form.get('upw') # request  form    get

    conn = Session.get_connection() # 교사용 DB 접속용 객체

    try : # 예외 발생 가능성
        with conn.cursor() as cursor : # DB에 커서 객체를 사용한다.

            # 1회원 정보 조회
            sql = "SELECT id, name, uid, role  \
            FROM members WHERE uid = %s AND password = %s" # == uid와 pwd가 동일하면 'id, name, uid, role'를 가져온다.
            cursor.execute(sql, (uid, upw)) # 쿼리문 실행
            user = cursor.fetchone() # 쿼리 결과 1개를 가져오고 user 변수에 넣는다.

            if user : # 찾은 계정이 있으면 브라우저의 session 영역에 보관한다.
                session['user_id'] = user['id'] # 계정 일련번호 (회원번호)
                session['user_name'] = user['name'] # 계정 이름
                session['user_uid'] = user['uid']  # 계정 로그인명
                session['user_role'] = user['role']  # 계정 권한
                # session에 저장 완료
                # '브라우저에서 F12 => application 탭 => cookie 항목' 순서대로 클릭하면 session 객체가 보인다.
                # 이 session을 삭제하면 로그아웃 처리된다.
                return redirect(url_for('index'))
                # 처리 후 이동하는 경로 (http://localhost:/index)

            else : # 찾은 계정이 없다면?
                return "<script>alert('아이디나 비번이 틀렸습니다.');history.back();</script>"
            #                   경고창                               뒤로가기

    finally :
        conn.close() # DB 연결 종료


@app.route('/logout') # 기본 동작이 GET 방식이기 때문에, 'methods=['GET']' 생략 가능하다.
def logout() :

    session.clear()  # session 비우기
    return redirect(url_for('login'))# http://localhost:5000/login (GET 방식)

@app.route('/join', methods=['GET','POST']) # 회원가입용 함수
def join() : # http://localhost:5000/ GET 매서드(화면 출력) post(화면 폼 처리용)

    # GET 매서드인 경우
    if request.method == 'GET' :
        return render_template('join.html') # 로그인용 프론트로 보낸다.

    # POST 메서드인 경우 (폼으로 데이터가 넘어올 때 처리한다.)

    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name') # 폼에서 넘어온 값을 변수에 넣는다.

    conn = Session.get_connection() # DB 연결
    try : # 예외 발생 가능성
        with conn.cursor() as cursor :
            # 아이디 중복 확인
            cursor.execute("SELECT id FROM members WHERE id = %s", (uid,))

            if cursor.fetchone() :
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            # 회원 정보 저장 (role, active에는 기본값이 들어간다.)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!');location.href='/login';</script>"

    except Exception as e : # 예외 발생 시 실행문
        print(f"회원가입 에러: {e}")
        return "가입 중 오류가 발생했습니다. /n join 매서드를 확인하세요."

    finally : # 항상 실행문
        conn.close()

@app.route('/member/edit', methods = ['GET', 'POST'])
def member_edit() :

    if 'user_id' not in session : # session에 'user_id'가 없다면
        return redirect(url_for('login')) # 로그인 경로로 보낸다.

    # 있다면 DB 연결 시작
    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            if request.method == 'GET' :
                # 기존 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE uid = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user = user_info)
                #                       가장 중요한 포인트 / GET 요청 시 페이지  / 객체 전달용 코드

            # POST 요청 : 정보 업데이트
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw : # 비밀번호 입력 시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))

            else : # 이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_id'] = new_name # session 이름 정보도 업데이트
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"

    except Exception as e : # 예외 발생 시 실행문
        print(f"회원 정보 수정 에러 : {e}")
        return "회원 정보 수정 도중 오류가 발생하였습니다. /n member_edit 매서드를 확인하세요."

    finally : # 항상 실행문
        conn.close()

@app.route('/mypage') # http://localhost:5000/mypage
def mypage() :
    if 'user_id' not in session : # 로그인 상태인지 아닌지 확인
        return redirect(url_for('login')) # 로그인 상태가 아니라면 'http://localhost:5000/login'으로 보낸다.

    conn = Session.get_connection() # DB 연결

    try :
        with conn.cursor() as cursor :
            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()

            # 2. 내가 쓴 게시물 갯수 조회 (작성한 boards 테이블 활용)
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE id = %s", (session['user_id'],))
            board_count = cursor.fetchone()['board_count']
            #                    개수를 세서 'fetchone()'에 넣는다. => 'board_count' 이름으로 개수를 가지고 있다.

            return render_template('mypage.html', user = user_info, board_count = board_count)
            # 결과를 리턴한다.                         'mypage,html'에게 'user' 객체와 'board_count' 객체를 담아 보낸다.
            # 프론트에서 사용하려면 {{ user.??? }} , {{ board_count }}

    finally :
        conn.close()

@app.route('/') # url 생성용 코드 http://localhost:5000/ or http://192.168.0.???:5000
def index() :
    return render_template('main.html')
    # render_template 웹 브라우저로 보낼 파일명
    # 'templates' 라는 폴더에서 'main.html'을 찾아 보낸다.

if __name__ == '__main__' :

    app.run(host='0.0.0.0', port=5000, debug=True)
    # host = '0.0.0.0' : 누가 요청하든 응답하라
    # port = 5000 : 플라스크에서 사용하는 포트 번호
    # debug=True : 콘솔에서 디버그를 보겠다.
