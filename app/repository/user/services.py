from sqlalchemy.orm import Session
from app.models import User
from app.repository.user.ops import CreateUser, DeleteUser, GetUserByID, GetUsers, UpdateUser, VerifyUserEmail, GenerateEmailVerificationToken  

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def CreateUser(self, user_data: dict) -> User:
        return CreateUser(self.db).execute(user_data)

    def VerifyUserEmail(self, user_id: str, token: str) -> User:
        return VerifyUserEmail(self.db).execute(user_id, token)

    def UpdateUser(self, user_id: str, user_data: dict) -> User:
        return UpdateUser(self.db).execute(user_id, user_data)    

    def DeleteUser(self, user_id: str) -> User:
        return DeleteUser(self.db).execute(user_id)

    def GetUsers(self) -> list[User]:
        return GetUsers(self.db).execute()
        
    def GetUserByID(self, user_id: str) -> User:
        return GetUserByID(self.db).execute(user_id)    
    
    def GenerateEmailVerificationToken(self, user_id: str) -> User:
        return GenerateEmailVerificationToken(self.db).execute(user_id)
    