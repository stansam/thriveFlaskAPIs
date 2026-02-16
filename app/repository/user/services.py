from sqlalchemy.orm import Session
from app.models import User
from app.repository.user.ops import CreateUser, DeleteUser, GetUserByID, GetUserByEmail, GetAdminUser, GetUsers, UpdateUser, VerifyUserEmail, GenerateEmailVerificationToken, GoogleOAuth
from app.repository.user.exceptions import UserNotFound

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def CreateUser(self, user_data: dict) -> User:
        return CreateUser(self.db).execute(user_data)

    def VerifyUserEmail(self, user_id: str, token: str) -> User:
        return VerifyUserEmail(self.db).execute(user_id, token)

    def google_oauth(self, id_token_string: str) -> User:
        return GoogleOAuth(self.db).execute(id_token_string)
    
    def UpdateUser(self, user_id: str, user_data: dict) -> User:
        return UpdateUser(self.db).execute(user_id, user_data)    

    def DeleteUser(self, user_id: str) -> User:
        return DeleteUser(self.db).execute(user_id)

    def GetUsers(self) -> list[User]:
        return GetUsers(self.db).execute()
        
    def GetUserByID(self, user_id: str) -> User:
        return GetUserByID(self.db).execute(user_id)
    
    def GetUserByEmail(self, email: str) -> User:
        return GetUserByEmail(self.db).execute(email)

    def GetAdminUser(self) -> User:
        return GetAdminUser(self.db).execute()
    
    def GenerateEmailVerificationToken(self, user_id: str) -> User:
        return GenerateEmailVerificationToken(self.db).execute(user_id)

    def authenticate_user(self, email: str, password: str) -> User:
        try:
            user = self.GetUserByEmail(email)
            if user and user.check_password(password):
                return user
        except UserNotFound:
            pass
        return None
    