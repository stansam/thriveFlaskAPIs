from app.services.base.repository import BaseRepository
from app.repository.base.repository import BaseRepository as NewBaseRepo
from app.repository.user.repository import UserRepository
from app.models.user import User

print("Repositories imported successfully.")
repo = UserRepository()
print("UserRepository instantiated successfully.")
