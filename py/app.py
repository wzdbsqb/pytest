import os,xlrd,xlwt,xlutils
from flask import Flask,render_template,request,redirect,jsonify
from sqlalchemy import create_engine,text
from werkzeug import secure_filename



app=Flask(__name__)
engine=create_engine('mysql+pymysql://root:123456@localhost:3306/tsy',connect_args={'charset':'utf8'},pool_recycle=60,pool_size=5)

UPLOAD_FOLDER = os.path.join(os.getcwd(),'static/pic')
UPLOAD_FOLDER1 = os.path.join(os.getcwd(),'static/excel')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# def check_path(UPLOAD_FOLDER):
#     if not os.path.exist(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)


#跳转主界面
@app.route('/')
def index():
    return render_template('index.html')

#跳转统计界面
@app.route('/count')
def count():
    return render_template('count.html')
    

#统计1-12月份销售额度
@app.route('/api/count', methods=['GET', 'POST'])
def api_count():
    if request.method == 'POST':
        statment=text('''
        select month(selltime) as month,cast(sum(price)/100 as CHAR) as sumprice  from sales as s
        left join books as g on s.books_id=g.id
        where  year(selltime)=:year
        group by month(selltime)
        ''').bindparams(year=request.form['year'])
        rows=engine.execute(statment).fetchall()
        return jsonify({
            'status':200,
            'data':[dict(row) for row in rows]
        })


#更改书籍图片
@app.route('/save/<id>', methods=['GET', 'POST'])
def upload_file_books(id):
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        statment=text('''
        UPDATE `books` 
        SET pic=:pic
        WHERE id=:id
        ''').bindparams(id=id,pic='/static/pic/'+filename)
        engine.execute(statment)

        return redirect('/booksedit/'+id)

#更改书店图片
@app.route('/saveuser/<id>', methods=['GET', 'POST'])
def upload_file_user(id):
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        statment=text('''
        UPDATE `user` 
        SET pic=:pic
        WHERE id=:id
        ''').bindparams(id=id,pic='/static/pic/'+filename)
        engine.execute(statment)
        return redirect('/messagedit')

#跳转批量添加html
@app.route('/saveall')
def saveall():
    return render_template('saveall.html')


#往books表中批量添加数据（Excel）
@app.route('/saveall/<id>', methods=['GET', 'POST'])
def saveall_id(id):
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER1, filename))
        xls = xlrd.open_workbook((os.path.join(os.getcwd(),'static/excel',filename)),'rb')
        sh=xls.sheets()[0]

        for i in range(sh.nrows):
                if i==0:
                    continue
                name=sh.cell(i,1).value
                price=int(sh.cell(i,2).value)
                pprice=int(sh.cell(i,3).value)
                tag=sh.cell(i,4).value
                intro=sh.cell(i,5).value         
                statment=text('''
                INSERT INTO 
                books(user_id, name, price, pprice, tag, intro) 
                VALUES (:id, :name, :price, :pprice, :tag, :intro)
                ''').bindparams(id=id,name=name,price=price,pprice=pprice,tag=tag,intro=intro)
                engine.execute(statment)

        return redirect('/saveall')


#创建书籍表单
@app.route('/creat/<id>')
def creat(id):
    statment=text('''
    select name,price,pprice,tag,intro
    from books 
    where user_id=:id
    ''').bindparams(id=id)
    rows=engine.execute(statment).fetchall()
    ws=xlwt.Workbook(encoding='utf-8')
    sheet=ws.add_sheet('books数据')

    for i in range(len(rows)):
        for j in range(len(rows[i])):
            sheet.write(i,j,rows[i][j])
    
    ws.save(os.path.join(os.getcwd(),'static/excel',id+'.xlsx'))
    return jsonify({
        'status':200,
        'message':'生成excel成功'
    })

#取出书店信息
@app.route('/api/user/<id>')
def user_info(id):
    statment=text('''
    select name,tel,addr,tag,pic,intro,lat,`long`,dur,licence
    from user 
    where id=:a
    ''').bindparams(a=id)
    rows=engine.execute(statment).fetchall()
    return jsonify({
        'status':200,
        'data':dict(rows[0])
    })

#取出书籍信息
@app.route('/api/books/<id>')
def books_info(id):
    statment=text('''
    select g.id,g.name,CAST(price/100 AS CHAR) as price,CAST(pprice/100 AS CHAR) as pprice,g.tag,g.pic,g.intro
    from books as g
    left join user as u on g.user_id=u.id
    where g.user_id=:a
    ''').bindparams(a=id)
    rows=engine.execute(statment).fetchall()
    return jsonify({
        'status':200,
        'data':[dict(row) for row in rows]
    })

#跳转书店信息显示界面
@app.route('/message')
def message():
    return render_template('message.html')

#跳转书籍添加界面
@app.route('/booksadd')
def booksadd():
    return render_template('booksadd.html')

#执行书籍添加
@app.route('/api/booksadd/<id>',methods=['GET','POST'])
def books_add(id):
    if request.method == 'POST':
        statment=text('''
        INSERT INTO 
        books(user_id, name, price, pprice, tag, intro) 
        VALUES (:id, :name, :price, :pprice, :tag, :intro)
        ''').bindparams(id=id,name=request.form['name'],price=request.form['price'],pprice=request.form['pprice'],tag=request.form['tag'],intro=request.form['intro'])
        engine.execute(statment)
        return jsonify({
            'status':200,
            'message':'添加成功'
        })

#删除书籍
@app.route('/booksdelete',methods=['GET','POST'])
def books_delete():
    if request.method == 'POST':
        statment=text('''
        DELETE FROM books
        WHERE id=:id
        ''').bindparams(id=request.form['id'])
        engine.execute(statment)
        return jsonify({
            'status':200,
            'message':'删除成功'
        })


#修改书店信息/跳转书店信息修改界面    
@app.route('/messagedit',methods=['GET','POST'])
def messagedit():
    if request.method == 'POST':
        statment=text('''
        UPDATE `user` 
        SET `name`=:name, `tel`=:tel, `addr`=:addr, `tag`=:tag, `intro`=:intro, `lat`=:lat, `long`=:long, `dur`=:dur, `licence`=:licence 
        WHERE (`id`=:id)
        ''').bindparams(id=request.form['id'],name=request.form['name'],tel=request.form['tel'],addr=request.form['addr'],tag=request.form['tag'],intro=request.form['intro'],lat=request.form['lat'],long=request.form['long'],dur=request.form['dur'],licence=request.form['licence'])
        engine.execute(statment)

        return jsonify({
            'status':200,
            'message':'修改成功'
        })
    return render_template('messagedit.html')


#修改密码/跳转修改密码界面
@app.route('/changepwd',methods=['GET','POST'])
def changepwd():
    if request.method == 'POST':
        statment=text('''
        UPDATE `user` 
        SET `password`=:password
        WHERE (`id`=:id)
        ''').bindparams(id=request.form['id'],password=request.form['password'])
        engine.execute(statment)
        return jsonify({
            'status':200,
            'message':'修改成功'
        })
    return render_template('changepwd.html')


#取出密码
@app.route('/getpwd/<id>')
def getpwd(id):
    statment=text('''
    select password
    from user 
    where id=:a
    ''').bindparams(a=id)
    rows=engine.execute(statment).fetchall()
    return jsonify({
        'status':200,
        'data':dict(rows[0])
    })


#跳转书籍信息编辑界面
@app.route('/booksedit/<id>')
def booksedit(id):
    return render_template('booksedit.html')


#书籍信息修改
@app.route('/api/booksedit/<id>',methods=['GET','POST'])
def books_edit(id):
    if request.method == 'POST':

        statment1=text('''
        UPDATE books 
        SET name=:name, price=:price, pprice=:pprice, tag=:tag,  intro=:intro 
        WHERE id=:id
        ''').bindparams(id=id,
            name=request.form['name'],
            price=request.form['price'],
            pprice=request.form['pprice'],
            tag=request.form['tag'],
            intro=request.form['intro'])
        engine.execute(statment1)
        return jsonify({
            'status':200,
            'message':'修改成功'
        }) 
    else :statment=text('''
    select name,price,pprice,tag,pic,intro
    from books
    where id=:a
    ''').bindparams(a=id)
    rows=engine.execute(statment).fetchall()
    return jsonify({
        'status':200,
        'data':dict(rows[0])
    })


#登陆
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        statment=text('''
        select id,account,name
        from user 
        where account =:acc
        and password=:pwd
        ''').bindparams(acc=request.form['account'],pwd=request.form['password'])
        rows=engine.execute(statment).fetchall()

        if len(rows) == 1:
            state="登陆成功"
            return jsonify({
                'status':200,
                'message':state,
                'data':dict(rows[0])
            })

        else:
            state="登陆失败"
            return jsonify({
                'status':401,
                'message':state
            })
    return render_template('login.html')


#注册
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        statment=text('''
        select count(*) as num
        from user 
        where account =:acc
        ''').bindparams(acc=request.form['account'])
        rows=engine.execute(statment).fetchall()

        if rows[0].num>=1:
            s=0
        elif  rows[0].num==0:
            s=1
            statment1=text('''
            INSERT INTO 
            user (account, password, name) 
            VALUES (:acc,:pwd,:acc)
            ''').bindparams(acc=request.form['account'],pwd=request.form['password'])
            engine.execute(statment1)

        return jsonify({
            'status':200,
            'message':s
        })       
    return render_template('register.html')


    
if __name__ == '__main__':
    app.run()