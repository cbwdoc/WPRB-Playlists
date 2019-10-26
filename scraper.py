"""
WPRB playlist web scraper

Made to feed the database for Django or some other type of project that uses data from the existing website.

Needs an update function that will get the most recent playlists and add them to the database.
Can get the most recent playlist from the table on http://wprb.com/playlists/recentplaylists/ or from #now-playing or #sidebar on every page of the site
"""
import logging, requests, pdb, sqlite3
from bs4 import BeautifulSoup


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

# get data from playlists
def get_playlist_data(dj_id, playlist_id):
	# open database
	db = sqlite3.connect('testdb.sqlite3')
	cursor = db.cursor()

	# open playlist page by show_id
	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/?show_id=" + str(playlist_id)).text, 'html.parser')
	# iterate each row
	for row in soup.findAll('tr', class_ = "playlist-row"):
		# initialize dictionary for feeding db
		song = {
			'artist' : "",
			'song' : "",
			'album' : "",
			'label' : "",
			'comment' : "",
			'emph' : "",
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
				song[key_name] = 'New Emph'
			else:
				song[key_name] = cell.text
		cursor.execute('INSERT INTO playlist_content VALUES (:artist, :song, :album, :label, :comment, :emph, :request, :comment, :playlist_id, :dj_id)', song)
		db.commit()
			
	db.close()

def get_show_info(id):
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
			print(data['description'])
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
		date = timeframe[2].strip(' ') + '-' + getMonthAsDigits(date[1]) + '-' + date[2]
		
		data['start_time'] = date + ' ' + genre[0] + ':00.000'

		del genre[:2]
		
		genre = ' '.join(genre)
		data['end_time'] = date  + ' ' + genre[:5] + ':00.000'		
		data['genre'] = genre.split(genre[:5])[1]

	return data

# get all playlists for a particular DJ
def get_dj_playlists(dj_id):
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('testdb.sqlite3')
	cursor = db.cursor()
	ids = []

	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/dj/?id=" + str(dj_id)).text, 'html.parser')

	for a in soup.findAll('ul', class_ = "djplaylistlist")[0].findAll('a'):
		id = a.get('href').split('=')[1]

		ids.append(id)

		data = get_show_info(id)
		
		get_playlist_data(dj_id, data['id'])

		print(data)
		
		# check unique constraints
		cursor.execute('INSERT INTO playlists VALUES (:dj_id, :dj_name, :id, :start_time, :end_time, :day, :program_name, :subtitle, :genre, :description)', data)
		db.commit()
		
	db.close()
	
	return ids

# get playlists from all DJ's starting with dj_id
def get_all_playlists(dj_id):
	logging.getLogger('test_case')
	logging.basicConfig(filename='logs/' + log_type + '.log',
						filemode='w',
						format='%(asctime)s: %(message)s',
						datefmt='%y-%b-%d %H:%M:%S',
						level=logging.ERROR
	)
	num_skips = 0
	# a gap of 5 exists already within the database, need to trim the upper limit at end of function
	while(num_skips < 6):			
		dj_playlists = get_dj_playlists(dj_id)
		if dj_playlists:
			print(' ...')
			num_skips = 0
		else:
			#logging.error('ERROR - Could not find playlists for DJ: %d' % (dj_id))
			print("ERROR - Could not find playlists for DJ: %d" % (dj_id))
			num_skips += 1
		dj_id+=1
	# trim log to the true upper limit
	print("END - Ended test at DJ %d" % (dj_id))

# updates starting with most recent playlist and counting backwards until it crashes
def get_new_playlists():
	# open database & initialize dictionary to feed records
	db = sqlite3.connect('testdb.sqlite3')
	cursor = db.cursor()

	soup = BeautifulSoup(requests.get("http://wprb.com/playlists/recentplaylists/").text, 'html.parser')
	id = soup.findAll('div', class_='recentplaylists')[0].findAll('a')[0].get('href').split('=')[1].strip('u')
	
	while(id):	# while (id not in db)
		data = get_show_info(id)
	
		get_playlist_data(data['dj_id'], data['id'])
		
		# check unique constraints
		cursor.execute('INSERT INTO playlists VALUES (:dj_id, :dj_name, :id, :start_time, :end_time, :day, :program_name, :subtitle, :genre, :description)', data)
		db.commit()
		id = int(id) - 1

	db.close()


# main logic goes HERE

# to fill database from oldest to newest
# get_all_playlists(1)

# to update database from newest to oldest
# get_new_playlists()
