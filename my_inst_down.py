from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import instaloader, os, re, glob, asyncio
from instaloader import Post

load_dotenv()
bot = Bot(token=os.environ['TOKEN'])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
L = instaloader.Instaloader(download_video_thumbnails=False,save_metadata=False, download_geotags=False,download_comments=False)

#check if there is a session file stored if not login with password and save the session yo
script_directory = os.path.dirname(os.path.abspath(__file__))
#session_file = os.path.join(script_directory, 'instagram_session')

#if os.path.isfile(session_file):
#   L.load_session_from_file(os.environ['USERNAME'], session_file)
#else:
#   L.login(os.environ['USERNAME'], os.environ['PASSWORD'])
#   L.save_session_to_file(session_file)

URL = 'https://www.instagram.com/'

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Send me an Instagram link and I'll send you back the content!")

@dp.message_handler(regexp=r'https?://(www\.)?instagram\.com/([^/]+)/([^/?]+)/?')
async def handle_instagram_link(message: types.Message):
    url = message.text
   
    shortcode, content_type = identify_instagram_content(url)
    directory = download_media(shortcode, content_type)
    
    # await message.reply(f"The content in the provided link is: {content_type} and shortcode is: {shortcode}")
 
    # print('path: ', directory)
    #await asyncio.sleep(1)
    media = types.MediaGroup()
    await types.ChatActions.upload_photo()
    os.chdir(directory)
     # send photo
    for file in glob.glob("*.jpg"):
      print(file)
      media.attach_photo(types.InputFile(file))
      await message.reply_media_group(media=media)
      media = types.MediaGroup()
      await types.ChatActions.upload_video()
    # send video
    for file in glob.glob("*.mp4"):
      print(file)
      media.attach_video(types.InputFile(file))
    await message.reply_media_group(media=media)
    # Delete downloaded files and directory
    for file in glob.glob("*"):
      os.remove(file)
    # Change back to the parent directory
    os.chdir("..")

    # Remove the directory
    os.rmdir(directory)

def identify_instagram_content(url):
    if re.search(r'/(?:stories)/', url):
        match = re.search(r'/(?:\w+)/(\d+)', url)
        shortcode = match.group(1)
        content_type='Stories'
        print(shortcode)
        return shortcode, content_type
    elif re.search(r'/p/|/reel/', url):
        shortcode = re.search(r'/(?:p|reel)/([^/?]+)', url).group(1)
        content_type='Post'
        print(shortcode)
        return shortcode, content_type
    elif re.search(r"story_media_id=([0-9]+)", url):
        match = re.search(r"story_media_id=([0-9]+)", url)
        shortcode = match.group(1)
        content_type='Stories'
        print(shortcode)
        return shortcode, content_type
    else:
        content_type = 'Unknown'
        shortcode = 'Unknown'
        return shortcode, content_type
    
def download_media(shortcode, content_type):
    if shortcode == 'Unknown':
      error_message = "the link is not media"
    elif content_type == 'Stories':
      media_id = int(shortcode)
      story_item = instaloader.StoryItem.from_mediaid(L.context, media_id)
      L.download_storyitem(story_item, target='{}'.format(story_item.owner_username))
      directory = story_item.owner_username
      print(f"{directory} Success.")
      return directory
    elif content_type == 'Post':
      post = Post.from_shortcode(L.context, shortcode)
      L.download_post(post, target='{}'.format(post.owner_username))
      directory = post.owner_username
      print(f"{directory} Success.")
      return directory
    else:
      error_message = "Failed to download media."
      asyncio.run(send_telegram_message(error_message))

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)