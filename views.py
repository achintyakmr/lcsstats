from flask import Flask
from flask import render_template
import sqlite3
from flask import request, g
import os

DATABASE = 'data/lcsstats.db'
DEBUG = False
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'


app = Flask(__name__)


def connect_db():
    return sqlite3.connect(DATABASE)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
@app.route('/players')
def show_players():
    players = g.db.execute('select player_name from player order by player_name').fetchall()
    return render_template('players.html', players=players)


@app.route('/teams')
def show_teams():
    teams = g.db.execute('select team_name from team order by team_name').fetchall()
    return render_template('teams.html', teams=teams)


@app.route('/tournaments')
def show_tournaments():
    temp = g.db.execute('select tournament_name,tournament_region,tournament_year,tournament_season from tournament order by tournament_year desc').fetchall()
    tournaments = []
    for t in temp:
        tournaments.append(str(t[0]) + ' ' + str(t[1]) + ' ' + str(t[2]) + ' ' + str(t[3]))
    return render_template('tournaments.html', tournaments=tournaments)


@app.route('/ps', methods=['GET', 'POST'])
def ps():
    playerselected = str(request.form.get('player'))
    players = g.db.execute('select player_name from player order by player_name').fetchall()
    query = 'select distinct team_name from roster where player_name=\'' + playerselected + '\' order by tournament_id desc'
    teams = g.db.execute(query).fetchall()

    region = g.db.execute('select player_region from player where player_name=\'' + playerselected + '\'').fetchall()
    kda = g.db.execute('select (sum(kills)+sum(assists))*1.0/sum(deaths) as kda from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    k = g.db.execute('select sum(kills) as k from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    d = g.db.execute('select sum(deaths) as d from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    a = g.db.execute('select sum(assists) as a from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    tcs = g.db.execute('select sum(cs) from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    tgs = g.db.execute('select sum(gold)/10 from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    gamesplayed = g.db.execute('select count(player_name) as gamesplayed from player_game_stats where player_name=\'' + playerselected + '\'').fetchall()
    games = g.db.execute('select g.game_date,g.game_time,g.duration from player_game_stats as p,game_stats as g  where player_name=\'' + playerselected + '\' and p.game_date=g.game_date and p.game_time=g.game_time').fetchall()
    tduration = []
    tdsum = 0
    for i in games:
        tduration.append(i[2])
    for i, j in enumerate(tduration):
        j = j.replace(':', '.')
        tduration[i] = float(j)
    for i in range(0, len(tduration)):
        tdsum += tduration[i]
    cspm = float(tcs[0][0]) / tdsum
    cspm = float("{0:.2f}".format(cspm))
    gpm = float(tgs[0][0]) / tdsum
    gpm = float("{0:.2f}".format(gpm))
    kda = float(kda[0][0])
    kda = float("{0:.2f}".format(kda))
    topchamps = g.db.execute('select champion_played, count(champion_played) as cpc from player_game_stats where player_name=\'' + playerselected + '\' group by champion_played order by cpc desc limit 5').fetchall()
    winratio = g.db.execute('select count(winner) from (select game_date as ggd, game_time as ggt from player_game_stats where player_name=\'' + playerselected + '\')games, (select distinct team_name as tn, tournament_id as tid from roster where player_name=\'' + playerselected + '\')temp, game_stats where winner=tn and tournament_id=tid and game_date=ggd and game_time=ggt').fetchall()
    wr = float(winratio[0][0]) / gamesplayed[0][0]
    wr = float("{0:.2f}".format(wr))

    return render_template('ps.html', players=players, teams=teams, playerselected=playerselected, cspm=cspm, gpm=gpm, wr=wr, gamesplayed=gamesplayed, kda=kda, topchamps=topchamps, region=region, k=k, d=d, a=a, g=tgs, cs=tcs)


@app.route('/psts', methods=['GET', 'POST'])
def psts():
    playerselected = str(request.form.get('player'))
    teamselected = str(request.form.get('team'))
    players = g.db.execute('select player_name from player order by player_name').fetchall()
    query = 'select distinct team_name from roster where player_name=\'' + playerselected + '\' order by team_name'
    teams = g.db.execute(query).fetchall()
    query = 'select tournament_name, tournament_region, tournament_year, tournament_season from tournament where tournament.tournament_id in (select distinct tournament_id from roster where roster.team_name=\''+teamselected+'\' and roster.player_name=\''+playerselected+'\') order by tournament_id desc'
    temp = g.db.execute(query).fetchall()
    tournaments = []
    for t in temp:
        tournaments.append(str(t[0]) + ' ' + str(t[1]) + ' ' + str(t[2]) + ' ' + str(t[3]))

    region = g.db.execute('select team_region from team where team_name=\'' + teamselected + '\'').fetchall()
    kda = g.db.execute('select (sum(kills)+sum(assists))*1.0/sum(deaths) as kda from (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    k = g.db.execute('select sum(kills) as k from (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    d = g.db.execute('select sum(deaths) as d from (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    a = g.db.execute('select sum(assists) as a from (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    tcs = g.db.execute('select sum(cs) from player_game_stats, (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    tgs = g.db.execute('select sum(gold)/10 from player_game_stats, (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    gamesplayed = g.db.execute('select count(player_name) as gamesplayed from player_game_stats, (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid').fetchall()
    games = g.db.execute('select g.game_date,g.game_time,g.duration from (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp, player_game_stats as p,game_stats as g  where player_name=\'' + playerselected + '\' and g.game_date=p.game_date and g.game_time=p.game_time and g.tournament_id=p.tournament_id and p.game_date=gd and p.game_time=gt and p.tournament_id=tid').fetchall()
    tduration = []
    tdsum = 0
    for i in games:
        tduration.append(i[2])
    for i, j in enumerate(tduration):
        j = j.replace(':', '.')
        tduration[i] = float(j)
    for i in range(0, len(tduration)):
        tdsum += tduration[i]
    cspm = float(tcs[0][0]) / tdsum
    cspm = float("{0:.2f}".format(cspm))
    gpm = float(tgs[0][0]) / tdsum
    gpm = float("{0:.2f}".format(gpm))
    kda = float(kda[0][0])
    kda = float("{0:.2f}".format(kda))
    topchamps = g.db.execute('select champion_played, count(champion_played) as cpc from player_game_stats, (select game_date as gd, game_time as gt, tournament_id as tid from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=tid group by champion_played order by cpc desc limit 5').fetchall()
    winratio = g.db.execute('select count(winner) from (select game_date as ggd, game_time as ggt from player_game_stats where player_name=\'' + playerselected + '\')games, (select distinct tournament_id as tid from roster where player_name=\'' + playerselected + '\' and team_name=\'' + teamselected + '\')temp, game_stats where winner=\'' + teamselected + '\' and tournament_id=tid and game_date=ggd and game_time=ggt').fetchall()
    wr = float(winratio[0][0]) / gamesplayed[0][0]
    wr = float("{0:.2f}".format(wr))

    return render_template('psts.html', players=players, teams=teams, playerselected=playerselected, tournaments=tournaments, teamselected=teamselected, cspm=cspm, gpm=gpm, wr=wr, gamesplayed=gamesplayed, kda=kda, topchamps=topchamps, region=region, k=k, d=d, a=a, g=tgs, cs=tcs)

@app.route('/pststs', methods=['GET', 'POST'])
def pststs():
    playerselected = str(request.form.get('player'))
    teamselected = str(request.form.get('team'))
    tournamentselected = str(request.form.get('tournament'))
    players = g.db.execute('select player_name from player order by player_name').fetchall()
    query = 'select distinct team_name from roster where player_name=\'' + playerselected + '\' order by team_name'
    teams = g.db.execute(query).fetchall()
    query = 'select tournament_name, tournament_region, tournament_year, tournament_season from tournament where tournament.tournament_id in (select distinct tournament_id from roster where roster.team_name=\''+teamselected+'\' and roster.player_name=\''+playerselected+'\') order by tournament_id desc'
    temp = g.db.execute(query).fetchall()
    tournaments = []
    for t in temp:
        tournaments.append(str(t[0]) + ' ' + str(t[1]) + ' ' + str(t[2]) + ' ' + str(t[3]))

    region = g.db.execute('select team_region from team where team_name=\'' + teamselected + '\'').fetchall()
    t = tournamentselected.split()
    if t[2] == 'America':
        x = [t[0], (t[1] + ' ' + t[2]), t[3], t[4]]
        del t[:]
        t = x[:]
    else:
        x = [t[0], t[1], t[2], t[3]]
        del t[:]
        t = x[:]
    query = 'select tournament_id from tournament where tournament_region=\'' + t[1] + '\' and tournament_year=' + t[2] + ' and tournament_season=\'' + t[3] + '\''
    tem = g.db.execute(query).fetchall()
    tid = str(tem[0][0])
    kda = g.db.execute('select (sum(kills)+sum(assists))*1.0/sum(deaths) as kda from (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    k = g.db.execute('select sum(kills) as k from (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    d = g.db.execute('select sum(deaths) as d from (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    a = g.db.execute('select sum(assists) as a from (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp, player_game_stats where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    tcs = g.db.execute('select sum(cs) from player_game_stats, (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    tgs = g.db.execute('select sum(gold)/10 from player_game_stats, (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    gamesplayed = g.db.execute('select count(player_name) as gamesplayed from player_game_stats, (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + '').fetchall()
    games = g.db.execute('select g.game_date,g.game_time,g.duration from (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp, player_game_stats as p,game_stats as g  where player_name=\'' + playerselected + '\' and g.game_date=p.game_date and g.game_time=p.game_time and g.tournament_id=p.tournament_id  and p.game_date=gd and p.game_time=gt and p.tournament_id=' + tid + '').fetchall()
    tduration = []
    tdsum = 0
    for i in games:
        tduration.append(i[2])
    for i, j in enumerate(tduration):
        j = j.replace(':', '.')
        tduration[i] = float(j)
    for i in range(0, len(tduration)):
        tdsum += tduration[i]
    cspm = float(tcs[0][0]) / tdsum
    cspm = float("{0:.2f}".format(cspm))
    gpm = float(tgs[0][0]) / tdsum
    gpm = float("{0:.2f}".format(gpm))
    kda = float(kda[0][0])
    kda = float("{0:.2f}".format(kda))
    topchamps = g.db.execute('select champion_played, count(champion_played) as cpc from player_game_stats, (select game_date as gd, game_time as gt from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + ')temp where player_name=\'' + playerselected + '\' and game_date=gd and game_time=gt and tournament_id=' + tid + ' group by champion_played order by cpc desc limit 5').fetchall()
    winratio = g.db.execute('select count(winner) from (select game_date as ggd, game_time as ggt from player_game_stats where player_name=\'' + playerselected + '\' and tournament_id=' + tid + ')games, game_stats where winner=\'' + teamselected + '\' and tournament_id=' + tid + ' and game_date=ggd and game_time=ggt').fetchall()
    wr = float(winratio[0][0]) / gamesplayed[0][0]
    wr = float("{0:.2f}".format(wr))

    return render_template('pststs.html', players=players, teams=teams, playerselected=playerselected, tournaments=tournaments, teamselected=teamselected, tournamentselected=tournamentselected, cspm=cspm, gpm=gpm, wr=wr, gamesplayed=gamesplayed, kda=kda, topchamps=topchamps, region=region, k=k, d=d, a=a, g=tgs, cs=tcs)


@app.route('/ts', methods=['GET', 'POST'])
def ts():
    teamselected = str(request.form.get('team'))
    teams = g.db.execute('select team_name from team order by team_name').fetchall()
    query = 'select player_name, tournament_id from roster where team_name=\'' + teamselected + '\' order by tournament_id desc'
    cur = g.db.execute(query).fetchall()
    t = cur[0][1]
    roster = []
    for c in cur:
        if c[1] == t:
            roster.append(str(c[0]))
    roster.sort()
    temp = g.db.execute('select tournament_name, tournament_region, tournament_year, tournament_season from (select distinct tournament_id as tid from roster where team_name=\'' + teamselected + '\')tt, tournament where tournament_id=tid order by tournament_id desc').fetchall()
    tournaments = []
    for t in temp:
        tournaments.append(str(t[0]) + ' ' + str(t[1]) + ' ' + str(t[2]) + ' ' + str(t[3]))

    region = g.db.execute('select team_region from team where team_name=\'' + teamselected + '\'').fetchall()
    gamesplayed = g.db.execute('select count(*) as gamesplayed from game_stats where blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\'').fetchall()
    winratio = g.db.execute('select count(*) from game_stats where winner=\'' + teamselected + '\'').fetchall()
    wr = float(winratio[0][0]) / gamesplayed[0][0]
    wr = float("{0:.2f}".format(wr))

    return render_template('ts.html', teams=teams, tournaments=tournaments, teamselected=teamselected, wr=wr, gamesplayed=gamesplayed, region=region, roster=roster)


@app.route('/tsts', methods=['GET', 'POST'])
def tsts():
    teamselected = str(request.form.get('team'))
    tournamentselected = str(request.form.get('tournament'))
    t = tournamentselected.split()
    if t[2] == 'America':
        x = [t[0], (t[1] + ' ' + t[2]), t[3], t[4]]
        del t[:]
        t = x[:]
    else:
        x = [t[0], t[1], t[2], t[3]]
        del t[:]
        t = x[:]
    query = 'select tournament_id from tournament where tournament_region=\'' + t[1] + '\' and tournament_year=' + t[2] + ' and tournament_season=\'' + t[3] + '\''
    tem = g.db.execute(query).fetchall()
    tid = str(tem[0][0])
    teams = g.db.execute('select team_name from team order by team_name').fetchall()
    query = 'select player_name from roster where team_name=\'' + teamselected + '\' and tournament_id=' + tid + ' order by player_name asc'
    roster = g.db.execute(query).fetchall()
    temp = g.db.execute('select tournament_name, tournament_region, tournament_year, tournament_season from (select distinct tournament_id as tid from roster where team_name=\'' + teamselected + '\')tt, tournament where tournament_id=tid order by tournament_id desc').fetchall()
    tournaments = []
    for x in temp:
        tournaments.append(str(x[0]) + ' ' + str(x[1]) + ' ' + str(x[2]) + ' ' + str(x[3]))

    region = g.db.execute('select team_region from team where team_name=\'' + teamselected + '\'').fetchall()
    gamesplayed = g.db.execute('select count(*) as gamesplayed from game_stats where (blue_team=\'' + teamselected + '\' or red_team=\'' + teamselected + '\') and tournament_id=' + tid + '').fetchall()
    winratio = g.db.execute('select count(*) from game_stats where winner=\'' + teamselected + '\' and tournament_id=' + tid + '').fetchall()
    wr = float(winratio[0][0]) / gamesplayed[0][0]
    wr = float("{0:.2f}".format(wr))

    return render_template('tsts.html', teams=teams, tournaments=tournaments, teamselected=teamselected, tournamentselected=tournamentselected, wr=wr, gamesplayed=gamesplayed, region=region, roster=roster)


@app.route('/tos', methods=['GET', 'POST'])
def tos():
    temp = g.db.execute('select tournament_name,tournament_region,tournament_year,tournament_season from tournament order by tournament_year desc').fetchall()
    tournaments = []
    for t in temp:
        tournaments.append(str(t[0]) + ' ' + str(t[1]) + ' ' + str(t[2]) + ' ' + str(t[3]))
    tournamentselected = str(request.form.get('tournament'))
    t = tournamentselected.split()
    if t[2] == 'America':
        x = [t[0], (t[1] + ' ' + t[2]), t[3], t[4]]
        del t[:]
        t = x[:]
    else:
        x = [t[0], t[1], t[2], t[3]]
        del t[:]
        t = x[:]
    query = 'select tournament_id from tournament where tournament_region=\'' + t[1] + '\' and tournament_year=' + t[2] + ' and tournament_season=\'' + t[3] + '\''
    tem = g.db.execute(query).fetchall()
    tid = str(tem[0][0])
    name = t[0]
    region = t[1]
    year = t[2]
    season = t[3]
    p = g.db.execute('select tournament_prize from tournament where tournament_id=' + tid + '').fetchall()
    f = g.db.execute('select tournament_first from tournament where tournament_id=' + tid + '').fetchall()
    s = g.db.execute('select tournament_second from tournament where tournament_id=' + tid + '').fetchall()
    return render_template('tos.html', tournaments=tournaments, tournamentselected=tournamentselected, p=p, f=f, s=s, name=name, region=region, year=year, season=season)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
