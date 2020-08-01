from flask import Flask,render_template,request,make_response,redirect,url_for,session,flash
from flask_mysqldb import MySQL,MySQLdb
from datetime import datetime
import pdfkit
import bcrypt

app = Flask(__name__) 
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='banking'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql=MySQL(app)


path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)




@app.route('/',methods=["POST","GET"])
def home():
    return render_template("home.html")

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",(name,email,password,))
        mysql.connection.commit()
        session['name'] = request.form['name']
        session['email'] = request.form['email']
        return redirect(url_for('home'))

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = curl.fetchone()
        curl.close()

        if len(user) > 0:
            if (user["password"].encode('utf-8')) == user["password"].encode('utf-8'):
                session['name'] = user['name']
                session['email'] = user['email']
                return render_template("home.html")
            else:
                return "Error password and email not match"
        else:
            return "Error user not found"
    else:
        return render_template("login.html")

@app.route('/cust',methods=["POST","GET"])
def Index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM customer")
    data = cur.fetchall()
    cur.close()
    return render_template('index2.html', customer=data )



@app.route('/insert', methods = ['POST'])
def insert():

    if request.method == "POST":
        flash("Data Inserted Successfully")
        ssn = request.form['ssn']
        name = request.form['name']
        age = request.form['age']
        address = request.form['address']
        state = request.form['state']
        city = request.form['city']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO customer (ssn,name, age, address, state, city) VALUES (%s, %s, %s, %s, %s, %s)", (ssn, name, age, address, state, city))
        mysql.connection.commit()
        return redirect(url_for('Index'))




@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customer WHERE ssn=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('Index'))

@app.route('/view',methods=['POST','GET'])
def veiw():

    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT custid,name,age,address FROM customer")
        mysql.connection.commit()
        return redirect(url_for('Index'))


@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        custid = request.form['custid']
        name = request.form['name']
        age = request.form['age']
        address = request.form['address']
        state=request.form['state']
        city=request.form['city']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE customer SET name=%s, age=%s, address=%s, state=%s, city=%s WHERE ssn =%s ", (name, age, address, state,city, custid))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('Index'))


@app.route('/logout',methods=["POST","GET"])
def logout():
    session.clear()
    return render_template("home.html")





#This is Account details page
@app.route('/accdet', methods=['GET', 'POST'])
def accdet():
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Balance FROM account")
    res = cur.fetchall()
    cur.close()
    # res is a list of data as dictionaries
    return render_template('accountdetails.html', res=res)

#This is deposit page
@app.route('/deposit/<int:id>/', methods=['GET', 'POST'])
def deposit(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Balance FROM account")
    res = cur.fetchall()
    bal = 0
    for i in res:
        for j, k in i.items():
            if j == "Account_id" and k == id:
                bal = i
    if request.method == 'POST':
        amount = request.form.get('amount')
        cur = mysql.connection.cursor()
        depositquery = ("UPDATE account SET Balance=Balance+%(amount)s WHERE Account_id=%(acc_id)s") #update accounts table
        cur.execute(depositquery, {'amount': amount, 'acc_id': id})
        mysql.connection.commit()
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE account SET Acc_ls_date=%s WHERE Account_id=%s", [datetime.now(),id])
        mysql.connection.commit()# update accounts table
        cur.close()
        cur = mysql.connection.cursor()
        r = cur.execute("SELECT * FROM account WHERE Account_id=%s", [id])
        if r > 0:
            data = cur.fetchone()
            c_id = data['Customer_id']
            a_t = data['Account_type']
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO transactions VALUES(Null,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [c_id, id, a_t, id, a_t, datetime.now(), amount, "Deposit"]) #update transactions table
        mysql.connection.commit()
        cur.close()
        #display successfull message. Redirection to home page is provided in button on html page
        flash("Amount Deposited Successfully!", "info")
        return redirect("/accdet")

    else:
        # bal is dictionary of account data for id
        return render_template('deposit.html', bal=bal)


@app.route('/withdraw/<int:id>/', methods=['GET', 'POST'])
def withdraw(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Balance FROM account")
    res = cur.fetchall()
    bal = 0
    for i in res:
        for j, k in i.items():
            if j == "Account_id" and k == id:
                bal = i
    if request.method == 'POST':
        amount = request.form.get('amount')
        cur = mysql.connection.cursor()
        withdrawcheckquery = ("SELECT Balance from account WHERE Account_id=%(acc_id)s")
        cur.execute(withdrawcheckquery, {'acc_id': id})
        res = cur.fetchall()
        cur.close()
        for i in res:
            for j, k in i.items():
                if j == 'Balance':
                    #checks if balance is sufficient to make withdraw
                    if int(k) >= int(amount):
                        cur = mysql.connection.cursor()
                        withdrawquery = ("UPDATE account SET Balance=Balance-%(amount)s WHERE Account_id=%(acc_id)s")
                        cur.execute(withdrawquery, {'amount': amount, 'acc_id': id})
                        mysql.connection.commit()
                        cur.close()
                        cur = mysql.connection.cursor()
                        r = cur.execute("SELECT * FROM account WHERE Account_id=%s", [id])
                        if r > 0:
                            data = cur.fetchone()
                            c_id = data['Customer_id']
                            a_t = data['Account_type']
                        cur.close()
                        cur = mysql.connection.cursor()
                        cur.execute("INSERT INTO transactions VALUES(Null,%s,%s,%s,%s,%s,%s,%s,%s)",
                                    [c_id, id, a_t, id, a_t, datetime.now(), amount, "Withdraw"]) #update transaction table
                        mysql.connection.commit()
                        cur.close()
                        cur = mysql.connection.cursor()
                        cur.execute(
                            "UPDATE account SET Acc_ls_date=%s WHERE Account_id=%s", [datetime.now(), id])
                        mysql.connection.commit()  # update accounts table
                        cur.close()
                        #Display successful withdrawl. Redirection to home page is provided in button on html page
                        flash("Withdrawn successfully!", "info")
                        return redirect("/accdet")
                    else:
                        #Display less balance and it stays on the page until valid amount is entered. Redirection to home page is provided in button on html page
                        flash("Withdraw not allowed, please choose smaller amount", "danger")
                        return redirect("")


    else:
        # bal is dictionary of account data for id
        return render_template('Withdraw.html', bal=bal)


@app.route('/transfer/<int:id>/', methods=['GET', 'POST'])
def transfer(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Balance FROM account")
    res = cur.fetchall()
    bal = 0
    for i in res:
        for j, k in i.items():
            if j == "Account_id" and k == id:
                bal = i
    if request.method == 'POST':
        t_acc_id = request.form.get('t_acc_id')
        t_a_t = request.form.get('accounttype')
        amount = request.form.get('amount')
        if int(id) != int(t_acc_id):
            cur = mysql.connection.cursor()
            transfercheckquery = ("SELECT Balance from account WHERE Account_id=%(acc_id)s")
            cur.execute(transfercheckquery, {'acc_id': id})
            res = cur.fetchall()
            cur.close()
            for i in res:
                for j, k in i.items():
                    if j == 'Balance':
                        if int(k) >= int(amount):
                            cur = mysql.connection.cursor()
                            transfercheck1query = ("SELECT * FROM account WHERE Account_id=%(acc_id)s")
                            cur.execute(transfercheck1query, {'acc_id': t_acc_id})
                            r = cur.fetchall()
                            cur.close()
                            #checks if target account id is valid or not. Here account type is neglected
                            if len(r) > 0:
                                cur = mysql.connection.cursor()
                                transfercheck2query = (
                                    "UPDATE account SET Balance=Balance+%(amount)s WHERE Account_id=%(acc_id)s")
                                cur.execute(transfercheck2query, {'amount': amount, 'acc_id': t_acc_id})  #update accounts table for target account
                                mysql.connection.commit()
                                transfercheck3query = (
                                    "UPDATE account SET Balance=Balance-%(amount)s WHERE Account_id=%(acc_id)s") #update accounts table for source account
                                cur.execute(transfercheck3query, {'amount': amount, 'acc_id': id})
                                mysql.connection.commit()
                                cur.close()
                                cur = mysql.connection.cursor()
                                r = cur.execute("SELECT * FROM account WHERE Account_id=%s", [id])
                                if r > 0:
                                    data = cur.fetchone()
                                    c_id = data['Customer_id']
                                    s_a_t = data['Account_type']
                                cur.close()
                                cur = mysql.connection.cursor()
                                cur.execute("INSERT INTO transactions VALUES(Null,%s,%s,%s,%s,%s,%s,%s,%s)",
                                            [c_id, id, s_a_t, t_acc_id, t_a_t, datetime.now(), amount, "Transfer"]) #update transactions table
                                mysql.connection.commit()
                                cur.close()
                                cur = mysql.connection.cursor()
                                cur.execute(
                                    "UPDATE account SET Acc_ls_date=%s WHERE Account_id=%s", [datetime.now(), id])
                                mysql.connection.commit()  # update accounts table
                                cur.close()
                                #Displays successful transferRedirection to home page is provided in button on html page
                                flash("Amount transfer completed successfully", "info")
                                return redirect('/accdet')
                            else:
                                # Display not a valid account and it stays on the page until valid account is entered. Redirection to home page is provided in button on html page
                                flash("Transfer not allowed, please choose valid account", "danger")
                                return redirect("")


                        else:
                            # Display enter small amount and it stays on the page until valid amount is entered. Redirection to home page is provided in button on html page
                            flash("Transfer not allowed, please choose smaller amount", "danger")
                            return redirect("")
        else:
            # Display enter different account as both source and target are same and it stays on the page different valid account is entered. Redirection to home page is provided in button on html page
            flash("Transfer not allowed, Source and Target accounts are same ", "danger")
            return redirect("")

    else:
        # bal is dictionary of account data for id
        return render_template('transfer.html', bal=bal)





@app.route("/createaccount", methods=['GET', 'POST'])
def cteacc():
    cur = mysql.connection.cursor()
    res=cur.execute("SELECT Account_id FROM account ORDER BY Account_id DESC")
    if res>0:
        data=cur.fetchone()
        accountid=data['Account_id']
    accountid+=1
    cur.close()
    if request.method == "POST":
        cusid = request.form.get('cusid')
        acctype = request.form.get('acctype')
        depamt = request.form.get('depamt')
        cur = mysql.connection.cursor()
        res = cur.execute("SELECT custid FROM customer WHERE custid=%s",[cusid])
        checkcustid=0
        if res > 0:
            data = cur.fetchone()
            checkcustid = data['custid']
        cur.close()
        if int(checkcustid)==int(cusid):
            cur = mysql.connection.cursor()
            res = cur.execute("SELECT Customer_id, Account_type FROM account  WHERE Customer_id=%s and Account_type=%s", [cusid,acctype])
            checkcustid2=0
            checkacctype=''
            if res > 0:
                data = cur.fetchone()
                checkcustid2 = data['Customer_id']
                checkacctype= data['Account_type']
            cur.close()
            if int(checkcustid2) == int(cusid) and checkacctype== acctype:
                flash("Account already exists", "danger")
                return redirect("")
            else:
                if int(depamt)>0:
                    cur = mysql.connection.cursor()
                    # create cursor
                   # cur.execute("UPDATE account SET Account_id=%s, Account_type=%s, Balance=%s,Acc_Cr_date=%s, Acc_ls_date=%s,Account_status=%s WHERE Customer_id=%s",[ accountid,acctype, depamt, datetime.now(),datetime.now(),'Active',cusid ])
                   # cur.execute("INSERT INTO account (Customer_id, Account_id, Account_type,Balance, Acc_Cr_date,Acc,ls_date,Account_status) VALUES(%s,%s,%s,%s,%s,%s,'Active')",[cusid, accountid,acctype, depamt, datetime.now(),datetime.now()])
                    cur.execute("INSERT INTO account (Customer_id, Account_id, Account_type,Balance, Acc_Cr_date,Acc_ls_date,Account_status) VALUES(%s,%s, %s, %s, %s, %s,'Active')",[cusid, accountid,acctype, depamt, datetime.now(),datetime.now])
                    # commit
                    mysql.connection.commit()
                    cur.close()
                    flash("Account created successfully","info")
                    return redirect('/createaccount')
                else:
                    flash("Enter valid amount", "danger")
                    return redirect("")
        else:
            flash("Enter valid customer id", "danger")
            return redirect("")
    else:
        return render_template("createacc.html")


@app.route("/deleteaccount", methods=['GET', 'POST'])
def delacc():
    cur = mysql.connection.cursor()
    if request.method == "POST":
        accidid = request.form.get('accid')
        acctype = request.form.get('acctype')
        cur = mysql.connection.cursor()
        res = cur.execute("SELECT Account_id, Account_type FROM account WHERE Account_id=%s", [accidid])
        checkaccid = 0
        checkacctype=''
        if res > 0:
            data = cur.fetchone()
            checkaccid = data['Account_id']
            checkacctype=data['Account_type']
        cur.close()
        if int(checkaccid)==int(accidid) and checkacctype==acctype:
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM account WHERE Account_Id = %s and Account_type=%s",[accidid,acctype])
            # commit
            mysql.connection.commit()
            cur.close()
            flash("Account Deleted Successfully", "info")
            return redirect('')
        else:
            flash("Account does not exist", "danger")
            return redirect('')
    return render_template("deleteacc.html")
@app.route('/accountstatus', methods=['GET', 'POST'])
def accountstatus():
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Account_status,Acc_ls_date FROM account ORDER BY Customer_id")
    res = cur.fetchall()
    cur.close()
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id FROM account GROUP BY Customer_id HAVING COUNT(Customer_id) > 1")
    msg = cur.fetchall()
    cur.close()
    lis=[]
    for i in msg:
        lis.append(i.get('Customer_id'))
    # res is a list of data as dictionaries
    return render_template('accountstatus.html', res=res,lis=lis)
#leave this for now
@app.route('/update1', methods=['GET', 'POST'])
def update1():
    ids=request.form.get('ids')
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id,Account_id,Account_type,Account_status,Acc_ls_date FROM account WHERE Account_id=%s",[ids])
    res = cur.fetchone()
    cur.close()
    cur = mysql.connection.cursor()
    cur.execute("SELECT Customer_id FROM account GROUP BY Customer_id HAVING COUNT(Customer_id) > 1")
    msg = cur.fetchall()
    cur.close()
    lis=[]
    for i in msg:
        lis.append(i.get('Customer_id'))
    # res is a list of data as dictionaries
    return render_template('accountstatus.html',res=res,lis=lis)


















@app.route('/printstat', methods = ["GET", "POST"])
def printstatement():
    if request.method=="POST":  
        aid=request.form["aid"]
        notr=request.form["notr"]
        sd=request.form["sd"]
        ed=request.form["ed"] 
        
        cur=mysql.connection.cursor()
        if notr:
            que="""SELECT t_no,dates,operation,amount FROM transactions where s_accountid=%s  order by t_no limit 5 """
            cur.execute(que,(aid,))
            data = cur.fetchall()   
        else:
            que2="""SELECT t_no,dates,operation,amount FROM transactions  where s_accountid=%s and dates between CAST(%s AS DATE) and CAST(%s AS DATE)"""
            cur.execute(que2,(aid,sd,ed))
            data = cur.fetchall()
        rendered=render_template('printtable.html',data=data)
        pdf=pdfkit.from_string(rendered,False,configuration=config)
        response=make_response(pdf)
        response.headers['Content-Type']='application/pdf'
        response.headers['Content-Disposition']='attachment; filename=bankstatement.pdf'
        return response
    return render_template('printstatement.html')


@app.route('/viewstat', methods = ["GET", "POST"])
def viewstatement():
    if request.method=="POST":  
        aid=request.form["aid"]
        notr=request.form["notr"]
        sd=request.form["sd"]
        ed=request.form["ed"] 
        
        cur=mysql.connection.cursor()
        if notr:
            que="""SELECT t_no,dates,operation,amount FROM transactions where s_accountid=%s  order by t_no limit 5 """
            cur.execute(que,(aid,))
            data = cur.fetchall()   
        else:
            que2="""SELECT t_no,dates,operation,amount FROM transactions  where s_accountid=%s and dates between CAST(%s AS DATE) and CAST(%s AS DATE)"""
            cur.execute(que2,(aid,sd,ed))
            data = cur.fetchall()
        return render_template('viewstatement.html',data=data)
        
    return render_template('viewstatement.html')


@app.route('/searchcust',methods=["GET","POST"])
def searchcust():
    if request.method=="POST":
        ssnid=request.form['sid']
        cid=request.form['cid']
        cur=mysql.connection.cursor()
        if ssnid:
            que3="""SELECT * from customer where ssn=%s """
            cur.execute(que3,(ssnid,))
            data=cur.fetchall()
            return render_template('searchcust.html',data=data)
        else:
            que4="""SELECT * from customer where custid=%s """
            cur.execute(que4,(cid,))
            data=cur.fetchall()
            return render_template('searchcust.html',data=data)

    return render_template('searchcust.html')


@app.route('/searchacc',methods=["GET","POST"])
def searchacc():
    if request.method=="POST":
        aid=request.form['aid']
        cid=request.form['cid']
        cur=mysql.connection.cursor()
        if aid:
            que6="""SELECT * from account where Account_id=%s """
            cur.execute(que6,(aid,))
            data=cur.fetchall()
            return render_template('searchacc.html',data=data)
        else:
            que7="""SELECT * from account where Customer_id=%s """
            cur.execute(que7,(cid,))
            data=cur.fetchall()
            return render_template('searchacc.html',data=data)

    return render_template('searchacc.html')

if __name__ == '__main__': 
    app.secret_key = "^A%DJAJU^JJ123"
    app.run(debug=True) 
    