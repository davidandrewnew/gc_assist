import tweepy
import simplekml
import re
import datetime

# Credentials
bearer_token = "your bearer token here"

# Misc
tweet_fields = ['author_id', 'created_at']
delimiters   = '[\s,()°]\s*'

# This function returns a list of coordinates (with links,times) from tweet
def get_coords(tweet):
    # Initialize output
    tweet_coords = []
    tweet_links  = []
    tweet_times  = []

    # Split tweet into words separated by delimiters
    words = re.split(delimiters, tweet.text)

    # Iterate through pairs of words
    skip_word = False
    for i in range(len(words)-1):
        if skip_word:
            skip_word = False
        else:
            # Is this word a floating point number?
            try:
                float(words[i])
            except:
                pass
            else:
                # Is the next word also a floating point number?
                try:
                    float(words[i+1])
                except:
                    pass
                else:
                    lat = float(words[i])
                    lon = float(words[i+1])
                    
                    # More error checking
                    if lat > -90. and lat < 90. and lon > -180. and lon < 360.:
                        # Set flag to skip next word since already part of this coordinate
                        skip_word = True            

                        # Append to geolocation
                        user = client.get_user(id=tweet.author_id)
                        tweet_coords.append( (lon,lat))
                        tweet_links.append('https://twitter.com/' + user.data.username + '/status/' + str(tweet.id))
                        tweet_times.append(tweet.created_at)
                        
    return tweet_coords,tweet_links,tweet_times

#
# Get coordinates
#

# Initialize Twitter API v2 client
client = tweepy.Client(bearer_token)

# Get GeoConfirmed's user ID
response = client.get_user(username='GeoConfirmed')
user_id  = response.data.id

# Build list of coordinates from GeoConfirmed's tweets
conf_coords = [] # 'conf' for 'confirmed'
conf_links  = []
conf_times  = []
response = client.get_users_tweets(user_id, max_results=100, tweet_fields=tweet_fields) # get tweets
for tweet in response.data:
    coords,links,times = get_coords(tweet) # get coordinates
    conf_coords.extend(coords)
    conf_links.extend(links)
    conf_times.extend(times)
    
# Build list of coordinates from GeoConfirmed's mentions
sub_coords = [] # 'sub' for 'submitted'
sub_links  = []
sub_times  = []
response   = client.get_users_mentions(user_id, max_results=100, tweet_fields=tweet_fields) # get mentions
for tweet in response.data:
    coords,links,times = get_coords(tweet) # get coordinates
    for coord,link,time in zip(coords,links,times):
        # Check if already part of confirmed coordinate list
        is_confirmed = False
        for conf_coord in conf_coords:
            # Is not within rounding error of coordinates from confirmed list?
            if abs( coord[0] - conf_coord[0] ) < 2.E-6 and abs( coord[1] - conf_coord[1] ) < 2.E-6: 
                is_confirmed = True
        # Append coordinates to list        
        if not is_confirmed:
            sub_coords.append(coord)
            sub_links.append(link)
            sub_times.append(time)

#
# Print information about age of geolocations
#

# Get datetimes
now = datetime.datetime.utcnow()

sub_oldest  = min(sub_times)
conf_oldest = min(conf_times)

sub_newest  = max(sub_times)
conf_newest = max(conf_times)

# Get age of geolocations in hours
old_sub_hours  = ( now - sub_oldest.replace(tzinfo=None) ).total_seconds()/3600.
old_conf_hours = ( now - conf_oldest.replace(tzinfo=None) ).total_seconds()/3600.

new_sub_hours  = ( now - sub_newest.replace(tzinfo=None) ).total_seconds()/3600.
new_conf_hours = ( now - conf_newest.replace(tzinfo=None) ).total_seconds()/3600.

# Print to terminal
print( '# Unconfirmed: %2d' % len(sub_coords) )
print( '# Confirmed:   %2d' % len(conf_coords) ) 
print( 'Newest / oldest unconfirmed: %6.2f / %6.2f hours ago' % (new_sub_hours,old_sub_hours) )
print( 'Newest / oldest confirmed:   %6.2f / %6.2f hours ago' % (new_conf_hours,old_conf_hours) )

#
# Save to coordinates to KML file
#

# Initialize
kml = simplekml.Kml()

# Save submitted coordinates
sub_folder = kml.newfolder(name='Unconfirmed')
for coord,link,time in zip(sub_coords,sub_links,sub_times):
    point = sub_folder.newpoint(description=link, coords=[coord])
    point.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/blu-circle.png'

# Save confirmed coordinates
conf_folder = kml.newfolder(name='Confirmed')    
for coord,link,time in zip(conf_coords,conf_links,conf_times):
    point = conf_folder.newpoint(description=link, coords=[coord])
    point.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/red-circle.png'    
    
# Save
kml.save('gc_assist.kml')
