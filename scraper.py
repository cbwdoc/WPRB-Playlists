"""
Modular version of WPRB playlist web scraper containing all functions:
Written by Casey Dougherty June 2019 through March 2020

Made to feed the database for Django or some other type of project that uses data from the existing website.

Start Python shell in this directory and begin with $import scraper

All dependencies are imported with the functions.

"""
import logging, requests, pdb, sqlite3
from bs4 import BeautifulSoup

error_log = open('errors.log', 'w')

def log_error(e):
	logging.getLogger('test_case')
	logging.basicConfig(filename= 'errors.log',
						filemode='w',
						format='%(asctime)s: %(message)s',
						datefmt='%y-%b-%d %H:%M:%S',
						level=logging.ERROR
	)
	logging.error(e)

# contains month dictionary, returns 2 char string with number value
def getMonthAsDigits(m):
	months = {
		'January' : '01',
		'February' : '02',
		'March' : '03',
		'April' : '04',
		'May' : '05',
		'June' : '06',
		'July' : '07',
		'August' : '08',
		'September' : '09',
		'October' : '10',
		'November' : '11',
		'December' : '12'
	}	
	month = months[m]
	return month

# contains month dictionary, returns 2 char string with number value
def getDaysInMonth(m):
	months = {
		'01' : 31,
		'02' : 28,
		'03' : 31,
		'04' : 30,
		'05' : 31,
		'06' : 30,
		'07' : 31,
		'08' : 31,
		'09' : 30,
		'10' : 31,
		'11' : 30,
		'12' : 31
	}	
	month = months[m]
	return month

# getter functions for database queries
def get_min_playlist():
	try:
		db = sqlite3.connect('db.sqlite3')
	except Error as e:
		print(e)		
	cursor = db.cursor()
	query = 'SELECT MIN(playlist_id) FROM playlists_playlist;'

	return cursor.execute(query).fetchone()[0]

def get_max_playlist():
	try:
		db = sqlite3.connect('db.sqlite3')
	except Error as e:
		print(e)		
	cursor = db.cursor()
	query = 'SELECT MAX(playlist_id) FROM playlists_playlist;'

	return cursor.execute(query).fetchone()[0]


# get data from playlists
def get_playlist_data(playlist_id):
	# open database
	db = sqlite3.connect('db.sqlite3')
	cursor = db.cursor()

	# open playlist page by show_id
	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/?show_id=" + str(playlist_id)).text, 'html.parser')

	try:
		dj_id = int(soup.findAll('span', class_ = 'playlist-link')[-1].findAll('a')[0].get('href').split('=')[1])
	except:
		dj_id = -1
		log_error("ERROR: Unable to read DJ ID from playlist %d." % (playlist_id))

	
	key_val = str(playlist_id)
	if dj_id < 1000:
		key_val = key_val + '0'
		if dj_id < 100:
			key_val = key_val + '0'
			if dj_id < 10:
				key_val = key_val + '0'
	key_val = key_val + str(abs(dj_id))
	counter = '1'
	
	# iterate each row
	for row in soup.findAll('tr', class_ = "playlist-row"):
		if int(counter) < 100:
			counter = '0' + counter
			if int(counter) < 10:
				counter = '0' + counter
		# initialize dictionary for feeding db
		song = {
			'key_val' : int(key_val + counter),
			'artist' : "",
			'song' : "",
			'album' : "",
			'label' : "",
			'comment' : "",
			'emph' : 0,
			'request' : 0,
			'comp' : 0,
			'playlist_id': playlist_id,
			'dj_id' : dj_id
		}

		# iterate cells of each row
		for cell in row.findAll('td', class_ = "playlist-cell"):
			# match column class with key value and add to dictionary
			key_name = str(cell.get('class')).split('-')[-1].strip("']")			
			# not adding comps for some reason
			if key_name == 'comp' or key_name == 'request':
				if len(cell.text) > 0:
					song[key_name] = '1'				
			# allow comp to be a boolean value
			elif key_name == 'emph' and cell.text == '*':
				song[key_name] = 1
			else:
				song[key_name] = cell.text
		try:
			cursor.execute('INSERT INTO playlists_content VALUES (:key_val, :artist, :song, :album, :label, :comment, :emph, :request, :comp, :dj_id, :playlist_id)', song)
			db.commit()
		except sqlite3.IntegrityError as err:
			print("ERROR importing playlist for show " + str(playlist_id) + '.\n' + str(err))
			log_error("ERROR importing playlist for show " + str(playlist_id) + '.\n' + str(err))

		counter = str(int(counter) + 1)
			
	db.close()

def get_show_info(id):
	data = {
		'dj_id': "",
		'dj_name': "",
		'id': id,
		'day': "",
		'program_name': "",
		'end_time': "",
		'start_time': "",
		'subtitle': "",
		'genre': "",
		'description': []
	}
	
	# simple elements to extract, add checks that they are not null
	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/?show_id=" + str(data['id'])).text, 'html.parser')

	if soup.findAll('h2', class_ = 'playlist-title-text'):
		data['program_name'] = soup.findAll('h2', class_ = 'playlist-title-text')[0].text

	if soup.findAll('h3', class_ = 'dj-name'):
		data['dj_name'] = soup.findAll('h3', class_ = 'dj-name')[0].text.split(' ')			
		# regardless of the length of the list, it begins with ['', 'with']
		del data['dj_name'][1]
		del data['dj_name'][0]			
		data['dj_name'] = ' '.join(data['dj_name'])
	

	if soup.findAll('h4', class_ = 'playlist-subtitle-text'):
		data['subtitle'] = soup.findAll('h4', class_ = 'playlist-subtitle-text')[0].text
			
	data['description'] = []
	for a in soup.findAll('span', class_ = 'playlist-link'):
		for b in a.findAll('a'):
			data['description'].append(str(b))
	data['dj_id'] = data['description'][-1].split('id=')[1].split('"')[0]
	del data['description'][-1]
	if data['description']:
		if len(data['description']) > 1:
			data['description'] = '\n<br />\n'.join(data['description'])
		else:
			data['description'] = data['description'][0]
	else:
		data['description'] = ""
		
	timeframe = soup.findAll('span', class_ = 'playlist-time')[0].text.split('\n')
	if timeframe:
		genre = timeframe[-2].split(' ')
		timeframe = timeframe[0].split(',')
		data['day'] = timeframe[0]
		date = timeframe[1].split(' ')
		if int(date[-1]) < 10:
			date[-1] = '0' + date[-1]
		date = timeframe[2].strip(' ') + '-' + getMonthAsDigits(date[1]) + '-' + date[2]
		data['start_time'] = date + ' ' + genre[0] + ':00'
		del genre[:2]
		
		genre = ' '.join(genre)
		if genre[0] > genre[:5]:
			date[-1] = '0' + date[-1]
		data['end_time'] = date  + ' ' + genre[:5] + ':00'
		if data['start_time'] > data['end_time']:
			date = date.split('-')
			date[-1] = str(int(date[-1]) + 1)
			if int(date[-1]) < 10:
				date[-1] = '0' + date[-1]				
			#pdb.set_trace()
			elif int(date[-1]) > getDaysInMonth(date[1]) and (int(date[-1]) >= getDaysInMonth(date[1]) + 2 or date[1] != '02' or (int(date[0]) % 4 != 0 or int(date[0]) % 100 == 0)):
				date[-1] = '01'
				date[1] = str(int(date[1]) + 1)
				if int(date[1]) < 10:
					date[1] = '0' + date[1]
				elif int(date[1]) > 12:
					date[0] = str(int(date[0]) + 1)
					date[1] = '01'

			data['end_time'] = '-'.join(date) + ' ' + genre[:5] + ':00'

		data['genre'] = genre.split(genre[:5])[1]

	return data

# get all playlists for a particular DJ
def get_dj_playlists(dj_id):
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('db.sqlite3')
	cursor = db.cursor()
	ids = []

	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/dj/?id=" + str(dj_id)).text, 'html.parser')

	for a in soup.findAll('ul', class_ = "djplaylistlist")[0].findAll('a'):
		
		id = a.get('href').split('=')[1]

		ids.append(id)

		data = get_show_info(id)
		#pdb.set_trace()
		get_playlist_data(data['id'])
		#pdb.set_trace()
		print(data)
		
		try:
			cursor.execute('INSERT INTO playlists_playlist VALUES (:dj_id, :dj_name, :playlist_id, :day, :program_name, :end_time, :start_time, :subtitle, :genre, :description)', data)
			'''
			data = {
		'dj_id': "",
		'dj_name': "",
		'id': id,
		'start_time': "",
		'end_time': "",
		'day': "",
		'program_name': "",
		'subtitle': "",
		'genre': "",
		'description': []
	}
			'''
			db.commit()
		except sqlite3.IntegrityError as err:
			print("ERROR importing playlists for DJ " + dj_id + '.\n' + str(err))
			log_error("ERROR importing playlists for DJ " + dj_id + '.\n' + str(err))

	db.close()
	
	return ids

# get playlists from all DJ's starting with dj_id
def get_all_playlists_by_dj(dj_id):
	
	num_skips = 0
	# a gap of 5 exists already within the database, need to trim the upper limit at end of function
	while(num_skips < 6):			
		dj_playlists = get_dj_playlists(dj_id)
		if dj_playlists:
			print(' ...')
			num_skips = 0
		else:
			log_error('ERROR - Could not find playlists for DJ: %d' % (dj_id))
			print("ERROR - Could not find playlists for DJ: %d" % (dj_id))
			num_skips += 1
		dj_id+=1
	# trim log to the true upper limit
	print("END - Ended test at DJ %d" % (dj_id))

# get playlists going up from a specified id
def get_all_playlists_ascend(playlist_id):
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('db.sqlite3')
	cursor = db.cursor()

	num_skips = 0
	# a gap of 5 exists already within the database, need to trim the upper limit at end of function
	while(num_skips < 6):			
		get_playlist_data(playlist_id)
		data = get_show_info(playlist_id)
		# open database & initialize dictionary to feed records
		try:
			cursor.execute('INSERT INTO playlists_playlist VALUES (:id, :dj_id, :dj_name, :program_name, :day, :start_time, :end_time, :subtitle, :genre, :description)', data)
			db.commit()
			print(data)
		except sqlite3.IntegrityError as err:
			print("ERROR importing playlists for show " + str(playlist_id) + '.\n' + str(err))
			log_error("ERROR importing playlists for show " + str(playlist_id) + '.\n' + str(err))


		playlist_id+=1
	db.close()
	# trim log to the true upper limit
	print("END - Ended test at playlist %d" % (playlist_id))

# get playlists going down from a specified id
def get_all_playlists_descend(playlist_id):
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('db.sqlite3')
	cursor = db.cursor()

	num_skips = 0
	# a gap of 5 exists already within the database, need to trim the upper limit at end of function
	while(num_skips < 6):			
		get_playlist_data(playlist_id)
		data = get_show_info(playlist_id)
		# open database & initialize dictionary to feed records
		try:
			cursor.execute('INSERT INTO playlists_playlist VALUES (:id, :dj_id, :dj_name, :program_name, :day, :start_time, :end_time, :subtitle, :genre, :description)', data)
			db.commit()
			print(data)
		except sqlite3.IntegrityError as err:
			print("ERROR importing playlists for show " + str(playlist_id) + '.\n' + str(err))
			log_error("ERROR importing playlists for show " + str(playlist_id) + '.\n' + str(err))
		playlist_id-=1

	db.close()
	# trim log to the true upper limit
	print("END - Ended test at playlist %d" % (playlist_id))

# one more method for last 10 days to update
def get_last_10_days():
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('db.sqlite3')
	cursor = db.cursor()

	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/recentplaylists/").text, 'html.parser')
	
	for i in soup.findAll('div', class_='recentplaylists')[0].findAll('a'):
		id = i.get('href').split('=')[1]

		data = get_show_info(id)

		# add queries to check if playlists or DJs are in database	
		get_playlist_data(data['id'])
		# get_dj_playlists(data['dj_id'])
		# open database & initialize dictionary to feed records
		try:
			cursor.execute('INSERT INTO playlists_playlist VALUES (:id, :dj_id, :dj_name, :start_time, :end_time, :day, :program_name, :subtitle, :genre, :description)', data)
			db.commit()
		except sqlite3.IntegrityError as err:
			print("ERROR importing playlists for DJ " + dj_id + '.\n' + str(err))
			log_error("ERROR importing playlists for DJ " + dj_id + '.\n' + str(err))

	db.close()
