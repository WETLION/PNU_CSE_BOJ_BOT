import sqlite3, func

level = ['unranked', 'bronzeV', 'bronzeIV', 'bronzeIII', 'bronzeII', 'bronzeI', 'silverV', 'silverIV', 'silverIII', 'silverII', 'silverI', 'goldV', 'goldIV', 'goldIII', 'goldII', 'goldI', 'platinumV', 'platinumIV', 'platinumIII', 'platinumII', 'platinumI', 'diamondV', 'diamondIV', 'diamondIII', 'diamondII', 'diamondI', 'rubyV', 'rubyIV', 'rubyIII', 'rubyII', 'rubyI']

discord_id = 0
boj_id = 1
week_score = 2
total_score = 3
day_score = 4

def make_all_level():
    ret = ""
    for i in level:
        ret += f", {i} INTEGER"
    return ret

def reset():
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute("DROP TABLE boj_id")
    cur.execute("DROP TABLE solved_problem")
    cur.execute("CREATE TABLE boj_id (discord_id TEXT, id TEXT, week_score INTEGER, total_score INTEGER, day_score INTEGER)")
    cur.execute("CREATE TABLE solved_problem (id TEXT" + make_all_level() + ")")
    # cur.execute("DELETE FROM boj_id WHERE id = ?", ('scientistkjm',))
    # cur.execute("DELETE FROM solved_problem WHERE id = ?", ("scientistkjm",))
    con.commit()
    con.close()

def user_init(ctx, msg):
    # 유효한 boj id인지 확인
    try:
        func.crawling(msg)
    except Exception as e:
        print(e)
        return -1
    
    ret = 0
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM boj_id WHERE discord_id = ?', (str(ctx.author),))
    arr = cur.fetchone()
    print(arr)
    if arr == None:
        cur.execute('INSERT INTO boj_id VALUES (?, ?, ?, ?, ?)', (str(ctx.author), msg, 0, 0, 0))
    else:
        cur.execute('DELETE FROM solved_problem WHERE id = ?', (arr[boj_id], ))
        cur.execute('UPDATE boj_id SET id = ? WHERE discord_id = ?', (msg, str(ctx.author)))
        ret = 1
    cur.execute('INSERT INTO solved_problem VALUES(' + '?, ' * 31 + '?)', (msg, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    con.commit()
    con.close()
    if solved_problem_update(msg) < 0:
        ret = -1
    return ret

def user_read(ctx): # user 정보 읽어오기
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM boj_id WHERE discord_id = ?', (str(ctx.author),))
    ret = cur.fetchone()
    con.close()
    return ret

def user_read_all(): # 전체 user 정보 읽어오기, 일일 및 주간 점수 체크용
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM boj_id')
    ret = cur.fetchall()
    con.close()
    return ret

def user_read_day_score(id): # 일일 점수 불러오기
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT day_score FROM boj_id WHERE id = ?', (id, )) # 이전 주간 점수 불러오기
    ret = cur.fetchone()[0]
    con.close()
    return ret

def user_update_day_score(id): # 일일 점수 업데이트
    ret = solved_problem_update(id)
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT day_score FROM boj_id WHERE id = ?', (id, ))
    user = cur.fetchone()
    ret = max(ret, user[0])
    cur.execute('UPDATE boj_id SET day_score = ? WHERE id = ?', (ret, id))
    con.commit()
    con.close()
    return ret

def user_read_week_score(id): # 주간 점수 가져오기
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT week_score FROM boj_id WHERE id = ?', (id, ))
    ret = cur.fetchone()[0]
    con.close()
    return ret
    
def user_update_week_score(id): # 주간 점수 업데이트
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    updated_week_score = user_update_day_score(id) + user_read_week_score(id)
    cur.execute('UPDATE boj_id SET day_score = ?, week_score = ? WHERE id = ?', (0, updated_week_score, id))
    con.commit()
    con.close()

def user_read_total_score(id): # 전체 점수 불러오기
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT total_score FROM boj_id WHERE id = ?', (id, ))
    ret = cur.fetchone()[0]
    con.close()
    return ret

def user_update_total_score(id, score): # 전체 점수 업데이트
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('UPDATE boj_id SET week_score = ?, total_score = ? WHERE id = ?', (0, score, id))
    con.commit()
    con.close()
    
def solved_problem_update(id):
    ret = 0
    con = sqlite3.connect('db/user.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM solved_problem WHERE id = ?', (id, )) # 이전 풀이 완료 문제 불러오기
    user = cur.fetchone()
    # print(user)
    try:
        data = func.crawling(id)
    except Exception as e:
        print(e)
        con.close()
        return -1
    # print(data, user)
    for i, j, k in zip(level, data, user[1:]):
        cur.execute('UPDATE solved_problem SET '+ i +' = ? WHERE id = ?', (j['solved'], id))
        if k != j['solved']: # 뒤로 갈수록 난이도가 높으므로 가능한 한 뒤에서 푼 문제를 점수로 카운트
            ret = j['level']
    con.commit()
    con.close()
    return ret