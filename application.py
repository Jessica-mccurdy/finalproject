from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import smtplib
import string

from helpers import apology, login_required, twelvey
# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use Postgres database
db = SQL("postgres://czznryphemnxjs:4a6625d3983a3befabf184350cfc1d43b1d285b396838bb7255421f1f32c3267@ec2-184-73-206-155.compute-1.amazonaws.com:5432/d36i73dhm3jssb")


@app.route("/")
def home():
    try:
        id = session["user_id"]
        row = db.execute("SELECT name FROM users WHERE userid = :id", id=id)
        name = row[0].get('name')
        return render_template("home.html", name=name)
    except:
        return render_template("home.html")


@app.route("/new_order", methods=["GET", "POST"])
@login_required
def new_order():
    """Request an Uber"""

    if request.method == "POST":
        if request.form.get("type"):
            session["type"] = request.form.get("type")
            return redirect("/order")
        else:
            return apology("Must select arrival or departure", 400)

    if request.method == "GET":
        return render_template("order_D_or_A.html")


@app.route("/order", methods=["GET", "POST"])
@login_required
def order():
    """Display and get info from departure form"""

    if request.method == "POST":

        id = session["user_id"]

        type = int(session["type"])

        # checks if user entered date
        if not request.form.get("date"):
            return apology("must provide date", 400)
        else:
            date = request.form.get("date")

        # checks if user entered optimal time
        if not request.form.get("otime"):
            return apology("must provide optimal time", 400)
        else:
            otime = request.form.get("otime")

        # checks if user entered wait time time
        if not request.form.get("etime"):
            return apology("must provide time", 400)
        else:
            etime = request.form.get("etime")

        # checks if valid times
        if timecheck(type, otime, etime) == "e":
            return apology("Earliest time must be earlier than optimum time", 400)
        elif timecheck(type, otime, etime) == "l":
            return apology("Latest time must be later than optimum time", 400)

        # checks if user entered airport
        if not request.form.get("airport"):
            return apology("must provide airport", 400)
        else:
            airport = request.form.get("airport")

        # checks if user entered number of passengers
        if not request.form.get("number"):
            return apology("must provide number of passengers", 400)
        else:
            number = int(request.form.get("number"))

        fnumber = 6 - number

        # insert
        rows = db.execute("INSERT INTO requests (userid, airport, date, otime, number, etime, type) VALUES (:userid, :airport, :date, :otime, :number, :etime, :type)",
                          userid=id, airport=airport, date=date, otime=otime, number=number, etime=etime, type=type)

        # insert into history
        db.execute("INSERT INTO history (rideid, userid, type, airport, date) VALUES (:rideid, :userid, :type, :airport, :date)",
                   rideid=rows, userid=id, airport=airport, date=date, type=type)

        matched = match(rows)

        return render_template("ordered.html", matched=matched)

    if request.method == "GET":
        return render_template("order.html", type=session["type"])


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        db.execute("DELETE FROM history WHERE userid = :userid", userid=session["user_id"])

        return redirect("/")

     # User reached route via GET (as by clicking a link or via redirect)
    else:
        # stores index
        rides = db.execute("SELECT * FROM history WHERE userid = :userid",
                           userid=session["user_id"])

        if rides != None:
            return render_template("history.html", rides=rides)
        else:
            return apology("table is empty", 400)

        if not request.form.get("clear"):
            return apology("must provide username", 403)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any userid
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        phone = request.form.get("phone")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords must match", 400)

        # Ensure name was submitted
        elif not request.form.get("name"):
            return apology("Must enter first name", 400)

        # Ensure surname was submitted
        elif not request.form.get("surname"):
            return apology("Must enter last name", 400)

        # Ensure email was submitted
        elif not request.form.get("email"):
            return apology("Must enter email", 400)

        # Ensure phone number was submitted
        elif not request.form.get("phone"):
            return apology("Must enter phone number", 400)

        # checks if valid phone number
        if phonec(phone) == "fail":
            return apology("Must enter valid 10 digit phone number", 400)
        phone = phonec(phone)

        # hashes password
        hash = generate_password_hash(request.form.get("password"))

        # inserts new user in data base and checks username
        rows = db.execute("INSERT INTO users ( username, password, name, surname, email, phone ) VALUES( :username, :hash, :name, :surname, :email, :phone )",
                          username=username, hash=hash, name=name, surname=surname, email=email, phone=phone)

        if rows == None:
            return apology("Username is taken :(", 400)

         # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/cancel", methods=["GET", "POST"])
@login_required
def cancel():
    """Cancel Ride"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("rideid"):
            return apology("Must select ride", 400)
        rideid = request.form.get("rideid")
        # update history
        db.execute("UPDATE history SET status=:new WHERE rideid = :id", new="Cancelled", id=rideid)
        # delete from requests
        db.execute("DELETE FROM requests WHERE rideid = :rideid", rideid=rideid)
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]
        rides = db.execute(
            "SELECT * FROM requests WHERE userid = :id", id=id)
        return render_template("cancel.html", rides=rides)


@app.route("/complete", methods=["GET", "POST"])
@login_required
def complete():
    """Complete Ride"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("rideid"):
            return apology("Must select ride", 400)
        rideid = request.form.get("rideid")
        # update history
        db.execute("UPDATE history SET status=:new WHERE rideid = :id", new="Complete", id=rideid)
        # delete from requests
        db.execute("DELETE FROM requests WHERE rideid = :rideid", rideid=rideid)
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]
        rides = db.execute(
            "SELECT * FROM requests WHERE userid = :id", id=id)
        return render_template("complete.html", rides=rides)


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update Ride"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        rideid = request.form.get("rideid")

        session['rideid'] = rideid
        return redirect("update2")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]
        rides = db.execute("SELECT * FROM requests WHERE userid = :id", id=id)
        return render_template("update.html", rides=rides)


@app.route("/update2", methods=["GET", "POST"])
@login_required
def update2():
    """Update Ride"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        rideid = session["rideid"]

        # checks if user entered date
        if request.form.get("date"):
            date = request.form.get("date")
            db.execute("UPDATE requests SET date=:new WHERE rideid = :id", new=date, id=rideid)

         # checks if user entered type
        if request.form.get("type"):
            type = request.form.get("type")
            db.execute("UPDATE requests SET type=:new WHERE rideid = :id", new=type, id=rideid)

        # gets current etime and type
        user = db.execute("SELECT * FROM requests WHERE rideid = :id", id=rideid)[0]
        etime = user["etime"]
        type = user["type"]

        # checks if user entered optimal time
        if request.form.get("otime"):
            otime = request.form.get("otime")
            # if the user is changing both
            if request.form.get("etime") and request.form.get("otime"):
                etime = request.form.get("etime")
                otime = request.form.get("otime")
            # checks times
            if timecheck(type, otime, etime) == "e":
                return apology("Earliest time must be earlier than optimum time", 400)
            elif timecheck(type, otime, etime) == "l":
                return apology("Latest time must be later than optimum time", 400)
            db.execute("UPDATE requests SET otime=:new WHERE rideid = :id", new=otime, id=rideid)

        # regets data in case of change
        user = db.execute("SELECT * FROM requests WHERE rideid = :id", id=rideid)[0]
        otime = user["otime"]

        # checks if user entered wait time time
        if request.form.get("etime"):
            etime = request.form.get("etime")
            # checks times
            if timecheck(type, otime, etime) == "e":
                return apology("Earliest time must be earlier than optimum time", 400)
            elif timecheck(type, otime, etime) == "l":
                return apology("Latest time must be later than optimum time", 400)
            db.execute("UPDATE requests SET etime=:new WHERE rideid = :id", new=etime, id=rideid)

        # checks if user entered airport
        if request.form.get("airport"):
            airport = request.form.get("airport")
            db.execute("UPDATE requests SET airport=:new WHERE rideid = :id", new=airport, id=rideid)

        # checks if user entered number of passengers
        if request.form.get("number"):
            number = int(request.form.get("number"))
            db.execute("UPDATE requests SET number=:new WHERE rideid = :id", new=number, id=rideid)

        matched = match(rideid)
        return render_template("ordered.html", matched=matched)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]
        rideid = session["rideid"]
        ride = db.execute("SELECT * FROM requests WHERE rideid = :rideid", rideid=rideid)[0]
        airport = ride["airport"]
        date = ride["date"]
        otime = ride["otime"]
        etime = ride["etime"]
        number = ride["number"]
        type = ride["type"]
        if type == 0:
            type = "Departure"
        else:
            type = "Arrival"
        return render_template("update2.html", airport=airport, date=date, otime=otime, etime=etime, number=number, type=type)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Allows user to change information"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        id = session["user_id"]

        if request.form.get("username"):
            username = request.form.get("username")
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
            if rows == None:
                return apology("Username is taken :(", 400)
            else:
                db.execute("UPDATE users SET username=:username WHERE userid = :id",
                           username=username, id=id)

        if request.form.get("fname"):
            db.execute("UPDATE users SET name=:fname WHERE userid = :id",
                       fname=request.form.get("fname"), id=id)

        if request.form.get("surname"):
            db.execute("UPDATE users SET surname=:surname WHERE userid = :id",
                       surname=request.form.get("surname"), id=id)

        if request.form.get("email"):
            db.execute("UPDATE users SET email=:email WHERE userid = :id",
                       email=request.form.get("email"), id=id)

        if request.form.get("phone"):
            phone = request.form.get("phone")
            if phonec(phone) == "fail":
                return apology("Must enter valid 10 digit phone number", 400)
            phone = phonec(request.form.get("phone"))
            db.execute("UPDATE users SET phone=:phone WHERE userid = :id", phone=phone, id=id)

        # checks if user entered passwords
        if request.form.get("oldpass"):

            if not request.form.get("newpass"):
                return apology("must enter new password", 400)
            elif not request.form.get("verification"):
                return apology("must verify password", 400)
            else:
                # stores passwords
                oldpass = request.form.get("oldpass")
                newpass = request.form.get("newpass")
                verification = request.form.get("verification")

                row = db.execute("SELECT password FROM users WHERE userid = :id", id=id)

                # ensure user inputs valid information
                if not check_password_hash(row[0]["password"], oldpass):
                    return apology("old password is incorrect", 400)

                if newpass != verification:
                    return apology("new passwords must match", 400)

                # update password
                newpass = generate_password_hash(newpass)
                db.execute("UPDATE users SET password=:newpass WHERE userid = :id",
                           newpass=newpass, id=id)

        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]

        # gets user information
        user = db.execute("SELECT * FROM users WHERE userid=:userid", userid=id)[0]
        email = user["email"]
        fname = user["name"]
        sname = user["surname"]
        phone = user["phone"]
        username = user["username"]

        return render_template("settings.html", username=username, fname=fname, sname=sname, email=email, phone=phone)


@app.route("/closest", methods=["GET", "POST"])
@login_required
def closest():
    """Checks for the closest time"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # set userid
        id = session["user_id"]

        # get rideid
        rideid = request.form.get("rideid")

        # get all info about ride
        ride = db.execute("SELECT * FROM requests WHERE rideid = :rideid",
                          rideid=rideid)[0]

        # get only values
        type = ride["type"]
        etime = ride["etime"]
        airport = ride["airport"]
        date = ride["date"]
        number = ride["number"]

        # set fnumber - make sure don't exceed uber capacity
        fnumber = 6 - number

        if type == 0:
            # search for matches for departure
            rows = db.execute("SELECT rideid FROM requests WHERE airport = :airport AND date = :date AND type = :type AND otime < :etime AND userid != :id",
                              airport=airport, date=date, type=type, etime=etime, id=id)
        else:
            # search for matches for arrival
            rows = db.execute("SELECT rideid FROM requests WHERE airport = :airport AND date = :date AND type = :type AND otime > :etime AND userid != :id",
                              airport=airport, date=date, type=type, etime=etime, id=id)

        if rows:
            # makes list of times
            times = []
            for i in rows:
                i = i.get('rideid')
                time = dict(db.execute("SELECT otime FROM requests WHERE rideid = :i", i=i)[0])
                times.append(time.get('otime'))

            # makes list of time differences
            diffs = []
            n = len(times)
            for i in range(n):
                FMT = '%H:%M'
                diffs.append(
                    abs((datetime.strptime(times[i], FMT) - datetime.strptime(etime, FMT)).total_seconds() / 60))

            # makes list of tupples sorted by time difference
            zipped = list(zip(rows, diffs))
            closest = min(zipped, key=lambda t: t[1])[0]
            # gets value of closest match
            closest = closest.get('rideid')

            # gets the matchees information
            user = db.execute(
                "SELECT * FROM requests JOIN users ON requests.userid = users.userid WHERE rideid = :closest", closest=closest)[0]

            # gets values
            email = user["email"]
            name = user["name"]
            phone = user["phone"]
            time = user["etime"]

            message = ["Here is the information for the person with the closest match:"]
            # creates message for departure
            if type == 0:
                message = message + ["\n"] + [name] + ["\'s optimal time (latest time) is "] + [time] + ["\n"] + [
                    "email: "] + [email] + ["\n"] + ["phone #: "] + [phone] + ["\n"]
            else:
                message = message + ["\n"] + [name] + ["\'s optimal time ( earliest time) is "] + [time] + ["\n"] + [
                    "email: "] + [email] + ["\n"] + ["phone #: "] + [phone] + ["\n"]

        # if nobody matched
        else:
            message = ["Sorry, there is nobody who matches your request"]

        return render_template("closested.html", message=message)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        id = session["user_id"]
        # gets user's rides
        rides = db.execute(
            "SELECT * FROM requests WHERE userid = :id", id=id)
        return render_template("closest.html", rides=rides)


def phonec(phone):
    # checks if valid phone number
    num_digits = 0
    dash = False

    if phone[0] != "(":
        for i in range(len(phone)):
            if (i == 3 or i == 7) and (phone[i] == "-" or phone[i] == " "):
                dash = True
                continue
            elif not phone[i].isdigit():
                return "fail"

            num_digits = num_digits + 1

        if num_digits != 10:
            return "fail"

        if not dash:
            phone = '-'.join([phone[:3], phone[3:6], phone[6:]])
    return phone


def match(rideid):

    id = session["user_id"]

    ride = db.execute("SELECT * FROM requests WHERE rideid = :rideid", rideid=rideid)[0]
    airport = ride["airport"]
    date = ride["date"]
    otime = ride["otime"]
    etime = ride["etime"]
    number = ride["number"]
    type = ride["type"]

    fnumber = 6 - number

    if type == 0:
        # search for matches for departure
        rows = db.execute("SELECT rideid FROM requests WHERE (userid!=:id AND airport=:airport AND date=:date AND type = :type AND number<=:fnumber AND otime>=:etime AND etime<=:etime) OR (userid!=:id AND airport=:airport AND date=:date AND type = :type AND number<=:fnumber AND otime>=:otime AND etime>=:otime)",
                          id=id, airport=airport, date=date, type=type, otime=otime, etime=etime, fnumber=fnumber)
    else:
        # search for matches for arrival
        rows = db.execute("SELECT rideid FROM requests WHERE (userid!=:id AND airport=:airport AND date=:date AND type = :type AND number<=:fnumber AND otime>=:otime AND otime<=:etime) OR (userid!=:id AND airport=:airport AND date=:date AND type = :type AND number<=:fnumber AND otime<=:otime AND etime>=:otime)",
                          id=id, airport=airport, date=date, type=type, otime=otime, etime=etime, fnumber=fnumber)

    if rows:
        # makes list of times
        times = []
        for i in rows:
            i = i.get('rideid')
            time = db.execute("SELECT otime FROM requests WHERE rideid=:rideid", rideid=i)[0]
            times.append(time.get('otime'))

        # makes list of time differences
        diffs = []
        n = len(times)
        for i in range(n):
            FMT = '%H:%M'
            diffs.append(
                abs((datetime.strptime(times[i], FMT) - datetime.strptime(otime, FMT)).total_seconds() / 60))

        # makes list of tupples sorted by time difference
        zipped = []
        zipped = list(zip(rows, diffs))
        zipped.sort(key=lambda tup: tup[1])

        # makes list of sorted rideids
        rides = []
        n = len(zipped)
        for i in range(n):
            rides.append(zipped[i][0])

        # begins message of email
        message = """Subject: Uber Match!
        We found one or more matches -"""

        emails = []
        names = []
        phones = []

        # finds information for email
        for i in rides:
            i = i["rideid"]
            user = db.execute(
                "SELECT * FROM requests JOIN users ON requests.userid = users.userid WHERE rideid=:rideid", rideid=i)[0]
            user["email"]
            emails.append(user["email"])
            names.append(user["name"])
            phones.append(user["phone"])

        # creates message of all info
        n = len(rides)
        for i in range(n):
            message = message + "\n     " + names[i] + "\'s optimum time is " + times[
                i] + "on " + date + "\n     email  - " + emails[i] + " phone # - " + phones[i] + "\n"

        # gets user email
        user = db.execute("SELECT * FROM users WHERE userid=:userid", userid=id)[0]
        email = user["email"]

        # sends email to person who requested a ride
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("yaleubershare@gmail.com", "najmtwbw")
        server.sendmail("yaleubershare@gmail.com", email, message)

        # gets user name and phone
        name = user["name"]
        phone = user["phone"]

        # create message for matches
        message = """Subject: Uber Match!
        Somebody matched with your uber request!\n"""

        message = message + "\n Here is their information - \n" + name + "'s optimum time is " + otime  + " on " + date + "\n     email - " + email + " phone # - " + phone


        # sends email to all matches
        for i in emails:
            server.sendmail("yaleubershare@gmail.com", i, message)

        matched = True
        return matched
    else:
        matched = False
        return matched


def timecheck(type, otime, etime):
    # checks if valid times
    if type == 0:
        if otime < etime:
            return "e"
    else:
        if otime > etime:
            return "l"


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run()
