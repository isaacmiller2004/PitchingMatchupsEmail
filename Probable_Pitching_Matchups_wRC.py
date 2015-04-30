import urllib2
from bs4 import BeautifulSoup
import smtplib
import datetime
import sys
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def main():
	data_url = 'http://www.fantasypros.com/mlb/probable-pitchers.php'

	content = urllib2.urlopen(data_url)
	soup = BeautifulSoup(content)
	data = soup.find('table', {'class':'table table-condensed'})
	tdTags = data.findAll('td')

	today = datetime.date.today()
	todayFormatted = str(today.month) + '/' + str(today.day) + '/' + str(today.year)
	todayFormattedWithoutYear = str(today.month) + '/' + str(today.day)

	myTeam = ['C. Kluber', 'A. Bradley', 'Y. Ventura', 'T. Walker', 'D. Keuchel', 'C. Tillman', 'H. Bailey', 'J. Nelson', 'N. Martinez']
	daysOfTheWeek = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

	days = []
	for i in range (0, len(daysOfTheWeek)):
		dayIndex = today.weekday()+i
		if dayIndex > 6: dayIndex -= 7
		days.append(daysOfTheWeek[dayIndex])	

	dates = [todayFormattedWithoutYear]
	for i in range(1,7):
		date = datetime.date.today() + datetime.timedelta(days=i)
		date = str(date.month) + '/' + str(date.day)
		dates.append(date)

	wRC_Dict = buildwRC()
		
	message_text = ''
	dataList = []
	pitcherList = []
	dayCount = 0		

	for line in tdTags:
		l = str(line.findAll(text=True))
		if len(l) < 3 or len(l) > 18 or l[len(l)-5:len(l)-2] == 'TBD':
			dataList.append(l)

	for line in dataList:
		if len(line) == 2:
			pitcherList.append(('N/A', 'N/A', dayCount))
			dayCount += 1
			if dayCount == 7:
				dayCount = 0
			continue
		p0 = line.split()[0]
		team = p0[3:len(p0)-2]
		if team[0] != '@': team = 'vs. ' + team
		p1 = line.split()[1]
		if p1 == "u'TBD']":
			pitcherList.append(('TBD', team, dayCount))
			dayCount += 1
			if dayCount == 7:
				dayCount = 0
			continue
		p1 = p1[2:len(p1)]
		p2 = line.split()[2]
		p2 = p2[:len(p2)-2]
		pitcher = p1 + ' ' + p2
		pitcherList.append((pitcher, team, dayCount))
		dayCount += 1
		if dayCount == 7: dayCount = 0

	message_text = '<p><b>wRC+ from Fangraphs in parentheses</b>'

	for pitcher in myTeam:
		starts = [ item for item in pitcherList if item[0] == pitcher ]
		numStarts = len(starts)
		if numStarts == 0:
			message_text += '<p><b>' + pitcher.ljust(15) + ':</b> No scheduled starts'
		elif numStarts == 1:
			wRC = wRC_Dict[getTeam(starts[0][1])]
			color = getwRCColor(wRC)
			wRC = "<b><font color = '" + color + "'>" + '(' + str(wRC) + ')</font></b>'
			message_text += '<p><b>' + pitcher.ljust(15) + ':</b> ' + days[starts[0][2]]+ ' ' + str(dates[starts[0][2]]) + ' ' + starts[0][1] + ' ' + wRC
		elif numStarts == 2:
			wRC1 = wRC_Dict[getTeam(starts[0][1])]
			wRC2 = wRC_Dict[getTeam(starts[1][1])]
			color1 = getwRCColor(wRC1)
			color2 = getwRCColor(wRC2)
			wRC1 = "<b><font color = '" + color1 + "'>" + '(' + str(wRC1) + ')</font></b>'
			wRC2 = "<b><font color = '" + color2 + "'>" + '(' + str(wRC2) + ')</font></b>'
			message_text += '<p><b>' + pitcher.ljust(15) + ':</b> ' + days[starts[0][2]] + ' ' + str(dates[starts[0][2]]) + ' ' 
			message_text += starts[0][1] + ' ' + wRC1 + ' & ' + days[starts[1][2]] + ' ' + str(dates[starts[1][2]]) + ' ' + starts[1][1] + ' ' + wRC2 

	sendMail(message_text)

def getwRCColor(wRC):	
	if wRC < 100: return 'green'
	if wRC > 100: return 'red'
	if wRC == 100: return 'black'
	
def buildwRC():
	data_url = 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=8&season=2015&month=0&season1=2015&ind=0&team=0,ts&rost=0&age=0&filter=&players=0&sort=16,d'

	content = urllib2.urlopen(data_url)
	soup = BeautifulSoup(content)
	data = soup.find('table', {'class':'rgMasterTable'})
	tdTagswRC = data.findAll('td', {'bgcolor': '#E5E5E5'})
	teams = data.findAll('a')
	
	count = 0
	teamDict = dict()

	for i in range(20,50):
		tmp = str(teams[i].findAll(text=True))
		team = tmp[3:len(tmp)-2]
		stat = tdTagswRC[count]
		stat = str(stat.findAll(text=True))[3:len(stat)-3]
		teamDict[teamMapping(team)] = int(stat)
		count += 1
	
	return teamDict

def getTeam(team):
	if team[0] == '@':
		return team[1:]
	else:
		return team[4:]
		
def sendMail(message_text):

	today = datetime.date.today()
	todayFormatted = str(today.month) + '/' + str(today.day) + '/' + str(today.year)
	
	fromEmail = 'fromEmail@example.com'
	toEmail = 'toEmail@example.com'
	subj = 'Probable Pitching Matchups - Week of ' + todayFormatted

	msg = MIMEMultipart()
	msg['From'] = fromEmail
	msg['To'] = toEmail
	msg['Subject'] = subj
	msg.attach(MIMEText(message_text, 'html'))	
	text = msg.as_string()
	username = fromEmail
	password = 'XXXXXXXXX'  #password for fromEmail

	try:
		server = smtplib.SMTP_SSL()
		server.connect("smtp.mail.yahoo.com", 465)  #Change settings for your fromEmail 
		server.login(username, password)
		server.sendmail(fromEmail, toEmail, text)
		server.quit()
		print 'Email sent successfully.'
	except Exception, e:
		print 'Unable to send email', str(e)
		
def teamMapping(team):

	if team == 'Diamondbacks': return 'ARI'
	if team == 'Braves': return 'ATL'
	if team == 'Orioles': return 'BAL'
	if team == 'Red Sox': return 'BOS'
	if team == 'Cubs': return 'CHC'
	if team == 'Reds': return 'CIN'
	if team == 'Indians': return 'CLE'
	if team == 'Rockies': return 'COL'
	if team == 'White Sox': return 'CWS'
	if team == 'Tigers': return 'DET'
	if team == 'Astros': return 'HOU'
	if team == 'Royals': return 'KC'
	if team == 'Angels': return 'LAA'
	if team == 'Dodgers': return 'LAD'
	if team == 'Marlins': return 'MIA'
	if team == 'Brewers': return 'MIL'
	if team == 'Twins': return 'MIN'
	if team == 'Mets': return 'NYM'
	if team == 'Yankees': return 'NYY'
	if team == 'Athletics': return 'OAK'
	if team == 'Phillies': return 'PHI'
	if team == 'Pirates': return 'PIT'
	if team == 'Padres': return 'SD'
	if team == 'Mariners': return 'SEA'
	if team == 'Giants': return 'SF'
	if team == 'Cardinals': return 'STL'
	if team == 'Rays': return 'TB'
	if team == 'Rangers': return 'TEX'
	if team == 'Blue Jays': return 'TOR'
	if team == 'Nationals': return 'WAS'
	
	return 'Team not found'
	
if __name__ == "__main__":
	main()