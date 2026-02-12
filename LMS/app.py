# pip install flask
# 플라스크 : 파이썬으로 만든 DB 연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 공간
# app.py : 플라스크로 서버를 동작하기 위한 파일명 (기본 파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아 놓은 폴더 (e.g. html, css, js)
# templates : 동적 파일을 모아 놓은 폴더 (e.g. CRUD 화면, 레이아웃, index)

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
#                플라스크   프론트 연결    요청, 응답 / 주소 전달 / 주소 생성 / 상태 저장소

import os
from LMS.common import Session
from LMS.domain import Board, Score
from LMS.service import PostService

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# session을 사용하기 위해 보안키 설정 (아무 문자열이나 입력)
# RuntimeError: The session is unavailable because no secret key was set.
# Set the secret_key on the application to something unique and secret.

@app.route('/login', methods=['GET','POST']) # http://localhost:5000/login
# methods : 웹의 동작을 관여한다.
# GET : URL 주소로 데이터를 처리한다. (e.g. 화면(HTML 렌더) 요청) => 보안상 좋지 않지만 속도가 빠르다.
# POST : BODY 영역에서 데이터를 처리한다. (e.g.화면에 있는 내용을 백엔드로 전달) => 보안상 좋고 대용량에서 많이 사용한다.

# ----------------------------------------------------------------------------------------------------------------------
#                                                 회원 CRUD
# ----------------------------------------------------------------------------------------------------------------------

# 로그인
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
                return "<script>alert('아이디 혹은 비번이 틀렸습니다.');history.back();</script>"
            #                   경고창                               뒤로가기

    finally :
        conn.close() # DB 연결 종료

# 로그아웃
@app.route('/logout') # 기본 동작이 GET 방식이기 때문에, 'methods=['GET']' 생략 가능하다.
def logout() :

    session.clear()  # session 비우기
    return redirect(url_for('login'))# http://localhost:5000/login (GET 방식)

# 회원가입
@app.route('/join', methods=['GET','POST'])
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
            cursor.execute("SELECT id FROM members WHERE Uid = %s", (uid,))

            if cursor.fetchone() :
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            # 회원 정보 저장 (role, active에는 기본값이 들어간다.)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!');location.href='/login';</script>"

    except Exception as e : # 예외 발생 시 실행문
        print(f"회원가입 에러: {e}")
        return "회원가입 도중 오류가 발생했습니다. /n join 매서드를 확인하세요."

    finally : # 항상 실행문
        conn.close()

# 회원 정보 수정
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
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
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
            session['user_name'] = new_name # session 이름 정보도 업데이트
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"

    except Exception as e : # 예외 발생 시 실행문
        print(f"회원 정보 수정 에러 : {e}")
        return "회원 정보 수정 도중 오류가 발생하였습니다. /n member_edit 매서드를 확인하세요."

    finally : # 항상 실행문
        conn.close()

# 마이페이지
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
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (session['user_id'],))
            board_count = cursor.fetchone()['board_count']
            #                    개수를 세서 'fetchone()'에 넣는다. => 'board_count' 이름으로 개수를 가지고 있다.

            return render_template('mypage.html', user = user_info, board_count = board_count)
            # 결과를 리턴한다.                         'mypage,html'에게 'user' 객체와 'board_count' 객체를 담아 보낸다.
            # 프론트에서 사용하려면 {{ user.??? }} , {{ board_count }}

    finally :
        conn.close()

# 마이페이지 - 성적 확인
@app.route('/score/my')
def score_my() :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 내 id로만 조회
            sql = "SELECT * FROM scores WHERE member_id = %s"
            cursor.execute(sql, (session['user_id'],))
            row = cursor.fetchone()
            print(row) # dict 타입으로 결과물이 출력된다.

            # Score 객체로 변환 (from_db 활용)
            score = Score.from_db(row) if row else None

            return render_template('score_my.html', score = score)

    finally :
        conn.close()

# 마이페이지 - 작성한 게시물 조회
@app.route('/board/my')  # http://localhost:5000/board/my
def my_board_list() :
    if 'user_id' not in session :
        return redirect(url_for('login'))

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 내가 쓴 글만 조회 (작성자 이름 포함)
            sql = """
                  SELECT b.*, m.name as writer_name
                  FROM boards b
                  JOIN members m ON b.member_id = m.id
                  WHERE b.member_id = %s
                  ORDER BY b.id DESC
                  """
            cursor.execute(sql, (session['user_id'],))
            rows = cursor.fetchall()

            # 기존 Board 도메인 객체 활용
            boards = [Board.from_db(row) for row in rows]

            # 기존 board_list.html을 재사용하거나 전용 페이지를 만듭니다.
            # 여기서는 '내 글 관리'라는 느낌을 주도록 새로운 제목과 함께 보냅니다.
            return render_template('board_list.html', boards=boards, list_title="내가 작성한 게시물")

    finally :
        conn.close()

# ----------------------------------------------------------------------------------------------------------------------
#                                                 게시판 CRUD
# ----------------------------------------------------------------------------------------------------------------------

# 게시물 작성
@app.route('/board/write', methods = ['GET', 'POST']) # http://localhost:5000/board/write
def board_write() :

    # 1. 사용자가 '게시물 작성' 버튼을 눌러서 들어왔을 때 (화면 보여주기)
    if request.method == 'GET' :
        if 'user_id' not in session :
            return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'
        return render_template('board_write.html')

    # 2. 사용자가 '등록하기' 버튼을 눌러서 데이터를 보냈을 때 (DB 저장)
    elif request.method == 'POST' : # <form action="/board/write" method = "POST">

        title = request.form.get('title')
        content = request.form.get('content')

        # session에 저장된 로그인 유저의 id (member_id)
        member_id = session.get('user_id')
        conn = Session.get_connection()

        try :
            with conn.cursor() as cursor :

                sql = "INSERT INTO boards (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (member_id, title, content))
                conn.commit()

            return redirect(url_for('board_list')) # 저장 후 게시물 목록으로 이동한다.

        except Exception as e :
            print(f"게시물 작성 에러 : {e}")
            return "작성된 게시물을 저장하는 도중 에러가 발생하였습니다."

        finally :
            conn.close()

# 게시물 목록
@app.route('/board') # http://localhost:5000/board
def board_list() :

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            sql = """
                  SELECT b.*, m.name as writer_name
                  FROM boards b
                  JOIN members m ON b.member_id = m.id
                  ORDER BY b.id DESC
                  """

            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html', boards = boards)
            # render_template : html에 객체 보낼 때

    finally :
        conn.close()

# 게시물 자세히 보기
@app.route('/board/view/<int:board_id>') # http://localhost:5000/board/view/n (게시물 번호)
def board_view(board_id) :

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # JOIN을 통해 작성자 정보(e.g. name, uid)를 함께 조회한다.
            sql = """
                  SELECT b.*, m.name as writer_name, m.uid as writer_uid
                  FROM boards b
                  JOIN members m ON b.member_id = m.id
                  WHERE b.id = %s
                  """

            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()

            if not row :
                return "<script>alert('존재하지 않는 게시물입니다.');'history.back();</script>"

            # Board 객체로 변환한다. (앞서 작성한 'Board.py'의 'from_db'를 활용)
            board = Board.from_db(row)
            return render_template('board_view.html', board = board)

    finally :
        conn.close()

# 게시물 수정
@app.route('/board/edit/<int:board_id>', methods = ['GET', 'POST']) # http://localhost:5000/board/edit/n (게시물 번호)
def board_edit(board_id) :

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 1. 화면 보여주기 (기존 데이터 로드)
            if request.method == 'GET' :

                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()

                if not row :
                    return "<script>alert('존재하지 않는 게시물입니다.');'history.back();</script>"

                # 본인 확인 로직 (필요 시 추가)
                if row['member_id'] == session.get('user_id') :
                    return "<script>alert('수정 권한이 없습니다.');'history.back();</script>"
                print(row) # 콘솔에 출력 테스트용
                board = Board.from_db(row)
                return render_template('board_edit.html', board = board)

            # 2. 실제 DB 업데이트 처리
            elif request.method == 'POST' :

                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()

                return redirect(url_for('board_view', board_id = board_id))

    finally :
        conn.close()

# 게시물 삭제
@app.route('/board/delete/<int:board_id>')
def board_delete(board_id) :

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            sql = "DELETE FROM boards WHERE id = %s"
            cursor.execute(sql, (board_id,))
            conn.commit()

            if cursor.rowcount > 0 :
                print(f"[{board_id}]번 게시물 삭제 성공")

            else :
                return "<script>alert('삭제할 게시물이 없거나 권한이 없습니다.');'history.back();</script>"

        return redirect(url_for('board_list'))

    except Exception as e :
        print(f"게시물 삭제 에러 : {e}")
        return "게시물 삭제 도중 오류가 발생하였습니다."

    finally :
        conn.close()

# ----------------------------------------------------------------------------------------------------------------------
#                                                 성적 CRUD
# ----------------------------------------------------------------------------------------------------------------------

# 주의사항 : 'ADMIN'과 'MANAGER'에게만 CUD를 제공한다.
# 일반 사용자의 ROLE은 USER이고, 본인의 성적만 조회할 수 있다.

# 성적 입력
@app.route('/score/add') # http://localhost:5000/score/add?uid=test1&name=test1
def score_add() :
    if session.get('user_role') not in ('admin', 'manager') :
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    target_uid = request.args.get('uid') # args : url(주소)를 통해 전달되는 값 => 주소 뒤에 '?k=v&k=v' 형식
    target_name = request.args.get('name')

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 1. 대상 학생의 id 조회
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()

            # 2. 기존 성적이 존재하는지 조회
            existing_score = None

            if student :
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (student['id'],))
                row = cursor.fetchone()

                if row :

                    # 기존에 만들었던 'Score.from_db' 활용
                    existing_score = Score.from_db(row)
                    # 위쪽에 객체 로드 처리 => from LMS.domain import Board, Score

            return render_template('score_form.html', # render_template : html에 전달
                                   target_uid = target_uid,
                                   target_name = target_name,
                                   score = existing_score) # score 객체 전달

    finally :
        conn.close()

# 성적 저장
@app.route('/score/save', methods = ['POST'])
def score_save() :

    if session.get('user_role') not in ('admin', 'manager') :
        return "권한 오류", 403 # 오류 페이지로 교체

    # 폼 데이터 수집
    target_uid = request.form.get('target_uid')
    kor = int(request.form.get('korean', 0))
    eng = int(request.form.get('english', 0))
    math = int(request.form.get('math', 0))

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 1. 대상 학생의 id(PK) 조회 => 학생의 번호를 가져온다.
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()
            print(student) # 학번 출력

            # 존재하지 않는 경우
            if not student :
                return "<script>alert('존재하지 않는 학생입니다.');history.back();</script>"

            # 2. Score 객체 생성 (계산 프로퍼티 활용)
            temp_score = Score(member_id = student['id'], kor = kor, eng = eng, math = math)
            #            '__init__'을 활용하여 객체 생성

            # 3. 학번(student)을 활용하여 기존 데이터가 존재하는지 확인
            cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))
            is_exist = cursor.fetchone() # 성적이 존재하면 id, 없으면 None

            if is_exist :

                # UPDATE 실행
                sql = """
                      UPDATE scores SET korean = %s, english = %s, math = %s,
                                        total = %s, average = %s, grade =  %s
                      WHERE member_id = %s
                      """

                cursor.execute(sql,(temp_score.kor, temp_score.eng, temp_score.math,
                                    temp_score.total, temp_score.avg, temp_score.grade,
                                    student['id']))

            else :

                # INSERT 실행
                sql = """
                      INSERT INTO scores (member_id, korean, english, math, total, average, grade)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)
                      """

                cursor.execute(sql, (student['id'], temp_score.kor, temp_score.eng, temp_score.math,
                                     temp_score.total, temp_score.avg, temp_score.grade))

            conn.commit()
            return f"<script>alert('{target_uid} 학생의 성적 입력이 완료되었습니다.');location.href='/score/list';</script>"

    finally :
        conn.close()

# 성적 조회
@app.route('/score/list') # http://localhost:5000/score/list
def score_list() :

    # 1. 권한 체크 (관리자나 매니저만 볼 수 있게 설정)
    if session.get('user_role') not in ('admin', 'manager') :
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 2. JOIN을 사용하여 학생 이름(name)과 성적 데이터를 함께 조회
            # 성적이 없는 학생은 제외하고, 성적이 있는 학생들만 총점 순으로 정렬

            sql = """
                  SELECT m.name, m.uid, s.* FROM scores s
                  JOIN members m ON s.member_id = m.id
                  ORDER BY s.total DESC
                  """

            cursor.execute(sql)
            datas = cursor.fetchall()
            print(f"sql 결과 테스트 : {datas}")

            # 3. DB에서 가져온 딕셔너리 리스트를 Score 객체 리스트로 변환
            score_objects = []
            for data in datas :

                # Score 클래스에 정의한 'from_db' 활용
                s = Score.from_db(data) # 직렬화 (dict 타입 => 객체)
                # 문자열은 주소가 없기 때문에, 주소인 객체로 만들어 줘야 한다.
                # 객체에 없는 이름(name) 정보는 수동으로 넣기 (JOIN에서 만든 값 활용)
                s.name = data['name']
                s.uid = data['uid']
                score_objects.append(s) # 객체(주소)를 리스트에 넣는다.

            return render_template('score_list.html', scores = score_objects)
            #                        프론트 화면 ui에                  성적이 담긴 리스트 객체를 전달한다.

    finally :
        conn.close()

# 성적 입력 (member 테이블 기반)
@app.route('/score/members')
def score_members() :

    if session.get('user_role') not in ('admin', 'manager') :
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # LEFT JOIN을 통해 성적이 있으면 's.id'를 숫자, 없으면 NULL 처리한다.
            sql = """
                  SELECT m.id, m.uid, m.name, s.id AS score_id
                  FROM members m
                  LEFT JOIN scores s ON m.id = s.member_id
                  WHERE m.role = 'user'
                  ORDER BY m.name ASC
                  """

            cursor.execute(sql)
            members = cursor.fetchall()
            return render_template('score_member_list.html', members = members)

    finally :
        conn.close()

# ----------------------------------------------------------------------------------------------------------------------
#                                              자료실 (파일 업로드)
# ----------------------------------------------------------------------------------------------------------------------

# 1. 파일 업로드 / 다운로드
# 2. 단일 파일 / 다중 파일 업로드 처리
# 3. 서비스 패키지 활용
## 4. '/upload' 폴더 사용 (용량 제한 : 16MB)
# 5. 파일명 중복 방지용 코드 활용
# 6. DB에서 부모 객체가 삭제되면 자식 객체도 삭제 처리 (CASCADE)

# 파일 처리 경로
UPLOAD_FOLDER = 'uploads/'
# 폴더 부재 시 자동 생성
if not os.path.exists(UPLOAD_FOLDER) : # 'import os' 상단에 추가
    os.makedirs(UPLOAD_FOLDER) # os.makedirs(경로) : 폴더 생성용 코드

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 최대 용량 제한 (e.g. 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# bit : 0, 1
# 1 byte == 8 bit => 0 ~ 255 (총 256개)
# 1 KB == 1024 byte
# 1 MB == 1024 Kbyte
# 1 GB == 1024 Mbyte
# 1 TB == 1024 Gbyte
# 1 PB == 1024 Tbyte
# 1 XB == 1024 Pbyte

# 파일 게시판 - 작성
@app.route('/filesboard/write', methods = ['GET', 'POST'])
def filesboard_write() :
    if 'user_id' not in session :
        return redirect(url_for('login'))

    if request.method == 'POST' :

        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files') # getlist : 리스트 형태로 가져온다.

        if PostService.save_post(session['user_id'], title, content, files) :
            return "<script>alert('게시물이 등록되었습니다.');location.href='/filesboard';</script>"

        else :
            return "<script>alert('등록 실패');history.back();</script>"

    return render_template('filesboard_write.html')

# 파일 게시판 - 목록
@app.route('/filesboard')
def filesboard_list() :
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

# 파일 게시판 - 자세히 보기
@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id) :
    post, files = PostService.get_post_detail(post_id)

    if not post :
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"

    return render_template('filesboard_view.html', post=post, files=files)

# 파일 게시판 - 자료 다운로드
@app.route('/download/<path:filename>')
def download_file(filename) :
    # 파일이 저장된 폴더(uploads)에서 파일을 찾아 전송한다.
    # 프론트 '<a href="{{ url_for('download_file', filename=file.save_name) }}" ...>' 처리용
    # filename : 서버에 저장된 save_name
    # 브라우저가 다운로드할 때 보여줄 원본 이름을 쿼리 스트링으로 받거나 DB에서 가져와야 한다.

    origin_name = request.args.get('origin_name')
    return send_from_directory('uploads/', filename, as_attachment = True, download_name = origin_name)
    # from flask import send_from_directory 필수

    #   return send_from_directory('uploads/', filename) : 브라우저에서 바로 열어버린다.
    #   as_attachment=True : 파일 다운로드 창
    #   저장할 파일명 : download_name=origin_name

# ----------------------------------------------------------------------------------------------------------------------
#                                                플라스크 실행
# ----------------------------------------------------------------------------------------------------------------------

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
