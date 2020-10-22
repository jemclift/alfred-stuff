import requests, sys, os, datetime, math

cache = "<some path>"
refresh_streamers = True
personal_id = '<personal id>'

headers = {
	'client-id': '<client id>',
	'Authorization': 'Bearer <oath token>'
}

# Get list of followed streamers

if refresh_streamers:
	# Get first batch of followed streamers
	responses = []
	streamers = requests.get('https://api.twitch.tv/helix/users/follows?first=100&from_id='+personal_id, headers=headers).json()
	responses.append(streamers)
	
	# Get more batches until all streamers are fetched
	while streamers['pagination']:
		streamers = requests.get('https://api.twitch.tv/helix/users/follows?first=100&from_id='+personal_id+'&after='+streamers['pagination']['cursor'], headers=headers).json()
		responses.append(streamers)

	# Write all of the responsed to a file with a max of 100 arguments (twitch api limit)
	with open(cache+'users.txt', 'w') as file:
		for batch in responses:
			file.write('https://api.twitch.tv/helix/streams?first=100')
			for num,streamer in enumerate(batch['data']):
				if (num+1)%100==0:
					file.write("\nhttps://api.twitch.tv/helix/streams?first=10")
				file.write('&user_id='+streamer['to_id'])

# Make a json of the results for alfred

output="{\"items\": [\n"

with open(cache+'users.txt', 'r') as file:
	for link in file:
		streams = requests.get(link, headers=headers).json()

		for stream in streams['data']:
			# Cache image if not already
			if not os.path.isfile(cache+stream['user_name']+".png"):
				user_info = requests.get("https://api.twitch.tv/helix/users?id="+stream['user_id'], headers=headers)
				image = requests.get(user_info.json()["data"][0]['profile_image_url'].replace("{width}","38").replace("{height}","38"))
				with open(cache+stream['user_name']+".png", 'wb') as file:
					file.write(image.content) 
						
			date = datetime.datetime.strptime(stream['started_at'],"%Y-%m-%dT%H:%M:%SZ")
			difference = datetime.datetime.utcnow() - date
			date_str = str(int(math.floor(difference.seconds/3600)))+' Hours, '+str(int(math.floor(difference.seconds%3600/60)))+' Minutes'
				
			output +="""  {
    \"title\": \""""+stream['user_name']+" - "+stream['title']+"""\",
    \"subtitle\": \""""+str(stream['viewer_count'])+" Viewers, Live for "+date_str+"""\",
    \"arg\": \"https://www.twitch.tv/"""+stream['user_name']+"""/\",
    \"autocomplete\": \""""+stream['user_name']+"""\",
    \"icon\": {
        \"path\": \""""+cache+stream['user_name']+""".png\"
    }
  },\n"""

	output=output[:-2]+"\n]}"
	
sys.stdout.write(output)
