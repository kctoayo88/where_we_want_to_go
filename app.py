import os

from flask import Flask, request, abort

from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

import googlemaps

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('Your Token')
# Channel Secret
handler = WebhookHandler('Your Secret')

# listening the post request from /callback
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# dealing with message
@handler.add(MessageEvent, message = TextMessage)
def handle_message(event):
    # get the send message
    recived_message = TextSendMessage(text = event.message.text)
    msg = TextSendMessage()
    command_text = recived_message.text[0:4]
    location_text = recived_message.text[4:]

    # check the message contain '我想去 ' or not
    if(recived_message.text[0:4] == '我想去 '):
        #print('Got!')

        # set your gmap API key
        gmap_key = 'Your Google API key'
        # Initialize googlemaps object
        gmaps = googlemaps.Client(key = gmap_key)

        # use google map API to search the place and return the results
        found_result = gmaps.find_place(input = location_text, input_type = 'textquery', language = 'zh-TW')
        found_candidates = found_result['candidates']

        # check the results
        if len(found_candidates) == 0:
            msg = TextSendMessage(text = '抱歉 我找不到這個地方QQ')
            # the linebot replys the message
            line_bot_api.reply_message(event.reply_token, msg)

        else:
            # take the first result as the output
            place_id = found_candidates[0]['place_id']
            #print(first_place_id)
            
            # get detail imfo from the place_id
            place = gmaps.place(place_id = place_id, language = 'zh-TW')
            #print(place)
            
            # get the lat and lng from searching result
            place_lat =             place['result']['geometry']['location']['lat']
            place_lng =             place['result']['geometry']['location']['lng']
            
            # get the name from searching result
            place_name =            place['result']['name']

            # try to get the rating  of place from searching result
            try:
                place_rating =      place['result']['rating']
            except:
                place_rating = 'N/A'

            # combine the rating with address
            place_address =     place['result']['formatted_address']
            info = '評分：{}\n地址：{}'.format(place_rating, place_address[5:])

            # get streetview or provided photo
            if place_rating == 'N/A':
                photo_url = 'https://maps.googleapis.com/maps/api/streetview?size=600x400&location={},{}&heading=151.78&pitch=-0.76&key={}'.format(place_lat, place_lng, gmap_key)
            else:
                # try to get the photo of place from searching result
                try:
                    place_photo =       place['result']['photos'][0]['photo_reference']
                    place_photo_width = place['result']['photos'][0]['width']
                    photo_url = 'https://maps.googleapis.com/maps/api/place/photo?key={}&photoreference={}&maxwidth={}'.format(gmap_key, place_photo, place_photo_width)
                except:
                    photo_url = None

            map_url = 'https://www.google.com/maps/search/?api=1&query={},{}&query_place_id={}'.format(place_lat, place_lng, place_id)
            #print(photo_url)
            #print(map_url)
            
            # create a button template
            msg = TemplateSendMessage(
                alt_text = '想去哪呢?',
                template = ButtonsTemplate(
                    thumbnail_image_url = photo_url,
                    title = place_name,
                    text = info,
                    actions = [
                        URITemplateAction(
                            label = '查看地圖',
                            uri = map_url
                        )
                    ]
                )
            )

            # the linebot replys the message
            line_bot_api.reply_message(event.reply_token, msg)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
