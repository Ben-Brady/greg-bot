from dotenv import load_dotenv
load_dotenv()
from modules.client import Client
import os

client = Client()
client.run(os.getenv("TOKEN"))